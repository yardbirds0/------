#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试用户公式识别问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.excel_utils import (
    parse_formula_references_three_segment,
    normalize_formula_punctuation
)

# 用户的公式
formula = "[利润表]![一、营业总收入]![本期金额]+ [利润表]![一、营业总收入]![本年累计]"

print("=" * 70)
print("调试用户公式")
print("=" * 70)

print(f"\n原始公式:")
print(f"  '{formula}'")

# 检查字符
print(f"\n字符分析:")
for i, char in enumerate(formula):
    if char in '!！[]【】':
        print(f"  位置{i}: '{char}' (Unicode: {ord(char)}, {hex(ord(char))})")

# 规范化
normalized = normalize_formula_punctuation(formula)
print(f"\n规范化后:")
print(f"  '{normalized}'")

if normalized != formula:
    print(f"  [变化] 有字符被转换")
else:
    print(f"  [不变] 没有字符需要转换")

# 解析
refs = parse_formula_references_three_segment(formula)

print(f"\n解析结果:")
print(f"  引用数量: {len(refs)}")
for i, ref in enumerate(refs, 1):
    print(f"  {i}. {ref['full_reference']}")
    print(f"     工作表: '{ref['sheet_name']}'")
    print(f"     项目: '{ref['item_name']}'")
    print(f"     列名: '{ref['column_name']}'")

# 测试正则
import re
pattern = r'\[([^\]]+)\]!\[([^\]]+)\]!\[([^\]]+)\]'
matches = list(re.finditer(pattern, normalized))
print(f"\n正则匹配:")
print(f"  模式: {pattern}")
print(f"  匹配数量: {len(matches)}")
for i, match in enumerate(matches, 1):
    print(f"  {i}. 完整匹配: '{match.group(0)}'")
    print(f"     位置: {match.start()}-{match.end()}")

print("\n" + "=" * 70)
