#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美化的工作表分类组件 - 带checkbox和箭头按钮
"""

import sys
import os
from typing import Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QGroupBox, QFrame, QCheckBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QMimeData, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDrag, QPixmap, QPainter, QFont, QColor, QLinearGradient, QPalette


class SimpleDotCheckBox(QCheckBox):
    """简单的圆点复选框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)

        # 简单的圆点样式 - 红色轮廓线/绿色填充
        self.setStyleSheet("""
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 7px;
                border: 3px solid #dc3545;
                background: transparent;
            }
            QCheckBox::indicator:checked {
                border: 3px solid #28a745;
                background: #28a745;
            }
        """)


class BeautifulSheetItem(QWidget):
    """美化的工作表项目组件"""

    toggled = Signal(str, bool)  # sheet_name, is_checked

    def __init__(self, sheet_name: str, category: str, parent=None):
        super().__init__(parent)
        self.sheet_name = sheet_name
        self.category = category
        self.setup_ui()

    def setup_ui(self):
        """设置美化的界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(4)  # 减少间距

        # 使用简单的圆点checkbox
        self.checkbox = SimpleDotCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.toggled.connect(lambda checked: self.toggled.emit(self.sheet_name, checked))
        layout.addWidget(self.checkbox)

        # 分类图标 - 紧凑设计
        icon = self.get_category_icon()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #666;
                margin: 0px;
                padding: 0px 3px;
            }
        """)
        icon_label.setFixedWidth(30)  # 大幅减少宽度
        layout.addWidget(icon_label)

        # 工作表名称 - 紧贴图标
        name_label = QLabel(self.sheet_name)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #333;
                font-weight: 500;
                margin: 0px;
                padding: 2px 4px;
                background: transparent;
            }
        """)
        layout.addWidget(name_label, 1)

        # 整体样式 - 更紧凑
        self.setStyleSheet("""
            BeautifulSheetItem {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 1px solid #e9ecef;
                border-radius: 4px;
                margin: 1px;
            }
            BeautifulSheetItem:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 1px solid #dee2e6;
            }
        """)

        # 添加轻微阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 1)
        self.setGraphicsEffect(shadow)

    def get_category_icon(self) -> str:
        """获取分类图标 - 更简洁"""
        if self.category == "flash_reports":
            return "📊"
        else:
            return "📋"

    def is_checked(self) -> bool:
        """获取勾选状态"""
        return self.checkbox.isChecked()

    def set_checked(self, checked: bool):
        """设置勾选状态"""
        self.checkbox.setChecked(checked)


class BeautifulDragDropList(QListWidget):
    """美化的拖拽列表"""

    itemMoved = Signal(str, str, str)  # item_name, from_category, to_category
    itemToggled = Signal(str, bool)    # item_name, is_checked

    def __init__(self, category_name: str, title: str):
        super().__init__()
        self.category_name = category_name
        self.title = title

        # 拖拽设置
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

        # 美化样式
        self.setStyleSheet(f"""
            QListWidget {{
                border: 2px solid #e9ecef;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                padding: 12px;
                min-height: 300px;
                alternate-background-color: #f8f9fa;
            }}
            QListWidget::item {{
                padding: 0px;
                margin: 3px 0px;
                border: none;
                background: transparent;
                border-radius: 6px;
            }}
            QListWidget::item:selected {{
                background: rgba(33, 150, 243, 0.1);
                border: 2px solid #2196F3;
            }}
        """)

    def add_sheet_item(self, sheet_name: str):
        """添加美化的工作表项目"""
        item = QListWidgetItem()
        self.addItem(item)

        # 创建美化的widget
        widget = BeautifulSheetItem(sheet_name, self.category_name)
        widget.toggled.connect(self.itemToggled.emit)

        item.setData(Qt.UserRole, sheet_name)
        item.setData(Qt.UserRole + 1, self.category_name)
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)

    def remove_sheet_item(self, sheet_name: str):
        """移除工作表项目"""
        for i in range(self.count()):
            item = self.item(i)
            if item and item.data(Qt.UserRole) == sheet_name:
                self.takeItem(i)
                break

    def get_sheet_names(self) -> List[str]:
        """获取工作表名称列表"""
        names = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if item and widget and widget.is_checked():  # 只返回勾选的项目
                names.append(item.data(Qt.UserRole))
        return names

    def get_cancelled_sheets(self) -> List[str]:
        """获取被取消的工作表列表"""
        cancelled = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if item and widget and not widget.is_checked():  # 未勾选的项目
                cancelled.append(item.data(Qt.UserRole))
        return cancelled

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
        """拖拽进入事件 - 美化高亮"""
        if event.mimeData().hasText():
            # 美化的高亮效果
            self.setStyleSheet(self.styleSheet().replace(
                "border: 2px solid #e9ecef",
                "border: 3px solid #4CAF50"
            ).replace(
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa)",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e8f5e8, stop:1 #c8e6c8)"
            ))
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """拖拽离开事件 - 恢复样式"""
        self.setStyleSheet(f"""
            QListWidget {{
                border: 2px solid #e9ecef;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                padding: 12px;
                min-height: 300px;
                alternate-background-color: #f8f9fa;
            }}
            QListWidget::item {{
                padding: 0px;
                margin: 3px 0px;
                border: none;
                background: transparent;
                border-radius: 6px;
            }}
            QListWidget::item:selected {{
                background: rgba(33, 150, 243, 0.1);
                border: 2px solid #2196F3;
            }}
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

                if from_category != self.category_name:
                    # 添加到当前列表
                    self.add_sheet_item(sheet_name)
                    # 发射移动信号
                    self.itemMoved.emit(sheet_name, from_category, self.category_name)
                    event.acceptProposedAction()
                else:
                    # 同列表内重排
                    super().dropEvent(event)
            else:
                event.ignore()
        else:
            event.ignore()