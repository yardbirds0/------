#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中文标点符号支持
验证用户使用中文输入法时的公式能否正确解析
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.data_models import SourceItem, WorkbookManager
from utils.excel_utils import (
    parse_formula_references_three_segment,
    build_formula_reference_three_segment,
    validate_formula_syntax_three_segment,
    evaluate_formula_with_values_three_segment
)

def test_chinese_punctuation_parse():
    """测试中文感叹号的公式解析"""
    print("\n=== 测试1: 中文标点解析 ===")

    # 用户实际输入的公式（中文感叹号）
    formula_chinese = "[上年科目余额表]！[银行存款]！[年初余额借方]+[上年科目余额表]！[银行存款]！[期初余额借方]"

    print(f"输入公式: {formula_chinese}")
    print(f"包含中文感叹号: {'！' in formula_chinese}")

    refs = parse_formula_references_three_segment(formula_chinese)

    print(f"解析结果: {len(refs)}个引用")
    for ref in refs:
        print(f"  - {ref['full_reference']}")

    # 验证解析结果
    assert len(refs) == 2, f"应该解析出2个引用，实际: {len(refs)}"
    assert refs[0]['sheet_name'] == "上年科目余额表"
    assert refs[0]['item_name'] == "银行存款"
    assert refs[0]['column_name'] == "年初余额借方"
    assert refs[1]['column_name'] == "期初余额借方"

    print("[OK] 中文标点解析成功")
    return True

def test_chinese_punctuation_validate():
    """测试中文感叹号的公式验证"""
    print("\n=== 测试2: 中文标点验证 ===")

    # 创建测试数据
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

    # 使用中文标点的公式
    formula = "[上年科目余额表]！[银行存款]！[年初余额借方]+[上年科目余额表]！[银行存款]！[期初余额借方]"

    is_valid, error = validate_formula_syntax_three_segment(formula, wm)

    if is_valid:
        print(f"[OK] 公式验证通过")
    else:
        print(f"[FAIL] 公式验证失败: {error}")

    assert is_valid, f"验证应该通过，但失败了: {error}"
    return True

def test_chinese_punctuation_calculate():
    """测试中文感叹号的公式计算"""
    print("\n=== 测试3: 中文标点计算 ===")

    source1 = SourceItem(
        id="s1",
        sheet_name="上年科目余额表",
        name="银行存款",
        cell_address="D10",
        row=10,
        column="D"
    )
    source1.values = {
        "年初余额借方": 50000,
        "期初余额借方": 30000
    }

    source_items = {"s1": source1}

    # 使用中文标点的公式
    formula = "[上年科目余额表]！[银行存款]！[年初余额借方]+[上年科目余额表]！[银行存款]！[期初余额借方]"

    success, result = evaluate_formula_with_values_three_segment(formula, source_items)

    if success:
        print(f"[OK] 计算成功: {formula} = {result}")
    else:
        print(f"[FAIL] 计算失败: {result}")

    assert success, f"计算应该成功，但失败了: {result}"
    assert result == 80000, f"计算结果应该是80000，实际: {result}"

    return True

def test_mixed_punctuation():
    """测试混合标点（部分中文部分英文）"""
    print("\n=== 测试4: 混合标点 ===")

    # 混合使用中英文标点
    formula = "[上年科目余额表]![银行存款]！[年初余额借方]"  # 第一个!是英文，第二个！是中文

    refs = parse_formula_references_three_segment(formula)

    assert len(refs) == 1, f"应该解析出1个引用，实际: {len(refs)}"
    print(f"[OK] 混合标点解析成功: {refs[0]['full_reference']}")

    return True

def test_other_chinese_punctuation():
    """测试其他中文标点（中文方括号）"""
    print("\n=== 测试5: 中文方括号 ===")

    # 使用中文方括号【】
    formula = "【上年科目余额表】！【银行存款】！【年初余额借方】"

    refs = parse_formula_references_three_segment(formula)

    if len(refs) == 1:
        print(f"[OK] 中文方括号解析成功: {refs[0]['full_reference']}")
    else:
        print(f"[INFO] 中文方括号解析结果: {len(refs)}个引用")

    # 中文方括号也应该被转换
    assert len(refs) == 1, f"应该解析出1个引用，实际: {len(refs)}"

    return True

def main():
    """运行所有测试"""
    print("=" * 60)
    print("中文标点符号支持测试")
    print("=" * 60)

    tests = [
        ("中文感叹号解析", test_chinese_punctuation_parse),
        ("中文感叹号验证", test_chinese_punctuation_validate),
        ("中文感叹号计算", test_chinese_punctuation_calculate),
        ("混合标点", test_mixed_punctuation),
        ("中文方括号", test_other_chinese_punctuation),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"[FAIL] {name}失败: {e}")
            failed += 1
        except Exception as e:
            print(f"[FAIL] {name}异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: [OK] {passed}个通过, [FAIL] {failed}个失败")
    print("=" * 60)

    if failed == 0:
        print("\n[SUCCESS] 所有中文标点测试通过！")
        return 0
    else:
        print(f"\n[WARNING] 有{failed}个测试失败，需要修复。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
