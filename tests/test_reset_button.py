# -*- coding: utf-8 -*-
"""
测试重置参数按钮功能
验证所有参数能否正确重置到默认值
"""

import sys
sys.path.insert(0, r"D:\Code\快报填写程序")

from PySide6.QtWidgets import QApplication
from components.chat.widgets.settings_panel import CherrySettingsPanel


def test_reset_functionality():
    """测试重置功能"""
    print("\n" + "="*50)
    print("测试重置参数按钮")
    print("="*50 + "\n")

    app = QApplication.instance() or QApplication(sys.argv)

    # 创建设置面板
    panel = CherrySettingsPanel()

    # 获取默认参数
    default_params = panel._default_parameters.copy()
    print("默认参数值:")
    for key, value in default_params.items():
        print(f"  {key}: {value}")

    # 启用所有参数组以便测试
    print("\n启用所有参数组...")
    for group in panel._parameter_groups.values():
        group.set_enabled(True)

    # 修改一些参数
    print("修改参数...")
    panel.temperature_slider.set_value(1.5)
    panel.max_tokens_slider.set_value(8000)
    panel.top_p_slider.set_value(0.5)
    panel.model_combo.set_current_text("gpt-4")
    panel.stream_toggle.set_checked(False)

    # 获取修改后的参数 (现在所有组都启用了)
    modified_params = panel.get_parameters()
    print("\n修改后的参数值:")
    for key, value in modified_params.items():
        print(f"  {key}: {value}")

    # 调用重置方法
    print("\n调用 reset_to_defaults()...")
    panel.reset_to_defaults()

    # 验证UI控件是否重置
    print("\n验证UI控件重置结果:")
    ui_checks = {
        'model': panel.model_combo.get_current_text() == default_params['model'],
        'temperature': abs(panel.temperature_slider.get_value() - default_params['temperature']) < 0.01,
        'max_tokens': abs(panel.max_tokens_slider.get_value() - default_params['max_tokens']) < 1,
        'top_p': abs(panel.top_p_slider.get_value() - default_params['top_p']) < 0.01,
        'frequency_penalty': abs(panel.frequency_penalty_slider.get_value() - default_params['frequency_penalty']) < 0.01,
        'presence_penalty': abs(panel.presence_penalty_slider.get_value() - default_params['presence_penalty']) < 0.01,
        'stream': panel.stream_toggle.is_checked() == default_params['stream'],
    }

    all_ui_reset = True
    for key, is_correct in ui_checks.items():
        if not is_correct:
            print(f"  [FAIL] {key} UI未正确重置")
            all_ui_reset = False
        else:
            print(f"  [PASS] {key} UI已正确重置")

    # 验证参数组是否重置为默认禁用状态
    print("\n验证参数组启用状态:")
    all_groups_disabled = True
    for param_name, group in panel._parameter_groups.items():
        if group.is_enabled():
            print(f"  [FAIL] {param_name} 组应该被禁用")
            all_groups_disabled = False
        else:
            print(f"  [PASS] {param_name} 组已正确禁用")

    # 验证内部参数状态
    print("\n验证内部参数字典:")
    internal_params = panel._parameters
    all_internal_reset = True
    for key in default_params:
        if internal_params.get(key) != default_params[key]:
            print(f"  [FAIL] {key} 内部值未正确重置")
            all_internal_reset = False
        else:
            print(f"  [PASS] {key} 内部值已正确重置")

    print("\n" + "="*50)
    if all_ui_reset and all_groups_disabled and all_internal_reset:
        print("测试通过: 所有参数已成功重置到默认值!")
        print("  - UI控件值已重置")
        print("  - 参数组状态已重置")
        print("  - 内部参数字典已重置")
    else:
        print("测试失败:")
        if not all_ui_reset:
            print("  - UI控件值重置失败")
        if not all_groups_disabled:
            print("  - 参数组状态重置失败")
        if not all_internal_reset:
            print("  - 内部参数字典重置失败")
    print("="*50 + "\n")

    return all_ui_reset and all_groups_disabled and all_internal_reset


if __name__ == "__main__":
    try:
        success = test_reset_functionality()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
