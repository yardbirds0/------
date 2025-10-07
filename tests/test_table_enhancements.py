"""
测试表格增强效果：
1. 扩大的滚动条（22px）
2. 放大的字体（14pt）
3. 竖向分割线
"""
import sys
sys.path.insert(0, 'd:\\Code\\快报填写程序-修改UI前(2)')

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QTableView, QTreeView, QTableWidget, QTableWidgetItem, QLabel,
                               QStandardItemModel, QStandardItem, QHeaderView, QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# 导入main.py以使用相同的样式
import main

class TableEnhancementTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("表格增强效果测试 - 滚动条/字体/分割线")
        self.setGeometry(100, 100, 1400, 900)

        # 应用main.py中的全局样式
        self.apply_main_stylesheet()

        # 创建中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 标题
        title = QLabel("✨ 表格增强效果测试")
        title.setStyleSheet("font-size: 20pt; font-weight: bold; color: #5a3a47; padding: 10px;")
        layout.addWidget(title)

        # 说明
        info = QLabel(
            "🎯 测试内容：\n"
            "  • 滚动条：从13px扩大到22px，添加渐变效果\n"
            "  • 字体：从默认扩大到14pt（约1.5倍）\n"
            "  • 分割线：添加淡粉色竖向单元格分割线\n"
            "  • Padding：调整以适应更大字体"
        )
        info.setStyleSheet("font-size: 12pt; color: #666; padding: 10px; background: rgba(255,250,253,0.5); border-radius: 8px;")
        layout.addWidget(info)

        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # 左侧：QTableView（使用Model）
        table_view_widget = QWidget()
        table_view_layout = QVBoxLayout(table_view_widget)
        table_view_layout.addWidget(QLabel("📊 QTableView（主表格）"))

        self.table_view = QTableView()
        self.setup_table_view()
        table_view_layout.addWidget(self.table_view)
        splitter.addWidget(table_view_widget)

        # 中间：QTreeView
        tree_view_widget = QWidget()
        tree_view_layout = QVBoxLayout(tree_view_widget)
        tree_view_layout.addWidget(QLabel("🌲 QTreeView（来源树）"))

        self.tree_view = QTreeView()
        self.setup_tree_view()
        tree_view_layout.addWidget(self.tree_view)
        splitter.addWidget(tree_view_widget)

        # 右侧：QTableWidget
        table_widget_widget = QWidget()
        table_widget_layout = QVBoxLayout(table_widget_widget)
        table_widget_layout.addWidget(QLabel("📝 QTableWidget（详情表）"))

        self.table_widget = QTableWidget()
        self.setup_table_widget()
        table_widget_layout.addWidget(self.table_widget)
        splitter.addWidget(table_widget_widget)

        # 设置分割比例
        splitter.setSizes([450, 450, 450])

    def apply_main_stylesheet(self):
        """应用main.py中的全局样式"""
        # 直接创建一个MainWindow实例来获取样式
        # 但不显示它，只是为了获取stylesheet
        temp_window = main.MainWindow()
        self.setStyleSheet(temp_window.styleSheet())

    def setup_table_view(self):
        """设置QTableView示例数据"""
        model = QStandardItemModel(15, 5)
        model.setHorizontalHeaderLabels(["状态", "级别", "项目名称", "本月数", "累计数"])

        for row in range(15):
            for col in range(5):
                if col == 0:
                    item = QStandardItem("✓" if row % 3 == 0 else "")
                elif col == 1:
                    item = QStandardItem(f"{row + 1}")
                elif col == 2:
                    indent = "  " * (row % 3)
                    item = QStandardItem(f"{indent}项目{row + 1}")
                else:
                    item = QStandardItem(f"{(row + 1) * 1000 + col * 100:,.2f}")
                model.setItem(row, col, item)

        self.table_view.setModel(model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_view.verticalHeader().setDefaultSectionSize(40)

    def setup_tree_view(self):
        """设置QTreeView示例数据"""
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["科目名称", "期初余额", "本期发生", "期末余额"])

        # 添加根节点
        for i in range(5):
            parent = QStandardItem(f"一级科目{i + 1}")
            row_data = [
                parent,
                QStandardItem(f"{(i + 1) * 10000:,.2f}"),
                QStandardItem(f"{(i + 1) * 5000:,.2f}"),
                QStandardItem(f"{(i + 1) * 15000:,.2f}")
            ]

            # 添加子节点
            for j in range(3):
                child = QStandardItem(f"  二级科目{i + 1}.{j + 1}")
                child_row = [
                    child,
                    QStandardItem(f"{(i + 1) * 1000 + j * 100:,.2f}"),
                    QStandardItem(f"{(i + 1) * 500 + j * 50:,.2f}"),
                    QStandardItem(f"{(i + 1) * 1500 + j * 150:,.2f}")
                ]
                parent.appendRow(child_row)

            model.appendRow(row_data)

        self.tree_view.setModel(model)
        self.tree_view.expandAll()
        self.tree_view.header().setSectionResizeMode(QHeaderView.ResizeToContents)

    def setup_table_widget(self):
        """设置QTableWidget示例数据"""
        self.table_widget.setRowCount(10)
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["来源表", "项目", "数值", "备注"])

        for row in range(10):
            self.table_widget.setItem(row, 0, QTableWidgetItem(f"数据表{row + 1}"))
            self.table_widget.setItem(row, 1, QTableWidgetItem(f"数据项{row + 1}"))
            self.table_widget.setItem(row, 2, QTableWidgetItem(f"{(row + 1) * 2500:,.2f}"))
            self.table_widget.setItem(row, 3, QTableWidgetItem(f"说明{row + 1}"))

        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.verticalHeader().setDefaultSectionSize(40)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TableEnhancementTestWindow()
    window.show()
    sys.exit(app.exec())
