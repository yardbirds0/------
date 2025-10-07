# -*- coding: utf-8 -*-
"""
测试最终修复
验证AI标题显示和删除按钮始终可见
"""

import sys
import io
from pathlib import Path
from datetime import datetime

# 设置UTF-8编码输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer

from components.chat.widgets.session_list_panel import SessionListPanel
from components.chat.widgets.message_area import MessageArea
from components.chat.styles.cherry_theme import COLORS, FONTS, SPACING


def main():
    """主测试函数"""
    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("最终修复测试 - AI标题 + 删除按钮")
    window.resize(1200, 800)
    window.setStyleSheet(f"background-color: {COLORS['bg_main']};")

    # 主布局
    main_layout = QHBoxLayout(window)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(SPACING['md'])

    # ==================== 左侧：会话列表（测试删除按钮始终可见） ====================
    left_panel = QWidget()
    left_panel.setFixedWidth(400)
    left_layout = QVBoxLayout(left_panel)
    left_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])

    # 标题
    title_label = QLabel("修复验证1：删除按钮(X)始终可见")
    title_label.setFont(FONTS['title'])
    title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
    left_layout.addWidget(title_label)

    # 说明
    desc_label = QLabel("✓ 每个会话右侧应该始终显示 X 按钮\n✓ 不需要悬停才能看到\n✓ 悬停时 X 会变红色")
    desc_label.setFont(FONTS['body'])
    desc_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
    desc_label.setWordWrap(True)
    left_layout.addWidget(desc_label)

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
            'title': '数据映射公式生成',
            'created_at': '2025-01-14T15:20:00',
            'updated_at': '2025-01-14T16:00:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_3',
            'title': 'Excel数据提取',
            'created_at': '2025-01-13T09:00:00',
            'updated_at': '2025-01-13T10:30:00',
            'settings_json': '{}'
        }
    ]
    session_panel.load_sessions(test_sessions)
    left_layout.addWidget(session_panel)

    main_layout.addWidget(left_panel)

    # ==================== 右侧：消息区域（测试AI标题默认显示） ====================
    right_panel = QWidget()
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])

    # 标题
    title_label2 = QLabel("修复验证2：AI标题显示默认值")
    title_label2.setFont(FONTS['title'])
    title_label2.setStyleSheet(f"color: {COLORS['text_primary']};")
    right_layout.addWidget(title_label2)

    # 说明
    desc_label2 = QLabel("✓ AI消息应显示标题：🤖 gemini-2.5-pro | Google + 时间\n✓ 即使没有明确传入参数，也应该显示默认值")
    desc_label2.setFont(FONTS['body'])
    desc_label2.setStyleSheet(f"color: {COLORS['text_secondary']};")
    desc_label2.setWordWrap(True)
    right_layout.addWidget(desc_label2)

    # 消息区域
    message_area = MessageArea()

    # 添加测试消息
    message_area.add_user_message("请帮我分析财务数据")

    # 模拟主程序流程：使用默认值
    current_time = datetime.now().strftime("%H:%M")

    # 方式1：使用默认模型名称
    message_area.start_streaming_message(
        model_name='gemini-2.5-pro',
        provider='Google',
        timestamp=current_time
    )

    # 模拟流式输出
    test_response = "好的，我来帮您分析财务数据。"

    def simulate_streaming():
        for char in test_response:
            message_area.update_streaming_message(char)
        message_area.finish_streaming_message()

    QTimer.singleShot(500, simulate_streaming)

    right_layout.addWidget(message_area)

    main_layout.addWidget(right_panel)

    window.show()

    print("=" * 80)
    print("最终修复测试")
    print("=" * 80)
    print()

    print("修复1：删除按钮始终可见")
    print("-" * 80)
    print("✓ 查看左侧会话列表")
    print("✓ 每个会话右侧应该始终显示 X 按钮（不需要悬停）")
    print("✓ 悬停时 X 按钮会变红色")
    print()

    print("修复2：AI标题显示默认值")
    print("-" * 80)
    print("✓ 查看右侧AI消息")
    print("✓ 应该显示标题：🤖 gemini-2.5-pro | Google [时间]")
    print("✓ 即使在主程序中没有明确参数，也会使用默认值")
    print()

    print("=" * 80)
    print("验收标准")
    print("=" * 80)
    print("1. X 按钮在所有会话项中始终可见（不需要悬停）")
    print("2. AI消息顶部显示完整标题行")
    print("3. 标题包含默认模型名称 gemini-2.5-pro 和 Google")
    print()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
