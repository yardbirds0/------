#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试利润表修复效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from utils.table_column_rules import TableColumnRules

def test_profit_fix():
    """测试利润表修复效果"""
    print("=== 测试利润表修复效果 ===")

    # 1. 加载数据
    current_dir = os.path.dirname(os.path.dirname(__file__))
    excel_file = None
    for file in os.listdir(current_dir):
        if file.endswith('.xlsx') and '科电' in file:
            excel_file = os.path.join(current_dir, file)
            break

    if not excel_file:
        print("[错误] 未找到Excel文件")
        return

    print(f"Excel文件: {excel_file}")

    file_manager = FileManager()
    success, message = file_manager.load_excel_files([excel_file])

    if not success:
        print(f"[错误] 数据加载失败: {message}")
        return

    workbook_manager = file_manager.workbook_manager

    # 2. 重新提取数据
    print("\n重新提取数据...")
    workbook_manager.source_items.clear()
    extractor = DataExtractor(workbook_manager)
    success = extractor.extract_all_data()

    if not success:
        print("[错误] 数据提取失败")
        return

    # 3. 查找利润表项目
    profit_items = []
    for source_id, source in workbook_manager.source_items.items():
        if source.sheet_name == "利润表":
            profit_items.append(source)

    print(f"\n利润表项目数量: {len(profit_items)}")

    if len(profit_items) == 0:
        print("[错误] 没有找到利润表项目")
        return

    # 4. 检查期望的列键
    expected_keys = TableColumnRules.get_ordered_column_keys("利润表")
    print(f"期望的列键: {expected_keys}")

    # 5. 分析前几个项目的数据
    print(f"\n前5个项目的数据分析:")
    for i, item in enumerate(profit_items[:5]):
        print(f"\n项目 {i+1}: {item.name}")
        print(f"  行号: {item.row}")

        if hasattr(item, 'data_columns') and item.data_columns:
            actual_keys = list(item.data_columns.keys())
            print(f"  实际列键: {actual_keys}")

            # 检查每个期望的键
            all_matched = True
            for expected_key in expected_keys:
                value = item.data_columns.get(expected_key, None)
                if value is not None:
                    print(f"    '{expected_key}': {value} ✓")
                else:
                    print(f"    '{expected_key}': 缺失 ✗")
                    all_matched = False

            # 显示额外的键（不在期望列表中的）
            extra_keys = set(actual_keys) - set(expected_keys)
            if extra_keys:
                print(f"    额外的键: {list(extra_keys)}")

            if all_matched:
                print(f"    [状态] 所有列都匹配 ✓")
            else:
                print(f"    [状态] 存在缺失列 ✗")

        else:
            print(f"    [警告] data_columns为空或不存在")

    # 6. 总结
    print(f"\n=== 测试总结 ===")

    # 统计有多少项目包含所有期望的列
    complete_items = 0
    partial_items = 0
    empty_items = 0

    for item in profit_items:
        if hasattr(item, 'data_columns') and item.data_columns:
            matched_count = sum(1 for key in expected_keys if key in item.data_columns)
            if matched_count == len(expected_keys):
                complete_items += 1
            elif matched_count > 0:
                partial_items += 1
            else:
                empty_items += 1
        else:
            empty_items += 1

    print(f"总项目数: {len(profit_items)}")
    print(f"完整项目 (包含所有列): {complete_items}")
    print(f"部分项目 (包含部分列): {partial_items}")
    print(f"空白项目 (无数据列): {empty_items}")

    success_rate = complete_items / len(profit_items) if len(profit_items) > 0 else 0
    print(f"成功率: {success_rate:.2%}")

    if success_rate >= 0.8:
        print("🎉 修复成功！利润表数据提取正常。")
        return True
    else:
        print("⚠️ 修复部分成功，但仍需改进。")
        return False

if __name__ == "__main__":
    test_profit_fix()