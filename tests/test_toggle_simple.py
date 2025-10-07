# -*- coding: utf-8 -*-
"""
测试Toggle开关功能
"""
import sys
sys.path.insert(0, r"D:\Code\快报填写程序")

from components.chat.widgets.common_widgets import ToggleSwitch, LabeledToggle
from components.chat.widgets.settings_panel import SettingsGroup


def test_toggle():
    """测试toggle功能"""
    # 测试1: ToggleSwitch基础功能
    toggle = ToggleSwitch()
    toggle.setChecked(False)
    print(f"[TEST 1] ToggleSwitch created, initial state: {toggle.isChecked()}")

    # 模拟点击
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QPoint, Qt, QEvent

    # 创建鼠标事件
    pos = QPoint(24, 14)  # 中心位置
    event = QMouseEvent(
        QEvent.MouseButtonPress,
        pos,
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier
    )

    # 触发点击
    toggle.mousePressEvent(event)
    print(f"[TEST 1] After click, state: {toggle.isChecked()}")
    assert toggle.isChecked() == True, "Toggle should be checked after click"
    print("[TEST 1] PASSED - ToggleSwitch click works!")

    # 测试2: LabeledToggle
    labeled_toggle = LabeledToggle(label="Test", default_state=True)
    print(f"[TEST 2] LabeledToggle created, initial state: {labeled_toggle.is_checked()}")

    # 测试set_state方法
    labeled_toggle.set_state(False)
    print(f"[TEST 2] After set_state(False): {labeled_toggle.is_checked()}")
    assert labeled_toggle.is_checked() == False, "set_state should work"
    print("[TEST 2] PASSED - LabeledToggle set_state works!")

    # 测试3: 无标签的Toggle
    empty_label_toggle = LabeledToggle(label="", default_state=False)
    print(f"[TEST 3] Empty label toggle created, state: {empty_label_toggle.is_checked()}")
    print("[TEST 3] PASSED - Empty label toggle works!")

    # 测试4: SettingsGroup
    group = SettingsGroup("Test Group", default_enabled=False, show_toggle=True)
    print(f"[TEST 4] SettingsGroup created, enabled: {group.is_enabled()}")

    group.set_enabled(True)
    print(f"[TEST 4] After set_enabled(True): {group.is_enabled()}")
    assert group.is_enabled() == True, "set_enabled should work"
    print("[TEST 4] PASSED - SettingsGroup works!")

    print("\n" + "="*50)
    print("ALL TESTS PASSED!")
    print("="*50)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    try:
        test_toggle()
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
