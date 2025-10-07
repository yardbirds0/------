"""
完整数据流测试：从提取到显示
"""
import sys
sys.path.insert(0, 'd:\\Code\\快报填写程序-修改UI前(2)')

import openpyxl
from models.data_models import WorkbookManager
from modules.data_extractor import DataExtractor

# 加载工作簿
workbook_path = 'd:\\Code\\快报填写程序-修改UI前(2)\\sample.xlsx'
print(f"将使用工作簿: {workbook_path}\n")

# 创建WorkbookManager
manager = WorkbookManager()
manager.file_path = workbook_path  # 设置file_path

# 模拟分类所有工作表（需要先临时加载获取工作表列表）
temp_wb = openpyxl.load_workbook(workbook_path, data_only=True)
for sheet_name in temp_wb.sheetnames:
    if '快报' in sheet_name:
        manager.flash_report_sheets.append(sheet_name)
    else:
        manager.data_source_sheets.append(sheet_name)

temp_wb.close()

print(f"快报表: {manager.flash_report_sheets}")
print(f"数据源表: {manager.data_source_sheets}\n")

# 创建数据提取器
extractor = DataExtractor(manager)

# 提取数据
print("开始提取数据...\n")
success = extractor.extract_all_data()
print(f"提取结果: {'成功' if success else '失败'}")
print(f"目标项数量: {len(manager.target_items)}")
print(f"来源项数量: {len(manager.source_items)}\n")

# 检查source_sheet_columns
print("=" * 60)
print("检查 source_sheet_columns 字典:")
print("=" * 60)
for sheet_name, columns in manager.source_sheet_columns.items():
    print(f"\n工作表: {sheet_name}")
    print(f"  列元数据数量: {len(columns)}")
    if len(columns) > 0:
        print(f"  列头示例:")
        for col in columns[:5]:  # 只显示前5列
            print(f"    - {col.get('display_name', 'N/A')}")
    else:
        print(f"  警告: 没有列元数据！")

# 重点检查科目余额表
print("\n" + "=" * 60)
print("重点检查科目余额表:")
print("=" * 60)
target_sheet = None
for sheet_name in manager.source_sheet_columns.keys():
    if '科目余额' in sheet_name:
        target_sheet = sheet_name
        break

if target_sheet:
    print(f"\n找到科目余额表: {target_sheet}")
    columns = manager.source_sheet_columns[target_sheet]
    print(f"列元数据数量: {len(columns)}")
    print(f"\n所有列头:")
    for idx, col in enumerate(columns):
        print(f"  {idx+1}. {col.get('display_name', 'N/A')} (列{col.get('column_letter', '?')})")
else:
    print("\n警告: source_sheet_columns中没有科目余额表！")
