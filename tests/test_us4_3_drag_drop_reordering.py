# -*- coding: utf-8 -*-
"""
US4.3 Provider Drag-Drop Reordering Test
测试Provider列表的拖拽重排序功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
from components.chat.widgets.model_config_dialog import ModelConfigDialog
from components.chat.controllers.config_controller import ConfigController


class TestWindow(QMainWindow):
    """测试主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("US4.3 - Provider Drag-Drop Reordering Test")
        self.resize(500, 400)

        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 标题
        title = QLabel("US4.3 - Provider拖拽重排序测试")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        # 说明信息
        info = QLabel(
            "测试步骤:\n\n"
            "1. 点击下方按钮打开模型配置对话框\n"
            "2. 在左侧Provider列表中:\n"
            "   • 观察每个Provider项前面是否有\"::\"拖拽手柄\n"
            "   • 鼠标悬停在\"::\"上时光标应变为拖拽图标\n"
            "   • 拖拽Provider项到不同位置\n"
            "   • 释放后观察顺序是否改变\n"
            "3. 关闭对话框,重新打开验证顺序是否保持\n"
            "4. 查看config/ai_models.json中的order字段是否更新\n\n"
            "预期结果:\n"
            "✓ 拖拽手柄\"::\"可见\n"
            "✓ 可以拖拽重排序Provider\n"
            "✓ 顺序立即保存并持久化\n"
            "✓ 拖拽阈值防止意外拖拽"
        )
        info.setWordWrap(True)
        info.setStyleSheet("padding: 10px; background-color: #F5F5F5; border-radius: 5px;")
        info.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(info)

        # 打开对话框按钮
        btn = QPushButton("打开模型配置对话框")
        btn.setFixedHeight(40)
        btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """
        )
        btn.clicked.connect(self.open_dialog)
        layout.addWidget(btn)

        # 当前顺序显示
        self.order_label = QLabel()
        self.order_label.setWordWrap(True)
        self.order_label.setStyleSheet("padding: 10px; background-color: #EFF6FF; border-radius: 5px;")
        layout.addWidget(self.order_label)

        # 初始化ConfigController
        self.controller = ConfigController.instance()
        self.controller.provider_changed.connect(self.update_order_display)

        # 显示初始顺序
        self.update_order_display()

    def open_dialog(self):
        """打开模型配置对话框"""
        dialog = ModelConfigDialog(self)
        dialog.exec()

    def update_order_display(self):
        """更新当前顺序显示"""
        providers = self.controller.get_providers()
        order_text = "当前Provider顺序:\n"
        for i, provider in enumerate(providers):
            order_text += f"{i + 1}. {provider.get('name', '未知')} (order={provider.get('order', '?')})\n"
        self.order_label.setText(order_text)


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 创建测试窗口
    window = TestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
