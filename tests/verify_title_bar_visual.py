# -*- coding: utf-8 -*-
"""
快速验证: 标题栏模型指示器集成
手动测试标题栏是否正常显示
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.chat.widgets.title_bar import CherryTitleBar
from components.chat.styles.cherry_theme import get_global_stylesheet, COLORS


def main():
    app = QApplication(sys.argv)

    # 创建主窗口
    window = QMainWindow()
    window.setWindowTitle("标题栏集成验证")
    window.setWindowFlags(Qt.FramelessWindowHint)  # 无边框窗口
    window.resize(1000, 700)

    # 应用全局样式
    window.setStyleSheet(get_global_stylesheet())

    # 创建中心部件
    central = QWidget()
    window.setCentralWidget(central)

    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # 添加标题栏
    title_bar = CherryTitleBar()
    layout.addWidget(title_bar)

    # 测试内容区域
    test_label = QLabel(
        "✅ 标题栏集成验证\n\n"
        "预期看到:\n"
        "• 左侧: 模型指示器显示当前模型\n"
        "• 右侧: 窗口控制按钮 (- □ ×)\n\n"
        "操作:\n"
        "• 点击模型指示器应弹出配置对话框（当前为消息框）\n"
        "• 鼠标悬停在模型指示器上应有高亮效果\n"
        "• 窗口控制按钮应正常工作"
    )
    test_label.setAlignment(Qt.AlignCenter)
    test_label.setStyleSheet(
        f"background: {COLORS['bg_main']}; "
        f"color: {COLORS['text_secondary']}; "
        f"padding: 40px; "
        f"font-size: 14px; "
        f"line-height: 1.6;"
    )
    layout.addWidget(test_label, stretch=1)

    # 连接窗口控制按钮
    title_bar.min_btn.clicked.connect(window.showMinimized)
    title_bar.max_btn.clicked.connect(
        lambda: window.showNormal() if window.isMaximized() else window.showMaximized()
    )
    title_bar.close_btn.clicked.connect(window.close)

    # 显示窗口
    window.show()

    # 打印验证信息
    print("=" * 60)
    print("标题栏集成验证")
    print("=" * 60)
    print(f"✓ 标题栏高度: {title_bar.height()}px")
    print(f"✓ 模型指示器可见: {title_bar.model_indicator.isVisible()}")
    print(f"✓ 模型指示器大小: {title_bar.model_indicator.width()}×{title_bar.model_indicator.height()}px")
    print(f"✓ 窗口控制按钮存在: 最小化={title_bar.min_btn is not None}, "
          f"最大化={title_bar.max_btn is not None}, 关闭={title_bar.close_btn is not None}")
    print("=" * 60)
    print("\n请在窗口中验证:")
    print("1. 模型指示器是否正确显示在标题栏左侧")
    print("2. 点击模型指示器是否弹出消息框")
    print("3. 窗口控制按钮是否在右侧正常工作")
    print("=" * 60)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
