#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试字符串匹配问题
"""

import sys
import openpyxl
sys.path.insert(0, r"D:\Code\快报填写程序")

from utils.excel_utils import parse_formula_references_three_segment

excel_path = r"D:\Code\快报填写程序\（科电）国资委、财政快报模板-纯净版 的副本.xlsx"

wb = openpyxl.load_workbook(excel_path, data_only=True)

sheet_name = "科目余额表（5级含未过账）"
sheet = wb[sheet_name]

# 从Excel读取
item_from_excel = sheet['B5'].value
column_from_excel = sheet['E2'].value

print("从Excel读取的值:")
print(f"  B5 (项目名): '{item_from_excel}'")
print(f"  B5 类型: {type(item_from_excel)}")
print(f"  B5 repr: {repr(item_from_excel)}")
print(f"  E2 (列名): '{column_from_excel}'")
print(f"  E2 类型: {type(column_from_excel)}")
print(f"  E2 repr: {repr(column_from_excel)}")

# 构建公式
formula = f"[{sheet_name}]![{item_from_excel}]![{column_from_excel}]"
print(f"\n公式: {formula}")
print(f"公式 repr: {repr(formula)}")

# 解析公式
refs = parse_formula_references_three_segment(formula)
print(f"\n解析结果:")
if refs:
    item_from_parse = refs[0]['item_name']
    column_from_parse = refs[0]['column_name']

    print(f"  item_name: '{item_from_parse}'")
    print(f"  item_name 类型: {type(item_from_parse)}")
    print(f"  item_name repr: {repr(item_from_parse)}")
    print(f"  column_name: '{column_from_parse}'")
    print(f"  column_name 类型: {type(column_from_parse)}")
    print(f"  column_name repr: {repr(column_from_parse)}")

    # 比较
    print(f"\n字符串比较:")
    print(f"  item_from_excel == item_from_parse: {item_from_excel == item_from_parse}")
    print(f"  column_from_excel == column_from_parse: {column_from_excel == column_from_parse}")

    if item_from_excel != item_from_parse:
        print(f"\n  [MISMATCH] 项目名不匹配!")
        print(f"    Excel值的字节: {item_from_excel.encode('utf-8')}")
        print(f"    解析值的字节: {item_from_parse.encode('utf-8')}")

    if column_from_excel != column_from_parse:
        print(f"\n  [MISMATCH] 列名不匹配!")
        print(f"    Excel值的字节: {column_from_excel.encode('utf-8')}")
        print(f"    解析值的字节: {column_from_parse.encode('utf-8')}")
