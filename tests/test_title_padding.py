# -*- coding: utf-8 -*-
"""
测试标题左边距调整
验证标题文字向右平移，不再紧贴左边缘
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
    window.setWindowTitle("标题左边距测试")
    window.resize(450, 600)
    window.setStyleSheet(f"background-color: {COLORS['bg_main']};")

    # 主布局
    layout = QVBoxLayout(window)
    layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])

    # 标题
    title = QLabel("标题左边距调整验证")
    title.setFont(FONTS['title'])
    title.setStyleSheet(f"color: {COLORS['text_primary']};")
    layout.addWidget(title)

    # 说明
    desc = QLabel(
        "调整内容:\n"
        "✓ 标题文字增加8px左边距\n"
        "✓ 文字向右平移，不再紧贴左边缘\n"
        "✓ 所有状态（默认、悬停、选中）都保持一致\n\n"
        "对比观察:\n"
        "- 标题文字与左边缘有适当间距\n"
        "- 选中白色背景时文字不会太靠边\n"
        "- 视觉上更舒适"
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
            'title': '财务报表分析',
            'created_at': '2025-01-15T10:30:00',
            'updated_at': '2025-01-15T11:30:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_2',
            'title': '数据映射与公式生成',
            'created_at': '2025-01-14T15:20:00',
            'updated_at': '2025-01-14T16:00:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_3',
            'title': 'Excel自动填充系统',
            'created_at': '2025-01-13T09:00:00',
            'updated_at': '2025-01-13T10:30:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_4',
            'title': 'AI智能分析对话',
            'created_at': '2025-01-12T14:00:00',
            'updated_at': '2025-01-12T15:30:00',
            'settings_json': '{}'
        }
    ]
    session_panel.load_sessions(test_sessions)
    layout.addWidget(session_panel)

    window.show()

    print("=" * 80)
    print("标题左边距调整测试")
    print("=" * 80)
    print()
    print("调整内容:")
    print("- 标题文字添加8px左边距 (padding-left: 8px)")
    print("- 文字向右平移，与左边缘保持适当距离")
    print()
    print("验证项:")
    print("1. 默认状态：标题文字与左边缘有8px间距")
    print("2. 悬停状态：文字位置不变，背景变浅灰")
    print("3. 选中状态：白色背景时文字不会紧贴左边")
    print("4. 视觉效果：整体更舒适，不拥挤")
    print()
    print("提示:")
    print("- 点击会话观察选中状态的文字位置")
    print("- 悬停观察文字是否保持相同位置")
    print()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
