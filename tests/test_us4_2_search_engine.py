#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
US4.2 Search Engine 单元测试
Provider/Model Search Engine Testing
"""

import sys
from pathlib import Path
import io

# 设置标准输出编码为UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.chat.services import SearchEngine


# 测试数据
TEST_PROVIDERS = [
    {
        "id": "openai",
        "name": "OpenAI",
        "models": [
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
        ],
    },
    {
        "id": "google",
        "name": "Google",
        "models": [
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
        ],
    },
    {
        "id": "siliconflow",
        "name": "硅基流动",
        "models": [
            {"id": "Qwen/Qwen2.5-7B-Instruct", "name": "Qwen2.5-7B-Instruct"},
            {"id": "Qwen/Qwen2.5-14B-Instruct", "name": "Qwen2.5-14B-Instruct"},
        ],
    },
]


def test_empty_query():
    """测试空查询返回所有内容"""
    print("\n=== 测试1: 空查询 ===")

    matched_providers, model_matches = SearchEngine.search("", TEST_PROVIDERS)

    print(f"匹配的providers: {matched_providers}")
    print(f"Model matches: {model_matches}")

    # 验证：应该返回所有providers
    assert len(matched_providers) == 3, "空查询应返回所有3个providers"
    assert "openai" in matched_providers
    assert "google" in matched_providers
    assert "siliconflow" in matched_providers

    # 验证：每个provider应包含所有models
    assert len(model_matches["openai"]) == 2
    assert len(model_matches["google"]) == 2
    assert len(model_matches["siliconflow"]) == 2

    print("✅ 空查询测试通过")


def test_provider_name_match():
    """测试Provider名称匹配"""
    print("\n=== 测试2: Provider名称匹配 ===")

    matched_providers, model_matches = SearchEngine.search("OpenAI", TEST_PROVIDERS)

    print(f"匹配的providers: {matched_providers}")
    print(f"Model matches: {model_matches}")

    # 验证：只匹配OpenAI
    assert len(matched_providers) == 1
    assert "openai" in matched_providers

    # 验证：OpenAI的所有models都返回（因为provider匹配）
    assert len(model_matches["openai"]) == 2
    assert "gpt-4-turbo" in model_matches["openai"]
    assert "gpt-3.5-turbo" in model_matches["openai"]

    print("✅ Provider名称匹配测试通过")


def test_model_name_match():
    """测试Model名称匹配"""
    print("\n=== 测试3: Model名称匹配 ===")

    matched_providers, model_matches = SearchEngine.search("Gemini", TEST_PROVIDERS)

    print(f"匹配的providers: {matched_providers}")
    print(f"Model matches: {model_matches}")

    # 验证：只匹配Google (因为有Gemini模型)
    assert len(matched_providers) == 1
    assert "google" in matched_providers

    # 验证：只返回匹配的Gemini models
    assert len(model_matches["google"]) == 2
    assert "gemini-2.5-pro" in model_matches["google"]
    assert "gemini-1.5-flash" in model_matches["google"]

    print("✅ Model名称匹配测试通过")


def test_model_id_match():
    """测试Model ID匹配"""
    print("\n=== 测试4: Model ID匹配 ===")

    matched_providers, model_matches = SearchEngine.search("gpt-4", TEST_PROVIDERS)

    print(f"匹配的providers: {matched_providers}")
    print(f"Model matches: {model_matches}")

    # 验证：只匹配OpenAI
    assert len(matched_providers) == 1
    assert "openai" in matched_providers

    # 验证：只返回gpt-4-turbo
    assert len(model_matches["openai"]) == 1
    assert "gpt-4-turbo" in model_matches["openai"]

    print("✅ Model ID匹配测试通过")


def test_case_insensitive():
    """测试大小写不敏感"""
    print("\n=== 测试5: 大小写不敏感 ===")

    # 测试小写查询
    matched_providers1, model_matches1 = SearchEngine.search("openai", TEST_PROVIDERS)

    # 测试大写查询
    matched_providers2, model_matches2 = SearchEngine.search("OPENAI", TEST_PROVIDERS)

    # 测试混合大小写
    matched_providers3, model_matches3 = SearchEngine.search("OpEnAi", TEST_PROVIDERS)

    print(f"小写查询: {matched_providers1}")
    print(f"大写查询: {matched_providers2}")
    print(f"混合查询: {matched_providers3}")

    # 验证：三种查询结果相同
    assert matched_providers1 == matched_providers2 == matched_providers3
    assert model_matches1 == model_matches2 == model_matches3

    print("✅ 大小写不敏感测试通过")


def test_chinese_search():
    """测试中文搜索"""
    print("\n=== 测试6: 中文搜索 ===")

    matched_providers, model_matches = SearchEngine.search("硅基", TEST_PROVIDERS)

    print(f"匹配的providers: {matched_providers}")
    print(f"Model matches: {model_matches}")

    # 验证：匹配硅基流动
    assert len(matched_providers) == 1
    assert "siliconflow" in matched_providers

    # 验证：返回所有models
    assert len(model_matches["siliconflow"]) == 2

    print("✅ 中文搜索测试通过")


def test_partial_match():
    """测试部分匹配"""
    print("\n=== 测试7: 部分匹配 ===")

    matched_providers, model_matches = SearchEngine.search("gpt", TEST_PROVIDERS)

    print(f"匹配的providers: {matched_providers}")
    print(f"Model matches: {model_matches}")

    # 验证：匹配OpenAI (因为有gpt models)
    assert len(matched_providers) == 1
    assert "openai" in matched_providers

    # 验证：返回所有gpt models
    assert len(model_matches["openai"]) == 2
    assert "gpt-4-turbo" in model_matches["openai"]
    assert "gpt-3.5-turbo" in model_matches["openai"]

    print("✅ 部分匹配测试通过")


def test_no_match():
    """测试无匹配结果"""
    print("\n=== 测试8: 无匹配 ===")

    matched_providers, model_matches = SearchEngine.search(
        "nonexistent", TEST_PROVIDERS
    )

    print(f"匹配的providers: {matched_providers}")
    print(f"Model matches: {model_matches}")

    # 验证：无匹配
    assert len(matched_providers) == 0
    assert len(model_matches) == 0

    print("✅ 无匹配测试通过")


def test_highlight_match():
    """测试高亮功能"""
    print("\n=== 测试9: 高亮匹配 ===")

    # 测试基本高亮
    result1 = SearchEngine.highlight_match("OpenAI GPT-4", "gpt")
    print(f"高亮结果1: {result1}")
    assert "<mark>GPT</mark>" in result1

    # 测试多次匹配
    result2 = SearchEngine.highlight_match("GPT-4 and GPT-3.5", "gpt")
    print(f"高亮结果2: {result2}")
    assert result2.count("<mark>") == 2

    # 测试空查询
    result3 = SearchEngine.highlight_match("OpenAI", "")
    print(f"高亮结果3: {result3}")
    assert result3 == "OpenAI"

    print("✅ 高亮功能测试通过")


def test_multiple_providers_match():
    """测试多个providers匹配"""
    print("\n=== 测试10: 多provider匹配 ===")

    # 搜索包含"i"的providers
    matched_providers, model_matches = SearchEngine.search("i", TEST_PROVIDERS)

    print(f"匹配的providers: {matched_providers}")
    print(f"Model matches数量: {len(model_matches)}")

    # 验证：OpenAI 和 硅基流动 都包含"i"
    assert "openai" in matched_providers
    assert "siliconflow" in matched_providers
    # Google不包含"i"但有Gemini模型包含"i"
    assert "google" in matched_providers

    print("✅ 多provider匹配测试通过")


def main():
    """运行所有测试"""
    print("=" * 80)
    print("US4.2 SearchEngine 单元测试")
    print("=" * 80)

    tests = [
        test_empty_query,
        test_provider_name_match,
        test_model_name_match,
        test_model_id_match,
        test_case_insensitive,
        test_chinese_search,
        test_partial_match,
        test_no_match,
        test_highlight_match,
        test_multiple_providers_match,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ 测试失败: {test.__name__}")
            print(f"   错误: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {test.__name__}")
            print(f"   错误: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    print(f"总计: {len(tests)} 个测试")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print("=" * 80)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
