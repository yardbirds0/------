#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单修复验证脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.data_models import TargetItem
from utils.table_column_rules import TableColumnRules

def test_targetitem_datatype():
    """测试TargetItem.data_type属性"""
    try:
        # 创建TargetItem实例
        target = TargetItem(
            id="test",
            name="test item",
            original_text="test item",
            sheet_name="test sheet",
            row=1,
            level=1
        )

        # 访问data_type属性
        data_type = target.data_type

        # 模拟main.py中的访问
        display_type = "数值" if target.data_type == "number" else "文本"

        print(f"TargetItem.data_type test: PASSED")
        print(f"  - data_type value: {data_type}")
        print(f"  - display_type: {display_type}")
        return True

    except AttributeError as e:
        print(f"TargetItem.data_type test: FAILED - {e}")
        return False

def test_column_key_generation():
    """测试列键名生成"""
    try:
        from modules.data_extractor import DataExtractor

        # 创建虚拟的col_info对象
        class MockColInfo:
            def __init__(self, primary_header, secondary_header=""):
                self.primary_header = primary_header
                self.secondary_header = secondary_header
                self.column_index = 1

        # 创建提取器实例
        extractor = DataExtractor(None)

        # 测试不同的列头
        test_cases = [
            ("期末余额", "借方", "科目余额表测试", "期末余额_借方"),
            ("本期金额", "", "利润表", "本期金额"),
            ("期末余额", "", "资产负债表", "期末余额"),
        ]

        all_passed = True
        print(f"Column key generation test:")

        for primary, secondary, sheet_name, expected in test_cases:
            col_info = MockColInfo(primary, secondary)
            result = extractor._generate_column_key(col_info, sheet_name)

            if result == expected:
                print(f"  PASSED: '{primary}' + '{secondary}' -> '{result}'")
            else:
                print(f"  FAILED: '{primary}' + '{secondary}' -> '{result}' (expected '{expected}')")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"Column key generation test: FAILED - {e}")
        return False

def test_table_type_detection():
    """测试表类型检测"""
    try:
        test_cases = [
            ("科目余额表", "科目余额表"),
            ("试算平衡表", "试算平衡表"),
            ("资产负债表", "资产负债表"),
            ("利润表", "利润表"),
            ("现金流量表", "现金流量表"),
        ]

        print(f"Table type detection test:")
        all_passed = True

        for sheet_name, expected in test_cases:
            result = TableColumnRules.detect_table_type(sheet_name)
            if result == expected:
                print(f"  PASSED: '{sheet_name}' -> '{result}'")
            else:
                print(f"  FAILED: '{sheet_name}' -> '{result}' (expected '{expected}')")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"Table type detection test: FAILED - {e}")
        return False

def main():
    """主测试函数"""
    print("=== 修复验证测试 ===")

    # 测试1: TargetItem.data_type
    test1_passed = test_targetitem_datatype()

    # 测试2: 表类型检测
    test2_passed = test_table_type_detection()

    # 测试3: 列键名生成
    test3_passed = test_column_key_generation()

    print(f"\n=== 测试结果 ===")
    print(f"TargetItem.data_type: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Table type detection: {'PASSED' if test2_passed else 'FAILED'}")
    print(f"Column key generation: {'PASSED' if test3_passed else 'FAILED'}")

    if test1_passed and test2_passed and test3_passed:
        print(f"\n所有测试通过! 修复成功!")
    else:
        print(f"\n部分测试失败，需要进一步检查。")

if __name__ == "__main__":
    main()