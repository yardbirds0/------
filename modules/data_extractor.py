#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的数据提取器 - 支持科目余额表专用识别和多列数据处理
"""

import sys
import os
import json
import openpyxl
import re
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.data_models import (
    WorkbookManager, TargetItem, SourceItem, SheetType, update_hierarchy_structure
)
from modules.table_schema_analyzer import TableSchemaAnalyzer, TableType, TableSchema
from utils.column_detector import ColumnDetector

class DataExtractor:
    """增强的数据提取器"""

    def __init__(self, workbook_manager: WorkbookManager):
        """初始化数据提取器"""
        self.workbook_manager = workbook_manager
        self.workbook = None
        self.schema_analyzer = TableSchemaAnalyzer()
        self.column_detector = ColumnDetector()

        # 加载表格规则
        self.table_rules = self._load_table_rules()

    def _load_table_rules(self) -> Dict:
        """加载表格规则配置"""
        try:
            rules_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'table_schema_rules.json')
            with open(rules_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("警告：无法找到表格规则文件，使用默认规则")
            return {"table_schemas": {}}

    def extract_all_data(self) -> bool:
        """提取所有数据"""
        try:
            print("开始提取表格数据...")

            # 加载Excel文件
            if not self._load_workbook():
                return False

            # 提取快报表目标项
            target_count = self._extract_flash_report_targets()
            print(f"提取到目标项: {target_count} 个")

            # 计算层级关系
            print("计算层级关系...")
            if update_hierarchy_structure(self.workbook_manager):
                print("+ 层级关系计算完成")
            else:
                print("X 层级关系计算失败")

            # 提取数据源项（使用增强逻辑）
            source_count = self._extract_data_source_items_enhanced()
            print(f"提取到来源项: {source_count} 个")

            return True

        except Exception as e:
            print(f"数据提取失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _load_workbook(self) -> bool:
        """加载Excel工作簿"""
        try:
            if not self.workbook_manager.file_path or not os.path.exists(self.workbook_manager.file_path):
                print("Excel文件不存在")
                return False

            self.workbook = openpyxl.load_workbook(self.workbook_manager.file_path, data_only=True)
            print(f"Excel文件加载成功: {self.workbook_manager.file_path}")
            return True

        except Exception as e:
            print(f"Excel文件加载失败: {e}")
            return False

    def _extract_flash_report_targets(self) -> int:
        """提取快报表目标项（保持原有逻辑）"""
        target_count = 0

        for sheet_item in self.workbook_manager.flash_report_sheets:
            sheet_name = self._get_sheet_name(sheet_item)
            print(f"\n提取快报表 '{sheet_name}' 的目标项...")

            if sheet_name not in self.workbook.sheetnames:
                print(f"  工作表 '{sheet_name}' 不存在")
                continue

            sheet = self.workbook[sheet_name]
            sheet_targets = self._extract_targets_from_sheet(sheet, sheet_name)
            target_count += len(sheet_targets)
            print(f"  提取到 {len(sheet_targets)} 个目标项")

            # 添加到工作簿管理器
            for target in sheet_targets:
                self.workbook_manager.target_items[target.id] = target

        return target_count

    def _extract_data_source_items_enhanced(self) -> int:
        """提取数据源项（增强版）"""
        source_count = 0

        for sheet_item in self.workbook_manager.data_source_sheets:
            sheet_name = self._get_sheet_name(sheet_item)
            print(f"\n提取数据源表 '{sheet_name}' 的来源项...")

            if sheet_name not in self.workbook.sheetnames:
                print(f"  工作表 '{sheet_name}' 不存在")
                continue

            sheet = self.workbook[sheet_name]

            # 分析表格模式
            print(f"  分析表格模式...")
            table_schema = self.schema_analyzer.analyze_table_schema(sheet)
            print(f"  识别为: {table_schema.table_type.value}")

            # 根据表格类型使用不同的提取策略
            if table_schema.table_type == TableType.TRIAL_BALANCE:
                sheet_sources = self._extract_trial_balance_sources(sheet, sheet_name, table_schema)
            else:
                sheet_sources = self._extract_general_sources(sheet, sheet_name, table_schema)

            source_count += len(sheet_sources)
            print(f"  提取到 {len(sheet_sources)} 个来源项")

            # 添加到工作簿管理器
            for source in sheet_sources:
                self.workbook_manager.source_items[source.id] = source

        return source_count

    def _extract_trial_balance_sources(self, sheet, sheet_name: str, schema: TableSchema) -> List[SourceItem]:
        """提取科目余额表来源项（专用逻辑）"""
        sources = []

        print(f"    使用科目余额表专用提取逻辑")
        print(f"    数据开始行: {schema.data_start_row}")
        print(f"    发现 {len(schema.data_columns)} 个数据列")

        # 获取科目余额表的列结构
        trial_balance_structure = self.column_detector.get_trial_balance_structure(
            [col for col in schema.data_columns]
        )

        # 扫描所有数据行（支持大型科目余额表）
        max_row = sheet.max_row or 5000  # 科目余额表通常更大

        for row_num in range(schema.data_start_row, max_row + 1):
            # 提取科目信息
            account_info = self._extract_account_info(sheet, row_num, schema)

            if not account_info:
                continue

            account_code = account_info['code']
            account_name = account_info['name']

            # 确定层级
            hierarchy_level = self._calculate_account_level(account_code)

            # 提取所有数据列的值
            data_columns = {}
            main_value = None

            for col_info in schema.data_columns:
                if col_info.is_numeric:
                    cell = sheet.cell(row=row_num, column=col_info.column_index)
                    if self._is_data_cell(cell):
                        value = self._extract_cell_value(cell)
                        # 生成更清晰的列键名
                        column_key = self._generate_column_key(col_info, sheet_name)
                        data_columns[column_key] = value

                        # 第一个有效数值作为主要数值
                        if main_value is None:
                            main_value = value

            # 只有找到有效数据才创建来源项
            if data_columns:
                source = self._create_enhanced_source_item(
                    sheet_name=sheet_name,
                    account_name=account_name,
                    account_code=account_code,
                    row_num=row_num,
                    hierarchy_level=hierarchy_level,
                    data_columns=data_columns,
                    main_value=main_value,
                    table_type="trial_balance"
                )
                sources.append(source)

        print(f"    科目余额表提取完成，共 {len(sources)} 个项目")
        return sources

    def _extract_general_sources(self, sheet, sheet_name: str, schema: TableSchema) -> List[SourceItem]:
        """提取通用表格来源项"""
        sources = []

        print(f"    使用通用表格提取逻辑")

        # 扫描所有数据行（移除行数限制）
        max_row = sheet.max_row or 2000  # 增加默认上限

        for row_num in range(schema.data_start_row, max_row + 1):
            # 提取项目名称
            item_name = None
            for name_col in schema.name_columns:
                cell = sheet.cell(row=row_num, column=name_col)
                if cell.value and str(cell.value).rstrip():  # 只删除尾部空白，保留前导缩进
                    item_name = str(cell.value).rstrip()  # 保留前导缩进
                    break

            if not item_name:
                continue

            # 提取所有数据列
            data_columns = {}
            main_value = None

            for col_info in schema.data_columns:
                if col_info.is_numeric:
                    cell = sheet.cell(row=row_num, column=col_info.column_index)
                    if self._is_data_cell(cell):
                        value = self._extract_cell_value(cell)
                        # 生成更清晰的列键名
                        column_key = self._generate_column_key(col_info, sheet_name)
                        data_columns[column_key] = value

                        if main_value is None:
                            main_value = value

            if data_columns:
                source = self._create_enhanced_source_item(
                    sheet_name=sheet_name,
                    account_name=item_name,
                    account_code="",
                    row_num=row_num,
                    hierarchy_level=0,
                    data_columns=data_columns,
                    main_value=main_value,
                    table_type=schema.table_type.value
                )
                sources.append(source)

        return sources

    def _extract_account_info(self, sheet, row_num: int, schema: TableSchema) -> Optional[Dict[str, str]]:
        """提取科目信息"""
        account_code = ""
        account_name = ""

        # 从编码列提取科目代码
        for code_col in schema.code_columns:
            cell = sheet.cell(row=row_num, column=code_col)
            if cell.value:
                code_text = str(cell.value).strip()
                # 优化科目代码识别模式
                if re.match(r'^\d{3,12}(\.\d+)*$', code_text):  # 支持3-12位代码，可带小数点分隔
                    account_code = code_text
                    break

        # 从名称列提取科目名称
        for name_col in schema.name_columns:
            cell = sheet.cell(row=row_num, column=name_col)
            if cell.value:
                name_text = str(cell.value).rstrip()  # 保留前导缩进
                if self._is_account_name(name_text):
                    account_name = name_text
                    break

        if account_name or account_code:
            return {
                'code': account_code,
                'name': account_name if account_name else f"科目{account_code}"
            }

        return None

    def _calculate_account_level(self, account_code: str) -> int:
        """计算科目层级（优化版）"""
        if not account_code:
            return 0

        # 支持小数点分隔的科目代码（如1001.01.001）
        if '.' in account_code:
            parts = account_code.split('.')
            return len(parts)  # 按分隔段数确定层级

        # 根据科目代码长度确定层级（传统方式）
        code_length = len(account_code)
        if code_length >= 12:
            return 4
        elif code_length >= 9:
            return 3
        elif code_length >= 6:
            return 2
        elif code_length >= 3:
            return 1
        else:
            return 0

    def _create_enhanced_source_item(self, sheet_name: str, account_name: str, account_code: str,
                                   row_num: int, hierarchy_level: int, data_columns: Dict[str, Any],
                                   main_value: Any, table_type: str) -> SourceItem:
        """创建增强的来源项"""

        # 生成唯一ID
        source_id = f"{sheet_name}_{account_code}_{row_num}" if account_code else f"{sheet_name}_{row_num}"

        # 创建基本的SourceItem
        source = SourceItem(
            id=source_id,
            sheet_name=sheet_name,
            name=account_name,
            cell_address=f"A{row_num}",  # 暂时使用A列
            row=row_num,
            column="A",
            value=main_value,
            account_code=account_code,
            hierarchy_level=hierarchy_level,
            table_type=table_type,
            data_columns=data_columns
        )

        # 设置层级信息
        if account_code:
            parent_code = self._get_parent_account_code(account_code)
            source.set_hierarchy_info(account_code, hierarchy_level, parent_code)

        return source

    def _generate_column_key(self, col_info, sheet_name: str = "") -> str:
        """生成清晰的数据列键名（与TableColumnRules规则一致）"""
        # 导入表列规则系统
        from utils.table_column_rules import TableColumnRules

        # 获取主要列头文本
        primary_header = col_info.primary_header.lower() if col_info.primary_header else ""
        secondary_header = col_info.secondary_header.lower() if hasattr(col_info, 'secondary_header') and col_info.secondary_header else ""

        # 如果列头为空，尝试直接从Excel读取（修复关键问题）
        if not primary_header and hasattr(self, 'workbook') and self.workbook:
            try:
                # 查找当前工作表
                current_sheet = None
                for ws_name in self.workbook.sheetnames:
                    if ws_name == sheet_name:
                        current_sheet = self.workbook[ws_name]
                        break

                if current_sheet:
                    # 尝试从第5行读取列头（根据利润表分析结果）
                    header_cell = current_sheet.cell(row=5, column=col_info.column_index)
                    if header_cell.value and str(header_cell.value).strip():
                        primary_header = str(header_cell.value).strip().lower()
            except Exception as e:
                pass  # 静默处理错误

        # 直接映射检查（优先处理，移到标准键匹配之前）
        if sheet_name and "利润表" in sheet_name:
            # 利润表列名映射
            income_mapping = {
                "本期金额": "本期金额",
                "本期": "本期金额",
                "上期金额": "上期金额",
                "上期": "上期金额",  # 关键修复：映射"上期"到"上期金额"
                "本年累计": "本年累计",
                "上年累计": "上年累计"
            }
            for pattern, standard_key in income_mapping.items():
                pattern_lower = pattern.lower()
                # 精确匹配或包含匹配
                if primary_header == pattern_lower or pattern_lower in primary_header or primary_header in pattern_lower:
                    return standard_key

        # 先检测当前工作表的表类型
        if sheet_name:
            table_type = TableColumnRules.detect_table_type(sheet_name)
            if table_type:
                # 获取该表类型的标准列键
                standard_keys = TableColumnRules.get_ordered_column_keys(table_type)

                # 尝试匹配到最合适的标准键
                best_match = self._match_to_standard_key(primary_header, secondary_header, standard_keys)
                if best_match:
                    return best_match

        if sheet_name and "资产负债表" in sheet_name:
            # 资产负债表列名映射
            balance_sheet_mapping = {
                "期末余额": "期末余额",
                "期末": "期末余额",
                "期末金额": "期末余额",
                "年初余额": "年初余额",
                "年初": "年初余额",
                "年初金额": "年初余额",
            }
            for pattern, standard_key in balance_sheet_mapping.items():
                if pattern.lower() in primary_header or primary_header in pattern.lower():
                    return standard_key

        if sheet_name and "现金流量表" in sheet_name:
            # 现金流量表列名映射
            cashflow_mapping = {
                "本期金额": "本期金额",
                "本期": "本期金额",
                "上期金额": "上期金额",
                "上期": "上期金额",
            }
            for pattern, standard_key in cashflow_mapping.items():
                if pattern.lower() in primary_header or primary_header in pattern.lower():
                    return standard_key

        # 详细的映射规则（作为备选方案）
        # 标准化科目余额表列名映射
        trial_balance_mapping = {
            # 年初余额相关
            "年初余额": {
                "借方": "年初余额_借方",
                "贷方": "年初余额_贷方",
                "合计": "年初余额_合计",
                "": "年初余额_合计"
            },
            # 期初余额相关
            "期初余额": {
                "借方": "期初余额_借方",
                "贷方": "期初余额_贷方",
                "合计": "期初余额_合计",
                "": "期初余额_合计"
            },
            # 本期发生额相关
            "本期发生额": {
                "借方": "本期发生额_借方",
                "贷方": "本期发生额_贷方",
                "合计": "本期发生额_合计",
                "": "本期发生额_合计"
            },
            # 期末余额相关
            "期末余额": {
                "借方": "期末余额_借方",
                "贷方": "期末余额_贷方",
                "合计": "期末余额_合计",
                "": "期末余额_合计"
            }
        }

        # 资产负债表列名映射
        balance_sheet_mapping = {
            "期末余额": "期末余额",
            "期末": "期末余额",
            "期末金额": "期末余额",
            "年初余额": "年初余额",
            "年初": "年初余额",
            "年初金额": "年初余额",
        }

        # 利润表列名映射
        income_mapping = {
            "本期金额": "本期金额",
            "本期": "本期金额",
            "上期金额": "上期金额",
            "上期": "上期金额",  # 关键修复：映射"上期"到"上期金额"
            "本年累计": "本年累计",
            "上年累计": "上年累计"
        }

        # 现金流量表列名映射
        cashflow_mapping = {
            "本期金额": "本期金额",
            "本期": "本期金额",
            "上期金额": "上期金额",
            "上期": "上期金额",
        }

        # 检查科目余额表模式
        for period_key, direction_map in trial_balance_mapping.items():
            if period_key in primary_header:
                # 确定借贷方向
                direction = ""
                if "借方" in secondary_header or "借" in secondary_header:
                    direction = "借方"
                elif "贷方" in secondary_header or "贷" in secondary_header:
                    direction = "贷方"
                elif "合计" in secondary_header or secondary_header == "":
                    direction = "合计"
                else:
                    # 根据数据类型判断
                    if hasattr(col_info, 'data_type') and col_info.data_type:
                        if col_info.data_type == 'debit':
                            direction = "借方"
                        elif col_info.data_type == 'credit':
                            direction = "贷方"

                if direction in direction_map:
                    return direction_map[direction]

        # 检查资产负债表模式
        for pattern, standard_key in balance_sheet_mapping.items():
            if pattern in primary_header:
                return standard_key

        # 检查利润表模式（优先处理）
        for pattern, standard_key in income_mapping.items():
            if pattern in primary_header:
                return standard_key

        # 检查现金流量表模式
        for pattern, standard_key in cashflow_mapping.items():
            if pattern in primary_header:
                return standard_key

        # 降级到原有逻辑
        if primary_header:
            base_name = primary_header.replace(" ", "_").replace(":", "")
        else:
            base_name = f"column_{col_info.column_index}"

        # 添加数据类型信息
        if hasattr(col_info, 'data_type') and col_info.data_type not in ['unknown', '']:
            if col_info.data_type in ['debit', 'credit']:
                return f"{base_name}_{col_info.data_type}"

        # 检查二级列头
        if hasattr(col_info, 'secondary_header') and col_info.secondary_header:
            secondary = col_info.secondary_header.replace(" ", "_").replace(":", "")
            return f"{base_name}_{secondary}"

        # 默认使用列索引区分
        return f"{base_name}_{col_info.column_index}"

    def _match_to_standard_key(self, primary_header: str, secondary_header: str, standard_keys: list) -> str:
        """匹配到最合适的标准键名"""
        # 创建候选匹配列表
        candidates = []

        for key in standard_keys:
            score = 0
            key_lower = key.lower()

            # 检查主要列头匹配
            if primary_header in key_lower:
                score += 10
            elif any(word in key_lower for word in primary_header.split()):
                score += 5

            # 检查二级列头匹配
            if secondary_header:
                if secondary_header in key_lower:
                    score += 10
                elif any(word in key_lower for word in secondary_header.split()):
                    score += 5

            # 特殊匹配规则
            if "借" in secondary_header and "借方" in key_lower:
                score += 8
            elif "贷" in secondary_header and "贷方" in key_lower:
                score += 8
            elif "合计" in secondary_header and "合计" in key_lower:
                score += 8

            if score > 0:
                candidates.append((key, score))

        # 返回得分最高的匹配
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        return None

    def _get_parent_account_code(self, account_code: str) -> str:
        """获取父级科目代码"""
        if len(account_code) <= 4:
            return ""

        # 根据层级规则返回父级代码
        if len(account_code) >= 6:
            return account_code[:4]  # 返回一级科目
        elif len(account_code) >= 8:
            return account_code[:6]  # 返回二级科目
        elif len(account_code) >= 10:
            return account_code[:8]  # 返回三级科目

        return ""

    def _extract_targets_from_sheet(self, sheet, sheet_name: str) -> List[TargetItem]:
        """从快报表中提取目标项（保持原有逻辑）"""
        targets = []
        max_row = sheet.max_row or 500  # 增加快报表扫描范围

        for row_num in range(1, max_row + 1):
            cell_a = sheet.cell(row=row_num, column=1)
            if cell_a.value and str(cell_a.value).rstrip():
                text = str(cell_a.value).rstrip()  # 保留前导缩进

                # 跳过明显的标题行
                if any(keyword in text for keyword in ['项目', '金额', '单位', '期间']):
                    continue

                # 分析项目文本
                item_info = self._analyze_target_item_text(text)
                if item_info:
                    target = TargetItem(
                        id=f"{sheet_name}_{row_num}",
                        name=item_info['clean_name'],
                        sheet_name=sheet_name,
                        row=row_num,
                        level=item_info['level'],
                        hierarchical_level=item_info['level'],
                        hierarchical_number=item_info['numbering'],
                        original_text=text
                    )
                    targets.append(target)

        return targets

    def _analyze_target_item_text(self, text: str) -> Optional[Dict]:
        """分析目标项文本"""
        if not text or len(text.strip()) < 2:
            return None

        # 检测编号模式
        numbering_patterns = [
            r'^(\d+)\.\s*(.+)',
            r'^(\d+)\s+(.+)',
            r'^(\d+)、\s*(.+)',
            r'^\((\d+)\)\s*(.+)',
        ]

        for pattern in numbering_patterns:
            match = re.match(pattern, text.strip())
            if match:
                return {
                    'numbering': match.group(1),
                    'clean_name': match.group(2).rstrip(),  # 保留前导缩进
                    'level': 1
                }

        # 没有编号的项目
        return {
            'numbering': '',
            'clean_name': text.rstrip(),  # 保留前导缩进
            'level': 1
        }

    def _is_account_name(self, text: str) -> bool:
        """判断是否是科目名称（增强版）"""
        if not text or len(text) < 2:
            return False

        # 排除模式（更全面）
        exclude_patterns = [
            r'^日期[:：]', r'^期间[:：]', r'^单位[:：]',
            r'^科目代码$', r'^科目名称$', r'^期初$', r'^期末$',
            r'^借方$', r'^贷方$', r'^合计$', r'^小计$',
            r'^年初$', r'^本期$', r'^余额$', r'^发生额$',
            r'^\d+$',  # 纯数字
            r'^[\d\.,\s\-\(\)]+$'  # 纯数字格式
        ]

        for pattern in exclude_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return False

        # 包含中文字符且长度合适
        if re.search(r'[\u4e00-\u9fff]', text) and 2 <= len(text) <= 50:
            return True

        return False

    def _is_data_cell(self, cell) -> bool:
        """判断是否是数据单元格（增强版）"""
        if cell.value is None:
            return False

        # 检查是否是数值
        if isinstance(cell.value, (int, float)):
            return True  # 允许0值

        # 检查是否是数值字符串
        if isinstance(cell.value, str):
            try:
                # 处理各种数值格式
                cleaned = cell.value.replace(',', '').replace(' ', '')
                # 处理负数括号格式
                if cleaned.startswith('(') and cleaned.endswith(')'):
                    cleaned = '-' + cleaned[1:-1]
                float(cleaned)
                return True
            except ValueError:
                return False

        return False

    def _extract_cell_value(self, cell) -> Optional[float]:
        """提取单元格数值"""
        if cell.value is None:
            return None

        if isinstance(cell.value, (int, float)):
            return float(cell.value)

        if isinstance(cell.value, str):
            try:
                cleaned = cell.value.replace(',', '').replace(' ', '')
                if cleaned.startswith('(') and cleaned.endswith(')'):
                    cleaned = '-' + cleaned[1:-1]
                return float(cleaned)
            except ValueError:
                return None

        return None

    def _get_sheet_name(self, sheet_item) -> str:
        """获取工作表名称"""
        if isinstance(sheet_item, str):
            return sheet_item
        elif hasattr(sheet_item, 'name'):
            return str(sheet_item.name)
        else:
            return str(sheet_item)

if __name__ == "__main__":
    # 测试用例
    print("增强数据提取器模块")