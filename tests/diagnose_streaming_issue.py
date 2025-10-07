# -*- coding: utf-8 -*-
"""
诊断流式响应问题的测试脚本
追踪整个流程并输出详细日志
"""

import sys
import logging
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_api_connection():
    """测试API连接"""
    from modules.ai_integration.api_providers import OpenAIProvider
    from modules.ai_integration.api_providers.base_provider import ProviderConfig

    logger.info("=" * 60)
    logger.info("步骤 1: 测试 API 连接")
    logger.info("=" * 60)

    config = ProviderConfig(
        api_key="UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t",
        base_url="https://api.kkyyxx.xyz/v1",
        model="gemini-2.5-pro",
        temperature=0.3,
        max_tokens=2000,
        timeout=30
    )

    logger.info(f"配置信息:")
    logger.info(f"  - API Key: {config.api_key[:20]}...")
    logger.info(f"  - Base URL: {config.base_url}")
    logger.info(f"  - Model: {config.model}")

    provider = OpenAIProvider(config)

    logger.info("\n正在验证连接...")
    success, message = provider.validate_connection()

    if success:
        logger.info(f"✅ {message}")
        return provider
    else:
        logger.error(f"❌ {message}")
        return None


def test_stream_response(provider):
    """测试流式响应"""
    from modules.ai_integration.api_providers.base_provider import ChatMessage

    logger.info("\n" + "=" * 60)
    logger.info("步骤 2: 测试流式响应")
    logger.info("=" * 60)

    messages = [
        ChatMessage(role='user', content='Say hello in 1-2 sentences')
    ]

    logger.info(f"\n发送测试消息: {messages[0].content}")
    logger.info("正在等待流式响应...\n")

    try:
        chunk_count = 0
        full_response = ""

        stream_iterator = provider.stream_message(
            messages,
            system_prompt="You are a friendly assistant."
        )

        logger.info("📡 开始接收流式响应:")
        logger.info("-" * 60)

        for chunk in stream_iterator:
            chunk_count += 1
            full_response += chunk

            # 显示每个chunk（带序号）
            print(f"[Chunk {chunk_count:03d}] {repr(chunk)}", flush=True)

        logger.info("-" * 60)
        logger.info(f"\n✅ 流式响应完成:")
        logger.info(f"  - 总chunk数: {chunk_count}")
        logger.info(f"  - 响应长度: {len(full_response)} 字符")
        logger.info(f"\n完整响应:\n{full_response}")

        return True

    except Exception as e:
        logger.error(f"\n❌ 流式响应失败:")
        logger.error(f"  - 异常类型: {type(e).__name__}")
        logger.error(f"  - 错误信息: {str(e)}")
        logger.exception("详细堆栈:")
        return False


def test_streaming_handler():
    """测试StreamingHandler"""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from modules.ai_integration import StreamingHandler, ChatManager
    from modules.ai_integration.api_providers import OpenAIProvider
    from modules.ai_integration.api_providers.base_provider import ProviderConfig, ChatMessage

    logger.info("\n" + "=" * 60)
    logger.info("步骤 3: 测试 StreamingHandler + Qt信号")
    logger.info("=" * 60)

    app = QApplication.instance() or QApplication(sys.argv)

    # 配置
    config = ProviderConfig(
        api_key="UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t",
        base_url="https://api.kkyyxx.xyz/v1",
        model="gemini-2.5-pro",
        temperature=0.3,
        max_tokens=2000,
        timeout=30
    )

    provider = OpenAIProvider(config)
    streaming_handler = StreamingHandler(provider)
    chat_manager = ChatManager()

    # 测试状态
    test_state = {
        'started': False,
        'chunks': [],
        'finished': False,
        'error': None
    }

    # 连接信号
    def on_started():
        test_state['started'] = True
        logger.info("🔔 信号: stream_started")

    def on_chunk(chunk):
        test_state['chunks'].append(chunk)
        chunk_num = len(test_state['chunks'])
        logger.info(f"🔔 信号: chunk_received #{chunk_num}: {repr(chunk[:50])}")

    def on_finished(response):
        test_state['finished'] = True
        logger.info(f"🔔 信号: stream_finished (长度: {len(response)} 字符)")

        # 验证结果
        logger.info("\n" + "=" * 60)
        logger.info("测试结果:")
        logger.info("=" * 60)
        logger.info(f"✅ stream_started: {test_state['started']}")
        logger.info(f"✅ chunks received: {len(test_state['chunks'])}")
        logger.info(f"✅ stream_finished: {test_state['finished']}")
        logger.info(f"✅ no errors: {test_state['error'] is None}")

        # 3秒后退出
        QTimer.singleShot(3000, app.quit)

    def on_error(error):
        test_state['error'] = error
        logger.error(f"🔔 信号: stream_error: {error}")
        QTimer.singleShot(1000, app.quit)

    streaming_handler.stream_started.connect(on_started)
    streaming_handler.chunk_received.connect(on_chunk)
    streaming_handler.stream_finished.connect(on_finished)
    streaming_handler.stream_error.connect(on_error)

    # 发送消息
    user_msg = "Say hello in 1-2 sentences"
    chat_manager.add_message('user', user_msg)
    messages = chat_manager.get_context_messages()

    logger.info(f"\n发送测试消息: {user_msg}")
    streaming_handler.start_stream(messages, system_prompt="You are a friendly assistant.")

    # 30秒超时保护
    QTimer.singleShot(30000, lambda: [
        logger.error("⏱️ 超时: 测试超过30秒"),
        app.quit()
    ])

    logger.info("等待Qt事件循环...\n")
    sys.exit(app.exec())


def main():
    """主测试流程"""
    logger.info("\n" + "=" * 70)
    logger.info("AI Streaming Diagnosis Tool")
    logger.info("=" * 70)

    # 测试1: API连接
    provider = test_api_connection()
    if not provider:
        logger.error("\n❌ API连接失败，停止后续测试")
        return

    # 测试2: 原始流式响应
    if not test_stream_response(provider):
        logger.error("\n❌ 流式响应测试失败，停止后续测试")
        return

    # 测试3: StreamingHandler + Qt
    logger.info("\n准备测试 StreamingHandler...")
    input("\n按回车键继续测试StreamingHandler（需要Qt窗口）...")
    test_streaming_handler()


if __name__ == '__main__':
    main()
