#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表格模式分析器 - 智能识别财务表格类型和列头结构
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

class TableType(Enum):
    """表格类型枚举"""
    BALANCE_SHEET = "资产负债表"
    INCOME_STATEMENT = "利润表"
    CASH_FLOW = "现金流量表"
    TRIAL_BALANCE = "科目余额表"
    UNKNOWN = "未知表格"

@dataclass
class ColumnInfo:
    """列信息"""
    column_index: int  # 列索引
    column_letter: str  # 列字母
    primary_header: str  # 一级列头
    secondary_header: str = ""  # 二级列头
    data_type: str = "unknown"  # 数据类型：debit, credit, amount, text
    is_numeric: bool = False  # 是否为数值列

@dataclass
class TableSchema:
    """表格模式"""
    table_type: TableType
    header_rows: int  # 列头行数
    data_start_row: int  # 数据开始行
    name_columns: List[int]  # 项目名称列
    code_columns: List[int]  # 编码列
    data_columns: List[ColumnInfo]  # 数据列信息
    has_hierarchy: bool = False  # 是否有层级结构

class TableSchemaAnalyzer:
    """表格模式分析器"""

    def __init__(self):
        # 财务表格关键词模式
        self.table_type_patterns = {
            TableType.BALANCE_SHEET: [
                r'资产负债表', r'资产.*负债', r'balance.*sheet',
                r'资产总计', r'负债总计', r'所有者权益'
            ],
            TableType.INCOME_STATEMENT: [
                r'利润表', r'损益表', r'income.*statement', r'profit.*loss',
                r'营业收入', r'营业利润', r'净利润'
            ],
            TableType.CASH_FLOW: [
                r'现金流量表', r'cash.*flow',
                r'经营活动', r'投资活动', r'筹资活动'
            ],
            TableType.TRIAL_BALANCE: [
                r'科目余额表', r'trial.*balance', r'余额表',
                r'科目代码', r'科目名称', r'期初余额', r'期末余额'
            ]
        }

        # 列头关键词模式
        self.column_patterns = {
            'debit': [r'借方', r'debit', r'dr'],
            'credit': [r'贷方', r'credit', r'cr'],
            'beginning': [r'期初', r'年初', r'beginning', r'opening'],
            'ending': [r'期末', r'年末', r'ending', r'closing'],
            'current': [r'本期', r'本年', r'current', r'this.*year'],
            'previous': [r'上期', r'上年', r'去年', r'previous', r'last.*year'],
            'amount': [r'金额', r'数额', r'amount', r'value'],
            'balance': [r'余额', r'balance']
        }

    def analyze_table_schema(self, sheet: Worksheet) -> TableSchema:
        """分析表格模式"""
        # 识别表格类型
        table_type = self._identify_table_type(sheet)

        # 分析列头结构
        header_info = self._analyze_headers(sheet)

        # 识别数据列
        data_columns = self._identify_data_columns(sheet, header_info)

        # 识别名称和编码列
        name_columns, code_columns = self._identify_name_code_columns(sheet, table_type)

        # 确定数据开始行
        data_start_row = self._find_data_start_row(sheet, header_info['header_rows'])

        return TableSchema(
            table_type=table_type,
            header_rows=header_info['header_rows'],
            data_start_row=data_start_row,
            name_columns=name_columns,
            code_columns=code_columns,
            data_columns=data_columns,
            has_hierarchy=(table_type == TableType.TRIAL_BALANCE or len(code_columns) > 0)
        )

    def _identify_table_type(self, sheet: Worksheet) -> TableType:
        """识别表格类型"""
        # 检查工作表名称
        sheet_name = sheet.title.lower()

        # 收集前10行的所有文本
        all_text = []
        for row in range(1, min(11, sheet.max_row + 1)):
            for col in range(1, min(11, sheet.max_column + 1)):
                cell = sheet.cell(row=row, column=col)
                if cell.value:
                    all_text.append(str(cell.value).lower())

        combined_text = ' '.join([sheet_name] + all_text)

        # 匹配表格类型
        for table_type, patterns in self.table_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    return table_type

        return TableType.UNKNOWN

    def _analyze_headers(self, sheet: Worksheet) -> Dict[str, Any]:
        """分析列头结构"""
        header_rows = 1
        max_scan_rows = min(5, sheet.max_row)

        # 寻找列头结束位置（开始出现数值或明显的数据行）
        for row in range(2, max_scan_rows + 1):
            numeric_count = 0
            total_cells = 0

            for col in range(1, min(16, sheet.max_column + 1)):
                cell = sheet.cell(row=row, column=col)
                if cell.value is not None:
                    total_cells += 1
                    if isinstance(cell.value, (int, float)) or self._is_numeric_string(cell.value):
                        numeric_count += 1

            # 如果数值比例超过30%，认为是数据行
            if total_cells > 0 and (numeric_count / total_cells) > 0.3:
                break
            else:
                header_rows = row

        return {
            'header_rows': header_rows,
            'has_merged_cells': self._check_merged_cells(sheet, header_rows)
        }

    def _identify_data_columns(self, sheet: Worksheet, header_info: Dict) -> List[ColumnInfo]:
        """识别数据列"""
        data_columns = []
        header_rows = header_info['header_rows']

        for col in range(1, min(16, sheet.max_column + 1)):
            col_letter = openpyxl.utils.get_column_letter(col)

            # 获取列头文本
            primary_header = ""
            secondary_header = ""

            if header_rows >= 1:
                cell1 = sheet.cell(row=1, column=col)
                if cell1.value:
                    primary_header = str(cell1.value).strip()

            if header_rows >= 2:
                cell2 = sheet.cell(row=2, column=col)
                if cell2.value:
                    secondary_header = str(cell2.value).strip()

            # 检查是否为数值列
            is_numeric = self._check_column_numeric(sheet, col, header_rows + 1)

            if is_numeric or primary_header or secondary_header:
                # 识别数据类型
                data_type = self._identify_data_type(primary_header, secondary_header)

                column_info = ColumnInfo(
                    column_index=col,
                    column_letter=col_letter,
                    primary_header=primary_header,
                    secondary_header=secondary_header,
                    data_type=data_type,
                    is_numeric=is_numeric
                )
                data_columns.append(column_info)

        return data_columns

    def _identify_name_code_columns(self, sheet: Worksheet, table_type: TableType) -> Tuple[List[int], List[int]]:
        """识别名称列和编码列"""
        name_columns = []
        code_columns = []

        # 检查前5列
        for col in range(1, min(6, sheet.max_column + 1)):
            # 获取列头
            header_text = ""
            for row in range(1, 4):
                cell = sheet.cell(row=row, column=col)
                if cell.value:
                    header_text += str(cell.value).lower()

            # 检查几行数据来判断列的性质
            sample_values = []
            for row in range(4, min(10, sheet.max_row + 1)):
                cell = sheet.cell(row=row, column=col)
                if cell.value:
                    sample_values.append(str(cell.value).strip())

            if not sample_values:
                continue

            # 判断是否为编码列
            if self._is_code_column(header_text, sample_values):
                code_columns.append(col)
            # 判断是否为名称列
            elif self._is_name_column(header_text, sample_values, table_type):
                name_columns.append(col)

        return name_columns, code_columns

    def _identify_data_type(self, primary: str, secondary: str) -> str:
        """识别数据类型"""
        combined = (primary + " " + secondary).lower()

        # 检查各种类型
        for data_type, patterns in self.column_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return data_type

        return "amount"

    def _is_code_column(self, header_text: str, sample_values: List[str]) -> bool:
        """判断是否为编码列"""
        # 检查列头
        if re.search(r'代码|code|编号|number', header_text, re.IGNORECASE):
            return True

        # 检查数据特征
        if not sample_values:
            return False

        numeric_count = 0
        for value in sample_values[:5]:  # 检查前5个值
            # 科目代码通常是纯数字或以数字开头
            if re.match(r'^\d{4,8}', value):
                numeric_count += 1

        return numeric_count >= len(sample_values) * 0.7

    def _is_name_column(self, header_text: str, sample_values: List[str], table_type: TableType) -> bool:
        """判断是否为名称列"""
        # 检查列头
        name_patterns = [r'名称|项目|科目|name|item|account']
        for pattern in name_patterns:
            if re.search(pattern, header_text, re.IGNORECASE):
                return True

        # 检查数据特征
        if not sample_values:
            return False

        chinese_count = 0
        for value in sample_values[:5]:
            # 包含中文且不是纯数字
            if re.search(r'[\u4e00-\u9fff]', value) and not re.match(r'^\d+\.?\d*$', value):
                chinese_count += 1

        return chinese_count >= len(sample_values) * 0.7

    def _check_column_numeric(self, sheet: Worksheet, col: int, start_row: int) -> bool:
        """检查列是否为数值列"""
        numeric_count = 0
        total_count = 0

        for row in range(start_row, min(start_row + 10, sheet.max_row + 1)):
            cell = sheet.cell(row=row, column=col)
            if cell.value is not None:
                total_count += 1
                if isinstance(cell.value, (int, float)) or self._is_numeric_string(cell.value):
                    numeric_count += 1

        return total_count > 0 and (numeric_count / total_count) >= 0.5

    def _is_numeric_string(self, value) -> bool:
        """判断是否为数值字符串"""
        if not isinstance(value, str):
            return False

        try:
            # 去除常见的格式符号
            cleaned = value.replace(',', '').replace(' ', '').replace('(', '-').replace(')', '')
            float(cleaned)
            return True
        except ValueError:
            return False

    def _check_merged_cells(self, sheet: Worksheet, header_rows: int) -> bool:
        """检查是否有合并单元格"""
        for row in range(1, header_rows + 1):
            for merged_range in sheet.merged_cells.ranges:
                if merged_range.min_row <= row <= merged_range.max_row:
                    return True
        return False

    def _find_data_start_row(self, sheet: Worksheet, header_rows: int) -> int:
        """寻找数据开始行"""
        # 从列头后一行开始寻找
        for row in range(header_rows + 1, min(header_rows + 5, sheet.max_row + 1)):
            # 检查这一行是否有有效数据
            has_name = False
            has_number = False

            for col in range(1, min(6, sheet.max_column + 1)):
                cell = sheet.cell(row=row, column=col)
                if cell.value:
                    value_str = str(cell.value).strip()
                    if re.search(r'[\u4e00-\u9fff]', value_str):  # 包含中文
                        has_name = True
                    elif isinstance(cell.value, (int, float)) or self._is_numeric_string(value_str):
                        has_number = True

            if has_name or has_number:
                return row

        return header_rows + 1

if __name__ == "__main__":
    # 测试代码
    print("表格模式分析器模块")