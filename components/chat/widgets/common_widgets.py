# -*- coding: utf-8 -*-
"""
Cherry Studio Common Widgets
通用UI控件 - Toggle Switch, Labeled Slider, etc.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QSlider, QComboBox, QCheckBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QRect
from PySide6.QtGui import QPainter, QColor, QPen

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING


class ToggleSwitch(QCheckBox):
    """
    iOS风格的Toggle开关
    绿色激活,灰色未激活
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 尺寸参数
        self._width = 48
        self._height = 28
        self._handle_size = 22

        self.setFixedSize(self._width, self._height)
        self.setCursor(Qt.PointingHandCursor)

        # 动画效果(可选,暂时简化)
        self.setStyleSheet("""
            QCheckBox {
                background: transparent;
                border: none;
            }
            QCheckBox::indicator {
                width: 0px;
                height: 0px;
            }
        """)

    def paintEvent(self, event):
        """自定义绘制"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景颜色
        if self.isChecked():
            bg_color = QColor(COLORS['accent_green'])
        else:
            bg_color = QColor(COLORS['border'])

        # 绘制背景轨道
        track_rect = QRect(0, 0, self._width, self._height)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(track_rect, self._height / 2, self._height / 2)

        # 绘制滑块圆圈
        handle_x = self._width - self._handle_size - 3 if self.isChecked() else 3
        handle_y = (self._height - self._handle_size) / 2
        handle_rect = QRect(int(handle_x), int(handle_y), self._handle_size, self._handle_size)

        painter.setBrush(QColor(COLORS['text_inverse']))
        painter.drawEllipse(handle_rect)

    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        # 切换状态
        self.setChecked(not self.isChecked())
        # 触发信号
        self.toggled.emit(self.isChecked())
        event.accept()


class LabeledSlider(QWidget):
    """
    带标签和数值显示的滑块
    标签 - 滑块 - 数值
    """

    # 信号定义
    value_changed = Signal(float)  # 发射浮点数值

    def __init__(self, label: str, min_value: float, max_value: float,
                 default_value: float, step: float = 0.1, integer_mode: bool = False, parent=None):
        super().__init__(parent)

        self._label_text = label
        self._min = min_value
        self._max = max_value
        self._step = step
        self._default = default_value
        self._integer_mode = integer_mode  # 是否以整数显示

        # 计算滑块范围(整数步进)
        self._slider_min = 0
        self._slider_max = int((max_value - min_value) / step)

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING['md'])

        # 滑块 (移除label,让滑块占满左侧)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self._slider_min)
        self.slider.setMaximum(self._slider_max)
        self.slider.setValue(self._value_to_slider(self._default))
        self.slider.setCursor(Qt.PointingHandCursor)

        # 滑块样式
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {COLORS['border']};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent_blue']};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: #2563EB;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['accent_blue']};
                border-radius: 2px;
            }}
        """)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.slider.wheelEvent = lambda event: event.ignore()  # 禁用滚轮
        layout.addWidget(self.slider, stretch=1)

        # 可编辑数值输入框 (替代原来的只读label)
        if self._integer_mode:
            self.value_input = QLineEdit(f"{int(self._default)}")
        else:
            self.value_input = QLineEdit(f"{self._default:.2f}")

        self.value_input.setFont(FONTS['body_small'])
        self.value_input.setStyleSheet(f"""
            QLineEdit {{
                color: {COLORS['text_secondary']};
                background: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 2px 6px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent_blue']};
            }}
        """)
        self.value_input.setFixedWidth(70)  # 稍微加宽以容纳大数字和编辑
        self.value_input.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_input.editingFinished.connect(self._on_input_changed)
        self.value_input.wheelEvent = lambda event: event.ignore()  # 禁用滚轮
        layout.addWidget(self.value_input)

    def _slider_to_value(self, slider_val: int) -> float:
        """滑块值转实际值"""
        return self._min + slider_val * self._step

    def _value_to_slider(self, value: float) -> int:
        """实际值转滑块值"""
        return round((value - self._min) / self._step)

    def _on_slider_changed(self, slider_val: int):
        """滑块值变化"""
        actual_value = self._slider_to_value(slider_val)
        if self._integer_mode:
            self.value_input.setText(f"{int(actual_value)}")
        else:
            self.value_input.setText(f"{actual_value:.2f}")
        self.value_changed.emit(actual_value)

    def _on_input_changed(self):
        """输入框值变化"""
        try:
            # 解析输入值
            input_text = self.value_input.text()
            if self._integer_mode:
                value = float(input_text)  # 先转为float以支持用户输入小数
            else:
                value = float(input_text)

            # 限制在范围内
            value = max(self._min, min(self._max, value))

            # 更新滑块和输入框显示
            self.slider.blockSignals(True)  # 避免循环触发
            self.slider.setValue(self._value_to_slider(value))
            self.slider.blockSignals(False)

            # 更新输入框显示为规范格式
            if self._integer_mode:
                self.value_input.setText(f"{int(value)}")
            else:
                self.value_input.setText(f"{value:.2f}")

            # 发射信号
            self.value_changed.emit(value)

        except ValueError:
            # 输入无效,恢复上一个有效值
            current_value = self.get_value()
            if self._integer_mode:
                self.value_input.setText(f"{int(current_value)}")
            else:
                self.value_input.setText(f"{current_value:.2f}")

    def get_value(self) -> float:
        """获取当前值"""
        return self._slider_to_value(self.slider.value())

    def set_value(self, value: float):
        """设置值"""
        # 更新滑块
        self.slider.blockSignals(True)
        self.slider.setValue(self._value_to_slider(value))
        self.slider.blockSignals(False)

        # 更新输入框显示
        if self._integer_mode:
            self.value_input.setText(f"{int(value)}")
        else:
            self.value_input.setText(f"{value:.2f}")


