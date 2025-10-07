# -*- coding: utf-8 -*-
"""
简单测试温度滑块的重置功能
"""

import sys
sys.path.insert(0, r"D:\Code\快报填写程序")

from PySide6.QtWidgets import QApplication
from components.chat.widgets.settings_panel import CherrySettingsPanel


def test_temperature_reset():
    """测试温度滑块重置"""
    app = QApplication.instance() or QApplication(sys.argv)

    panel = CherrySettingsPanel()

    print(f"初始温度值: {panel.temperature_slider.get_value()}")
    print(f"默认温度值: {panel._default_parameters['temperature']}")

    # 修改温度
    print(f"\n设置温度为 1.5...")
    panel.temperature_slider.set_value(1.5)
    print(f"修改后温度值: {panel.temperature_slider.get_value()}")

    # 重置
    print(f"\n调用 reset_to_defaults()...")
    panel.reset_to_defaults()
    print(f"重置后温度值: {panel.temperature_slider.get_value()}")
    print(f"期望温度值: {panel._default_parameters['temperature']}")

    # 检查
    actual = panel.temperature_slider.get_value()
    expected = panel._default_parameters['temperature']
    diff = abs(actual - expected)

    print(f"\n差值: {diff}")
    if diff < 0.01:
        print("温度重置成功!")
        return True
    else:
        print(f"温度重置失败! 实际值={actual}, 期望值={expected}")
        return False


if __name__ == "__main__":
    try:
        success = test_temperature_reset()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
