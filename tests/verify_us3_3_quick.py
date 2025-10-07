# -*- coding: utf-8 -*-
"""
US-3.3 Quick Verification - Test streaming functionality and auto-exit
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from modules.ai_integration import OpenAIService, StreamingHandler, ChatManager
from components.chat.widgets.message_area import MessageArea

def main():
    app = QApplication(sys.argv)

    # 创建消息区域
    message_area = MessageArea()
    message_area.resize(700, 600)
    message_area.show()

    # 创建AI服务
    service = OpenAIService({})
    streaming_handler = StreamingHandler(service)
    chat_manager = ChatManager()

    # 测试状态
    test_state = {
        'started': False,
        'chunks_received': 0,
        'finished': False,
        'error': None
    }

    # 连接信号
    def on_started():
        test_state['started'] = True
        print("[OK] Stream started - Loading animation should appear")

    def on_chunk(chunk):
        test_state['chunks_received'] += 1
        if test_state['chunks_received'] == 1:
            print("[OK] First chunk received - Loading animation should disappear, bubble should appear")
        if test_state['chunks_received'] % 10 == 0:
            print(f"[OK] Received {test_state['chunks_received']} chunks...")

    def on_finished(response):
        test_state['finished'] = True
        print(f"[OK] Stream finished - Total chunks: {test_state['chunks_received']}")
        print(f"[OK] Response length: {len(response)} characters")

        # 验证结果
        print("\n" + "=" * 60)
        print("VERIFICATION RESULTS:")
        print("=" * 60)
        print(f"Stream Started: {'PASS' if test_state['started'] else 'FAIL'}")
        print(f"Chunks Received: {'PASS' if test_state['chunks_received'] > 0 else 'FAIL'} ({test_state['chunks_received']} chunks)")
        print(f"Stream Finished: {'PASS' if test_state['finished'] else 'FAIL'}")
        print(f"No Errors: {'PASS' if test_state['error'] is None else 'FAIL'}")
        print("=" * 60)

        # 3秒后退出
        QTimer.singleShot(3000, app.quit)

    def on_error(error):
        test_state['error'] = error
        print(f"[ERROR] {error}")
        QTimer.singleShot(1000, app.quit)

    streaming_handler.stream_started.connect(on_started)
    streaming_handler.chunk_received.connect(on_chunk)
    streaming_handler.stream_finished.connect(on_finished)
    streaming_handler.stream_error.connect(on_error)

    # 发送测试消息
    print("\n" + "=" * 60)
    print("US-3.3 QUICK VERIFICATION TEST")
    print("=" * 60)
    print("\nSending test message...")

    user_msg = "Say hello in 2-3 sentences"
    message_area.add_user_message(user_msg)
    chat_manager.add_message('user', user_msg)

    messages = chat_manager.get_context_messages()
    streaming_handler.start_stream(messages, system_prompt="You are a friendly assistant. Be concise.")

    # 30秒超时保护
    QTimer.singleShot(30000, lambda: [
        print("\n[TIMEOUT] Test exceeded 30 seconds"),
        app.quit()
    ])

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
