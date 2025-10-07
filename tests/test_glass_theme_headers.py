# -*- coding: utf-8 -*-
"""
测试: 带玻璃化主题的列头显示
"""
import sys
sys.path.insert(0, 'd:\\Code\\快报填写程序-修改UI前(2)')

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import openpyxl

from components.advanced_widgets import SearchableSourceTree
from models.data_models import WorkbookManager
from modules.data_extractor import DataExtractor

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("带玻璃化主题 - 列头显示测试")
        self.setGeometry(100, 100, 1400, 900)

        # 🎨 应用玻璃化主题（简化版）
        self.apply_glass_theme()

        # 创建中央控件
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 添加说明标签
        info_label = QLabel("✓ 已应用玻璃化主题\n请检查列头文字是否显示")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; color: #2c3e50;")
        layout.addWidget(info_label)

        # 创建SearchableSourceTree
        self.source_tree = SearchableSourceTree()
        layout.addWidget(self.source_tree)

        # 加载数据
        self.load_data()

    def apply_glass_theme(self):
        """应用玻璃化主题（简化版，只包含关键部分）"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(240, 245, 250, 0.85),
                    stop:0.5 rgba(235, 242, 248, 0.8),
                    stop:1 rgba(230, 238, 245, 0.75));
            }

            QWidget#centralWidget {
                background: transparent;
            }

            QTreeView {
                background: rgba(255, 255, 255, 0.65);
                border: 1px solid rgba(190, 200, 215, 0.5);
                border-radius: 10px;
            }

            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(248, 250, 253, 0.92),
                    stop:1 rgba(240, 243, 250, 0.88));
                border: none;
                border-right: 1px solid rgba(190, 200, 215, 0.35);
                border-bottom: 1px solid rgba(190, 200, 215, 0.45);
                padding: 7px 10px;
                font-weight: 600;
                color: #2c3e50;
            }
        """)

    def load_data(self):
        """加载测试数据"""
        workbook_path = 'd:\\Code\\快报填写程序-修改UI前(2)\\上年科目余额表.xlsx'

        manager = WorkbookManager()
        manager.file_path = workbook_path

        temp_wb = openpyxl.load_workbook(workbook_path, data_only=True)
        for sheet_name in temp_wb.sheetnames:
            manager.data_source_sheets.append(sheet_name)
        temp_wb.close()

        extractor = DataExtractor(manager)
        success = extractor.extract_all_data()

        if success:
            print(f"[成功] 数据提取完成")
            print(f"  来源项: {len(manager.source_items)}")

            self.source_tree.set_column_metadata(manager.source_sheet_columns)
            self.source_tree.populate_source_items(manager.source_items)

            print(f"[完成] 数据已加载，请检查列头文字是否显示")
        else:
            print("[失败] 数据提取失败")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("\n" + "="*60)
    print("带玻璃化主题的测试窗口已启动")
    print("请检查列头文字是否正常显示（深色 #2c3e50）")
    print("="*60)
    sys.exit(app.exec())