class LabeledComboBox(QWidget):
    """
    带标签的下拉框
    标签 - 下拉框
    """

    # 信号定义
    selection_changed = Signal(str)  # 选中项文本

    def __init__(self, label: str, items: list, default_index: int = 0, parent=None):
        super().__init__(parent)

        self._label_text = label
        self._items = items
        self._default_index = default_index

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING['md'])

        # 标签
        self.label = QLabel(self._label_text)
        self.label.setFont(FONTS['body'])
        self.label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.label.setFixedWidth(120)
        layout.addWidget(self.label)

        # 下拉框
        self.combobox = QComboBox()
        self.combobox.addItems(self._items)
        self.combobox.setCurrentIndex(self._default_index)
        self.combobox.setFont(FONTS['body'])
        self.combobox.setCursor(Qt.PointingHandCursor)

        # 下拉框样式
        self.combobox.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 6px 12px;
                min-width: 150px;
            }}
            QComboBox:hover {{
                border: 1px solid {COLORS['border_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {COLORS['text_secondary']};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_main']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                selection-background-color: {COLORS['accent_blue']};
                selection-color: {COLORS['text_inverse']};
            }}
        """)

        self.combobox.currentTextChanged.connect(self.selection_changed.emit)
        layout.addWidget(self.combobox, stretch=1)

    def get_current_text(self) -> str:
        """获取当前选中文本"""
        return self.combobox.currentText()

    def set_current_text(self, text: str):
        """设置当前选中项"""
        index = self.combobox.findText(text)
        if index >= 0:
            self.combobox.setCurrentIndex(index)


class LabeledToggle(QWidget):
    """
    带标签的Toggle开关
    标签 - 开关
    """

    # 信号定义
    toggled = Signal(bool)

    def __init__(self, label: str, default_state: bool = True, parent=None):
        super().__init__(parent)

        self._label_text = label
        self._default_state = default_state

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING['md'])

        # 标签 (仅当label非空时显示)
        if self._label_text:
            self.label = QLabel(self._label_text)
            self.label.setFont(FONTS['body'])
            self.label.setStyleSheet(f"color: {COLORS['text_primary']};")
            self.label.setFixedWidth(120)
            layout.addWidget(self.label)

            # 弹性空间 (仅当有label时添加)
            layout.addStretch()

        # Toggle开关
        self.toggle = ToggleSwitch()
        self.toggle.setChecked(self._default_state)
        self.toggle.toggled.connect(self.toggled.emit)
        layout.addWidget(self.toggle)

    def is_checked(self) -> bool:
        """获取开关状态"""
        return self.toggle.isChecked()

    def set_checked(self, checked: bool):
        """设置开关状态"""
        self.toggle.setChecked(checked)

    def set_state(self, state: bool):
        """设置开关状态（别名方法）"""
        self.set_checked(state)


# ==================== 导出符号 ====================

__all__ = [
    'ToggleSwitch',
    'LabeledSlider',
    'LabeledComboBox',
    'LabeledToggle',
]
