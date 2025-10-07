# -*- coding: utf-8 -*-
"""
Chat Controller
对话功能控制器，协调 UI 和 AI 服务
"""

import logging
import time
import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMessageBox
from modules.ai_integration import (
    OpenAIProvider, ProviderConfig, ChatManager,
    StreamingHandler, ChatMessage
)
from modules.ai_integration.api_providers.base_provider import ProviderError
from modules.ai_integration.prompt_store import PromptStore
from models.data_models import PromptTemplate, TokenUsageInfo
from .request_preview_service import RequestPreviewService, RequestPreviewState
# 使用新的Cherry Studio组件
from components.chat import CherryMainWindow
from components.chat.dialogs.prompt_editor_dialog import PromptEditorDialog
# 导入数据库管理器
from data.chat.db_manager import ChatDatabaseManager

logger = logging.getLogger(__name__)

# ==================== 常量定义 ====================
SESSION_TITLE_MAX_LENGTH = 10  # 会话标题最大字符数
SESSION_RETENTION_DAYS = 90  # 会话保留天数


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

        # 重置窗口打开标志
        self.window_just_opened = True

        self.chat_window.show()
        self.chat_window.raise_()
        self.chat_window.activateWindow()

    def hide_chat_window(self):
        """隐藏对话窗口"""
        if self.chat_window:
            self.chat_window.hide()

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

        # 获取上下文消息
        context_messages = self.chat_manager.get_context_messages()

        developer_content = (self.current_prompt.content or "").strip()
        messages_for_api = []
        if developer_content:
            messages_for_api.append(ChatMessage(role='developer', content=developer_content))
        messages_for_api.extend(context_messages)

        # 获取系统提示词
        base_system_prompt = self.current_parameters.get(
            'system_prompt',
            "你是一个专业的财务数据分析助手。"
        )

        developer_content = (self.current_prompt.content or "").strip()
        messages_for_api = []
        system_prompt_for_api = base_system_prompt

        if developer_content:
            if base_system_prompt:
                combined_prompt = f"{base_system_prompt}\n\n{developer_content}"
            else:
                combined_prompt = developer_content
            messages_for_api.append(
                ChatMessage(role='system', content=combined_prompt)
            )
            system_prompt_for_api = None  # 避免重复的 system 消息

        # 获取上下文消息
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
