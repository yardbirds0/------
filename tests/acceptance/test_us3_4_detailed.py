#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
US3.4详细检查
调查radio button问题
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QRadioButton
from components.chat.widgets.model_config_dialog import ModelConfigDialog
from components.chat.controllers.config_controller import ConfigController


def main():
    """详细检查US3.4模型选择"""
    app = QApplication.instance() or QApplication(sys.argv)

    print("=" * 80)
    print("US3.4 模型选择详细检查")
    print("=" * 80)

    dialog = ModelConfigDialog()
    controller = ConfigController.instance()

    # 1. 检查模型列表容器
    print("\n[1] 模型列表容器检查:")
    if hasattr(dialog, 'models_container_layout'):
        print(f"    models_container_layout: 存在")
        print(f"    Item count: {dialog.models_container_layout.count()}")
    else:
        print("    [WARN] models_container_layout不存在")

    # 2. 检查所有QRadioButton
    print("\n[2] QRadioButton检查:")
    all_radio_buttons = dialog.findChildren(QRadioButton)
    print(f"    找到 {len(all_radio_buttons)} 个 QRadioButton")

    if len(all_radio_buttons) > 0:
        for i, btn in enumerate(all_radio_buttons[:5]):  # 只显示前5个
            print(f"    [{i+1}] Text: '{btn.text()}', Checked: {btn.isChecked()}")
    else:
        print("    [WARN] 没有找到任何QRadioButton!")

    # 3. 检查ModelCategoryCard
    print("\n[3] ModelCategoryCard检查:")
    category_cards = []
    for widget in dialog.findChildren(object):
        if widget.__class__.__name__ == 'ModelCategoryCard':
            category_cards.append(widget)

    print(f"    找到 {len(category_cards)} 个 ModelCategoryCard")

    if len(category_cards) > 0:
        for i, card in enumerate(category_cards[:3]):  # 只显示前3个
            card_name = getattr(card, 'category_name', 'Unknown')
            model_count = len(getattr(card, 'models', []))
            print(f"    [{i+1}] Category: {card_name}, Models: {model_count}")

            # 检查卡片内的radio buttons
            if hasattr(card, 'radio_buttons'):
                print(f"         Radio buttons: {len(card.radio_buttons)}")

    # 4. 选择第一个provider以触发模型列表加载
    print("\n[4] 选择Provider以触发模型列表加载:")
    provider_list = dialog.provider_list if hasattr(dialog, 'provider_list') else None
    if provider_list and provider_list.count() > 0:
        # 选择第一个provider
        provider_list.setCurrentRow(0)
        first_item = provider_list.item(0)
        first_widget = provider_list.itemWidget(first_item)
        if first_widget:
            provider_id = getattr(first_widget, 'provider_id', 'Unknown')
            print(f"    Selected provider: {provider_id}")

        # 等待一下让UI更新
        app.processEvents()

        # 重新检查radio buttons
        print("\n[4.1] 选择Provider后重新检查Radio Buttons:")
        all_radio_buttons = dialog.findChildren(QRadioButton)
        print(f"    找到 {len(all_radio_buttons)} 个 QRadioButton")

        if len(all_radio_buttons) > 0:
            for i, btn in enumerate(all_radio_buttons[:5]):
                print(f"    [{i+1}] Text: '{btn.text()}', Checked: {btn.isChecked()}")
    else:
        print("    [ERROR] provider_list为空或不存在")

    # 5. 检查当前模型
    print("\n[5] 当前模型检查:")
    current_model = controller.get_current_model()
    print(f"    Current model: {current_model}")

    # 6. 检查provider列表
    print("\n[6] Provider列表检查:")
    provider_list = dialog.provider_list if hasattr(dialog, 'provider_list') else None
    if provider_list:
        print(f"    Provider count: {provider_list.count()}")
        if provider_list.currentItem():
            selected_widget = provider_list.itemWidget(provider_list.currentItem())
            if selected_widget:
                provider_id = getattr(selected_widget, 'provider_id', 'Unknown')
                print(f"    Selected provider: {provider_id}")
        else:
            print("    [WARN] No provider selected")
    else:
        print("    [ERROR] provider_list不存在")

    # 7. 检查模型按钮组
    print("\n[7] 模型按钮组检查:")
    if hasattr(dialog, 'model_button_group'):
        print(f"    model_button_group: 存在")
        print(f"    Buttons in group: {len(dialog.model_button_group.buttons())}")
        checked_button = dialog.model_button_group.checkedButton()
        if checked_button:
            print(f"    Checked button: '{checked_button.text()}'")
        else:
            print("    [INFO] No button checked")
    else:
        print("    [WARN] model_button_group不存在")

    # 8. 诊断结论
    print("\n" + "=" * 80)
    print("诊断结论:")
    print("=" * 80)

    has_radio_buttons = len(all_radio_buttons) > 0
    has_category_cards = len(category_cards) > 0

    if has_radio_buttons and has_category_cards:
        print("[OK] 模型选择UI已正确实现")
        print(f"     - {len(category_cards)} 个分类卡片")
        print(f"     - {len(all_radio_buttons)} 个模型选项")
    elif has_category_cards and not has_radio_buttons:
        print("[WARN] 分类卡片存在但没有radio buttons")
        print("       可能原因:")
        print("       1. 模型列表为空（配置问题）")
        print("       2. Radio buttons在卡片创建后才添加（延迟加载）")
        print("       3. 使用了不同的选择机制")
    else:
        print("[ERROR] 模型选择UI缺失")
        print("        需要检查:")
        print("        1. ConfigController是否有默认配置")
        print("        2. _populate_model_tree()是否被调用")
        print("        3. ModelCategoryCard是否正确创建")

    dialog.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
