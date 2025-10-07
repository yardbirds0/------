# -*- coding: utf-8 -*-
"""
Acceptance Test - Model Dialogs
验收测试 - 模型对话框功能

测试清单:
1. AddModelDialog (添加模型对话框)
2. ModelBrowserDialog (管理模型对话框)
3. 集成到ModelConfigDialog
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import Qt
from components.chat.widgets.model_config_dialog import ModelConfigDialog
from components.chat.dialogs import AddModelDialog, ModelBrowserDialog


class AcceptanceTestWindow(QWidget):
    """验收测试主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Model Dialogs 验收测试")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("模型对话框验收测试")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        # 测试说明
        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setMaximumHeight(200)
        instructions.setPlainText("""
验收测试步骤:

1. 点击 "打开模型配置窗口" 按钮
2. 在模型配置窗口中，点击底部 "添加模型" 按钮
   - 验证: 对话框尺寸 480x360px
   - 验证: 3个输入字段 (模型ID*, 模型名称, 分组名称)
   - 验证: 绿色 "添加模型" 按钮
   - 测试: 输入有效的模型ID (例如: "test-model-1")
   - 测试: 点击添加，验证成功消息

3. 在模型配置窗口中，点击底部 "管理模型" 按钮
   - 验证: 对话框尺寸 1000x680px
   - 验证: 搜索框存在
   - 验证: 8个分类标签 (全部、推理、视觉等)
   - 验证: Provider分组树显示
   - 测试: 在搜索框输入文字，验证过滤
   - 测试: 点击不同分类，验证过滤
   - 测试: 点击某个模型，验证选择并关闭

4. 验证UI样式符合cherry_theme
5. 验证所有功能正常工作
        """)
        layout.addWidget(instructions)

        # 测试按钮
        test_btn = QPushButton("打开模型配置窗口")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                padding: 12px;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        test_btn.clicked.connect(self.open_model_config)
        layout.addWidget(test_btn)

        # 结果显示
        self.result_label = QLabel("等待测试...")
        self.result_label.setStyleSheet("padding: 10px; font-size: 12px;")
        layout.addWidget(self.result_label)

        layout.addStretch()

    def open_model_config(self):
        """打开模型配置窗口"""
        self.result_label.setText("已打开模型配置窗口，请测试 '添加模型' 和 '管理模型' 按钮...")

        dialog = ModelConfigDialog()
        dialog.exec()

        self.result_label.setText("模型配置窗口已关闭。请检查测试结果。")


def main():
    print("=" * 70)
    print("Model Dialogs 验收测试")
    print("=" * 70)
    print()
    print("启动验收测试窗口...")
    print()

    app = QApplication(sys.argv)

    window = AcceptanceTestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
