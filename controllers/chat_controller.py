# -*- coding: utf-8 -*-
"""
Chat Controller
对话功能控制器，协调 UI 和 AI 服务
"""

import logging
import time
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, TYPE_CHECKING
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMessageBox
from modules.ai_integration import (
    OpenAIProvider, ProviderConfig, ChatManager,
    StreamingHandler, ChatMessage
)
from modules.ai_integration.api_providers.base_provider import ProviderError
from modules.ai_integration.prompt_store import PromptStore
from models import AnalysisPanelState
from models.data_models import PromptTemplate, TokenUsageInfo
from .analysis_session_controller import AnalysisSessionController
from .request_preview_service import RequestPreviewService, RequestPreviewState
# 使用新的Cherry Studio组件
from components.chat import CherryMainWindow
from components.chat.dialogs.prompt_editor_dialog import PromptEditorDialog
# 导入数据库管理器
from data.chat.db_manager import ChatDatabaseManager

if TYPE_CHECKING:  # pragma: no cover
    from main import MainWindow

logger = logging.getLogger(__name__)

# ==================== 常量定义 ====================
SESSION_TITLE_MAX_LENGTH = 10  # 会话标题最大字符数
SESSION_RETENTION_DAYS = 90  # 会话保留天数
MAPPING_KEY_PATTERN = re.compile(r"\[(?P<item>.+?)\]!\[(?P<column>.+?)\]")


