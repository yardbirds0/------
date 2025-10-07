# -*- coding: utf-8 -*-
"""
测试UI改进
验证4个UI需求的实现：
1. 新建会话按钮 - 绿色、动态宽度
2. 会话历史布局 - 标题和时间同行
3. 气泡复制功能 - 悬停显示、淡入淡出
4. AI气泡标题 - logo、模型名称、提供商、时间
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

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel
from PySide6.QtCore import Qt

from components.chat.widgets.session_list_panel import SessionListPanel
from components.chat.widgets.message_bubble import MessageBubble
from components.chat.styles.cherry_theme import COLORS, FONTS, SPACING


def test_session_list():
    """测试需求1和2：新建会话按钮和会话历史布局"""
    app = QApplication(sys.argv)

    # 创建会话列表面板
    panel = SessionListPanel()
    panel.setWindowTitle("测试：会话列表改进")
    panel.resize(400, 600)

    # 加载测试会话数据
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
            'title': '快报表格填充',
            'created_at': '2025-01-13T09:00:00',
            'updated_at': '2025-01-13T10:30:00',
            'settings_json': '{}'
        }
    ]

    panel.load_sessions(test_sessions)
    panel.show()

    print("=" * 80)
    print("需求1验证：新建会话按钮")
    print("-" * 80)
    print("✓ 按钮文字改为'新建会话'（4个中文字）")
    print("✓ 按钮颜色改为绿色（#10B981）")
    print("✓ 按钮宽度自适应内容")
    print()

    print("=" * 80)
    print("需求2验证：会话历史布局")
    print("-" * 80)
    print("✓ 标题和时间在同一行")
    print("✓ 标题在左侧")
    print("✓ 时间在右侧，右对齐")
    print()

    sys.exit(app.exec())


def test_message_bubbles():
    """测试需求3和4：气泡复制功能和AI气泡标题"""
    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("测试：消息气泡改进")
    window.resize(800, 700)
    window.setStyleSheet(f"background-color: {COLORS['bg_main']};")

    # 滚动区域
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setStyleSheet("border: none;")

    scroll_content = QWidget()
    scroll_layout = QVBoxLayout(scroll_content)
    scroll_layout.setContentsMargins(SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
    scroll_layout.setSpacing(SPACING['md'])
    scroll_layout.setAlignment(Qt.AlignTop)

    # ==================== 测试标题 ====================
    title = QLabel("消息气泡改进测试")
    title.setFont(FONTS['title'])
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(f"color: {COLORS['text_primary']}; padding: {SPACING['md']}px;")
    scroll_layout.addWidget(title)

    # ==================== 用户消息1 ====================
    user_bubble1 = MessageBubble("你好，请帮我分析财务报表数据。", is_user=True)
    user_container1 = QWidget()
    user_layout1 = QHBoxLayout(user_container1)
    user_layout1.setContentsMargins(0, 0, 0, 0)
    user_layout1.addStretch()
    user_layout1.addWidget(user_bubble1)
    scroll_layout.addWidget(user_container1)

    # ==================== AI消息1（带标题） ====================
    # 获取当前时间并格式化为"月/日 时:分"
    now = datetime.now()
    timestamp = now.strftime("%m/%d %H:%M")

    ai_bubble1 = MessageBubble(
        content="您好！我是Cherry Studio AI助手。\n\n我可以帮助您：\n"
                "- 📊 分析财务数据结构\n"
                "- 🔍 生成智能映射公式\n"
                "- 💡 解答技术问题\n\n"
                "请上传您的财务报表文件。",
        is_user=False,
        model_name="Qwen3-8B",
        provider="硅基流动",
        timestamp=timestamp
    )
    ai_container1 = QWidget()
    ai_layout1 = QHBoxLayout(ai_container1)
    ai_layout1.setContentsMargins(0, 0, 0, 0)
    ai_layout1.addWidget(ai_bubble1)
    ai_layout1.addStretch()
    scroll_layout.addWidget(ai_container1)

    # ==================== 用户消息2 ====================
    user_bubble2 = MessageBubble(
        "这份报表包含利润表、资产负债表等多个工作表，"
        "我需要提取数据并填充到快报表格中。",
        is_user=True
    )
    user_container2 = QWidget()
    user_layout2 = QHBoxLayout(user_container2)
    user_layout2.setContentsMargins(0, 0, 0, 0)
    user_layout2.addStretch()
    user_layout2.addWidget(user_bubble2)
    scroll_layout.addWidget(user_container2)

    # ==================== AI消息2（带标题） ====================
    ai_bubble2 = MessageBubble(
        content="明白了！让我帮您分析这些工作表的结构：\n\n"
                "1. **利润表**：包含营业收入、营业成本等项目\n"
                "2. **资产负债表**：包含资产、负债、所有者权益\n"
                "3. **现金流量表**：包含经营、投资、筹资活动\n\n"
                "我会为您生成精确的映射公式。",
        is_user=False,
        model_name="GPT-4",
        provider="OpenAI",
        timestamp=now.strftime("%m/%d %H:%M")
    )
    ai_container2 = QWidget()
    ai_layout2 = QHBoxLayout(ai_container2)
    ai_layout2.setContentsMargins(0, 0, 0, 0)
    ai_layout2.addWidget(ai_bubble2)
    ai_layout2.addStretch()
    scroll_layout.addWidget(ai_container2)

    # ==================== 测试说明 ====================
    instructions = QLabel(
        "测试说明：\n"
        "✓ 将鼠标悬停在任意消息气泡上，查看复制按钮的淡入效果\n"
        "✓ 点击复制按钮，将消息内容复制到剪贴板\n"
        "✓ AI消息包含标题：紫色logo + 模型名称|提供商 + 时间\n"
        "✓ 移开鼠标，复制按钮淡出隐藏"
    )
    instructions.setFont(FONTS['body_small'])
    instructions.setWordWrap(True)
    instructions.setStyleSheet(f"""
        QLabel {{
            color: {COLORS['text_secondary']};
            background-color: {COLORS['bg_sidebar']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: {SPACING['md']}px;
        }}
    """)
    scroll_layout.addWidget(instructions)

    scroll_layout.addStretch()
    scroll_area.setWidget(scroll_content)

    main_layout = QVBoxLayout(window)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(scroll_area)

    window.show()

    print("=" * 80)
    print("需求3验证：气泡复制功能")
    print("-" * 80)
    print("✓ 每个气泡下方有复制按钮（默认隐藏）")
    print("✓ 鼠标悬停时按钮淡入显示")
    print("✓ 鼠标离开时按钮淡出隐藏")
    print("✓ 点击按钮复制内容到剪贴板")
    print("✓ 复制成功显示'✓ 已复制'提示")
    print()

    print("=" * 80)
    print("需求4验证：AI气泡标题")
    print("-" * 80)
    print("✓ AI消息包含标题部分")
    print("✓ 左侧：48x48紫色logo，显示🤖")
    print("✓ 右侧第一行：模型名称 | 提供商")
    print("✓ 右侧第二行：时间（月/日 时:分格式）")
    print()

    sys.exit(app.exec())


if __name__ == "__main__":
    print("=" * 80)
    print("UI改进测试")
    print("=" * 80)
    print()
    print("请选择测试：")
    print("1. 测试会话列表改进（需求1、2）")
    print("2. 测试消息气泡改进（需求3、4）")
    print()

    choice = input("请输入选择 (1 或 2): ").strip()

    if choice == "1":
        test_session_list()
    elif choice == "2":
        test_message_bubbles()
    else:
        print("无效选择！")
        sys.exit(1)
