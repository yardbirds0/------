#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公式转换模块
将内部DSL公式转换为Excel原生公式
"""

import re
import os
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from functools import lru_cache
from datetime import datetime
from pathlib import Path

from models.data_models import (
    WorkbookManager, TargetItem, SourceItem, MappingFormula
)

# Excel限制常量
MAX_EXCEL_FORMULA_LENGTH = 8192  # Excel公式最大长度
MAX_EXCEL_ROWS = 1048576  # Excel最大行数
MAX_EXCEL_COLS = 16384  # Excel最大列数 (XFD)

# 危险的公式前缀 (防止注入攻击)
DANGEROUS_FORMULA_PREFIXES = ['-', '+', '=', '@', '\t', '\r', '\n']


@dataclass
class ExcelReference:
    """Excel外部引用"""
    workbook_path: str      # 绝对路径
    workbook_name: str      # 文件名 (用于公式)
    sheet_name: str         # 工作表名
    cell_coordinate: str    # 如 "B5" 或 "B5:B10"
    item_name: str          # 原始项目名称
    is_external: bool = True  # 是否为外部引用

    def to_excel_formula_part(self, use_absolute_path: bool = True) -> str:
        """
        转换为Excel公式片段

        Args:
            use_absolute_path: 是否使用绝对路径

        Returns:
            Excel公式引用字符串
        """
        if self.is_external and use_absolute_path:
            # 外部工作簿引用: ='[D:\path\file.xlsx]Sheet'!A1
            # Excel要求路径用单引号包裹
            escaped_sheet = self.sheet_name.replace("'", "''")
            return f"'[{self.workbook_path}]{escaped_sheet}'!{self.cell_coordinate}"
        else:
            # 内部引用或相对引用: =Sheet!A1 或 ='Sheet Name'!A1
            # Excel要求包含特殊字符的工作表名用单引号包裹
            special_chars = [' ', "'", '(', ')', '（', '）', '[', ']', '/', '\\', '?', '*', ':', '-']
            needs_quotes = any(char in self.sheet_name for char in special_chars)

            if needs_quotes:
                escaped_sheet = self.sheet_name.replace("'", "''")
                return f"'{escaped_sheet}'!{self.cell_coordinate}"
            else:
                return f"{self.sheet_name}!{self.cell_coordinate}"


@dataclass
class ConversionError:
    """公式转换错误记录"""
    target_item: Optional[TargetItem]
    internal_formula: str
    error_type: str         # "cell_not_found" | "syntax_error" | "reference_error" | "security_error" | "circular_reference"
    error_message: str
    fallback_action: str    # "used_value" | "skipped" | "failed"
    timestamp: datetime = field(default_factory=datetime.now)


class SecurityValidator:
    """安全验证器"""

    @staticmethod
    def sanitize_item_name(item_name: str) -> str:
        """
        防止公式注入攻击

        Args:
            item_name: 项目名称

        Returns:
            安全的项目名称
        """
        if not item_name:
            return item_name

        # 先检查DDE攻击特征 (在添加单引号之前)
        dangerous_patterns = [
            r'=cmd\|',
            r'=dde\|',
            r'@SUM\(.*cmd.*\)',
            r'\\\\.*\\.*',  # UNC路径
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, item_name, re.IGNORECASE):
                raise ValueError(f"检测到潜在的公式注入攻击: {item_name}")

        # 然后检查危险前缀并转义
        if item_name[0] in DANGEROUS_FORMULA_PREFIXES:
            # 使用单引号包裹使其成为文字
            return "'" + item_name

        return item_name

    @staticmethod
    def sanitize_sheet_name(sheet_name: str) -> str:
        """
        清理工作表名称

        Args:
            sheet_name: 工作表名称

        Returns:
            ��全的工作表名称
        """
        if not sheet_name:
            return sheet_name

        # 检查危险前缀
        if sheet_name[0] in DANGEROUS_FORMULA_PREFIXES:
            # 使用单引号包裹
            return "'" + sheet_name

        return sheet_name

    @staticmethod
    def validate_cell_address(cell_address: str) -> Tuple[bool, str]:
        """
        验证单元格地址是否在Excel范围内

        Args:
            cell_address: 单元格地址 (如 "A1", "XFD1048576")

        Returns:
            (is_valid, error_message)
        """
        if not cell_address:
            return False, "单元格地址为空"

        # 解析单元格地址
        match = re.match(r'^([A-Z]+)(\d+)$', cell_address.upper())
        if not match:
            return False, f"无效的单元格地址格式: {cell_address}"

        col_letters = match.group(1)
        row_num = int(match.group(2))

        # 验证行数
        if row_num < 1 or row_num > MAX_EXCEL_ROWS:
            return False, f"行号超出Excel限制 (1-{MAX_EXCEL_ROWS}): {row_num}"

        # 验证列数 (将列字母转换为数字)
        col_num = 0
        for i, char in enumerate(reversed(col_letters)):
            col_num += (ord(char) - ord('A') + 1) * (26 ** i)

        if col_num < 1 or col_num > MAX_EXCEL_COLS:
            return False, f"列号超出Excel限制 (1-{MAX_EXCEL_COLS}, A-XFD): {col_letters}"

        return True, ""

    @staticmethod
    def validate_path(file_path: str, base_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        验证文件路径安全性,防止目录遍历攻击

        Args:
            file_path: 文件路径
            base_dir: 基础目录 (可选,默认为用户文档目录)

        Returns:
            (is_valid, error_message)
        """
        try:
            # 规范化路径
            resolved_path = Path(file_path).resolve()

            # 如果没有指定基础目录,使用用户文档目录
            if base_dir is None:
                import os
                base_dir = os.path.expanduser("~")

            base_path = Path(base_dir).resolve()

            # 检查路径是否在允许的目录下
            try:
                resolved_path.relative_to(base_path)
            except ValueError:
                # 如果不在用户目录下,检查是否在当前工作目录下
                try:
                    cwd = Path.cwd().resolve()
                    resolved_path.relative_to(cwd)
                except ValueError:
                    return False, f"路径不在允许的目录范围内: {file_path}"

            # 检查危险字符
            dangerous_chars = ['..', '<', '>', '|', '\x00']
            for char in dangerous_chars:
                if char in str(file_path):
                    return False, f"路径包含危险字符: {char}"

            return True, ""

        except (ValueError, OSError) as e:
            return False, f"无效的路径: {str(e)}"


