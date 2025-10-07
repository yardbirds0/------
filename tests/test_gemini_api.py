#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Gemini API 转发服务连接
"""

import sys
import os
import io

# 设置UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.ai_integration.api_providers.openai_provider import OpenAIProvider
from modules.ai_integration.api_providers.base_provider import ProviderConfig, ChatMessage

def test_api_connection():
    """测试API连接"""
    print("=" * 60)
    print("🔍 开始测试 Gemini API 转发服务连接...")
    print("=" * 60)

    # 配置信息
    config = ProviderConfig(
        api_key="UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t",
        base_url="https://api.kkyyxx.xyz//v1",
        model="gemini-2.5-pro",
        temperature=0.7,
        max_tokens=1000,
        timeout=30
    )

    print(f"\n📋 配置信息:")
    print(f"  - Base URL: {config.base_url}")
    print(f"  - Model: {config.model}")
    print(f"  - API Key: {config.api_key[:20]}...")
    print(f"  - Temperature: {config.temperature}")
    print(f"  - Max Tokens: {config.max_tokens}")

    # 创建Provider
    provider = OpenAIProvider(config)

    # 测试1: 连接验证
    print("\n" + "=" * 60)
    print("📡 测试1: API连接验证")
    print("=" * 60)

    try:
        is_valid, message = provider.validate_connection()
        if is_valid:
            print(f"✅ 连接成功: {message}")
        else:
            print(f"❌ 连接失败: {message}")
            return False
    except Exception as e:
        print(f"❌ 连接测试异常: {e}")
        return False

    # 测试2: 简单对话
    print("\n" + "=" * 60)
    print("💬 测试2: 基础对话功能")
    print("=" * 60)

    test_messages = [
        ChatMessage(role="user", content="请用一句话介绍你自己")
    ]

    try:
        print(f"\n发送消息: {test_messages[0].content}")
        response = provider.send_message(test_messages)

        print(f"\n✅ 收到响应:")
        print(f"  内容: {response.content[:200]}..." if len(response.content) > 200 else f"  内容: {response.content}")
        print(f"  Tokens: {response.usage.get('total_tokens', 'N/A')}")
        print(f"  模型: {response.model}")

    except Exception as e:
        print(f"❌ 对话测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试3: 流式响应
    print("\n" + "=" * 60)
    print("🌊 测试3: 流式响应功能")
    print("=" * 60)

    stream_messages = [
        ChatMessage(role="user", content="从1数到10")
    ]

    try:
        print(f"\n发送流式请求: {stream_messages[0].content}")
        print("接收中: ", end="", flush=True)

        full_response = ""
        for chunk in provider.stream_message(stream_messages):
            print(chunk, end="", flush=True)
            full_response += chunk

        print(f"\n\n✅ 流式响应完成")
        print(f"  完整内容: {full_response}")

    except Exception as e:
        print(f"\n❌ 流式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试4: 参数测试（通过不同config实例）
    print("\n" + "=" * 60)
    print("⚙️ 测试4: 参数兼容性测试")
    print("=" * 60)

    # 测试低温度
    print(f"\n测试低温度 (0.3):")
    try:
        low_temp_config = ProviderConfig(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            temperature=0.3,
            max_tokens=50
        )
        low_temp_provider = OpenAIProvider(low_temp_config)
        response = low_temp_provider.send_message([ChatMessage(role="user", content="说个数字")])
        print(f"  ✅ 低温度 - 成功: {response.content[:50]}")
    except Exception as e:
        print(f"  ⚠️ 低温度 - 失败: {str(e)[:100]}")

    # 测试高温度
    print(f"\n测试高温度 (0.9):")
    try:
        high_temp_config = ProviderConfig(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            temperature=0.9,
            max_tokens=50
        )
        high_temp_provider = OpenAIProvider(high_temp_config)
        response = high_temp_provider.send_message([ChatMessage(role="user", content="说个数字")])
        print(f"  ✅ 高温度 - 成功: {response.content[:50]}")
    except Exception as e:
        print(f"  ⚠️ 高温度 - 失败: {str(e)[:100]}")

    print("\n" + "=" * 60)
    print("🎉 所有测试完成！API可用")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_api_connection()
    sys.exit(0 if success else 1)
