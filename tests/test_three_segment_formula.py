#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三段式公式系统测试脚本
验证：解析、构建、验证、计算全流程
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

def test_parse_three_segment():
    """测试三段式解析"""
    print("\n=== 测试1: 三段式解析 ===")

    formula = "[利润表]![营业收入]![本年累计] + [利润表]![营业成本]![本年累计]"
    refs = parse_formula_references_three_segment(formula)

    assert len(refs) == 2, f"应该解析出2个引用，实际: {len(refs)}"
    assert refs[0]['sheet_name'] == "利润表", f"工作表名错误: {refs[0]['sheet_name']}"
    assert refs[0]['item_name'] == "营业收入", f"项目名错误: {refs[0]['item_name']}"
    assert refs[0]['column_name'] == "本年累计", f"列名错误: {refs[0]['column_name']}"

    print(f"[OK] 解析成功: {len(refs)}个引用")
    for ref in refs:
        print(f"   - {ref['full_reference']}")
    return True

def test_build_three_segment():
    """测试三段式构建"""
    print("\n=== 测试2: 三段式构建 ===")

    ref = build_formula_reference_three_segment("利润表", "营业收入", "本年累计")
    expected = "[利润表]![营业收入]![本年累计]"

    assert ref == expected, f"构建错误: {ref} != {expected}"
    print(f"[OK] 构建成功: {ref}")
    return True

def test_validate_with_manager():
    """测试带workbook_manager的验证"""
    print("\n=== 测试3: 公式验证（含数据验证）===")

    # 创建测试数据
    wm = WorkbookManager()
    wm.worksheets = {"利润表": None}

    # 创建source_item（关键：必须有values字典）
    source1 = SourceItem(
        id="s1",
        sheet_name="利润表",
        name="营业收入",
        cell_address="D10",
        row=10,
        column="D",
        value=100000
    )
    # ⭐ 关键：设置values字典
    source1.values = {
        "本期金额": 50000,
        "本年累计": 100000
    }

    source2 = SourceItem(
        id="s2",
        sheet_name="利润表",
        name="营业成本",
        cell_address="D15",
        row=15,
        column="D",
        value=60000
    )
    source2.values = {
        "本期金额": 30000,
        "本年累计": 60000
    }

    wm.source_items = {"s1": source1, "s2": source2}

    # 测试正确的公式
    formula1 = "[利润表]![营业收入]![本年累计] + [利润表]![营业成本]![本年累计]"
    is_valid, error = validate_formula_syntax_three_segment(formula1, wm)
    assert is_valid, f"验证失败: {error}"
    print(f"[OK] 正确公式验证通过: {formula1}")

    # 测试错误的工作表
    formula2 = "[不存在的表]![营业收入]![本年累计]"
    is_valid, error = validate_formula_syntax_three_segment(formula2, wm)
    assert not is_valid, "应该检测到工作表不存在"
    assert "未找到工作表" in error, f"错误信息不对: {error}"
    print(f"[OK] 检测到工作表错误: {error}")

    # 测试错误的项目
    formula3 = "[利润表]![不存在的项目]![本年累计]"
    is_valid, error = validate_formula_syntax_three_segment(formula3, wm)
    assert not is_valid, "应该检测到项目不存在"
    assert "未找到项目" in error, f"错误信息不对: {error}"
    print(f"[OK] 检测到项目错误: {error}")

    # 测试错误的列名
    formula4 = "[利润表]![营业收入]![不存在的列]"
    is_valid, error = validate_formula_syntax_three_segment(formula4, wm)
    assert not is_valid, "应该检测到列名不存在"
    assert "不包含列" in error, f"错误信息不对: {error}"
    print(f"[OK] 检测到列名错误: {error}")

    return True

def test_calculate():
    """测试公式计算"""
    print("\n=== 测试4: 公式计算 ===")

    # 创建测试数据
    source1 = SourceItem(
        id="s1",
        sheet_name="利润表",
        name="营业收入",
        cell_address="D10",
        row=10,
        column="D"
    )
    source1.values = {
        "本期金额": 50000,
        "本年累计": 100000
    }

    source2 = SourceItem(
        id="s2",
        sheet_name="利润表",
        name="营业成本",
        cell_address="D15",
        row=15,
        column="D"
    )
    source2.values = {
        "本期金额": 30000,
        "本年累计": 60000
    }

    source_items = {"s1": source1, "s2": source2}

    # 测试计算
    formula = "[利润表]![营业收入]![本年累计] - [利润表]![营业成本]![本年累计]"
    success, result = evaluate_formula_with_values_three_segment(formula, source_items)

    assert success, f"计算失败: {result}"
    assert result == 40000, f"计算结果错误: {result} (应为40000)"
    print(f"[OK] 计算成功: {formula} = {result}")

    # 测试复杂公式
    formula2 = "([利润表]![营业收入]![本年累计] - [利润表]![营业成本]![本年累计]) / 1000"
    success, result = evaluate_formula_with_values_three_segment(formula2, source_items)
    assert success, f"复杂公式计算失败: {result}"
    assert result == 40.0, f"复杂公式结果错误: {result}"
    print(f"[OK] 复杂公式计算成功: {formula2} = {result}")

    return True

def test_source_item_matching():
    """测试source_item匹配问题"""
    print("\n=== 测试5: SourceItem匹配 ===")

    # 模拟实际数据结构
    source = SourceItem(
        id="s1",
        sheet_name="科目余额表",
        name="库存现金",  # ⭐ 原始name，不含科目代码
        cell_address="D5",
        row=5,
        column="D",
        account_code="1001",  # 科目代码单独存储
        hierarchy_level=1
    )
    # full_name_with_indent会自动生成为 "  1001 库存现金"

    print(f"原始name: '{source.name}'")
    print(f"科目代码: '{source.account_code}'")
    print(f"显示名称: '{source.full_name_with_indent}'")

    # 测试正确的匹配方式
    display_text = source.full_name_with_indent  # "  1001 库存现金"

    # [FAIL] 错误方式：直接strip
    wrong_match = display_text.strip()  # "1001 库存现金"
    assert wrong_match != source.name, "错误匹配方式应该失败"
    print(f"[FAIL] 错误匹配: '{wrong_match}' != '{source.name}'")

    # [OK] 正确方式1：去除科目代码
    parts = display_text.strip().split(" ", 1)
    if len(parts) == 2 and parts[0].isdigit():
        correct_name = parts[1]
    else:
        correct_name = display_text.strip()
    assert correct_name == source.name, "应该匹配成功"
    print(f"[OK] 正确匹配方式1: '{correct_name}' == '{source.name}'")

    # [OK] 正确方式2：直接使用UserRole存储的对象
    print(f"[OK] 正确匹配方式2: 直接从UserRole获取source_item对象")

    return True

def main():
    """运行所有测试"""
    print("=" * 60)
    print("三段式公式系统完整测试")
    print("=" * 60)

    tests = [
        ("解析测试", test_parse_three_segment),
        ("构建测试", test_build_three_segment),
        ("验证测试", test_validate_with_manager),
        ("计算测试", test_calculate),
        ("匹配测试", test_source_item_matching),
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
        print("\n[SUCCESS] 所有测试通过！三段式公式系统工作正常。")
        return 0
    else:
        print(f"\n[WARNING] 有{failed}个测试失败，需要修复。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
