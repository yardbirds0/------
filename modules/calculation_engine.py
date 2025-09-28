#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算引擎模块
实现公式解析、计算和导出功能
"""

import openpyxl
from typing import Dict, List, Tuple, Any, Optional, Union
import re
from dataclasses import dataclass, field
from datetime import datetime
import json

from models.data_models import (
    TargetItem, SourceItem, MappingFormula, WorkbookManager,
    FormulaStatus, CalculationResult
)
from utils.excel_utils_v2 import (
    validate_formula_syntax_v2, parse_formula_references_v2,
    build_formula_reference_v2, evaluate_formula_with_values_v2,
    write_values_to_excel, backup_excel_file
)


@dataclass
class CalculationContext:
    """计算上下文信息"""
    workbook_manager: WorkbookManager
    value_cache: Dict[str, Any] = field(default_factory=dict)
    calculation_order: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CalculationEngine:
    """计算引擎主类"""

    def __init__(self, workbook_manager: WorkbookManager):
        """
        初始化计算引擎

        Args:
            workbook_manager: 工作簿管理器
        """
        self.workbook_manager = workbook_manager
        self.calculation_context = CalculationContext(workbook_manager)

        # 计算统计
        self.total_formulas = 0
        self.successful_calculations = 0
        self.failed_calculations = 0
        self.calculation_time = 0.0

    def build_value_map(self) -> Dict[str, Any]:
        """
        构建引用值映射表

        Returns:
            Dict[str, Any]: {引用字符串: 值}
        """
        value_map = {}

        for source_id, source in self.workbook_manager.source_items.items():
            # 为每个来源项创建引用
            if source.value is not None:
                reference = build_formula_reference_v2(source.sheet_name, source.name, source.cell_address)
                value_map[reference] = source.value

        return value_map

    def validate_all_formulas(self) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        验证所有公式

        Returns:
            Dict[str, Tuple[bool, Optional[str]]]: {target_id: (是否有效, 错误信息)}
        """
        results = {}

        for target_id, formula in self.workbook_manager.mapping_formulas.items():
            is_valid, error_msg = validate_formula_syntax_v2(formula.formula)
            results[target_id] = (is_valid, error_msg)

            # 更新公式状态
            if is_valid:
                formula.status = FormulaStatus.VALIDATED
            else:
                formula.status = FormulaStatus.ERROR

        return results

    def calculate_single_formula(self, target_id: str,
                                formula_obj: MappingFormula) -> CalculationResult:
        """
        计算单个公式

        Args:
            target_id: 目标项ID
            formula_obj: 公式对象

        Returns:
            CalculationResult: 计算结果
        """
        try:
            # 验证公式
            is_valid, error_msg = validate_formula_syntax_v2(formula_obj.formula)
            if not is_valid:
                return CalculationResult(
                    target_id=target_id,
                    success=False,
                    error_message=error_msg,
                    calculation_time=0.0
                )

            # 构建值映射
            if not self.calculation_context.value_cache:
                self.calculation_context.value_cache = self.build_value_map()

            # 计算公式
            start_time = datetime.now()
            success, result = evaluate_formula_with_values_v2(
                formula_obj.formula,
                self.calculation_context.value_cache
            )
            end_time = datetime.now()

            calculation_time = (end_time - start_time).total_seconds() * 1000  # 毫秒

            if success:
                # 更新公式状态
                formula_obj.status = FormulaStatus.CALCULATED
                formula_obj.calculation_result = result
                formula_obj.last_calculated = datetime.now()

                return CalculationResult(
                    target_id=target_id,
                    success=True,
                    result=result,
                    calculation_time=calculation_time
                )
            else:
                return CalculationResult(
                    target_id=target_id,
                    success=False,
                    error_message=str(result),
                    calculation_time=calculation_time
                )

        except Exception as e:
            return CalculationResult(
                target_id=target_id,
                success=False,
                error_message=f"计算异常: {str(e)}",
                calculation_time=0.0
            )

    def calculate_all_formulas(self, show_progress: bool = True) -> List[CalculationResult]:
        """
        计算所有公式

        Args:
            show_progress: 是否显示进度

        Returns:
            List[CalculationResult]: 计算结果列表
        """
        results = []
        self.calculation_context.errors.clear()
        self.calculation_context.warnings.clear()

        # 重置统计
        self.total_formulas = len(self.workbook_manager.mapping_formulas)
        self.successful_calculations = 0
        self.failed_calculations = 0

        start_time = datetime.now()

        if show_progress:
            print(f"开始计算 {self.total_formulas} 个公式...")

        for i, (target_id, formula) in enumerate(self.workbook_manager.mapping_formulas.items()):
            if show_progress and (i + 1) % 10 == 0:
                print(f"进度: {i + 1}/{self.total_formulas}")

            result = self.calculate_single_formula(target_id, formula)
            results.append(result)

            # 将计算结果存储到workbook_manager中
            self.workbook_manager.calculation_results[target_id] = result

            if result.success:
                self.successful_calculations += 1
            else:
                self.failed_calculations += 1
                self.calculation_context.errors.append(
                    f"目标项 {target_id}: {result.error_message}"
                )

        end_time = datetime.now()
        self.calculation_time = (end_time - start_time).total_seconds()

        if show_progress:
            print(f"计算完成: 成功 {self.successful_calculations}, 失败 {self.failed_calculations}")
            print(f"总耗时: {self.calculation_time:.2f} 秒")

        return results

    def get_calculation_summary(self) -> Dict[str, Any]:
        """
        获取计算摘要

        Returns:
            Dict[str, Any]: 计算摘要信息
        """
        return {
            "total_formulas": self.total_formulas,
            "successful_calculations": self.successful_calculations,
            "failed_calculations": self.failed_calculations,
            "success_rate": round(
                self.successful_calculations / self.total_formulas * 100, 2
            ) if self.total_formulas > 0 else 0.0,
            "calculation_time": round(self.calculation_time, 3),
            "errors_count": len(self.calculation_context.errors),
            "warnings_count": len(self.calculation_context.warnings)
        }

    def export_results_to_json(self, file_path: str) -> bool:
        """
        导出计算结果到JSON文件

        Args:
            file_path: 输出文件路径

        Returns:
            bool: 是否成功
        """
        try:
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "total_targets": len(self.workbook_manager.target_items),
                    "total_sources": len(self.workbook_manager.source_items),
                    "total_formulas": len(self.workbook_manager.mapping_formulas)
                },
                "calculation_summary": self.get_calculation_summary(),
                "results": []
            }

            # 添加每个目标项的结果
            for target_id, target in self.workbook_manager.target_items.items():
                result_data = {
                    "target_id": target_id,
                    "target_name": target.name,
                    "sheet_name": target.sheet_name,
                    "row": target.row,
                    "level": target.level,
                    "is_empty_target": target.is_empty_target
                }

                # 添加公式信息
                if target_id in self.workbook_manager.mapping_formulas:
                    formula = self.workbook_manager.mapping_formulas[target_id]
                    result_data.update({
                        "formula": formula.formula,
                        "formula_status": formula.status.value,
                        "calculation_result": formula.calculation_result,
                        "last_calculated": formula.last_calculated.isoformat() if formula.last_calculated else None
                    })
                else:
                    result_data.update({
                        "formula": "",
                        "formula_status": "empty",
                        "calculation_result": None,
                        "last_calculated": None
                    })

                export_data["results"].append(result_data)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            self.calculation_context.errors.append(f"导出JSON失败: {str(e)}")
            return False

    def export_to_excel(self, target_file_path: str,
                       source_file_path: Optional[str] = None) -> bool:
        """
        导出计算结果到Excel文件

        Args:
            target_file_path: 目标Excel文件路径
            source_file_path: 源Excel文件路径（如果不提供则使用原文件）

        Returns:
            bool: 是否成功
        """
        try:
            # 确定源文件
            if source_file_path is None:
                source_file_path = self.workbook_manager.file_path

            # 创建备份
            backup_path = backup_excel_file(source_file_path)
            print(f"已创建备份文件: {backup_path}")

            # 打开工作簿
            workbook = openpyxl.load_workbook(source_file_path)

            # 准备写入的值
            values_to_write = {}

            for target_id, formula in self.workbook_manager.mapping_formulas.items():
                if formula.calculation_result is not None:
                    target = self.workbook_manager.target_items.get(target_id)
                    if target:
                        sheet_name = target.sheet_name
                        if sheet_name not in values_to_write:
                            values_to_write[sheet_name] = {}

                        # 构建单元格地址
                        # 假设目标项在第一列为名称，第二列为数值
                        cell_address = f"B{target.row}"  # 简化处理，实际应该根据具体位置
                        values_to_write[sheet_name][cell_address] = formula.calculation_result

            # 写入每个工作表
            updated_count = 0
            for sheet_name, sheet_values in values_to_write.items():
                if sheet_name in workbook.sheetnames:
                    sheet = workbook[sheet_name]

                    for cell_address, value in sheet_values.items():
                        try:
                            sheet[cell_address] = value
                            updated_count += 1
                        except Exception as e:
                            error_msg = f"写入 {sheet_name}!{cell_address} 失败: {str(e)}"
                            self.calculation_context.errors.append(error_msg)

            # 保存工作簿
            workbook.save(target_file_path)
            workbook.close()

            print(f"成功导出 {updated_count} 个计算结果到 {target_file_path}")
            return True

        except Exception as e:
            self.calculation_context.errors.append(f"导出Excel失败: {str(e)}")
            return False

    def generate_formula_report(self) -> str:
        """
        生成公式报告

        Returns:
            str: 报告内容
        """
        report_lines = []

        # 报告头部
        report_lines.append("=" * 60)
        report_lines.append("公式计算报告")
        report_lines.append("=" * 60)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # 统计信息
        summary = self.get_calculation_summary()
        report_lines.append("统计摘要:")
        report_lines.append(f"  总公式数: {summary['total_formulas']}")
        report_lines.append(f"  成功计算: {summary['successful_calculations']}")
        report_lines.append(f"  计算失败: {summary['failed_calculations']}")
        report_lines.append(f"  成功率: {summary['success_rate']}%")
        report_lines.append(f"  计算耗时: {summary['calculation_time']} 秒")
        report_lines.append("")

        # 公式详情
        report_lines.append("公式详情:")
        report_lines.append("-" * 40)

        for target_id, formula in self.workbook_manager.mapping_formulas.items():
            target = self.workbook_manager.target_items.get(target_id)
            if target:
                report_lines.append(f"目标项: {target.name} ({target.sheet_name})")
                report_lines.append(f"  公式: {formula.formula}")
                report_lines.append(f"  状态: {formula.status.value}")

                if formula.calculation_result is not None:
                    report_lines.append(f"  结果: {formula.calculation_result}")
                else:
                    report_lines.append("  结果: 未计算")

                report_lines.append("")

        # 错误信息
        if self.calculation_context.errors:
            report_lines.append("错误信息:")
            report_lines.append("-" * 40)
            for error in self.calculation_context.errors:
                report_lines.append(f"  - {error}")
            report_lines.append("")

        # 警告信息
        if self.calculation_context.warnings:
            report_lines.append("警告信息:")
            report_lines.append("-" * 40)
            for warning in self.calculation_context.warnings:
                report_lines.append(f"  - {warning}")
            report_lines.append("")

        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def save_formula_report(self, file_path: str) -> bool:
        """
        保存公式报告到文件

        Args:
            file_path: 输出文件路径

        Returns:
            bool: 是否成功
        """
        try:
            report_content = self.generate_formula_report()

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)

            return True

        except Exception as e:
            self.calculation_context.errors.append(f"保存报告失败: {str(e)}")
            return False

    def get_errors(self) -> List[str]:
        """获取错误列表"""
        return self.calculation_context.errors.copy()

    def get_warnings(self) -> List[str]:
        """获取警告列表"""
        return self.calculation_context.warnings.copy()

    def clear_errors(self):
        """清空错误列表"""
        self.calculation_context.errors.clear()

    def clear_warnings(self):
        """清空警告列表"""
        self.calculation_context.warnings.clear()

    def preview_calculations(self, target_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        预览计算结果（不修改实际数据）

        Args:
            target_ids: 要预览的目标项ID列表，None表示预览全部

        Returns:
            Dict[str, Any]: 预览结果
        """
        preview_results = {}

        # 确定要预览的公式
        formulas_to_preview = {}
        if target_ids:
            for target_id in target_ids:
                if target_id in self.workbook_manager.mapping_formulas:
                    formulas_to_preview[target_id] = self.workbook_manager.mapping_formulas[target_id]
        else:
            formulas_to_preview = self.workbook_manager.mapping_formulas

        # 构建值映射
        value_map = self.build_value_map()

        # 计算预览
        for target_id, formula in formulas_to_preview.items():
            target = self.workbook_manager.target_items.get(target_id)

            preview_data = {
                "target_name": target.name if target else "未知",
                "formula": formula.formula,
                "current_status": formula.status.value
            }

            # 尝试计算
            success, result = evaluate_formula_with_values_v2(formula.formula, value_map)

            if success:
                preview_data["preview_result"] = result
                preview_data["can_calculate"] = True
            else:
                preview_data["preview_error"] = str(result)
                preview_data["can_calculate"] = False

            preview_results[target_id] = preview_data

        return {
            "total_previewed": len(preview_results),
            "results": preview_results,
            "value_map_size": len(value_map)
        }

    def calculate_formula_realtime(self, formula_text: str,
                                 return_preview: bool = True) -> Dict[str, Any]:
        """
        实时计算公式（用于FormulaEditDialog的预览功能）

        Args:
            formula_text: 要计算的公式文本
            return_preview: 是否返回预览信息

        Returns:
            Dict[str, Any]: 实时计算结果
        """
        result = {
            "success": False,
            "value": None,
            "error": None,
            "validation": {
                "is_valid": False,
                "error_message": None
            },
            "references": [],
            "calculation_time": 0.0
        }

        try:
            start_time = datetime.now()

            # 1. 验证公式语法
            is_valid, validation_error = validate_formula_syntax_v2(formula_text)
            result["validation"]["is_valid"] = is_valid
            result["validation"]["error_message"] = validation_error

            if not is_valid:
                result["error"] = f"语法错误: {validation_error}"
                return result

            # 2. 解析公式引用
            try:
                references = parse_formula_references_v2(formula_text)
                result["references"] = references
            except Exception as e:
                result["error"] = f"引用解析错误: {str(e)}"
                return result

            # 3. 构建值映射表（使用缓存以提高性能）
            if not self.calculation_context.value_cache:
                self.calculation_context.value_cache = self.build_value_map()

            value_map = self.calculation_context.value_cache

            # 4. 计算公式
            success, calc_result = evaluate_formula_with_values_v2(formula_text, value_map)

            if success:
                result["success"] = True
                result["value"] = calc_result
            else:
                result["error"] = f"计算错误: {str(calc_result)}"

            # 5. 计算耗时
            end_time = datetime.now()
            result["calculation_time"] = (end_time - start_time).total_seconds() * 1000

        except Exception as e:
            result["error"] = f"未知错误: {str(e)}"

        return result

    def invalidate_cache(self):
        """
        清除缓存（当数据源发生变化时调用）
        """
        self.calculation_context.value_cache.clear()

    def update_formula_realtime(self, target_id: str, formula_text: str,
                              auto_validate: bool = True) -> bool:
        """
        实时更新公式（立即生效）

        Args:
            target_id: 目标项ID
            formula_text: 新的公式文本
            auto_validate: 是否自动验证和计算

        Returns:
            bool: 是否更新成功
        """
        try:
            # 1. 确保有映射公式对象
            if target_id not in self.workbook_manager.mapping_formulas:
                self.workbook_manager.mapping_formulas[target_id] = MappingFormula(
                    target_id=target_id
                )

            formula_obj = self.workbook_manager.mapping_formulas[target_id]

            # 2. 更新公式文本
            formula_obj.formula = formula_text

            if auto_validate and formula_text.strip():
                # 3. 自动验证
                is_valid, error_msg = validate_formula_syntax_v2(formula_text)

                if is_valid:
                    formula_obj.status = FormulaStatus.VALID
                    formula_obj.validation_error = None

                    # 4. 立即计算
                    calc_result = self.calculate_single_formula(target_id, formula_obj)
                    return calc_result.success
                else:
                    formula_obj.status = FormulaStatus.ERROR
                    formula_obj.validation_error = error_msg
                    formula_obj.calculation_result = None
                    return False
            else:
                # 仅更新，不验证
                formula_obj.status = FormulaStatus.DRAFT
                return True

        except Exception as e:
            if target_id in self.workbook_manager.mapping_formulas:
                self.workbook_manager.mapping_formulas[target_id].status = FormulaStatus.ERROR
                self.workbook_manager.mapping_formulas[target_id].validation_error = str(e)
            return False

    def get_available_references(self, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取可用的引用列表（用于FormulaEditDialog的数据源选择）

        Args:
            sheet_name: 要筛选的工作表名称，None表示获取全部

        Returns:
            List[Dict[str, Any]]: 可用引用列表
        """
        references = []

        for source_id, source in self.workbook_manager.source_items.items():
            # 筛选工作表
            if sheet_name and source.sheet_name != sheet_name:
                continue

            reference_info = {
                "id": source_id,
                "name": source.name,
                "sheet_name": source.sheet_name,
                "cell_address": source.cell_address,
                "value": source.value,
                "value_type": source.value_type,
                "reference_string": build_formula_reference_v2(source.sheet_name, source.name, source.cell_address),
                "display_text": f"{source.sheet_name}:\"{source.name}\"({source.cell_address}) = {source.value}"
            }
            references.append(reference_info)

        # 按工作表和名称排序
        references.sort(key=lambda x: (x["sheet_name"], x["name"]))
        return references

    def get_sheet_names(self) -> List[str]:
        """
        获取所有数据源工作表名称

        Returns:
            List[str]: 工作表名称列表
        """
        sheet_names = set()
        for source in self.workbook_manager.source_items.values():
            sheet_names.add(source.sheet_name)
        return sorted(list(sheet_names))

    def optimize_calculation_order(self) -> List[str]:
        """
        优化计算顺序（基于依赖关系）

        Returns:
            List[str]: 优化后的目标项ID列表
        """
        # 简化版本：按层级排序，避免循环依赖
        target_levels = []

        for target_id, target in self.workbook_manager.target_items.items():
            if target_id in self.workbook_manager.mapping_formulas:
                target_levels.append((target.hierarchical_level or 1, target_id))

        # 按层级排序：先计算低层级的项目
        target_levels.sort(key=lambda x: x[0])
        return [target_id for level, target_id in target_levels]


def create_calculation_engine(workbook_manager: WorkbookManager) -> CalculationEngine:
    """
    创建计算引擎实例

    Args:
        workbook_manager: 工作簿管理器

    Returns:
        CalculationEngine: 计算引擎实例
    """
    return CalculationEngine(workbook_manager)