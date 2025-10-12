#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel 公式导出对话框
提供用户友好的导出配置界面
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QFileDialog, QGroupBox, QRadioButton, QButtonGroup,
    QTextEdit, QDialogButtonBox, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from models.data_models import WorkbookManager
from modules.excel_exporter import ExportOptions


class ExportDialog(QDialog):
    """Excel 公式导出配置对话框"""

    # 信号：用户确认导出，传递配置信息
    export_requested = Signal(dict)  # {'output_path': str, 'options': ExportOptions, 'target_sheet': str}

    def __init__(self, workbook_manager: WorkbookManager, parent=None):
        """
        初始化导出对话框

        Args:
            workbook_manager: 工作簿管理器
            parent: 父窗口
        """
        super().__init__(parent)
        self.workbook_manager = workbook_manager
        self.config_path = Path(__file__).parent.parent / "config" / "export_settings.json"

        # 加载配置
        self.settings = self._load_settings()

        self._init_ui()
        self._load_defaults()
        self._connect_signals()

        # 设置窗口属性
        self.setWindowTitle("导出公式到 Excel")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

    def _init_ui(self):
        """初始化UI布局"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("导出 Excel 公式")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 基本配置区
        layout.addWidget(self._create_basic_config_group())

        # 输出路径
        layout.addWidget(self._create_output_path_group())

        # 导出选项
        layout.addWidget(self._create_export_options_group())

        # 按钮区
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.preview_button = QPushButton("预览公式")
        self.preview_button.setToolTip("查看前10条公式的转换预览")
        button_layout.addWidget(self.preview_button)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.button(QDialogButtonBox.Ok).setText("导出")
        self.button_box.button(QDialogButtonBox.Cancel).setText("取消")
        button_layout.addWidget(self.button_box)

        layout.addLayout(button_layout)

    def _create_basic_config_group(self) -> QGroupBox:
        """创建基本配置分组"""
        group = QGroupBox("基本配置")
        layout = QFormLayout()

        # 工作簿选择（当前仅支持单工作簿）
        self.workbook_label = QLabel(os.path.basename(self.workbook_manager.file_path))
        self.workbook_label.setToolTip(self.workbook_manager.file_path)
        layout.addRow("源工作簿:", self.workbook_label)

        # 目标工作表选择
        self.sheet_combo = QComboBox()
        self.sheet_combo.addItems(self.workbook_manager.get_sheet_names())
        self.sheet_combo.setToolTip("选择要填充公式的目标工作表")
        layout.addRow("目标工作表:", self.sheet_combo)

        group.setLayout(layout)
        return group

    def _create_output_path_group(self) -> QGroupBox:
        """创建输出路径配置分组"""
        group = QGroupBox("输出文件")
        layout = QHBoxLayout()

        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择导出文件路径...")
        layout.addWidget(self.output_path_edit)

        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self._browse_output_path)
        layout.addWidget(browse_button)

        group.setLayout(layout)
        return group

    def _create_export_options_group(self) -> QGroupBox:
        """创建导出选项配置分组"""
        group = QGroupBox("导出选项")
        layout = QVBoxLayout()

        # 基础选项
        self.include_metadata_checkbox = QCheckBox("包含元数据表")
        self.include_metadata_checkbox.setToolTip(
            "在导出文件中添加 '_Export_Metadata' 工作表，记录导出统计信息"
        )
        self.include_metadata_checkbox.setChecked(True)
        layout.addWidget(self.include_metadata_checkbox)

        self.preserve_values_checkbox = QCheckBox("错误时保留原始值")
        self.preserve_values_checkbox.setToolTip(
            "当公式转换失败时，使用计算好的数值填充单元格，而不是留空"
        )
        self.preserve_values_checkbox.setChecked(True)
        layout.addWidget(self.preserve_values_checkbox)

        self.auto_validate_checkbox = QCheckBox("导出后自动验证")
        self.auto_validate_checkbox.setToolTip(
            "导出完成后自动验证公式的正确性（需要打开 Excel 文件计算）"
        )
        self.auto_validate_checkbox.setChecked(False)
        layout.addWidget(self.auto_validate_checkbox)

        self.add_comments_checkbox = QCheckBox("添加公式注释")
        self.add_comments_checkbox.setToolTip(
            "在包含公式的单元格中添加注释，显示原始值和生成信息"
        )
        self.add_comments_checkbox.setChecked(False)
        layout.addWidget(self.add_comments_checkbox)

        # 错误处理模式
        error_group = QGroupBox("错误处理模式")
        error_layout = QVBoxLayout()

        self.error_button_group = QButtonGroup()

        self.error_preserve_radio = QRadioButton("保留值（推荐）")
        self.error_preserve_radio.setToolTip("失败的公式使用计算值填充")
        self.error_preserve_radio.setChecked(True)
        self.error_button_group.addButton(self.error_preserve_radio, 0)
        error_layout.addWidget(self.error_preserve_radio)

        self.error_skip_radio = QRadioButton("跳过失败项")
        self.error_skip_radio.setToolTip("失败的公式留空不填充")
        self.error_button_group.addButton(self.error_skip_radio, 1)
        error_layout.addWidget(self.error_skip_radio)

        self.error_fail_radio = QRadioButton("遇错终止")
        self.error_fail_radio.setToolTip("遇到转换错误时停止整个导出")
        self.error_button_group.addButton(self.error_fail_radio, 2)
        error_layout.addWidget(self.error_fail_radio)

        error_group.setLayout(error_layout)
        layout.addWidget(error_group)

        # 路径模式
        path_group = QGroupBox("引用路径")
        path_layout = QVBoxLayout()

        self.use_absolute_path_checkbox = QCheckBox("使用绝对路径")
        self.use_absolute_path_checkbox.setToolTip(
            "使用绝对路径引用源文件（推荐），取消勾选则使用相对路径"
        )
        self.use_absolute_path_checkbox.setChecked(True)
        path_layout.addWidget(self.use_absolute_path_checkbox)

        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        group.setLayout(layout)
        return group

    def _browse_output_path(self):
        """浏览输出文件路径"""
        default_dir = os.path.dirname(self.workbook_manager.file_path)
        default_name = os.path.splitext(os.path.basename(self.workbook_manager.file_path))[0]
        default_name += "_formulas.xlsx"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择导出文件路径",
            os.path.join(default_dir, default_name),
            "Excel Files (*.xlsx)"
        )

        if file_path:
            self.output_path_edit.setText(file_path)

    def _connect_signals(self):
        """连接信号与槽"""
        self.button_box.accepted.connect(self._on_export_clicked)
        self.button_box.rejected.connect(self.reject)
        self.preview_button.clicked.connect(self._show_formula_preview)

    def _on_export_clicked(self):
        """处理导出按钮点击"""
        # 验证输入
        output_path = self.output_path_edit.text().strip()
        if not output_path:
            QMessageBox.warning(
                self,
                "输入错误",
                "请选择输出文件路径"
            )
            return

        target_sheet = self.sheet_combo.currentText()
        if not target_sheet:
            QMessageBox.warning(
                self,
                "输入错误",
                "请选择目标工作表"
            )
            return

        # 构建导出配置
        options = self._get_export_options()

        # 保存配置
        self._save_settings()

        # 发送导出请求信号
        export_config = {
            'output_path': output_path,
            'target_sheet': target_sheet,
            'options': options
        }

        self.export_requested.emit(export_config)
        self.accept()

    def _get_export_options(self) -> ExportOptions:
        """获取当前的导出选项配置"""
        # 确定错误处理模式
        error_mode = "preserve"
        if self.error_skip_radio.isChecked():
            error_mode = "skip"
        elif self.error_fail_radio.isChecked():
            error_mode = "fail"

        return ExportOptions(
            include_metadata_sheet=self.include_metadata_checkbox.isChecked(),
            preserve_values_on_error=self.preserve_values_checkbox.isChecked(),
            auto_validate=self.auto_validate_checkbox.isChecked(),
            error_handling_mode=error_mode,
            use_absolute_path=self.use_absolute_path_checkbox.isChecked(),
            add_formula_comments=self.add_comments_checkbox.isChecked()
        )

    def _show_formula_preview(self):
        """显示公式转换预览对话框"""
        from modules.formula_converter import FormulaConverter

        converter = FormulaConverter(self.workbook_manager)
        target_sheet = self.sheet_combo.currentText()

        # 收集目标工作表的前10个公式
        preview_formulas = []
        count = 0

        for target_id, mapping in self.workbook_manager.mapping_formulas.items():
            target_item = self.workbook_manager.target_items.get(target_id)
            if target_item and target_item.sheet_name == target_sheet:
                internal_formula = mapping.formula if hasattr(mapping, 'formula') else str(mapping)

                excel_formula, references, errors = converter.convert_formula(
                    internal_formula, target_item
                )

                preview_formulas.append({
                    'target_name': target_item.name,
                    'internal_formula': internal_formula,
                    'excel_formula': excel_formula,
                    'has_error': len(errors) > 0,
                    'error_msg': errors[0].error_message if errors else ""
                })

                count += 1
                if count >= 10:
                    break

        # 显示预览对话框
        dialog = FormulaPreviewDialog(preview_formulas, self)
        dialog.exec()

    def _load_settings(self) -> Dict[str, Any]:
        """从配置文件加载设置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载导出配置失败: {e}")

        # 默认配置
        return {
            'include_metadata_sheet': True,
            'preserve_values_on_error': True,
            'auto_validate': False,
            'error_handling_mode': 'preserve',
            'use_absolute_path': True,
            'add_formula_comments': False
        }

    def _save_settings(self):
        """保存当前设置到配置文件"""
        try:
            # 确保配置目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存配置
            settings = {
                'include_metadata_sheet': self.include_metadata_checkbox.isChecked(),
                'preserve_values_on_error': self.preserve_values_checkbox.isChecked(),
                'auto_validate': self.auto_validate_checkbox.isChecked(),
                'error_handling_mode': 'preserve' if self.error_preserve_radio.isChecked()
                                      else 'skip' if self.error_skip_radio.isChecked()
                                      else 'fail',
                'use_absolute_path': self.use_absolute_path_checkbox.isChecked(),
                'add_formula_comments': self.add_comments_checkbox.isChecked()
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"保存导出配置失败: {e}")

    def _load_defaults(self):
        """加载默认值到UI"""
        self.include_metadata_checkbox.setChecked(
            self.settings.get('include_metadata_sheet', True)
        )
        self.preserve_values_checkbox.setChecked(
            self.settings.get('preserve_values_on_error', True)
        )
        self.auto_validate_checkbox.setChecked(
            self.settings.get('auto_validate', False)
        )
        self.use_absolute_path_checkbox.setChecked(
            self.settings.get('use_absolute_path', True)
        )
        self.add_comments_checkbox.setChecked(
            self.settings.get('add_formula_comments', False)
        )

        # 错误处理模式
        error_mode = self.settings.get('error_handling_mode', 'preserve')
        if error_mode == 'skip':
            self.error_skip_radio.setChecked(True)
        elif error_mode == 'fail':
            self.error_fail_radio.setChecked(True)
        else:
            self.error_preserve_radio.setChecked(True)


