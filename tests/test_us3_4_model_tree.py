# -*- coding: utf-8 -*-
"""
测试: US3.4 Right Panel - Model Selection Tree
验证模型选择树的UI和功能
"""

import sys
import io
from pathlib import Path
from PySide6.QtWidgets import QApplication, QTreeWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

# 设置stdout为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.chat.widgets.model_config_dialog import ModelConfigDialog, ModelItemWidget
from components.chat.controllers.config_controller import ConfigController


def test_model_list_section_structure():
    """测试: 模型列表区域结构"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证模型列表section存在
    assert hasattr(dialog, 'model_list_section'), "模型列表section应存在"
    assert hasattr(dialog, 'model_tree'), "模型树应存在"

    # 验证树形控件属性
    assert dialog.model_tree.isHeaderHidden(), "树形控件header应隐藏"
    assert dialog.model_tree.rootIsDecorated(), "树形控件应显示展开/收起箭头"

    dialog.close()
    print("✓ 模型列表区域结构测试通过")


def test_footer_section():
    """测试: 底部按钮区域"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 查找底部按钮
    manage_btn = None
    add_btn = None

    # 遍历所有按钮查找
    from PySide6.QtWidgets import QPushButton
    for widget in dialog.findChildren(QPushButton):
        if widget.text() == "管理模型":
            manage_btn = widget
        elif widget.text() == "添加模型":
            add_btn = widget

    # 验证按钮存在
    assert manage_btn is not None, "管理模型按钮应存在"
    assert add_btn is not None, "添加模型按钮应存在"

    # 验证按钮尺寸 (100×36px)
    assert manage_btn.size().width() == 100, f"管理模型按钮宽度应为100px,实际{manage_btn.size().width()}px"
    assert manage_btn.size().height() == 36, f"管理模型按钮高度应为36px,实际{manage_btn.size().height()}px"
    assert add_btn.size().width() == 100, f"添加模型按钮宽度应为100px,实际{add_btn.size().width()}px"
    assert add_btn.size().height() == 36, f"添加模型按钮高度应为36px,实际{add_btn.size().height()}px"

    dialog.close()
    print("✓ 底部按钮区域测试通过")


def test_model_tree_population():
    """测试: 模型树填充"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 获取第一个provider
    controller = ConfigController.instance()
    providers = controller.get_providers()

    if len(providers) == 0:
        print("⚠ 跳过模型树填充测试: 无provider")
        dialog.close()
        return

    first_provider = providers[0]
    provider_id = first_provider.get("id", "")

    # 选择provider触发模型树加载
    if dialog.provider_list.count() > 0:
        first_item = dialog.provider_list.item(0)
        first_item.setSelected(True)
        QTest.qWait(100)

    # 验证模型树已填充
    root_count = dialog.model_tree.topLevelItemCount()

    # 如果provider有模型,应该至少有1个category
    models = first_provider.get("models", [])
    if len(models) > 0:
        assert root_count > 0, f"Provider有{len(models)}个模型,应至少有1个category,实际{root_count}个"

    dialog.close()
    print(f"✓ 模型树填充测试通过: {root_count}个category")


def test_model_grouping_by_category():
    """测试: 模型按category分组"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 获取第一个provider
    controller = ConfigController.instance()
    providers = controller.get_providers()

    if len(providers) == 0 or len(providers[0].get("models", [])) == 0:
        print("⚠ 跳过分组测试: 无provider或无模型")
        dialog.close()
        return

    # 选择第一个provider
    first_item = dialog.provider_list.item(0)
    first_item.setSelected(True)
    QTest.qWait(100)

    # 检查是否有category项
    root_count = dialog.model_tree.topLevelItemCount()
    if root_count > 0:
        # 获取第一个category
        first_category = dialog.model_tree.topLevelItem(0)
        category_name = first_category.text(0)

        # 验证category有子项
        child_count = first_category.childCount()
        assert child_count > 0, f"Category '{category_name}'应有子项"

        # 验证子项是模型widget
        if child_count > 0:
            first_child = first_category.child(0)
            widget = dialog.model_tree.itemWidget(first_child, 0)
            assert widget is not None, "模型子项应有自定义widget"
            assert isinstance(widget, ModelItemWidget), "模型widget应为ModelItemWidget类型"

    dialog.close()
    print("✓ 模型分组测试通过")


