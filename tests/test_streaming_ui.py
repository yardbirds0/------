#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试流式UI显示效果 - 验证逐字显示
"""

import sys
import os
import io
import time

# 设置UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from modules.ai_integration.api_providers.base_provider import ProviderConfig
from controllers.chat_controller import ChatController

def test_streaming_ui():
    """测试流式UI显示"""
    print("=" * 60)
    print("🎬 测试流式UI显示效果")
    print("=" * 60)

    # 创建Qt应用
    app = QApplication(sys.argv)

    # 创建ChatController
    controller = ChatController(parent=None)

    # 配置API
    config = ProviderConfig(
        api_key="UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t",
        base_url="https://api.kkyyxx.xyz//v1",
        model="gemini-2.5-pro",
        temperature=0.7,
        max_tokens=100,  # 限制tokens减少测试时间
        timeout=30
    )

    print("\n✅ 初始化ChatController...")
    controller.initialize(config)

    print("✅ 显示AI助手窗口...")
    controller.show_chat_window()

    # 自动发送测试消息
    def auto_test():
        print("\n📤 自动发送测试消息: '从1数到5'")
        print("💡 观察：AI的回复应该一个字一个字逐步显示，而不是一次性出现\n")

        if controller.chat_window and controller.chat_window.isVisible():
            # 模拟用户输入
            controller.chat_window.input_box.setPlainText("从1数到5")
            # 触发发送
            controller.chat_window._send_message()
            print("✅ 消息已发送，开始接收流式响应...")
        else:
            print("❌ 窗口未显示")
            app.quit()

    # 20秒后自动关闭（给足够时间观察流式效果）
    def auto_close():
        print("\n" + "=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)
        app.quit()

    # 3秒后自动发送消息
    QTimer.singleShot(3000, auto_test)

    # 30秒后自动关闭
    QTimer.singleShot(30000, auto_close)

    print("\n💡 窗口将在3秒后自动发送测试消息...")
    print("💡 请观察AI回复是否一个字一个字逐步显示...")
    print("💡 程序将在30秒后自动退出...\n")

    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    test_streaming_ui()
