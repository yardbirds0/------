# -*- coding: utf-8 -*-
"""
测试UI改进 - 需求11和12
验证选中会话的悬浮阴影效果和AI气泡标题显示
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
from PySide6.QtCore import Qt

from components.chat.widgets.session_list_panel import SessionListPanel
from components.chat.widgets.message_area import MessageArea
from components.chat.styles.cherry_theme import COLORS, FONTS, SPACING


def main():
    """主测试函数"""
    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("UI改进测试 - 需求11和12")
    window.resize(1200, 800)
    window.setStyleSheet(f"background-color: {COLORS['bg_main']};")

    # 主布局
    main_layout = QHBoxLayout(window)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(SPACING['md'])

    # ==================== 左侧：会话列表（测试悬浮阴影） ====================
    left_panel = QWidget()
    left_panel.setFixedWidth(400)
    left_layout = QVBoxLayout(left_panel)
    left_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])

    # 标题
    title_label = QLabel("需求11测试：选中会话的悬浮阴影效果")
    title_label.setFont(FONTS['title'])
    title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
    left_layout.addWidget(title_label)

    # 说明
    desc_label = QLabel("点击会话项，观察选中状态的阴影效果")
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

    # ==================== 右侧：消息区域（测试AI标题） ====================
    right_panel = QWidget()
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])

    # 标题
    title_label2 = QLabel("需求12测试：AI气泡标题显示")
    title_label2.setFont(FONTS['title'])
    title_label2.setStyleSheet(f"color: {COLORS['text_primary']};")
    right_layout.addWidget(title_label2)

    # 说明
    desc_label2 = QLabel("观察AI消息气泡是否显示标题（包含logo、模型名称、提供商、时间）")
    desc_label2.setFont(FONTS['body'])
    desc_label2.setStyleSheet(f"color: {COLORS['text_secondary']};")
    desc_label2.setWordWrap(True)
    right_layout.addWidget(desc_label2)

    # 消息区域
    message_area = MessageArea()

    # 添加测试消息
    message_area.add_user_message("请帮我分析一下这份财务报表")

    # 添加带完整元数据的AI消息
    current_time = datetime.now().strftime("%H:%M")
    message_area.add_ai_message(
        "好的，我来帮您分析这份财务报表。\n\n根据数据显示：\n1. 营业收入稳定增长\n2. 成本控制良好\n3. 利润率保持健康水平",
        model_name="GPT-4",
        provider="OpenAI",
        timestamp=current_time
    )

    message_area.add_user_message("能详细说明一下成本结构吗？")

    # 添加另一条AI消息（不同模型）
    message_area.add_ai_message(
        "当然可以。成本结构主要包括：\n- 直接成本：60%\n- 间接成本：30%\n- 管理费用：10%",
        model_name="Claude-3",
        provider="Anthropic",
        timestamp=datetime.now().strftime("%H:%M")
    )

    right_layout.addWidget(message_area)

    main_layout.addWidget(right_panel)

    window.show()

    print("=" * 80)
    print("UI改进测试 - 需求11和12")
    print("=" * 80)
    print()

    print("需求11验证：选中会话的悬浮阴影效果")
    print("-" * 80)
    print("✓ 点击左侧会话列表中的任意项")
    print("✓ 观察选中项是否出现悬浮阴影效果")
    print("✓ 阴影应该在四周，产生'悬浮'的视觉效果")
    print()

    print("需求12验证：AI气泡标题显示")
    print("-" * 80)
    print("✓ 查看右侧AI消息气泡")
    print("✓ 每个AI气泡顶部应该显示标题行")
    print("✓ 标题行包含：🤖 logo + 模型名称|提供商 + 时间")
    print("✓ 示例：🤖  GPT-4 | OpenAI    14:30")
    print()

    print("=" * 80)
    print("测试说明")
    print("=" * 80)
    print("1. 左侧：点击会话列表项，观察选中时的阴影效果")
    print("2. 右侧：查看AI消息气泡是否有标题行")
    print("3. 标题行应显示在每个AI消息的顶部")
    print()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
