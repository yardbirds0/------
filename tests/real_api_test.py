# -*- coding: utf-8 -*-
"""
Real API Integration Test
真实API集成测试 - 实际调用Gemini转发服务

这个脚本会向用户提供的API发送真实请求
用户可以在后台日志中看到实际的HTTP请求
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.ai_integration.providers.openai_service import OpenAIService
from modules.ai_integration.config_loader import AIConfigLoader


async def test_basic_request():
    """测试1: 基础请求 - 简单问答"""
    print("\n" + "="*60)
    print("测试1: 基础请求测试")
    print("="*60)

    # 使用空配置，会自动使用内置的默认配置
    service = OpenAIService({})

    print(f"\n[OK] 服务初始化成功")
    print(f"  - API URL: {service.config.base_url}")
    print(f"  - Model: {service.config.model}")
    print(f"  - API Key: {service.config.api_key[:20]}...")

    print(f"\n正在发送请求到: {service.config.base_url}/chat/completions")
    print(f"问题: 你好，请介绍一下你自己\n")

    try:
        # 发送真实请求
        full_response = ""
        async for chunk in service.send_message(
            prompt="你好，请介绍一下你自己",
            context=[],
            streaming=True
        ):
            print(chunk, end='', flush=True)
            full_response += chunk

        print(f"\n\n[OK] 请求成功!")
        print(f"  - 响应长度: {len(full_response)} 字符")
        print(f"  - Token估算: {service.estimate_tokens(full_response)} tokens")

        return True

    except Exception as e:
        print(f"\n[FAIL] 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streaming_output():
    """测试2: 流式输出 - 验证逐字符显示"""
    print("\n" + "="*60)
    print("测试2: 流式输出测试")
    print("="*60)

    service = OpenAIService({})

    print(f"\n问题: 用一句话解释什么是人工智能\n")

    try:
        chunk_count = 0
        start_time = asyncio.get_event_loop().time()

        async for chunk in service.send_message(
            prompt="用一句话解释什么是人工智能",
            context=[],
            streaming=True,
            max_tokens=100
        ):
            print(chunk, end='', flush=True)
            chunk_count += 1

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        print(f"\n\n[OK] 流式输出成功!")
        print(f"  - 接收到 {chunk_count} 个chunk")
        print(f"  - 耗时: {duration:.2f} 秒")
        print(f"  - 平均延迟: {duration/chunk_count*1000:.1f} ms/chunk")

        return True

    except Exception as e:
        print(f"\n[FAIL] 流式输出失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_context_conversation():
    """测试3: 上下文对话 - 多轮对话"""
    print("\n" + "="*60)
    print("测试3: 上下文对话测试")
    print("="*60)

    service = OpenAIService({})

    # 第一轮对话
    print(f"\n【第1轮】用户: 我喜欢编程\n")

    context = []

    try:
        response1 = ""
        async for chunk in service.send_message(
            prompt="我喜欢编程",
            context=context,
            streaming=True,
            max_tokens=50
        ):
            print(chunk, end='', flush=True)
            response1 += chunk

        # 更新上下文
        context.append({"role": "user", "content": "我喜欢编程"})
        context.append({"role": "assistant", "content": response1})

        # 第二轮对话
        print(f"\n\n【第2轮】用户: 我最喜欢的语言是什么？\n")

        response2 = ""
        async for chunk in service.send_message(
            prompt="我最喜欢的语言是什么？",
            context=context,
            streaming=True,
            max_tokens=50
        ):
            print(chunk, end='', flush=True)
            response2 += chunk

        print(f"\n\n[OK] 上下文对话成功!")
        print(f"  - 对话轮次: 2")
        print(f"  - 上下文长度: {len(context) + 2} 条消息")

        return True

    except Exception as e:
        print(f"\n[FAIL] 上下文对话失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_parameter_customization():
    """测试4: 参数自定义 - temperature, max_tokens等"""
    print("\n" + "="*60)
    print("测试4: 参数自定义测试")
    print("="*60)

    service = OpenAIService({})

    print(f"\n问题: 写一个Python函数计算斐波那契数列")
    print(f"参数: temperature=0.2, max_tokens=200\n")

    try:
        response = ""
        async for chunk in service.send_message(
            prompt="写一个Python函数计算斐波那契数列的第n项",
            context=[],
            streaming=True,
            temperature=0.2,  # 低温度，更确定性
            max_tokens=200
        ):
            print(chunk, end='', flush=True)
            response += chunk

        print(f"\n\n[OK] 参数自定义成功!")
        print(f"  - 响应包含代码: {'def' in response or 'function' in response}")

        return True

    except Exception as e:
        print(f"\n[FAIL] 参数自定义失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_config_loader():
    """测试5: 配置加载器 - 验证配置文件读写"""
    print("\n" + "="*60)
    print("测试5: 配置加载器测试")
    print("="*60)

    loader = AIConfigLoader()

    # 加载配置
    config = loader.load_config()

    print(f"\n[OK] 配置加载成功")
    print(f"  - 激活服务: {config['active_service']}")
    print(f"  - 可用服务: {', '.join(config['services'].keys())}")

    # 获取OpenAI服务配置
    openai_config = loader.get_service_config('openai')

    print(f"\n[OK] OpenAI服务配置:")
    print(f"  - API URL: {openai_config['base_url']}")
    print(f"  - Model: {openai_config['model']}")
    print(f"  - Description: {openai_config.get('description', 'N/A')}")

    # 列出所有服务
    services = loader.list_services()

    print(f"\n[OK] 所有可用服务:")
    for name, desc in services.items():
        print(f"  - {name}: {desc}")

    return True


async def main():
    """运行所有真实API测试"""
    print("\n" + "="*60)
    print("OpenAI服务真实API集成测试")
    print("API Provider: Gemini 2.5 Pro (via OpenAI-compatible forwarding)")
    print("="*60)

    results = []

    # 测试1: 基础请求
    results.append(("基础请求", await test_basic_request()))

    # 测试2: 流式输出
    results.append(("流式输出", await test_streaming_output()))

    # 测试3: 上下文对话
    results.append(("上下文对话", await test_context_conversation()))

    # 测试4: 参数自定义
    results.append(("参数自定义", await test_parameter_customization()))

    # 测试5: 配置加载器
    results.append(("配置加载器", await test_config_loader()))

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} - {name}")

    total = len(results)
    passed = sum(1 for _, success in results if success)

    print(f"\n总计: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n所有测试通过! OpenAI服务集成成功!")
        return 0
    else:
        print(f"\n{total - passed} 个测试失败，请检查")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
