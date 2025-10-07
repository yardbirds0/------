# -*- coding: utf-8 -*-
"""
测试标题栏标签页显示
验证初始标签页正确显示
"""

import sys
import io
from pathlib import Path

# 设置UTF-8编码输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from components.chat.main_window import CherryMainWindow


def main():
    """主测试函数"""
    app = QApplication(sys.argv)

    # 创建主窗口
    window = CherryMainWindow()

    print("=" * 80)
    print("标题栏标签页显示测试")
    print("=" * 80)
    print()
    print("修复内容:")
    print("- 在初始化时添加默认标签页 '💬 AI 分析助手'")
    print("- 解决标题栏左侧空白区域问题")
    print()
    print("验证项:")
    print("1. 标题栏左侧应该显示 '💬 AI 分析助手' 标签页")
    print("2. 鼠标悬停时不应该有空的灰色框")
    print("3. 点击 '+' 按钮可以添加新标签页")
    print("4. 标签页可以正常切换")
    print()
    print("现在窗口已打开，请检查标题栏...")
    print()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
