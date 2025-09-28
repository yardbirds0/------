#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Excel文件中的工作表名称
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl
from utils.table_column_rules import TableColumnRules

def check_sheet_names():
    """检查工作表名称和类型检测"""
    print("=== 工作表名称检查 ===")

    # 找到Excel文件
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

    # 直接用openpyxl打开文件
    try:
        workbook = openpyxl.load_workbook(excel_file, data_only=True)
        print(f"\n工作表列表:")

        for i, sheet_name in enumerate(workbook.sheetnames):
            print(f"  {i+1}. '{sheet_name}'")

            # 测试类型检测
            detected_type = TableColumnRules.detect_table_type(sheet_name)
            print(f"     检测类型: '{detected_type}'")

            # 手动检查包含关键词
            if "利润" in sheet_name:
                print(f"     包含'利润': True")
            else:
                print(f"     包含'利润': False")

    except Exception as e:
        print(f"[错误] 分析Excel文件失败: {e}")

if __name__ == "__main__":
    check_sheet_names()