#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作表浏览器模型 - 树状结构显示工作表分类
"""

from typing import Dict, List, Optional, Any
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QWidget, QMessageBox
)

from models.data_models import WorkbookManager, SheetType


class SheetExplorerItem:
    """工作表浏览器项目"""

    def __init__(self, name: str, sheet_type: Optional[SheetType] = None, parent=None):
        self.name = name
        self.sheet_type = sheet_type  # None表示分组节点
        self.parent_item = parent
        self.child_items = []

        if parent:
            parent.child_items.append(self)

    def child(self, row: int):
        if 0 <= row < len(self.child_items):
            return self.child_items[row]
        return None

    def child_count(self) -> int:
        return len(self.child_items)

    def column_count(self) -> int:
        return 1

    def row(self) -> int:
        if self.parent_item:
            return self.parent_item.child_items.index(self)
        return 0

    def parent(self):
        return self.parent_item

    def is_sheet_group(self) -> bool:
        """是否为工作表分组（快报表或数据来源表）"""
        return self.sheet_type is None

    def is_flash_report(self) -> bool:
        """是否为快报表"""
        return self.sheet_type == SheetType.FLASH_REPORT

    def is_data_source(self) -> bool:
        """是否为数据来源表"""
        return self.sheet_type == SheetType.DATA_SOURCE


class SheetExplorerModel(QAbstractItemModel):
    """工作表浏览器模型"""

    # 信号：工作表选择变化
    sheetSelected = Signal(str, SheetType)  # (sheet_name, sheet_type)
    flashReportActivated = Signal(str)  # (sheet_name) - 激活快报表

    def __init__(self, workbook_manager: Optional[WorkbookManager] = None):
        super().__init__()
        self.workbook_manager = workbook_manager
        self.root_item = SheetExplorerItem("Root")
        self.flash_report_group = None
        self.data_source_group = None
        self.build_tree()

    def set_workbook_manager(self, workbook_manager: WorkbookManager):
        """设置工作簿管理器并重建树"""
        self.beginResetModel()
        self.workbook_manager = workbook_manager
        self.build_tree()
        self.endResetModel()

    def build_tree(self):
        """构建工作表树状结构"""
        # 清空现有结构
        self.root_item.child_items.clear()

        if not self.workbook_manager:
            return

        # 创建分组节点
        self.flash_report_group = SheetExplorerItem("[快报表]", parent=self.root_item)
        self.data_source_group = SheetExplorerItem("[数据来源表]", parent=self.root_item)

        # 添加快报表
        for sheet_item in self.workbook_manager.flash_report_sheets:
            sheet_name = self._safe_get_sheet_name(sheet_item)
            SheetExplorerItem(sheet_name, SheetType.FLASH_REPORT, self.flash_report_group)

        # 添加数据来源表
        for sheet_item in self.workbook_manager.data_source_sheets:
            sheet_name = self._safe_get_sheet_name(sheet_item)
            SheetExplorerItem(sheet_name, SheetType.DATA_SOURCE, self.data_source_group)

    def _safe_get_sheet_name(self, sheet_item):
        """安全获取工作表名称"""
        if isinstance(sheet_item, str):
            return sheet_item
        elif hasattr(sheet_item, 'name'):
            return str(sheet_item.name)
        else:
            return str(sheet_item)

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)

        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root_item or parent_item is None:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        return parent_item.child_count()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.DisplayRole:
            return item.name

        elif role == Qt.DecorationRole:
            if item.is_sheet_group():
                return None  # 分组已经有emoji图标
            elif item.is_flash_report():
                return "📈"  # 快报表图标
            elif item.is_data_source():
                return "[表]"  # 数据表图标

        elif role == Qt.FontRole:
            if item.is_sheet_group():
                font = QFont()
                font.setBold(True)
                return font

        elif role == Qt.ToolTipRole:
            if item.is_sheet_group():
                if "快报表" in item.name:
                    count = len(self.workbook_manager.flash_report_sheets) if self.workbook_manager else 0
                    return f"包含 {count} 个快报表"
                else:
                    count = len(self.workbook_manager.data_source_sheets) if self.workbook_manager else 0
                    return f"包含 {count} 个数据来源表"
            else:
                return f"工作表: {item.name}\n类型: {'快报表' if item.is_flash_report() else '数据来源表'}"

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 0:
            return "工作表结构"
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags

        item = index.internalPointer()

        if item.is_sheet_group():
            return Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def get_sheet_info(self, index: QModelIndex):
        """获取工作表信息"""
        if not index.isValid():
            return None, None

        item = index.internalPointer()
        if item.is_sheet_group():
            return None, None

        return item.name, item.sheet_type

    def handle_item_clicked(self, index: QModelIndex):
        """处理项目点击"""
        sheet_name, sheet_type = self.get_sheet_info(index)

        if sheet_name and sheet_type:
            # 发送工作表选择信号
            self.sheetSelected.emit(sheet_name, sheet_type)

            # 如果是快报表，发送激活信号
            if sheet_type == SheetType.FLASH_REPORT:
                self.flashReportActivated.emit(sheet_name)


class SheetClassificationDialog(QDialog):
    """工作表分类审核对话框"""

    # 信号：分类更改
    classificationChanged = Signal(str, SheetType)  # (sheet_name, new_type)

    def __init__(self, workbook_manager: WorkbookManager, parent=None):
        super().__init__(parent)
        self.workbook_manager = workbook_manager
        self.classification_changes = {}  # 记录更改
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("工作表分类审核")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # 说明标签
        info_label = QLabel("🔍 请审核AI自动分类结果，可手动调整工作表类型：")
        info_label.setStyleSheet("font-weight: bold; margin: 10px 0;")
        layout.addWidget(info_label)

        # 分类表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["工作表名", "当前分类", "建议分类", "操作"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # 填充表格数据
        self.populate_table()
        layout.addWidget(self.table)

        # 统计信息
        self.stats_label = QLabel()
        self.update_stats()
        layout.addWidget(self.stats_label)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.auto_classify_btn = QPushButton("🤖 重新AI分类")
        self.auto_classify_btn.clicked.connect(self.auto_classify)
        button_layout.addWidget(self.auto_classify_btn)

        button_layout.addStretch()

        self.apply_btn = QPushButton("✅ 应用更改")
        self.apply_btn.clicked.connect(self.apply_changes)
        button_layout.addWidget(self.apply_btn)

        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def populate_table(self):
        """填充表格数据"""
        if not self.workbook_manager or not self.workbook_manager.workbook:
            return

        sheet_names = self.workbook_manager.workbook.sheetnames
        self.table.setRowCount(len(sheet_names))

        for row, sheet_name in enumerate(sheet_names):
            # 工作表名
            name_item = QTableWidgetItem(sheet_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            # 当前分类
            current_type = self.get_current_classification(sheet_name)
            current_item = QTableWidgetItem(self.type_to_text(current_type))
            current_item.setFlags(current_item.flags() & ~Qt.ItemIsEditable)
            if current_type == SheetType.FLASH_REPORT:
                current_item.setBackground(QColor(230, 255, 230))  # 浅绿
            elif current_type == SheetType.DATA_SOURCE:
                current_item.setBackground(QColor(230, 230, 255))  # 浅蓝
            else:
                current_item.setBackground(QColor(255, 240, 230))  # 浅橙
            self.table.setItem(row, 1, current_item)

            # 建议分类
            suggested_type = self.suggest_classification(sheet_name)
            suggested_item = QTableWidgetItem(self.type_to_text(suggested_type))
            suggested_item.setFlags(suggested_item.flags() & ~Qt.ItemIsEditable)
            if suggested_type != current_type:
                suggested_item.setBackground(QColor(255, 255, 200))  # 高亮建议
            self.table.setItem(row, 2, suggested_item)

            # 操作按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)

            # 分类下拉框
            type_combo = QComboBox()
            type_combo.addItems(["[快报表]", "[数据来源表]", "[未分类]"])
            type_combo.setCurrentText(self.type_to_text(current_type))
            type_combo.currentTextChanged.connect(
                lambda text, sheet=sheet_name: self.on_classification_changed(sheet, text)
            )
            button_layout.addWidget(type_combo)

            # 重置按钮
            reset_btn = QPushButton("🔄")
            reset_btn.setMaximumWidth(30)
            reset_btn.setToolTip("重置为原始分类")
            reset_btn.clicked.connect(
                lambda checked, sheet=sheet_name: self.reset_classification(sheet)
            )
            button_layout.addWidget(reset_btn)

            self.table.setCellWidget(row, 3, button_widget)

        # 调整列宽
        self.table.resizeColumnsToContents()

    def get_current_classification(self, sheet_name: str) -> SheetType:
        """获取当前分类"""
        if sheet_name in self.workbook_manager.flash_report_sheets:
            return SheetType.FLASH_REPORT
        elif sheet_name in self.workbook_manager.data_source_sheets:
            return SheetType.DATA_SOURCE
        else:
            return SheetType.UNKNOWN

    def suggest_classification(self, sheet_name: str) -> SheetType:
        """AI建议分类（简化版规则）"""
        name_lower = sheet_name.lower()

        # 快报表关键词
        flash_keywords = ['快报', '报表', '汇总', '总表', '统计', 'summary', 'report']
        if any(keyword in name_lower for keyword in flash_keywords):
            return SheetType.FLASH_REPORT

        # 数据来源表关键词
        data_keywords = ['明细', '数据', '原始', '基础', 'data', 'detail', '台账']
        if any(keyword in name_lower for keyword in data_keywords):
            return SheetType.DATA_SOURCE

        # 默认为数据来源表
        return SheetType.DATA_SOURCE

    def type_to_text(self, sheet_type: SheetType) -> str:
        """类型转文本"""
        type_map = {
            SheetType.FLASH_REPORT: "[快报表]",
            SheetType.DATA_SOURCE: "[数据来源表]",
            SheetType.UNKNOWN: "[未分类]"
        }
        return type_map.get(sheet_type, "[未分类]")

    def text_to_type(self, text: str) -> SheetType:
        """文本转类型"""
        text_map = {
            "[快报表]": SheetType.FLASH_REPORT,
            "[数据来源表]": SheetType.DATA_SOURCE,
            "[未分类]": SheetType.UNKNOWN
        }
        return text_map.get(text, SheetType.UNKNOWN)

    def on_classification_changed(self, sheet_name: str, new_text: str):
        """分类更改处理"""
        new_type = self.text_to_type(new_text)
        old_type = self.get_current_classification(sheet_name)

        if new_type != old_type:
            self.classification_changes[sheet_name] = new_type
            self.apply_btn.setText(f"✅ 应用更改 ({len(self.classification_changes)})")
        elif sheet_name in self.classification_changes:
            del self.classification_changes[sheet_name]
            if not self.classification_changes:
                self.apply_btn.setText("✅ 应用更改")

        self.update_stats()

    def reset_classification(self, sheet_name: str):
        """重置分类"""
        if sheet_name in self.classification_changes:
            del self.classification_changes[sheet_name]

        # 重新设置下拉框
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == sheet_name:
                widget = self.table.cellWidget(row, 3)
                combo = widget.findChild(QComboBox)
                if combo:
                    original_type = self.get_current_classification(sheet_name)
                    combo.setCurrentText(self.type_to_text(original_type))
                break

        self.update_stats()

    def auto_classify(self):
        """自动分类"""
        reply = QMessageBox.question(
            self, "确认操作",
            "🤖 将使用AI规则重新分类所有工作表，是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 应用AI建议
            for row in range(self.table.rowCount()):
                sheet_name = self.table.item(row, 0).text()
                suggested_type = self.suggest_classification(sheet_name)

                widget = self.table.cellWidget(row, 3)
                combo = widget.findChild(QComboBox)
                if combo:
                    combo.setCurrentText(self.type_to_text(suggested_type))

    def update_stats(self):
        """更新统计信息"""
        total = self.table.rowCount()
        changes = len(self.classification_changes)

        flash_count = 0
        data_count = 0
        unknown_count = 0

        for row in range(total):
            sheet_name = self.table.item(row, 0).text()
            if sheet_name in self.classification_changes:
                sheet_type = self.classification_changes[sheet_name]
            else:
                sheet_type = self.get_current_classification(sheet_name)

            if sheet_type == SheetType.FLASH_REPORT:
                flash_count += 1
            elif sheet_type == SheetType.DATA_SOURCE:
                data_count += 1
            else:
                unknown_count += 1

        stats_text = f"[快报表]: {flash_count} | [数据来源表]: {data_count} | [未分类]: {unknown_count}"
        if changes > 0:
            stats_text += f" | 🔄 待应用更改: {changes}"

        self.stats_label.setText(stats_text)

    def apply_changes(self):
        """应用更改"""
        if not self.classification_changes:
            self.accept()
            return

        # 应用分类更改
        for sheet_name, new_type in self.classification_changes.items():
            # 从原有分类中移除
            if sheet_name in self.workbook_manager.flash_report_sheets:
                self.workbook_manager.flash_report_sheets.remove(sheet_name)
            if sheet_name in self.workbook_manager.data_source_sheets:
                self.workbook_manager.data_source_sheets.remove(sheet_name)

            # 添加到新分类
            if new_type == SheetType.FLASH_REPORT:
                self.workbook_manager.flash_report_sheets.append(sheet_name)
            elif new_type == SheetType.DATA_SOURCE:
                self.workbook_manager.data_source_sheets.append(sheet_name)

            # 发送信号
            self.classificationChanged.emit(sheet_name, new_type)

        QMessageBox.information(
            self, "操作完成",
            f"✅ 已成功应用 {len(self.classification_changes)} 项分类更改"
        )

        self.accept()


# 在components/advanced_widgets.py中添加相关组件