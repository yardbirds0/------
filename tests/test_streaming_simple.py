# -*- coding: utf-8 -*-
"""
简单流式输出测试 - 无GUI
"""

import sys
import logging
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def main():
    print("\n" + "=" * 60)
    print("测试流式输出（无GUI）")
    print("=" * 60 + "\n")

    from modules.ai_integration import OpenAIProvider, ProviderConfig, ChatMessage

    # 配置
    config = ProviderConfig(
        api_key="UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t",
        base_url="https://api.kkyyxx.xyz/v1",
        model="gemini-2.5-pro",
        temperature=0.3,
        max_tokens=100,
        timeout=30
    )

    provider = OpenAIProvider(config)

    # 测试消息
    messages = [
        ChatMessage(role='user', content='Say hello in one sentence')
    ]

    print(f"发送消息: {messages[0].content}\n")
    print("接收流式响应:")
    print("-" * 60)

    try:
        chunk_count = 0
        full_response = ""

        for chunk in provider.stream_message(messages, system_prompt="You are a friendly assistant."):
            chunk_count += 1
            full_response += chunk
            print(f"[{chunk_count:02d}] {chunk}", end='', flush=True)

        print("\n" + "-" * 60)
        print(f"\n完成! 共{chunk_count}个chunk, 总长度{len(full_response)}字符")
        print(f"\n完整响应:\n{full_response}")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
