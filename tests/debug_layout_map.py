# -*- coding: utf-8 -*-
"""
调试: 检查layout_map中的文字内容
"""
import sys
sys.path.insert(0, 'd:\\Code\\快报填写程序-修改UI前(2)')

import openpyxl
from models.data_models import WorkbookManager
from modules.data_extractor import DataExtractor
from components.advanced_widgets import derive_header_layout_from_metadata

# 加载数据
workbook_path = 'd:\\Code\\快报填写程序-修改UI前(2)\\上年科目余额表.xlsx'
manager = WorkbookManager()
manager.file_path = workbook_path

temp_wb = openpyxl.load_workbook(workbook_path, data_only=True)
for sheet_name in temp_wb.sheetnames:
    manager.data_source_sheets.append(sheet_name)
temp_wb.close()

extractor = DataExtractor(manager)
extractor.extract_all_data()

# 获取科目余额表的列元数据
sheet_name = '上年科目余额表'
metadata = manager.source_sheet_columns.get(sheet_name, [])

print(f"工作表: {sheet_name}")
print(f"列元数据数量: {len(metadata)}\n")

# 显示前3列的完整元数据
for idx, entry in enumerate(metadata[:3]):
    print(f"列 {idx+1}:")
    for key, value in entry.items():
        if value:  # 只显示非空值
            print(f"  {key}: {value}")
    print()

# 生成layout_map
print("="*60)
print("生成 layout_map:")
print("="*60)

layout_map, row_count = derive_header_layout_from_metadata(metadata, base_offset=5)

print(f"row_count: {row_count}")
print(f"layout_map 数量: {len(layout_map)}\n")

# 显示前3个section的layout
for idx in range(5, min(8, 5 + len(metadata))):
    if idx in layout_map:
        entry = layout_map[idx]
        print(f"Section {idx} (列 {idx-5+1}):")
        primary = entry.get('primary', {})
        secondary = entry.get('secondary', {})

        print(f"  primary:")
        print(f"    text: '{primary.get('text', '')}'")
        print(f"    col_span: {primary.get('col_span')}")
        print(f"    row_span: {primary.get('row_span')}")
        print(f"    members: {primary.get('members')}")

        print(f"  secondary:")
        print(f"    text: '{secondary.get('text', '')}'")
        print(f"    col_span: {secondary.get('col_span')}")
        print(f"    row_span: {secondary.get('row_span')}")
        print()

if not any(layout_map[idx]['primary'].get('text') for idx in layout_map):
    print("⚠️⚠️⚠️ 严重问题: layout_map中所有primary.text都为空!")

if not any(layout_map[idx]['secondary'].get('text') for idx in layout_map):
    print("⚠️⚠️⚠️ 严重问题: layout_map中所有secondary.text都为空!")
