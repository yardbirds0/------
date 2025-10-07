#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"D:\Code\快报填写程序")

from utils.excel_utils import parse_formula_references_three_segment

# 测试公式
formula = "[项目余额表5个暂未审定]![银行存款]![内本:内蒙古]"

print(f"原始公式: {formula}")

refs = parse_formula_references_three_segment(formula)

print(f"解析结果:")
for ref in refs:
    print(f"  sheet_name: '{ref['sheet_name']}'")
    print(f"  item_name: '{ref['item_name']}'")
    print(f"  column_name: '{ref['column_name']}'")
