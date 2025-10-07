# -*- coding: utf-8 -*-
"""
Cherry Studio Tab Bar
横向TAB导航栏组件 - 用于侧边栏TAB切换
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING


class CherryTabButton(QPushButton):
    """
    单个TAB按钮
    """

    def __init__(self, tab_id: str, text: str, parent=None):
        super().__init__(text, parent)
        self.tab_id = tab_id
        self._is_active = False

        self.setFont(FONTS['body'])
        self.setFixedHeight(SIZES['tab_height'])
        self.setCursor(Qt.PointingHandCursor)

        self._update_style()

    def set_active(self, active: bool):
        """设置激活状态"""
        self._is_active = active
        self._update_style()

    def _update_style(self):
        """更新样式"""
        if self._is_active:
            # 选中态：蓝色背景，白色文字，圆角
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_blue']};
                    color: {COLORS['text_inverse']};
                    border: none;
                    border-radius: {SIZES['border_radius']}px;
                    padding: 0px {SPACING['md']}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #2563EB;
                }}
            """)
        else:
            # 未选中态：透明背景，灰色文字，圆角
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_secondary']};
                    border: none;
                    border-radius: {SIZES['border_radius']}px;
                    padding: 0px {SPACING['md']}px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_hover']};
                    color: {COLORS['text_primary']};
                }}
            """)


class CherryTabBar(QWidget):
    """
    Cherry Studio TAB导航栏
    横向TAB切换组件
    """

    # 信号：TAB切换
    tab_changed = Signal(str)  # tab_id

    def __init__(self, parent=None):
        super().__init__(parent)

        self._tabs = {}  # tab_id -> CherryTabButton
        self._active_tab_id = None

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setFixedHeight(SIZES['tab_height'])
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_sidebar']};
                border: none;
            }}
        """)

        # 水平布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(SPACING['sm'], 0, 0, 0)
        self.layout.setSpacing(SPACING['sm'])
        self.layout.setAlignment(Qt.AlignLeft)

    def add_tab(self, tab_id: str, text: str):
        """
        添加TAB

        Args:
            tab_id: TAB唯一ID
            text: TAB显示文本
        """
        if tab_id in self._tabs:
            return

        tab_button = CherryTabButton(tab_id, text)
        tab_button.clicked.connect(lambda: self._on_tab_clicked(tab_id))

        self._tabs[tab_id] = tab_button
        self.layout.addWidget(tab_button)

    def set_active_tab(self, tab_id: str):
        """
        设置激活TAB

        Args:
            tab_id: TAB ID
        """
        if tab_id not in self._tabs:
            return

        if self._active_tab_id == tab_id:
            return

        # 取消旧TAB激活状态
        if self._active_tab_id and self._active_tab_id in self._tabs:
            self._tabs[self._active_tab_id].set_active(False)

        # 激活新TAB
        self._active_tab_id = tab_id
        self._tabs[tab_id].set_active(True)

        # 发射信号
        self.tab_changed.emit(tab_id)

    def _on_tab_clicked(self, tab_id: str):
        """处理TAB点击"""
        self.set_active_tab(tab_id)

    def get_active_tab(self) -> str:
        """获取当前激活的TAB ID"""
        return self._active_tab_id
