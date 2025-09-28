#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel处理工具函数
包含Excel文件操作的通用工具函数
"""

import openpyxl
from typing import List, Dict, Tuple, Any, Optional, Union
from datetime import datetime
import re


def safe_get_cell_value(sheet, row: int, column: Union[int, str]) -> Any:
    """
    安全获取单元格值

    Args:
        sheet: openpyxl工作表对象
        row: 行号（1开始）
        column: 列号（整数）或列字母（字符串）

    Returns:
        Any: 单元格值，如果出错则返回None
    """
    try:
        if isinstance(column, str):
            cell = sheet[f"{column}{row}"]
        else:
            cell = sheet.cell(row=row, column=column)
        return cell.value
    except:
        return None


def get_merged_cell_value(sheet, row: int, column: int) -> Any:
    """
    获取合并单元格的值

    Args:
        sheet: openpyxl工作表对象
        row: 行号
        column: 列号

    Returns:
        Any: 单元格值
    """
    cell = sheet.cell(row=row, column=column)

    # 检查是否为合并单元格
    for merged_range in sheet.merged_cells.ranges:
        if cell.coordinate in merged_range:
            # 返回合并范围左上角单元格的值
            top_left = merged_range.start_cell
            return sheet.cell(top_left.row, top_left.column).value

    return cell.value


def find_header_row(sheet, keywords: List[str], max_search_rows: int = 20) -> Optional[int]:
    """
    查找表头行

    Args:
        sheet: openpyxl工作表对象
        keywords: 要查找的关键词列表
        max_search_rows: 最大搜索行数

    Returns:
        Optional[int]: 表头行号，如果没找到返回None
    """
    for row_num in range(1, min(max_search_rows + 1, sheet.max_row + 1)):
        row_text = ""
        for col_num in range(1, min(sheet.max_column + 1, 10)):  # 只检查前10列
            cell_value = safe_get_cell_value(sheet, row_num, col_num)
            if cell_value:
                row_text += str(cell_value).lower()

        # 检查是否包含关键词
        if any(keyword.lower() in row_text for keyword in keywords):
            return row_num

    return None


def extract_number_from_text(text: str) -> Optional[Union[int, float]]:
    """
    从文本中提取数字

    Args:
        text: 输入文本

    Returns:
        Optional[Union[int, float]]: 提取的数字，如果没有数字返回None
    """
    if not isinstance(text, str):
        return None

    # 移除常见的非数字字符，保留数字、小数点、负号
    cleaned_text = re.sub(r'[^\d\.\-]', '', text)

    if not cleaned_text:
        return None

    try:
        # 尝试转换为浮点数
        if '.' in cleaned_text:
            return float(cleaned_text)
        else:
            return int(cleaned_text)
    except ValueError:
        return None


def is_numeric_cell(cell_value: Any) -> bool:
    """
    判断单元格值是否为数值

    Args:
        cell_value: 单元格值

    Returns:
        bool: 是否为数值
    """
    if cell_value is None:
        return False

    if isinstance(cell_value, (int, float)):
        return True

    # 尝试从文本中提取数字
    if isinstance(cell_value, str):
        return extract_number_from_text(cell_value) is not None

    return False


def format_cell_address(row: int, column: Union[int, str]) -> str:
    """
    格式化单元格地址

    Args:
        row: 行号
        column: 列号（整数）或列字母（字符串）

    Returns:
        str: 格式化的单元格地址，如'A1'
    """
    if isinstance(column, int):
        column_letter = openpyxl.utils.get_column_letter(column)
    else:
        column_letter = column.upper()

    return f"{column_letter}{row}"


def parse_cell_address(address: str) -> Tuple[int, str]:
    """
    解析单元格地址

    Args:
        address: 单元格地址，如'A1'

    Returns:
        Tuple[int, str]: (行号, 列字母)
    """
    match = re.match(r'([A-Z]+)(\d+)', address.upper())
    if match:
        column_letter = match.group(1)
        row_number = int(match.group(2))
        return row_number, column_letter
    else:
        raise ValueError(f"无效的单元格地址: {address}")


def get_column_values(sheet, column: Union[int, str], start_row: int = 1,
                     end_row: Optional[int] = None) -> List[Any]:
    """
    获取指定列的所有值

    Args:
        sheet: openpyxl工作表对象
        column: 列号或列字母
        start_row: 开始行号
        end_row: 结束行号，如果为None则到最后一行

    Returns:
        List[Any]: 列值列表
    """
    if end_row is None:
        end_row = sheet.max_row

    values = []
    for row_num in range(start_row, end_row + 1):
        value = safe_get_cell_value(sheet, row_num, column)
        values.append(value)

    return values


def find_empty_cells(sheet, column: Union[int, str], start_row: int = 1,
                    end_row: Optional[int] = None) -> List[int]:
    """
    查找指定列中的空单元格

    Args:
        sheet: openpyxl工作表对象
        column: 列号或列字母
        start_row: 开始行号
        end_row: 结束行号

    Returns:
        List[int]: 空单元格的行号列表
    """
    if end_row is None:
        end_row = sheet.max_row

    empty_rows = []
    for row_num in range(start_row, end_row + 1):
        value = safe_get_cell_value(sheet, row_num, column)
        if value is None or (isinstance(value, str) and not value.strip()):
            empty_rows.append(row_num)

    return empty_rows


def calculate_fill_rate(sheet) -> float:
    """
    计算工作表的填充率

    Args:
        sheet: openpyxl工作表对象

    Returns:
        float: 填充率百分比
    """
    if not sheet.max_row or not sheet.max_column:
        return 0.0

    total_cells = sheet.max_row * sheet.max_column
    non_empty_cells = 0

    for row in sheet.iter_rows():
        for cell in row:
            if cell.value is not None and str(cell.value).strip():
                non_empty_cells += 1

    return round(non_empty_cells / total_cells * 100, 2) if total_cells > 0 else 0.0


def backup_excel_file(file_path: str) -> str:
    """
    备份Excel文件

    Args:
        file_path: 原文件路径

    Returns:
        str: 备份文件路径
    """
    from pathlib import Path
    import shutil

    original_path = Path(file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{original_path.stem}_backup_{timestamp}{original_path.suffix}"
    backup_path = original_path.parent / backup_name

    shutil.copy2(file_path, backup_path)
    return str(backup_path)


def create_excel_copy(source_path: str, target_path: str) -> bool:
    """
    创建Excel文件副本

    Args:
        source_path: 源文件路径
        target_path: 目标文件路径

    Returns:
        bool: 是否成功
    """
    try:
        import shutil
        shutil.copy2(source_path, target_path)
        return True
    except Exception as e:
        print(f"创建文件副本失败: {str(e)}")
        return False


def write_values_to_excel(file_path: str, sheet_name: str,
                         values: Dict[str, Any], backup: bool = True) -> bool:
    """
    向Excel文件写入值

    Args:
        file_path: Excel文件路径
        sheet_name: 工作表名称
        values: 要写入的值 {单元格地址: 值}
        backup: 是否创建备份

    Returns:
        bool: 是否成功
    """
    try:
        # 创建备份
        if backup:
            backup_path = backup_excel_file(file_path)
            print(f"已创建备份文件: {backup_path}")

        # 打开工作簿
        workbook = openpyxl.load_workbook(file_path)

        if sheet_name not in workbook.sheetnames:
            print(f"工作表 '{sheet_name}' 不存在")
            return False

        sheet = workbook[sheet_name]

        # 写入值
        for cell_address, value in values.items():
            try:
                row, column = parse_cell_address(cell_address)
                sheet[cell_address] = value
                print(f"写入 {cell_address}: {value}")
            except Exception as e:
                print(f"写入 {cell_address} 失败: {str(e)}")

        # 保存文件
        workbook.save(file_path)
        workbook.close()

        return True

    except Exception as e:
        print(f"写入Excel文件失败: {str(e)}")
        return False


def validate_excel_file(file_path: str) -> Tuple[bool, str]:
    """
    验证Excel文件

    Args:
        file_path: Excel文件路径

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)
    """
    try:
        import os

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"

        # 检查文件扩展名
        if not file_path.lower().endswith(('.xlsx', '.xls')):
            return False, f"不支持的文件格式: {file_path}"

        # 尝试打开文件
        workbook = openpyxl.load_workbook(file_path, data_only=True)

        # 检查是否有工作表
        if not workbook.sheetnames:
            workbook.close()
            return False, "文件中没有工作表"

        workbook.close()
        return True, "文件验证成功"

    except Exception as e:
        return False, f"文件验证失败: {str(e)}"


def get_sheet_statistics(sheet) -> Dict[str, Any]:
    """
    获取工作表统计信息

    Args:
        sheet: openpyxl工作表对象

    Returns:
        Dict[str, Any]: 统计信息
    """
    stats = {
        'name': sheet.title,
        'max_row': sheet.max_row or 0,
        'max_column': sheet.max_column or 0,
        'total_cells': 0,
        'non_empty_cells': 0,
        'numeric_cells': 0,
        'text_cells': 0,
        'formula_cells': 0,
        'fill_rate': 0.0
    }

    if sheet.max_row and sheet.max_column:
        stats['total_cells'] = sheet.max_row * sheet.max_column

        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is not None and str(cell.value).strip():
                    stats['non_empty_cells'] += 1

                    if isinstance(cell.value, (int, float)):
                        stats['numeric_cells'] += 1
                    elif isinstance(cell.value, str):
                        if cell.value.strip().startswith('='):
                            stats['formula_cells'] += 1
                        else:
                            stats['text_cells'] += 1

        stats['fill_rate'] = round(stats['non_empty_cells'] / stats['total_cells'] * 100, 2)

    return stats


def validate_formula_syntax(formula: str) -> Tuple[bool, Optional[str]]:
    """
    验证公式语法

    Args:
        formula: 公式字符串

    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not formula or not formula.strip():
        return False, "公式不能为空"

    formula = formula.strip()

    # 检查引用格式 [工作表名]![项目名]
    reference_pattern = r'\[([^\[\]]+)\]!\[([^\[\]]+)\]'

    # 查找所有引用
    references = re.findall(reference_pattern, formula)

    if not references:
        # 检查是否包含数字或基本运算符
        if re.match(r'^[\d\+\-\*/\(\)\s\.]+$', formula):
            return True, None
        else:
            return False, "公式必须包含有效的引用格式 [工作表名]![项目名] 或数字运算"

    # 验证引用格式
    for sheet_name, item_name in references:
        if not sheet_name.strip():
            return False, f"工作表名不能为空"
        if not item_name.strip():
            return False, f"项目名不能为空"

    # 检查运算符
    # 移除所有引用，检查剩余部分是否只包含有效字符
    formula_without_refs = re.sub(reference_pattern, '1', formula)

    # 允许的字符：数字、运算符、括号、空格
    if not re.match(r'^[\d\+\-\*/\(\)\s\.]+$', formula_without_refs):
        return False, "公式包含无效字符，只允许使用 +、-、*、/、() 运算符"

    # 检查括号匹配
    if formula_without_refs.count('(') != formula_without_refs.count(')'):
        return False, "括号不匹配"

    # 尝试评估语法（不执行实际计算）
    try:
        # 简单的语法检查
        test_formula = formula_without_refs.replace(' ', '')

        # 检查是否有连续的运算符
        if re.search(r'[\+\-\*/]{2,}', test_formula):
            return False, "包含连续的运算符"

        # 检查运算符位置
        if re.search(r'^[\+\*/]|[\+\-\*/]$', test_formula):
            return False, "运算符位置不正确"

    except Exception as e:
        return False, f"语法错误: {str(e)}"

    return True, None


