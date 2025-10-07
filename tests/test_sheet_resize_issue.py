#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试程序：专门测试"企业财务快报利润因素分析表"导致的自动扩宽功能失效问题
"""

import sys
import os
import json
import traceback
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QTextEdit, QLabel, QComboBox,
    QTableView, QHeaderView, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt, QTimer, QAbstractItemModel, QModelIndex, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem

# 添加项目路径
sys.path.insert(0, r'd:\Code\快报填写程序')

from models.data_models import WorkbookManager, TargetItem
from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from components.advanced_widgets import ensure_interactive_header, schedule_row_resize


class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试：企业财务快报利润因素分析表问题")
        self.resize(1400, 800)

        # 初始化组件
        self.workbook_manager = WorkbookManager()
        self.file_manager = FileManager()
        self.data_extractor = DataExtractor()

        # 设置日志
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)

        # 用于记录错误
        self.error_count = 0
        self.resize_call_count = 0
        self._main_auto_resizing = False
        self._user_column_widths = {}

        self.setup_ui()
        self.log("程序启动，请加载Excel文件进行测试")

    def setup_ui(self):
        """设置界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 控制按钮
        control_group = QGroupBox("控制面板")
        control_layout = QHBoxLayout()
        control_group.setLayout(control_layout)

        self.load_btn = QPushButton("加载测试Excel文件")
        self.load_btn.clicked.connect(self.load_test_file)
        control_layout.addWidget(self.load_btn)

        control_layout.addWidget(QLabel("选择工作表:"))
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentTextChanged.connect(self.on_sheet_changed)
        control_layout.addWidget(self.sheet_combo)

        self.test_resize_btn = QPushButton("手动触发列宽调整")
        self.test_resize_btn.clicked.connect(lambda: self.schedule_main_table_resize(0))
        control_layout.addWidget(self.test_resize_btn)

        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self.log_text.clear)
        control_layout.addWidget(self.clear_log_btn)

        control_layout.addStretch()
        layout.addWidget(control_group)

        # 主表格
        table_group = QGroupBox("主数据表格")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)

        self.main_table = QTableView()
        self.main_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.main_table)

        layout.addWidget(table_group)

        # 日志区域
        log_group = QGroupBox(f"日志输出 (错误: {self.error_count}, 调整次数: {self.resize_call_count})")
        self.log_group = log_group
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = QTimer().singleShot(0, lambda: None)  # 获取当前时间
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")

        if level == "ERROR":
            self.error_count += 1
            self.log_text.append(f'<span style="color: red;">[{time_str}] {level}: {message}</span>')
        elif level == "WARNING":
            self.log_text.append(f'<span style="color: orange;">[{time_str}] {level}: {message}</span>')
        elif level == "SUCCESS":
            self.log_text.append(f'<span style="color: green;">[{time_str}] {level}: {message}</span>')
        else:
            self.log_text.append(f"[{time_str}] {level}: {message}")

        # 更新错误计数显示
        self.log_group.setTitle(f"日志输出 (错误: {self.error_count}, 调整次数: {self.resize_call_count})")

    def load_test_file(self):
        """加载测试文件"""
        try:
            # 查找包含"快报"的Excel文件
            test_dir = Path(r"d:\Code\快报填写程序")
            excel_files = list(test_dir.glob("*.xlsx")) + list(test_dir.glob("*.xls"))

            target_file = None
            for file in excel_files:
                if "快报" in file.name and not file.name.startswith("~"):
                    target_file = file
                    break

            if not target_file:
                self.log("未找到包含'快报'的Excel文件", "ERROR")
                return

            self.log(f"正在加载文件: {target_file.name}")

            # 加载文件
            success = self.file_manager.load_file(str(target_file))
            if not success:
                self.log("文件加载失败", "ERROR")
                return

            # 获取所有工作簿
            all_workbooks = self.file_manager.get_all_workbooks()
            if not all_workbooks:
                self.log("未能获取工作簿数据", "ERROR")
                return

            self.log(f"成功加载 {len(all_workbooks)} 个工作簿", "SUCCESS")

            # 设置到WorkbookManager
            for wb_name, wb_data in all_workbooks.items():
                self.workbook_manager.add_workbook(wb_name, wb_data["workbook"])

            # 分类工作表
            self.classify_sheets()

            # 提取数据
            self.extract_data()

            # 设置模型
            self.setup_model()

        except Exception as e:
            self.log(f"加载文件时发生错误: {e}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")

    def classify_sheets(self):
        """分类工作表"""
        try:
            for wb_name, wb_data in self.file_manager.get_all_workbooks().items():
                workbook = wb_data["workbook"]
                for sheet_name in workbook.sheetnames:
                    # 判断是否为快报表
                    if "快报" in sheet_name:
                        self.workbook_manager.set_sheet_type(
                            wb_name, sheet_name, "flash_report"
                        )
                        self.log(f"识别快报表: {sheet_name}")
                    else:
                        self.workbook_manager.set_sheet_type(
                            wb_name, sheet_name, "data_source"
                        )

        except Exception as e:
            self.log(f"分类工作表时出错: {e}", "ERROR")

    def extract_data(self):
        """提取数据"""
        try:
            all_workbooks = self.file_manager.get_all_workbooks()

            for wb_name, wb_data in all_workbooks.items():
                workbook = wb_data["workbook"]

                for sheet_name in workbook.sheetnames:
                    sheet = workbook[sheet_name]
                    sheet_type = self.workbook_manager.get_sheet_type(wb_name, sheet_name)

                    if sheet_type == "flash_report":
                        # 提取目标项
                        items = self.data_extractor.extract_target_items(
                            sheet, wb_name, sheet_name
                        )
                        for item in items:
                            self.workbook_manager.add_target_item(item)

        except Exception as e:
            self.log(f"提取数据时出错: {e}", "ERROR")

    def setup_model(self):
        """设置数据模型"""
        try:
            # 获取所有快报表
            flash_sheets = []
            for sheet_id, sheet_type in self.workbook_manager.sheet_types.items():
                if sheet_type == "flash_report":
                    _, sheet_name = sheet_id.rsplit("::", 1)
                    flash_sheets.append(sheet_name)

            self.log(f"找到 {len(flash_sheets)} 个快报表")

            # 添加到下拉框
            self.sheet_combo.clear()
            self.sheet_combo.addItems(flash_sheets)

            # 创建简单的测试模型
            self.create_test_model()

        except Exception as e:
            self.log(f"设置模型时出错: {e}", "ERROR")

    def create_test_model(self):
        """创建测试模型"""
        model = QStandardItemModel()

        # 设置表头 - 模拟真实情况
        headers = ["状态", "级别", "行次", "项目名称", "映射公式", "预览值"]
        model.setHorizontalHeaderLabels(headers)

        # 添加headers属性，模拟TargetItemModel
        model.headers = headers

        # 添加测试数据
        for i in range(10):
            row = []
            row.append(QStandardItem("⭕"))
            row.append(QStandardItem(str(i % 3)))
            row.append(QStandardItem(str(i + 1)))
            row.append(QStandardItem(f"测试项目 {i+1}"))
            row.append(QStandardItem(f"[Sheet1]![A{i+1}]"))
            row.append(QStandardItem("0.00"))
            model.appendRow(row)

        self.main_table.setModel(model)
        self.log("已创建测试模型", "SUCCESS")

    def on_sheet_changed(self, sheet_name):
        """处理工作表切换"""
        if not sheet_name:
            return

        self.log(f"切换到工作表: {sheet_name}")

        # 检查是否是问题表格
        if "企业财务快报利润因素分析表" in sheet_name:
            self.log("⚠️ 检测到问题表格：企业财务快报利润因素分析表", "WARNING")

        # 模拟主程序的行为
        try:
            # 触发列宽调整
            self.schedule_main_table_resize(0)
        except Exception as e:
            self.log(f"切换工作表时触发错误: {e}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")

    def schedule_main_table_resize(self, delay_ms=0):
        """模拟主程序的列宽调整"""
        self.log(f"触发列宽调整，延迟: {delay_ms}ms")
        self.resize_call_count += 1

        try:
            if not hasattr(self, "_resize_timer"):
                self._resize_timer = QTimer(self)
                self._resize_timer.setSingleShot(True)
                self._resize_timer.timeout.connect(self.adjust_table_columns)

            self._resize_timer.start(max(0, delay_ms))

        except Exception as e:
            self.log(f"启动定时器失败: {e}", "ERROR")

    def adjust_table_columns(self):
        """调整表格列宽"""
        self.log("开始调整列宽...")

        try:
            header = self.main_table.horizontalHeader()
            model = self.main_table.model()

            if not header or not model:
                self.log("header或model为空", "WARNING")
                return

            # 检查headers属性
            if not hasattr(model, "headers"):
                self.log("⚠️ model缺少headers属性", "WARNING")
                # 尝试从headerData获取
                col_count = model.columnCount()
                self.log(f"列数: {col_count}")
                for i in range(col_count):
                    header_text = model.headerData(i, Qt.Horizontal, Qt.DisplayRole)
                    self.log(f"列{i}: {header_text}")
            else:
                self.log(f"✅ model.headers存在: {model.headers}", "SUCCESS")

                # 测试索引访问
                for i in range(model.columnCount()):
                    try:
                        if i < len(model.headers):
                            col_name = model.headers[i]
                            self.log(f"列{i}: {col_name}")
                        else:
                            self.log(f"⚠️ 列{i}超出headers范围", "WARNING")
                    except Exception as e:
                        self.log(f"访问headers[{i}]时出错: {e}", "ERROR")

            # 执行列宽调整
            self._main_auto_resizing = True
            for column in range(model.columnCount()):
                try:
                    self.main_table.resizeColumnToContents(column)
                    width = self.main_table.columnWidth(column)
                    self.log(f"列{column}宽度: {width}px")
                except Exception as e:
                    self.log(f"调整列{column}宽度时出错: {e}", "ERROR")

            self._main_auto_resizing = False
            self.log("列宽调整完成", "SUCCESS")

        except Exception as e:
            self.log(f"调整列宽时发生错误: {e}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")


def main():
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()