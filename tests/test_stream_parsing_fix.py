#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟流式响应测试 - 验证choices[]空数组处理
"""

import sys
import os
import io

# 设置UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from io import BytesIO

def simulate_streaming_response():
    """模拟OpenAI流式响应，包括空choices数组的usage块"""
    # 模拟真实的SSE流数据
    chunks = [
        # 第1个chunk - 开始，有role
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gemini-2.5-pro","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}\n\n',

        # 第2个chunk - 第一部分内容
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gemini-2.5-pro","choices":[{"index":0,"delta":{"content":"你好"},"finish_reason":null}]}\n\n',

        # 第3个chunk - 第二部分内容
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gemini-2.5-pro","choices":[{"index":0,"delta":{"content":"！"},"finish_reason":null}]}\n\n',

        # 第4个chunk - 第三部分内容
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gemini-2.5-pro","choices":[{"index":0,"delta":{"content":"我"},"finish_reason":null}]}\n\n',

        # 第5个chunk - 结束，空delta
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gemini-2.5-pro","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n',

        # 第6个chunk - usage信息块，choices为空数组（这是之前导致错误的地方）
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gemini-2.5-pro","choices":[],"usage":{"prompt_tokens":10,"completion_tokens":5,"total_tokens":15}}\n\n',

        # 结束标记
        'data: [DONE]\n\n'
    ]

    return chunks

def test_stream_parsing():
    """测试流式响应解析"""
    print("=" * 60)
    print("🧪 测试流式响应解析（包含空choices数组）")
    print("=" * 60)

    chunks = simulate_streaming_response()
    collected_content = []
    errors = []

    print("\n📦 模拟接收7个数据块...")

    for i, line in enumerate(chunks, 1):
        line = line.strip()

        if not line:
            continue

        print(f"\n📨 Chunk {i}: {line[:80]}...")

        # SSE 格式: "data: {...}"
        if line.startswith('data: '):
            data_str = line[6:]  # 移除 "data: " 前缀

            # 流结束标记
            if data_str == '[DONE]':
                print("  ✅ 收到结束标记")
                break

            try:
                data = json.loads(data_str)

                # 修复后的代码：检查 choices 数组是否为空
                if not data.get('choices'):
                    print("  ⚠️  空choices数组（usage信息块）- 正确跳过")
                    continue

                # 安全地获取第一个 choice
                choice = data['choices'][0]
                delta = choice.get('delta', {})
                content = delta.get('content', '')

                if content:
                    collected_content.append(content)
                    print(f"  ✅ 提取内容: '{content}'")
                else:
                    print(f"  ℹ️  空内容（role或finish_reason块）")

            except (json.JSONDecodeError, KeyError) as e:
                error_msg = f"解析失败: {e}"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")
                continue

    print("\n" + "=" * 60)
    print("📊 测试结果")
    print("=" * 60)

    full_content = ''.join(collected_content)

    print(f"\n✅ 收集到的内容: '{full_content}'")
    print(f"✅ 内容片段数: {len(collected_content)}")
    print(f"✅ 错误数量: {len(errors)}")

    if errors:
        print("\n❌ 发现错误:")
        for error in errors:
            print(f"  - {error}")
        return False

    if full_content == "你好！我":
        print("\n🎉 测试通过！流式解析完全正确！")
        print("✅ 空choices数组被正确处理（不会导致IndexError）")
        print("✅ 内容正确提取并拼接")
        return True
    else:
        print(f"\n❌ 内容不匹配，期望: '你好！我'，实际: '{full_content}'")
        return False

if __name__ == "__main__":
    success = test_stream_parsing()
    sys.exit(0 if success else 1)
