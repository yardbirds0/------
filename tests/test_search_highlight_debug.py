#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索高亮问题诊断脚本

测试两个问题：
1. 中间主表格高亮后文字消失
2. 右侧来源项库表格高亮未生效
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTreeView, QLineEdit, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush

# 导入主程序的高亮delegate
from main import SearchHighlightDelegate


class TestWindow(QMainWindow):
    """测试窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("搜索高亮问题诊断")
        self.resize(1200, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # 左侧：测试问题1（中间主表格）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("<b>问题1：主表格高亮后文字消失</b>"))

        self.search_input1 = QLineEdit()
        self.search_input1.setPlaceholderText("输入搜索文本...")
        left_layout.addWidget(self.search_input1)

        search_btn1 = QPushButton("搜索（设置高亮）")
        search_btn1.clicked.connect(self.test_main_table_highlight)
        left_layout.addWidget(search_btn1)

        self.main_table = QTreeView()
        self.main_table.setAlternatingRowColors(True)
        self.main_table.setRootIsDecorated(False)

        # 应用SearchHighlightDelegate
        self.search_delegate = SearchHighlightDelegate(self.main_table)
        self.main_table.setItemDelegate(self.search_delegate)

        # 创建测试数据
        self.main_model = QStandardItemModel()
        self.main_model.setHorizontalHeaderLabels(["状态", "级别", "项目名称", "数值"])

        for i in range(5):
            row = [
                QStandardItem(f"待填充"),
                QStandardItem(f"1.{i}"),
                QStandardItem(f"测试项目{i}"),
                QStandardItem(f"{i * 1000}")
            ]
            self.main_model.appendRow(row)

        self.main_table.setModel(self.main_model)
        left_layout.addWidget(self.main_table)

        # 右侧：测试问题2（来源项库）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("<b>问题2：来源项库高亮未生效</b>"))

        self.search_input2 = QLineEdit()
        self.search_input2.setPlaceholderText("输入搜索文本...")
        right_layout.addWidget(self.search_input2)

        search_btn2 = QPushButton("搜索（设置高亮）")
        search_btn2.clicked.connect(self.test_source_tree_highlight)
        right_layout.addWidget(search_btn2)

        test_delegate_btn = QPushButton("测试：应用SearchHighlightDelegate")
        test_delegate_btn.clicked.connect(self.apply_delegate_to_source)
        right_layout.addWidget(test_delegate_btn)

        self.source_tree = QTreeView()
        self.source_tree.setRootIsDecorated(True)

        # 创建测试数据
        self.source_model = QStandardItemModel()
        self.source_model.setHorizontalHeaderLabels(["项目名称", "值", "单位"])

        for i in range(3):
            parent = QStandardItem(f"工作表{i}")
            for j in range(3):
                row = [
                    QStandardItem(f"来源项{i}-{j}"),
                    QStandardItem(f"{j * 100}"),
                    QStandardItem("元")
                ]
                parent.appendRow(row)
            self.source_model.appendRow(parent)

        self.source_tree.setModel(self.source_model)
        self.source_tree.expandAll()
        right_layout.addWidget(self.source_tree)

        layout.addWidget(left_widget)
        layout.addWidget(right_widget)

        # 添加CSS样式（模拟主程序）
        self.setStyleSheet("""
            QTreeView {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(190, 200, 215, 0.5);
                border-radius: 8px;
            }
            QTreeView::item {
                padding: 5px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTreeView::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)

    def test_main_table_highlight(self):
        """测试主表格高亮"""
        search_text = self.search_input1.text().lower()
        if not search_text:
            print("请输入搜索文本")
            return

        print(f"\n=== 测试主表格高亮：搜索 '{search_text}' ===")
        highlight_color = QColor("#ffe0f0")

        for row in range(self.main_model.rowCount()):
            for col in range(self.main_model.columnCount()):
                index = self.main_model.index(row, col)
                text = self.main_model.data(index, Qt.DisplayRole)

                if text and search_text in str(text).lower():
                    # 设置背景色
                    self.main_model.setData(index, QBrush(highlight_color), Qt.BackgroundRole)
                    print(f"  高亮单元格 ({row}, {col}): {text}")
                    print(f"    - 设置BackgroundRole为: {highlight_color.name()}")

                    # 验证是否设置成功
                    bg = self.main_model.data(index, Qt.BackgroundRole)
                    print(f"    - 读取BackgroundRole: {bg}")
                else:
                    # 清除背景色
                    self.main_model.setData(index, None, Qt.BackgroundRole)

        # 触发视图更新
        top_left = self.main_model.index(0, 0)
        bottom_right = self.main_model.index(
            self.main_model.rowCount() - 1,
            self.main_model.columnCount() - 1
        )
        self.main_model.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])
        print("  触发dataChanged信号")

    def test_source_tree_highlight(self):
        """测试来源项树高亮"""
        search_text = self.search_input2.text().lower()
        if not search_text:
            print("请输入搜索文本")
            return

        print(f"\n=== 测试来源项树高亮：搜索 '{search_text}' ===")
        highlight_color = QColor("#ffeb3b")  # 黄色

        def process_item(item: QStandardItem):
            if not item:
                return

            parent_index = item.index().parent()
            row = item.row()

            for col in range(self.source_model.columnCount()):
                index = self.source_model.index(row, col, parent_index)
                text = self.source_model.data(index, Qt.DisplayRole)

                if text and search_text in str(text).lower():
                    # 设置背景色
                    self.source_model.setData(index, QBrush(highlight_color), Qt.BackgroundRole)
                    print(f"  高亮单元格: {text}")
                    print(f"    - 设置BackgroundRole为: {highlight_color.name()}")

                    # 验证是否设置成功
                    bg = self.source_model.data(index, Qt.BackgroundRole)
                    print(f"    - 读取BackgroundRole: {bg}")
                else:
                    self.source_model.setData(index, None, Qt.BackgroundRole)

            # 递归处理子项
            for child_row in range(item.rowCount()):
                process_item(item.child(child_row))

        # 处理所有项
        for row in range(self.source_model.rowCount()):
            root_item = self.source_model.item(row)
            process_item(root_item)

        print("  触发dataChanged信号")
        top_left = self.source_model.index(0, 0)
        bottom_right = self.source_model.index(
            self.source_model.rowCount() - 1,
            self.source_model.columnCount() - 1
        )
        self.source_model.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])

    def apply_delegate_to_source(self):
        """为来源项树应用SearchHighlightDelegate"""
        print("\n=== 为来源项树应用SearchHighlightDelegate ===")
        delegate = SearchHighlightDelegate(self.source_tree)
        self.source_tree.setItemDelegate(delegate)
        print("  已应用delegate，现在可以搜索测试")


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()

    print("\n" + "="*80)
    print("搜索高亮问题诊断脚本")
    print("="*80)
    print("\n使用说明：")
    print("1. 左侧测试主表格：")
    print("   - 输入搜索文本（如'测试'），点击'搜索'")
    print("   - 观察：文字是否消失？高亮是否显示？")
    print("   - 检查控制台输出的BackgroundRole设置情况")
    print("\n2. 右侧测试来源项库：")
    print("   - 输入搜索文本（如'来源'），点击'搜索'")
    print("   - 观察：高亮是否显示？")
    print("   - 点击'测试：应用SearchHighlightDelegate'后再次搜索")
    print("   - 对比应用delegate前后的区别")
    print("\n" + "="*80 + "\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
