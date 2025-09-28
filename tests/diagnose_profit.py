#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
利润表专项诊断脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from utils.table_column_rules import TableColumnRules

def diagnose_profit_statement():
    """专项诊断利润表"""
    print("=== 利润表专项诊断 ===")

    # 1. 检查利润表的TableColumnRules定义
    print("\n[1] 利润表标准定义:")
    profit_rules = TableColumnRules.get_table_rule("利润表")
    if profit_rules:
        print(f"  显示名称: {profit_rules['display_name']}")
        print(f"  主要列: {profit_rules['primary_column']}")
        column_keys = TableColumnRules.get_ordered_column_keys("利润表")
        print(f"  标准列键: {column_keys}")
    else:
        print("  [错误] 找不到利润表规则定义")
        return

    # 2. 查找Excel文件
    current_dir = os.path.dirname(os.path.dirname(__file__))
    excel_file = None
    for file in os.listdir(current_dir):
        if file.endswith('.xlsx') and '科电' in file:
            excel_file = os.path.join(current_dir, file)
            break

    if not excel_file:
        print("[错误] 未找到Excel文件")
        return

    print(f"\n[2] 数据提取测试:")
    print(f"  Excel文件: {excel_file}")

    # 3. 数据提取
    file_manager = FileManager()
    success, message = file_manager.load_excel_files([excel_file])

    if not success:
        print(f"  [错误] 数据加载失败: {message}")
        return

    workbook_manager = file_manager.workbook_manager
    extractor = DataExtractor(workbook_manager)

    # 4. 查找利润表工作表
    profit_sheets = []
    for source_id, source in workbook_manager.source_items.items():
        sheet_name = source.sheet_name
        table_type = TableColumnRules.detect_table_type(sheet_name)
        if table_type == "利润表":
            if sheet_name not in profit_sheets:
                profit_sheets.append(sheet_name)

    print(f"\n[3] 利润表工作表:")
    for sheet in profit_sheets:
        print(f"  - {sheet}")

    if not profit_sheets:
        print("  [错误] 没有找到利润表工作表")
        return

    # 5. 重新提取数据
    success = extractor.extract_all_data()
    if not success:
        print("  [错误] 数据提取失败")
        return

    # 6. 分析利润表数据
    print(f"\n[4] 利润表数据分析:")
    for sheet_name in profit_sheets:
        print(f"\n  工作表: {sheet_name}")

        # 找到该工作表的项目
        sheet_items = []
        for source_id, source in workbook_manager.source_items.items():
            if source.sheet_name == sheet_name:
                sheet_items.append(source)

        print(f"    项目数量: {len(sheet_items)}")

        # 分析前几个项目的数据
        for i, item in enumerate(sheet_items[:5]):
            print(f"\n    项目 {i+1}: {item.name}")
            print(f"      行号: {item.row}")

            if hasattr(item, 'data_columns') and item.data_columns:
                print(f"      data_columns: {item.data_columns}")

                # 检查键名匹配
                expected_keys = TableColumnRules.get_ordered_column_keys("利润表")
                for expected_key in expected_keys:
                    value = item.data_columns.get(expected_key, None)
                    if value is not None:
                        print(f"        '{expected_key}': {value} ✓")
                    else:
                        print(f"        '{expected_key}': 缺失 ✗")
            else:
                print(f"      [警告] 没有data_columns或为空")

            # 检查主要数值
            if hasattr(item, 'value') and item.value is not None:
                print(f"      主要数值: {item.value}")
            else:
                print(f"      [警告] 没有主要数值")

    print(f"\n=== 诊断完成 ===")

if __name__ == "__main__":
    diagnose_profit_statement()