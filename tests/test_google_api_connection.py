#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Google供应商的API连接
验证gemini-2.5-pro模型配置和"检测"按钮功能
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

from PySide6.QtWidgets import QApplication
from components.chat.services import APITestService
from components.chat.controllers.config_controller import ConfigController


def test_google_api_direct():
    """直接测试Google API连接（不通过UI）"""
    print("=" * 80)
    print("Google Gemini 2.5 Pro API连接测试")
    print("=" * 80)

    app = QApplication.instance() or QApplication(sys.argv)

    # 获取配置
    controller = ConfigController.instance()
    google_provider = controller.get_provider("google")

    if not google_provider:
        print("\n[ERROR] 未找到Google供应商配置")
        return 1

    print(f"\n[1] Google供应商配置:")
    print(f"    ID: {google_provider.get('id')}")
    print(f"    名称: {google_provider.get('name')}")
    print(f"    启用状态: {google_provider.get('enabled')}")
    print(f"    API地址: {google_provider.get('api_url')}")
    print(f"    API密钥: {google_provider.get('api_key')[:20]}... (已隐藏)")
    print(f"    模型数量: {len(google_provider.get('models', []))}")

    models = google_provider.get("models", [])
    if models:
        print(f"\n[2] 模型列表:")
        for i, model in enumerate(models):
            print(f"    [{i+1}] {model.get('name')} ({model.get('id')})")
            print(f"        分类: {model.get('category')}")
            print(f"        上下文长度: {model.get('context_length')}")
            print(f"        最大Token: {model.get('max_tokens')}")

    # 测试API连接
    print(f"\n[3] 开始API连接测试:")
    print("    这将向Google API发送测试请求...")
    print("    请等待...\n")

    service = APITestService.instance()

    # 用于收集结果
    test_result = {"success": None, "message": None}

    def on_progress(msg, current, total):
        print(f"    进度: {msg}")

    def on_finished(success, message):
        test_result["success"] = success
        test_result["message"] = message

    service.progress_update.connect(on_progress)
    service.test_finished.connect(on_finished)

    # 启动测试
    service.test_api(
        api_url=google_provider.get("api_url"),
        api_key=google_provider.get("api_key"),
        model_id=models[0].get("id"),
        max_retries=3,
        timeout=10,
    )

    # 等待测试完成
    max_wait = 400  # 最多等待40秒 (考虑3次重试,每次10秒超时)
    import time

    for i in range(max_wait):
        app.processEvents()
        if test_result["success"] is not None:
            break
        time.sleep(0.1)

        # 每5秒输出一次等待状态
        if (i + 1) % 50 == 0:
            print(f"    等待中... ({(i + 1) // 10}秒)")

    # 显示结果
    print("\n" + "=" * 80)
    print("测试结果:")
    print("=" * 80)

    if test_result["success"] is None:
        print("[TIMEOUT] 测试超时，未收到结果")
        return 1
    elif test_result["success"]:
        print(f"[SUCCESS] ✅ {test_result['message']}")
        print("\n配置验证:")
        print(f"  • API地址: {google_provider.get('api_url')} ✅")
        print(f"  • API密钥: 有效 ✅")
        print(f"  • 模型: {models[0].get('id')} ✅")
        print(f"  • 分类: {models[0].get('category')} ✅")
        print("\n「检测」按钮功能正常！")
        return 0
    else:
        print(f"[FAIL] ❌ {test_result['message']}")
        print("\n请检查:")
        print("  1. API地址是否正确")
        print("  2. API密钥是否有效")
        print("  3. 网络连接是否正常")
        print("  4. 模型ID是否支持")
        return 1


def main():
    """运行测试"""
    try:
        return test_google_api_direct()
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
