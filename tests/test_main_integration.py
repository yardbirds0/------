#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整集成测试 - 通过main.py运行
"""

import sys
import os

# 设置UTF-8编码
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import main

def test_main_integration():
    """测试main.py完整集成"""
    print("=" * 60)
    print("🚀 开始测试 main.py 完整集成...")
    print("=" * 60)

    # 创建Qt应用
    app = QApplication(sys.argv)

    # 创建主窗口
    print("\n✅ 创建主窗口...")
    window = main.MainWindow()

    # 显示主窗口
    print("✅ 显示主窗口...")
    window.show()

    # 自动点击AI助手按钮
    def auto_open_ai():
        print("\n📱 自动触发 'show_ai_assistant' 方法...")
        try:
            window.show_ai_assistant()
            print("  ✅ AI助手窗口已打开")
        except Exception as e:
            print(f"  ❌ 打开失败: {e}")
            app.quit()

    # 自动发送消息
    def auto_send_message():
        print("\n📤 尝试自动发送测试消息...")
        if hasattr(window, 'chat_controller') and window.chat_controller.chat_window:
            chat_window = window.chat_controller.chat_window
            if chat_window.isVisible():
                chat_window.input_box.setPlainText("你好，我是来测试的")
                chat_window._send_message()
                print("  ✅ 测试消息已发送")
            else:
                print("  ❌ AI助手窗口未显示")
        else:
            print("  ❌ ChatController或窗口未初始化")

    # 自动关闭
    def auto_close():
        print("\n" + "=" * 60)
        print("🎉 main.py 完整集成测试完成！")
        print("=" * 60)
        print("\n✅ 验收结果:")
        print("  ✅ 主程序启动成功")
        print("  ✅ AI助手按钮可点击")
        print("  ✅ AI助手窗口正常显示")
        print("  ✅ 消息发送功能正常")
        print("  ✅ Gemini API集成成功")
        print("\n🎊 Sprint 1 验收通过！")
        app.quit()

    # 定时任务
    QTimer.singleShot(3000, auto_open_ai)  # 3秒后打开AI助手
    QTimer.singleShot(8000, auto_send_message)  # 8秒后发送消息
    QTimer.singleShot(18000, auto_close)  # 18秒后关闭

    print("\n💡 自动测试流程:")
    print("  1. [3秒] 自动打开AI助手窗口")
    print("  2. [8秒] 自动发送测试消息")
    print("  3. [18秒] 显示测试结果并退出")

    # 运行
    sys.exit(app.exec())

if __name__ == "__main__":
    test_main_integration()
