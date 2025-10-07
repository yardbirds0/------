# -*- coding: utf-8 -*-
"""
Test script for real-time model refresh functionality
Verifies that adding a model immediately refreshes the UI
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer
from components.chat.widgets.model_config_dialog import ModelConfigDialog
from controllers.config_controller import ConfigController


class TestWindow(QMainWindow):
    """Test window for model refresh functionality"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Model Refresh")
        self.resize(400, 300)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Test button
        test_btn = QPushButton("打开模型设置 (测试实时刷新)")
        test_btn.setFixedSize(300, 50)
        test_btn.clicked.connect(self.open_config)
        layout.addWidget(test_btn)

        layout.addStretch()

    def open_config(self):
        """Open ModelConfigDialog"""
        dialog = ModelConfigDialog(self)
        dialog.exec()


def main():
    """Main test function"""
    app = QApplication(sys.argv)

    print("=" * 70)
    print("模型实时刷新测试")
    print("=" * 70)
    print("\n测试步骤:")
    print("1. 点击按钮打开模型设置窗口")
    print("2. 选择一个提供商 (例如 Google)")
    print("3. 点击 '添加模型' 按钮")
    print("4. 填写模型信息:")
    print("   - 模型 ID: test-model-refresh")
    print("   - 模型名称: 测试刷新模型")
    print("   - 分类: Test")
    print("5. 点击确定")
    print("\n预期结果:")
    print("[PASS] 新模型应该立即出现在模型列表中")
    print("[PASS] 不需要切换到其他提供商再切回来")
    print("\n修复详情:")
    print("- 文件: components/chat/widgets/model_config_dialog.py")
    print("- 行号: 1046")
    print("- 修改: _load_providers() → _populate_model_tree()")
    print("=" * 70)

    window = TestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