class CircularReferenceDetector:
    """循环引用检测器"""

    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = {}

    def add_dependency(self, target: str, dependencies: List[str]):
        """
        添加依赖关系

        Args:
            target: 目标单元格
            dependencies: 依赖的单元格列表
        """
        if target not in self.dependency_graph:
            self.dependency_graph[target] = set()
        self.dependency_graph[target].update(dependencies)

    def detect_circular_reference(self, start_node: str, visited: Optional[Set[str]] = None,
                                   path: Optional[List[str]] = None) -> Optional[List[str]]:
        """
        检测循环引用

        Args:
            start_node: 起始节点
            visited: 已访问的节点集合
            path: 当前路径

        Returns:
            如果存在循环引用,返回循环路径;否则返回None
        """
        if visited is None:
            visited = set()
        if path is None:
            path = []

        # 如果当前节点已在路径中,说明存在循环
        if start_node in path:
            cycle_start = path.index(start_node)
            return path[cycle_start:] + [start_node]

        # 如果已访问过且没有循环,直接返回
        if start_node in visited:
            return None

        visited.add(start_node)
        path.append(start_node)

        # 检查所有依赖
        dependencies = self.dependency_graph.get(start_node, set())
        for dep in dependencies:
            cycle = self.detect_circular_reference(dep, visited, path.copy())
            if cycle:
                return cycle

        return None

    def validate_all(self) -> List[List[str]]:
        """
        检查所有节点的循环引用

        Returns:
            所有检测到的循环路径列表
        """
        cycles = []
        checked = set()

        for node in self.dependency_graph.keys():
            if node not in checked:
                cycle = self.detect_circular_reference(node)
                if cycle:
                    cycles.append(cycle)
                    checked.update(cycle)
                else:
                    checked.add(node)

        return cycles


