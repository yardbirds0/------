#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确验证 - 直接定位单元格E5
"""

import openpyxl

excel_path = r"D:\Code\快报填写程序\（科电）国资委、财政快报模板-纯净版 的副本.xlsx"

print("=" * 100)
print("精确单元格验证")
print("=" * 100)

wb = openpyxl.load_workbook(excel_path, data_only=True)

# 第9个工作表
target_sheet = wb.sheetnames[8]
print(f"\n工作表名: '{target_sheet}'")

sheet = wb[target_sheet]

# 验证关键单元格
print(f"\n关键单元格验证:")
print(f"  B5 (项目名): {sheet['B5'].value}")
print(f"  E2 (列名表头): {sheet['E2'].value}")
print(f"  E5 (数据值): {sheet['E5'].value}")

print(f"\n公式验证:")
formula = f"[{target_sheet}]![{sheet['B5'].value}]![{sheet['E2'].value}]"
print(f"  公式: {formula}")
print(f"  应该引用: 单元格E5")
print(f"  单元格E5的值: {sheet['E5'].value}")

print("\n" + "=" * 100)
print(f"结论: 公式 {formula} 引用单元格E5，值为 {sheet['E5'].value}")
print("=" * 100)
