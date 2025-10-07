#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟流式UI显示测试 - 不依赖真实API
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
from components.chat.chat_window import ChatWindow

def test_simulated_streaming():
    """模拟流式显示测试"""
    print("=" * 60)
    print("🧪 模拟流式UI显示测试（无需API）")
    print("=" * 60)

    # 创建Qt应用
    app = QApplication(sys.argv)

    # 创建ChatWindow
    chat_window = ChatWindow()
    chat_window.show()

    print("\n✅ ChatWindow已创建并显示")
    print("💡 将模拟逐字符流式响应...\n")

    # 测试内容
    test_response = "你好！我是AI助手。\n\n我可以帮您：\n1. 分析数据\n2. 回答问题\n3. 提供建议"
    chunks = list(test_response)  # 拆分成单个字符

    current_index = [0]  # 使用列表以便在闭包中修改

    def simulate_chunk():
        """模拟接收一个字符"""
        if current_index[0] < len(chunks):
            chunk = chunks[current_index[0]]
            chat_window.update_streaming_message(chunk)
            print(f"📨 Chunk {current_index[0] + 1}/{len(chunks)}: '{chunk}'", end='\r')
            current_index[0] += 1

            # 继续下一个chunk（50ms间隔，模拟真实流式速度）
            QTimer.singleShot(50, simulate_chunk)
        else:
            print(f"\n\n✅ 所有{len(chunks)}个字符已发送完成！")
            chat_window.finish_streaming_message()
            print("💡 观察窗口中的消息是否一个字一个字显示出来\n")

            # 3秒后关闭
            QTimer.singleShot(3000, app.quit)

    # 开始模拟
    def start_simulation():
        print("📤 开始模拟流式响应...")
        # 添加用户消息
        chat_window.add_user_message("请介绍一下你自己")

        # 创建空的流式消息
        chat_window.start_streaming_message()

        # 延迟500ms开始发送chunk（模拟API延迟）
        QTimer.singleShot(500, simulate_chunk)

    # 1秒后开始模拟
    QTimer.singleShot(1000, start_simulation)

    print("💡 窗口将在1秒后开始模拟流式响应...")
    print("💡 每50ms发送1个字符，观察是否逐字显示...")
    print("💡 完成后3秒自动退出...\n")

    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    test_simulated_streaming()