class CellResolver:
    """单元格坐标解析器"""

    def __init__(self, workbook_manager: WorkbookManager):
        """
        初始化解析器

        Args:
            workbook_manager: 工作簿管理器
        """
        self.workbook_manager = workbook_manager
        self._build_indices()

    def _build_indices(self):
        """构建索引以加速查找"""
        # 构建 (sheet_name, item_name) -> cell_address 的索引
        self.target_index: Dict[Tuple[str, str], str] = {}
        self.source_index: Dict[Tuple[str, str], str] = {}

        # 构建 (sheet_name, item_name) -> source_item 的索引（用于三段式）
        self.source_item_index: Dict[Tuple[str, str], SourceItem] = {}

        # 构建 (sheet_name, column_name) -> column_letter 的索引
        self.column_letter_index: Dict[Tuple[str, str], str] = {}

        for target in self.workbook_manager.target_items.values():
            key = (target.sheet_name, target.name)
            self.target_index[key] = target.target_cell_address or ""

        for source in self.workbook_manager.source_items.values():
            key = (source.sheet_name, source.name)
            self.source_index[key] = source.cell_address or ""
            self.source_item_index[key] = source

        # 构建列名到列字母的索引
        for sheet_name, columns in self.workbook_manager.source_sheet_columns.items():
            for col_info in columns:
                col_name = col_info.get('header_text') or col_info.get('name', '')
                col_letter = col_info.get('column_letter', '')
                if col_name and col_letter:
                    self.column_letter_index[(sheet_name, col_name)] = col_letter

    @lru_cache(maxsize=10000)
    def resolve_cell_coordinate(
        self,
        sheet_name: str,
        item_name: str,
        search_targets: bool = False
    ) -> Optional[str]:
        """
        解析单元格坐标 (带缓存，支持前缀匹配)

        Args:
            sheet_name: 工作表名
            item_name: 项目名
            search_targets: 是否搜索目标项 (默认搜索源项)

        Returns:
            单元格地址,如 "D23"
        """
        key = (sheet_name, item_name)
        index = self.target_index if search_targets else self.source_index

        # 1. 直接查找
        cell_address = index.get(key)
        if cell_address:
            return cell_address

        # 2. 尝试添加常见财务报表前缀后查找
        # 常见前缀: "加："、"减："、"其中："、"*"等
        common_prefixes = [
            "加：", "减：", "其中：", "其中:",
            "*", "☆", "△", "▲", "√"
        ]

        for prefix in common_prefixes:
            prefixed_name = prefix + item_name
            prefixed_key = (sheet_name, prefixed_name)
            cell_address = index.get(prefixed_key)
            if cell_address:
                return cell_address

        return None

    def resolve_three_segment_reference(
        self,
        sheet_name: str,
        item_name: str,
        column_name: str
    ) -> Optional[str]:
        """
        解析三段式引用: [Sheet]![Item]![Column]（支持前缀匹配）

        Args:
            sheet_name: 工作表名
            item_name: 项目名
            column_name: 列名

        Returns:
            单元格地址,如 "D23"
        """
        # 1. 查找source_item获取行号
        source_key = (sheet_name, item_name)
        source_item = self.source_item_index.get(source_key)

        # 1.1 如果直接查找失败，尝试添加常见前缀
        if not source_item:
            common_prefixes = [
                "加：", "减：", "其中：", "其中:",
                "*", "☆", "△", "▲", "√"
            ]

            for prefix in common_prefixes:
                prefixed_name = prefix + item_name
                prefixed_key = (sheet_name, prefixed_name)
                source_item = self.source_item_index.get(prefixed_key)
                if source_item:
                    break

        if not source_item:
            return None

        row_number = source_item.row
        if not row_number:
            return None

        # 2. 查找列名对应的列字母
        # 尝试直接查找
        column_key = (sheet_name, column_name)
        column_letter = self.column_letter_index.get(column_key)

        # 如果没找到,尝试将下划线格式转换为空格-斜杠-空格格式
        if not column_letter and '_' in column_name:
            normalized_column_name = column_name.replace('_', ' / ')
            column_key = (sheet_name, normalized_column_name)
            column_letter = self.column_letter_index.get(column_key)

        if not column_letter:
            return None

        # 3. 组合单元格地址
        cell_address = f"{column_letter}{row_number}"
        return cell_address

    def get_merged_cell_ranges(self, sheet_name: str) -> List[str]:
        """
        获取合并单元格范围 (简化版,实际可能需要从Excel读取)

        Args:
            sheet_name: 工作表名

        Returns:
            合并单元格范围列表
        """
        # 简化实现:返回空列表
        # 实际应用中,可以从openpyxl读取工作表的merged_cells
        return []


