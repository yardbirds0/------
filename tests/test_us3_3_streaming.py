# -*- coding: utf-8 -*-
"""
US-3.3 完整测试 - 流式输出Handler + 加载动画 + 圆角气泡
测试真实的AI流式回复功能
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

from modules.ai_integration import OpenAIService, StreamingHandler, ChatManager, ChatMessage
from components.chat.widgets.message_area import MessageArea
from components.chat.styles.cherry_theme import COLORS, SPACING


def main():
    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("US-3.3 Streaming Output Test")
    window.resize(800, 700)
    window.setStyleSheet(f"background-color: {COLORS['bg_main']};")

    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)

    # 消息区域
    message_area = MessageArea()
    layout.addWidget(message_area, stretch=1)

    # 测试按钮区域
    button_widget = QWidget()
    button_layout = QHBoxLayout(button_widget)
    button_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
    button_layout.setSpacing(SPACING['sm'])

    # 创建AI服务和StreamingHandler
    service = OpenAIService({})  # 使用内置默认配置
    streaming_handler = StreamingHandler(service)
    chat_manager = ChatManager()

    # 连接信号
    streaming_handler.stream_started.connect(lambda: message_area.start_streaming_message())
    streaming_handler.chunk_received.connect(lambda chunk: message_area.update_streaming_message(chunk))
    streaming_handler.stream_finished.connect(lambda response: message_area.finish_streaming_message())
    streaming_handler.stream_error.connect(lambda error: print(f"错误: {error}"))

    # 测试按钮1: 简单问题
    test_btn1 = QPushButton("Test 1: Simple Question")

    def test_simple_question():
        # 添加用户消息
        user_msg = "Hello, please introduce yourself"
        message_area.add_user_message(user_msg)

        # 添加到对话历史
        chat_manager.add_message('user', user_msg)

        # 发送流式请求
        messages = chat_manager.get_context_messages()
        streaming_handler.start_stream(messages, system_prompt="You are a friendly AI assistant.")

    test_btn1.clicked.connect(test_simple_question)
    button_layout.addWidget(test_btn1)

    # 测试按钮2: 代码生成
    test_btn2 = QPushButton("Test 2: Code Generation")

    def test_code_generation():
        # 添加用户消息
        user_msg = "Write a Python function to calculate the nth Fibonacci number"
        message_area.add_user_message(user_msg)

        # 添加到对话历史
        chat_manager.add_message('user', user_msg)

        # 发送流式请求
        messages = chat_manager.get_context_messages()
        streaming_handler.start_stream(messages, system_prompt="You are a professional programming assistant.")

    test_btn2.clicked.connect(test_code_generation)
    button_layout.addWidget(test_btn2)

    # 测试按钮3: 长文本
    test_btn3 = QPushButton("Test 3: Long Response")

    def test_long_response():
        # 添加用户消息
        user_msg = "Please explain artificial intelligence in detail and list several practical applications"
        message_area.add_user_message(user_msg)

        # 添加到对话历史
        chat_manager.add_message('user', user_msg)

        # 发送流式请求
        messages = chat_manager.get_context_messages()
        streaming_handler.start_stream(messages, system_prompt="You are a knowledgeable explainer.")

    test_btn3.clicked.connect(test_long_response)
    button_layout.addWidget(test_btn3)

    # 清空按钮
    clear_btn = QPushButton("Clear Chat")
    clear_btn.clicked.connect(lambda: [message_area.clear_messages(), chat_manager.__init__()])
    button_layout.addWidget(clear_btn)

    layout.addWidget(button_widget)

    # 显示说明
    print("\n" + "=" * 60)
    print("US-3.3 Streaming Output Test")
    print("=" * 60)
    print("\nFeatures:")
    print("[OK] StreamingHandler - Real async streaming")
    print("[OK] TypingIndicator - Three-dot loading animation")
    print("[OK] MessageArea - Loading animation -> Streaming update")
    print("[OK] MessageBubble - 12px large border-radius")
    print("[OK] Markdown rendering - AI messages support Markdown")
    print("\nInstructions:")
    print("1. Click any test button to send message")
    print("2. Watch three-dot loading animation")
    print("3. Watch AI reply display character by character")
    print("4. Check bubble border-radius effect")
    print("5. Click 'Clear Chat' to test again")
    print("\n" + "=" * 60 + "\n")

    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
