# -*- coding: utf-8 -*-
"""
Session List Item
会话列表项组件 - 显示单个会话
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING


class SessionListItem(QWidget):
    """
    会话列表项
    显示会话标题、创建时间和删除按钮
    """

    # 信号定义
    clicked = Signal(str)  # session_id
    delete_requested = Signal(str)  # session_id

    def __init__(self, session_id: str, title: str, created_at: str, parent=None):
        super().__init__(parent)

        self.session_id = session_id
        self.title = title
        self.created_at = created_at

        self._is_selected = False
        self._is_hovered = False

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setFixedHeight(48)  # 减小高度，因为只显示一行
        self.setCursor(Qt.PointingHandCursor)

        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(SPACING['md'], SPACING['sm'], SPACING['md'], SPACING['sm'])
        main_layout.setSpacing(SPACING['sm'])

        # ==================== 标题（占据整行） ====================
        # 限制标题为前20个字符
        display_title = self.title[:20] if len(self.title) > 20 else self.title
        self.title_label = QLabel(display_title)
        self.title_label.setFont(FONTS['body'])
        self.title_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none; padding-left: 8px;")
        main_layout.addWidget(self.title_label, stretch=1)

        # ==================== 右侧：删除按钮 ====================
        self.delete_btn = QPushButton("✕")  # 使用U+2715字符，更清晰
        delete_font = QFont(FONTS['title'].family(), 16, QFont.Bold)
        self.delete_btn.setFont(delete_font)
        self.delete_btn.setFixedSize(28, 28)  # 增大按钮尺寸
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 14px;
                padding: 0px;
                qproperty-iconSize: 16px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_red']};
                color: white;
                font-weight: bold;
            }}
        """)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.delete_btn.hide()  # 默认隐藏，悬停时显示

        main_layout.addWidget(self.delete_btn)

        # 更新样式
        self._update_style()

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self._is_selected = selected
        self._update_style()

    def _update_style(self):
        """更新样式"""
        if self._is_selected:
            # 选中态：白色背景，加粗文字，悬浮阴影效果
            bg_color = "#FFFFFF"
            text_color = COLORS['text_primary']
            font_weight = "bold"
        elif self._is_hovered:
            # 悬停态：浅灰背景
            bg_color = COLORS['bg_hover']
            text_color = COLORS['text_primary']
            font_weight = "normal"
        else:
            # 默认态：透明背景
            bg_color = "transparent"
            text_color = COLORS['text_primary']
            font_weight = "normal"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: {SIZES['border_radius']}px;
                border: none;
            }}
        """)

        # 动态添加/移除阴影效果
        if self._is_selected:
            # 每次都创建新的阴影效果，避免重用已删除的对象
            from PySide6.QtWidgets import QGraphicsDropShadowEffect
            from PySide6.QtGui import QColor

            shadow_effect = QGraphicsDropShadowEffect()
            shadow_effect.setBlurRadius(12)  # 模糊半径
            shadow_effect.setColor(QColor(0, 0, 0, 40))  # 阴影颜色和透明度
            shadow_effect.setOffset(0, 4)  # 阴影偏移
            self.setGraphicsEffect(shadow_effect)
        else:
            # 移除阴影效果
            self.setGraphicsEffect(None)

        self.title_label.setStyleSheet(f"color: {text_color}; border: none; font-weight: {font_weight}; padding-left: 8px;")

    def mousePressEvent(self, event):
        """处理鼠标点击"""
        if event.button() == Qt.LeftButton:
            # 点击删除按钮区域不触发会话选中
            if not self.delete_btn.geometry().contains(event.pos()):
                self.clicked.emit(self.session_id)

        super().mousePressEvent(event)

    def enterEvent(self, event):
        """鼠标进入"""
        self._is_hovered = True
        self.delete_btn.show()  # 悬停时显示删除按钮
        self._update_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self._is_hovered = False
        self.delete_btn.hide()  # 离开时隐藏删除按钮
        self._update_style()
        super().leaveEvent(event)

    def _on_delete_clicked(self):
        """处理删除按钮点击"""
        self.delete_requested.emit(self.session_id)
