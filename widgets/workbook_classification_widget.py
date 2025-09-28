#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的工作表分类界面 - 支持按钮控制和拖拽
"""

import sys
import os
from typing import Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QGroupBox, QFrame, QSplitter, QTextEdit, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QMimeData, QSize
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDrag, QPixmap, QPainter, QFont, QColor


class SheetItemWidget(QWidget):
    """工作表项目控件 - 包含名称和控制按钮"""

    moveRequested = Signal(str, str, str)  # sheet_name, from_category, to_category
    removeRequested = Signal(str, str)     # sheet_name, category

    def __init__(self, sheet_name: str, category: str, parent=None):
        super().__init__(parent)
        self.sheet_name = sheet_name
        self.category = category
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        # 图标和名称 - 简化样式避免重影
        icon = self.get_icon_for_category()
        name_label = QLabel(f"{icon} {self.sheet_name}")
        name_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #000;
                background: transparent;
            }
        """)
        layout.addWidget(name_label, 1)  # 占据剩余空间

        # 控制按钮
        self.add_control_buttons(layout)

        # 设置样式
        self.setStyleSheet("""
            SheetItemWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 3px;
                margin: 1px;
            }
            SheetItemWidget:hover {
                background-color: #f5f5f5;
                border: 1px solid #bbb;
            }
        """)

    def get_icon_for_category(self) -> str:
        """根据分类获取图标 - 修复emoji显示问题"""
        if self.category == "flash_reports":
            return "[快报]"
        elif self.category == "data_sources":
            return "[数据]"
        else:  # cancelled
            return "[取消]"

    def add_control_buttons(self, layout):
        """添加控制按钮"""
        # 根据分类添加不同的方向按钮
        if self.category == "flash_reports":
            # 快报表列：只有右箭头
            right_btn = QPushButton("→")
            right_btn.setFixedSize(25, 25)
            right_btn.setToolTip("移至数据来源表")
            right_btn.clicked.connect(lambda: self.moveRequested.emit(
                self.sheet_name, self.category, "data_sources"))
            layout.addWidget(right_btn)

        elif self.category == "data_sources":
            # 数据来源表列：左箭头+右箭头
            left_btn = QPushButton("←")
            left_btn.setFixedSize(25, 25)
            left_btn.setToolTip("移至快报表")
            left_btn.clicked.connect(lambda: self.moveRequested.emit(
                self.sheet_name, self.category, "flash_reports"))
            layout.addWidget(left_btn)

            right_btn = QPushButton("→")
            right_btn.setFixedSize(25, 25)
            right_btn.setToolTip("移至已取消")
            right_btn.clicked.connect(lambda: self.moveRequested.emit(
                self.sheet_name, self.category, "cancelled"))
            layout.addWidget(right_btn)

        elif self.category == "cancelled":
            # 已取消列：只有左箭头
            left_btn = QPushButton("←")
            left_btn.setFixedSize(25, 25)
            left_btn.setToolTip("移至数据来源表")
            left_btn.clicked.connect(lambda: self.moveRequested.emit(
                self.sheet_name, self.category, "data_sources"))
            layout.addWidget(left_btn)

        # X按钮（除了已取消列）
        if self.category != "cancelled":
            remove_btn = QPushButton("×")
            remove_btn.setFixedSize(25, 25)
            remove_btn.setToolTip("移至已取消")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff4444;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #cc0000;
                }
            """)
            remove_btn.clicked.connect(lambda: self.moveRequested.emit(
                self.sheet_name, self.category, "cancelled"))
            layout.addWidget(remove_btn)


class DragDropListWidget(QListWidget):
    """支持拖拽的列表控件 - 简化版"""

    itemMoved = Signal(str, str, str)  # item_name, from_category, to_category

    def __init__(self, category_name: str):
        super().__init__()
        self.category_name = category_name

        # 拖拽设置 - 确保正确配置
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.SingleSelection)

        # 确保能够处理内部移动
        self.setDragDropOverwriteMode(False)

        # 设置样式
        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #ccc;
                border-radius: 5px;
                background-color: #fafafa;
                min-height: 200px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 0px;
                margin: 2px;
                border: none;
                background: transparent;
            }
            QListWidget::item:selected {
                background: transparent;
                border: none;
            }
        """)

    def add_sheet_item(self, sheet_name: str):
        """添加工作表项目"""
        item = QListWidgetItem()
        self.addItem(item)

        # 创建自定义widget
        widget = SheetItemWidget(sheet_name, self.category_name)
        widget.moveRequested.connect(self.on_move_requested)

        # 设置item属性以支持拖拽
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        item.setText(sheet_name)  # 设置文本，确保拖拽数据可用
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)

    def on_move_requested(self, sheet_name: str, from_category: str, to_category: str):
        """处理移动请求"""
        # 从当前列表移除项目
        self.remove_sheet_item(sheet_name)
        # 发射信号
        self.itemMoved.emit(sheet_name, from_category, to_category)

    def remove_sheet_item(self, sheet_name: str):
        """移除指定的工作表项目"""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget and widget.sheet_name == sheet_name:
                self.takeItem(i)
                break

    def get_sheet_names(self) -> List[str]:
        """获取当前列表中的所有工作表名称"""
        names = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget:
                names.append(widget.sheet_name)
        return names

    # 简化拖拽实现
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            self.setStyleSheet(self.styleSheet() + """
                QListWidget { border: 2px solid #4CAF50 !important; background-color: #e8f5e8 !important; }
            """)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #ccc;
                border-radius: 5px;
                background-color: #fafafa;
                min-height: 200px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 0px;
                margin: 2px;
                border: none;
                background: transparent;
            }
            QListWidget::item:selected {
                background: transparent;
                border: none;
            }
        """)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        """处理拖拽放置事件"""
        self.dragLeaveEvent(event)  # 恢复样式

        if event.mimeData().hasText():
            item_data = event.mimeData().text()
            parts = item_data.split('|')
            if len(parts) >= 2:
                sheet_name = parts[0]
                from_category = parts[1]

                if from_category != self.category_name:
                    # 添加项目到当前列表
                    self.add_sheet_item(sheet_name)
                    # 发射移动信号
                    self.itemMoved.emit(sheet_name, from_category, self.category_name)
                    event.acceptProposedAction()
                else:
                    event.ignore()
            else:
                event.ignore()
        else:
            event.ignore()

    def startDrag(self, supportedActions):
        """开始拖拽操作"""
        item = self.currentItem()
        if item is None:
            return

        widget = self.itemWidget(item)
        if widget is None:
            return

        drag = QDrag(self)
        mimeData = QMimeData()

        # 设置拖拽数据
        item_data = f"{widget.sheet_name}|{self.category_name}"
        mimeData.setText(item_data)
        drag.setMimeData(mimeData)

        # 创建拖拽预览图
        pixmap = QPixmap(200, 30)
        pixmap.fill(QColor(173, 216, 230, 180))
        painter = QPainter(pixmap)
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, widget.sheet_name)
        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())

        # 执行拖拽 - 修复PySide6兼容性
        dropAction = drag.exec(Qt.MoveAction)

        # 如果拖拽成功，移除项目
        if dropAction == Qt.MoveAction:
            self.remove_sheet_item(widget.sheet_name)


class WorkbookClassificationWidget(QWidget):
    """工作簿分类界面 - 改进版"""

    classificationChanged = Signal()
    confirmRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.workbook_manager = None
        self.setup_ui()

    def setup_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("工作表分类")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #333; margin: 10px 0;")
        layout.addWidget(title_label)

        # 说明文字
        instruction = QLabel("🔄 使用拖拽或按钮调整工作表分类，然后点击确认")
        instruction.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(instruction)

        # 统计信息
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #555; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.stats_label)

        # 创建三列布局
        lists_layout = QHBoxLayout()

        # 快报表列
        flash_group = QGroupBox("📊 快报表 (待填写数据)")
        flash_layout = QVBoxLayout(flash_group)
        self.flash_reports_list = DragDropListWidget("flash_reports")
        self.flash_reports_list.itemMoved.connect(self.on_item_moved)
        flash_layout.addWidget(self.flash_reports_list)
        lists_layout.addWidget(flash_group)

        # 数据来源表列
        data_group = QGroupBox("📋 数据来源表 (提供源数据)")
        data_layout = QVBoxLayout(data_group)
        self.data_sources_list = DragDropListWidget("data_sources")
        self.data_sources_list.itemMoved.connect(self.on_item_moved)
        data_layout.addWidget(self.data_sources_list)
        lists_layout.addWidget(data_group)

        # 已取消列
        cancelled_group = QGroupBox("❌ 已取消 (不处理)")
        cancelled_layout = QVBoxLayout(cancelled_group)
        self.cancelled_list = DragDropListWidget("cancelled")
        self.cancelled_list.itemMoved.connect(self.on_item_moved)
        cancelled_layout.addWidget(self.cancelled_list)
        lists_layout.addWidget(cancelled_group)

        layout.addLayout(lists_layout, 1)

        # 操作按钮
        buttons_layout = QHBoxLayout()

        reset_btn = QPushButton("🔄 重置分类")
        reset_btn.clicked.connect(self.reset_classification)
        buttons_layout.addWidget(reset_btn)

        buttons_layout.addStretch()

        confirm_btn = QPushButton("✅ 确认分类")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        confirm_btn.clicked.connect(self.confirm_classification)
        buttons_layout.addWidget(confirm_btn)

        layout.addLayout(buttons_layout)

        # 初始隐藏
        self.hide()

    def load_workbook(self, workbook_manager):
        """加载工作簿数据"""
        self.workbook_manager = workbook_manager

        # 清空现有列表
        self.flash_reports_list.clear()
        self.data_sources_list.clear()
        self.cancelled_list.clear()

        # 添加工作表 - 使用安全的获取名称方法
        for sheet in workbook_manager.flash_report_sheets:
            sheet_name = self._safe_get_sheet_name(sheet)
            self.flash_reports_list.add_sheet_item(sheet_name)

        for sheet in workbook_manager.data_source_sheets:
            sheet_name = self._safe_get_sheet_name(sheet)
            self.data_sources_list.add_sheet_item(sheet_name)

        # 更新统计
        self.update_stats()
        self.show()

    def _safe_get_sheet_name(self, sheet_item):
        """安全获取工作表名称"""
        if isinstance(sheet_item, str):
            return sheet_item
        elif hasattr(sheet_item, 'name'):
            return str(sheet_item.name)
        else:
            return str(sheet_item)

    def on_item_moved(self, sheet_name: str, from_category: str, to_category: str):
        """处理项目移动"""
        # 添加到目标列表
        if to_category == "flash_reports":
            self.flash_reports_list.add_sheet_item(sheet_name)
        elif to_category == "data_sources":
            self.data_sources_list.add_sheet_item(sheet_name)
        elif to_category == "cancelled":
            self.cancelled_list.add_sheet_item(sheet_name)

        self.update_stats()
        self.classificationChanged.emit()

    def update_stats(self):
        """更新统计信息"""
        flash_count = self.flash_reports_list.count()
        data_count = self.data_sources_list.count()
        cancelled_count = self.cancelled_list.count()
        total_count = flash_count + data_count + cancelled_count

        stats_text = (
            f"共 {total_count} 个工作表 | "
            f"快报表: {flash_count} 个，数据来源表: {data_count} 个，已取消: {cancelled_count} 个"
        )
        self.stats_label.setText(stats_text)

    def reset_classification(self):
        """重置为系统自动分类"""
        if self.workbook_manager:
            self.load_workbook(self.workbook_manager)

    def confirm_classification(self):
        """确认分类"""
        self.confirmRequested.emit()

    def get_final_classifications(self) -> Dict[str, List[str]]:
        """获取最终分类结果"""
        return {
            'flash_reports': self.flash_reports_list.get_sheet_names(),
            'data_sources': self.data_sources_list.get_sheet_names(),
            'cancelled': self.cancelled_list.get_sheet_names()
        }

    def hide_classification_ui(self):
        """隐藏分类界面"""
        self.hide()