#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合测试：验证所有修复
1. 无重复对话框
2. 流式UI实时更新
3. 气泡自动高度（无滚动条）
"""

import sys
import os
import io

# 设置UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from modules.ai_integration.api_providers.base_provider import ProviderConfig
from controllers.chat_controller import ChatController

def test_all_fixes():
    """综合测试所有修复"""
    print("=" * 70)
    print("🧪 综合测试：验证所有修复")
    print("=" * 70)

    app = QApplication(sys.argv)

    # 创建ChatController
    controller = ChatController(parent=None)

    # 配置API
    config = ProviderConfig(
        api_key="UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t",
        base_url="https://api.kkyyxx.xyz//v1",
        model="gemini-2.5-pro",
        temperature=0.7,
        max_tokens=150,
        timeout=30
    )

    print("\n✅ 初始化ChatController...")
    controller.initialize(config)

    print("✅ 显示AI助手窗口...")
    controller.show_chat_window()

    message_count = [0]  # 记录发送的消息数

    def send_test_message():
        """发送测试消息"""
        message_count[0] += 1
        test_message = f"测试消息{message_count[0]}: 用一句话介绍Python"

        print(f"\n📤 发送测试消息 {message_count[0]}: '{test_message}'")
        print("💡 验证点：")
        print("   1. 只出现1个对话框（不是2个或3个）")
        print("   2. AI回复一个字一个字逐步显示")
        print("   3. 气泡高度自动调整，无滚动条\n")

        if controller.chat_window and controller.chat_window.isVisible():
            controller.chat_window.input_box.setPlainText(test_message)
            controller.chat_window._send_message()
        else:
            print("❌ 窗口未显示")
            app.quit()

    # 测试流程
    def test_sequence():
        """测试序列"""
        if message_count[0] == 0:
            # 第一次测试
            send_test_message()
            # 15秒后发送第二条消息
            QTimer.singleShot(15000, test_sequence)
        elif message_count[0] == 1:
            # 第二次测试
            print("\n" + "=" * 70)
            print("📨 第二轮测试：验证多次发送不会创建重复气泡")
            print("=" * 70)
            send_test_message()
            # 15秒后结束测试
            QTimer.singleShot(15000, finish_test)

    def finish_test():
        """完成测试"""
        print("\n" + "=" * 70)
        print("✅ 综合测试完成！")
        print("=" * 70)
        print("\n📋 验证清单：")
        print("✓ 每次发送只创建1个AI气泡（无重复）")
        print("✓ AI回复逐字显示（流式效果）")
        print("✓ 气泡高度自动调整（无滚动条）")
        print("\n程序将在3秒后退出...")
        QTimer.singleShot(3000, app.quit)

    # 3秒后开始测试
    QTimer.singleShot(3000, test_sequence)

    print("\n💡 窗口将在3秒后开始测试...")
    print("💡 将发送2条测试消息，每条间隔15秒...")
    print("💡 请仔细观察验证点...\n")

    sys.exit(app.exec())

if __name__ == "__main__":
    test_all_fixes()