class ChatController(QObject):
    """
    对话功能控制器
    管理对话窗口、AI 服务提供商和对话历史
    """

    def __init__(self, parent=None):
        """初始化控制器"""
        super().__init__(parent)

        # 组件
        self.chat_window: Optional[CherryMainWindow] = None
        self.provider: Optional[OpenAIProvider] = None
        self.chat_manager: Optional[ChatManager] = None
        self.streaming_handler: Optional[StreamingHandler] = None

        # 数据库管理器 (新增)
        self.db_manager: Optional[ChatDatabaseManager] = None

        # 参数配置
        self.current_config: Optional[ProviderConfig] = None
        self.current_parameters = {}

        # 会话状态 (新增)
        self.current_session_id: Optional[str] = None
        self.window_just_opened = True  # 窗口刚打开标志

        # 错误通知标志 (避免重复弹窗)
        self._db_save_error_shown = False

        # 提示词管理
        self.prompt_store = PromptStore()
        self.current_prompt: PromptTemplate = self.prompt_store.load_default_prompt()
        self.request_preview_service = RequestPreviewService()
        self._preview_initialized = False
        self._last_stream_usage_payload: Optional[Dict[str, Any]] = None

        # 分析面板控制器
        self.analysis_controller = AnalysisSessionController(Path(".cache") / "analysis_session")
        self.analysis_controller.set_callbacks(
            on_state_change=self._on_analysis_state_changed,
            on_payload_change=self._on_analysis_payload_changed,
        )
        self._analysis_panel_state: AnalysisPanelState = AnalysisPanelState()
        self._analysis_preview_text: Optional[str] = None
        self._analysis_payload_json: Optional[str] = None

        # 一键解析状态标志
        self._auto_parse_pending = False  # 是否在等待AI回复后自动解析

    def initialize(self, config: ProviderConfig):
        """
        初始化 AI 服务

        Args:
            config: 提供商配置
        """
        try:
            # 创建提供商
            self.provider = OpenAIProvider(config)
            self.current_config = config

            # 创建对话管理器
            self.chat_manager = ChatManager()

            # 创建流式处理器
            self.streaming_handler = StreamingHandler(self.provider)
            self.request_preview_service.set_headers(self.provider.headers)
            self.request_preview_service.set_request_metadata(
                endpoint_url=getattr(self.provider, "base_url", None),
                model_name=self.current_config.model if self.current_config else None,
            )

            # 连接信号（只连接一次，避免重复连接）
            self.streaming_handler.stream_started.connect(self._on_stream_started)
            self.streaming_handler.chunk_received.connect(self._on_chunk_received)
            self.streaming_handler.stream_finished.connect(self._on_stream_finished)
            self.streaming_handler.stream_error.connect(self._on_stream_error)
            self.streaming_handler.usage_received.connect(self._on_stream_usage)

            # 初始化数据库 (新增)
            self._initialize_database()

            # 重新加载默认提示词
            self.current_prompt = self.prompt_store.load_default_prompt()

            logger.info(f"AI 服务初始化成功: {config.model}")

        except Exception as e:
            logger.error(f"初始化 AI 服务失败: {e}")
            raise

    def _initialize_database(self):
        """初始化数据库连接"""
        try:
            self.db_manager = ChatDatabaseManager()
            self.db_manager.connect()

            # 清理旧会话（使用常量）
            deleted_count = self.db_manager.cleanup_old_sessions(days=SESSION_RETENTION_DAYS)
            if deleted_count > 0:
                logger.info(f"启动时清理了 {deleted_count} 个旧会话")

            # 迁移旧的JSON数据（如果存在）
            self.db_manager.migrate_from_json('.cache/chat_state.json')

        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            self.db_manager = None  # 确保失败时设为None

    def update_analysis_context(
        self,
        workbook_manager,
        *,
        current_sheet: Optional[str] = None,
        target_column_config: Optional[List[Dict[str, Any]]] = None,
        source_column_configs: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> None:
        """由主界面调用，用于同步最新的工作簿与列配置。"""
        self.analysis_controller.sync_context(
            workbook_manager,
            current_sheet=current_sheet,
            target_column_config=target_column_config,
            source_column_configs=source_column_configs,
        )

    def _push_analysis_state_to_ui(self) -> None:
        if not self.chat_window:
            return
        self.chat_window.sidebar.update_analysis_state(self._analysis_panel_state)
        if self._analysis_preview_text:
            self.chat_window.update_analysis_preview(self._analysis_preview_text, is_placeholder=False)
        else:
            self.chat_window.update_analysis_preview("", is_placeholder=True)

    def _set_analysis_preview_placeholder(self) -> None:
        self._analysis_preview_text = None
        self._analysis_payload_json = None
        if self.chat_window:
            self.chat_window.update_analysis_preview("", is_placeholder=True)

    def _save_analysis_request_history(
        self,
        sheet_name: str,
        payload: Dict[str, Any],
        preview_text: str,
    ) -> None:
        """Persist analysis pre-send payload for auditing purposes."""
        parent_window = self.parent()
        file_manager = getattr(parent_window, "file_manager", None)
        if not file_manager:
            return

        headers: Dict[str, Any] = {}
        if self.provider and hasattr(self.provider, "headers"):
            try:
                headers = dict(getattr(self.provider, "headers", {}) or {})
            except Exception:  # pragma: no cover - defensive
                headers = {}

        endpoint = getattr(self.provider, "base_url", None)
        model_name = self.current_config.model if self.current_config else None

        try:
            file_manager.save_analysis_request_history(
                sheet_name=sheet_name,
                payload=payload,
                prompt_text=preview_text,
                headers=headers,
                endpoint=endpoint,
                model=model_name,
                warnings=self.analysis_controller.get_latest_warnings(),
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to save analysis request history: %s", exc)

    def _export_formula_snapshot(
        self,
        sheet_name: str,
        entries: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> None:
        parent_window = self.parent()
        file_manager = getattr(parent_window, "file_manager", None)
        if not file_manager or not entries:
            return
        try:
            file_manager.export_formula_snapshot(
                sheet_name=sheet_name,
                entries=entries,
                metadata=metadata,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to export formula snapshot: %s", exc)

    @staticmethod
    def _make_json_safe(value: Any) -> Any:
        """确保对象可序列化为 JSON。"""
        try:
            json.dumps(value, ensure_ascii=False)
            return value
        except TypeError:
            if isinstance(value, dict):
                return {
                    str(key): ChatController._make_json_safe(val)
                    for key, val in value.items()
                }
            if isinstance(value, (list, tuple, set)):
                return [ChatController._make_json_safe(item) for item in value]
            return str(value)

    def _alert_user(self, message: str, title: str = "提示") -> None:
        if self.chat_window:
            QMessageBox.information(self.chat_window, title, message)
        else:
            logger.info("%s: %s", title, message)

    def _extract_analysis_mappings(self, raw_text: str) -> Optional[Dict[str, Dict[str, str]]]:
        if not raw_text:
            return None

        candidates: List[str] = []
        code_block = self._extract_json_from_code_block(raw_text)
        if code_block:
            candidates.append(code_block)

        bracket_candidate = self._extract_json_bracket_block(raw_text)
        if bracket_candidate:
            candidates.append(bracket_candidate)

        candidates.append(raw_text)

        for candidate in candidates:
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError:
                continue

            if not isinstance(data, dict):
                continue

            mappings = data.get("mappings")
            if mappings is None:
                continue

            result: Dict[str, Dict[str, str]] = {}

            if isinstance(mappings, dict):
                for target_name, column_map in mappings.items():
                    if isinstance(column_map, dict):
                        nested: Dict[str, str] = {}
                        for column_name, payload in column_map.items():
                            if isinstance(payload, dict):
                                formula = payload.get("formula")
                            else:
                                formula = payload
                            if not formula:
                                continue
                            nested[str(column_name)] = str(formula)
                        if nested:
                            result[str(target_name)] = nested
                    else:
                        formula = (
                            column_map.get("formula")
                            if isinstance(column_map, dict)
                            else column_map
                        )
                        if formula:
                            result.setdefault(str(target_name), {})["__default__"] = str(formula)

            elif isinstance(mappings, list):
                for item in mappings:
                    if not isinstance(item, dict):
                        continue
                    raw_key = item.get("target_name") or item.get("target_id") or ""
                    column_display = item.get("column_display") or item.get("column") or item.get("column_name")
                    formula = item.get("formula")
                    if not formula:
                        continue

                    target_name: Optional[str] = None
                    column_name: Optional[str] = column_display

                    if item.get("target_name"):
                        target_name = str(item.get("target_name"))
                    else:
                        split_target, split_column = self._split_analysis_mapping_key(str(raw_key))
                        if split_target and split_column:
                            target_name = split_target
                            column_name = column_display or split_column
                        elif split_target:
                            target_name = split_target
                            column_name = column_display or split_column or "__default__"
                        else:
                            target_name = str(raw_key)
                            column_name = column_display or "__default__"

                    if not target_name or not column_name:
                        continue

                    result.setdefault(target_name, {})[str(column_name)] = str(formula)

            if result:
                return result

        return None

    def _extract_json_from_code_block(self, text: str) -> Optional[str]:
        if "```" not in text:
            return None

        segments = text.split("```")
        for segment in segments:
            stripped = segment.strip()
            if not stripped:
                continue
            if stripped.lower().startswith("json"):
                stripped = stripped[4:].strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                return stripped
        return None

    def _extract_json_bracket_block(self, text: str) -> Optional[str]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return text[start : end + 1]

    def _split_analysis_mapping_key(self, raw_key: str) -> Tuple[Optional[str], Optional[str]]:
        if not raw_key:
            return None, None
        match = MAPPING_KEY_PATTERN.fullmatch(raw_key.strip())
        if not match:
            return None, None
        return match.group("item").strip(), match.group("column").strip()

    def _on_analysis_state_changed(self, state: AnalysisPanelState) -> None:
        initial_warnings = self.analysis_controller.get_latest_warnings()
        if hasattr(state, "warnings"):
            state.warnings = list(initial_warnings)
        self._analysis_panel_state = state

        # 更新AI助手窗口的分析面板
        if self.chat_window:
            self.chat_window.sidebar.update_analysis_state(state)

        # 同时更新主界面的分析面板（新增）
        parent_window = self.parent()
        if parent_window and hasattr(parent_window, 'main_analysis_panel'):
            parent_window.main_analysis_panel.set_state(state)

        has_selection = any(column.checked for column in state.target_columns)
        if not state.has_workbook or not has_selection:
            self._set_analysis_preview_placeholder()
            return

        # 生成最新的预览 payload
        self.analysis_controller.build_payload()

        updated_warnings = self.analysis_controller.get_latest_warnings()
        if updated_warnings != initial_warnings:
            if hasattr(state, "warnings"):
                state.warnings = list(updated_warnings)
            # 更新两个面板
            if self.chat_window:
                self.chat_window.sidebar.update_analysis_state(state)
            if parent_window and hasattr(parent_window, 'main_analysis_panel'):
                parent_window.main_analysis_panel.set_state(state)

    def _on_analysis_payload_changed(self, payload: Dict[str, Any]) -> None:
        if not payload or not payload.get("targets_to_map"):
            self._set_analysis_preview_placeholder()
            return

        try:
            raw_json = json.dumps(payload, ensure_ascii=False, indent=2)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to serialize analysis payload: %s", exc)
            raw_json = str(payload)

        self._analysis_payload_json = raw_json

        warnings = self.analysis_controller.get_latest_warnings()
        if warnings:
            warning_lines = "\n".join(f"- {warning}" for warning in warnings)
            preview_text = f"⚠️ 标识符告警:\n{warning_lines}\n\n{raw_json}"
        else:
            preview_text = raw_json

        self._analysis_preview_text = preview_text
        if self.chat_window:
            self.chat_window.update_analysis_preview(preview_text, is_placeholder=False)

    def show_chat_window(self):
        """显示对话窗口"""
        if not self.chat_window:
            self.chat_window = CherryMainWindow()

            # 连接信号
            self.chat_window.message_sent.connect(self._on_user_message_sent)
            self.chat_window.window_closed.connect(self._on_window_closed)
            self.chat_window.parameters_changed.connect(self._on_parameters_changed)
            self.chat_window.generation_stopped.connect(self._on_generation_stopped)
            self.chat_window.prompt_edit_requested.connect(self._on_prompt_edit_requested)
            self.chat_window.input_area.draft_changed.connect(self._on_draft_text_changed)

            # 连接会话管理信号 (新增)
            sidebar = self.chat_window.sidebar
            sidebar.session_selected.connect(self._on_session_selected)
            sidebar.session_delete_requested.connect(self._on_session_delete_requested)
            sidebar.new_session_requested.connect(self._on_new_session_requested)
            sidebar.analysis_target_sheet_changed.connect(self.analysis_controller.handle_target_sheet_change)
            sidebar.analysis_target_column_toggled.connect(self.analysis_controller.handle_target_column_toggle)
            sidebar.analysis_source_column_toggled.connect(self.analysis_controller.handle_source_column_toggle)
            sidebar.analysis_apply_requested.connect(self._on_analysis_apply_requested)
            sidebar.analysis_auto_parse_requested.connect(self._on_analysis_auto_parse_requested)  # 一键解析信号连接
            sidebar.analysis_export_json_requested.connect(self._on_analysis_export_json_requested)  # 导出JSON信号连接

            # 设置初始参数
            if self.current_parameters:
                param_panel = self.chat_window.get_parameter_panel()
                if param_panel:
                    # 将参数应用到设置面板
                    for key, value in self.current_parameters.items():
                        param_panel.set_parameter(key, value)

            # 加载会话列表 (新增)
            self._load_session_list()

            # 默认选中"对话"TAB (新增)
            sidebar.show_sessions_tab()
            self._publish_preview_state(self.request_preview_service.placeholder_state())
        # 更新提示词显示
        self.chat_window.set_prompt_template(self.current_prompt)
        self._push_analysis_state_to_ui()

        # 重置窗口打开标志
        self.window_just_opened = True

        self.chat_window.show()
        self.chat_window.raise_()
        self.chat_window.activateWindow()

    def hide_chat_window(self):
        """隐藏对话窗口"""
        if self.chat_window:
            self.chat_window.hide()

    def _on_analysis_auto_parse_requested(self) -> None:
        """一键解析：预发送 → 自动发送 → 等待AI回复 → 自动解析应用"""
        # 1. 执行预发送逻辑
        payload = self.analysis_controller.build_payload()
        if payload is None:
            self._alert_user("没有可用的分析请求，请检查目标列与来源列的勾选。")
            return

        text = self._analysis_payload_json
        if not text:
            try:
                text = json.dumps(payload, ensure_ascii=False, indent=2)
            except Exception:
                text = str(payload)
            self._analysis_payload_json = text

        sheet_name = self.analysis_controller.get_current_sheet_name()
        if sheet_name:
            self._save_analysis_request_history(sheet_name, payload, text)

        if not self.chat_window:
            return

        # 2. 切换到对话TAB
        self.chat_window.sidebar.show_sessions_tab()

        # 3. 设置自动解析标志
        self._auto_parse_pending = True

        # 4. 锁定分析面板交互
        self.chat_window.sidebar.set_analysis_enabled(False)

        # 5. 自动发送消息
        # 获取当前AI参数
        ai_params = self.chat_window.sidebar.get_parameters() if self.chat_window else {}
        self._on_user_message_sent(text, ai_params)

    def _on_analysis_export_json_requested(self) -> None:
        """导出JSON：先输出提示词，再输出请求payload"""
        # 1. 生成payload
        payload = self.analysis_controller.build_payload()
        if payload is None:
            self._alert_user("没有可用的分析请求，请检查目标列与来源列的勾选。")
            return

        # 2. 获取当前表名
        sheet_name = self.analysis_controller.get_current_sheet_name()
        if not sheet_name:
            self._alert_user("请先选择待写入的目标表。")
            return

        # 3. 准备导出内容
        export_data = {}

        # 3.1 添加提示词部分
        developer_content = (self.current_prompt.content or "").strip()
        base_system_prompt = self.current_parameters.get(
            'system_prompt',
            "你是一个专业的财务数据分析助手。"
        )

        if developer_content:
            if base_system_prompt:
                combined_prompt = f"{base_system_prompt}\n\n{developer_content}"
            else:
                combined_prompt = developer_content
            export_data["prompt"] = combined_prompt
        elif base_system_prompt:
            export_data["prompt"] = base_system_prompt

        # 3.2 添加请求payload
        export_data["request"] = payload

        # 3.3 添加元数据
        export_data["metadata"] = {
            "sheet_name": sheet_name,
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": self.current_config.model if self.current_config else "unknown"
        }

        # 4. 创建导出目录
        from pathlib import Path
        export_dir = Path("请求文件夹")
        export_dir.mkdir(exist_ok=True)

        # 5. 生成文件名: 表名+请求.json
        filename = f"{sheet_name}+请求.json"
        export_path = export_dir / filename

        # 6. 写入文件
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            self._alert_user(f"JSON文件已成功导出到:\n{export_path}")
            logger.info(f"导出JSON成功: {export_path}")

        except Exception as e:
            self._alert_user(f"导出JSON失败: {str(e)}", title="错误")
            logger.error(f"导出JSON失败: {e}")

    def _on_analysis_apply_requested(self) -> None:
        """解析AI回复并尝试将公式应用到主界面。"""
        sheet_name = self.analysis_controller.get_current_sheet_name()
        if not sheet_name:
            self._alert_user("请先选择待写入的目标表。")
            return

        if not self.chat_manager:
            self._alert_user("当前对话为空，请先让 AI 返回映射结果。")
            return

        last_message = self.chat_manager.get_last_message()
        if not last_message or last_message.role != "assistant":
            self._alert_user("未找到可解析的 AI 回复，请先获取映射结果。")
            return

        mappings = self._extract_analysis_mappings(last_message.content or "")
        if not mappings:
            self._alert_user("AI 回复中未找到有效的映射结果。")
            return

        selected_columns = self.analysis_controller.get_selected_target_columns()
        entries: List[Dict[str, Any]] = []

        for target_name, column_map in mappings.items():
            if not isinstance(column_map, dict):
                column_map = {"__default__": column_map}

            for column_display, mapping_info in column_map.items():
                display_name = str(column_display)
                if isinstance(mapping_info, dict):
                    formula_text = str(mapping_info.get("formula", "")).strip()
                    confidence_raw = mapping_info.get("confidence")
                    reasoning_text = str(mapping_info.get("reasoning", "") or "").strip()
                else:
                    formula_text = str(mapping_info or "").strip()
                    confidence_raw = None
                    reasoning_text = ""

                column_key = self.analysis_controller.resolve_target_column_key(display_name)
                if not column_key:
                    continue
                if selected_columns and column_key not in selected_columns:
                    continue
                if not formula_text:
                    continue

                entry: Dict[str, Any] = {
                    "target_name": str(target_name),
                    "column_display": display_name,
                    "column_key": column_key,
                    "formula": formula_text,
                }

                try:
                    if confidence_raw is not None:
                        confidence_value = max(0.0, min(1.0, float(confidence_raw)))
                        entry["confidence"] = confidence_value
                except (TypeError, ValueError):
                    pass

                if reasoning_text:
                    entry["reasoning"] = reasoning_text

                entries.append(entry)

        if not entries:
            self._alert_user("映射结果与当前分析配置不匹配，请确认后重试。")
            return

        metadata: Dict[str, Any] = {
            "source": "ai_analysis",
            "assistant_message": last_message.content,
            "raw_mappings": self._make_json_safe(mappings),
            "model": self.current_config.model if self.current_config else None,
        }
        cached_payload = self.analysis_controller.get_cached_payload()
        if cached_payload:
            metadata["analysis_payload"] = self._make_json_safe(cached_payload)
        if self._analysis_preview_text:
            metadata["analysis_preview"] = self._analysis_preview_text

        parent_window = self.parent()
        if not parent_window or not hasattr(parent_window, "apply_analysis_formulas"):
            logger.error("主窗口引用不存在或不支持 apply_analysis_formulas。")
            self._alert_user("内部错误：无法访问主界面。", title="错误")
            return

        applied, total = parent_window.apply_analysis_formulas(sheet_name, entries)  # type: ignore[attr-defined]
        metadata["applied_count"] = applied
        metadata["total_entries"] = total
        metadata["timestamp"] = datetime.now().astimezone().isoformat(timespec="seconds")
        self._export_formula_snapshot(sheet_name, entries, metadata)

        if applied:
            self._alert_user(f"已成功应用 {applied}/{total} 条映射公式。")
        else:
            self._alert_user("未能应用任何映射公式，请检查 AI 返回的内容。", title="提示")

    @Slot(str, dict)
    def _on_user_message_sent(self, message: str, ai_params: dict):
        """
        处理用户发送的消息（新接口）

        Args:
            message: 用户消息内容
            ai_params: AI参数字典
        """
        # 更新参数
        if ai_params:
            self.update_parameters(ai_params)

        # 调用原有的处理逻辑
        self._on_user_message(message)

    @Slot(str)
    def _on_user_message(self, message: str):
        """
        处理用户发送的消息

        Args:
            message: 用户消息内容
        """
        if not self.provider or not self.chat_manager:
            logger.error("AI 服务未初始化")
            return

        # 重置本次流式 usage 缓存
        self._last_stream_usage_payload = None

        # 处理新会话创建逻辑 (新增)
        if self.window_just_opened and not self.current_session_id:
            # 窗口刚打开且没有选中会话，创建新会话
            self._create_new_session(message)
            self.window_just_opened = False

        # 保存用户消息到数据库 (新增)
        if self.current_session_id and self.db_manager:
            try:
                self.db_manager.save_message(self.current_session_id, 'user', message)
            except Exception as e:
                logger.error(f"保存用户消息失败: {e}")
                # 显示用户友好的错误提示（每个会话仅提示一次）
                if not self._db_save_error_shown and self.chat_window:
                    self._db_save_error_shown = True
                    QMessageBox.warning(
                        self.chat_window,
                        "消息保存失败",
                        f"无法保存消息到数据库：{str(e)}\n\n对话可以继续，但本次会话的历史记录将不会保存。"
                    )

        # 添加到历史
        self.chat_manager.add_message('user', message)

        # 禁用输入
        if self.chat_window:
            self.chat_window.set_input_enabled(False)
            self.chat_window.show_typing_indicator()
            self.chat_window.hide_welcome_message()

        # 组装API消息列表
        # 1. 获取提示词内容
        developer_content = (self.current_prompt.content or "").strip()

        # 2. 获取系统提示词
        base_system_prompt = self.current_parameters.get(
            'system_prompt',
            "你是一个专业的财务数据分析助手。"
        )

        # 3. 构建messages数组
        messages_for_api = []
        system_prompt_for_api = base_system_prompt

        # 先添加提示词（作为system消息）
        if developer_content:
            if base_system_prompt:
                combined_prompt = f"{base_system_prompt}\n\n{developer_content}"
            else:
                combined_prompt = developer_content
            messages_for_api.append(
                ChatMessage(role='system', content=combined_prompt)
            )
            system_prompt_for_api = None  # 避免重复的 system 消息

        # 再添加历史消息
        context_messages = self.chat_manager.get_context_messages()
        messages_for_api.extend(context_messages)

        # 记录请求开始时间
        self.request_start_time = time.time()

        endpoint_base = getattr(self.provider, 'base_url', 'https://api.openai.com/v1')
        request_url = f"{endpoint_base}/chat/completions"
        self.request_preview_service.set_request_metadata(endpoint_url=request_url)
        request_data: Dict[str, Any] = {
            'url': request_url,
            'model': self.current_config.model if self.current_config else 'unknown',
            'messages': [msg.to_dict() for msg in messages_for_api],
        }
        if system_prompt_for_api:
            request_data['system_prompt'] = system_prompt_for_api

        optional_fields = [
            'temperature',
            'max_tokens',
            'top_p',
            'frequency_penalty',
            'presence_penalty',
        ]
        for field in optional_fields:
            if field in self.current_parameters:
                request_data[field] = self.current_parameters[field]

        stream_enabled = self.current_parameters.get('stream', True)
        if stream_enabled:
            request_data['stream'] = True

        preview_state = self.request_preview_service.build_preview(request_payload=request_data)
        self._publish_preview_state(preview_state)

        # 记录到调试查看器
        if self.chat_window:
            self.chat_window.log_api_call(request_data)

        # 检查是否启用流式输出
        stream_output = stream_enabled

        if stream_output:
            # 启动流式响应
            try:
                # 确保参数已经通过 update_parameters 更新到 provider
                # StreamingHandler 会使用 provider 的配置
                self.streaming_handler.start_stream(
                    messages=messages_for_api,
                    system_prompt=system_prompt_for_api
                )
            except ProviderError as e:
                self._on_stream_error(str(e))
        else:
            # 非流式响应（一次性获取完整响应）
            try:
                # 使用同步方式获取响应
                response = self.provider.chat_completion(
                    messages=messages_for_api,
                    system_prompt=system_prompt_for_api,
                    stream=False
                )
                # 直接处理完整响应
                self._on_non_stream_response(response)
            except ProviderError as e:
                self._on_stream_error(str(e))

    @Slot()
    def _on_stream_started(self):
        """处理流式响应开始"""
        # CherryMainWindow 已在 _on_message_sent 中调用了 start_streaming_message()
        # 这里不需要再次调用，避免重复
        pass

    @Slot(dict)
    def _on_stream_usage(self, usage: Dict[str, Any]):
        """记录流式响应中的 usage 信息"""
        self._last_stream_usage_payload = usage or {}

    def _build_usage_info(self, usage_payload: Optional[Dict[str, Any]]) -> TokenUsageInfo:
        info = TokenUsageInfo.from_usage_payload(usage_payload)
        if info.status != "complete":
            return TokenUsageInfo.missing()
        return info

    @Slot(str)
    def _on_chunk_received(self, chunk: str):
        """
        处理接收到的流式响应片段

        Args:
            chunk: 文本片段
        """
        # 实时更新UI显示流式文本
        if self.chat_window:
            self.chat_window.update_streaming_message(chunk)

    @Slot(str)
    def _on_stream_finished(self, full_response: str):
        """
        处理流式响应完成

        Args:
            full_response: 完整响应文本
        """
        # 计算耗时
        elapsed = time.time() - self.request_start_time if hasattr(self, 'request_start_time') else 0

        usage_payload = self.streaming_handler.last_usage or self._last_stream_usage_payload
        usage_info = self._build_usage_info(usage_payload)
        self._last_stream_usage_payload = None

        # 保存AI消息到数据库 (新增)
        if self.current_session_id and self.db_manager:
            try:
                metadata = {"token_usage": usage_info.to_metadata()}
                self.db_manager.save_message(
                    self.current_session_id,
                    'assistant',
                    full_response,
                    metadata_json=metadata,
                )
            except Exception as e:
                logger.error(f"保存AI消息失败: {e}")
                # 显示用户友好的错误提示（每个会话仅提示一次）
                if not self._db_save_error_shown and self.chat_window:
                    self._db_save_error_shown = True
                    QMessageBox.warning(
                        self.chat_window,
                        "消息保存失败",
                        f"无法保存消息到数据库：{str(e)}\n\n对话可以继续，但本次会话的历史记录将不会保存。"
                    )

        # 添加到历史
        self.chat_manager.add_message('assistant', full_response)

        # 完成流式消息显示
        if self.chat_window:
            self.chat_window.finish_streaming_message(token_usage=usage_info)
            self.chat_window.set_input_enabled(True)

        # 检查是否需要自动解析应用
        if self._auto_parse_pending:
            self._auto_parse_pending = False
            # 解锁分析面板
            if self.chat_window:
                self.chat_window.sidebar.set_analysis_enabled(True)
            # 自动执行解析应用
            self._on_analysis_apply_requested()
            return  # 提前返回，避免重复更新UI

        # 更新调试信息
        if self.chat_window:
            if usage_info.status == "complete" and usage_info.has_all_tokens:
                token_count = {
                    'prompt_tokens': usage_info.prompt_tokens,
                    'completion_tokens': usage_info.completion_tokens,
                    'total_tokens': usage_info.total_tokens,
                }
            else:
                token_count = {
                    'prompt_tokens': None,
                    'completion_tokens': None,
                    'total_tokens': None,
                }

            response_data = {
                'content': full_response,
                'finish_reason': 'stop',
                'model': self.current_config.model if self.current_config else 'unknown'
            }
            response_data['usage'] = usage_info.to_metadata()

            self.chat_window.log_api_call(
                request_data={},  # 已在 _on_user_message 中记录
                response_data=response_data,
                elapsed_time=elapsed,
                token_count=token_count
            )

        logger.info(f"AI 响应完成，耗时: {elapsed:.2f}秒, 长度: {len(full_response)}")
        self._update_request_preview()

    @Slot(str)
    def _on_stream_error(self, error_msg: str):
        """
        处理流式响应错误

        Args:
            error_msg: 错误消息
        """
        logger.error(f"AI 响应错误: {error_msg}")
        self._last_stream_usage_payload = None

        # 如果是一键解析过程中出错，解锁分析面板
        if self._auto_parse_pending:
            self._auto_parse_pending = False
            if self.chat_window:
                self.chat_window.sidebar.set_analysis_enabled(True)

        # 显示错误消息
        if self.chat_window:
            self.chat_window.hide_typing_indicator()
            error_response = f"❌ **错误**: {error_msg}\n\n请检查网络连接和 API 配置。"
            self.chat_window.add_assistant_message(error_response)
            self.chat_window.set_input_enabled(True)

    def _on_non_stream_response(self, response: str):
        """
        处理非流式响应（一次性完整响应）

        Args:
            response: 完整的响应文本
        """
        # 计算耗时
        elapsed = time.time() - self.request_start_time if hasattr(self, 'request_start_time') else 0

        # 隐藏输入指示器
        if self.chat_window:
            self.chat_window.hide_typing_indicator()

        usage_info = self._build_usage_info(getattr(response, "usage", None))

        # 保存AI消息到数据库 (新增)
        if self.current_session_id and self.db_manager:
            try:
                metadata = {"token_usage": usage_info.to_metadata()}
                self.db_manager.save_message(
                    self.current_session_id,
                    'assistant',
                    response,
                    metadata_json=metadata,
                )
            except Exception as e:
                logger.error(f"保存AI消息失败: {e}")
                # 显示用户友好的错误提示（每个会话仅提示一次）
                if not self._db_save_error_shown and self.chat_window:
                    self._db_save_error_shown = True
                    QMessageBox.warning(
                        self.chat_window,
                        "消息保存失败",
                        f"无法保存消息到数据库：{str(e)}\n\n对话可以继续，但本次会话的历史记录将不会保存。"
                    )

        # 添加到历史
        self.chat_manager.add_message('assistant', response)

        # 直接显示完整消息
        if self.chat_window:
            self.chat_window.add_assistant_message(response, token_usage=usage_info)
            self.chat_window.set_input_enabled(True)

        # 检查是否需要自动解析应用
        if self._auto_parse_pending:
            self._auto_parse_pending = False
            # 解锁分析面板
            if self.chat_window:
                self.chat_window.sidebar.set_analysis_enabled(True)
            # 自动执行解析应用
            self._on_analysis_apply_requested()
            return  # 提前返回，避免重复更新UI

        # 更新调试信息
        if self.chat_window:
            if usage_info.status == "complete" and usage_info.has_all_tokens:
                token_count = {
                    'prompt_tokens': usage_info.prompt_tokens,
                    'completion_tokens': usage_info.completion_tokens,
                    'total_tokens': usage_info.total_tokens,
                }
            else:
                token_count = {
                    'prompt_tokens': None,
                    'completion_tokens': None,
                    'total_tokens': None,
                }

            response_data = {
                'content': response,
                'finish_reason': 'stop',
                'model': self.current_config.model if self.current_config else 'unknown'
            }
            response_data['usage'] = usage_info.to_metadata()

            self.chat_window.log_api_call(
                request_data={},  # 已在 _on_user_message 中记录
                response_data=response_data,
                elapsed_time=elapsed,
                token_count=token_count
            )

        logger.info(f"AI 响应完成（非流式），耗时: {elapsed:.2f}秒, 长度: {len(response)}")
        self._update_request_preview()

    @Slot()
    def _on_window_closed(self):
        """处理窗口关闭"""
        # 保存对话状态
        if self.chat_manager:
            self.chat_manager.save_state()

        logger.info("对话窗口已关闭")

    @Slot(str)
    def _on_draft_text_changed(self, text: str):
        """输入框草稿更新时刷新调试预览。"""

        self._update_request_preview(draft_text=text)

    @Slot(dict)
    def _on_parameters_changed(self, parameters: dict):
        """
        处理参数变更信号

        Args:
            parameters: 参数字典
        """
        self.update_parameters(parameters)

    def update_parameters(self, parameters: dict):
        """
        更新 AI 参数

        Args:
            parameters: 参数字典
        """
        self.current_parameters = parameters

        # 更新提供商配置
        if self.current_config and self.provider:
            optional_fields = [
                'temperature',
                'max_tokens',
                'top_p',
                'frequency_penalty',
                'presence_penalty',
            ]
            for field in optional_fields:
                setattr(
                    self.current_config,
                    field,
                    parameters.get(field) if field in parameters else None,
                )

            # 重新创建提供商（应用新参数）
            self.provider = OpenAIProvider(self.current_config)
            self.streaming_handler = StreamingHandler(self.provider)
            self.request_preview_service.set_headers(self.provider.headers)
            endpoint_url = f"{getattr(self.provider, 'base_url', 'https://api.openai.com/v1')}/chat/completions"
            self.request_preview_service.set_request_metadata(
                endpoint_url=endpoint_url,
                model_name=self.current_config.model if self.current_config else None,
            )

            # 重新连接信号（包括所有信号）
            self.streaming_handler.stream_started.connect(self._on_stream_started)
            self.streaming_handler.chunk_received.connect(self._on_chunk_received)
            self.streaming_handler.stream_finished.connect(self._on_stream_finished)
            self.streaming_handler.stream_error.connect(self._on_stream_error)

            logger.info(f"参数已更新: {parameters}")

        self._update_request_preview()

    @Slot()
    def _on_generation_stopped(self):
        """处理用户停止生成请求"""
        # 停止流式处理
        if self.streaming_handler:
            # TODO: StreamingHandler需要添加stop方法
            logger.info("用户请求停止生成")

        # 重新启用输入
        if self.chat_window:
            self.chat_window.set_input_enabled(True)

    def test_connection(self) -> tuple[bool, str]:
        """
        测试 API 连接

        Returns:
            (是否成功, 消息)
        """
        if not self.provider:
            return False, "AI 服务未初始化"

        return self.provider.validate_connection()

    # ==================== 会话管理方法 (新增) ====================

    def _load_session_list(self):
        """加载会话列表到侧边栏"""
        if not self.db_manager or not self.chat_window:
            return

        try:
            sessions = self.db_manager.list_sessions(limit=100)
            self.chat_window.sidebar.load_sessions(sessions)
            logger.info(f"已加载 {len(sessions)} 个会话")
        except Exception as e:
            logger.error(f"加载会话列表失败: {e}")

    def _load_prompt_for_session(self, session_id: Optional[str]) -> PromptTemplate:
        """根据会话ID加载提示词"""
        if not session_id or not self.db_manager:
            return self.prompt_store.load_default_prompt()

        prompt = self.db_manager.get_session_prompt(session_id)
        if prompt:
            return prompt
        return self.prompt_store.load_default_prompt()

    def _save_prompt_for_session(self, prompt: PromptTemplate):
        """保存当前提示词到会话"""
        if not self.db_manager or not self.current_session_id:
            return
        try:
            self.db_manager.save_session_prompt(self.current_session_id, prompt)
        except Exception as e:
            logger.error(f"保存会话提示词失败: {e}")

    def _set_current_prompt(self, prompt: PromptTemplate, save_default: bool = False):
        """更新当前提示词并刷新 UI"""
        self.current_prompt = prompt
        if save_default:
            try:
                self.prompt_store.save_default_prompt(prompt)
            except Exception as e:
                logger.error(f"保存默认提示词失败: {e}")
        if self.chat_window:
            self.chat_window.set_prompt_template(self.current_prompt)
        self._update_request_preview()

    def _on_prompt_edit_requested(self):
        """处理提示词编辑请求"""
        if not self.chat_window:
            return

        history_items: List[Tuple[str, PromptTemplate]] = []

        def format_label(prefix: str, prompt: PromptTemplate) -> str:
            timestamp = prompt.updated_at.strftime("%Y-%m-%d %H:%M") if isinstance(prompt.updated_at, datetime) else str(prompt.updated_at)
            summary = prompt.first_line or prompt.title or "(空提示词)"
            summary = summary[:24] + "…" if len(summary) > 24 else summary
            return f"{prefix} {timestamp} · {summary}"

        if self.db_manager and self.current_session_id:
            session_history = self.db_manager.get_session_prompt_history(self.current_session_id, limit=5)
            for prompt in session_history:
                history_items.append((format_label("会话", prompt), prompt))

        default_history = self.prompt_store.get_history(limit=5)
        for prompt in default_history:
            history_items.append((format_label("默认", prompt), prompt))

        dialog = PromptEditorDialog(
            self.chat_window,
            prompt=self.current_prompt,
            history=history_items,
        )
        dialog.prompt_saved.connect(self._on_prompt_saved)
        dialog.exec()

    def _on_prompt_saved(self, prompt: PromptTemplate):
        """提示词保存后更新存储"""
        self._set_current_prompt(prompt, save_default=True)
        self._save_prompt_for_session(prompt)

    def _update_request_preview(self, *, draft_text: Optional[str] = None) -> None:
        if not self.chat_window:
            return

        if draft_text is None:
            draft_text = self.chat_window.input_area.get_input_text()

        history = list(self.chat_manager.messages) if self.chat_manager else []
        parameters = self.current_parameters or {}

        state = self.request_preview_service.update_sources(
            parameters=parameters,
            prompt=self.current_prompt,
            history=history,
            draft_text=draft_text,
        )

        if state:
            self._publish_preview_state(state)
        elif not self._preview_initialized:
            self._publish_preview_state(self.request_preview_service.placeholder_state())

    def _publish_preview_state(self, state: RequestPreviewState) -> None:
        if not self.chat_window:
            return

        self.chat_window.update_request_preview(state)
        self._preview_initialized = True

    def _create_new_session(self, first_message: str):
        """
        创建新会话

        Args:
            first_message: 第一条用户消息
        """
        if not self.db_manager:
            logger.warning("数据库未初始化，无法创建会话")
            return

        try:
            # 生成会话标题（前SESSION_TITLE_MAX_LENGTH字符，空白时使用默认标题）
            trimmed_message = first_message.strip() if first_message else ""
            if trimmed_message:
                title = trimmed_message[:SESSION_TITLE_MAX_LENGTH]
            else:
                # 使用时间戳创建唯一的默认标题
                title = f"新对话 {datetime.now().strftime('%m-%d %H:%M')}"

            # 序列化AI参数
            settings_json = json.dumps(self.current_parameters, ensure_ascii=False)

            # 创建会话
            self.current_session_id = self.db_manager.create_session(title, settings_json)
            logger.info(f"已创建新会话: {self.current_session_id}, 标题: {title}")

            # 重置错误通知标志（新会话允许重新提示）
            self._db_save_error_shown = False

            # 保存当前提示词到会话
            self._save_prompt_for_session(self.current_prompt)

            # 刷新会话列表
            self._load_session_list()

        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            # 显示用户友好的错误提示
            if self.chat_window:
                QMessageBox.warning(
                    self.chat_window,
                    "创建会话失败",
                    f"无法创建新会话：{str(e)}\n\n对话可以继续，但历史记录将不会保存。"
                )

    @Slot(str)
    def _on_session_selected(self, session_id: str):
        """
        处理会话选中事件

        Args:
            session_id: 被选中的会话ID
        """
        if not self.db_manager:
            return

        try:
            # 加载新会话
            self.current_session_id = session_id
            session_prompt = self._load_prompt_for_session(session_id)
            self._set_current_prompt(session_prompt, save_default=False)
            messages = self.db_manager.load_messages(session_id)

            # 清空聊天窗口
            if self.chat_window:
                self.chat_window.clear_messages()
                self.chat_window.set_prompt_template(self.current_prompt)
                self.chat_window.hide_welcome_message()

            # 重新创建ChatManager
            self.chat_manager = ChatManager()

            # 加载消息到UI和ChatManager
            for msg in messages:
                # 添加到ChatManager
                self.chat_manager.add_message(msg['role'], msg['content'])

                # 添加到UI
                if self.chat_window:
                    if msg['role'] == 'user':
                        self.chat_window.add_user_message(msg['content'])
                    else:
                        metadata = msg.get('metadata') or {}
                        usage_info = TokenUsageInfo.from_metadata(metadata.get('token_usage'))
                        self.chat_window.add_assistant_message(
                            msg['content'],
                            token_usage=usage_info,
                        )

            # 清除窗口打开标志（已选中会话，不会自动创建新会话）
            self.window_just_opened = False

            # 重置错误通知标志（切换会话允许重新提示）
            self._db_save_error_shown = False

            logger.info(f"已加载会话: {session_id}, 消息数: {len(messages)}")
            self._update_request_preview()

        except Exception as e:
            logger.error(f"加载会话失败: {e}")

    @Slot(str)
    def _on_session_delete_requested(self, session_id: str):
        """
        处理会话删除请求

        Args:
            session_id: 要删除的会话ID
        """
        if not self.db_manager or not self.chat_window:
            return

        try:
            # 获取会话标题
            session = self.db_manager.load_session(session_id)
            if not session:
                return

            # 弹出确认对话框
            reply = QMessageBox.question(
                self.chat_window,
                "确认删除",
                f"确认删除会话「{session['title']}」？\n此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # 删除会话
                self.db_manager.delete_session(session_id)

                # 从UI移除
                self.chat_window.sidebar.remove_session(session_id)

                # 如果删除的是当前会话，清空聊天区域
                if self.current_session_id == session_id:
                    self.current_session_id = None
                    if self.chat_window:
                        self.chat_window.clear_messages()
                    # 重置ChatManager
                    self.chat_manager = ChatManager()

                logger.info(f"已删除会话: {session_id}")

        except Exception as e:
            logger.error(f"删除会话失败: {e}")

    @Slot()
    def _on_new_session_requested(self):
        """处理新建会话请求"""
        # 清空当前会话
        self.current_session_id = None

        # 重置提示词为默认值
        default_prompt = self.prompt_store.load_default_prompt()
        self._set_current_prompt(default_prompt, save_default=False)

        # 清空聊天窗口
        if self.chat_window:
            self.chat_window.clear_messages()
            self.chat_window.set_prompt_template(self.current_prompt)

        # 重置ChatManager
        self.chat_manager = ChatManager()

        # 清除会话选中状态
        if self.chat_window:
            self.chat_window.sidebar.clear_session_selection()
        self._update_request_preview()

        # 设置窗口打开标志（下次发送消息时自动创建新会话）
        self.window_just_opened = True

        # 重置错误通知标志（新会话允许重新提示）
        self._db_save_error_shown = False

        logger.info("准备创建新会话")
