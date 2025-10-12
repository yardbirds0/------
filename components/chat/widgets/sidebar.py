# -*- coding: utf-8 -*-
"""
Cherry Studio Sidebar
右侧抽屉式侧边栏 - TAB导航 + 面板切换
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING
from .settings_panel import CherrySettingsPanel
from .tab_bar import CherryTabBar
from .session_list_panel import SessionListPanel
from .debug_panel import CherryDebugPanel
from .analysis_panel import AnalysisPanel


class CherrySidebar(QWidget):
    """
    Cherry Studio 侧边栏
    包含TAB导航和可切换的面板(对话、AI参数设置)
    """

    # 信号定义
    parameter_changed = Signal(str, object)
    debug_panel_clicked = Signal()

    analysis_target_sheet_changed = Signal(str)
    analysis_target_column_toggled = Signal(str, bool)
    analysis_source_column_toggled = Signal(str, str, bool)
    analysis_apply_requested = Signal()
    analysis_auto_parse_requested = Signal()  # 一键解析信号
    analysis_export_json_requested = Signal()  # 导出JSON信号
    analysis_debug_panel_clicked = Signal()

    # 会话相关信号（新）
    session_selected = Signal(str)  # session_id
    session_delete_requested = Signal(str)  # session_id
    new_session_requested = Signal()

    # 兼容性信号（保留向后兼容）
    new_chat_requested = Signal()  # 等同于new_session_requested
    manage_chats_requested = Signal()  # 暂时保留

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_tab = "sessions"  # 默认选中"对话"TAB

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")

        # 固定宽度
        self.setFixedWidth(SIZES['sidebar_width'])

        # 主布局 (垂直)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==================== TAB导航栏 ====================
        self.tab_bar = CherryTabBar()
        self.tab_bar.add_tab("sessions", "对话")
        self.tab_bar.add_tab("analysis", "分析")
        self.tab_bar.add_tab("settings", "AI参数设置")
        self.tab_bar.add_tab("debug", "调试")
        self.tab_bar.set_active_tab("sessions")  # 默认选中"对话"
        main_layout.addWidget(self.tab_bar)

        # ==================== 面板切换器 ====================
        self.panel_stack = QStackedWidget()

        # 1. 对话列表面板
        self.session_list_panel = SessionListPanel()
        self.panel_stack.addWidget(self.session_list_panel)

        # 2. 分析面板
        self.analysis_panel = AnalysisPanel()
        self.panel_stack.addWidget(self.analysis_panel)

        # 3. AI参数设置面板
        self.settings_panel = CherrySettingsPanel()
        self.panel_stack.addWidget(self.settings_panel)

        # 4. 调试面板
        self.debug_panel = CherryDebugPanel()
        self.panel_stack.addWidget(self.debug_panel)

        main_layout.addWidget(self.panel_stack)

        # 连接信号
        self._connect_signals()

    def _create_placeholder_panel(self, icon: str, title: str, description: str) -> QWidget:
        """创建占位面板"""
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        layout.setSpacing(SPACING['md'])
        layout.setAlignment(Qt.AlignCenter)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont(FONTS['title'].family(), 48))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(title)
        title_label.setFont(FONTS['title'])
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setFont(FONTS['body'])
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        layout.addWidget(desc_label)

        return panel

    def _connect_signals(self):
        """连接信号"""
        # TAB切换信号
        self.tab_bar.tab_changed.connect(self._on_tab_changed)

        # 设置面板信号
        self.settings_panel.parameter_changed.connect(self.parameter_changed.emit)
        self.debug_panel.panel_clicked.connect(self.debug_panel_clicked.emit)
        self.analysis_panel.target_sheet_changed.connect(self.analysis_target_sheet_changed.emit)
        self.analysis_panel.target_column_toggled.connect(self.analysis_target_column_toggled.emit)
        self.analysis_panel.source_column_toggled.connect(self.analysis_source_column_toggled.emit)
        self.analysis_panel.apply_requested.connect(self.analysis_apply_requested.emit)
        self.analysis_panel.auto_parse_requested.connect(self.analysis_auto_parse_requested.emit)  # 一键解析信号连接
        self.analysis_panel.export_json_requested.connect(self.analysis_export_json_requested.emit)  # 导出JSON信号连接
        self.debug_panel.analysis_panel_clicked.connect(self.analysis_debug_panel_clicked.emit)

        # 会话列表面板信号
        self.session_list_panel.session_selected.connect(self.session_selected.emit)
        self.session_list_panel.session_delete_requested.connect(self.session_delete_requested.emit)
        self.session_list_panel.new_session_requested.connect(self._on_new_session_requested)

    def _on_new_session_requested(self):
        """处理新建会话请求，发射兼容信号"""
        self.new_session_requested.emit()
        self.new_chat_requested.emit()  # 向后兼容

    def _on_tab_changed(self, tab_id: str):
        """处理TAB切换"""
        self._current_tab = tab_id

        if tab_id == "sessions":
            self.panel_stack.setCurrentIndex(0)
        elif tab_id == "analysis":
            self.panel_stack.setCurrentIndex(1)
        elif tab_id == "settings":
            self.panel_stack.setCurrentIndex(2)
        elif tab_id == "debug":
            self.panel_stack.setCurrentIndex(3)

    def show_sessions_tab(self):
        """显示对话TAB"""
        self.tab_bar.set_active_tab("sessions")

    def show_settings_tab(self):
        """显示设置TAB"""
        self.tab_bar.set_active_tab("settings")

    def show_analysis_tab(self):
        """显示分析TAB"""
        self.tab_bar.set_active_tab("analysis")

    def show_debug_tab(self):
        """显示调试TAB"""
        self.tab_bar.set_active_tab("debug")

    def expand(self):
        """展开侧边栏（已废弃，保留兼容性）"""
        pass

    def collapse(self):
        """收起侧边栏（已废弃，保留兼容性）"""
        pass

    def toggle(self):
        """切换展开/收起状态（已废弃，保留兼容性）"""
        pass

    def is_expanded(self) -> bool:
        """是否已展开（始终返回True）"""
        return True

    def get_parameters(self):
        """获取AI参数"""
        return self.settings_panel.get_parameters()

    def update_debug_preview(self, text: str, *, is_placeholder: bool) -> None:
        """更新调试面板中的请求预览文本。"""

        self.debug_panel.set_chat_preview(text, is_placeholder=is_placeholder)

    def update_analysis_preview(self, text: str, *, is_placeholder: bool) -> None:
        """更新分析请求预览文本。"""

        self.debug_panel.set_analysis_preview(text, is_placeholder=is_placeholder)

    def set_parameter(self, param_name: str, value):
        """设置单个参数"""
        self.settings_panel.set_parameter(param_name, value)

    # ==================== 会话管理方法 (新增) ====================

    def load_sessions(self, sessions: list):
        """
        加载会话列表

        Args:
            sessions: 会话数据列表
        """
        self.session_list_panel.load_sessions(sessions)

    def remove_session(self, session_id: str):
        """
        移除会话项

        Args:
            session_id: 会话ID
        """
        self.session_list_panel.remove_session(session_id)

    def clear_session_selection(self):
        """清除会话选中状态"""
        self.session_list_panel.clear_selection()

    # ==================== 分析面板方法 ====================

    def update_analysis_state(self, state):
        """更新分析TAB的展示内容"""
        self.analysis_panel.set_state(state)

    def set_analysis_enabled(self, enabled: bool):
        """启用或禁用分析TAB交互"""
        self.analysis_panel.block_interactions(not enabled)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("Cherry Studio Sidebar Test")
    window.resize(1000, 700)

    layout = QHBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # 测试内容区域
    content_area = QWidget()
    content_area.setStyleSheet(f"background: {COLORS['bg_main']};")
    content_layout = QVBoxLayout(content_area)
    content_layout.setContentsMargins(SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
    content_layout.setSpacing(SPACING['md'])

    # 测试说明
    info_label = QLabel("测试说明:\n\n"
                       "1. 查看右侧TAB切换功能\n"
                       "2. 点击会话列表项测试选中效果\n"
                       "3. 调整AI参数,下方显示变更信息\n"
                       "4. 点击'新建会话'测试信号\n"
                       "5. 点击'显示对话/设置TAB'切换面板")
    info_label.setFont(FONTS['body'])
    info_label.setWordWrap(True)
    info_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
    content_layout.addWidget(info_label)

    # 参数变更显示区域
    param_display = QLabel("等待参数变更...")
    param_display.setFont(QFont(FONTS['body'].family(), 14))
    param_display.setWordWrap(True)
    param_display.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    param_display.setStyleSheet(f"""
        QLabel {{
            background: {COLORS['bg_input']};
            color: {COLORS['text_primary']};
            padding: {SPACING['md']}px;
            border: 1px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
        }}
    """)
    content_layout.addWidget(param_display, stretch=1)

    # 测试按钮区域
    test_btn_container = QWidget()
    test_btn_layout = QHBoxLayout(test_btn_container)
    test_btn_layout.setSpacing(SPACING['sm'])

    show_sessions_btn = QPushButton("显示对话TAB")
    show_sessions_btn.setFont(FONTS['body'])

    show_settings_btn = QPushButton("显示设置TAB")
    show_settings_btn.setFont(FONTS['body'])

    test_btn_layout.addWidget(show_sessions_btn)
    test_btn_layout.addWidget(show_settings_btn)
    test_btn_layout.addStretch()

    content_layout.addWidget(test_btn_container)

    layout.addWidget(content_area, stretch=1)

    # 添加侧边栏
    sidebar = CherrySidebar()
    layout.addWidget(sidebar)

    # 加载测试会话数据
    test_sessions = [
        {
            'id': 'session_1',
            'title': '财务报表分析',
            'created_at': '2025-01-15T10:30:00',
            'updated_at': '2025-01-15T11:30:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_2',
            'title': '数据映射',
            'created_at': '2025-01-14T15:20:00',
            'updated_at': '2025-01-14T16:00:00',
            'settings_json': '{}'
        }
    ]
    sidebar.load_sessions(test_sessions)

    # 连接测试按钮
    show_sessions_btn.clicked.connect(sidebar.show_sessions_tab)
    show_settings_btn.clicked.connect(sidebar.show_settings_tab)

    # 连接信号测试
    def on_new_session():
        param_display.setText("✅ 新建会话请求")

    def on_session_selected(session_id):
        param_display.setText(f"📌 选中会话: {session_id}")

    def on_param_changed(param_name, value):
        params = sidebar.get_parameters()
        text = f"⚙️ 参数变更: {param_name} = {value}\n\n当前所有参数:\n"
        for k, v in params.items():
            text += f"  {k}: {v}\n"
        param_display.setText(text)

    sidebar.new_session_requested.connect(on_new_session)
    sidebar.session_selected.connect(on_session_selected)
    sidebar.parameter_changed.connect(on_param_changed)

    window.show()
    sys.exit(app.exec())
