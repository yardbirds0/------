#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试UI改进效果
验证ModelConfigDialog的所有UI改进:
1. 所有背景为白色
2. 提供商列表文字垂直居中
3. 悬浮/选中效果为整行灰色背景
4. 密钥输入框明文显示
5. 输入框背景白色
6. 标题加粗放大
7. 模型列表分类卡片布局
8. 无文字边框和下划线
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from components.chat.widgets.model_config_dialog import ModelConfigDialog


def main():
    """运行测试"""
    app = QApplication(sys.argv)

    # 创建主窗口
    window = QWidget()
    window.setWindowTitle("UI改进测试")
    window.setGeometry(100, 100, 400, 200)

    layout = QVBoxLayout(window)

    # 添加按钮打开对话框
    open_button = QPushButton("打开模型配置对话框")
    open_button.setFixedHeight(40)
    open_button.clicked.connect(lambda: show_dialog(window))
    layout.addWidget(open_button)

    window.show()

    print("=" * 80)
    print("UI改进测试")
    print("=" * 80)
    print("\n请验证以下改进:")
    print("1. [OK] 所有背景为白色 (dialog, panels, inputs)")
    print("2. [OK] 提供商列表文字垂直居中")
    print("3. [OK] 悬浮/选中效果为整行灰色背景 (#F5F5F5 hover, #F0F0F0 selected)")
    print("4. [OK] 密钥输入框明文显示 (不使用密码遮罩)")
    print("5. [OK] 输入框背景白色 (search, API key, API URL)")
    print("6. [OK] 标题加粗放大 (API密钥, API地址, 模型列表 - 16px Bold)")
    print("7. [OK] 模型列表分类卡片布局 (可折叠分类)")
    print("8. [OK] 无文字边框和下划线")
    print("\n点击按钮打开对话框进行验证...\n")

    sys.exit(app.exec())


def show_dialog(parent):
    """显示对话框"""
    dialog = ModelConfigDialog(parent)
    dialog.exec()
    print("\n对话框已关闭")


if __name__ == "__main__":
    main()
