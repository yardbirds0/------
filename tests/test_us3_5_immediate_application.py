# -*- coding: utf-8 -*-
"""
测试: US3.5 Immediate Model Application
验证模型选择立即应用,无需保存按钮
"""

import sys
import io
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

# 设置stdout为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.chat.widgets.model_config_dialog import ModelConfigDialog, ModelItemWidget
from components.chat.controllers.config_controller import ConfigController


def test_no_save_button():
    """测试: 对话框中没有保存按钮"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 查找所有按钮
    from PySide6.QtWidgets import QPushButton
    save_buttons = []
    for widget in dialog.findChildren(QPushButton):
        text = widget.text().lower()
        if "保存" in text or "save" in text:
            save_buttons.append(widget)

    # 验证没有保存按钮
    assert len(save_buttons) == 0, "对话框中不应有保存按钮"

    dialog.close()
    print("✓ 无保存按钮测试通过")


def test_model_selection_applies_immediately():
    """测试: 模型选择立即应用到ConfigController"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    controller = ConfigController.instance()
    providers = controller.get_providers()

    if len(providers) == 0 or len(providers[0].get("models", [])) == 0:
        print("⚠ 跳过立即应用测试: 无provider或无模型")
        dialog.close()
        return

    # 记录初始模型
    initial_provider, initial_model = controller.get_current_model()

    # 选择第一个provider
    first_item = dialog.provider_list.item(0)
    first_item.setSelected(True)
    QTest.qWait(100)

    provider_id = providers[0].get("id", "")

    # 查找并选择第一个模型
    root_count = dialog.model_tree.topLevelItemCount()
    model_changed = False

    for i in range(root_count):
        category_item = dialog.model_tree.topLevelItem(i)
        if category_item.childCount() > 0:
            first_child = category_item.child(0)
            widget = dialog.model_tree.itemWidget(first_child, 0)
            if isinstance(widget, ModelItemWidget):
                # 点击radio button选择模型
                widget.radio_btn.setChecked(True)
                QTest.qWait(100)

                # 验证ConfigController已立即更新
                new_provider, new_model = controller.get_current_model()

                assert new_provider == provider_id, \
                    f"Provider应立即更新为{provider_id},实际为{new_provider}"
                assert new_model == widget.model_id, \
                    f"Model应立即更新为{widget.model_id},实际为{new_model}"

                model_changed = True
                break

    assert model_changed, "应该成功选择并更新模型"

    dialog.close()
    print("✓ 模型立即应用测试通过")


def test_dialog_remains_open():
    """测试: 选择模型后对话框保持打开"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    controller = ConfigController.instance()
    providers = controller.get_providers()

    if len(providers) == 0 or len(providers[0].get("models", [])) == 0:
        print("⚠ 跳过对话框保持打开测试: 无provider或无模型")
        dialog.close()
        return

    # 选择第一个provider
    first_item = dialog.provider_list.item(0)
    first_item.setSelected(True)
    QTest.qWait(100)

    # 查找并选择第一个模型
    root_count = dialog.model_tree.topLevelItemCount()
    for i in range(root_count):
        category_item = dialog.model_tree.topLevelItem(i)
        if category_item.childCount() > 0:
            first_child = category_item.child(0)
            widget = dialog.model_tree.itemWidget(first_child, 0)
            if isinstance(widget, ModelItemWidget):
                # 点击radio button
                widget.radio_btn.setChecked(True)
                QTest.qWait(100)

                # 验证对话框仍然可见
                assert dialog.isVisible(), "选择模型后对话框应保持打开"
                break

    dialog.close()
    print("✓ 对话框保持打开测试通过")


def test_multiple_selections_without_close():
    """测试: 可以连续选择多个模型,对话框不关闭"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    controller = ConfigController.instance()
    providers = controller.get_providers()

    if len(providers) == 0 or len(providers[0].get("models", [])) == 0:
        print("⚠ 跳过连续选择测试: 无provider或无模型")
        dialog.close()
        return

    # 选择第一个provider
    first_item = dialog.provider_list.item(0)
    first_item.setSelected(True)
    QTest.qWait(100)

    provider_id = providers[0].get("id", "")

    # 收集所有模型widget
    model_widgets = []
    root_count = dialog.model_tree.topLevelItemCount()
    for i in range(root_count):
        category_item = dialog.model_tree.topLevelItem(i)
        for j in range(category_item.childCount()):
            child_item = category_item.child(j)
            widget = dialog.model_tree.itemWidget(child_item, 0)
            if isinstance(widget, ModelItemWidget):
                model_widgets.append(widget)

    # 至少需要2个模型才能测试连续选择
    if len(model_widgets) < 2:
        print("⚠ 跳过连续选择测试: 模型数量不足2个")
        dialog.close()
        return

    # 连续选择前两个模型
    for i in range(min(2, len(model_widgets))):
        widget = model_widgets[i]
        widget.radio_btn.setChecked(True)
        QTest.qWait(100)

        # 验证对话框仍打开
        assert dialog.isVisible(), f"第{i+1}次选择后对话框应保持打开"

        # 验证ConfigController已更新
        new_provider, new_model = controller.get_current_model()
        assert new_model == widget.model_id, f"第{i+1}次选择应立即生效"

    dialog.close()
    print("✓ 连续选择测试通过")


def test_no_workflow_interruption():
    """测试: 模型选择不中断用户工作流"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    controller = ConfigController.instance()
    providers = controller.get_providers()

    if len(providers) == 0 or len(providers[0].get("models", [])) == 0:
        print("⚠ 跳过工作流中断测试: 无provider或无模型")
        dialog.close()
        return

    # 选择provider
    first_item = dialog.provider_list.item(0)
    first_item.setSelected(True)
    QTest.qWait(100)

    # 选择模型
    root_count = dialog.model_tree.topLevelItemCount()
    for i in range(root_count):
        category_item = dialog.model_tree.topLevelItem(i)
        if category_item.childCount() > 0:
            first_child = category_item.child(0)
            widget = dialog.model_tree.itemWidget(first_child, 0)
            if isinstance(widget, ModelItemWidget):
                widget.radio_btn.setChecked(True)
                QTest.qWait(100)

                # 验证对话框仍可交互
                assert dialog.isEnabled(), "选择后对话框应保持可交互"
                assert dialog.isVisible(), "选择后对话框应保持可见"

                # 验证可以继续修改API配置
                assert dialog.api_key_input.isEnabled(), "API密钥输入框应保持可用"
                assert dialog.api_url_input.isEnabled(), "API地址输入框应保持可用"
                break

    dialog.close()
    print("✓ 无工作流中断测试通过")


def run_all_tests():
    """运行所有US3.5测试"""
    print("=" * 60)
    print("US3.5: Immediate Model Application - 测试")
    print("=" * 60)

    test_no_save_button()
    test_model_selection_applies_immediately()
    test_dialog_remains_open()
    test_multiple_selections_without_close()
    test_no_workflow_interruption()

    print("=" * 60)
    print("✅ 所有US3.5测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    # 运行自动化测试
    run_all_tests()

    # 可视化验证说明
    print("\n" + "=" * 60)
    print("可视化验证说明")
    print("=" * 60)
    print("\n验证项:")
    print("1. 对话框中无保存按钮")
    print("2. 选择模型后ConfigController立即更新")
    print("3. 选择模型后对话框保持打开")
    print("4. 可以连续选择多个模型而不关闭对话框")
    print("5. 模型选择不中断用户工作流(可继续修改API配置)")
    print("6. 标题栏模型指示器实时更新(需在主窗口中验证)")
    print("=" * 60)
