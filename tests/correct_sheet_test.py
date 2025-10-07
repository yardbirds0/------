#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用正确工作表名验证
工作表: 科目余额表（5级含未过账）
"""

import sys
import openpyxl
sys.path.insert(0, r"D:\Code\快报填写程序")

from models.data_models import SourceItem, WorkbookManager
from utils.excel_utils import (
    parse_formula_references_three_segment,
    validate_formula_syntax_three_segment,
    evaluate_formula_with_values_three_segment,
)

excel_path = r"D:\Code\快报填写程序\（科电）国资委、财政快报模板-纯净版 的副本.xlsx"

print("=" * 100)
print("使用正确工作表名验证")
print("=" * 100)

wb = openpyxl.load_workbook(excel_path, data_only=True)

# 正确的工作表名
sheet_name = "科目余额表（5级含未过账）"
print(f"\n工作表: '{sheet_name}'")

sheet = wb[sheet_name]

# 验证单元格
b5_value = sheet['B5'].value
e2_value = sheet['E2'].value

# ⭐ strip去除空格，与公式解析保持一致
item_name = b5_value.strip() if isinstance(b5_value, str) else b5_value
column_name = e2_value.strip() if isinstance(e2_value, str) else e2_value

print(f"\n单元格验证:")
print(f"  B5 (原始值): '{b5_value}'")
print(f"  B5 (strip后): '{item_name}'")
print(f"  E2 (原始值): '{e2_value}'")
print(f"  E2 (strip后): '{column_name}'")
print(f"  E5 (数据): {sheet['E5'].value}")

# 构建公式
formula = f"[{sheet_name}]![{item_name}]![{column_name}]"
print(f"\n构建公式: {formula}")

# 创建WorkbookManager和SourceItem
wm = WorkbookManager()
wm.worksheets[sheet_name] = sheet

source = SourceItem(
    id="test",
    sheet_name=sheet_name,
    name=item_name,  # 使用strip后的值
    cell_address="B5",
    row=5,
    column="B",
    value=sheet['E5'].value
)
source.values = {column_name: sheet['E5'].value}  # 使用strip后的列名

wm.source_items["test"] = source

# 测试公式系统
print(f"\n测试三段式公式系统:")

# 解析
refs = parse_formula_references_three_segment(formula)
print(f"  [1] 解析: {len(refs)}个引用")
if refs:
    print(f"      sheet_name: '{refs[0]['sheet_name']}'")
    print(f"      item_name: '{refs[0]['item_name']}'")
    print(f"      column_name: '{refs[0]['column_name']}'")

# 验证
is_valid, error = validate_formula_syntax_three_segment(formula, wm)
print(f"  [2] 验证: {'[OK]' if is_valid else f'[FAIL] {error}'}")

# 计算
success, result = evaluate_formula_with_values_three_segment(formula, wm.source_items)
print(f"  [3] 计算: {'[OK] 结果=' + str(result) if success else f'[FAIL] {result}'}")

# 对比
expected = sheet['E5'].value
print(f"\n最终验证:")
print(f"  公式: {formula}")
print(f"  引用单元格: E5")
print(f"  单元格值: {expected}")
print(f"  计算结果: {result}")
print(f"  匹配: {'[OK] 一致' if result == expected else '[FAIL] 不一致'}")

print("\n" + "=" * 100)
