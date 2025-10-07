# -*- coding: utf-8 -*-
"""
测试AI参数设置面板的清理工作
验证标题和模型设置包裹块是否已被移除
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget
from components.chat.widgets.sidebar import CherrySidebar


class TestWindow(QMainWindow):
    """测试窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI参数设置面板清理测试")
        self.resize(1000, 700)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # 左侧内容区域
        from components.chat.styles.cherry_theme import COLORS
        content = QWidget()
        content.setStyleSheet(f"background: {COLORS['bg_main']};")
        layout.addWidget(content, stretch=1)

        # 右侧侧边栏
        self.sidebar = CherrySidebar()
        layout.addWidget(self.sidebar)

        # 默认切换到AI参数设置TAB
        self.sidebar.show_settings_tab()


def main():
    """主测试函数"""
    app = QApplication(sys.argv)

    print("=" * 70)
    print("AI参数设置面板清理测试")
    print("=" * 70)
    print("\n修改内容:")
    print("\n1. 移除了TAB下方的重复标题 \"AI 参数设置\"")
    print("   - 之前: TAB标签显示\"AI参数设置\" + 下方还有一个\"AI 参数设置\"标题")
    print("   - 现在: 只有TAB标签，下方直接显示参数设置项")
    print("\n2. 移除了第一个包裹块 \"模型设置\"")
    print("   - 之前: 第一个包裹块是模型选择下拉框")
    print("   - 现在: 第一个包裹块是\"流式输出 (Stream)\"")
    print("   - 原因: 模型设置功能已被标题栏的模型指示器替代")
    print("\n验证步骤:")
    print("1. 窗口打开后，右侧默认显示\"AI参数设置\"TAB")
    print("2. 检查TAB下方是否没有重复的\"AI 参数设置\"标题")
    print("3. 检查第一个包裹块是否是\"流式输出 (Stream)\"")
    print("4. 确认没有\"模型设置\"包裹块")
    print("=" * 70)

    window = TestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
