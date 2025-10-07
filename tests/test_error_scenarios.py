# -*- coding: utf-8 -*-
"""
Error Scenarios Test
错误场景测试：配置文件损坏、网络故障、无效输入等
"""

import sys
import json
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from components.chat.controllers.config_controller import ConfigController


def backup_config():
    """备份配置文件"""
    config_path = Path("config/ai_models.json")
    backup_path = Path("config/ai_models.json.test_backup")

    if config_path.exists():
        shutil.copy2(config_path, backup_path)
        return True
    return False


def restore_config():
    """恢复配置文件"""
    config_path = Path("config/ai_models.json")
    backup_path = Path("config/ai_models.json.test_backup")

    if backup_path.exists():
        shutil.copy2(backup_path, config_path)
        backup_path.unlink()
        return True
    return False


def test_corrupted_json():
    """测试1: 损坏的 JSON 配置文件"""
    print("=" * 60)
    print("测试1: 损坏的 JSON 配置文件")
    print("=" * 60)

    config_path = Path("config/ai_models.json")

    # 备份原配置
    if not backup_config():
        print("  [SKIP] 配置文件不存在,跳过测试")
        return

    try:
        # 写入损坏的 JSON
        print("\n1.1 创建损坏的 JSON 文件")
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write('{ "invalid json": ')  # 故意不完整

        print("  [OK] 已写入损坏的 JSON")

        # 创建新的 ConfigController 实例(强制重新加载)
        print("\n1.2 测试 ConfigController 错误处理")

        # 监听 config_error 信号
        error_received = []

        def on_error(message):
            error_received.append(message)

        # 需要新建实例才能触发加载
        # 由于是单例,需要先清理
        if ConfigController._instance:
            ConfigController._instance = None

        controller = ConfigController.instance()
        controller.config_error.connect(on_error)

        # 检查是否加载了默认配置
        providers = controller.get_providers()
        if len(providers) > 0:
            print("  [OK] 加载了默认配置")
        else:
            print("  [FAIL] 未加载默认配置")

        # 检查是否有备份文件
        corrupted_path = Path("config/ai_models.json.corrupted")
        if corrupted_path.exists():
            print("  [OK] 已创建损坏文件备份")
            corrupted_path.unlink()  # 清理
        else:
            print("  [INFO] 未创建损坏文件备份")

    finally:
        # 恢复配置
        restore_config()
        print("\n  [INFO] 已恢复原配置文件")


def test_missing_config_file():
    """测试2: 配置文件不存在"""
    print("\n" + "=" * 60)
    print("测试2: 配置文件不存在")
    print("=" * 60)

    config_path = Path("config/ai_models.json")

    # 备份原配置
    if not backup_config():
        print("  [SKIP] 配置文件不存在,跳过测试")
        return

    try:
        # 删除配置文件
        print("\n2.1 删除配置文件")
        config_path.unlink()
        print("  [OK] 已删除配置文件")

        # 重新创建 ConfigController
        print("\n2.2 测试 ConfigController 自动创建默认配置")

        # 清理单例
        if ConfigController._instance:
            ConfigController._instance = None

        controller = ConfigController.instance()

        # 检查是否创建了配置文件
        if config_path.exists():
            print("  [OK] 已自动创建配置文件")
        else:
            print("  [FAIL] 未自动创建配置文件")

        # 检查是否加载了默认配置
        providers = controller.get_providers()
        if len(providers) > 0:
            print(f"  [OK] 加载了默认配置 ({len(providers)} 个 providers)")
        else:
            print("  [FAIL] 未加载默认配置")

        # 检查配置文件内容
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if "version" in config and "providers" in config:
            print("  [OK] 配置文件结构正确")
        else:
            print("  [FAIL] 配置文件结构错误")

    finally:
        # 恢复配置
        restore_config()
        print("\n  [INFO] 已恢复原配置文件")


