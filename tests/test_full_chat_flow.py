# -*- coding: utf-8 -*-
"""
完整测试Chat流程 - 从UI到AI服务
"""

import sys
import logging
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """测试完整流程"""
    app = QApplication.instance() or QApplication(sys.argv)

    # 导入组件
    from controllers.chat_controller import ChatController
    from modules.ai_integration.api_providers.base_provider import ProviderConfig

    # 创建控制器
    chat_controller = ChatController()

    # 配置AI服务
    config = ProviderConfig(
        api_key="UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t",
        base_url="https://api.kkyyxx.xyz/v1",
        model="gemini-2.5-pro",
        temperature=0.3,
        max_tokens=500,  # 减少tokens以加快响应
        timeout=30
    )

    logger.info("初始化AI服务...")
    chat_controller.initialize(config)

    logger.info("显示对话窗口...")
    chat_controller.show_chat_window()

    # 获取窗口引用
    chat_window = chat_controller.chat_window

    # 添加调试信号
    def on_message_sent(message, params):
        logger.info(f"[SIGNAL] message_sent: {message[:50]}...")
        logger.info(f"[SIGNAL] AI params: {params}")

    def on_stream_started():
        logger.info("[SIGNAL] StreamingHandler.stream_started")

    def on_chunk_received(chunk):
        logger.info(f"[SIGNAL] StreamingHandler.chunk_received: {repr(chunk[:30])}")

    def on_stream_finished(response):
        logger.info(f"[SIGNAL] StreamingHandler.stream_finished (length: {len(response)})")
        logger.info("\n" + "="*60)
        logger.info("测试成功完成!")
        logger.info("="*60)
        # 3秒后退出
        QTimer.singleShot(3000, app.quit)

    def on_stream_error(error):
        logger.error(f"[SIGNAL] StreamingHandler.stream_error: {error}")
        # 1秒后退出
        QTimer.singleShot(1000, app.quit)

    # 连接调试信号
    chat_window.message_sent.connect(on_message_sent)
    if chat_controller.streaming_handler:
        chat_controller.streaming_handler.stream_started.connect(on_stream_started)
        chat_controller.streaming_handler.chunk_received.connect(on_chunk_received)
        chat_controller.streaming_handler.stream_finished.connect(on_stream_finished)
        chat_controller.streaming_handler.stream_error.connect(on_stream_error)
    else:
        logger.warning("streaming_handler未初始化!")

    # 5秒后自动发送测试消息
    def send_test_message():
        logger.info("\n发送测试消息...")
        # 直接调用内部方法模拟用户输入
        test_msg = "Hello, say hi in 1 sentence"
        test_params = chat_window.get_ai_parameters()

        logger.info(f"消息: {test_msg}")
        logger.info(f"参数: {test_params}")

        # 发射message_sent信号
        chat_window.message_sent.emit(test_msg, test_params)

    QTimer.singleShot(2000, send_test_message)

    # 30秒超时保护
    QTimer.singleShot(30000, lambda: [
        logger.error("测试超时!"),
        app.quit()
    ])

    logger.info("\n" + "="*60)
    logger.info("开始测试 - 窗口已打开")
    logger.info("="*60)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
