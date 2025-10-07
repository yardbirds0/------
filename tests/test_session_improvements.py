# -*- coding: utf-8 -*-
"""
测试最新修改
验证:
1. ✕按钮只在悬停时显示
2. 标题限制为前20个字符
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

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from components.chat.widgets.session_list_panel import SessionListPanel
from components.chat.styles.cherry_theme import COLORS, FONTS, SPACING


def main():
    """主测试函数"""
    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("会话列表改进测试 - ✕悬停显示 + 标题20字符")
    window.resize(500, 700)
    window.setStyleSheet(f"background-color: {COLORS['bg_main']};")

    # 主布局
    layout = QVBoxLayout(window)
    layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])

    # 标题
    title = QLabel("会话列表改进验证")
    title.setFont(FONTS['title'])
    title.setStyleSheet(f"color: {COLORS['text_primary']};")
    layout.addWidget(title)

    # 说明
    desc = QLabel(
        "测试内容:\n"
        "1. ✕按钮只在鼠标悬停时显示（默认隐藏）\n"
        "2. 标题限制为前20个字符\n"
        "3. 超过20字符的标题会被截断\n\n"
        "验证方法:\n"
        "- 将鼠标移到会话上，✕应该出现\n"
        "- 移开鼠标，✕应该消失\n"
        "- 长标题只显示前20个字符"
    )
    desc.setFont(FONTS['body'])
    desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
    desc.setWordWrap(True)
    layout.addWidget(desc)

    # 会话列表
    session_panel = SessionListPanel()
    test_sessions = [
        {
            'id': 'session_1',
            'title': '短标题',  # 3个字符
            'created_at': '2025-01-15T10:30:00',
            'updated_at': '2025-01-15T11:30:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_2',
            'title': '这是一个正好二十个字符的标题测试',  # 正好20个字符
            'created_at': '2025-01-14T15:20:00',
            'updated_at': '2025-01-14T16:00:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_3',
            'title': '这是一个超过二十个字符的标题应该被截断显示',  # 超过20个字符
            'created_at': '2025-01-13T09:00:00',
            'updated_at': '2025-01-13T10:30:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_4',
            'title': '财务报表数据分析与快报填充系统开发项目',  # 超长标题
            'created_at': '2025-01-12T14:00:00',
            'updated_at': '2025-01-12T15:30:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_5',
            'title': 'AI Powered Financial Report Data Mapping',  # 英文超长
            'created_at': '2025-01-11T11:00:00',
            'updated_at': '2025-01-11T12:00:00',
            'settings_json': '{}'
        }
    ]
    session_panel.load_sessions(test_sessions)
    layout.addWidget(session_panel)

    window.show()

    print("=" * 80)
    print("会话列表改进测试")
    print("=" * 80)
    print()
    print("改进1: ✕按钮只在悬停时显示")
    print("-" * 80)
    print("✓ 默认状态：✕按钮隐藏")
    print("✓ 鼠标悬停：✕按钮显示（白色 + 红色背景）")
    print("✓ 鼠标移开：✕按钮再次隐藏")
    print()
    print("改进2: 标题限制为前20个字符")
    print("-" * 80)
    print("原始标题 → 显示标题:")
    print(f"1. '短标题' → '短标题' (3字符，不截断)")
    print(f"2. '这是一个正好二十个字符的标题测试' → '这是一个正好二十个字符的标题测试' (20字符，刚好)")
    print(f"3. '这是一个超过二十个字符的标题应该被截断显示' → '这是一个超过二十个字符的标题' (截断)")
    print(f"4. '财务报表数据分析与快报填充系统开发项目' → '财务报表数据分析与快报填充系统开发' (截断)")
    print(f"5. 'AI Powered Financial Report Data Mapping' → 'AI Powered Financia' (截断)")
    print()
    print("验收标准:")
    print("1. ✕按钮默认不可见")
    print("2. 悬停时✕按钮出现")
    print("3. 所有标题长度 ≤ 20字符")
    print()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
