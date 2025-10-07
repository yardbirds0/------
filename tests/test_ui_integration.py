#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 AI 助手 UI 集成
"""

import sys
import os

# 设置UTF-8编码
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加父目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from modules.ai_integration.api_providers.base_provider import ProviderConfig, ChatMessage
from controllers.chat_controller import ChatController
from models.data_models import WorkbookManager

def test_ui_integration():
    """测试UI集成"""
    print("=" * 60)
    print("🖥️  开始测试 AI 助手 UI 集成...")
    print("=" * 60)

    # 创建Qt应用
    app = QApplication(sys.argv)

    # 创建WorkbookManager（空的也可以）
    workbook_manager = WorkbookManager()

    # 创建ChatController（不需要传workbook_manager作为parent）
    controller = ChatController(parent=None)

    # 配置API
    config = ProviderConfig(
        api_key="UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t",
        base_url="https://api.kkyyxx.xyz//v1",
        model="gemini-2.5-pro",
        temperature=0.7,
        max_tokens=2000,
        timeout=30
    )

    print("\n✅ 初始化ChatController...")
    controller.initialize(config)

    print("✅ 显示AI助手窗口...")
    controller.show_chat_window()

    # 自动发送测试消息
    def auto_test():
        print("\n📤 自动发送测试消息: '你好，请介绍一下你自己'")
        if controller.chat_window and controller.chat_window.isVisible():
            # 模拟用户输入
            controller.chat_window.input_box.setPlainText("你好，请介绍一下你自己")
            # 触发发送
            controller.chat_window._send_message()
            print("✅ 消息已发送，等待响应...")
        else:
            print("❌ 窗口未显示")
            app.quit()

    # 5秒后自动发送消息
    QTimer.singleShot(5000, auto_test)

    # 15秒后自动关闭
    def auto_close():
        print("\n" + "=" * 60)
        print("🎉 UI集成测试完成！")
        print("=" * 60)
        app.quit()

    QTimer.singleShot(15000, auto_close)

    print("\n💡 窗口将在5秒后自动发送测试消息...")
    print("💡 程序将在15秒后自动退出...")
    print("\n请观察：")
    print("  1. AI助手窗口是否正常显示")
    print("  2. 消息是否成功发送")
    print("  3. 流式响应是否正常显示")
    print("  4. 调试信息是否显示")

    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    test_ui_integration()
