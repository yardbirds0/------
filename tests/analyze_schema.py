#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema分析脚本 - 检查利润表的schema生成过程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor

def analyze_schema():
    """分析schema生成过程"""
    print("=== Schema分析 ===")

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

    file_manager = FileManager()
    success, message = file_manager.load_excel_files([excel_file])

    if not success:
        print(f"[错误] 数据加载失败: {message}")
        return

    workbook_manager = file_manager.workbook_manager
    extractor = DataExtractor(workbook_manager)

    # 确保workbook被加载
    extractor._load_workbook()

    # 2. 直接访问workbook并分析利润表
    print(f"\n正在分析利润表的schema...")

    try:
        # 获取利润表工作表
        sheet = extractor.workbook["利润表"]
        print(f"利润表尺寸: {sheet.max_row} 行 x {sheet.max_column} 列")

        # 3. 使用schema_analyzer分析
        schema = extractor.schema_analyzer.analyze_table_schema(sheet)

        print(f"\n=== Schema分析结果 ===")
        print(f"表类型: {schema.table_type}")
        print(f"数据开始行: {schema.data_start_row}")
        print(f"名称列: {schema.name_columns}")
        print(f"数据列数量: {len(schema.data_columns)}")

        # 4. 详细分析每个数据列
        print(f"\n=== 数据列详细信息 ===")
        for i, col_info in enumerate(schema.data_columns):
            print(f"数据列 {i+1}:")
            print(f"  列索引: {col_info.column_index}")
            print(f"  主要列头: '{col_info.primary_header}'")

            if hasattr(col_info, 'secondary_header'):
                print(f"  二级列头: '{col_info.secondary_header}'")

            print(f"  是否数值: {col_info.is_numeric}")

            if hasattr(col_info, 'data_type'):
                print(f"  数据类型: {col_info.data_type}")

            # 测试列键名生成
            column_key = extractor._generate_column_key(col_info, "利润表")
            print(f"  生成的键名: '{column_key}'")

        # 5. 检查是否有其他列被遗漏
        print(f"\n=== 手动检查所有列 ===")
        print(f"检查前3行的所有列内容:")

        for row in range(1, 4):
            print(f"\n第{row}行:")
            for col in range(1, sheet.max_column + 1):
                cell = sheet.cell(row=row, column=col)
                if cell.value:
                    print(f"  列{col}: '{cell.value}'")

        # 6. 检查第5行（列头行）的数值列
        print(f"\n=== 第5行列头检查 ===")
        headers_row = 5
        for col in range(1, sheet.max_column + 1):
            cell = sheet.cell(row=headers_row, column=col)
            if cell.value and str(cell.value).strip():
                header_text = str(cell.value).strip()

                # 检查该列下面是否有数值
                has_numeric = False
                for check_row in range(headers_row + 1, min(headers_row + 5, sheet.max_row + 1)):
                    check_cell = sheet.cell(row=check_row, column=col)
                    if check_cell.value and isinstance(check_cell.value, (int, float)):
                        has_numeric = True
                        break

                print(f"  列{col}: '{header_text}' - 有数值: {has_numeric}")

    except Exception as e:
        print(f"[错误] Schema分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_schema()