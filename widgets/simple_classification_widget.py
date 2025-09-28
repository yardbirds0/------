#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的工作表分类界面 - 修复拖拽和字体问题
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


class SimpleDragDropListWidget(QListWidget):
    """简化的拖拽列表控件"""

    itemMoved = Signal(str, str, str)  # item_name, from_category, to_category

    def __init__(self, category_name: str):
        super().__init__()
        self.category_name = category_name

        # 基础拖拽设置
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

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
                padding: 8px;
                margin: 2px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background: white;
                color: #333;
                font-size: 12px;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
                border: 1px solid #2196F3;
            }
            QListWidget::item:hover {
                background: #f5f5f5;
                border: 1px solid #bbb;
            }
        """)

    def add_sheet_item(self, sheet_name: str):
        """添加工作表项目"""
        icon = self.get_icon_for_category()
        item_text = f"{icon} {sheet_name}"

        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, sheet_name)  # 存储原始名称
        item.setData(Qt.UserRole + 1, self.category_name)  # 存储分类
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        self.addItem(item)

    def get_icon_for_category(self) -> str:
        """根据分类获取图标"""
        if self.category_name == "flash_reports":
            return "[快报]"
        elif self.category_name == "data_sources":
            return "[数据]"
        else:  # cancelled
            return "[取消]"

    def remove_sheet_item(self, sheet_name: str):
        """移除指定的工作表项目"""
        for i in range(self.count()):
            item = self.item(i)
            if item and item.data(Qt.UserRole) == sheet_name:
                self.takeItem(i)
                break

    def get_sheet_names(self) -> List[str]:
        """获取当前列表中的所有工作表名称"""
        names = []
        for i in range(self.count()):
            item = self.item(i)
            if item:
                sheet_name = item.data(Qt.UserRole)
                if sheet_name:
                    names.append(sheet_name)
        return names

    def mimeTypes(self):
        """支持的MIME类型"""
        return ['text/plain']

    def mimeData(self, items):
        """创建拖拽数据"""
        mimeData = QMimeData()
        if items:
            item = items[0]
            sheet_name = item.data(Qt.UserRole)
            category = item.data(Qt.UserRole + 1)
            data = f"{sheet_name}|{category}"
            mimeData.setText(data)
        return mimeData

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasText():
            # 高亮显示
            self.setStyleSheet(self.styleSheet().replace(
                "border: 2px dashed #ccc",
                "border: 2px solid #4CAF50"
            ).replace(
                "background-color: #fafafa",
                "background-color: #e8f5e8"
            ))
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        # 恢复原样式
        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #ccc;
                border-radius: 5px;
                background-color: #fafafa;
                min-height: 200px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 8px;
                margin: 2px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background: white;
                color: #333;
                font-size: 12px;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
                border: 1px solid #2196F3;
            }
            QListWidget::item:hover {
                background: #f5f5f5;
                border: 1px solid #bbb;
            }
        """)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        """拖拽放置事件"""
        self.dragLeaveEvent(event)  # 恢复样式

        if event.mimeData().hasText():
            data = event.mimeData().text()
            parts = data.split('|')
            if len(parts) == 2:
                sheet_name, from_category = parts

                # 检查是否是跨列表拖拽
                if from_category != self.category_name:
                    # 添加到当前列表
                    self.add_sheet_item(sheet_name)
                    # 发射移动信号
                    self.itemMoved.emit(sheet_name, from_category, self.category_name)
                    event.acceptProposedAction()
                else:
                    # 同列表内重排，使用默认行为
                    super().dropEvent(event)
            else:
                event.ignore()
        else:
            event.ignore()

    def startDrag(self, supportedActions):
        """开始拖拽"""
        item = self.currentItem()
        if item:
            # 先移除当前项目（如果拖拽失败会在dropEvent中处理）
            sheet_name = item.data(Qt.UserRole)

            # 执行拖拽
            super().startDrag(supportedActions)