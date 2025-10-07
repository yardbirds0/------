# -*- coding: utf-8 -*-
"""
Cherry Studio Settings Panel
设置面板 - 7组AI参数配置
"""

from typing import Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QFrame, QPushButton
)
from PySide6.QtCore import Qt, Signal

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING
from .common_widgets import LabeledSlider, LabeledComboBox, LabeledToggle


class SettingsGroup(QFrame):
    """
    设置组
    包含标题和多个设置项
    支持启用/禁用切换
    """

    # 信号定义
    enabled_changed = Signal(bool)  # 启用状态变化

    def __init__(self, title: str, default_enabled: bool = True, show_toggle: bool = True, parent=None):
        super().__init__(parent)

        self._title = title
        self._enabled = default_enabled
        self._show_toggle = show_toggle
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_main']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius']}px;
            }}
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        self.layout.setSpacing(SPACING['md'])

        # 标题行 (包含标题和开关)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(SPACING['sm'])

        # 标题
        title_label = QLabel(self._title)
        title_label.setFont(FONTS['subtitle'])
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        title_layout.addWidget(title_label, stretch=1)

        # 启用/禁用开关 (如果需要显示)
        if self._show_toggle:
            self.enable_toggle = LabeledToggle(
                label="",  # 无标签,只显示开关
                default_state=self._enabled
            )
            self.enable_toggle.toggled.connect(self._on_enabled_changed)
            title_layout.addWidget(self.enable_toggle)

        self.layout.addLayout(title_layout)

    def add_widget(self, widget: QWidget):
        """添加设置项"""
        self.layout.addWidget(widget)

    def _on_enabled_changed(self, enabled: bool):
        """启用状态变化"""
        self._enabled = enabled
        self.enabled_changed.emit(enabled)

    def is_enabled(self) -> bool:
        """获取启用状态"""
        return self._enabled

    def set_enabled(self, enabled: bool):
        """设置启用状态"""
        self._enabled = enabled
        if self._show_toggle and hasattr(self, 'enable_toggle'):
            self.enable_toggle.blockSignals(True)
            self.enable_toggle.set_state(enabled)
            self.enable_toggle.blockSignals(False)


