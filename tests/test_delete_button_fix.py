# -*- coding: utf-8 -*-
"""
测试删除按钮显示修复
验证✕字符在各种状态下都能正确显示
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
    window.setWindowTitle("删除按钮显示测试")
    window.resize(500, 600)
    window.setStyleSheet(f"background-color: {COLORS['bg_main']};")

    # 主布局
    layout = QVBoxLayout(window)
    layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])

    # 标题
    title = QLabel("删除按钮(✕)显示测试")
    title.setFont(FONTS['title'])
    title.setStyleSheet(f"color: {COLORS['text_primary']};")
    layout.addWidget(title)

    # 说明
    desc = QLabel(
        "请检查:\n"
        "1. 每个会话右侧是否显示 ✕ 字符\n"
        "2. ✕ 字符是否清晰可见(中灰色)\n"
        "3. 悬停时 ✕ 是否变白色,背景变红色\n"
        "4. ✕ 字符是否居中显示"
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
            'title': '测试会话 1 - 财务报表',
            'created_at': '2025-01-15T10:30:00',
            'updated_at': '2025-01-15T11:30:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_2',
            'title': '测试会话 2 - 数据分析',
            'created_at': '2025-01-14T15:20:00',
            'updated_at': '2025-01-14T16:00:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_3',
            'title': '测试会话 3 - Excel处理',
            'created_at': '2025-01-13T09:00:00',
            'updated_at': '2025-01-13T10:30:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_4',
            'title': '测试会话 4 - AI对话',
            'created_at': '2025-01-12T14:00:00',
            'updated_at': '2025-01-12T15:30:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_5',
            'title': '测试会话 5 - 代码生成',
            'created_at': '2025-01-11T11:00:00',
            'updated_at': '2025-01-11T12:00:00',
            'settings_json': '{}'
        }
    ]
    session_panel.load_sessions(test_sessions)
    layout.addWidget(session_panel)

    window.show()

    print("=" * 80)
    print("删除按钮显示测试")
    print("=" * 80)
    print()
    print("修复内容:")
    print("1. 字符从 × 改为 ✕ (Unicode U+2715)")
    print("2. 字号调整为 16px，加粗")
    print("3. 按钮尺寸从 24x24 增加到 28x28")
    print("4. 默认颜色改为中灰色 (更明显)")
    print("5. 悬停时明确使用白色")
    print()
    print("检查项:")
    print("- ✕ 字符是否在所有会话右侧显示")
    print("- ✕ 字符是否清晰可见")
    print("- 悬停时是否变成白色 ✕ + 红色圆形背景")
    print("- 点击 ✕ 是否能触发删除(会有console输出)")
    print()

    # 监听删除请求（如果有的话）
    # session_panel会内部处理删除逻辑

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
