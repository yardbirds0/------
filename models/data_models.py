#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心数据模型定义 - PySide6版本
定义系统中使用的所有核心数据结构，支持新的公式格式
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from datetime import datetime
import uuid


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
        return f'[{self.sheet_name}:"{self.name}"]({self.cell_address})'

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
class MappingFormula:
    """映射公式数据模型"""

    target_id: str  # 关联的目标项ID
    formula: str  # 公式内容（新格式）
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

    def update_formula(self, new_formula: str, status: FormulaStatus = FormulaStatus.USER_MODIFIED):
        """更新公式"""
        self.formula = new_formula
        self.status = status
        self.modified_time = datetime.now()
        self.version += 1
        self.is_valid = False  # 需要重新验证

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

    file_path: str  # Excel文件路径

    # 工作表信息
    worksheets: Dict[str, WorksheetInfo] = field(default_factory=dict)
    flash_report_sheets: List[str] = field(default_factory=list)
    data_source_sheets: List[str] = field(default_factory=list)

    # 数据项
    target_items: Dict[str, TargetItem] = field(default_factory=dict)
    source_items: Dict[str, SourceItem] = field(default_factory=dict)
    mapping_formulas: Dict[str, MappingFormula] = field(default_factory=dict)
    calculation_results: Dict[str, 'CalculationResult'] = field(default_factory=dict)

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
        self.mapping_formulas[target_id] = formula
        self.total_formulas = len(self.mapping_formulas)

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

        for formula in self.mapping_formulas.values():
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
                "notes": item.notes
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

            "mapping_formulas": {tid: {
                "target_id": formula.target_id,
                "formula": formula.formula,
                "status": formula.status.value,
                "calculation_result": formula.calculation_result,
                "is_valid": formula.is_valid,
                "validation_error": formula.validation_error,
                "ai_confidence": formula.ai_confidence,
                "version": formula.version,
                "notes": formula.notes
            } for tid, formula in self.mapping_formulas.items()}
        }

        return json.dumps(data, ensure_ascii=False, indent=2)


@dataclass
class CalculationResult:
    """计算结果数据模型"""

    target_id: str  # 目标项ID
    success: bool  # 是否成功
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

    基于hierarchical_level生成如1、1.1、1.1.1、2、2.1格式的编号

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

        for item in sheet_items:
            level = item.hierarchical_level

            # 重置更深层级的计数器
            levels_to_reset = [k for k in level_counters.keys() if k > level]
            for reset_level in levels_to_reset:
                del level_counters[reset_level]

            # 增加当前层级的计数器
            if level not in level_counters:
                level_counters[level] = 0
            level_counters[level] += 1

            # 生成层级编号
            number_parts = []
            for i in range(1, level + 1):
                if i in level_counters:
                    number_parts.append(str(level_counters[i]))
                else:
                    number_parts.append("1")

            item.hierarchical_number = ".".join(number_parts)

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