class CherrySettingsPanel(QWidget):
    """
    Cherry Studio 设置面板
    包含所有AI参数配置,参数立即生效
    """

    # 信号定义
    parameter_changed = Signal(str, object)  # (parameter_name, value)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 默认参数值（用于重置）
        self._default_parameters: Dict[str, Any] = {
            'model': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 2000,
            'top_p': 1.0,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
            'stream': True,
        }

        # 当前参数值
        self._parameters: Dict[str, Any] = self._default_parameters.copy()

        # 参数组引用 (用于检查启用状态)
        self._parameter_groups: Dict[str, SettingsGroup] = {}

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"background: {COLORS['bg_sidebar']}; border: none;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        scroll_layout.setSpacing(SPACING['md'])
        scroll_layout.setAlignment(Qt.AlignTop)

        # ==================== Group 2: Stream Output ====================
        group2 = SettingsGroup("流式输出 (Stream)", show_toggle=False)  # 流式输出不需要toggle

        self.stream_toggle = LabeledToggle(
            label="流式输出",
            default_state=True
        )
        self.stream_toggle.toggled.connect(
            lambda value: self._on_parameter_changed('stream', value)
        )
        group2.add_widget(self.stream_toggle)

        stream_desc = QLabel("启用后,AI将逐字输出回复,提供更好的交互体验。")
        stream_desc.setFont(FONTS['caption'])
        stream_desc.setWordWrap(True)
        stream_desc.setStyleSheet(f"color: {COLORS['text_tertiary']}; border: none; padding: 0px;")
        group2.add_widget(stream_desc)

        scroll_layout.addWidget(group2)

        # ==================== Group 3: Temperature ====================
        group3 = SettingsGroup("温度 (Temperature)", default_enabled=False)  # 默认禁用

        self.temperature_slider = LabeledSlider(
            label="Temperature",
            min_value=0.0,
            max_value=2.0,
            default_value=0.7,
            step=0.1
        )
        self.temperature_slider.value_changed.connect(
            lambda value: self._on_parameter_changed('temperature', value)
        )
        group3.add_widget(self.temperature_slider)

        # 说明文字
        temp_desc = QLabel("控制输出的随机性。较高的值使输出更随机,较低的值使输出更确定。")
        temp_desc.setFont(FONTS['caption'])
        temp_desc.setWordWrap(True)
        temp_desc.setStyleSheet(f"color: {COLORS['text_tertiary']}; border: none; padding: 0px;")
        group3.add_widget(temp_desc)

        scroll_layout.addWidget(group3)
        self._parameter_groups['temperature'] = group3  # 存储引用

        # ==================== Group 4: Max Tokens ====================
        group4 = SettingsGroup("最大令牌数 (Max Tokens)", default_enabled=False)  # 默认禁用

        self.max_tokens_slider = LabeledSlider(
            label="Max Tokens",
            min_value=500,
            max_value=32000,
            default_value=2000,
            step=100,
            integer_mode=True
        )
        self.max_tokens_slider.value_changed.connect(
            lambda value: self._on_parameter_changed('max_tokens', int(value))
        )
        group4.add_widget(self.max_tokens_slider)

        max_desc = QLabel("生成的最大令牌数量。更高的值允许更长的回复。")
        max_desc.setFont(FONTS['caption'])
        max_desc.setWordWrap(True)
        max_desc.setStyleSheet(f"color: {COLORS['text_tertiary']}; border: none; padding: 0px;")
        group4.add_widget(max_desc)

        scroll_layout.addWidget(group4)
        self._parameter_groups['max_tokens'] = group4  # 存储引用

        # ==================== Group 5: Top P ====================
        group5 = SettingsGroup("核采样 (Top P)", default_enabled=False)  # 默认禁用

        self.top_p_slider = LabeledSlider(
            label="Top P",
            min_value=0.0,
            max_value=1.0,
            default_value=1.0,
            step=0.05
        )
        self.top_p_slider.value_changed.connect(
            lambda value: self._on_parameter_changed('top_p', value)
        )
        group5.add_widget(self.top_p_slider)

        top_p_desc = QLabel("控制输出的多样性。较低的值使输出更集中,较高的值使输出更多样。")
        top_p_desc.setFont(FONTS['caption'])
        top_p_desc.setWordWrap(True)
        top_p_desc.setStyleSheet(f"color: {COLORS['text_tertiary']}; border: none; padding: 0px;")
        group5.add_widget(top_p_desc)

        scroll_layout.addWidget(group5)
        self._parameter_groups['top_p'] = group5  # 存储引用

        # ==================== Group 6: Frequency Penalty ====================
        group6 = SettingsGroup("频率惩罚 (Frequency Penalty)", default_enabled=False)  # 默认禁用

        self.frequency_penalty_slider = LabeledSlider(
            label="Frequency Penalty",
            min_value=-2.0,
            max_value=2.0,
            default_value=0.0,
            step=0.1
        )
        self.frequency_penalty_slider.value_changed.connect(
            lambda value: self._on_parameter_changed('frequency_penalty', value)
        )
        group6.add_widget(self.frequency_penalty_slider)

        freq_desc = QLabel("减少重复出现的词语。正值降低重复,负值增加重复。")
        freq_desc.setFont(FONTS['caption'])
        freq_desc.setWordWrap(True)
        freq_desc.setStyleSheet(f"color: {COLORS['text_tertiary']}; border: none; padding: 0px;")
        group6.add_widget(freq_desc)

        scroll_layout.addWidget(group6)
        self._parameter_groups['frequency_penalty'] = group6  # 存储引用

        # ==================== Group 7: Presence Penalty ====================
        group7 = SettingsGroup("存在惩罚 (Presence Penalty)", default_enabled=False)  # 默认禁用

        self.presence_penalty_slider = LabeledSlider(
            label="Presence Penalty",
            min_value=-2.0,
            max_value=2.0,
            default_value=0.0,
            step=0.1
        )
        self.presence_penalty_slider.value_changed.connect(
            lambda value: self._on_parameter_changed('presence_penalty', value)
        )
        group7.add_widget(self.presence_penalty_slider)

        pres_desc = QLabel("鼓励谈论新话题。正值增加新话题,负值减少新话题。")
        pres_desc.setFont(FONTS['caption'])
        pres_desc.setWordWrap(True)
        pres_desc.setStyleSheet(f"color: {COLORS['text_tertiary']}; border: none; padding: 0px;")
        group7.add_widget(pres_desc)

        scroll_layout.addWidget(group7)
        self._parameter_groups['presence_penalty'] = group7  # 存储引用

        # ==================== 重置按钮 ====================
        reset_button = QPushButton("重置参数")
        reset_button.setFont(FONTS['body'])
        reset_button.setCursor(Qt.PointingHandCursor)
        reset_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 10px 20px;
                margin-top: {SPACING['lg']}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                border-color: {COLORS['accent_blue']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['bg_active']};
            }}
        """)
        reset_button.clicked.connect(self.reset_to_defaults)
        scroll_layout.addWidget(reset_button)

        # 添加底部空间
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def _on_parameter_changed(self, param_name: str, value: Any):
        """参数变更处理"""
        # 更新内部状态
        self._parameters[param_name] = value

        # 立即发射信号(无需Apply按钮)
        self.parameter_changed.emit(param_name, value)

    def get_parameters(self) -> Dict[str, Any]:
        """
        获取所有启用的参数
        只返回对应参数组被启用的参数
        """
        enabled_params = {}

        for param_name, value in self._parameters.items():
            # 检查该参数是否有对应的组
            if param_name in self._parameter_groups:
                # 只有组启用时才包含该参数
                if self._parameter_groups[param_name].is_enabled():
                    enabled_params[param_name] = value
            else:
                # 没有对应组的参数(如model和stream)总是包含
                enabled_params[param_name] = value

        return enabled_params

    def set_parameter(self, param_name: str, value: Any):
        """设置单个参数"""
        if param_name not in self._parameters:
            return

        self._parameters[param_name] = value

        # 更新UI控件
        if param_name == 'model':
            pass  # 模型设置已被标题栏模型指示器替代
        elif param_name == 'temperature':
            self.temperature_slider.set_value(value)
        elif param_name == 'max_tokens':
            self.max_tokens_slider.set_value(value)
        elif param_name == 'top_p':
            self.top_p_slider.set_value(value)
        elif param_name == 'frequency_penalty':
            self.frequency_penalty_slider.set_value(value)
        elif param_name == 'presence_penalty':
            self.presence_penalty_slider.set_value(value)
        elif param_name == 'stream':
            self.stream_toggle.set_checked(value)

    def reset_to_defaults(self):
        """重置所有参数到默认值"""
        # 模型设置已被标题栏模型指示器替代，不再在此处理

        # Reset sliders
        self.temperature_slider.set_value(self._default_parameters['temperature'])
        self.max_tokens_slider.set_value(self._default_parameters['max_tokens'])
        self.top_p_slider.set_value(self._default_parameters['top_p'])
        self.frequency_penalty_slider.set_value(self._default_parameters['frequency_penalty'])
        self.presence_penalty_slider.set_value(self._default_parameters['presence_penalty'])

        # Reset stream toggle
        self.stream_toggle.set_checked(self._default_parameters['stream'])

        # Reset parameter groups to default enabled states (all disabled except model and stream)
        for param_name, group in self._parameter_groups.items():
            group.set_enabled(False)  # All parameter groups are disabled by default

        # Update internal state
        self._parameters = self._default_parameters.copy()

        # Emit signals for all changed parameters
        for param_name, value in self._default_parameters.items():
            self.parameter_changed.emit(param_name, value)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QHBoxLayout

    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("Cherry Studio Settings Panel Test")
    window.resize(800, 700)

    layout = QHBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # 添加设置面板
    settings = CherrySettingsPanel()
    settings.setFixedWidth(SIZES['sidebar_width'])
    layout.addWidget(settings)

    # 测试内容区域
    test_label = QLabel("设置面板测试\n\n调整左侧参数,参数立即生效")
    test_label.setAlignment(Qt.AlignCenter)
    test_label.setStyleSheet(f"""
        background: {COLORS['bg_main']};
        color: {COLORS['text_secondary']};
        padding: 40px;
        font-size: 16px;
    """)
    layout.addWidget(test_label, stretch=1)

    # 连接信号测试
    def on_param_changed(param_name, value):
        params = settings.get_parameters()
        text = f"参数变更: {param_name} = {value}\n\n当前所有参数:\n"
        for k, v in params.items():
            text += f"{k}: {v}\n"
        test_label.setText(text)

    settings.parameter_changed.connect(on_param_changed)

    window.show()
    sys.exit(app.exec())
