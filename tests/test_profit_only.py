#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试利润表数据提取
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from utils.table_column_rules import TableColumnRules

def test_profit_statement_only():
    """专门测试利润表"""
    print("=== 专门测试利润表 ===")

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
    print(f"\n重新提取数据...")
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
            for expected_key in expected_keys:
                value = item.data_columns.get(expected_key, None)
                if value is not None:
                    print(f"    '{expected_key}': {value} ✓")
                else:
                    print(f"    '{expected_key}': 缺失 ✗")

            # 显示额外的键（不在期望列表中的）
            extra_keys = set(actual_keys) - set(expected_keys)
            if extra_keys:
                print(f"    额外的键: {list(extra_keys)}")

        else:
            print(f"    [警告] data_columns为空或不存在")

if __name__ == "__main__":
    test_profit_statement_only()