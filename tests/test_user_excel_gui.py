# -*- coding: utf-8 -*-
"""
GUI测试: 上年科目余额表.xlsx
"""
import sys
sys.path.insert(0, 'd:\\Code\\快报填写程序-修改UI前(2)')

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
import openpyxl

from components.advanced_widgets import SearchableSourceTree
from models.data_models import WorkbookManager
from modules.data_extractor import DataExtractor

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("上年科目余额表 - 列头显示测试")
        self.setGeometry(100, 100, 1400, 900)

        # 创建中央控件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 添加说明标签
        info_label = QLabel("请在下拉菜单中选择工作表,查看列头是否显示")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(info_label)

        # 创建SearchableSourceTree
        self.source_tree = SearchableSourceTree()
        layout.addWidget(self.source_tree)

        # 加载数据
        self.load_data()

    def load_data(self):
        """加载测试数据"""
        workbook_path = 'd:\\Code\\快报填写程序-修改UI前(2)\\上年科目余额表.xlsx'

        # 创建管理器
        manager = WorkbookManager()
        manager.file_path = workbook_path

        # 分类工作表 - 全部作为数据源表
        temp_wb = openpyxl.load_workbook(workbook_path, data_only=True)
        for sheet_name in temp_wb.sheetnames:
            manager.data_source_sheets.append(sheet_name)
        temp_wb.close()

        print(f"数据源表: {manager.data_source_sheets}")

        # 提取数据
        extractor = DataExtractor(manager)
        success = extractor.extract_all_data()

        if success:
            print(f"\n[成功] 数据提取完成")
            print(f"  来源项: {len(manager.source_items)}")
            print(f"  来源表数量: {len(manager.source_sheet_columns)}")

            # 显示列元数据详情
            print(f"\n列元数据详情:")
            for sheet_name, columns in manager.source_sheet_columns.items():
                print(f"\n  工作表: {sheet_name}")
                print(f"    列数: {len(columns)}")
                print(f"    列头:")
                for idx, col in enumerate(columns):
                    primary = col.get('primary_header', '')
                    secondary = col.get('secondary_header', '')
                    display = col.get('display_name', '')
                    print(f"      {idx+1}. {display} (主:{primary}, 次:{secondary})")

            # 设置数据到树控件
            print(f"\n设置列元数据到树控件...")
            self.source_tree.set_column_metadata(manager.source_sheet_columns)

            print(f"填充来源项到树控件...")
            self.source_tree.populate_source_items(manager.source_items)

            print(f"\n[完成] 数据已加载到界面")
            print(f"  可用工作表: {self.source_tree.available_sheets}")
            print(f"  当前工作表: {self.source_tree.current_sheet}")
            print(f"  当前列头: {self.source_tree.current_headers}")
        else:
            print("[失败] 数据提取失败")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("\n========================================")
    print("GUI窗口已启动,请检查列头显示")
    print("========================================")
    sys.exit(app.exec())
