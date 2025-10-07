#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证空格保留 - 确保UI显示保留原始空格，但公式比对正常工作
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
print("验证空格保留 - UI显示 vs 公式比对")
print("=" * 100)

wb = openpyxl.load_workbook(excel_path, data_only=True)

sheet_name = "科目余额表（5级含未过账）"
sheet = wb[sheet_name]

# 从Excel读取（含空格）
b5_raw = sheet['B5'].value
e2_raw = sheet['E2'].value

print(f"\n[1] Excel原始值（用于UI显示）:")
print(f"  B5项目名: '{b5_raw}'")
print(f"  B5 repr: {repr(b5_raw)}")
print(f"  E2列名: '{e2_raw}'")
print(f"  E2 repr: {repr(e2_raw)}")

# 模拟data_extractor创建SourceItem（保留原始值）
wm = WorkbookManager()
wm.worksheets[sheet_name] = sheet

source = SourceItem(
    id="test",
    sheet_name=sheet_name,
    name=b5_raw,  # 保留原始值（含空格）
    cell_address="B5",
    row=5,
    column="B",
    value=sheet['E5'].value
)
source.values = {e2_raw: sheet['E5'].value}  # 保留原始列名（含空格）

wm.source_items["test"] = source

print(f"\n[2] SourceItem存储（用于UI显示）:")
print(f"  source.name: '{source.name}'")
print(f"  source.name repr: {repr(source.name)}")
print(f"  source.values keys: {list(source.values.keys())}")
print(f"  source.values keys repr: {[repr(k) for k in source.values.keys()]}")

# 构建公式（用户可能输入strip后的值）
b5_stripped = b5_raw.strip()
e2_stripped = e2_raw.strip()

formula = f"[{sheet_name}]![{b5_stripped}]![{e2_stripped}]"

print(f"\n[3] 用户输入公式（可能已strip）:")
print(f"  公式: {formula}")

# 测试公式系统
print(f"\n[4] 三段式公式系统测试:")

# 解析
refs = parse_formula_references_three_segment(formula)
print(f"  解析: {len(refs)}个引用 {'[OK]' if refs else '[FAIL]'}")

# 验证
is_valid, error = validate_formula_syntax_three_segment(formula, wm)
print(f"  验证: {'[OK]' if is_valid else f'[FAIL] {error}'}")

# 计算
success, result = evaluate_formula_with_values_three_segment(formula, wm.source_items)
print(f"  计算: {'[OK] 结果=' + str(result) if success else f'[FAIL] {result}'}")

# 最终检查
expected = sheet['E5'].value
print(f"\n[5] 最终验证:")
print(f"  UI应显示项目名: '{b5_raw}' (含空格)")
print(f"  UI应显示列名: '{e2_raw}' (含空格)")
print(f"  公式计算结果: {result}")
print(f"  期望值: {expected}")
print(f"  结果匹配: {'[OK]' if result == expected else '[FAIL]'}")

print(f"\n[6] 结论:")
if is_valid and success and result == expected:
    print(f"  [SUCCESS] 空格保留正确!")
    print(f"  - SourceItem.name保留原始空格: '{source.name}'")
    print(f"  - values字典key保留原始空格: {list(source.values.keys())}")
    print(f"  - 公式验证和计算正常工作: {result}")
else:
    print(f"  [FAIL] 存在问题!")

print("\n" + "=" * 100)
