#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新设计的工作表分类对话框 - 现代化设计风格
"""

import sys
import os
from typing import Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QGroupBox, QFrame, QCheckBox, QGraphicsDropShadowEffect, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal, QMimeData, QSize, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDrag, QPixmap, QPainter, QFont, QColor, QLinearGradient, QPalette


class CheckMarkWidget(QCheckBox):
    """√和x样式的复选框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)

        # 设置√和x样式 - 修复定位问题
        self.setStyleSheet("""
            QCheckBox {
                spacing: 0px;
                margin: 0px;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 11px;
                border: 2px solid #e74c3c;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                margin: 0px;
                padding: 0px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #e74c3c;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #ffeaea);
            }
            QCheckBox::indicator:checked {
                border: 2px solid #27ae60;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
                color: white;
            }
        """)

    def paintEvent(self, event):
        """自定义绘制√和x符号"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 获取checkbox的rect
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2

        # 设置字体和颜色
        painter.setFont(QFont("Arial", 12, QFont.Bold))

        if self.isChecked():
            painter.setPen(QColor(255, 255, 255))  # 白色
            painter.drawText(rect, Qt.AlignCenter, "✓")
        else:
            painter.setPen(QColor(231, 76, 60))  # 红色
            painter.drawText(rect, Qt.AlignCenter, "×")


class ModernSheetItem(QWidget):
    """现代化的工作表项目组件"""

    toggled = Signal(str, bool)  # sheet_name, is_checked

    def __init__(self, sheet_name: str, category: str, parent=None):
        super().__init__(parent)
        self.sheet_name = sheet_name
        self.category = category
        self.setup_ui()

    def setup_ui(self):
        """设置现代化界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        # 使用新的√/x复选框
        self.checkbox = CheckMarkWidget()
        self.checkbox.setChecked(True)
        self.checkbox.toggled.connect(lambda checked: self.toggled.emit(self.sheet_name, checked))
        layout.addWidget(self.checkbox, 0, Qt.AlignCenter)

        # 分类图标
        icon_label = QLabel(self.get_category_icon())
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #34495e;
                background: transparent;
                padding: 2px;
                min-width: 20px;
                text-align: center;
            }
        """)
        layout.addWidget(icon_label, 0, Qt.AlignCenter)

        # 工作表名称
        name_label = QLabel(self.sheet_name)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 500;
                color: #2c3e50;
                background: transparent;
                padding: 4px 6px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(name_label, 1)

        # 移除整体项目的边框，只保留背景和悬停效果
        self.setStyleSheet("""
            ModernSheetItem {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: none;
                border-radius: 6px;
                margin: 1px;
                padding: 2px;
            }
            ModernSheetItem:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8f4fd, stop:1 #d6eaf8);
                border: 1px solid #85c1e9;
            }
        """)

        # 添加微妙阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(3)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 1)
        self.setGraphicsEffect(shadow)

    def get_category_icon(self) -> str:
        """获取分类图标"""
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


class ModernDragDropList(QListWidget):
    """现代化的拖拽列表"""

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

        # 现代化样式
        self.setStyleSheet("""
            QListWidget {
                border: 2px solid #bdc3c7;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                padding: 12px;
                min-height: 350px;
                outline: none;
            }
            QListWidget::item {
                padding: 2px;
                margin: 2px 0px;
                border: none;
                background: transparent;
                border-radius: 6px;
                min-height: 32px;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border: 2px solid #2196f3;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f2f6;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #95a5a6;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #7f8c8d;
            }
        """)

    def add_sheet_item(self, sheet_name: str):
        """添加工作表项目"""
        item = QListWidgetItem()
        self.addItem(item)

        # 创建现代化的widget
        widget = ModernSheetItem(sheet_name, self.category_name)
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
        """获取勾选的工作表名称列表"""
        names = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if item and widget and widget.is_checked():
                names.append(item.data(Qt.UserRole))
        return names

    def get_cancelled_sheets(self) -> List[str]:
        """获取被取消的工作表列表"""
        cancelled = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if item and widget and not widget.is_checked():
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
        """拖拽进入事件"""
        if event.mimeData().hasText():
            # 高亮效果
            self.setStyleSheet(self.styleSheet().replace(
                "border: 2px solid #bdc3c7",
                "border: 3px solid #3498db"
            ).replace(
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa)",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e8f4fd, stop:1 #d1ecf1)"
            ))
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        # 恢复原始样式
        self.setStyleSheet("""
            QListWidget {
                border: 2px solid #bdc3c7;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                padding: 12px;
                min-height: 350px;
                outline: none;
            }
            QListWidget::item {
                padding: 2px;
                margin: 2px 0px;
                border: none;
                background: transparent;
                border-radius: 6px;
                min-height: 32px;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border: 2px solid #2196f3;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f2f6;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #95a5a6;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #7f8c8d;
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


class SheetClassificationDialog(QDialog):
    """现代化工作表分类对话框"""

    classificationConfirmed = Signal(dict)  # 发射确认的分类结果

    def __init__(self, parent=None):
        super().__init__(parent)
        self.workbook_manager = None
        self.setup_ui()
        self.setup_window()

    def setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle("工作表分类")
        self.setModal(True)
        self.resize(1000, 700)

        # 现代化窗口样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7f9fc, stop:1 #ecf0f1);
                border-radius: 15px;
            }
        """)

    def setup_ui(self):
        """初始化现代化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题区域
        title_frame = self.create_title_section()
        layout.addWidget(title_frame)

        # 主要分类区域
        classification_frame = self.create_classification_section()
        layout.addWidget(classification_frame, 1)

        # 按钮区域
        buttons_frame = self.create_buttons_section()
        layout.addWidget(buttons_frame)

    def create_title_section(self):
        """创建现代化标题区域"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3498db, stop:0.5 #2980b9, stop:1 #1abc9c);
                border-radius: 20px;
                padding: 25px;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        # 主标题
        title_label = QLabel("📋 智能工作表分类器")
        title_label.setFont(QFont("Microsoft YaHei", 26, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                text-align: center;
                padding: 8px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)

        # 添加发光效果
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(255, 255, 255, 100))
        glow.setOffset(0, 0)
        title_label.setGraphicsEffect(glow)
        layout.addWidget(title_label)

        # 描述文字
        desc_label = QLabel("将工作表拖拽至对应分类，或使用√/× 启用/禁用工作表")
        desc_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 15px;
                font-weight: 400;
                background: transparent;
                padding: 4px;
            }
        """)
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)

        # 统计信息
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
                font-weight: 500;
                background: rgba(255, 255, 255, 0.1);
                padding: 8px 16px;
                border-radius: 15px;
                margin: 5px;
            }
        """)
        self.stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_label)

        return frame

    def create_classification_section(self):
        """创建现代化分类区域"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.98);
                border-radius: 20px;
                padding: 25px;
                border: 1px solid rgba(189, 195, 199, 0.3);
            }
        """)

        # 添加阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 8))
        shadow.setOffset(0, 4)
        frame.setGraphicsEffect(shadow)

        main_layout = QHBoxLayout(frame)
        main_layout.setSpacing(30)

        # 快报表列
        flash_container = self.create_column_container("📊 快报表", "#e74c3c", "#f8d7da")
        self.flash_reports_list = ModernDragDropList("flash_reports", "快报表")
        self.flash_reports_list.itemMoved.connect(self.on_item_moved)
        self.flash_reports_list.itemToggled.connect(self.on_item_toggled)
        flash_container.layout().addWidget(self.flash_reports_list)
        main_layout.addWidget(flash_container, 1)

        # 中间箭头按钮
        buttons_container = self.create_arrow_buttons()
        main_layout.addWidget(buttons_container)

        # 数据来源表列
        data_container = self.create_column_container("📋 数据来源表", "#3498db", "#d1ecf1")
        self.data_sources_list = ModernDragDropList("data_sources", "数据来源表")
        self.data_sources_list.itemMoved.connect(self.on_item_moved)
        self.data_sources_list.itemToggled.connect(self.on_item_toggled)
        data_container.layout().addWidget(self.data_sources_list)
        main_layout.addWidget(data_container, 1)

        return frame

    def create_column_container(self, title: str, primary_color: str, bg_color: str):
        """创建现代化列容器"""
        container = QGroupBox()
        container.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        container.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 3px solid {primary_color};
                border-radius: 15px;
                margin-top: 25px;
                padding-top: 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 1), stop:1 {bg_color});
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 8px 20px;
                color: white;
                background: {primary_color};
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
        """)

        # 设置标题
        container.setTitle(title)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 30, 20, 20)

        return container

    def create_arrow_buttons(self):
        """创建现代化箭头按钮"""
        container = QFrame()
        container.setFixedWidth(100)
        container.setStyleSheet("""
            QFrame {
                background: transparent;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # 向左箭头 (数据源 -> 快报)
        left_btn = QPushButton("◀")
        left_btn.setFixedSize(60, 60)
        left_btn.setFont(QFont("Arial", 20, QFont.Bold))
        left_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border: none;
                border-radius: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:1 #e74c3c);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0392b, stop:1 #a93226);
            }
        """)
        left_btn.setToolTip("移至快报表")
        left_btn.clicked.connect(self.move_to_flash_reports)

        # 向右箭头 (快报 -> 数据源)
        right_btn = QPushButton("▶")
        right_btn.setFixedSize(60, 60)
        right_btn.setFont(QFont("Arial", 20, QFont.Bold))
        right_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: none;
                border-radius: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #21618c);
            }
        """)
        right_btn.setToolTip("移至数据来源表")
        right_btn.clicked.connect(self.move_to_data_sources)

        # 添加现代化阴影
        for btn in [left_btn, right_btn]:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 0, 0, 40))
            shadow.setOffset(0, 5)
            btn.setGraphicsEffect(shadow)

        layout.addWidget(left_btn)
        layout.addWidget(right_btn)

        return container

    def create_buttons_section(self):
        """创建现代化按钮区域"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.9);
                border-radius: 15px;
                padding: 20px;
                border: 1px solid rgba(189, 195, 199, 0.3);
            }
        """)

        layout = QHBoxLayout(frame)
        layout.setSpacing(20)

        # 重置按钮
        reset_btn = QPushButton("🔄 重置")
        reset_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        reset_btn.setFixedHeight(50)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-weight: bold;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a6b5b6, stop:1 #95a5a6);
            }
        """)
        reset_btn.clicked.connect(self.reset_classification)

        # 取消按钮
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        cancel_btn.setFixedHeight(50)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-weight: bold;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:1 #e74c3c);
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        # 确认按钮
        confirm_btn = QPushButton("✅ 确认分类")
        confirm_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        confirm_btn.setFixedHeight(50)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-weight: bold;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
            }
        """)
        confirm_btn.clicked.connect(self.confirm_classification)

        # 添加阴影效果
        for btn in [reset_btn, cancel_btn, confirm_btn]:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setColor(QColor(0, 0, 0, 30))
            shadow.setOffset(0, 3)
            btn.setGraphicsEffect(shadow)

        layout.addWidget(reset_btn)
        layout.addStretch()
        layout.addWidget(cancel_btn)
        layout.addWidget(confirm_btn)

        return frame

    def load_workbook(self, workbook_manager):
        """加载工作簿数据"""
        self.workbook_manager = workbook_manager
        if not workbook_manager:
            return

        # 清空现有列表
        self.flash_reports_list.clear()
        self.data_sources_list.clear()

        # 添加工作表
        flash_sheets = getattr(workbook_manager, 'flash_report_sheets', [])
        for sheet in flash_sheets:
            sheet_name = self._safe_get_sheet_name(sheet)
            self.flash_reports_list.add_sheet_item(sheet_name)

        data_sheets = getattr(workbook_manager, 'data_source_sheets', [])
        for sheet in data_sheets:
            sheet_name = self._safe_get_sheet_name(sheet)
            self.data_sources_list.add_sheet_item(sheet_name)

        # 更新统计
        self.update_stats()

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
        if from_category == "flash_reports":
            self.flash_reports_list.remove_sheet_item(sheet_name)
        elif from_category == "data_sources":
            self.data_sources_list.remove_sheet_item(sheet_name)
        self.update_stats()

    def on_item_toggled(self, sheet_name: str, is_checked: bool):
        """处理checkbox状态变化"""
        self.update_stats()

    def move_to_flash_reports(self):
        """移至快报表"""
        current_item = self.data_sources_list.currentItem()
        if current_item:
            sheet_name = current_item.data(Qt.UserRole)
            if sheet_name:
                self.data_sources_list.remove_sheet_item(sheet_name)
                self.flash_reports_list.add_sheet_item(sheet_name)
                self.update_stats()

    def move_to_data_sources(self):
        """移至数据来源表"""
        current_item = self.flash_reports_list.currentItem()
        if current_item:
            sheet_name = current_item.data(Qt.UserRole)
            if sheet_name:
                self.flash_reports_list.remove_sheet_item(sheet_name)
                self.data_sources_list.add_sheet_item(sheet_name)
                self.update_stats()

    def update_stats(self):
        """更新统计信息"""
        flash_count = self.flash_reports_list.count()
        data_count = self.data_sources_list.count()
        total_count = flash_count + data_count

        # 计算启用/禁用项目数
        cancelled_count = 0
        for list_widget in [self.flash_reports_list, self.data_sources_list]:
            cancelled_count += len(list_widget.get_cancelled_sheets())

        enabled_count = total_count - cancelled_count

        stats_text = (
            f"总计 {total_count} 个工作表  |  "
            f"快报表: {flash_count}  |  数据来源表: {data_count}  |  "
            f"已启用: {enabled_count}  |  已禁用: {cancelled_count}"
        )
        self.stats_label.setText(stats_text)

    def reset_classification(self):
        """重置分类"""
        if self.workbook_manager:
            self.load_workbook(self.workbook_manager)

    def confirm_classification(self):
        """确认分类"""
        classifications = self.get_final_classifications()
        self.classificationConfirmed.emit(classifications)
        self.accept()

    def get_final_classifications(self) -> Dict[str, List[str]]:
        """获取最终分类结果"""
        return {
            'flash_reports': self.flash_reports_list.get_sheet_names(),
            'data_sources': self.data_sources_list.get_sheet_names(),
            'cancelled': (self.flash_reports_list.get_cancelled_sheets() +
                         self.data_sources_list.get_cancelled_sheets())
        }

    @staticmethod
    def show_classification_dialog(workbook_manager, parent=None) -> Optional[Dict[str, List[str]]]:
        """显示分类对话框"""
        dialog = SheetClassificationDialog(parent)
        dialog.load_workbook(workbook_manager)

        result = dialog.exec()
        if result == QDialog.Accepted:
            return dialog.get_final_classifications()
        return None