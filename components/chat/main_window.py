# -*- coding: utf-8 -*-
"""
Cherry Studio Main Window
主窗口 - 集成所有组件,实现完整的聊天界面
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from models.data_models import PromptTemplate, TokenUsageInfo
from .styles.cherry_theme import COLORS, FONTS, SIZES, SPACING, get_global_stylesheet
from .widgets.title_bar import CherryTitleBar
from .widgets.message_area import MessageArea
from .widgets.input_area import CherryInputArea
from .widgets.suggestion_area import CherrySuggestionArea
from .widgets.sidebar import CherrySidebar
from controllers.request_preview_service import RequestPreviewState
from .dialogs.request_preview_dialog import RequestPreviewDialog


class CherryMainWindow(QWidget):
    """
    Cherry Studio 主窗口
    无边框窗口,集成所有UI组件
    """

    # 信号定义
    message_sent = Signal(str, dict)  # (消息内容, AI参数)
    generation_stopped = Signal()  # 停止生成
    file_uploaded = Signal(str)  # 文件上传

    # 向后兼容信号（用于ChatController）
    window_closed = Signal()  # 窗口关闭
    parameters_changed = Signal(dict)  # 参数变更
    prompt_edit_requested = Signal()  # 请求编辑提示词

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_tab_id = 0
        self._is_generating = False
        self._request_preview_state: Optional[RequestPreviewState] = None
        self._preview_dialog: Optional[RequestPreviewDialog] = None

        self._setup_window()
        self._setup_ui()
        self._connect_signals()

    def _setup_window(self):
        """设置窗口属性"""
        # 无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint)

        # 窗口大小（增加宽度80px以适应更宽的侧边栏，增加高度100px以避免滚动）
        self.resize(1320, 900)

        # 应用全局样式表
        self.setStyleSheet(get_global_stylesheet())

    def _setup_ui(self):
        """设置UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==================== 标题栏 ====================
        self.title_bar = CherryTitleBar()
        main_layout.addWidget(self.title_bar)

        # ==================== 内容区域 ====================
        content_area = QWidget()
        content_area.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 中央聊天区域
        chat_area = QWidget()
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # 消息区域
        self.message_area = MessageArea()
        chat_layout.addWidget(self.message_area, stretch=1)
        self.message_area.prompt_clicked.connect(self.prompt_edit_requested.emit)

        # 建议芯片区域
        self.suggestion_area = CherrySuggestionArea()
        chat_layout.addWidget(self.suggestion_area)

        # 输入区域
        self.input_area = CherryInputArea()
        chat_layout.addWidget(self.input_area)

        content_layout.addWidget(chat_area, stretch=1)

        # 侧边栏
        self.sidebar = CherrySidebar()
        content_layout.addWidget(self.sidebar)

        main_layout.addWidget(content_area, stretch=1)

        # 添加初始标签页
        initial_tab_id = self.title_bar.add_tab("💬", "AI 分析助手")
        self._current_tab_id = initial_tab_id

    def _connect_signals(self):
        """连接信号"""
        # 标题栏信号
        self.title_bar.tab_changed.connect(self._on_tab_changed)
        self.title_bar.tab_closed.connect(self._on_tab_closed)
        self.title_bar.new_tab_requested.connect(self._on_new_tab)
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.maximize_requested.connect(self._toggle_maximize)
        self.title_bar.close_requested.connect(self.close)

        # 输入区域信号
        self.input_area.message_sent.connect(self._on_message_sent)
        self.input_area.stop_requested.connect(self._on_stop_generation)
        self.input_area.file_uploaded.connect(self.file_uploaded.emit)
        self.input_area.help_requested.connect(lambda: self.sidebar.show_help_panel())
        self.input_area.history_requested.connect(self._on_history_requested)
        self.input_area.template_requested.connect(self._on_template_requested)

        # 建议芯片信号
        self.suggestion_area.suggestion_clicked.connect(self._on_suggestion_clicked)

        # 侧边栏信号
        self.sidebar.new_chat_requested.connect(self._on_new_tab)
        self.sidebar.manage_chats_requested.connect(self._on_manage_chats)
        self.sidebar.parameter_changed.connect(self._on_parameter_changed)  # 处理单个参数变化
        self.sidebar.debug_panel_clicked.connect(self._on_debug_panel_clicked)

    def _on_parameter_changed(self, param_name: str, value):
        """
        处理单个参数变化
        收集所有参数后发射parameters_changed信号
        """
        # 获取完整的参数字典
        all_params = self.sidebar.get_parameters()
        # 发射向后兼容的信号
        self.parameters_changed.emit(all_params)

    def _on_tab_changed(self, tab_id: int):
        """Tab切换"""
        self._current_tab_id = tab_id
        # TODO: 加载对应Tab的对话历史

    def _on_tab_closed(self, tab_id: int):
        """Tab关闭"""
        # TODO: 保存对话历史
        pass

    def _on_new_tab(self):
        """新建Tab"""
        new_id = self.title_bar.add_tab("💬", "新对话")
        self._current_tab_id = new_id

    def _on_message_sent(self, message: str):
        """发送消息"""
        self.message_area.hide_welcome_message()
        # 添加用户消息到消息区域
        self.message_area.add_user_message(message)

        # 获取AI参数
        ai_params = self.sidebar.get_parameters()

        # 提取模型信息用于显示标题
        model_name = ai_params.get('model', 'gemini-2.5-pro')  # 默认模型
        provider = "Google"  # 默认提供商
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")

        # 开始流式AI消息，传入AI元数据
        self.message_area.start_streaming_message(
            model_name=model_name,
            provider=provider,
            timestamp=timestamp
        )

        # 设置生成状态
        self._is_generating = True
        self.input_area.set_generating(True)

        # 发射信号 (由外部AI服务处理)
        self.message_sent.emit(message, ai_params)

    def _on_stop_generation(self):
        """停止生成"""
        self._is_generating = False
        self.input_area.set_generating(False)
        self.message_area.finish_streaming_message()
        self.generation_stopped.emit()

    def _on_suggestion_clicked(self, suggestion: str):
        """建议被点击 - 填充到输入框"""
        self.input_area.set_input_text(suggestion)
        self.input_area.focus_input()

    def _on_history_requested(self):
        """查看历史记录"""
        # TODO: 实现历史记录对话框
        pass

    def _on_template_requested(self):
        """使用模板"""
        # TODO: 实现模板选择对话框
        pass

    def _on_manage_chats(self):
        """管理对话"""
        # TODO: 实现对话管理对话框
        pass

    def _toggle_maximize(self):
        """切换最大化/还原"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ==================== 外部调用接口 ====================

    def start_streaming_message(self):
        """
        开始流式消息 (由外部AI服务调用)
        显示加载动画
        """
        self.message_area.start_streaming_message()

    def update_streaming_message(self, chunk: str):
        """
        更新流式消息 (由外部AI服务调用)

        Args:
            chunk: 新的文本片段
        """
        self.message_area.update_streaming_message(chunk)

    def finish_streaming_message(self, token_usage: Optional[TokenUsageInfo] = None):
        """完成流式消息 (由外部AI服务调用)"""
        self.message_area.finish_streaming_message(token_usage=token_usage)
        self._is_generating = False
        self.input_area.set_generating(False)

    def add_ai_message(self, content: str, token_usage: Optional[TokenUsageInfo] = None):
        """
        添加AI完整消息 (非流式,由外部AI服务调用)

        Args:
            content: 消息内容
        """
        self.message_area.hide_welcome_message()
        self.message_area.add_ai_message(content, token_usage=token_usage)

    def set_suggestions(self, suggestions: list):
        """
        设置建议芯片

        Args:
            suggestions: 建议文本列表
        """
        self.suggestion_area.set_suggestions(suggestions)

    def set_prompt_template(self, prompt: PromptTemplate):
        """更新提示词气泡显示"""
        self.message_area.set_prompt(prompt)

    def hide_welcome_message(self):
        """隐藏欢迎文案"""
        self.message_area.hide_welcome_message()

    def clear_messages(self):
        """清空所有消息"""
        self.message_area.clear_messages()

    def get_ai_parameters(self) -> Dict[str, Any]:
        """获取当前AI参数"""
        return self.sidebar.get_parameters()

    # ==================== 向后兼容接口（用于ChatController） ====================

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.window_closed.emit()
        super().closeEvent(event)

    def set_input_enabled(self, enabled: bool):
        """
        设置输入框启用状态（向后兼容）

        Args:
            enabled: True=启用, False=禁用
        """
        self.input_area.set_generating(not enabled)

    def show_typing_indicator(self):
        """显示打字指示器（向后兼容）"""
        # 在新UI中，通过开始流式消息来表示AI正在思考
        pass  # 实际上start_streaming_message会处理

    def hide_typing_indicator(self):
        """隐藏打字指示器（向后兼容）"""
        # 新UI中不需要额外处理
        pass

    def add_assistant_message(self, content: str, token_usage: Optional[TokenUsageInfo] = None):
        """
        添加助手消息（向后兼容，别名）

        Args:
            content: 消息内容
        """
        self.add_ai_message(content, token_usage=token_usage)

    def add_user_message(self, content: str):
        """
        添加用户消息（向后兼容，包装方法）

        Args:
            content: 消息内容
        """
        self.message_area.hide_welcome_message()
        self.message_area.add_user_message(content)

    def log_api_call(
        self,
        request_data: dict = None,
        response_data: dict = None,
        elapsed_time: float = 0,
        token_count: dict = None,
    ):
        """
        记录API调用（向后兼容，简化实现）

        Args:
            request_data: 请求数据
            response_data: 响应数据
            elapsed_time: 耗时（秒）
            token_count: Token统计
        """
        # 简化实现：仅打印到控制台
        if request_data:
            print(f"[API Request] Model: {request_data.get('model', 'unknown')}")
        if response_data:
            print(f"[API Response] Time: {elapsed_time:.2f}s, Tokens: {token_count}")

    def get_parameter_panel(self):
        """获取参数面板（向后兼容）"""
        return self.sidebar.settings_panel

    def get_debug_viewer(self):
        """获取调试查看器（向后兼容，暂未实现）"""
        return None

    # ==================== 调试Tab支持 ====================

    def update_request_preview(self, state: Optional[RequestPreviewState]) -> None:
        """将预览内容显示在调试TAB中，并缓存当前状态。"""

        self._request_preview_state = state
        if state is None or state.is_placeholder or not state.display_text:
            self.sidebar.update_debug_preview("", is_placeholder=True)
        else:
            self.sidebar.update_debug_preview(state.display_text, is_placeholder=False)

        if self._preview_dialog:
            self._preview_dialog.set_preview(state)

    def _on_debug_panel_clicked(self) -> None:
        if self._preview_dialog is None:
            self._preview_dialog = RequestPreviewDialog(self)
        self._preview_dialog.set_preview(self._request_preview_state)
        self._preview_dialog.show()
        self._preview_dialog.raise_()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # 创建主窗口
    window = CherryMainWindow()

    # ==================== 模拟AI流式输出测试 ====================
    def simulate_ai_response(message: str, params: Dict[str, Any]):
        """模拟AI流式响应"""
        print(f"\n✅ 收到消息: {message}")
        print(f"📊 AI参数: {params}")

        # 模拟AI响应文本
        ai_response = (
            f"您好!我收到了您的消息:\n\n"
            f"「{message}」\n\n"
            f"让我为您分析一下...\n\n"
            f"这是一条模拟的AI流式输出响应。"
            f"当前使用的模型是: {params.get('model', 'unknown')}\n"
            f"Temperature设置为: {params.get('temperature', 0.7)}\n\n"
            f"如果这是真实的AI服务,这里将显示智能分析结果。"
        )

        # 模拟流式输出 (每50ms输出一个字符)
        char_index = [0]

        def stream_next_char():
            if char_index[0] < len(ai_response):
                window.update_streaming_message(ai_response[char_index[0]])
                char_index[0] += 1
            else:
                timer.stop()
                window.finish_streaming_message()

        timer = QTimer()
        timer.timeout.connect(stream_next_char)
        timer.start(30)  # 每30ms输出一个字符

    def on_generation_stopped():
        """生成被停止"""
        print("\n⛔ 用户停止了生成")

    def on_file_uploaded(filename: str):
        """文件上传"""
        print(f"\n📎 文件上传: {filename}")

    # 连接信号
    window.message_sent.connect(simulate_ai_response)
    window.generation_stopped.connect(on_generation_stopped)
    window.file_uploaded.connect(on_file_uploaded)

    # 设置初始建议
    window.set_suggestions(
        [
            "帮我分析这份财务报表的数据结构",
            "生成营业收入的映射公式",
            "如何提取利润表中的数据?",
            "解释快报表的填充逻辑",
        ]
    )

    window.show()
    sys.exit(app.exec())