def parse_formula_references(formula: str) -> List[Tuple[str, str]]:
    """
    解析公式中的引用

    Args:
        formula: 公式字符串

    Returns:
        List[Tuple[str, str]]: 引用列表 [(工作表名, 项目名), ...]
    """
    if not formula:
        return []

    reference_pattern = r'\[([^\[\]]+)\]!\[([^\[\]]+)\]'
    references = re.findall(reference_pattern, formula)

    return references


def build_formula_reference(sheet_name: str, item_name: str) -> str:
    """
    构建标准的公式引用

    Args:
        sheet_name: 工作表名
        item_name: 项目名

    Returns:
        str: 标准引用格式
    """
    return f"[{sheet_name}]![{item_name}]"


def format_formula_display(formula: str, max_length: int = 50) -> str:
    """
    格式化公式显示

    Args:
        formula: 原始公式
        max_length: 最大显示长度

    Returns:
        str: 格式化后的公式
    """
    if not formula:
        return ""

    if len(formula) <= max_length:
        return formula

    return formula[:max_length-3] + "..."


def evaluate_formula_with_values(formula: str, value_map: Dict[str, Any]) -> Tuple[bool, Union[float, str]]:
    """
    使用给定的值评估公式

    Args:
        formula: 公式字符串
        value_map: 值映射 {引用字符串: 值}

    Returns:
        Tuple[bool, Union[float, str]]: (是否成功, 计算结果或错误信息)
    """
    try:
        # 首先验证公式语法
        is_valid, error_msg = validate_formula_syntax(formula)
        if not is_valid:
            return False, error_msg

        # 替换引用为实际值
        eval_formula = formula

        reference_pattern = r'\[([^\[\]]+)\]!\[([^\[\]]+)\]'
        references = re.findall(reference_pattern, formula)

        for sheet_name, item_name in references:
            reference = build_formula_reference(sheet_name, item_name)

            if reference in value_map:
                value = value_map[reference]

                # 确保值是数字
                if isinstance(value, str):
                    try:
                        value = float(value) if '.' in value else int(value)
                    except ValueError:
                        return False, f"引用 {reference} 的值不是有效数字: {value}"

                eval_formula = eval_formula.replace(reference, str(value))
            else:
                return False, f"找不到引用 {reference} 的值"

        # 安全地评估数学表达式
        try:
            # 移除空格
            eval_formula = eval_formula.replace(' ', '')

            # 使用eval计算（注意：在生产环境中应该使用更安全的方法）
            result = eval(eval_formula)

            return True, result

        except ZeroDivisionError:
            return False, "除零错误"
        except Exception as e:
            return False, f"计算错误: {str(e)}"

    except Exception as e:
        return False, f"公式评估失败: {str(e)}"