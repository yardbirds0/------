# -*- coding: utf-8 -*-
"""
测试模型浏览器对话框的按钮修复
验证编辑和删除按钮是否可见和可用
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from components.chat.dialogs.model_browser_dialog import ModelBrowserDialog


class TestWindow(QMainWindow):
    """测试窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("按钮修复测试")
        self.resize(400, 300)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Test button
        test_btn = QPushButton("打开模型浏览器")
        test_btn.setFixedSize(300, 50)
        test_btn.clicked.connect(self.open_browser)
        layout.addWidget(test_btn)

        layout.addStretch()

    def open_browser(self):
        """打开模型浏览器对话框"""
        dialog = ModelBrowserDialog(self)
        dialog.exec()


def main():
    """主测试函数"""
    app = QApplication(sys.argv)

    print("=" * 70)
    print("模型浏览器按钮修复测试")
    print("=" * 70)
    print("\n修复内容:")
    print("\n1. 模型行按钮:")
    print("   - 编辑按钮: 蓝色背景，白色文字 \"编辑\"")
    print("   - 删除按钮: 红色背景，白色文字 \"删除\"")
    print("   - 点击编辑按钮应该打开预填充的添加模型对话框")
    print("   - 点击删除按钮应该显示确认对话框")
    print("\n2. 搜索栏按钮:")
    print("   - 移除了 filter 按钮")
    print("   - 清空按钮: 绿色背景，白色文字 \"清空\"")
    print("   - 点击清空按钮应该清空搜索框并重置到\"全部\"分类")
    print("\n3. 标题栏模型指示器:")
    print("   - 最大宽度增加到 500px")
    print("   - 文本截断长度增加到 60 个字符")
    print("   - 可以完整显示 \"gemini-2.5-flash-preview-09-2025\" 等长名称")
    print("\n测试步骤:")
    print("1. 点击 '打开模型浏览器' 按钮")
    print("2. 检查每个模型行右侧是否有清晰的 \"编辑\" 和 \"删除\" 按钮")
    print("3. 点击 \"编辑\" 按钮，验证是否打开编辑对话框")
    print("4. 点击 \"删除\" 按钮，验证是否显示确认对话框")
    print("5. 在搜索框中输入内容，然后点击 \"清空\" 按钮")
    print("6. 验证搜索框是否清空，分类是否重置到\"全部\"")
    print("=" * 70)

    window = TestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
