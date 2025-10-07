#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心数据模型定义 - PySide6版本
定义系统中使用的所有核心数据结构，支持新的公式格式
"""

from typing import Dict, List, Optional, Union, Any, Tuple, Literal
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from datetime import datetime
import uuid

from utils.excel_utils import convert_formula_to_new_format, build_formula_reference_simple


@dataclass
class PromptTemplate:
    """提示词模板数据模型"""

    group_name: str = "默认提示词"
    title: str = ""
    content: str = ""
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def first_line(self) -> str:
        """返回内容的第一行（去除首尾空白）"""
        text = (self.content or "").strip()
        if not text:
            return ""
        return text.splitlines()[0]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_name": self.group_name,
            "title": self.title,
            "content": self.content,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        if not data:
            return cls()
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except ValueError:
                updated_at = datetime.now()
        elif not isinstance(updated_at, datetime):
            updated_at = datetime.now()

        return cls(
            group_name=data.get("group_name", "默认提示词"),
            title=data.get("title", ""),
            content=data.get("content", ""),
            updated_at=updated_at,
        )


@dataclass
class TokenUsageInfo:
    """AI 调用的 Token 用量信息"""

    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    status: Literal["complete", "missing"] = "complete"
    recorded_at: datetime = field(default_factory=datetime.now)

    PLACEHOLDER_TEXT = "无token用量数据"

    @classmethod
    def from_usage_payload(cls, payload: Optional[Dict[str, Any]]) -> "TokenUsageInfo":
        """根据 OpenAI usage 字段创建实例。"""
        if not payload:
            return cls.missing()

        def to_int(value: Any) -> Optional[int]:
            if value is None:
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        prompt = to_int(payload.get("prompt_tokens"))
        completion = to_int(payload.get("completion_tokens"))
        total = to_int(payload.get("total_tokens"))

        if prompt is None and completion is None and total is None:
            return cls.missing()

        # 补全 total，如缺失则尝试从已知值计算
        if total is None and prompt is not None and completion is not None:
            total = prompt + completion

        return cls(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=total,
            status="complete",
        )

    @classmethod
    def from_metadata(cls, metadata: Optional[Dict[str, Any]]) -> "TokenUsageInfo":
        if not metadata:
            return cls.missing()

        status = metadata.get("status", "complete")
        prompt = metadata.get("prompt_tokens")
        completion = metadata.get("completion_tokens")
        total = metadata.get("total_tokens")
        recorded_at = metadata.get("recorded_at")

        if isinstance(recorded_at, str):
            try:
                recorded_at = datetime.fromisoformat(recorded_at)
            except ValueError:
                recorded_at = datetime.now()
        elif not isinstance(recorded_at, datetime):
            recorded_at = datetime.now()

        def to_int(value: Any) -> Optional[int]:
            if value is None:
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        info = cls(
            prompt_tokens=to_int(prompt),
            completion_tokens=to_int(completion),
            total_tokens=to_int(total),
            status="complete" if status == "complete" else "missing",
            recorded_at=recorded_at,
        )

        if info.status != "complete" or not info.has_all_tokens:
            return cls.missing()
        return info

    @classmethod
    def missing(cls) -> "TokenUsageInfo":
        return cls(
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            status="missing",
        )

    @property
    def has_all_tokens(self) -> bool:
        return (
            self.prompt_tokens is not None
            and self.completion_tokens is not None
            and self.total_tokens is not None
        )

    def as_text(self) -> str:
        if self.status != "complete" or not self.has_all_tokens:
            return self.PLACEHOLDER_TEXT
        return (
            f"输入：{self.prompt_tokens}；"
            f"输出：{self.completion_tokens}，"
            f"总：{self.total_tokens}"
        )

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "recorded_at": self.recorded_at.isoformat(),
        }


class SheetType(Enum):
    """工作表类型枚举"""
    FLASH_REPORT = "flash_report"  # 快报表
    DATA_SOURCE = "data_source"    # 数据来源表


class FormulaStatus(Enum):
    """映射公式状态枚举"""
    EMPTY = "empty"           # 空公式
    PENDING = "pending"       # 待处理
    AI_GENERATED = "ai_generated"  # AI生成
    USER_MODIFIED = "user_modified"  # 用户修改
    VALIDATED = "validated"   # 已验证
    CALCULATED = "calculated" # 已计算
    ERROR = "error"          # 有错误


@dataclass
class CellReference:
    """单元格引用信息"""
    sheet_name: str
    cell_address: str  # 如'A1', 'D5'
    row: int
    column: str  # 列字母，如'A', 'D'

    def __post_init__(self):
        if not self.cell_address and self.row and self.column:
            self.cell_address = f"{self.column}{self.row}"


@dataclass
class TargetItem:
    """目标项数据模型 - 快报表中需要填充的项目"""

    id: str  # 唯一标识符
    name: str  # 项目名称（清理后的文本）
    original_text: str  # 原始文本（未清理）
    sheet_name: str  # 所属工作表名
    row: int  # 所在行号
    level: int = 0  # 原始缩进值（来自Excel）
    hierarchical_level: int = 1  # 计算出的层级深度（1为顶级）
    hierarchical_number: str = "1"  # 层级编号（如1、1.1、1.1.1、2、2.1）
    parent_id: Optional[str] = None  # 父项目ID
    children_ids: List[str] = field(default_factory=list)  # 子项目ID列表

    # 单元格引用信息
    cell_reference: Optional[CellReference] = None
    target_cell_address: str = ""  # 待填入数据的单元格地址

    # 显示和状态信息
    is_empty_target: bool = True  # 是否为需要填充的空目标
    display_index: str = ""  # 显示序号
    indentation_level: int = 0  # 缩进级别

    # 元数据
    extracted_time: datetime = field(default_factory=datetime.now)
    notes: str = ""  # 备注信息
    columns: Dict[str, 'TargetColumnEntry'] = field(default_factory=dict)  # 目标项列信息

    def __post_init__(self):
        if not self.id:
            self.id = f"target_{uuid.uuid4().hex[:8]}"

        if not self.target_cell_address and self.cell_reference:
            self.target_cell_address = self.cell_reference.cell_address

    @property
    def cell_address(self) -> str:
        """cell_address属性，返回target_cell_address的值"""
        return self.target_cell_address


@dataclass
class SourceItem:
    """来源项数据模型 - 数据来源表中的数据项"""

    id: str  # 唯一标识符
    sheet_name: str  # 所属工作表名
    name: str  # 项目名称
    cell_address: str  # 单元格地址
    row: int  # 行号
    column: str  # 列字母
    value: Union[int, float, str, None] = None  # 数值

    # 扩展信息
    original_text: str = ""  # 原始文本
    value_type: str = "unknown"  # 值类型: number, text, formula, etc.
    is_calculated: bool = False  # 是否为计算值

    # 层级信息（新增）
    account_code: str = ""  # 科目代码
    hierarchy_level: int = 0  # 层级深度（0为根级）
    parent_code: str = ""  # 父级科目代码
    full_name_with_indent: str = ""  # 带缩进的完整名称
    has_children: bool = False  # 是否有子项

    # 多列数据支持（新增）
    data_columns: Dict[str, Any] = field(default_factory=dict)  # 多列数据字典
    column_info: Dict[str, str] = field(default_factory=dict)  # 列信息描述
    table_type: str = "unknown"  # 表格类型

    # 数据分类（新增）
    data_category: str = ""  # 数据分类（beginning, ending, current, previous等）
    data_type_detail: str = ""  # 数据类型详情（debit, credit, amount等）

    # 元数据
    extracted_time: datetime = field(default_factory=datetime.now)
    notes: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"source_{uuid.uuid4().hex[:8]}"

        if not self.cell_address and self.row and self.column:
            self.cell_address = f"{self.column}{self.row}"

        # 如果没有设置带缩进的名称，使用原名称
        if not self.full_name_with_indent:
            indent = "  " * self.hierarchy_level
            if self.account_code:
                self.full_name_with_indent = f"{indent}{self.account_code} {self.name}"
            else:
                self.full_name_with_indent = f"{indent}{self.name}"

    def add_data_column(self, column_name: str, value: Any, column_desc: str = ""):
        """添加数据列"""
        self.data_columns[column_name] = value
        if column_desc:
            self.column_info[column_name] = column_desc

    def get_data_column(self, column_name: str, default=None):
        """获取数据列值"""
        return self.data_columns.get(column_name, default)

    def get_all_data_columns(self) -> Dict[str, Any]:
        """获取所有数据列"""
        return self.data_columns.copy()

    def set_hierarchy_info(self, account_code: str, level: int, parent_code: str = ""):
        """设置层级信息"""
        self.account_code = account_code
        self.hierarchy_level = level
        self.parent_code = parent_code

        # 更新带缩进的名称
        indent = "  " * level
        self.full_name_with_indent = f"{indent}{account_code} {self.name}"

    def to_reference_string(self) -> str:
        """生成新格式的引用字符串"""
        return build_formula_reference_simple(self.sheet_name, self.cell_address)

    def to_display_dict(self) -> Dict[str, Any]:
        """转换为显示用的字典"""
        display_data = {
            "名称": self.full_name_with_indent,
            "科目代码": self.account_code,
            "层级": self.hierarchy_level,
            "工作表": self.sheet_name,
            "单元格": self.cell_address,
            "主要数值": self.value
        }

        # 添加所有数据列
        for col_name, col_value in self.data_columns.items():
            display_data[col_name] = col_value

        return display_data


@dataclass
class TargetColumnEntry:
    """目标项列定义"""

    key: str
    display_name: str
    column_index: int
    column_letter: str
    is_numeric: bool = False
    data_type: str = "unknown"
    header_text: str = ""
    is_data_column: bool = True
    cell_address: str = ""
    source_value: Any = None
    is_placeholder: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "column_index": self.column_index,
            "column_letter": self.column_letter,
            "is_numeric": self.is_numeric,
            "data_type": self.data_type,
            "header_text": self.header_text,
            "is_data_column": self.is_data_column,
            "cell_address": self.cell_address,
            "source_value": self.source_value,
            "is_placeholder": self.is_placeholder,
        }


@dataclass
class MappingFormula:
    """映射公式数据模型（支持多列）"""

    target_id: str  # 关联的目标项ID
    column_key: str = "__default__"  # 列键
    column_name: str = ""  # 列名称
    formula: str = ""  # 公式内容（新格式）
    constant_value: Optional[Union[int, float, str]] = None  # 固定值映射
    status: FormulaStatus = FormulaStatus.EMPTY

    # 计算结果
    calculation_result: Optional[Union[int, float]] = None
    last_calculated: Optional[datetime] = None
    calculation_time: float = 0.0  # 计算耗时（毫秒）

    # 验证信息
    is_valid: bool = False
    validation_error: str = ""
    last_validated: Optional[datetime] = None

    # AI相关
    ai_confidence: float = 0.0  # AI生成的置信度
    ai_reasoning: str = ""  # AI推理过程

    # 元数据
    created_time: datetime = field(default_factory=datetime.now)
    modified_time: datetime = field(default_factory=datetime.now)
    version: int = 1  # 版本号
    notes: str = ""

    def update_formula(
        self,
        new_formula: str,
        status: FormulaStatus = FormulaStatus.USER_MODIFIED,
        column_name: Optional[str] = None,
    ):
        """更新公式"""
        self.formula = convert_formula_to_new_format(new_formula)
        self.status = status
        self.modified_time = datetime.now()
        self.version += 1
        self.is_valid = False  # 需要重新验证
        if column_name:
            self.column_name = column_name
        if new_formula.strip():
            self.constant_value = None

    def __post_init__(self):
        self.formula = convert_formula_to_new_format(self.formula)
        if not self.column_key:
            self.column_key = "__default__"

    def set_calculation_result(self, result: Union[int, float], calculation_time: float = 0.0):
        """设置计算结果"""
        self.calculation_result = result
        self.last_calculated = datetime.now()
        self.calculation_time = calculation_time
        self.status = FormulaStatus.CALCULATED

    def set_validation_result(self, is_valid: bool, error_message: str = ""):
        """设置验证结果"""
        self.is_valid = is_valid
        self.validation_error = error_message
        self.last_validated = datetime.now()
        if is_valid:
            self.status = FormulaStatus.VALIDATED
        else:
            self.status = FormulaStatus.ERROR


@dataclass
class WorksheetInfo:
    """工作表信息"""

    name: str  # 工作表名称
    sheet_type: SheetType  # 工作表类型
    target_count: int = 0  # 目标项数量
    source_count: int = 0  # 来源项数量

    # 元数据
    max_row: int = 0
    max_column: int = 0
    has_merged_cells: bool = False
    data_range: str = ""  # 数据范围，如'A1:D100'

    # 处理状态
    is_processed: bool = False
    extraction_time: Optional[datetime] = None
    notes: str = ""


@dataclass
class WorkbookManager:
    """工作簿管理器 - 管理整个工作簿的数据"""

    file_path: str = ""  # Excel文件路径

    # 工作表信息
    worksheets: Dict[str, WorksheetInfo] = field(default_factory=dict)
    flash_report_sheets: List[str] = field(default_factory=list)
    data_source_sheets: List[str] = field(default_factory=list)
    source_sheet_columns: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    target_sheet_columns: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    source_sheet_header_rows: Dict[str, int] = field(default_factory=dict)
    target_sheet_header_rows: Dict[str, int] = field(default_factory=dict)

    # 数据项
    target_items: Dict[str, TargetItem] = field(default_factory=dict)
    source_items: Dict[str, SourceItem] = field(default_factory=dict)
    mapping_formulas: Dict[str, Dict[str, MappingFormula]] = field(default_factory=dict)
    calculation_results: Dict[str, Dict[str, 'CalculationResult']] = field(default_factory=dict)

    # 列配置（按工作表名存储）
    column_configs: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    # 统计信息
    total_target_items: int = 0
    total_source_items: int = 0
    total_formulas: int = 0

    # 处理状态
    is_loaded: bool = False
    is_data_extracted: bool = False
    last_processed: Optional[datetime] = None

    # 元数据
    created_time: datetime = field(default_factory=datetime.now)
    notes: str = ""

    @property
    def file_name(self) -> str:
        """从文件路径获取文件名"""
        if self.file_path:
            return os.path.basename(self.file_path)
        return ""

    @file_name.setter
    def file_name(self, value: str):
        self.file_path = value or ""

    @property
    def flash_reports(self) -> List[str]:
        """兼容旧字段名，返回快报表列表"""
        return self.flash_report_sheets

    @flash_reports.setter
    def flash_reports(self, sheets: List[str]):
        self.flash_report_sheets = list(sheets or [])

    @property
    def data_sources(self) -> List[str]:
        """兼容旧字段名，返回数据来源表列表"""
        return self.data_source_sheets

    @data_sources.setter
    def data_sources(self, sheets: List[str]):
        self.data_source_sheets = list(sheets or [])

    def add_worksheet(self, name: str, sheet_type: SheetType) -> WorksheetInfo:
        """添加工作表信息"""
        worksheet_info = WorksheetInfo(name=name, sheet_type=sheet_type)
        self.worksheets[name] = worksheet_info

        if sheet_type == SheetType.FLASH_REPORT:
            if name not in self.flash_report_sheets:
                self.flash_report_sheets.append(name)
        else:
            if name not in self.data_source_sheets:
                self.data_source_sheets.append(name)

        return worksheet_info

    def add_target_item(self, target_item: TargetItem):
        """添加目标项"""
        self.target_items[target_item.id] = target_item
        self.total_target_items = len(self.target_items)

        # 更新工作表统计
        if target_item.sheet_name in self.worksheets:
            self.worksheets[target_item.sheet_name].target_count += 1

    def add_source_item(self, source_item: SourceItem):
        """添加来源项"""
        self.source_items[source_item.id] = source_item
        self.total_source_items = len(self.source_items)

        # 更新工作表统计
        if source_item.sheet_name in self.worksheets:
            self.worksheets[source_item.sheet_name].source_count += 1

    def add_mapping_formula(self, target_id: str, formula: MappingFormula):
        """添加映射公式"""
        existing = self.mapping_formulas.get(target_id)
        if isinstance(existing, MappingFormula):
            existing = {existing.column_key or "__default__": existing}
            self.mapping_formulas[target_id] = existing
        target_map = self.mapping_formulas.setdefault(target_id, {})
        column_key = formula.column_key or "__default__"
        target_map[column_key] = formula
        self.total_formulas = sum(len(columns) for columns in self.mapping_formulas.values())

    def get_mapping(self, target_id: str, column_key: Optional[str] = None) -> Optional[MappingFormula]:
        """获取指定目标项与列的映射公式"""
        key = column_key or "__default__"
        existing = self.mapping_formulas.get(target_id)
        if isinstance(existing, MappingFormula):
            return existing if (existing.column_key or "__default__") == key else None
        return (existing or {}).get(key) if existing else None

    def ensure_mapping(
        self,
        target_id: str,
        column_key: str,
        column_name: str = "",
    ) -> MappingFormula:
        """确保目标项列映射存在，不存在则创建"""
        existing = self.mapping_formulas.get(target_id)
        if isinstance(existing, MappingFormula):
            existing = {existing.column_key or "__default__": existing}
            self.mapping_formulas[target_id] = existing
        target_map = self.mapping_formulas.setdefault(target_id, {})
        mapping = target_map.get(column_key)
        if not mapping:
            mapping = MappingFormula(
                target_id=target_id,
                column_key=column_key,
                column_name=column_name,
            )
            target_map[column_key] = mapping
            self.total_formulas = sum(len(columns) for columns in self.mapping_formulas.values())
        elif column_name and not mapping.column_name:
            mapping.column_name = column_name
        return mapping

    def remove_mapping(self, target_id: str, column_key: Optional[str] = None):
        """移除映射公式"""
        if target_id not in self.mapping_formulas:
            return
        if column_key is None:
            removed = self.mapping_formulas.pop(target_id, None)
            if removed:
                self.total_formulas = sum(len(columns) for columns in self.mapping_formulas.values())
            self.calculation_results.pop(target_id, None)
            return

        target_map = self.mapping_formulas.get(target_id)
        if isinstance(target_map, MappingFormula):
            if (target_map.column_key or "__default__") == column_key:
                self.mapping_formulas.pop(target_id, None)
                self.calculation_results.pop(target_id, None)
                self.total_formulas = sum(len(columns) for columns in self.mapping_formulas.values())
            return
        target_map = target_map or {}
        if column_key in target_map:
            del target_map[column_key]
            if not target_map:
                self.mapping_formulas.pop(target_id, None)
                self.calculation_results.pop(target_id, None)
            self.total_formulas = sum(len(columns) for columns in self.mapping_formulas.values())

    def iter_mappings(self, target_id: str) -> List[MappingFormula]:
        """遍历目标项的所有映射"""
        existing = self.mapping_formulas.get(target_id)
        if isinstance(existing, MappingFormula):
            return [existing]
        return list((existing or {}).values())

    def get_target_children(self, target_id: str) -> List[TargetItem]:
        """获取目标项的子项"""
        target = self.target_items.get(target_id)
        if not target:
            return []

        children = []
        for child_id in target.children_ids:
            child = self.target_items.get(child_id)
            if child:
                children.append(child)

        return children

    def get_target_parent(self, target_id: str) -> Optional[TargetItem]:
        """获取目标项的父项"""
        target = self.target_items.get(target_id)
        if not target or not target.parent_id:
            return None

        return self.target_items.get(target.parent_id)

    def search_source_items(self, query: str) -> List[SourceItem]:
        """搜索来源项"""
        query_lower = query.lower()
        results = []

        for source_item in self.source_items.values():
            if (query_lower in source_item.name.lower() or
                query_lower in source_item.sheet_name.lower()):
                results.append(source_item)

        return results

    def get_formula_statistics(self) -> Dict[str, int]:
        """获取公式统计信息"""
        stats = {status.value: 0 for status in FormulaStatus}

        for formula_map in self.mapping_formulas.values():
            for formula in formula_map.values():
                stats[formula.status.value] += 1

        return stats

    def export_summary(self) -> Dict[str, Any]:
        """导出摘要信息"""
        return {
            "file_path": self.file_path,
            "worksheets_count": len(self.worksheets),
            "flash_report_sheets_count": len(self.flash_report_sheets),
            "data_source_sheets_count": len(self.data_source_sheets),
            "total_target_items": self.total_target_items,
            "total_source_items": self.total_source_items,
            "total_formulas": self.total_formulas,
            "formula_statistics": self.get_formula_statistics(),
            "created_time": self.created_time.isoformat(),
            "last_processed": self.last_processed.isoformat() if self.last_processed else None,
            "is_loaded": self.is_loaded,
            "is_data_extracted": self.is_data_extracted
        }

    def to_json(self) -> str:
        """导出为JSON格式"""
        data = {
            "workbook_info": self.export_summary(),
            "worksheets": {name: {
                "name": info.name,
                "sheet_type": info.sheet_type.value,
                "target_count": info.target_count,
                "source_count": info.source_count,
                "data_range": info.data_range,
                "is_processed": info.is_processed,
                "notes": info.notes
            } for name, info in self.worksheets.items()},

            "target_items": {tid: {
                "id": item.id,
                "name": item.name,
                "sheet_name": item.sheet_name,
                "level": item.level,
                "target_cell_address": item.target_cell_address,
                "is_empty_target": item.is_empty_target,
                "notes": item.notes,
                "columns": {key: column.to_dict() for key, column in item.columns.items()}
            } for tid, item in self.target_items.items()},

            "source_items": {sid: {
                "id": item.id,
                "name": item.name,
                "sheet_name": item.sheet_name,
                "cell_address": item.cell_address,
                "value": item.value,
                "value_type": item.value_type,
                "notes": item.notes
            } for sid, item in self.source_items.items()},

            "mapping_formulas": {
                tid: {
                    column_key: {
                        "target_id": formula.target_id,
                        "column_key": formula.column_key,
                        "column_name": formula.column_name,
                        "formula": formula.formula,
                        "constant_value": formula.constant_value,
                        "status": formula.status.value,
                        "calculation_result": formula.calculation_result,
                        "is_valid": formula.is_valid,
                        "validation_error": formula.validation_error,
                        "ai_confidence": formula.ai_confidence,
                        "version": formula.version,
                        "notes": formula.notes
                    }
                    for column_key, formula in column_map.items()
                }
                for tid, column_map in self.mapping_formulas.items()
            }
        }

        return json.dumps(data, ensure_ascii=False, indent=2)


@dataclass
class CalculationResult:
    """计算结果数据模型"""

    target_id: str  # 目标项ID
    success: bool  # 是否成功
    column_key: str = "__default__"  # 列键
    column_name: str = ""
    result: Optional[Union[int, float]] = None  # 计算结果
    error_message: str = ""  # 错误信息
    calculation_time: float = 0.0  # 计算耗时（毫秒）

    # 详细信息
    formula_used: str = ""  # 使用的公式
    input_values: Dict[str, Any] = field(default_factory=dict)  # 输入值
    calculation_steps: List[str] = field(default_factory=list)  # 计算步骤

    # 元数据
    calculated_time: datetime = field(default_factory=datetime.now)


@dataclass
class AIAnalysisRequest:
    """AI分析请求数据模型"""

    task_description: str = "Analyze financial items and create calculation formulas."
    target_items: List[Dict[str, Any]] = field(default_factory=list)
    source_items: List[Dict[str, Any]] = field(default_factory=list)

    # AI配置
    api_url: str = ""
    api_key: str = ""
    model: str = "gpt-4"
    system_prompt: str = ""

    # 请求参数
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 30

    def add_target_item(self, target_item: TargetItem):
        """添加目标项"""
        self.target_items.append({
            "id": target_item.id,
            "name": target_item.name,
            "level": target_item.level,
            "sheet_name": target_item.sheet_name
        })

    def add_source_item(self, source_item: SourceItem):
        """添加来源项"""
        self.source_items.append({
            "id": source_item.id,
            "sheet": source_item.sheet_name,
            "name": source_item.name,
            "cell": source_item.cell_address,
            "value": source_item.value
        })


@dataclass
class AIAnalysisResponse:
    """AI分析响应数据模型"""

    success: bool = False
    mappings: List[Dict[str, str]] = field(default_factory=list)
    error_message: str = ""


@dataclass
class MappingTemplate:
    """映射关系模板"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    source_sheet: str = ""  # 来源快报表
    target_sheet: str = ""  # 目标快报表
    created_time: datetime = field(default_factory=datetime.now)
    mappings: Dict[str, str] = field(default_factory=dict)  # target_item_name -> formula_text

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_sheet": self.source_sheet,
            "target_sheet": self.target_sheet,
            "created_time": self.created_time.isoformat(),
            "mappings": self.mappings
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MappingTemplate':
        """从字典创建"""
        template = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            source_sheet=data.get("source_sheet", ""),
            target_sheet=data.get("target_sheet", ""),
            mappings=data.get("mappings", {})
        )

        # 解析时间
        if "created_time" in data:
            try:
                template.created_time = datetime.fromisoformat(data["created_time"])
            except:
                template.created_time = datetime.now()

        return template


