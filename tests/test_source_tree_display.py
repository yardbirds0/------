# -*- coding: utf-8 -*-
"""
GUI测试：科目余额表列头显示
"""
import sys
sys.path.insert(0, 'd:\\Code\\快报填写程序-修改UI前(2)')

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
import openpyxl

from components.advanced_widgets import SearchableSourceTree
from models.data_models import WorkbookManager
from modules.data_extractor import DataExtractor

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("科目余额表列头显示测试")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中央控件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 创建SearchableSourceTree
        self.source_tree = SearchableSourceTree()
        layout.addWidget(self.source_tree)

        # 加载数据
        self.load_data()

    def load_data(self):
        """加载测试数据"""
        workbook_path = 'd:\\Code\\快报填写程序-修改UI前(2)\\sample.xlsx'

        # 创建管理器
        manager = WorkbookManager()
        manager.file_path = workbook_path

        # 分类工作表
        temp_wb = openpyxl.load_workbook(workbook_path, data_only=True)
        for sheet_name in temp_wb.sheetnames:
            if '快报' in sheet_name:
                manager.flash_report_sheets.append(sheet_name)
            else:
                manager.data_source_sheets.append(sheet_name)
        temp_wb.close()

        # 提取数据
        extractor = DataExtractor(manager)
        success = extractor.extract_all_data()

        if success:
            print(f"[成功] 数据提取成功")
            print(f"  目标项: {len(manager.target_items)}")
            print(f"  来源项: {len(manager.source_items)}")
            print(f"  来源表列元数据: {len(manager.source_sheet_columns)}")

            # 检查科目余额表
            for sheet_name in manager.source_sheet_columns:
                if '科目余额' in sheet_name:
                    columns = manager.source_sheet_columns[sheet_name]
                    print(f"\n科目余额表 '{sheet_name}':")
                    print(f"  列数: {len(columns)}")
                    for col in columns[:5]:
                        print(f"    - {col.get('display_name')}")

            # 设置数据到树控件
            self.source_tree.set_column_metadata(manager.source_sheet_columns)
            self.source_tree.populate_source_items(manager.source_items)

            print(f"\n[完成] 数据已加载到界面")
            print(f"  可用工作表: {self.source_tree.available_sheets}")
            print(f"  当前工作表: {self.source_tree.current_sheet}")
        else:
            print("[失败] 数据提取失败")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
