# -*- coding: utf-8 -*-
"""
Cross-Component Integration Test
跨组件集成测试：验证 ConfigController, TitleBarModelIndicator, ModelConfigDialog 之间的集成
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal

from components.chat.controllers.config_controller import ConfigController
from components.chat.widgets.title_bar_model_indicator import TitleBarModelIndicator


class SignalSpy(QObject):
    """信号监听器,用于测试信号发射"""

    def __init__(self):
        super().__init__()
        self.signals_received = []

    def on_signal(self, *args):
        """记录收到的信号"""
        self.signals_received.append(args)


def test_config_controller_signals():
    """测试1: ConfigController 信号机制"""
    print("=" * 60)
    print("测试1: ConfigController 信号机制")
    print("=" * 60)

    controller = ConfigController.instance()

    # 创建信号监听器
    model_changed_spy = SignalSpy()
    provider_changed_spy = SignalSpy()

    # 连接信号
    controller.model_changed.connect(model_changed_spy.on_signal)
    controller.provider_changed.connect(provider_changed_spy.on_signal)

    # 测试1.1: 切换模型应该发出 model_changed 信号
    print("\n1.1 测试 model_changed 信号")
    initial_count = len(model_changed_spy.signals_received)
    providers = controller.get_providers()

    if len(providers) >= 2:
        # 切换到第二个 provider 的第一个模型
        provider = providers[1]
        models = provider.get("models", [])
        if models:
            provider_id = provider["id"]
            model_id = models[0]["id"]

            controller.set_current_model(provider_id, model_id)

            if len(model_changed_spy.signals_received) > initial_count:
                received_args = model_changed_spy.signals_received[-1]
                if received_args == (provider_id, model_id):
                    print(f"  [OK] model_changed 信号正确发出: {provider_id}/{model_id}")
                else:
                    print(f"  [FAIL] 信号参数错误: expected ({provider_id}, {model_id}), got {received_args}")
            else:
                print("  [FAIL] model_changed 信号未发出")
        else:
            print("  [SKIP] Provider 没有模型")
    else:
        print("  [SKIP] Providers 数量不足")

    # 测试1.2: 更新 provider 应该发出 provider_changed 信号
    print("\n1.2 测试 provider_changed 信号")
    initial_count = len(provider_changed_spy.signals_received)

    if len(providers) > 0:
        provider = providers[0].copy()
        provider_id = provider["id"]
        provider["enabled"] = not provider.get("enabled", True)

        controller.update_provider(provider_id, provider)

        if len(provider_changed_spy.signals_received) > initial_count:
            received_args = provider_changed_spy.signals_received[-1]
            if received_args == (provider_id,):
                print(f"  [OK] provider_changed 信号正确发出: {provider_id}")
            else:
                print(f"  [FAIL] 信号参数错误: got {received_args}")
        else:
            print("  [FAIL] provider_changed 信号未发出")
    else:
        print("  [SKIP] 没有 providers")

    # 清理
    controller.model_changed.disconnect(model_changed_spy.on_signal)
    controller.provider_changed.disconnect(provider_changed_spy.on_signal)


def test_title_bar_indicator_integration():
    """测试2: TitleBarModelIndicator 与 ConfigController 集成"""
    print("\n" + "=" * 60)
    print("测试2: TitleBarModelIndicator 与 ConfigController 集成")
    print("=" * 60)

    controller = ConfigController.instance()
    indicator = TitleBarModelIndicator()

    # 测试2.1: Indicator 应该显示当前模型
    print("\n2.1 测试 Indicator 显示当前模型")
    provider_id, model_id = controller.get_current_model()

    # 获取 provider 和 model 信息
    provider = controller.get_provider(provider_id)
    if provider:
        provider_name = provider.get("name", "")
        models = provider.get("models", [])
        model_name = next((m["name"] for m in models if m["id"] == model_id), "")

        # 检查 indicator 显示
        indicator_model = indicator.model_label.text()
        indicator_provider = indicator.provider_label.text()

        if indicator_model == model_name and indicator_provider == provider_name:
            print(f"  [OK] Indicator 正确显示: {model_name} | {provider_name}")
        else:
            print(f"  [FAIL] Indicator 显示错误:")
            print(f"    期望: {model_name} | {provider_name}")
            print(f"    实际: {indicator_model} | {indicator_provider}")
    else:
        print("  [FAIL] 无法获取 provider 信息")

    # 测试2.2: 切换模型时 Indicator 应该更新
    print("\n2.2 测试模型切换时 Indicator 更新")
    providers = controller.get_providers()

    if len(providers) >= 2:
        # 切换到不同的 provider
        new_provider = providers[1] if providers[0]["id"] == provider_id else providers[0]
        new_provider_id = new_provider["id"]
        new_provider_name = new_provider["name"]

        models = new_provider.get("models", [])
        if models:
            new_model_id = models[0]["id"]
            new_model_name = models[0]["name"]

            # 切换模型
            controller.set_current_model(new_provider_id, new_model_id)

            # 检查 indicator 是否更新
            indicator_model = indicator.model_label.text()
            indicator_provider = indicator.provider_label.text()

            if indicator_model == new_model_name and indicator_provider == new_provider_name:
                print(f"  [OK] Indicator 正确更新: {new_model_name} | {new_provider_name}")
            else:
                print(f"  [FAIL] Indicator 未正确更新:")
                print(f"    期望: {new_model_name} | {new_provider_name}")
                print(f"    实际: {indicator_model} | {indicator_provider}")
        else:
            print("  [SKIP] 新 provider 没有模型")
    else:
        print("  [SKIP] Providers 数量不足")

    # 清理
    indicator.deleteLater()


def test_search_engine_integration():
    """测试3: SearchEngine 与 ConfigController 集成"""
    print("\n" + "=" * 60)
    print("测试3: SearchEngine 集成")
    print("=" * 60)

    from components.chat.services.search_engine import SearchEngine

    controller = ConfigController.instance()
    providers = controller.get_providers()

    # 测试3.1: 搜索 provider 名称
    print("\n3.1 测试搜索 provider 名称")
    if len(providers) > 0:
        first_provider = providers[0]
        search_query = first_provider["name"][:2]  # 搜索前两个字符

        matched_providers, model_matches = SearchEngine.search(search_query, providers)

        if first_provider["id"] in matched_providers:
            print(f"  [OK] 搜索 '{search_query}' 找到 provider: {first_provider['name']}")
        else:
            print(f"  [FAIL] 搜索 '{search_query}' 未找到 provider: {first_provider['name']}")
    else:
        print("  [SKIP] 没有 providers")

    # 测试3.2: 搜索 model 名称
    print("\n3.2 测试搜索 model 名称")
    for provider in providers:
        models = provider.get("models", [])
        if models:
            first_model = models[0]
            model_name = first_model.get("name", "")
            if len(model_name) >= 2:
                search_query = model_name[:3]  # 搜索前三个字符

                matched_providers, model_matches = SearchEngine.search(search_query, providers)

                # 检查是否找到该 provider
                if provider["id"] in matched_providers:
                    # 检查是否找到该 model
                    if provider["id"] in model_matches:
                        matched_models = model_matches[provider["id"]]
                        if first_model["id"] in matched_models:
                            print(f"  [OK] 搜索 '{search_query}' 找到 model: {model_name}")
                        else:
                            print(f"  [FAIL] 搜索 '{search_query}' 未找到 model: {model_name}")
                    else:
                        print(f"  [FAIL] Provider {provider['id']} 没有匹配的 models")
                else:
                    print(f"  [FAIL] 搜索 '{search_query}' 未找到 provider")
                break
    else:
        print("  [SKIP] 没有模型可搜索")

    # 测试3.3: 大小写不敏感
    print("\n3.3 测试大小写不敏感搜索")
    if len(providers) > 0:
        first_provider = providers[0]
        provider_name = first_provider["name"]
        if provider_name:
            # 使用大写搜索
            upper_query = provider_name[:2].upper()
            matched_providers, _ = SearchEngine.search(upper_query, providers)

            if first_provider["id"] in matched_providers:
                print(f"  [OK] 大写搜索 '{upper_query}' 成功匹配")
            else:
                print(f"  [FAIL] 大写搜索 '{upper_query}' 未匹配")
    else:
        print("  [SKIP] 没有 providers")


def test_api_test_service():
    """测试4: APITestService 集成"""
    print("\n" + "=" * 60)
    print("测试4: APITestService 信号机制")
    print("=" * 60)

    from components.chat.services.api_test_service import APITestService

    service = APITestService.instance()

    # 创建信号监听器
    progress_spy = SignalSpy()
    finished_spy = SignalSpy()

    # 连接信号
    service.progress_update.connect(progress_spy.on_signal)
    service.test_finished.connect(finished_spy.on_signal)

    # 测试信号连接
    print("\n4.1 测试信号连接")
    print("  [OK] APITestService 信号已连接")
    print("  [INFO] 实际 API 测试需要有效的 API 密钥和网络连接")
    print("  [INFO] 建议使用 GUI 测试进行手动验证")

    # 清理
    service.progress_update.disconnect(progress_spy.on_signal)
    service.test_finished.disconnect(finished_spy.on_signal)


def main():
    """主函数"""
    print("\n")
    print("=" * 60)
    print("跨组件集成测试")
    print("=" * 60)

    # 创建 QApplication 实例
    app = QApplication(sys.argv)

    # 运行测试
    test_config_controller_signals()
    test_title_bar_indicator_integration()
    test_search_engine_integration()
    test_api_test_service()

    print("\n" + "=" * 60)
    print("跨组件集成测试完成")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
