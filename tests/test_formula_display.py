#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试公式多行显示格式 - 验证逻辑正确后再应用到主程序
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.excel_utils import parse_formula_references_three_segment

def format_formula_multiline(formula: str, result_text: str = None) -> str:
    """
    将公式格式化为多行显示

    目标格式：
    - 每个来源项单独一行（运算符跟随在引用后面）
    - 结果单独一行

    示例输入：
    "[表1]![项目1]![列1] + [表2]![项目2]![列2]"
    result_text = "3419294.52"

    期望输出：
    [表1]![项目1]![列1] +
    [表2]![项目2]![列2]
    → 3419294.52
    """

    # 解析引用
    refs = parse_formula_references_three_segment(formula)

    if not refs:
        # 无引用，直接返回原公式
        if result_text:
            return f"{formula}\n→ {result_text}"
        return formula

    # 按引用分割公式，每个引用后保留运算符
    lines = []
    remaining_formula = formula

    for i, ref in enumerate(refs):
        full_ref = ref['full_reference']

        # 找到引用在剩余公式中的位置
        pos = remaining_formula.find(full_ref)

        if pos >= 0:
            # 提取引用本身
            ref_text = full_ref

            # 提取引用后的部分
            after_ref = remaining_formula[pos + len(full_ref):]

            # 如果不是最后一个引用，提取运算符
            operator = ""
            if i < len(refs) - 1:
                # 提取运算符（去除前后空格，找到+、-、*、/）
                after_stripped = after_ref.strip()
                for op in ['+', '-', '*', '/']:
                    if after_stripped.startswith(op):
                        operator = f" {op}"
                        break

            # 构建这一行：引用 + 运算符
            lines.append(ref_text + operator)

            # 更新剩余公式（跳过当前引用和运算符）
            remaining_formula = after_ref

    # 添加结果行
    if result_text:
        lines.append(f"→ {result_text}")

    return "\n".join(lines)


# 测试案例
print("=" * 100)
print("测试公式多行显示格式")
print("=" * 100)

test_cases = [
    {
        "formula": "[上年科目余额表]![银行存款　_交通银行]![年初余额_借方] + [上年科目余额表]![银行存款　_交通银行]![期初余额_借方]",
        "result": "3419294.52"
    },
    {
        "formula": "[科目余额表（5级含未过账）]![银行存款]![内本:内蒙古]",
        "result": "7377542.51"
    },
    {
        "formula": "[表1]![项目A]![列1] - [表2]![项目B]![列2] * [表3]![项目C]![列3]",
        "result": "12345.67"
    },
    {
        "formula": "[表1]![项目1]![列1] + [表2]![项目2]![列2] - [表3]![项目3]![列3]",
        "result": "999999.99"
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n测试 {i}:")
    print(f"  原始公式: {test['formula']}")
    print(f"  结果值: {test['result']}")

    formatted = format_formula_multiline(test['formula'], test['result'])

    print(f"\n  多行显示:")
    for line_num, line in enumerate(formatted.split('\n'), 1):
        print(f"    行{line_num}: {line}")

    # 检查显示正确性
    lines = formatted.split('\n')

    # 验证1：结果行应该是最后一行
    last_line = lines[-1]
    if last_line.startswith("→"):
        print(f"  ✓ 结果在独立行: {last_line}")
    else:
        print(f"  ✗ 错误：结果不在独立行")

    # 验证2：应该有运算符（如果公式包含运算符）
    if "+" in test['formula'] or "-" in test['formula'] or "*" in test['formula'] or "/" in test['formula']:
        has_operator = any("+" in line or "-" in line or "*" in line or "/" in line for line in lines[:-1])
        if has_operator:
            print(f"  ✓ 运算符已保留")
        else:
            print(f"  ✗ 错误：运算符丢失")

    # 验证3：显示文本长度合理（不应该被截断）
    max_line_length = max(len(line) for line in lines)
    print(f"  最长行长度: {max_line_length} 字符")

    print()

print("=" * 100)
print("测试完成")
print("=" * 100)

print("\n建议的显示格式:")
print("  1. 每个引用占一行，保留前后的运算符")
print("  2. 结果单独占一行，前面有→符号")
print("  3. 确保所有文本可见，不被截断（...）")
print("\n如果显示正常，将此逻辑应用到main.py")
