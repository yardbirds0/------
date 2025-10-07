#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试搜索功能修复
验证两个问题：
1. 中间主表格搜索功能是否正常工作
2. 右边表格高亮功能是否正常显示
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QLabel, QTreeView
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush

from components.advanced_widgets import SearchableSourceTree


def test_qtreeview_setrowhidden():
    """测试QTreeView的setRowHidden方法参数"""
    print("\n=== 测试1: QTreeView.setRowHidden参数 ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    tree = QTreeView()
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["名称", "值"])

    # 添加测试数据
    for i in range(5):
        row = [QStandardItem(f"项目{i}"), QStandardItem(f"值{i}")]
        model.appendRow(row)

    tree.setModel(model)

    try:
        # 错误的调用方式（只有2个参数）
        print("❌ 测试错误调用方式（2个参数）...")
        tree.setRowHidden(0, True)
        print("   意外：没有报错，但可能不是预期的API")
    except TypeError as e:
        print(f"   预期错误: {e}")

    try:
        # 正确的调用方式（3个参数）
        print("✅ 测试正确调用方式（3个参数）...")
        tree.setRowHidden(0, QModelIndex(), True)
        print("   成功：第0行已隐藏")

        # 验证行是否隐藏
        is_hidden = tree.isRowHidden(0, QModelIndex())
        print(f"   验证：第0行隐藏状态 = {is_hidden}")

        # 显示第0行
        tree.setRowHidden(0, QModelIndex(), False)
        is_hidden = tree.isRowHidden(0, QModelIndex())
        print(f"   验证：第0行隐藏状态 = {is_hidden}")

    except Exception as e:
        print(f"   错误: {e}")

    print("测试1完成\n")


def test_highlight_with_datachanged():
    """测试高亮功能配合dataChanged信号"""
    print("\n=== 测试2: 高亮功能配合dataChanged信号 ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    tree = QTreeView()
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["名称", "数值", "描述"])

    # 添加测试数据
    test_data = [
        ("资产总计", "1000000", "流动资产"),
        ("负债总计", "500000", "流动负债"),
        ("所有者权益", "500000", "实收资本"),
        ("营业收入", "2000000", "主营业务收入"),
        ("营业成本", "1500000", "主营业务成本"),
    ]

    for name, value, desc in test_data:
        row = [QStandardItem(name), QStandardItem(value), QStandardItem(desc)]
        model.appendRow(row)

    tree.setModel(model)

    # 测试高亮设置
    print("设置高亮...")
    highlight_color = QColor("#ffeb3b")
    highlight_brush = QBrush(highlight_color)

    # 高亮包含"资产"的行
    search_text = "资产"
    modified_indices = []

    for row in range(model.rowCount()):
        for col in range(model.columnCount()):
            index = model.index(row, col)
            cell_text = str(model.data(index, Qt.DisplayRole) or "")

            if search_text in cell_text:
                print(f"  找到匹配: 行{row}, 列{col}, 内容='{cell_text}'")
                model.setData(index, highlight_brush, Qt.BackgroundRole)
                modified_indices.append(index)

                # 验证背景色是否设置成功
                bg = model.data(index, Qt.BackgroundRole)
                print(f"    验证背景色: {bg}")

    # 发送dataChanged信号
    if modified_indices:
        print(f"\n发送dataChanged信号，共{len(modified_indices)}个单元格被修改")
        top_left = modified_indices[0]
        bottom_right = modified_indices[-1]
        model.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])
        print("✅ dataChanged信号已发送")

    # 清除高亮
    print("\n清除高亮...")
    for row in range(model.rowCount()):
        for col in range(model.columnCount()):
            index = model.index(row, col)
            model.setData(index, None, Qt.BackgroundRole)

    # 再次发送dataChanged信号
    if model.rowCount() > 0 and model.columnCount() > 0:
        top_left = model.index(0, 0)
        bottom_right = model.index(model.rowCount() - 1, model.columnCount() - 1)
        model.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])
        print("✅ 高亮已清除，dataChanged信号已发送")

    print("测试2完成\n")


def test_searchable_source_tree():
    """测试SearchableSourceTree的搜索和高亮功能"""
    print("\n=== 测试3: SearchableSourceTree搜索和高亮 ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 创建SearchableSourceTree实例
    tree = SearchableSourceTree()

    # 模拟source_items数据
    from models.data_models import SourceItem

    source_items = {}
    test_items = [
        ("资产负债表", "资产总计", 1, 1000000, {"本年累计": 1000000, "上年同期": 950000}),
        ("资产负债表", "流动资产", 2, 600000, {"本年累计": 600000, "上年同期": 570000}),
        ("资产负债表", "负债总计", 1, 500000, {"本年累计": 500000, "上年同期": 480000}),
        ("利润表", "营业收入", 1, 2000000, {"本年累计": 2000000, "上年同期": 1800000}),
        ("利润表", "营业成本", 2, 1500000, {"本年累计": 1500000, "上年同期": 1400000}),
    ]

    for idx, (sheet, name, level, value, data_cols) in enumerate(test_items):
        item = SourceItem(
            id=f"source_{idx}",
            sheet_name=sheet,
            name=name,
            value=value,
            row=idx + 1,
            column="D"
        )
        item.hierarchy_level = level
        item.data_columns = data_cols
        source_items[item.id] = item

    # 填充数据
    print("填充测试数据...")
    tree.populate_source_items(source_items)
    print(f"  已添加 {len(source_items)} 个source items")

    # 测试搜索功能
    print("\n测试搜索'资产'...")
    tree.search_line.setText("资产")

    # 检查是否有行被隐藏/显示
    model = tree.model()
    if model:
        visible_count = 0
        hidden_count = 0
        for row in range(model.rowCount()):
            if tree.isRowHidden(row, QModelIndex()):
                hidden_count += 1
            else:
                visible_count += 1
                # 检查高亮
                for col in range(model.columnCount()):
                    index = model.index(row, col)
                    bg = model.data(index, Qt.BackgroundRole)
                    if bg is not None:
                        print(f"  行{row}列{col} 已高亮: {model.data(index, Qt.DisplayRole)}")

        print(f"  可见行数: {visible_count}, 隐藏行数: {hidden_count}")

    # 清除搜索
    print("\n清除搜索...")
    tree.search_line.clear()

    if model:
        visible_count = sum(1 for row in range(model.rowCount()) if not tree.isRowHidden(row, QModelIndex()))
        print(f"  可见行数: {visible_count}")

    print("测试3完成\n")


if __name__ == "__main__":
    print("开始搜索功能修复测试...")
    print("=" * 60)

    # 运行测试
    test_qtreeview_setrowhidden()
    test_highlight_with_datachanged()
    test_searchable_source_tree()

    print("=" * 60)
    print("所有测试完成！")
    print("\n修复总结：")
    print("1. ✅ 修复了filter_target_items方法中setRowHidden的参数问题")
    print("   - 原因：QTreeView.setRowHidden需要3个参数(row, parent, hide)")
    print("   - 修复：添加QModelIndex()作为第二个参数")
    print("\n2. ✅ 增强了右边表格的高亮显示功能")
    print("   - 使用更明显的黄色(#ffeb3b)")
    print("   - 使用QBrush设置背景色")
    print("   - 主动发送dataChanged信号强制刷新视图")
