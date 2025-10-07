"""
调试脚本：检查data_columns和columns的数据是否正确填充
"""
import sys
sys.path.insert(0, 'd:\\Code\\快报填写程序-修改UI前(2)')

import openpyxl
from models.data_models import WorkbookManager
from modules.data_extractor import DataExtractor

print("=" * 80)
print("测试：检查data_columns和columns数据填充")
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

# 提取数据
extractor = DataExtractor(manager)
success = extractor.extract_all_data()

print("\n" + "=" * 80)
print("检查TargetItem.columns是否有数据")
print("=" * 80)
if manager.target_items:
    sample_items = list(manager.target_items.values())[:3]
    for item in sample_items:
        print(f"\n目标项: {item.name}")
        print(f"  工作表: {item.sheet_name}")
        print(f"  columns键: {list(item.columns.keys())}")
        if item.columns:
            print(f"  columns内容（前3个）:")
            for key, entry in list(item.columns.items())[:3]:
                print(f"    {key}:")
                print(f"      display_name: {entry.display_name}")
                print(f"      source_value: {entry.source_value}")
                print(f"      cell_address: {entry.cell_address}")

print("\n" + "=" * 80)
print("检查SourceItem.data_columns是否有数据")
print("=" * 80)
if manager.source_items:
    # 找一个科目余额表的项
    balance_items = [item for item in manager.source_items.values() if '余额' in item.sheet_name]
    if balance_items:
        sample = balance_items[0]
        print(f"\n来源项: {sample.name}")
        print(f"  工作表: {sample.sheet_name}")
        print(f"  data_columns键: {list(sample.data_columns.keys())}")
        if sample.data_columns:
            print(f"  data_columns内容:")
            for key, value in list(sample.data_columns.items())[:5]:
                print(f"    {key}: {value}")
        print(f"\n  基本属性:")
        print(f"    name: {sample.name}")
        print(f"    account_code: {sample.account_code}")
        print(f"    hierarchy_level: {sample.hierarchy_level}")
        print(f"    value: {sample.value}")

print("\n" + "=" * 80)
print("检查source_sheet_columns元数据")
print("=" * 80)
for sheet_name, columns in manager.source_sheet_columns.items():
    if '余额' in sheet_name or '科目' in sheet_name:
        print(f"\n数据源工作表: {sheet_name}")
        print(f"  列数: {len(columns)}")
        print("  所有列的display_name:")
        for i, col in enumerate(columns):
            print(f"    {i+1}. key: {col.get('key')}, display_name: {col.get('display_name')}, is_data_column: {col.get('is_data_column')}")

print("\n" + "=" * 80)
print("调试完成！")
print("=" * 80)
