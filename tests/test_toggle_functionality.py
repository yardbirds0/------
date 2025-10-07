# -*- coding: utf-8 -*-
"""
测试Toggle开关功能
验证所有控件的点击和状态变化是否正常
"""

import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

# 添加项目路径
sys.path.insert(0, r"D:\Code\快报填写程序")

from components.chat.widgets.common_widgets import ToggleSwitch, LabeledToggle, LabeledSlider
from components.chat.widgets.settings_panel import SettingsGroup


def test_toggle_switch():
    """测试基础ToggleSwitch"""
    print("\n=== 测试 ToggleSwitch ===")

    app = QApplication.instance() or QApplication(sys.argv)

    widget = QWidget()
    layout = QVBoxLayout(widget)

    # 创建toggle
    toggle = ToggleSwitch()
    toggle.setChecked(False)

    # 连接信号
    def on_toggled(checked):
        print(f"Toggle状态变化: {checked}")

    toggle.toggled.connect(on_toggled)

    label = QLabel("点击下方的Toggle开关")
    layout.addWidget(label)
    layout.addWidget(toggle)

    widget.setWindowTitle("ToggleSwitch测试")
    widget.resize(300, 100)
    widget.show()

    print("✓ ToggleSwitch创建成功")
    print(f"✓ 初始状态: {toggle.isChecked()}")

    # 不自动退出,让用户手动测试点击
    # app.exec()


def test_labeled_toggle():
    """测试LabeledToggle"""
    print("\n=== 测试 LabeledToggle ===")

    app = QApplication.instance() or QApplication(sys.argv)

    widget = QWidget()
    layout = QVBoxLayout(widget)

    # 创建带标签的toggle
    toggle1 = LabeledToggle(label="流式输出", default_state=True)
    toggle2 = LabeledToggle(label="", default_state=False)  # 无标签

    def on_toggle1(checked):
        print(f"Toggle1(带标签)状态: {checked}")

    def on_toggle2(checked):
        print(f"Toggle2(无标签)状态: {checked}")

    toggle1.toggled.connect(on_toggle1)
    toggle2.toggled.connect(on_toggle2)

    layout.addWidget(QLabel("带标签的Toggle:"))
    layout.addWidget(toggle1)
    layout.addWidget(QLabel("无标签的Toggle:"))
    layout.addWidget(toggle2)

    widget.setWindowTitle("LabeledToggle测试")
    widget.resize(400, 150)
    widget.show()

    print("✓ LabeledToggle创建成功")
    print(f"✓ Toggle1初始状态: {toggle1.is_checked()}")
    print(f"✓ Toggle2初始状态: {toggle2.is_checked()}")

    # 测试set_state方法
    toggle1.set_state(False)
    print(f"✓ set_state测试成功: {toggle1.is_checked()}")


def test_settings_group():
    """测试SettingsGroup的enable toggle"""
    print("\n=== 测试 SettingsGroup ===")

    app = QApplication.instance() or QApplication(sys.argv)

    widget = QWidget()
    layout = QVBoxLayout(widget)

    # 创建带toggle的参数组
    group1 = SettingsGroup("温度 (Temperature)", default_enabled=False, show_toggle=True)
    slider1 = LabeledSlider(
        label="Temperature",
        min_value=0.0,
        max_value=2.0,
        default_value=0.7,
        step=0.1
    )
    group1.add_widget(slider1)

    # 创建不带toggle的参数组
    group2 = SettingsGroup("模型设置", show_toggle=False)

    def on_enabled_changed(enabled):
        print(f"参数组启用状态变化: {enabled}")

    group1.enabled_changed.connect(on_enabled_changed)

    layout.addWidget(group1)
    layout.addWidget(group2)

    widget.setWindowTitle("SettingsGroup测试")
    widget.resize(400, 300)
    widget.show()

    print("✓ SettingsGroup创建成功")
    print(f"✓ Group1初始启用状态: {group1.is_enabled()}")
    print(f"✓ Group1有toggle: {group1._show_toggle}")
    print(f"✓ Group2有toggle: {group2._show_toggle}")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("开始测试Toggle功能")
    print("=" * 50)

    try:
        test_toggle_switch()
        test_labeled_toggle()
        test_settings_group()

        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