def test_model_item_widget_structure():
    """测试: ModelItemWidget结构"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 选择第一个provider
    if dialog.provider_list.count() > 0:
        first_item = dialog.provider_list.item(0)
        first_item.setSelected(True)
        QTest.qWait(100)

    # 查找第一个模型widget
    model_widget = None
    root_count = dialog.model_tree.topLevelItemCount()

    for i in range(root_count):
        category_item = dialog.model_tree.topLevelItem(i)
        if category_item.childCount() > 0:
            first_child = category_item.child(0)
            widget = dialog.model_tree.itemWidget(first_child, 0)
            if isinstance(widget, ModelItemWidget):
                model_widget = widget
                break

    if model_widget is None:
        print("⚠ 跳过ModelItemWidget结构测试: 未找到模型widget")
        dialog.close()
        return

    # 验证widget结构
    assert hasattr(model_widget, 'radio_btn'), "ModelItemWidget应有radio_btn"
    assert hasattr(model_widget, 'model_id'), "ModelItemWidget应有model_id"
    assert hasattr(model_widget, 'model_name'), "ModelItemWidget应有model_name"

    dialog.close()
    print("✓ ModelItemWidget结构测试通过")


def test_active_model_preselected():
    """测试: 当前激活模型预选中"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    controller = ConfigController.instance()
    current_provider, current_model = controller.get_current_model()

    if not current_provider or not current_model:
        print("⚠ 跳过预选中测试: 无当前模型")
        dialog.close()
        return

    # 选择当前provider
    for i in range(dialog.provider_list.count()):
        item = dialog.provider_list.item(i)
        provider_id = item.data(Qt.UserRole)
        if provider_id == current_provider:
            item.setSelected(True)
            QTest.qWait(100)
            break

    # 查找当前模型的widget,验证radio button被选中
    found_active = False
    root_count = dialog.model_tree.topLevelItemCount()

    for i in range(root_count):
        category_item = dialog.model_tree.topLevelItem(i)
        for j in range(category_item.childCount()):
            child_item = category_item.child(j)
            widget = dialog.model_tree.itemWidget(child_item, 0)
            if isinstance(widget, ModelItemWidget):
                if widget.model_id == current_model:
                    assert widget.radio_btn.isChecked(), f"当前模型{current_model}的radio button应被选中"
                    found_active = True
                    break
        if found_active:
            break

    assert found_active, f"应找到当前激活的模型{current_model}"

    dialog.close()
    print(f"✓ 激活模型预选中测试通过: {current_model}")


def test_model_selection_updates_config():
    """测试: 模型选择立即更新ConfigController"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 获取第一个provider
    controller = ConfigController.instance()
    providers = controller.get_providers()

    if len(providers) == 0 or len(providers[0].get("models", [])) == 0:
        print("⚠ 跳过选择更新测试: 无provider或无模型")
        dialog.close()
        return

    first_provider = providers[0]
    provider_id = first_provider.get("id", "")
    models = first_provider.get("models", [])
    test_model_id = models[0].get("id", "")

    # 选择provider
    first_item = dialog.provider_list.item(0)
    first_item.setSelected(True)
    QTest.qWait(100)

    # 查找并点击第一个模型
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

                # 验证ConfigController已更新
                new_provider, new_model = controller.get_current_model()
                assert new_provider == provider_id, f"Provider应为{provider_id},实际为{new_provider}"
                assert new_model == widget.model_id, f"Model应为{widget.model_id},实际为{new_model}"
                break

    dialog.close()
    print("✓ 模型选择更新ConfigController测试通过")


def test_visual_styling():
    """测试: 视觉样式符合Cherry Studio主题"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证模型树样式
    tree_style = dialog.model_tree.styleSheet()
    assert "border-radius" in tree_style, "模型树应有圆角样式"

    # 验证底部footer存在border-top
    from PySide6.QtWidgets import QPushButton
    manage_btn = None
    for widget in dialog.findChildren(QPushButton):
        if widget.text() == "管理模型":
            manage_btn = widget
            break

    if manage_btn:
        # 验证按钮有样式
        btn_style = manage_btn.styleSheet()
        assert "border-radius" in btn_style, "按钮应有圆角样式"

    dialog.close()
    print("✓ 视觉样式测试通过")


def run_all_tests():
    """运行所有US3.4测试"""
    print("=" * 60)
    print("US3.4: Right Panel - Model Selection Tree - 测试")
    print("=" * 60)

    test_model_list_section_structure()
    test_footer_section()
    test_model_tree_population()
    test_model_grouping_by_category()
    test_model_item_widget_structure()
    test_active_model_preselected()
    test_model_selection_updates_config()
    test_visual_styling()

    print("=" * 60)
    print("✅ 所有US3.4测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    # 运行自动化测试
    run_all_tests()

    # 可视化验证说明
    print("\n" + "=" * 60)
    print("可视化验证说明")
    print("=" * 60)
    print("\n验证项:")
    print("1. 模型列表标签: '模型列表' (14px, weight 500)")
    print("2. QTreeWidget: 隐藏header, 显示展开/收起箭头")
    print("3. 模型分组: 按category分组 (e.g., 'GPT-4', 'Claude')")
    print("4. 模型项: Radio button + 模型名 + 元数据徽章 (e.g., '128K')")
    print("5. 当前激活模型: Radio button预选中")
    print("6. 底部按钮: '管理模型'(outlined) + '添加模型'(primary), 各100×36px")
    print("7. 模型选择: 立即更新ConfigController, 无需保存按钮")
    print("8. 整体风格: 与Provider配置面板一致")
    print("=" * 60)
