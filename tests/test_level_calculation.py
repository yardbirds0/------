#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试级别计算功能
"""

import sys
import re
sys.path.insert(0, 'd:\\Code\\快报填写程序')

# 直接定义测试函数（从 data_extractor.py 复制）
def analyze_target_item_text(text: str):
    """
    分析目标项文本，识别层级关系

    优先级：
    1. 文字表述关系（"其中"、"减"、"加"等关键词）
    2. 缩进关系（前导空格数量）
    """
    if not text or len(text.strip()) < 2:
        return None

    # 1. 检测前导空格（缩进）
    indent_count = len(text) - len(text.lstrip())

    # 2. 检测层级关键词
    # 一级关键词：表示顶级项目
    level_1_keywords = ['一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、', '九、', '十、']
    level_1_patterns = [
        r'^[一二三四五六七八九十]+、',  # 中文编号
        r'^[（(]?[一二三四五六七八九十]+[)）]',  # 括号中文编号
    ]

    # 二级关键词：表示子项
    level_2_keywords = ['其中：', '其中', '包括：', '包括', '含：', '含']

    # 三级关键词：表示更细的子项
    level_3_keywords = ['减：', '减', '加：', '加', '明细：', '明细', '细项：', '细项']

    stripped_text = text.strip()

    # 3. 检测编号模式
    numbering = ''
    clean_name = stripped_text

    numbering_patterns = [
        r'^(\d+)\.\s*(.+)',  # "1. xxx"
        r'^(\d+)\s+(.+)',    # "1 xxx"
        r'^(\d+)、\s*(.+)',  # "1、xxx"
        r'^\((\d+)\)\s*(.+)',  # "(1) xxx"
    ]

    for pattern in numbering_patterns:
        match = re.match(pattern, stripped_text)
        if match:
            numbering = match.group(1)
            clean_name = match.group(2).rstrip()
            break

    # 4. 根据关键词和缩进计算层级
    # 优先使用文字表述关系判断
    calculated_level = indent_count  # 默认使用缩进值

    # 检查一级关键词
    is_level_1 = False
    for keyword in level_1_keywords:
        if stripped_text.startswith(keyword):
            is_level_1 = True
            calculated_level = 0  # 一级项目缩进为0
            break

    if not is_level_1:
        for pattern in level_1_patterns:
            if re.match(pattern, stripped_text):
                is_level_1 = True
                calculated_level = 0
                break

    # 检查二级关键词（只有在非一级的情况下）
    if not is_level_1:
        for keyword in level_2_keywords:
            if keyword in stripped_text:
                # 如果有缩进，使用缩进值；否则设置为较小的缩进
                if indent_count == 0:
                    calculated_level = 2  # 默认二级缩进
                break

        # 检查三级关键词
        for keyword in level_3_keywords:
            if keyword in stripped_text:
                # 如果有缩进，使用缩进值；否则设置为更大的缩进
                if indent_count == 0:
                    calculated_level = 4  # 默认三级缩进
                break

    return {
        'numbering': numbering,
        'clean_name': clean_name,
        'level': calculated_level  # 使用计算出的层级值
    }

# 测试用例
test_cases = [
    ("1.营业总收入", "一级项目，无缩进"),
    ("  其中：主营业务收入", "二级项目，有缩进和关键词"),
    ("    减：营业成本", "三级项目，有缩进和关键词"),
    ("一、资产", "一级项目，中文编号"),
    ("  流动资产", "二级项目，只有缩进"),
    ("    存货", "三级项目，只有缩进"),
    ("      其中：原材料", "四级项目，缩进+关键词"),
    ("2.营业支出", "一级项目，数字编号"),
    ("包括：管理费用", "二级项目，关键词"),
]

print("=" * 80)
print("级别计算测试")
print("=" * 80)

for text, description in test_cases:
    result = analyze_target_item_text(text)
    if result:
        indent_count = len(text) - len(text.lstrip())
        print(f"\n文本: '{text}'")
        print(f"描述: {description}")
        print(f"缩进空格数: {indent_count}")
        print(f"计算的level值: {result['level']}")
        print(f"清理后名称: '{result['clean_name']}'")
        print(f"编号: '{result['numbering']}'")
    else:
        print(f"\n文本: '{text}' - 分析失败")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
