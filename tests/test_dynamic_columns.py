"""
测试动态列功能：验证所有表格都是基于Excel元数据动态生成的
"""
import sys
sys.path.insert(0, 'd:\\Code\\快报填写程序-修改UI前(2)')

import openpyxl
from PySide6.QtWidgets import QApplication
from models.data_models import WorkbookManager
from modules.data_extractor import DataExtractor

print("=" * 80)
print("测试1: 验证WorkbookManager数据提取")
print("=" * 80)

# 创建WorkbookManager
manager = WorkbookManager()
manager.file_path = 'd:\\Code\\快报填写程序-修改UI前(2)\\sample.xlsx'

# 模拟分类工作表
temp_wb = openpyxl.load_workbook(manager.file_path, data_only=True)
for sheet_name in temp_wb.sheetnames:
    if '快报' in sheet_name:
        manager.flash_report_sheets.append(sheet_name)
    else:
        manager.data_source_sheets.append(sheet_name)
temp_wb.close()

print(f"快报表: {manager.flash_report_sheets}")
print(f"数据源表: {manager.data_source_sheets}\n")

# 提取数据
extractor = DataExtractor(manager)
success = extractor.extract_all_data()

print(f"提取结果: {'成功' if success else '失败'}")
print(f"目标项数量: {len(manager.target_items)}")
print(f"来源项数量: {len(manager.source_items)}\n")

# 检查target_sheet_columns
print("=" * 80)
print("测试2: 验证target_sheet_columns元数据")
print("=" * 80)
for sheet_name, columns in manager.target_sheet_columns.items():
    print(f"\n目标工作表: {sheet_name}")
    print(f"  列数: {len(columns)}")
    if columns:
        print("  前3列:")
        for col in columns[:3]:
            print(f"    - {col.get('display_name', 'N/A')}")

# 检查source_sheet_columns
print("\n" + "=" * 80)
print("测试3: 验证source_sheet_columns元数据")
print("=" * 80)
for sheet_name, columns in manager.source_sheet_columns.items():
    print(f"\n数据源工作表: {sheet_name}")
    print(f"  列数: {len(columns)}")
    if columns:
        print("  前3列:")
        for col in columns[:3]:
            print(f"    - {col.get('display_name', 'N/A')}")

# 检查TargetItem的columns
print("\n" + "=" * 80)
print("测试4: 验证TargetItem的columns属性")
print("=" * 80)
if manager.target_items:
    # target_items是字典，需要获取第一个值
    sample_item = list(manager.target_items.values())[0]
    print(f"样本项: {sample_item.name}")
    print(f"  工作表: {sample_item.sheet_name}")
    print(f"  columns键: {list(sample_item.columns.keys())}")
    if sample_item.columns:
        print(f"  columns值示例:")
        for key, entry in list(sample_item.columns.items())[:3]:
            print(f"    {key}: {entry}")

# 检查SourceItem的data_columns
print("\n" + "=" * 80)
print("测试5: 验证SourceItem的data_columns")
print("=" * 80)
if manager.source_items:
    # source_items是字典，需要获取第一个值
    sample_item = list(manager.source_items.values())[0]
    print(f"样本项: {sample_item.name}")
    print(f"  data_columns键: {list(sample_item.data_columns.keys())}")
    print(f"  data_columns值示例:")
    for key, value in list(sample_item.data_columns.items())[:3]:
        print(f"    {key}: {value}")

print("\n" + "=" * 80)
print("数据验证完成！")
print("=" * 80)
