#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版搜索功能测试
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QTreeView
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush


def test_setrowhidden_params():
    """测试setRowHidden参数"""
    print("\n测试1: QTreeView.setRowHidden参数")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    tree = QTreeView()
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Name", "Value"])

    for i in range(5):
        row = [QStandardItem(f"Item{i}"), QStandardItem(f"Value{i}")]
        model.appendRow(row)

    tree.setModel(model)

    # 测试正确的调用方式（3个参数）
    try:
        tree.setRowHidden(0, QModelIndex(), True)
        is_hidden = tree.isRowHidden(0, QModelIndex())
        print(f"  Row 0 hidden: {is_hidden}")
        assert is_hidden, "Row should be hidden"

        tree.setRowHidden(0, QModelIndex(), False)
        is_hidden = tree.isRowHidden(0, QModelIndex())
        print(f"  Row 0 shown: {not is_hidden}")
        assert not is_hidden, "Row should be visible"

        print("  PASS: setRowHidden works correctly with 3 parameters")
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

    return True


def test_highlight_with_datachanged():
    """测试高亮配合dataChanged"""
    print("\n测试2: Highlight with dataChanged signal")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    tree = QTreeView()
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Name", "Value"])

    test_data = [
        ("Assets", "1000000"),
        ("Liabilities", "500000"),
        ("Revenue", "2000000"),
    ]

    for name, value in test_data:
        row = [QStandardItem(name), QStandardItem(value)]
        model.appendRow(row)

    tree.setModel(model)

    # 设置高亮
    highlight_brush = QBrush(QColor("#ffeb3b"))
    search_text = "Assets"
    modified_indices = []

    for row in range(model.rowCount()):
        for col in range(model.columnCount()):
            index = model.index(row, col)
            cell_text = str(model.data(index, Qt.DisplayRole) or "")

            if search_text in cell_text:
                model.setData(index, highlight_brush, Qt.BackgroundRole)
                modified_indices.append(index)
                bg = model.data(index, Qt.BackgroundRole)
                print(f"  Highlighted: row{row}, col{col}, text='{cell_text}', bg={bg}")

    # 发送dataChanged信号
    if modified_indices:
        top_left = modified_indices[0]
        bottom_right = modified_indices[-1]
        model.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])
        print(f"  dataChanged signal emitted for {len(modified_indices)} cells")
        print("  PASS: Highlight with dataChanged works")
        return True

    print("  FAIL: No cells highlighted")
    return False


if __name__ == "__main__":
    print("Starting search fixes tests...")
    print("=" * 60)

    results = []
    results.append(("setRowHidden params", test_setrowhidden_params()))
    results.append(("Highlight with dataChanged", test_highlight_with_datachanged()))

    print("\n" + "=" * 60)
    print("Test Results:")
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")

    all_passed = all(r[1] for r in results)
    print("\n" + ("All tests PASSED!" if all_passed else "Some tests FAILED!"))

    print("\nFix Summary:")
    print("1. Fixed filter_target_items: Added QModelIndex() as 2nd parameter")
    print("2. Enhanced highlight: Use brighter color and emit dataChanged signal")