@dataclass
class TemplateManager:
    """模板管理器"""

    templates: Dict[str, MappingTemplate] = field(default_factory=dict)
    template_file_path: str = "mapping_templates.json"

    def add_template(self, template: MappingTemplate):
        """添加模板"""
        self.templates[template.id] = template

    def remove_template(self, template_id: str):
        """删除模板"""
        if template_id in self.templates:
            del self.templates[template_id]

    def get_template(self, template_id: str) -> Optional[MappingTemplate]:
        """获取模板"""
        return self.templates.get(template_id)

    def get_templates_for_sheet(self, sheet_name: str) -> List[MappingTemplate]:
        """获取适用于指定表格的模板"""
        return [t for t in self.templates.values()
                if t.target_sheet == sheet_name or not t.target_sheet]

    def save_to_file(self):
        """保存模板到文件"""
        try:
            data = {
                "templates": [t.to_dict() for t in self.templates.values()]
            }
            with open(self.template_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存模板失败: {e}")

    def load_from_file(self):
        """从文件加载模板"""
        try:
            with open(self.template_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.templates.clear()
            for template_data in data.get("templates", []):
                template = MappingTemplate.from_dict(template_data)
                self.templates[template.id] = template

        except FileNotFoundError:
            # 文件不存在，创建空模板管理器
            self.templates.clear()
        except Exception as e:
            print(f"加载模板失败: {e}")
            self.templates.clear()

    def create_template_from_workbook(self, workbook_manager: 'WorkbookManager',
                                    sheet_name: str, template_name: str,
                                    description: str = "") -> MappingTemplate:
        """从工作簿创建模板"""
        template = MappingTemplate(
            name=template_name,
            description=description,
            source_sheet=sheet_name,
            target_sheet=""  # 通用模板
        )

        # 提取映射关系
        for target_id, formula in workbook_manager.mapping_formulas.items():
            if formula.formula:
                target_item = workbook_manager.target_items.get(target_id)
                if target_item and target_item.sheet_name == sheet_name:
                    template.mappings[target_item.name] = formula.formula

        return template

    def apply_template_to_sheet(self, template: MappingTemplate,
                              workbook_manager: 'WorkbookManager',
                              target_sheet: str) -> int:
        """将模板应用到指定表格"""
        applied_count = 0

        # 查找目标表格中的项目
        for target_id, target_item in workbook_manager.target_items.items():
            if target_item.sheet_name == target_sheet:
                if target_item.name in template.mappings:
                    formula_text = template.mappings[target_item.name]

                    # 创建或更新映射公式
                    if target_id not in workbook_manager.mapping_formulas:
                        workbook_manager.mapping_formulas[target_id] = MappingFormula(
                            target_id=target_id,
                            formula_text=formula_text,
                            status=FormulaStatus.USER_MODIFIED
                        )
                    else:
                        workbook_manager.mapping_formulas[target_id].formula_text = formula_text
                        workbook_manager.mapping_formulas[target_id].status = FormulaStatus.USER_MODIFIED

                    applied_count += 1

        return applied_count


def generate_unique_id(prefix: str = "item") -> str:
    """生成唯一ID"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def create_empty_workbook_manager(file_path: str) -> WorkbookManager:
    """创建空的工作簿管理器"""
    return WorkbookManager(file_path=file_path)


def validate_target_item(item: TargetItem) -> Tuple[bool, str]:
    """验证目标项数据"""
    if not item.id:
        return False, "目标项ID不能为空"
    if not item.name:
        return False, "目标项名称不能为空"
    if not item.sheet_name:
        return False, "工作表名不能为空"
    if item.row <= 0:
        return False, "行号必须大于0"
    return True, ""


def validate_source_item(item: SourceItem) -> Tuple[bool, str]:
    """验证来源项数据"""
    if not item.id:
        return False, "来源项ID不能为空"
    if not item.name:
        return False, "来源项名称不能为空"
    if not item.sheet_name:
        return False, "工作表名不能为空"
    if not item.cell_address:
        return False, "单元格地址不能为空"
    return True, ""


def calculate_hierarchy_levels(target_items: List[TargetItem]) -> List[TargetItem]:
    """
    根据表格结构.md的栈算法计算层级关系

    基于原始缩进值(level字段)计算出hierarchical_level和parent_id
    实现表格结构.md中描述的层级计算算法

    Args:
        target_items: 按原始顺序排列的目标项列表

    Returns:
        已计算层级关系的目标项列表
    """
    if not target_items:
        return target_items

    # 步骤1: 生成全局唯一ID（如果需要）
    for item in target_items:
        if not item.id or not item.id.startswith(f"{item.sheet_name}_{item.row}"):
            item.id = f"{item.sheet_name}_{item.row}"

    # 步骤2: 核心层级计算算法
    parent_stack = []  # 父级栈

    for current_item in target_items:
        # 栈操作：弹出不再是父级的项目
        while parent_stack:
            last_parent = parent_stack[-1]
            # 如果当前项的缩进值 <= 栈顶项的缩进值，说明不再是子级关系
            if current_item.level <= last_parent.level:
                parent_stack.pop()
            else:
                break

        # 确定父级并分配层级
        if parent_stack:
            # 有父级：当前项是栈顶项的子级
            parent = parent_stack[-1]
            current_item.parent_id = parent.id
            current_item.hierarchical_level = parent.hierarchical_level + 1

            # 将当前项添加到父级的children_ids中
            if current_item.id not in parent.children_ids:
                parent.children_ids.append(current_item.id)
        else:
            # 无父级：当前项是顶级项
            current_item.parent_id = None
            current_item.hierarchical_level = 1

        # 将当前项压入栈，作为后续项目的潜在父级
        parent_stack.append(current_item)

    return target_items


def generate_hierarchical_numbers(target_items: List[TargetItem]) -> List[TargetItem]:
    """
    为已计算层级关系的目标项生成层级编号

    增强逻辑：
    1. 识别连续编号模式（如"其中:1.", "2.", "3."应该是同级）
    2. 防止级别跳跃（避免从3直接到3.1.1）
    3. 优先使用原始编号，但要结合上下文判断

    Args:
        target_items: 已计算层级关系的目标项列表

    Returns:
        已分配层级编号的目标项列表
    """
    if not target_items:
        return target_items

    # 按工作表分组处理
    sheets_groups = {}
    for item in target_items:
        if item.sheet_name not in sheets_groups:
            sheets_groups[item.sheet_name] = []
        sheets_groups[item.sheet_name].append(item)

    # 为每个工作表独立生成编号
    for sheet_name, sheet_items in sheets_groups.items():
        # 按原始顺序排序（按行号）
        sheet_items.sort(key=lambda x: x.row)

        # 层级计数器：每个层级维护一个计数器
        level_counters = {}

        # 上下文追踪
        prev_item = None
        prev_had_qizhong_pattern = False  # 上一项是否是"其中:数字."模式

        for item in sheet_items:
            level = item.hierarchical_level
            original_num = item.display_index  # 从Excel提取的原始编号
            original_text = item.original_text or ""

            # 检测"其中:"模式
            has_qizhong = "其中:" in original_text or "其中" in original_text

            # 检测"其中:数字."模式（如"其中:1."）
            qizhong_number_match = None
            if has_qizhong:
                import re
                # 匹配"其中:1."、"其中：2."等模式
                match = re.search(r'其中[:：]\s*(\d+)\.', original_text)
                if match:
                    qizhong_number_match = match.group(1)

            # 检查是否是连续编号的一部分
            is_sequential_number = False
            sequential_target_level = None

            if original_num and original_num.strip().rstrip('.').isdigit():
                current_num = int(original_num.strip().rstrip('.'))

                # 策略1：查找level_counters中是否有某个层级的值是current_num-1
                # 但仅当当前项不是明显的一级项目时（有缩进或"其中:"）
                if level > 1 or has_qizhong:  # 不是一级项目，才尝试连续编号检测
                    for check_level in sorted(level_counters.keys(), reverse=True):
                        if level_counters[check_level] == current_num - 1:
                            # 找到了连续编号！
                            is_sequential_number = True
                            sequential_target_level = check_level
                            break

                # 策略2：如果前一项有"其中:"模式，且缩进相近，也算连续
                if not is_sequential_number and prev_had_qizhong_pattern and prev_item:
                    if abs(item.level - prev_item.level) <= 1:
                        is_sequential_number = True
                        sequential_target_level = len(prev_item.hierarchical_number.split('.'))

            # 防止级别跳跃：限制最大增幅为1
            if prev_item:
                max_allowed_level = prev_item.hierarchical_level + 1
                if level > max_allowed_level:
                    level = max_allowed_level
                    item.hierarchical_level = level  # 更新项目的层级

            # 重置更深层级的计数器
            levels_to_reset = [k for k in level_counters.keys() if k > level]
            for reset_level in levels_to_reset:
                del level_counters[reset_level]

            # ========== 编号生成逻辑 ==========

            # 情况1：连续编号（如"其中:1."后的"2.", "3."）
            if is_sequential_number and sequential_target_level:
                current_num = int(original_num.strip().rstrip('.'))

                # 根据目标层级构建编号
                parent_parts = []
                for i in range(1, sequential_target_level):
                    if i in level_counters:
                        parent_parts.append(str(level_counters[i]))
                    else:
                        parent_parts.append("1")

                # 更新当前层级的计数器
                level_counters[sequential_target_level] = current_num

                # 组合编号
                number_parts = parent_parts + [str(current_num)]
                item.hierarchical_number = ".".join(number_parts)

                # 更新项目的层级为实际层级
                item.hierarchical_level = sequential_target_level

                # 记录这是连续编号的一部分
                prev_had_qizhong_pattern = False  # 重置
                prev_item = item
                continue

            # 情况2：有原始编号
            if original_num and original_num.strip():
                original_clean = original_num.strip()

                # 情况2a：纯数字（如"3"、"3."）- 可能是一级项目
                if original_clean.rstrip('.').isdigit():
                    num_value = original_clean.rstrip('.')

                    # 检查是否真的是一级项目
                    # 如果有"其中:"且前面已有一级项目，可能是二级
                    if has_qizhong and 1 in level_counters:
                        # 这是"其中:1."这样的模式，是二级项目
                        parent_num = level_counters.get(1, 1)
                        item.hierarchical_number = f"{parent_num}.{num_value}"
                        level_counters[2] = int(num_value)
                        level_counters[level] = int(num_value)

                        # 标记这是"其中:数字."模式
                        prev_had_qizhong_pattern = True
                    else:
                        # 这是真正的一级项目
                        item.hierarchical_number = num_value
                        level_counters[1] = int(num_value)
                        # 重置所有更深层级
                        for k in list(level_counters.keys()):
                            if k > 1:
                                del level_counters[k]
                        prev_had_qizhong_pattern = False

                    prev_item = item
                    continue

                # 情况2b：多级编号（如"2.1"、"1.2.3"）
                if '.' in original_clean:
                    parts = original_clean.strip('.').split('.')
                    if all(p.isdigit() for p in parts if p):
                        item.hierarchical_number = '.'.join(parts)
                        # 更新对应层级的计数器
                        for idx, part in enumerate(parts, start=1):
                            level_counters[idx] = int(part)
                        prev_had_qizhong_pattern = False
                        prev_item = item
                        continue

            # 情况3：检测"其中:数字."模式（即使没有 display_index）
            if qizhong_number_match:
                # 找到了"其中:1."这样的模式
                num_value = qizhong_number_match
                parent_num = level_counters.get(1, 1)
                item.hierarchical_number = f"{parent_num}.{num_value}"
                level_counters[2] = int(num_value)

                # 更新项目的层级为2级
                item.hierarchical_level = 2

                # 标记这是"其中:数字."模式
                prev_had_qizhong_pattern = True
                prev_item = item
                continue

            # 情况4：无原始编号，使用自动生成
            if level == 1:
                # 一级项目
                if 1 not in level_counters:
                    level_counters[1] = 0
                level_counters[1] += 1
                item.hierarchical_number = str(level_counters[1])

                # 检查是否包含"其中:"
                if has_qizhong:
                    prev_had_qizhong_pattern = True
                else:
                    prev_had_qizhong_pattern = False
            else:
                # 多级项目
                parent_parts = []
                for i in range(1, level):
                    if i in level_counters:
                        parent_parts.append(str(level_counters[i]))
                    else:
                        parent_parts.append("1")

                if level not in level_counters:
                    level_counters[level] = 0
                level_counters[level] += 1
                number_parts = parent_parts + [str(level_counters[level])]
                item.hierarchical_number = ".".join(number_parts)

                prev_had_qizhong_pattern = False

            prev_item = item

    return target_items


def update_hierarchy_structure(workbook_manager: WorkbookManager) -> bool:
    """
    更新工作簿管理器中所有目标项的层级结构

    Args:
        workbook_manager: 工作簿管理器

    Returns:
        是否成功更新
    """
    try:
        # 按工作表分组处理
        sheets_items = {}
        for target_item in workbook_manager.target_items.values():
            sheet_name = target_item.sheet_name
            if sheet_name not in sheets_items:
                sheets_items[sheet_name] = []
            sheets_items[sheet_name].append(target_item)

        # 对每个工作表的项目进行层级计算
        for sheet_name, items in sheets_items.items():
            # 按行号排序，确保原始顺序
            items.sort(key=lambda x: x.row)

            # 计算层级关系
            calculate_hierarchy_levels(items)

            # 生成层级编号
            generate_hierarchical_numbers(items)

        return True

    except Exception as e:
        print(f"更新层级结构失败: {e}")
        return False