class FormulaPreviewDialog(QDialog):
    """公式预览对话框"""

    def __init__(self, formulas: list, parent=None):
        """
        初始化预览对话框

        Args:
            formulas: 公式预览数据列表
            parent: 父窗口
        """
        super().__init__(parent)
        self.formulas = formulas

        self.setWindowTitle("公式转换预览")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 提示信息
        info_label = QLabel(f"显示前 {len(self.formulas)} 条公式的转换预览")
        layout.addWidget(info_label)

        # 创建表格
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["目标项", "内部公式", "Excel 公式", "状态"])
        table.setRowCount(len(self.formulas))

        # 设置列宽
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        # 填充数据
        for row, formula_data in enumerate(self.formulas):
            # 目标项名称
            name_item = QTableWidgetItem(formula_data['target_name'])
            table.setItem(row, 0, name_item)

            # 内部公式
            internal_item = QTableWidgetItem(formula_data['internal_formula'])
            table.setItem(row, 1, internal_item)

            # Excel 公式
            excel_item = QTableWidgetItem(formula_data['excel_formula'])
            table.setItem(row, 2, excel_item)

            # 状态
            if formula_data['has_error']:
                status_item = QTableWidgetItem("✗ 错误")
                status_item.setToolTip(formula_data['error_msg'])
            else:
                status_item = QTableWidgetItem("✓ 就绪")

            table.setItem(row, 3, status_item)

        layout.addWidget(table)

        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
