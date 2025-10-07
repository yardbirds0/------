#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试淡粉色玻璃主题效果
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QGroupBox, QLabel, QPushButton, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt

# 淡粉色玻璃主题CSS
GLASS_THEME_CSS = """
    QMainWindow {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(255, 245, 250, 0.85),
            stop:0.5 rgba(254, 242, 248, 0.8),
            stop:1 rgba(252, 238, 245, 0.75));
    }

    QGroupBox {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(255, 252, 254, 0.8),
            stop:0.5 rgba(255, 250, 253, 0.75),
            stop:1 rgba(254, 248, 252, 0.7));
        border: 1px solid rgba(240, 215, 228, 0.7);
        border-radius: 14px;
        margin-top: 10px;
        padding-top: 14px;
        font-weight: 500;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 18px;
        top: -6px;
        padding: 6px 16px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(215, 120, 165, 0.92),
            stop:1 rgba(235, 145, 190, 0.88));
        color: white;
        border-radius: 7px;
        font-weight: 700;
        font-size: 14pt;
    }

    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(255, 252, 254, 0.92),
            stop:1 rgba(252, 245, 250, 0.88));
        border: 1px solid rgba(230, 200, 215, 0.6);
        border-radius: 8px;
        padding: 7px 18px;
        color: #5a3a47;
        font-weight: 600;
    }

    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(235, 145, 190, 0.25),
            stop:1 rgba(235, 145, 190, 0.18));
        border: 1px solid rgba(215, 130, 165, 0.5);
    }

    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(255, 248, 252, 0.92),
            stop:0.5 rgba(254, 242, 248, 0.88),
            stop:1 rgba(252, 238, 245, 0.85));
        border: 1px solid rgba(230, 200, 215, 0.6);
        border-radius: 12px;
    }

    QDialog QLabel {
        color: #5a3a47;
    }
"""


class TestDialog(QDialog):
    """测试对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("测试对话框 - 淡粉色主题")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("这是一个测试对话框")
        title.setStyleSheet("font-size: 14pt; font-weight: 700; color: #8b4f6f;")
        layout.addWidget(title)

        # 内容
        content = QLabel("测试淡粉色玻璃主题效果\n检查背景、边框和文字颜色是否正确")
        layout.addWidget(content)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class TestWindow(QMainWindow):
    """测试主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("淡粉色玻璃主题测试")
        self.setGeometry(100, 100, 900, 600)

        # 应用主题
        self.setStyleSheet(GLASS_THEME_CSS)

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # 测试GroupBox 1 - 工作表浏览器
        group1 = QGroupBox("工作表浏览器")
        group1_layout = QVBoxLayout(group1)
        tree = QTreeWidget()
        tree.setHeaderLabels(["工作表名称"])
        for i in range(5):
            item = QTreeWidgetItem([f"工作表 {i+1}"])
            tree.addTopLevelItem(item)
        group1_layout.addWidget(tree)
        main_layout.addWidget(group1)

        # 测试GroupBox 2 - 分类摘要
        group2 = QGroupBox("分类摘要")
        group2_layout = QVBoxLayout(group2)
        label = QLabel("快报表: 2 个\n数据源表: 3 个")
        group2_layout.addWidget(label)
        main_layout.addWidget(group2)

        # 按钮区域
        button_layout = QHBoxLayout()
        btn1 = QPushButton("测试按钮")
        btn2 = QPushButton("打开对话框")
        btn2.clicked.connect(self.show_dialog)
        button_layout.addWidget(btn1)
        button_layout.addWidget(btn2)
        main_layout.addLayout(button_layout)

        self.statusBar().showMessage("淡粉色玻璃主题已应用")

    def show_dialog(self):
        """显示测试对话框"""
        dialog = TestDialog(self)
        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
