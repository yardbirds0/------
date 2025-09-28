#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表格列规则定义模块
定义不同表类型的数据列规则，支持多数据列识别和显示
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ColumnRule:
    """数据列规则定义"""
    key: str          # 列键名，用于在data_columns中存储
    display: str      # 显示名称
    level: int = 1    # 列级别：1为一级列，2为二级列
    parent: str = ""  # 父列名称（用于二级列）
    order: int = 0    # 排序顺序


class TableColumnRules:
    """表格列规则管理器"""

    # 表类型列规则定义
    RULES = {
        "科目余额表": {
            "display_name": "科目余额表",
            "primary_column": "期末余额_借方",
            "columns": [
                ColumnRule("科目代码", "科目代码", 1, "", 0),
                ColumnRule("年初余额_借方", "年初借方", 2, "年初余额", 1),
                ColumnRule("年初余额_贷方", "年初贷方", 2, "年初余额", 2),
                ColumnRule("年初余额_合计", "年初合计", 2, "年初余额", 3),
                ColumnRule("期初余额_借方", "期初借方", 2, "期初余额", 4),
                ColumnRule("期初余额_贷方", "期初贷方", 2, "期初余额", 5),
                ColumnRule("期初余额_合计", "期初合计", 2, "期初余额", 6),
                ColumnRule("本期发生额_借方", "本期借方", 2, "本期发生额", 7),
                ColumnRule("本期发生额_贷方", "本期贷方", 2, "本期发生额", 8),
                ColumnRule("本期发生额_合计", "本期合计", 2, "本期发生额", 9),
                ColumnRule("期末余额_借方", "期末借方", 2, "期末余额", 10),
                ColumnRule("期末余额_贷方", "期末贷方", 2, "期末余额", 11),
                ColumnRule("期末余额_合计", "期末合计", 2, "期末余额", 12),
            ]
        },

        "试算平衡表": {
            "display_name": "试算平衡表",
            "primary_column": "期末余额_借方",
            "columns": [
                ColumnRule("科目代码", "科目代码", 1, "", 0),
                ColumnRule("年初余额_借方", "年初借方", 2, "年初余额", 1),
                ColumnRule("年初余额_贷方", "年初贷方", 2, "年初余额", 2),
                ColumnRule("期初余额_借方", "期初借方", 2, "期初余额", 3),
                ColumnRule("期初余额_贷方", "期初贷方", 2, "期初余额", 4),
                ColumnRule("本期发生额_借方", "本期借方", 2, "本期发生额", 5),
                ColumnRule("本期发生额_贷方", "本期贷方", 2, "本期发生额", 6),
                ColumnRule("期末余额_借方", "期末借方", 2, "期末余额", 7),
                ColumnRule("期末余额_贷方", "期末贷方", 2, "期末余额", 8),
            ]
        },

        "资产负债表": {
            "display_name": "资产负债表",
            "primary_column": "期末余额",
            "columns": [
                ColumnRule("期末余额", "期末金额", 1, "", 1),
                ColumnRule("年初余额", "年初金额", 1, "", 2),
            ]
        },

        "利润表": {
            "display_name": "利润表",
            "primary_column": "本期金额",
            "columns": [
                ColumnRule("本期金额", "本期金额", 1, "", 1),
                ColumnRule("上期金额", "上期金额", 1, "", 2),
                ColumnRule("本年累计", "本年累计", 1, "", 3),
                ColumnRule("上年累计", "上年累计", 1, "", 4),
            ]
        },

        "现金流量表": {
            "display_name": "现金流量表",
            "primary_column": "本期金额",
            "columns": [
                ColumnRule("本期金额", "本期金额", 1, "", 1),
                ColumnRule("上期金额", "上期金额", 1, "", 2),
            ]
        }
    }

    @classmethod
    def get_table_types(cls) -> List[str]:
        """获取所有支持的表类型"""
        return list(cls.RULES.keys())

    @classmethod
    def detect_table_type(cls, sheet_name: str) -> Optional[str]:
        """根据sheet名称检测表类型"""
        sheet_name_lower = sheet_name.lower()

        # 优先精确匹配
        for table_type in cls.RULES:
            if table_type in sheet_name:
                return table_type

        # 模糊匹配关键词
        if any(keyword in sheet_name_lower for keyword in ["科目余额", "余额表"]):
            return "科目余额表"
        elif any(keyword in sheet_name_lower for keyword in ["试算", "平衡"]):
            return "试算平衡表"
        elif any(keyword in sheet_name_lower for keyword in ["资产负债", "负债表"]):
            return "资产负债表"
        elif any(keyword in sheet_name_lower for keyword in ["利润", "损益"]):
            return "利润表"
        elif any(keyword in sheet_name_lower for keyword in ["现金流量", "流量表"]):
            return "现金流量表"

        return None

    @classmethod
    def get_table_rule(cls, table_type: str) -> Optional[Dict]:
        """获取指定表类型的规则"""
        return cls.RULES.get(table_type)

    @classmethod
    def get_column_rules(cls, table_type: str) -> List[ColumnRule]:
        """获取指定表类型的列规则"""
        rule = cls.get_table_rule(table_type)
        if rule:
            return sorted(rule["columns"], key=lambda x: x.order)
        return []

    @classmethod
    def get_display_headers(cls, table_type: str, include_item_name: bool = True) -> List[str]:
        """获取显示列头"""
        headers = []

        # 第一列：标识符列
        if table_type and table_type in ["科目余额表", "试算平衡表"]:
            headers.append("科目代码")
        else:
            headers.append("级别/行号")

        # 第二列：项目名称
        if include_item_name:
            headers.append("项目名称")

        # 后续列：数据列
        column_rules = cls.get_column_rules(table_type)
        if column_rules:
            # 跳过第一个规则（已作为第一列处理）
            data_rules = column_rules[1:] if len(column_rules) > 1 else []
            for rule in data_rules:
                headers.append(rule.display)

        return headers

    @classmethod
    def get_primary_column(cls, table_type: str) -> Optional[str]:
        """获取主要数据列的键名"""
        rule = cls.get_table_rule(table_type)
        if rule:
            return rule["primary_column"]
        return None

    @classmethod
    def get_column_key_mapping(cls, table_type: str) -> Dict[str, str]:
        """获取列键名到显示名的映射"""
        mapping = {}
        column_rules = cls.get_column_rules(table_type)
        for rule in column_rules:
            mapping[rule.key] = rule.display
        return mapping

    @classmethod
    def validate_data_columns(cls, table_type: str, data_columns: Dict[str, any]) -> Tuple[bool, List[str]]:
        """验证数据列是否符合规则"""
        rule = cls.get_table_rule(table_type)
        if not rule:
            return False, [f"未知的表类型: {table_type}"]

        missing_columns = []
        column_rules = cls.get_column_rules(table_type)

        for rule in column_rules:
            if rule.key not in data_columns:
                missing_columns.append(rule.display)

        return len(missing_columns) == 0, missing_columns

    @classmethod
    def get_ordered_column_keys(cls, table_type: str) -> List[str]:
        """获取按顺序排列的列键名"""
        column_rules = cls.get_column_rules(table_type)
        return [rule.key for rule in column_rules]

    @classmethod
    def format_column_value(cls, value: any) -> str:
        """格式化列值显示"""
        if value is None or value == '':
            return ''

        if isinstance(value, (int, float)):
            if value == 0:
                return '0'
            elif abs(value) >= 10000:
                return f"{value:,.0f}"
            else:
                return f"{value:.2f}"

        return str(value)

    @classmethod
    def get_parent_columns(cls, table_type: str) -> Dict[str, List[str]]:
        """获取父列和子列的映射关系"""
        column_rules = cls.get_column_rules(table_type)
        parent_map = {}

        for rule in column_rules:
            if rule.parent:
                if rule.parent not in parent_map:
                    parent_map[rule.parent] = []
                parent_map[rule.parent].append(rule.key)

        return parent_map