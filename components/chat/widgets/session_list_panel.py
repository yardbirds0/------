# -*- coding: utf-8 -*-
"""
Session List Panel
会话列表面板 - 显示所有历史会话
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING
from .session_list_item import SessionListItem


class SessionListPanel(QWidget):
    """
    会话列表面板
    显示所有历史会话，支持选中和删除
    """

    # 信号定义
    session_selected = Signal(str)  # session_id
    session_delete_requested = Signal(str)  # session_id
    new_session_requested = Signal()  # 新建会话

    def __init__(self, parent=None):
        super().__init__(parent)

        self._sessions = []  # 会话数据列表
        self._session_widgets = {}  # session_id -> SessionListItem
        self._selected_session_id = None

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==================== 工具栏 ====================
        toolbar = QWidget()
        toolbar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_sidebar']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        toolbar.setFixedHeight(48)

        toolbar_layout = QVBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(SPACING['md'], SPACING['sm'], SPACING['md'], SPACING['sm'])

        # 新建会话按钮（绿色+动态宽度）
        self.new_session_btn = QPushButton("➕ 新建会话")
        self.new_session_btn.setFont(FONTS['body'])
        self.new_session_btn.setCursor(Qt.PointingHandCursor)
        self.new_session_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #10B981;  /* 绿色 */
                color: {COLORS['text_inverse']};
                border: none;
                border-radius: {SIZES['border_radius']}px;
                padding: {SPACING['sm']}px {SPACING['md']}px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #059669;  /* 深绿色悬停效果 */
            }}
        """)
        # 设置动态宽度（自适应内容）
        from PySide6.QtWidgets import QSizePolicy
        self.new_session_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.new_session_btn.adjustSize()

        self.new_session_btn.clicked.connect(self.new_session_requested.emit)
        toolbar_layout.addWidget(self.new_session_btn, alignment=Qt.AlignLeft)

        main_layout.addWidget(toolbar)

        # ==================== 会话列表滚动区域 ====================
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")

        # 列表容器
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        self.list_layout.setAlignment(Qt.AlignTop)

        # 空状态占位符
        self.empty_label = QLabel("暂无对话记录\n点击上方按钮新建会话")
        self.empty_label.setFont(FONTS['body'])
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_tertiary']};
                padding: {SPACING['xl']}px;
            }}
        """)
        self.list_layout.addWidget(self.empty_label)

        scroll_area.setWidget(self.list_container)
        main_layout.addWidget(scroll_area)

    def load_sessions(self, sessions: list):
        """
        加载会话列表

        Args:
            sessions: 会话数据列表，每项格式:
                {
                    'id': str,
                    'title': str,
                    'created_at': str,
                    'updated_at': str,
                    'settings_json': str
                }
        """
        # 清空现有会话
        self._clear_sessions()

        self._sessions = sessions

        if not sessions:
            # 显示空状态
            self.empty_label.show()
            return

        # 隐藏空状态
        self.empty_label.hide()

        # 添加会话项
        for session in sessions:
            session_item = SessionListItem(
                session_id=session['id'],
                title=session['title'],
                created_at=session['created_at']
            )

            # 连接信号
            session_item.clicked.connect(self._on_session_clicked)
            session_item.delete_requested.connect(self._on_delete_requested)

            self._session_widgets[session['id']] = session_item
            self.list_layout.addWidget(session_item)

    def _clear_sessions(self):
        """清空会话列表"""
        for widget in self._session_widgets.values():
            widget.deleteLater()

        self._session_widgets.clear()
        self._selected_session_id = None

    def _on_session_clicked(self, session_id: str):
        """处理会话点击"""
        # 取消旧选中状态
        if self._selected_session_id and self._selected_session_id in self._session_widgets:
            self._session_widgets[self._selected_session_id].set_selected(False)

        # 设置新选中状态
        self._selected_session_id = session_id
        if session_id in self._session_widgets:
            self._session_widgets[session_id].set_selected(True)

        # 发射信号
        self.session_selected.emit(session_id)

    def _on_delete_requested(self, session_id: str):
        """处理删除请求"""
        self.session_delete_requested.emit(session_id)

    def remove_session(self, session_id: str):
        """
        移除会话项（删除后调用）

        Args:
            session_id: 会话ID
        """
        if session_id in self._session_widgets:
            widget = self._session_widgets[session_id]
            widget.deleteLater()
            del self._session_widgets[session_id]

        # 更新空状态
        if not self._session_widgets:
            self.empty_label.show()

    def clear_selection(self):
        """清除选中状态"""
        if self._selected_session_id and self._selected_session_id in self._session_widgets:
            self._session_widgets[self._selected_session_id].set_selected(False)
        self._selected_session_id = None
