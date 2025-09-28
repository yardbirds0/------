#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
层级关系解析工具
专门用于分析财务报表项目的层级结构
"""

import re
from typing import List, Dict, Any, Optional


def analyze_hierarchy_patterns(items: List[str]) -> Dict[str, Any]:
    """
    分析一组项目的层级模式

    Args:
        items: 项目文本列表

    Returns:
        Dict[str, Any]: 层级模式分析结果
    """
    patterns = {
        'numbering_styles': set(),
        'indent_levels': set(),
        'keywords': set(),
        'level_distribution': {},
        'suggestions': []
    }

    for item in items:
        if not item:
            continue

        # 检测编号样式
        numbering_match = re.match(r'^(\d+\.|\([^)]+\)|[一二三四五六七八九十]+、|[①②③④⑤⑥⑦⑧⑨⑩]+)', item.strip())
        if numbering_match:
            patterns['numbering_styles'].add(numbering_match.group(1))

        # 检测缩进
        indent = len(item) - len(item.lstrip())
        if indent > 0:
            patterns['indent_levels'].add(indent)

        # 检测关键词
        for keyword in ['其中', '减', '加', '包括', '含', '小计', '合计']:
            if keyword in item:
                patterns['keywords'].add(keyword)

    return patterns


def clean_item_text(text: str) -> str:
    """
    清理项目文本，移除编号和多余空格

    Args:
        text: 原始文本

    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""

    text = text.strip()

    # 移除各种编号格式
    patterns_to_remove = [
        r'^\d+\.\s*',  # "1. "
        r'^[一二三四五六七八九十]+、\s*',  # "一、"
        r'^\([^)]+\)\s*',  # "(1)" 或 "(一)"
        r'^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]+\s*',  # "①"
        r'^[ABCDEFGHIJKLMNOPQRSTUVWXYZ]\.\s*',  # "A."
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text)

    return text.strip()


def detect_level_by_content(text: str) -> int:
    """
    根据内容特征判断层级

    Args:
        text: 项目文本

    Returns:
        int: 建议的层级
    """
    if not text:
        return 1

    text_lower = text.lower()

    # 一级项目特征
    level_1_patterns = [
        r'^[一二三四五六七八九十]+、',  # 中文编号
        r'^\d+\.',  # 数字编号
        r'^资产', r'^负债', r'^所有者权益', r'^收入', r'^成本', r'^费用'
    ]

    for pattern in level_1_patterns:
        if re.match(pattern, text):
            return 1

    # 二级项目特征
    if any(keyword in text for keyword in ['其中', '减', '加']):
        return 2

    # 三级项目特征
    if any(keyword in text for keyword in ['明细', '细项', '分项']):
        return 3

    # 默认层级
    return 1


def validate_hierarchy(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    验证和修正层级关系

    Args:
        items: 包含层级信息的项目列表

    Returns:
        List[Dict[str, Any]]: 修正后的项目列表
    """
    if not items:
        return items

    # 按顺序处理
    for i, item in enumerate(items):
        current_level = item.get('level', 1)

        # 检查与前一项的关系
        if i > 0:
            prev_level = items[i-1].get('level', 1)

            # 层级不能跳跃太大
            if current_level - prev_level > 2:
                item['level'] = prev_level + 1
                item['level_adjusted'] = True

            # 层级不能小于1
            if current_level < 1:
                item['level'] = 1
                item['level_adjusted'] = True

        # 检查与后一项的关系
        if i < len(items) - 1:
            next_level = items[i+1].get('level', 1)

            # 如果下一项层级明显更高，可能当前项层级过低
            if next_level - current_level > 2:
                # 这里可以添加层级调整逻辑
                pass

    return items


def build_tree_structure(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    构建树状结构

    Args:
        items: 项目列表

    Returns:
        List[Dict[str, Any]]: 树状结构
    """
    if not items:
        return []

    # 添加层级关系
    stack = []  # 用于追踪父级的栈

    for item in items:
        current_level = item.get('level', 1)

        # 弹出层级大于等于当前层级的项目
        while stack and stack[-1]['level'] >= current_level:
            stack.pop()

        # 设置父级关系
        if stack:
            parent = stack[-1]
            item['parent_id'] = parent.get('id')
            if 'children' not in parent:
                parent['children'] = []
            parent['children'].append(item)
        else:
            item['parent_id'] = None

        # 初始化子项目列表
        if 'children' not in item:
            item['children'] = []

        # 加入栈
        stack.append(item)

    # 返回顶级项目
    return [item for item in items if item.get('parent_id') is None]


def extract_hierarchy_keywords(text: str) -> List[str]:
    """
    提取层级关键词

    Args:
        text: 项目文本

    Returns:
        List[str]: 关键词列表
    """
    keywords = []

    # 层级指示词
    hierarchy_indicators = [
        '其中', '其中：', '其中:',
        '减', '减：', '减:',
        '加', '加：', '加:',
        '包括', '包括：', '包括:',
        '含', '含：', '含:',
        '小计', '合计', '总计'
    ]

    for keyword in hierarchy_indicators:
        if keyword in text:
            keywords.append(keyword)

    return keywords


def suggest_hierarchy_improvements(items: List[Dict[str, Any]]) -> List[str]:
    """
    建议层级结构改进

    Args:
        items: 项目列表

    Returns:
        List[str]: 改进建议
    """
    suggestions = []

    if not items:
        return suggestions

    # 统计层级分布
    level_counts = {}
    for item in items:
        level = item.get('level', 1)
        level_counts[level] = level_counts.get(level, 0) + 1

    # 检查层级分布是否合理
    max_level = max(level_counts.keys()) if level_counts else 1

    if max_level > 5:
        suggestions.append(f"层级过深(最大层级: {max_level})，建议简化结构")

    if 1 not in level_counts:
        suggestions.append("缺少一级项目，建议添加顶级分类")

    # 检查层级跳跃
    for i, item in enumerate(items[1:], 1):
        current_level = item.get('level', 1)
        prev_level = items[i-1].get('level', 1)

        if current_level - prev_level > 2:
            suggestions.append(f"第{i+1}项存在层级跳跃，从{prev_level}级跳到{current_level}级")

    # 检查空层级
    all_levels = set(range(1, max_level + 1))
    existing_levels = set(level_counts.keys())
    missing_levels = all_levels - existing_levels

    if missing_levels:
        suggestions.append(f"缺少层级: {sorted(missing_levels)}")

    return suggestions