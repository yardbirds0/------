# -*- coding: utf-8 -*-
"""
Cherry Studio Title Bar
标题栏组件 - 标签页容器 + 窗口控制按钮
"""

from typing import Dict, List
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QToolButton, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QPen

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING
from .title_bar_model_indicator import TitleBarModelIndicator


class TitleBarTab(QPushButton):
    """
    标签页按钮
    单个标签页，支持图标、标题、关闭按钮
    """

    # 信号定义
    close_requested = Signal(int)  # tab_id

    def __init__(self, tab_id: int, icon: str, title: str, parent=None):
        super().__init__(parent)

        self.tab_id = tab_id
        self._icon = icon
        self._title = title
        self._is_active = False

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setCheckable(True)
        self.setFont(FONTS['body'])
        self.setMinimumWidth(100)
        self.setMaximumWidth(200)
        self.setFixedHeight(SIZES['tab_height'])

        # 自定义样式（避免Qt CSS冲突）
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()

    def _update_style(self):
        """更新样式"""
        if self._is_active:
            bg_color = COLORS['bg_main']
            text_color = COLORS['text_primary']
        else:
            bg_color = COLORS['bg_hover']
            text_color = COLORS['text_secondary']

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: 0px;
                padding: 0px 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_active']};
            }}
        """)

    def set_active(self, active: bool):
        """设置激活状态"""
        self._is_active = active
        self.setChecked(active)
        self._update_style()

    def get_title(self) -> str:
        """获取标题"""
        return self._title

    def set_title(self, title: str):
        """设置标题"""
        self._title = title
        self.setText(f"{self._icon} {title}")

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MiddleButton:
            # 中键点击关闭标签页
            self.close_requested.emit(self.tab_id)
            event.accept()
        else:
            super().mousePressEvent(event)


class CherryTitleBar(QWidget):
    """
    Cherry Studio 标题栏
    包含标签页容器和窗口控制按钮
    """

    # 信号定义
    tab_changed = Signal(int)       # tab_id
    tab_closed = Signal(int)        # tab_id
    new_tab_requested = Signal()    # 新建标签页请求
    minimize_requested = Signal()   # 最小化窗口请求
    maximize_requested = Signal()   # 最大化窗口请求
    close_requested = Signal()      # 关闭窗口请求

    def __init__(self, parent=None):
        super().__init__(parent)

        # 向后兼容：保留空的标签页属性
        self._tabs: Dict[int, TitleBarTab] = {}
        self._active_tab_id: int = 0
        self._next_tab_id: int = 1

        # 鼠标拖动
        self._drag_start_position = None

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setFixedHeight(SIZES['titlebar_height'])
        self.setStyleSheet(f"background-color: {COLORS['bg_main']}; border-bottom: 1px solid {COLORS['border']};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 0, 0)  # 左边距15px
        layout.setSpacing(0)

        # 左侧：模型指示器
        self.model_indicator = TitleBarModelIndicator()
        self.model_indicator.clicked.connect(self._on_model_indicator_clicked)
        layout.addWidget(self.model_indicator)

        # 弹性间隔（推送窗口控制按钮到右侧）
        layout.addStretch(1)

        # 右侧：窗口控制按钮
        # 最小化按钮
        self.min_btn = self._create_window_button("—")
        layout.addWidget(self.min_btn)

        # 最大化/还原按钮
        self.max_btn = self._create_window_button("□")
        layout.addWidget(self.max_btn)

        # 关闭按钮
        self.close_btn = self._create_window_button("×", is_close=True)
        layout.addWidget(self.close_btn)

        # 连接窗口控制按钮信号
        self.min_btn.clicked.connect(self.minimize_requested.emit)
        self.max_btn.clicked.connect(self.maximize_requested.emit)
        self.close_btn.clicked.connect(self.close_requested.emit)

    def _create_window_button(self, text: str, is_close: bool = False) -> QToolButton:
        """创建窗口控制按钮"""
        btn = QToolButton()
        btn.setText(text)
        btn.setFont(FONTS['title'])
        btn.setFixedSize(48, SIZES['titlebar_height'])
        btn.setCursor(Qt.PointingHandCursor)

        hover_bg = COLORS['accent_red'] if is_close else COLORS['bg_hover']
        hover_text = COLORS['text_inverse'] if is_close else COLORS['text_primary']

        btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                font-size: 16px;
            }}
            QToolButton:hover {{
                background-color: {hover_bg};
                color: {hover_text};
            }}
        """)

        return btn

    def _on_model_indicator_clicked(self):
        """模型指示器点击事件 - 打开模型配置对话框"""
        from .model_config_dialog import ModelConfigDialog
        dialog = ModelConfigDialog(self)
        dialog.exec()

    # ==================== 向后兼容的空方法 ====================
    # 这些方法保留以维持 API 兼容性，但不再执行实际操作

    def add_tab(self, icon: str = "💬", title: str = "新对话") -> int:
        """
        添加标签页（已弃用 - 标签页功能已移除）

        Args:
            icon: 标签页图标
            title: 标签页标题

        Returns:
            int: 固定返回 0（无效 tab_id）
        """
        # 标签页功能已移除，返回占位符 ID
        return 0

    def remove_tab(self, tab_id: int):
        """删除标签页（已弃用 - 标签页功能已移除）"""
        # 标签页功能已移除，方法保留以保持兼容性
        pass

    def set_active_tab(self, tab_id: int):
        """设置激活的标签页（已弃用 - 标签页功能已移除）"""
        # 标签页功能已移除，方法保留以保持兼容性
        pass

    def get_active_tab_id(self) -> int:
        """获取当前激活的标签页ID（已弃用 - 标签页功能已移除）"""
        # 标签页功能已移除，返回占位符 ID
        return 0

    def set_tab_title(self, tab_id: int, title: str):
        """设置标签页标题（已弃用 - 标签页功能已移除）"""
        # 标签页功能已移除，方法保留以保持兼容性
        pass

    def _on_tab_clicked(self, tab_id: int):
        """标签页点击（已弃用 - 标签页功能已移除）"""
        # 标签页功能已移除，方法保留以保持兼容性
        pass

    def _on_tab_close_requested(self, tab_id: int):
        """标签页关闭请求（已弃用 - 标签页功能已移除）"""
        # 标签页功能已移除，方法保留以保持兼容性
        pass

    def mousePressEvent(self, event):
        """鼠标按下事件 - 开始拖动窗口"""
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖动窗口"""
        if not (event.buttons() & Qt.LeftButton):
            return
        if self._drag_start_position is None:
            return

        # 计算移动距离
        diff = event.globalPosition().toPoint() - self._drag_start_position

        # 移动窗口
        window = self.window()
        window.move(window.pos() + diff)

        # 更新起始位置
        self._drag_start_position = event.globalPosition().toPoint()

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件 - 最大化/还原窗口"""
        if event.button() == Qt.LeftButton:
            self.max_btn.click()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel

    app = QApplication(sys.argv)

    # 创建主窗口
    window = QMainWindow()
    window.setWindowTitle("Cherry Studio Title Bar Test")
    window.setWindowFlags(Qt.FramelessWindowHint)  # 无边框窗口
    window.resize(900, 600)

    # 应用全局样式
    from ..styles.cherry_theme import get_global_stylesheet
    window.setStyleSheet(get_global_stylesheet())

    # 创建中心部件
    central = QWidget()
    window.setCentralWidget(central)

    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # 添加标题栏
    title_bar = CherryTitleBar()
    layout.addWidget(title_bar)

    # 测试内容区域
    test_label = QLabel("标题栏测试\n\n点击 + 按钮添加标签页\n中键点击标签页关闭")
    test_label.setAlignment(Qt.AlignCenter)
    test_label.setStyleSheet(f"background: {COLORS['bg_main']}; color: {COLORS['text_secondary']}; padding: 40px; font-size: 16px;")
    layout.addWidget(test_label, stretch=1)

    # 连接窗口控制按钮
    title_bar.min_btn.clicked.connect(window.showMinimized)
    title_bar.max_btn.clicked.connect(
        lambda: window.showNormal() if window.isMaximized() else window.showMaximized()
    )
    title_bar.close_btn.clicked.connect(window.close)

    # 添加初始标签页
    title_bar.add_tab("💬", "新对话 1")

    # 测试新建标签页
    tab_counter = [2]  # 使用列表以便在闭包中修改
    def add_new_tab():
        tab_id = title_bar.add_tab("💬", f"新对话 {tab_counter[0]}")
        tab_counter[0] += 1
        test_label.setText(f"添加了标签页 {tab_id}\n当前激活: {title_bar.get_active_tab_id()}")

    title_bar.new_tab_requested.connect(add_new_tab)

    # 测试标签页切换
    title_bar.tab_changed.connect(
        lambda tid: test_label.setText(f"切换到标签页 {tid}")
    )

    # 测试标签页关闭
    def on_tab_closed(tab_id):
        title_bar.remove_tab(tab_id)
        test_label.setText(f"关闭了标签页 {tab_id}\n当前激活: {title_bar.get_active_tab_id()}")

    title_bar.tab_closed.connect(on_tab_closed)

    window.show()
    sys.exit(app.exec())
