# -*- coding: utf-8 -*-
"""
Typing Indicator - 三点加载动画
AI正在输入时显示的动画效果
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QPen

from ..styles.cherry_theme import COLORS, SIZES, SPACING


class TypingDot(QLabel):
    """单个跳动的点"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(8, 8)
        self._opacity = 0.3

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        self.update()

    opacity = Property(float, get_opacity, set_opacity)

    def paintEvent(self, event):
        """绘制圆点"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 设置透明度
        color = QColor(COLORS['text_secondary'])
        color.setAlphaF(self._opacity)

        painter.setBrush(color)
        painter.setPen(Qt.NoPen)

        # 绘制圆形
        painter.drawEllipse(0, 0, 8, 8)


class TypingIndicator(QWidget):
    """
    三点加载动画组件
    显示 "● ● ●" 循环跳动动画
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._dots = []
        self._animations = []
        self._timer = None

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING['sm'], SPACING['xs'], SPACING['sm'], SPACING['xs'])
        layout.setSpacing(SPACING['xs'])

        # 创建三个点
        for i in range(3):
            dot = TypingDot()
            self._dots.append(dot)
            layout.addWidget(dot)

            # 创建透明度动画
            animation = QPropertyAnimation(dot, b"opacity")
            animation.setDuration(600)  # 600ms一个循环
            animation.setStartValue(0.3)
            animation.setKeyValueAt(0.5, 1.0)
            animation.setEndValue(0.3)
            animation.setEasingCurve(QEasingCurve.InOutQuad)
            animation.setLoopCount(-1)  # 无限循环

            self._animations.append(animation)

        self.setFixedHeight(24)

    def start(self):
        """开始动画"""
        # 依次启动三个点的动画，每个延迟200ms
        for i, animation in enumerate(self._animations):
            QTimer.singleShot(i * 200, animation.start)

    def stop(self):
        """停止动画"""
        for animation in self._animations:
            animation.stop()

    def hideEvent(self, event):
        """隐藏时停止动画"""
        self.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        """显示时启动动画"""
        self.start()
        super().showEvent(event)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QVBoxLayout

    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("Typing Indicator Test")
    window.resize(300, 200)
    window.setStyleSheet(f"background-color: {COLORS['bg_main']};")

    layout = QVBoxLayout(window)
    layout.setAlignment(Qt.AlignCenter)

    # 添加加载动画
    indicator = TypingIndicator()
    layout.addWidget(indicator)

    window.show()
    sys.exit(app.exec())
