#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度诊断脚本 - 检查表类型检测问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from utils.table_column_rules import TableColumnRules

def deep_diagnosis():
    """深度诊断"""
    print("=== 深度诊断 ===")

    # 1. 测试表类型检测
    print("\n[1] 表类型检测测试:")
    test_sheets = ["利润表", "资产负债表", "现金流量表", "科目余额表", "试算平衡表"]
    for sheet in test_sheets:
        detected = TableColumnRules.detect_table_type(sheet)
        print(f"  '{sheet}' -> '{detected}'")

    # 2. 加载Excel文件
    current_dir = os.path.dirname(os.path.dirname(__file__))
    excel_file = None
    for file in os.listdir(current_dir):
        if file.endswith('.xlsx') and '科电' in file:
            excel_file = os.path.join(current_dir, file)
            break

    if not excel_file:
        print("[错误] 未找到Excel文件")
        return

    print(f"\n[2] 加载Excel文件:")
    print(f"  文件: {excel_file}")

    file_manager = FileManager()
    success, message = file_manager.load_excel_files([excel_file])

    if not success:
        print(f"  [错误] 数据加载失败: {message}")
        return

    workbook_manager = file_manager.workbook_manager

    # 3. 检查现有的source_items
    print(f"\n[3] 现有source_items分析:")
    print(f"  总计: {len(workbook_manager.source_items)} 个项目")

    sheets_summary = {}
    for source_id, source in workbook_manager.source_items.items():
        sheet_name = source.sheet_name
        if sheet_name not in sheets_summary:
            sheets_summary[sheet_name] = 0
        sheets_summary[sheet_name] += 1

    for sheet_name, count in sheets_summary.items():
        detected_type = TableColumnRules.detect_table_type(sheet_name)
        print(f"  '{sheet_name}': {count} 项目, 检测类型: '{detected_type}'")

    # 4. 重新运行数据提取并观察过程
    print(f"\n[4] 重新运行数据提取:")
    extractor = DataExtractor(workbook_manager)

    # 在提取前清空现有数据
    workbook_manager.source_items.clear()

    success = extractor.extract_all_data()
    if success:
        print(f"  提取成功，新的项目数: {len(workbook_manager.source_items)}")

        # 重新统计
        new_sheets_summary = {}
        for source_id, source in workbook_manager.source_items.items():
            sheet_name = source.sheet_name
            if sheet_name not in new_sheets_summary:
                new_sheets_summary[sheet_name] = 0
            new_sheets_summary[sheet_name] += 1

        print(f"\n[5] 重新提取后的结果:")
        for sheet_name, count in new_sheets_summary.items():
            detected_type = TableColumnRules.detect_table_type(sheet_name)
            print(f"  '{sheet_name}': {count} 项目, 检测类型: '{detected_type}'")

            # 特别检查利润表
            if detected_type == "利润表":
                print(f"    [利润表详细检查]")
                profit_items = [item for item in workbook_manager.source_items.values() if item.sheet_name == sheet_name]

                for i, item in enumerate(profit_items[:3]):  # 只看前3个
                    print(f"      项目 {i+1}: {item.name}")
                    if hasattr(item, 'data_columns') and item.data_columns:
                        print(f"        data_columns: {item.data_columns}")
                    else:
                        print(f"        [警告] data_columns为空")
    else:
        print(f"  提取失败")

if __name__ == "__main__":
    deep_diagnosis()