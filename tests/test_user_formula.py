#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户实际公式
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.data_models import SourceItem, WorkbookManager
from utils.excel_utils import (
    parse_formula_references_three_segment,
    validate_formula_syntax_three_segment,
    evaluate_formula_with_values_three_segment
)

def main():
    print("=" * 70)
    print("用户实际公式测试")
    print("=" * 70)

    # 用户的实际公式（带中文标点）
    user_formula = "[上年科目余额表]！[银行存款]！[年初余额借方]+[上年科目余额表]！[银行存款]！[期初余额借方]"

    print(f"\n原始公式:")
    print(f"  {user_formula}")
    print(f"\n包含中文标点: {'！' in user_formula}")

    # 测试1: 解析
    print("\n--- 步骤1: 解析公式 ---")
    refs = parse_formula_references_three_segment(user_formula)
    print(f"解析出 {len(refs)} 个引用:")
    for i, ref in enumerate(refs, 1):
        print(f"  {i}. {ref['full_reference']}")
        print(f"     工作表: {ref['sheet_name']}")
        print(f"     项目名: {ref['item_name']}")
        print(f"     列名: {ref['column_name']}")

    # 测试2: 验证
    print("\n--- 步骤2: 验证公式 ---")
    wm = WorkbookManager()
    wm.worksheets = {"上年科目余额表": None}

    source1 = SourceItem(
        id="s1",
        sheet_name="上年科目余额表",
        name="银行存款",
        cell_address="D10",
        row=10,
        column="D",
        value=100000
    )
    source1.values = {
        "年初余额借方": 50000,
        "期初余额借方": 30000
    }

    wm.source_items = {"s1": source1}

    is_valid, error = validate_formula_syntax_three_segment(user_formula, wm)

    if is_valid:
        print(f"[OK] 公式验证通过")
    else:
        print(f"[FAIL] 公式验证失败: {error}")
        return 1

    # 测试3: 计算
    print("\n--- 步骤3: 计算公式 ---")
    source_items = {"s1": source1}
    success, result = evaluate_formula_with_values_three_segment(user_formula, source_items)

    if success:
        print(f"[OK] 计算成功: {result}")
        print(f"     50000 + 30000 = {result}")
    else:
        print(f"[FAIL] 计算失败: {result}")
        return 1

    print("\n" + "=" * 70)
    print("[SUCCESS] 用户公式测试全部通过！")
    print("=" * 70)
    print("\n修复内容:")
    print("  1. 添加 normalize_formula_punctuation() 函数")
    print("  2. 支持中文标点: ！→! 【】→[] （）→()")
    print("  3. 在解析、验证、计算前自动规范化")
    print("\n现在用户可以使用中文输入法输入公式了！")
    print("=" * 70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
