# -*- coding: utf-8 -*-
"""
Cherry Studio Icon Navigation
Icon导航组件 - 左侧垂直图标列表
"""

from typing import List, Dict
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolButton, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING


class IconNavButton(QToolButton):
    """
    Icon导航按钮
    单个图标按钮,支持图标、工具提示、激活状态
    """

    def __init__(self, icon: str, tooltip: str, nav_id: str, parent=None):
        super().__init__(parent)

        self.nav_id = nav_id
        self._icon = icon
        self._is_active = False

        self._setup_ui(tooltip)

    def _setup_ui(self, tooltip: str):
        """设置UI"""
        self.setText(self._icon)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setFixedSize(SIZES['sidebar_icon_width'], SIZES['sidebar_icon_width'])
        self.setCursor(Qt.PointingHandCursor)

        # 设置字体（emoji图标）
        font = QFont(FONTS['title'])
        font.setPixelSize(24)
        self.setFont(font)

        self._update_style()

    def _update_style(self):
        """更新样式"""
        if self._is_active:
            bg_color = COLORS['accent_blue']
            text_color = COLORS['text_inverse']
        else:
            bg_color = "transparent"
            text_color = COLORS['text_secondary']

        self.setStyleSheet(f"""
            QToolButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: {SIZES['border_radius']}px;
            }}
            QToolButton:hover {{
                background-color: {COLORS['bg_hover'] if not self._is_active else COLORS['accent_blue']};
                color: {COLORS['text_primary'] if not self._is_active else COLORS['text_inverse']};
            }}
            QToolButton:pressed {{
                background-color: {COLORS['accent_blue']};
                color: {COLORS['text_inverse']};
            }}
        """)

    def set_active(self, active: bool):
        """设置激活状态"""
        self._is_active = active
        self.setChecked(active)
        self._update_style()


class CherryIconNav(QWidget):
    """
    Cherry Studio Icon导航
    垂直图标列表,支持切换不同的功能面板
    """

    # 信号定义
    nav_changed = Signal(str)           # nav_id: "chat", "manage", "settings", "help"
    new_chat_requested = Signal()       # 新建对话请求
    manage_chats_requested = Signal()   # 管理历史对话请求
    settings_requested = Signal()       # 打开设置请求
    help_requested = Signal()           # 打开帮助请求

    # 导航项配置
    NAV_ITEMS = [
        {"id": "new_chat", "icon": "➕", "tooltip": "新建对话"},
        {"id": "manage", "icon": "📁", "tooltip": "管理历史对话"},
        {"id": "settings", "icon": "⚙️", "tooltip": "设置"},
        {"id": "help", "icon": "❓", "tooltip": "帮助"},
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        # 导航按钮管理
        self._nav_buttons: Dict[str, IconNavButton] = {}
        self._active_nav_id: str = None

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setFixedWidth(SIZES['sidebar_icon_width'])
        self.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['xs'], SPACING['sm'], SPACING['xs'], SPACING['sm'])
        layout.setSpacing(SPACING['xs'])
        layout.setAlignment(Qt.AlignTop)

        # 创建导航按钮
        for nav_item in self.NAV_ITEMS:
            btn = IconNavButton(
                icon=nav_item['icon'],
                tooltip=nav_item['tooltip'],
                nav_id=nav_item['id']
            )
            btn.clicked.connect(lambda checked, nid=nav_item['id']: self._on_nav_clicked(nid))
            layout.addWidget(btn)

            self._nav_buttons[nav_item['id']] = btn

        # 添加弹性空间
        layout.addStretch()

    def _on_nav_clicked(self, nav_id: str):
        """导航按钮点击"""
        # 更新激活状态
        for nid, btn in self._nav_buttons.items():
            btn.set_active(nid == nav_id)

        # 更新激活导航ID
        old_nav_id = self._active_nav_id
        self._active_nav_id = nav_id

        # 发射信号
        if old_nav_id != nav_id:
            self.nav_changed.emit(nav_id)

        # 发射特定导航的信号
        if nav_id == "new_chat":
            self.new_chat_requested.emit()
        elif nav_id == "manage":
            self.manage_chats_requested.emit()
        elif nav_id == "settings":
            self.settings_requested.emit()
        elif nav_id == "help":
            self.help_requested.emit()

    def set_active_nav(self, nav_id: str):
        """设置激活的导航项"""
        if nav_id in self._nav_buttons:
            self._on_nav_clicked(nav_id)

    def get_active_nav_id(self) -> str:
        """获取当前激活的导航项ID"""
        return self._active_nav_id


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel

    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("Cherry Studio Icon Nav Test")
    window.resize(400, 600)

    layout = QHBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # 添加Icon导航
    icon_nav = CherryIconNav()
    layout.addWidget(icon_nav)

    # 测试内容区域
    test_label = QLabel("点击左侧图标导航\n查看切换效果")
    test_label.setAlignment(Qt.AlignCenter)
    test_label.setStyleSheet(f"""
        background: {COLORS['bg_main']};
        color: {COLORS['text_secondary']};
        padding: 40px;
        font-size: 16px;
    """)
    layout.addWidget(test_label, stretch=1)

    # 连接信号测试
    icon_nav.nav_changed.connect(
        lambda nid: test_label.setText(f"导航切换到: {nid}\n\n当前激活: {icon_nav.get_active_nav_id()}")
    )

    icon_nav.new_chat_requested.connect(
        lambda: test_label.setText("新建对话请求\n(应该创建新标签页)")
    )

    icon_nav.manage_chats_requested.connect(
        lambda: test_label.setText("管理历史对话请求\n(应该打开历史管理对话框)")
    )

    icon_nav.settings_requested.connect(
        lambda: test_label.setText("设置请求\n(应该打开设置面板)")
    )

    icon_nav.help_requested.connect(
        lambda: test_label.setText("帮助请求\n(应该打开帮助文档)")
    )

    window.show()
    sys.exit(app.exec())
