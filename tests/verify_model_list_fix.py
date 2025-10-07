#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证模型列表显示修复
测试所有category都能正常显示
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from components.chat.widgets.model_config_dialog import ModelConfigDialog
from components.chat.controllers.config_controller import ConfigController


def main():
    """验证模型列表修复"""
    app = QApplication.instance() or QApplication(sys.argv)

    print("=" * 80)
    print("验证模型列表显示修复")
    print("=" * 80)

    controller = ConfigController.instance()
    dialog = ModelConfigDialog()

    # 获取硅基流动provider
    siliconflow = controller.get_provider("siliconflow")

    if not siliconflow:
        print("\n[ERROR] 未找到硅基流动provider")
        return 1

    print(f"\n[1] 硅基流动Provider配置:")
    print(f"    ID: {siliconflow.get('id')}")
    print(f"    名称: {siliconflow.get('name')}")
    print(f"    模型数量: {len(siliconflow.get('models', []))}")

    # 检查模型的category
    print(f"\n[2] 模型分类检查:")
    models = siliconflow.get("models", [])
    categories_found = {}
    for model in models:
        category = model.get("category", "未知")
        if category not in categories_found:
            categories_found[category] = []
        categories_found[category].append(model.get("name"))

    for category, model_names in categories_found.items():
        print(f"    [{category}]: {len(model_names)} 个模型")
        for name in model_names:
            print(f"        - {name}")

    # 选择硅基流动provider以触发模型列表加载
    print(f"\n[3] 触发模型列表加载:")
    if hasattr(dialog, "provider_list") and dialog.provider_list.count() > 0:
        # 查找硅基流动在列表中的索引
        siliconflow_index = -1
        for i in range(dialog.provider_list.count()):
            item = dialog.provider_list.item(i)
            widget = dialog.provider_list.itemWidget(item)
            if widget and getattr(widget, "provider_id", None) == "siliconflow":
                siliconflow_index = i
                break

        if siliconflow_index >= 0:
            dialog.provider_list.setCurrentRow(siliconflow_index)
            app.processEvents()
            print(f"    已选择硅基流动 (index: {siliconflow_index})")
        else:
            print(f"    [WARN] 未在列表中找到硅基流动")
    else:
        print(f"    [ERROR] provider_list为空或不存在")

    # 检查UI中的ModelCategoryCard
    print(f"\n[4] UI中的分类卡片检查:")
    category_cards = []
    for widget in dialog.findChildren(object):
        if widget.__class__.__name__ == "ModelCategoryCard":
            category_cards.append(widget)

    print(f"    找到 {len(category_cards)} 个分类卡片")

    if len(category_cards) > 0:
        for i, card in enumerate(category_cards):
            card_name = getattr(card, "category_name", "Unknown")
            card_models = getattr(card, "models", [])
            print(f"    [{i+1}] {card_name}: {len(card_models)} 个模型")

            # 显示前3个模型
            for j, model in enumerate(card_models[:3]):
                model_name = model.get("name", "Unknown")
                print(f"         [{j+1}] {model_name}")
            if len(card_models) > 3:
                print(f"         ... 还有 {len(card_models) - 3} 个模型")
    else:
        print(f"    [ERROR] 没有找到任何分类卡片")

    # 检查所有category是否都已显示
    print(f"\n[5] 分类完整性检查:")
    displayed_categories = {
        getattr(card, "category_name", "") for card in category_cards
    }
    missing_categories = set(categories_found.keys()) - displayed_categories

    if missing_categories:
        print(f"    [ERROR] 以下分类未显示:")
        for cat in missing_categories:
            print(f"        - {cat}")
    else:
        print(f"    [OK] 所有分类都已正确显示")

    # 结论
    print("\n" + "=" * 80)
    print("检查结论:")
    print("=" * 80)

    if len(category_cards) == 0:
        print("[FAIL] 未找到任何分类卡片，模型列表为空")
        return 1
    elif missing_categories:
        print(f"[FAIL] 有 {len(missing_categories)} 个分类未显示")
        return 1
    else:
        print(f"[PASS] 所有 {len(categories_found)} 个分类都已正确显示")
        print(f"       总计 {len(models)} 个模型")
        return 0


if __name__ == "__main__":
    sys.exit(main())
