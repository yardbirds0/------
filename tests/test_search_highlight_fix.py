#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索高亮修复验证脚本

验证两个问题已修复：
1. 主表格高亮后文字正常显示
2. 来源项库高亮正常显示
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTreeView, QLineEdit, QLabel, QPushButton, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush

# 导入主程序的高亮delegate
from main import SearchHighlightDelegate


class TestWindow(QMainWindow):
    """测试窗口 - 验证搜索高亮修复"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("搜索高亮修复验证 - 两个问题均已修复")
        self.resize(1400, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 说明标签
        info_label = QLabel(
            "<h2>🔍 搜索高亮修复验证</h2>"
            "<p><b>问题1修复</b>：主表格高亮后文字消失 → 现在文字正常显示</p>"
            "<p><b>问题2修复</b>：来源项库高亮未生效 → 现在高亮正常显示</p>"
            "<p><b>测试方法</b>：在搜索框输入文字，点击搜索按钮，观察高亮效果</p>"
        )
        info_label.setStyleSheet("background: #e3f2fd; padding: 15px; border-radius: 5px;")
        main_layout.addWidget(info_label)

        # 创建分隔器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：主表格测试
        left_widget = self._create_main_table_test()
        splitter.addWidget(left_widget)

        # 右侧：来源项库测试
        right_widget = self._create_source_tree_test()
        splitter.addWidget(right_widget)

        splitter.setSizes([700, 700])
        main_layout.addWidget(splitter)

        # 应用CSS样式（模拟主程序）
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

    def _create_main_table_test(self) -> QWidget:
        """创建主表格测试区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 标题
        title = QLabel("<b>问题1：主表格（已修复✅）</b>")
        title.setStyleSheet("font-size: 14px; color: #1976d2;")
        layout.addWidget(title)

        # 搜索框
        search_layout = QHBoxLayout()
        self.search_input1 = QLineEdit()
        self.search_input1.setPlaceholderText("输入搜索文本（如：测试、1000）")
        search_layout.addWidget(self.search_input1, 3)

        search_btn = QPushButton("🔍 搜索")
        search_btn.clicked.connect(self.test_main_table_highlight)
        search_layout.addWidget(search_btn, 1)

        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(self.clear_main_table_highlight)
        search_layout.addWidget(clear_btn, 1)

        layout.addLayout(search_layout)

        # 表格
        self.main_table = QTreeView()
        self.main_table.setAlternatingRowColors(True)
        self.main_table.setRootIsDecorated(False)

        # 🔧 应用修复后的SearchHighlightDelegate
        self.search_delegate = SearchHighlightDelegate(self.main_table)
        self.main_table.setItemDelegate(self.search_delegate)

        # 创建测试数据
        self.main_model = QStandardItemModel()
        self.main_model.setHorizontalHeaderLabels(["状态", "级别", "项目名称", "数值"])

        test_data = [
            ("待填充", "1.1", "测试项目A", "1000"),
            ("已完成", "1.2", "测试项目B", "2000"),
            ("待填充", "2.1", "营业收入", "5000"),
            ("已完成", "2.2", "营业成本", "3000"),
            ("待填充", "3.1", "利润总额", "1000"),
        ]

        for data in test_data:
            row = [QStandardItem(str(val)) for val in data]
            self.main_model.appendRow(row)

        self.main_table.setModel(self.main_model)
        self.main_table.resizeColumnToContents(0)
        self.main_table.resizeColumnToContents(1)
        layout.addWidget(self.main_table)

        # 状态标签
        self.main_status = QLabel("等待搜索...")
        self.main_status.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.main_status)

        return widget

    def _create_source_tree_test(self) -> QWidget:
        """创建来源项库测试区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 标题
        title = QLabel("<b>问题2：来源项库（已修复✅）</b>")
        title.setStyleSheet("font-size: 14px; color: #1976d2;")
        layout.addWidget(title)

        # 搜索框
        search_layout = QHBoxLayout()
        self.search_input2 = QLineEdit()
        self.search_input2.setPlaceholderText("输入搜索文本（如：科目、100）")
        search_layout.addWidget(self.search_input2, 3)

        search_btn = QPushButton("🔍 搜索")
        search_btn.clicked.connect(self.test_source_tree_highlight)
        search_layout.addWidget(search_btn, 1)

        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(self.clear_source_tree_highlight)
        search_layout.addWidget(clear_btn, 1)

        layout.addLayout(search_layout)

        # 树
        self.source_tree = QTreeView()
        self.source_tree.setRootIsDecorated(True)

        # 🔧 应用修复后的SearchHighlightDelegate（修复问题2）
        self.source_delegate = SearchHighlightDelegate(self.source_tree)
        self.source_tree.setItemDelegate(self.source_delegate)

        # 创建测试数据
        self.source_model = QStandardItemModel()
        self.source_model.setHorizontalHeaderLabels(["项目名称", "值", "单位"])

        sheets_data = [
            ("资产负债表", [
                ("货币资金", "10000", "元"),
                ("应收账款", "5000", "元"),
                ("固定资产", "20000", "元"),
            ]),
            ("利润表", [
                ("营业收入", "50000", "元"),
                ("营业成本", "30000", "元"),
                ("管理费用", "5000", "元"),
            ]),
            ("科目余额表", [
                ("科目1001", "1000", "元"),
                ("科目2002", "2000", "元"),
                ("科目3003", "3000", "元"),
            ]),
        ]

        for sheet_name, items in sheets_data:
            parent = QStandardItem(sheet_name)
            for item_data in items:
                row = [QStandardItem(val) for val in item_data]
                parent.appendRow(row)
            self.source_model.appendRow(parent)

        self.source_tree.setModel(self.source_model)
        self.source_tree.expandAll()
        self.source_tree.resizeColumnToContents(0)
        layout.addWidget(self.source_tree)

        # 状态标签
        self.source_status = QLabel("等待搜索...")
        self.source_status.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.source_status)

        return widget

    def test_main_table_highlight(self):
        """测试主表格高亮"""
        search_text = self.search_input1.text().lower()
        if not search_text:
            self.main_status.setText("请输入搜索文本")
            return

        highlight_color = QColor("#ffe0f0")  # 粉色
        match_count = 0

        for row in range(self.main_model.rowCount()):
            for col in range(self.main_model.columnCount()):
                index = self.main_model.index(row, col)
                text = self.main_model.data(index, Qt.DisplayRole)

                if text and search_text in str(text).lower():
                    self.main_model.setData(index, QBrush(highlight_color), Qt.BackgroundRole)
                    match_count += 1
                else:
                    self.main_model.setData(index, None, Qt.BackgroundRole)

        # 触发视图更新
        top_left = self.main_model.index(0, 0)
        bottom_right = self.main_model.index(
            self.main_model.rowCount() - 1,
            self.main_model.columnCount() - 1
        )
        self.main_model.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])

        self.main_status.setText(f"✅ 找到 {match_count} 个匹配项，高亮已应用（文字应可见）")

    def clear_main_table_highlight(self):
        """清除主表格高亮"""
        for row in range(self.main_model.rowCount()):
            for col in range(self.main_model.columnCount()):
                index = self.main_model.index(row, col)
                self.main_model.setData(index, None, Qt.BackgroundRole)

        top_left = self.main_model.index(0, 0)
        bottom_right = self.main_model.index(
            self.main_model.rowCount() - 1,
            self.main_model.columnCount() - 1
        )
        self.main_model.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])
        self.main_status.setText("已清除高亮")

    def test_source_tree_highlight(self):
        """测试来源项树高亮"""
        search_text = self.search_input2.text().lower()
        if not search_text:
            self.source_status.setText("请输入搜索文本")
            return

        highlight_color = QColor("#ffeb3b")  # 黄色
        match_count = 0

        def process_item(item: QStandardItem):
            nonlocal match_count
            if not item:
                return

            parent_index = item.index().parent()
            row = item.row()

            for col in range(self.source_model.columnCount()):
                index = self.source_model.index(row, col, parent_index)
                text = self.source_model.data(index, Qt.DisplayRole)

                if text and search_text in str(text).lower():
                    self.source_model.setData(index, QBrush(highlight_color), Qt.BackgroundRole)
                    match_count += 1
                else:
                    self.source_model.setData(index, None, Qt.BackgroundRole)

            # 递归处理子项
            for child_row in range(item.rowCount()):
                process_item(item.child(child_row))

        # 处理所有项
        for row in range(self.source_model.rowCount()):
            root_item = self.source_model.item(row)
            process_item(root_item)

        # 触发视图更新
        top_left = self.source_model.index(0, 0)
        bottom_right = self.source_model.index(
            self.source_model.rowCount() - 1,
            self.source_model.columnCount() - 1
        )
        self.source_model.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])

        self.source_status.setText(f"✅ 找到 {match_count} 个匹配项，高亮已应用")

    def clear_source_tree_highlight(self):
        """清除来源项树高亮"""
        def clear_item(item: QStandardItem):
            if not item:
                return

            parent_index = item.index().parent()
            row = item.row()

            for col in range(self.source_model.columnCount()):
                index = self.source_model.index(row, col, parent_index)
                self.source_model.setData(index, None, Qt.BackgroundRole)

            for child_row in range(item.rowCount()):
                clear_item(item.child(child_row))

        for row in range(self.source_model.rowCount()):
            root_item = self.source_model.item(row)
            clear_item(root_item)

        top_left = self.source_model.index(0, 0)
        bottom_right = self.source_model.index(
            self.source_model.rowCount() - 1,
            self.source_model.columnCount() - 1
        )
        self.source_model.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])
        self.source_status.setText("已清除高亮")


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()

    print("\n" + "="*80)
    print("搜索高亮修复验证脚本")
    print("="*80)
    print("\n核心修复：")
    print("1. 问题1修复：SearchHighlightDelegate先绘制文字，再叠加半透明高亮背景")
    print("   - 原因：之前先绘制背景再绘制文字，painter状态错误导致文字消失")
    print("   - 解决：调用super().paint()绘制文字，然后用fillRect叠加透明背景")
    print("\n2. 问题2修复：为来源项库应用SearchHighlightDelegate")
    print("   - 原因：来源项库只设置了BackgroundRole，但被CSS覆盖")
    print("   - 解决：为source_tree设置SearchHighlightDelegate")
    print("\n测试步骤：")
    print("1. 左侧主表格：输入'测试'或'1000'，点击搜索")
    print("   - 预期：粉色高亮，文字清晰可见✅")
    print("2. 右侧来源项库：输入'科目'或'100'，点击搜索")
    print("   - 预期：黄色高亮，文字清晰可见✅")
    print("3. 点击'清除'按钮清除高亮")
    print("\n" + "="*80 + "\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
