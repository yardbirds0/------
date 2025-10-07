#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
US4.2 Search Engine 性能测试
测试20+个providers的搜索性能（要求<100ms）
"""

import sys
from pathlib import Path
import io
import time

# 设置标准输出编码为UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.chat.services import SearchEngine


def generate_large_provider_list(num_providers=25):
    """
    生成大量providers用于性能测试

    Args:
        num_providers: Provider数量（默认25）

    Returns:
        List[dict]: Provider列表
    """
    providers = []

    for i in range(num_providers):
        provider_id = f"provider_{i}"
        provider_name = f"Provider {i}"

        # 每个provider有5-10个models
        models = []
        num_models = 5 + (i % 6)  # 5-10个models

        for j in range(num_models):
            model_id = f"model_{i}_{j}"
            model_name = f"Model {i}.{j}"
            models.append({"id": model_id, "name": model_name})

        providers.append(
            {"id": provider_id, "name": provider_name, "models": models}
        )

    return providers


def measure_search_performance(providers, query, iterations=10):
    """
    测量搜索性能

    Args:
        providers: Provider列表
        query: 搜索查询
        iterations: 迭代次数

    Returns:
        tuple: (avg_time_ms, min_time_ms, max_time_ms)
    """
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        SearchEngine.search(query, providers)
        end = time.perf_counter()

        elapsed_ms = (end - start) * 1000
        times.append(elapsed_ms)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    return avg_time, min_time, max_time


def main():
    """运行性能测试"""
    print("=" * 80)
    print("US4.2 SearchEngine 性能测试")
    print("=" * 80)

    # 生成25个providers，每个有5-10个models（总共约187个models）
    num_providers = 25
    providers = generate_large_provider_list(num_providers)

    total_models = sum(len(p.get("models", [])) for p in providers)
    print(f"\n测试数据规模:")
    print(f"  • Providers: {num_providers}")
    print(f"  • 总Models: {total_models}")

    print(f"\n性能要求: < 100ms (US4.2 AC8)")
    print("=" * 80)

    # 测试场景
    test_cases = [
        ("空查询", ""),
        ("Provider名称匹配", "Provider 10"),
        ("Model匹配", "Model 5"),
        ("部分匹配", "5"),
        ("无匹配", "nonexistent"),
    ]

    all_passed = True
    results = []

    for test_name, query in test_cases:
        avg, min_t, max_t = measure_search_performance(providers, query, iterations=10)

        passed = avg < 100  # 要求平均时间 < 100ms
        status = "✅ PASS" if passed else "❌ FAIL"

        print(f"\n{test_name}:")
        print(f"  查询: '{query}'")
        print(f"  平均: {avg:.2f}ms")
        print(f"  最小: {min_t:.2f}ms")
        print(f"  最大: {max_t:.2f}ms")
        print(f"  状态: {status}")

        results.append(
            {
                "test": test_name,
                "avg": avg,
                "min": min_t,
                "max": max_t,
                "passed": passed,
            }
        )

        if not passed:
            all_passed = False

    # 汇总结果
    print("\n" + "=" * 80)
    print("性能测试汇总")
    print("=" * 80)

    print(f"\n{'测试场景':<20} {'平均(ms)':<12} {'最小(ms)':<12} {'最大(ms)':<12} {'状态':<8}")
    print("-" * 80)

    for result in results:
        print(
            f"{result['test']:<20} "
            f"{result['avg']:<12.2f} "
            f"{result['min']:<12.2f} "
            f"{result['max']:<12.2f} "
            f"{'✅' if result['passed'] else '❌':<8}"
        )

    print("-" * 80)

    # 计算整体统计
    avg_of_avgs = sum(r["avg"] for r in results) / len(results)
    print(f"\n总体平均响应时间: {avg_of_avgs:.2f}ms")

    passed_count = sum(1 for r in results if r["passed"])
    print(f"通过测试: {passed_count}/{len(results)}")

    print("\n" + "=" * 80)

    if all_passed:
        print("✅ 所有性能测试通过！搜索响应时间符合US4.2要求（<100ms）")
        print("=" * 80)
        return 0
    else:
        print("❌ 部分性能测试未通过，需要优化")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
