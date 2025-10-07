# -*- coding: utf-8 -*-
"""
US4.3 Provider Drag-Drop Reordering Unit Test
测试拖拽重排序的逻辑
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from components.chat.controllers.config_controller import ConfigController


def test_reorder_providers():
    """测试provider重排序功能"""
    print("=" * 60)
    print("US4.3 Provider Reordering Unit Test")
    print("=" * 60)

    # 创建QApplication实例(ConfigController需要)
    app = QApplication(sys.argv)

    # 获取ConfigController实例
    controller = ConfigController.instance()

    # 获取初始顺序
    initial_providers = controller.get_providers()
    print("\n初始Provider顺序:")
    for i, p in enumerate(initial_providers):
        print(f"  {i + 1}. {p['name']:15} (id={p['id']:15}, order={p.get('order', '?')})")

    # 提取provider IDs
    provider_ids = [p["id"] for p in initial_providers]

    # 测试1: 反转顺序
    print("\n测试1: 反转顺序")
    reversed_ids = list(reversed(provider_ids))
    print(f"  新顺序: {reversed_ids}")

    controller.reorder_providers(reversed_ids)

    # 验证顺序
    reordered_providers = controller.get_providers()
    print("  重排后的顺序:")
    for i, p in enumerate(reordered_providers):
        print(f"  {i + 1}. {p['name']:15} (id={p['id']:15}, order={p.get('order', '?')})")

    # 检查顺序是否正确
    actual_ids = [p["id"] for p in reordered_providers]
    if actual_ids == reversed_ids:
        print("  [OK] 顺序反转成功")
    else:
        print(f"  [FAIL] 顺序错误: expected {reversed_ids}, got {actual_ids}")

    # 测试2: 移动第一个到最后
    print("\n测试2: 移动第一个provider到最后")
    new_order = provider_ids[1:] + [provider_ids[0]]
    print(f"  新顺序: {new_order}")

    controller.reorder_providers(new_order)

    # 验证顺序
    reordered_providers = controller.get_providers()
    print("  重排后的顺序:")
    for i, p in enumerate(reordered_providers):
        print(f"  {i + 1}. {p['name']:15} (id={p['id']:15}, order={p.get('order', '?')})")

    # 检查顺序是否正确
    actual_ids = [p["id"] for p in reordered_providers]
    if actual_ids == new_order:
        print("  [OK] 顺序移动成功")
    else:
        print(f"  [FAIL] 顺序错误: expected {new_order}, got {actual_ids}")

    # 测试3: 恢复初始顺序
    print("\n测试3: 恢复初始顺序")
    controller.reorder_providers(provider_ids)

    # 验证顺序
    final_providers = controller.get_providers()
    print("  最终顺序:")
    for i, p in enumerate(final_providers):
        print(f"  {i + 1}. {p['name']:15} (id={p['id']:15}, order={p.get('order', '?')})")

    actual_ids = [p["id"] for p in final_providers]
    if actual_ids == provider_ids:
        print("  [OK] 顺序恢复成功")
    else:
        print(f"  [FAIL] 顺序错误: expected {provider_ids}, got {actual_ids}")

    # 测试4: 验证持久化
    print("\n测试4: 验证配置文件持久化")
    config_path = Path("config/ai_models.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        saved_providers = config.get("providers", [])
        print("  配置文件中的顺序:")
        for i, p in enumerate(saved_providers):
            print(f"  {i + 1}. {p['name']:15} (order={p.get('order', '?')})")

        # 检查order字段是否正确
        order_correct = all(p.get("order") == i for i, p in enumerate(saved_providers))
        if order_correct:
            print("  [OK] Order字段正确且连续")
        else:
            print("  [FAIL] Order字段不正确")
    else:
        print("  [FAIL] 配置文件不存在")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_reorder_providers()
