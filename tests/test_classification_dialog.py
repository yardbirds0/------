#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试独立的工作表分类对话框
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from dialogs.sheet_classification_dialog import SheetClassificationDialog
from models.data_models import WorkbookManager

def test_classification_dialog():
    """测试分类对话框"""
    app = QApplication(sys.argv)

    # 创建一个模拟的工作簿管理器
    workbook_manager = WorkbookManager()
    workbook_manager.file_name = "测试文件.xlsx"
    workbook_manager.flash_report_sheets = ["快报表1", "快报表2"]
    workbook_manager.data_source_sheets = ["利润表", "资产负债表", "现金流量表"]

    # 创建并显示对话框
    dialog = SheetClassificationDialog()
    dialog.load_workbook(workbook_manager)

    result = dialog.exec()
    if result == dialog.Accepted:
        classifications = dialog.get_final_classifications()
        print("用户确认的分类结果:")
        print(f"快报表: {classifications['flash_reports']}")
        print(f"数据来源表: {classifications['data_sources']}")
        print(f"已取消: {classifications['cancelled']}")
    else:
        print("用户取消了分类")

if __name__ == "__main__":
    test_classification_dialog()