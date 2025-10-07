#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
US4.1 单元测试：API Connection Testing Service
测试API测试服务的核心功能
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch
import time
import io

# 设置标准输出编码为UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread
from components.chat.services import APITestService, APITestWorker


def test_api_worker_initialization():
    """测试APITestWorker初始化"""
    print("\n[TEST 1] APITestWorker初始化测试")

    worker = APITestWorker(
        api_url="https://api.example.com/v1",
        api_key="test_key",
        model_id="test_model",
        max_retries=3,
        timeout=10,
    )

    assert worker.api_url == "https://api.example.com/v1"
    assert worker.api_key == "test_key"
    assert worker.model_id == "test_model"
    assert worker.max_retries == 3
    assert worker.timeout == 10

    print("   ✅ Worker初始化成功")
    return True


def test_api_service_singleton():
    """测试APITestService单例模式"""
    print("\n[TEST 2] APITestService单例模式测试")

    service1 = APITestService.instance()
    service2 = APITestService.instance()

    assert service1 is service2
    print("   ✅ 单例模式正确实现")
    return True


def test_api_test_with_mock():
    """测试API测试（使用Mock）"""
    print("\n[TEST 3] API测试（Mock HTTP请求）")

    app = QApplication.instance() or QApplication(sys.argv)

    # 创建worker
    worker = APITestWorker(
        api_url="https://api.example.com/v1",
        api_key="test_key",
        model_id="test_model",
        max_retries=3,
        timeout=1,  # 短超时用于测试
    )

    # 用于收集信号
    progress_signals = []
    finished_signals = []

    worker.progress_update.connect(
        lambda msg, curr, total: progress_signals.append((msg, curr, total))
    )
    worker.test_finished.connect(lambda success, msg: finished_signals.append((success, msg)))

    # Mock requests.post to simulate success
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "Success"

    with patch("requests.post", return_value=mock_response):
        worker.test_connection()

        # 处理事件循环以接收信号
        for _ in range(10):
            app.processEvents()
            time.sleep(0.05)

    # 验证信号
    print(f"   进度信号数量: {len(progress_signals)}")
    print(f"   完成信号数量: {len(finished_signals)}")

    if len(progress_signals) > 0:
        print(f"   第一次进度: {progress_signals[0]}")

    if len(finished_signals) > 0:
        success, message = finished_signals[0]
        print(f"   结果: {'成功' if success else '失败'} - {message}")
        assert success is True
        print("   ✅ API测试成功")
        return True
    else:
        print("   ⚠️ 未收到完成信号")
        return False


def test_api_test_with_retry_mock():
    """测试API测试重试逻辑（使用Mock）"""
    print("\n[TEST 4] API测试重试逻辑（Mock失败后成功）")

    app = QApplication.instance() or QApplication(sys.argv)

    worker = APITestWorker(
        api_url="https://api.example.com/v1",
        api_key="test_key",
        model_id="test_model",
        max_retries=3,
        timeout=1,
    )

    progress_signals = []
    finished_signals = []

    worker.progress_update.connect(
        lambda msg, curr, total: progress_signals.append((msg, curr, total))
    )
    worker.test_finished.connect(lambda success, msg: finished_signals.append((success, msg)))

    # Mock requests.post to simulate 2 failures then success
    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        mock_resp = Mock()
        if call_count <= 2:
            # First 2 attempts fail
            mock_resp.status_code = 500
            mock_resp.text = "Server Error"
        else:
            # Third attempt succeeds
            mock_resp.status_code = 200
            mock_resp.text = "Success"
        return mock_resp

    with patch("requests.post", side_effect=mock_post):
        worker.test_connection()

        # 处理事件循环
        for _ in range(10):
            app.processEvents()
            time.sleep(0.05)

    print(f"   总共调用次数: {call_count}")
    print(f"   进度信号数量: {len(progress_signals)}")
    print(f"   完成信号数量: {len(finished_signals)}")

    # 应该有3次进度更新（3次尝试）
    if len(progress_signals) >= 2:
        print(f"   第1次进度: {progress_signals[0]}")
        print(f"   第2次进度: {progress_signals[1]}")
        if len(progress_signals) >= 3:
            print(f"   第3次进度: {progress_signals[2]}")

    if len(finished_signals) > 0:
        success, message = finished_signals[0]
        print(f"   最终结果: {'成功' if success else '失败'}")
        assert call_count == 3, f"期望3次调用，实际{call_count}次"
        assert success is True, "第3次应该成功"
        print("   ✅ 重试逻辑正确")
        return True
    else:
        print("   ⚠️ 未收到完成信号")
        return False


def test_api_service_thread_management():
    """测试APITestService线程管理"""
    print("\n[TEST 5] APITestService线程管理测试")

    app = QApplication.instance() or QApplication(sys.argv)
    service = APITestService.instance()

    # 确保service处于干净状态
    if service.thread is not None:
        service._cleanup_worker()
        time.sleep(0.5)
        app.processEvents()

    # 用于跟踪信号
    thread_created = [False]
    thread_cleaned = [False]

    # Mock慢速响应，确保我们能观察到线程状态
    def slow_mock_post(*args, **kwargs):
        time.sleep(0.5)  # 延迟0.5秒
        mock_resp = Mock()
        mock_resp.status_code = 200
        return mock_resp

    try:
        with patch("requests.post", side_effect=slow_mock_post):
            # 启动测试
            service.test_api(
                api_url="https://api.example.com/v1",
                api_key="test_key",
                model_id="test_model",
            )

            # 立即检查 - 线程应该已创建
            if service.thread is not None and isinstance(service.thread, QThread):
                thread_created[0] = True
                print("   ✅ 线程已创建")
            else:
                print("   ⚠️  线程未创建")
                return False

            # 验证worker已创建
            if service.worker is not None and isinstance(
                service.worker, APITestWorker
            ):
                print("   ✅ Worker已创建")
            else:
                print("   ⚠️  Worker未创建")
                return False

            # 等待测试完成和清理
            max_wait = 30  # 最多等待3秒
            for i in range(max_wait):
                app.processEvents()
                time.sleep(0.1)
                if service.thread is None:  # 清理完成
                    thread_cleaned[0] = True
                    print(f"   ✅ 线程已清理（耗时{(i+1)*0.1:.1f}秒）")
                    break
            else:
                print("   ⚠️  线程未在预期时间内清理")
                return False

            # 验证最终状态
            if thread_created[0] and thread_cleaned[0]:
                print("   ✅ 线程生命周期管理正确")
                return True
            else:
                print(f"   ⚠️  状态异常 - 创建:{thread_created[0]}, 清理:{thread_cleaned[0]}")
                return False

    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 80)
    print("US4.1 API测试服务单元测试")
    print("=" * 80)

    tests = [
        test_api_worker_initialization,
        test_api_service_singleton,
        test_api_test_with_mock,
        test_api_test_with_retry_mock,
        test_api_service_thread_management,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            results.append((test_func.__name__, False))

    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总:")
    print("=" * 80)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n总计: {passed} 通过, {failed} 失败")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