class FormulaConverter:
    """公式转换核心类"""

    # 公式引用的正则表达式
    # 匹配 [Sheet]![Item]![Column] (三段式) 或 [Sheet]![Item] (两段式) 或 [Sheet]CellAddress
    REFERENCE_PATTERN = re.compile(
        r'\[([^\]]+)\]!\[([^\]]+)\]!\[([^\]]+)\]|'  # 三段式: [Sheet]![Item]![Column]
        r'\[([^\]]+)\]!\[([^\]]+)\]|'               # 两段式: [Sheet]![Item]
        r'\[([^\]]+)\]([A-Z]+\d+)'                  # 单元格: [Sheet]CellAddress
    )

    def __init__(self, workbook_manager: WorkbookManager):
        """
        初始化公式转换器

        Args:
            workbook_manager: 工作簿管理器
        """
        self.workbook_manager = workbook_manager
        self.cell_resolver = CellResolver(workbook_manager)
        self.conversion_cache: Dict[str, str] = {}
        self.errors: List[ConversionError] = []
        self.security_validator = SecurityValidator()
        self.circular_detector = CircularReferenceDetector()

    def convert_formula(
        self,
        internal_formula: str,
        target_item: Optional[TargetItem] = None,
        use_absolute_path: bool = True
    ) -> Tuple[str, List[ExcelReference], List[ConversionError]]:
        """
        转换单个公式

        Args:
            internal_formula: 内部DSL公式
            target_item: 目标项 (用于错误报告)
            use_absolute_path: 是否使用绝对路径

        Returns:
            (excel_formula, references, errors)
        """
        if not internal_formula or not internal_formula.strip():
            return "", [], []

        # 检查缓存
        cache_key = f"{internal_formula}|{use_absolute_path}"
        if cache_key in self.conversion_cache:
            return self.conversion_cache[cache_key], [], []

        references: List[ExcelReference] = []
        errors: List[ConversionError] = []
        excel_formula = internal_formula

        # 收集依赖用于循环引用检测
        target_cell_key = None
        if target_item and target_item.target_cell_address:
            target_cell_key = f"{target_item.sheet_name}!{target_item.target_cell_address}"
        dependencies = []

        # 查找所有引用
        matches = list(self.REFERENCE_PATTERN.finditer(internal_formula))

        # 从后向前替换,避免位置偏移
        for match in reversed(matches):
            if match.group(1) and match.group(2) and match.group(3):
                # 三段式: [Sheet]![Item]![Column]
                sheet_name = match.group(1)
                item_name = match.group(2)
                column_name = match.group(3)

                # 安全验证
                try:
                    item_name = self.security_validator.sanitize_item_name(item_name)
                    sheet_name = self.security_validator.sanitize_sheet_name(sheet_name)
                    column_name = self.security_validator.sanitize_item_name(column_name)
                except ValueError as e:
                    error = ConversionError(
                        target_item=target_item,
                        internal_formula=internal_formula,
                        error_type="security_error",
                        error_message=str(e),
                        fallback_action="failed"
                    )
                    errors.append(error)
                    return "", references, errors

                # 解析三段式引用
                cell_coord = self.cell_resolver.resolve_three_segment_reference(
                    sheet_name, item_name, column_name
                )

                if cell_coord:
                    # 验证单元格地址边界
                    is_valid, error_msg = self.security_validator.validate_cell_address(cell_coord)
                    if not is_valid:
                        error = ConversionError(
                            target_item=target_item,
                            internal_formula=internal_formula,
                            error_type="cell_bounds_error",
                            error_message=error_msg,
                            fallback_action="failed"
                        )
                        errors.append(error)
                        return "", references, errors

                    # 记录依赖
                    dep_key = f"{sheet_name}!{cell_coord}"
                    dependencies.append(dep_key)

                    # 创建Excel引用
                    source_workbook = self.workbook_manager.file_path
                    ref = ExcelReference(
                        workbook_path=source_workbook,
                        workbook_name=os.path.basename(source_workbook),
                        sheet_name=sheet_name,
                        cell_coordinate=cell_coord,
                        item_name=f"{item_name}:{column_name}",
                        is_external=False  # 同一个工作簿内的引用
                    )
                    references.append(ref)

                    # 替换公式中的引用
                    excel_ref = ref.to_excel_formula_part(use_absolute_path)
                    excel_formula = (
                        excel_formula[:match.start()] +
                        excel_ref +
                        excel_formula[match.end():]
                    )
                else:
                    # 未找到单元格
                    error = ConversionError(
                        target_item=target_item,
                        internal_formula=internal_formula,
                        error_type="cell_not_found",
                        error_message=f"未找到项目 '[{sheet_name}]![{item_name}]![{column_name}]' 的单元格地址",
                        fallback_action="skipped"
                    )
                    errors.append(error)

            elif match.group(4) and match.group(5):
                # 两段式: [Sheet]![Item]
                sheet_name = match.group(4)
                item_name = match.group(5)

                # 安全验证: 检查item_name和sheet_name
                try:
                    item_name = self.security_validator.sanitize_item_name(item_name)
                    sheet_name = self.security_validator.sanitize_sheet_name(sheet_name)
                except ValueError as e:
                    error = ConversionError(
                        target_item=target_item,
                        internal_formula=internal_formula,
                        error_type="security_error",
                        error_message=str(e),
                        fallback_action="failed"
                    )
                    errors.append(error)
                    return "", references, errors

                # 解析单元格坐标
                cell_coord = self.cell_resolver.resolve_cell_coordinate(
                    sheet_name, item_name
                )

                if not cell_coord:
                    # 尝试从目标项查找
                    cell_coord = self.cell_resolver.resolve_cell_coordinate(
                        sheet_name, item_name, search_targets=True
                    )

                if cell_coord:
                    # 验证单元格地址边界
                    is_valid, error_msg = self.security_validator.validate_cell_address(cell_coord)
                    if not is_valid:
                        error = ConversionError(
                            target_item=target_item,
                            internal_formula=internal_formula,
                            error_type="cell_bounds_error",
                            error_message=error_msg,
                            fallback_action="failed"
                        )
                        errors.append(error)
                        return "", references, errors

                    # 记录依赖
                    dep_key = f"{sheet_name}!{cell_coord}"
                    dependencies.append(dep_key)

                    # 创建Excel引用
                    source_workbook = self.workbook_manager.file_path
                    ref = ExcelReference(
                        workbook_path=source_workbook,
                        workbook_name=os.path.basename(source_workbook),
                        sheet_name=sheet_name,
                        cell_coordinate=cell_coord,
                        item_name=item_name
                    )
                    references.append(ref)

                    # 替换公式中的引用
                    excel_ref = ref.to_excel_formula_part(use_absolute_path)
                    excel_formula = (
                        excel_formula[:match.start()] +
                        excel_ref +
                        excel_formula[match.end():]
                    )
                else:
                    # 未找到单元格
                    error = ConversionError(
                        target_item=target_item,
                        internal_formula=internal_formula,
                        error_type="cell_not_found",
                        error_message=f"未找到项目 '[{sheet_name}]![{item_name}]' 的单元格地址",
                        fallback_action="skipped"
                    )
                    errors.append(error)

            elif match.group(6) and match.group(7):
                # [Sheet]CellAddress 格式
                sheet_name = match.group(6)
                cell_address = match.group(7)

                # 安全验证
                try:
                    sheet_name = self.security_validator.sanitize_sheet_name(sheet_name)
                except ValueError as e:
                    error = ConversionError(
                        target_item=target_item,
                        internal_formula=internal_formula,
                        error_type="security_error",
                        error_message=str(e),
                        fallback_action="failed"
                    )
                    errors.append(error)
                    return "", references, errors

                # 验证单元格地址边界
                is_valid, error_msg = self.security_validator.validate_cell_address(cell_address)
                if not is_valid:
                    error = ConversionError(
                        target_item=target_item,
                        internal_formula=internal_formula,
                        error_type="cell_bounds_error",
                        error_message=error_msg,
                        fallback_action="failed"
                    )
                    errors.append(error)
                    return "", references, errors

                # 记录依赖
                dep_key = f"{sheet_name}!{cell_address}"
                dependencies.append(dep_key)

                source_workbook = self.workbook_manager.file_path
                ref = ExcelReference(
                    workbook_path=source_workbook,
                    workbook_name=os.path.basename(source_workbook),
                    sheet_name=sheet_name,
                    cell_coordinate=cell_address,
                    item_name=cell_address
                )
                references.append(ref)

                # 替换公式中的引用
                excel_ref = ref.to_excel_formula_part(use_absolute_path)
                excel_formula = (
                    excel_formula[:match.start()] +
                    excel_ref +
                    excel_formula[match.end():]
                )

        # 添加循环引用依赖关系
        if target_cell_key and dependencies:
            self.circular_detector.add_dependency(target_cell_key, dependencies)

        # 验证公式长度
        if len(excel_formula) > MAX_EXCEL_FORMULA_LENGTH:
            error = ConversionError(
                target_item=target_item,
                internal_formula=internal_formula,
                error_type="formula_too_long",
                error_message=f"公式长度��过Excel限制 ({len(excel_formula)} > {MAX_EXCEL_FORMULA_LENGTH})",
                fallback_action="failed"
            )
            errors.append(error)
            return "", references, errors

        # 添加等号前缀
        if excel_formula and not excel_formula.startswith('='):
            excel_formula = '=' + excel_formula

        # 缓存结果
        if not errors:
            self.conversion_cache[cache_key] = excel_formula

        return excel_formula, references, errors

    def batch_convert(
        self,
        formulas: Dict[str, MappingFormula],
        use_absolute_path: bool = True
    ) -> Dict[str, Tuple[str, List[ExcelReference], List[ConversionError]]]:
        """
        批量转换公式

        Args:
            formulas: {target_id: MappingFormula}
            use_absolute_path: 是否使用绝对路径

        Returns:
            {target_id: (excel_formula, references, errors)}
        """
        results = {}

        for target_id, mapping_formula in formulas.items():
            target_item = self.workbook_manager.target_items.get(target_id)

            # 支持多列的映射公式
            if isinstance(mapping_formula, dict):
                # 多列格式: {column_key: MappingFormula}
                for column_key, formula_obj in mapping_formula.items():
                    internal_formula = formula_obj.formula
                    result_key = f"{target_id}#{column_key}"
                    results[result_key] = self.convert_formula(
                        internal_formula, target_item, use_absolute_path
                    )
            else:
                # 单公式格式
                internal_formula = mapping_formula.formula
                results[target_id] = self.convert_formula(
                    internal_formula, target_item, use_absolute_path
                )

        return results

    def validate_excel_formula(self, excel_formula: str) -> Tuple[bool, str]:
        """
        验证Excel公式语法

        Args:
            excel_formula: Excel公式

        Returns:
            (is_valid, error_message)
        """
        if not excel_formula:
            return False, "公式为空"

        if not excel_formula.startswith('='):
            return False, "公式必须以等号开头"

        if len(excel_formula) > 8192:
            return False, f"公式长度超过Excel限制 ({len(excel_formula)} > 8192)"

        # 简单的括号匹配检查
        open_count = excel_formula.count('(')
        close_count = excel_formula.count(')')
        if open_count != close_count:
            return False, f"括号不匹配 (左括号:{open_count}, 右括号:{close_count})"

        return True, ""

    def clear_cache(self):
        """清空缓存"""
        self.conversion_cache.clear()
        self.cell_resolver.resolve_cell_coordinate.cache_clear()

    def get_conversion_statistics(self) -> Dict[str, int]:
        """获取转换统计信息"""
        return {
            "cache_size": len(self.conversion_cache),
            "target_items": len(self.workbook_manager.target_items),
            "source_items": len(self.workbook_manager.source_items),
            "total_errors": len(self.errors)
        }
