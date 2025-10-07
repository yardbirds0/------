#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证实时公式重算链路的最小集成测试"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication

from main import MainWindow
from models.data_models import (
    TargetItem,
    SourceItem,
    MappingFormula,
    FormulaStatus,
    create_empty_workbook_manager,
)
from utils.excel_utils import build_formula_reference_simple


def build_reference(sheet: str, name: str, cell: str) -> str:
    return build_formula_reference_simple(sheet, cell)


def create_target(target_id: str, name: str, sheet: str, row: int) -> TargetItem:
    return TargetItem(
        id=target_id,
        name=name,
        original_text=name,
        sheet_name=sheet,
        row=row,
        level=0,
    )


def create_source(source_id: str, name: str, sheet: str, cell: str, value: float) -> SourceItem:
    column = ''.join(filter(str.isalpha, cell)) or 'A'
    return SourceItem(
        id=source_id,
        sheet_name=sheet,
        name=name,
        cell_address=cell,
        row=int(''.join(filter(str.isdigit, cell)) or 1),
        column=column,
        value=value,
    )


def ensure_mapping(window: MainWindow, target_id: str, formula: str, status: FormulaStatus):
    window.workbook_manager.mapping_formulas[target_id] = MappingFormula(
        target_id=target_id,
        formula=formula,
        status=status,
    )


def main():
    app = QApplication([])

    window = MainWindow()
    window.hide()

    window.workbook_manager = create_empty_workbook_manager("test.xlsx")
    wm = window.workbook_manager

    # 构建基础数据
    source = create_source("source-1", "营业收入", "利润表", "D10", 120.0)
    wm.add_source_item(source)

    target1 = create_target("target-1", "一、营业总收入", "利润表", 5)
    target2 = create_target("target-2", "减：营业成本", "利润表", 6)

    wm.add_target_item(target1)
    wm.add_target_item(target2)

    window.target_model.set_workbook_manager(wm)

    # 测试1：有效公式应成功计算
    formula_ok = build_reference(source.sheet_name, source.name, source.cell_address)
    ensure_mapping(window, target1.id, formula_ok, FormulaStatus.USER_MODIFIED)

    window.recalculate_targets([target1.id], reason="test-success")

    result_ok = wm.calculation_results.get(target1.id)
    assert result_ok is not None and result_ok.success, "有效公式应计算成功"
    assert result_ok.result == source.value, "结果应匹配来源值"

    # 测试2：错误公式应标记错误
    bad_formula = "[利润表!营业成本]"  # 缺少规范格式
    ensure_mapping(window, target2.id, bad_formula, FormulaStatus.USER_MODIFIED)

    window.recalculate_targets([target2.id], reason="test-error")

    result_bad = wm.calculation_results.get(target2.id)
    assert result_bad is None or not result_bad.success, "错误公式应无法计算"
    assert wm.mapping_formulas[target2.id].status == FormulaStatus.ERROR, "状态应标记错误"

    # 测试3：清空公式应移除结果
    ensure_mapping(window, target1.id, "", FormulaStatus.EMPTY)
    window.recalculate_targets([target1.id], reason="test-clear")
    assert target1.id not in wm.calculation_results, "清空公式后不应保留结果"

    print("All realtime recalculation checks passed.")

    window.close()
    app.quit()


if __name__ == "__main__":
    main()