def test_invalid_model_selection():
    """测试3: 无效的模型选择"""
    print("\n" + "=" * 60)
    print("测试3: 无效的模型选择")
    print("=" * 60)

    # 清理单例,使用备份的配置
    if ConfigController._instance:
        ConfigController._instance = None

    controller = ConfigController.instance()

    # 监听错误信号
    error_received = []

    def on_error(message):
        error_received.append(message)

    controller.config_error.connect(on_error)

    # 测试3.1: 不存在的 provider
    print("\n3.1 测试选择不存在的 provider")
    initial_error_count = len(error_received)

    controller.set_current_model("nonexistent_provider", "nonexistent_model")

    if len(error_received) > initial_error_count:
        print(f"  [OK] 正确发出错误信号: {error_received[-1]}")
    else:
        print("  [FAIL] 未发出错误信号")

    # 验证模型未改变
    provider_id, model_id = controller.get_current_model()
    if provider_id != "nonexistent_provider":
        print("  [OK] 无效选择未改变当前模型")
    else:
        print("  [FAIL] 无效选择改变了当前模型")

    # 测试3.2: 存在的 provider 但不存在的 model
    print("\n3.2 测试选择不存在的 model")
    providers = controller.get_providers()
    if len(providers) > 0:
        valid_provider_id = providers[0]["id"]
        initial_error_count = len(error_received)

        controller.set_current_model(valid_provider_id, "nonexistent_model")

        if len(error_received) > initial_error_count:
            print(f"  [OK] 正确发出错误信号: {error_received[-1]}")
        else:
            print("  [FAIL] 未发出错误信号")
    else:
        print("  [SKIP] 没有 providers")


def test_provider_crud_errors():
    """测试4: Provider CRUD 操作错误"""
    print("\n" + "=" * 60)
    print("测试4: Provider CRUD 操作错误")
    print("=" * 60)

    # 使用当前的 ConfigController
    controller = ConfigController.instance()

    # 测试4.1: 添加重复 ID 的 provider
    print("\n4.1 测试添加重复 ID 的 provider")
    providers = controller.get_providers()
    if len(providers) > 0:
        duplicate_provider = {
            "id": providers[0]["id"],  # 使用已存在的 ID
            "name": "Duplicate Provider",
            "models": []
        }

        try:
            controller.add_provider(duplicate_provider)
            print("  [FAIL] 未抛出异常")
        except ValueError as e:
            print(f"  [OK] 正确抛出异常: {e}")
    else:
        print("  [SKIP] 没有 providers")

    # 测试4.2: 添加缺少必需字段的 provider
    print("\n4.2 测试添加缺少必需字段的 provider")
    invalid_provider = {
        "name": "Invalid Provider"
        # 缺少 'id' 字段
    }

    try:
        controller.add_provider(invalid_provider)
        print("  [FAIL] 未抛出异常")
    except ValueError as e:
        print(f"  [OK] 正确抛出异常: {e}")

    # 测试4.3: 更新不存在的 provider
    print("\n4.3 测试更新不存在的 provider")
    try:
        controller.update_provider("nonexistent_provider", {"name": "Updated"})
        print("  [FAIL] 未抛出异常")
    except ValueError as e:
        print(f"  [OK] 正确抛出异常: {e}")

    # 测试4.4: 删除不存在的 provider
    print("\n4.4 测试删除不存在的 provider")
    try:
        controller.delete_provider("nonexistent_provider")
        print("  [FAIL] 未抛出异常")
    except ValueError as e:
        print(f"  [OK] 正确抛出异常: {e}")


def test_reorder_with_missing_providers():
    """测试5: 重排序时包含不存在的 provider"""
    print("\n" + "=" * 60)
    print("测试5: 重排序时包含不存在的 provider")
    print("=" * 60)

    controller = ConfigController.instance()
    providers = controller.get_providers()

    if len(providers) >= 2:
        # 创建包含不存在 provider 的列表
        provider_ids = [p["id"] for p in providers]
        invalid_order = ["nonexistent_provider"] + provider_ids

        print(f"\n5.1 测试重排序(包含不存在的 provider)")
        print(f"  原始顺序: {provider_ids}")
        print(f"  新顺序(含无效): {invalid_order}")

        controller.reorder_providers(invalid_order)

        # 验证顺序
        reordered_providers = controller.get_providers()
        actual_ids = [p["id"] for p in reordered_providers]

        # 不存在的 provider 应该被忽略
        if actual_ids == provider_ids:
            print("  [OK] 正确忽略不存在的 provider")
        else:
            print(f"  [FAIL] 顺序错误: {actual_ids}")
    else:
        print("  [SKIP] Providers 数量不足")


def main():
    """主函数"""
    print("\n")
    print("=" * 60)
    print("错误场景测试")
    print("=" * 60)

    # 创建 QApplication 实例
    app = QApplication(sys.argv)

    # 运行测试
    test_corrupted_json()
    test_missing_config_file()
    test_invalid_model_selection()
    test_provider_crud_errors()
    test_reorder_with_missing_providers()

    print("\n" + "=" * 60)
    print("错误场景测试完成")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
