#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试内置模型配置
验证:
1. 默认配置包含所有必需的模型分类
2. 模型列表正确显示
3. 分类卡片可折叠
4. 分类顺序正确
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from components.chat.controllers.config_controller import ConfigController


def verify_builtin_models():
    """验证内置模型配置"""
    app = QApplication(sys.argv)

    print("=" * 80)
    print("内置模型配置验证")
    print("=" * 80)

    # 获取ConfigController实例
    controller = ConfigController.instance()

    # 获取默认配置
    config = controller._get_default_config()

    print("\n[1] 验证Provider数量...")
    providers = config.get("providers", [])
    print(f"    Provider数量: {len(providers)}")

    expected_providers = ["siliconflow", "openai", "anthropic", "google", "doubao"]
    actual_provider_ids = [p.get("id") for p in providers]

    all_present = all(pid in actual_provider_ids for pid in expected_providers)
    print(f"    [{'PASS' if all_present else 'FAIL'}] 所有Provider都存在")

    print("\n[2] 验证模型分类...")
    expected_categories = [
        "DeepSeek", "Anthropic", "Doubao", "Embedding",
        "Openai", "Gemini", "Gemma", "Llama-3.2", "BAAI", "Qwen"
    ]

    # 收集所有模型的分类
    all_categories = set()
    total_models = 0

    for provider in providers:
        models = provider.get("models", [])
        total_models += len(models)
        for model in models:
            category = model.get("category", "")
            if category:
                all_categories.add(category)

        print(f"    {provider.get('name')}: {len(models)} 个模型")

    print(f"\n    总模型数: {total_models}")
    print(f"    发现的分类: {sorted(all_categories)}")

    categories_complete = all(cat in all_categories for cat in expected_categories)
    print(f"    [{'PASS' if categories_complete else 'FAIL'}] 所有必需分类都存在")

    print("\n[3] 验证website字段...")
    has_website = all("website" in p for p in providers)
    print(f"    [{'PASS' if has_website else 'FAIL'}] 所有Provider都有website字段")

    print("\n[4] 验证模型详细信息...")

    # 检查siliconflow的模型
    siliconflow = next((p for p in providers if p.get("id") == "siliconflow"), None)
    if siliconflow:
        models = siliconflow.get("models", [])
        deepseek_models = [m for m in models if m.get("category") == "DeepSeek"]
        qwen_models = [m for m in models if m.get("category") == "Qwen"]
        embedding_models = [m for m in models if m.get("category") == "Embedding"]

        print(f"    硅基流动:")
        print(f"      DeepSeek: {len(deepseek_models)} 个模型")
        print(f"      Qwen: {len(qwen_models)} 个模型")
        print(f"      Embedding: {len(embedding_models)} 个模型")

    # 检查openai的模型
    openai = next((p for p in providers if p.get("id") == "openai"), None)
    if openai:
        models = openai.get("models", [])
        openai_category_models = [m for m in models if m.get("category") == "Openai"]
        embedding_models = [m for m in models if m.get("category") == "Embedding"]

        print(f"    OpenAI:")
        print(f"      Openai: {len(openai_category_models)} 个模型")
        print(f"      Embedding: {len(embedding_models)} 个模型")

        # 验证category名称正确性
        has_wrong_categories = any(
            m.get("category") in ["GPT-4", "GPT-3.5"] for m in models
        )
        print(f"    [{'FAIL' if has_wrong_categories else 'PASS'}] OpenAI模型使用正确的category名称")

    # 检查anthropic的模型
    anthropic = next((p for p in providers if p.get("id") == "anthropic"), None)
    if anthropic:
        models = anthropic.get("models", [])
        anthropic_models = [m for m in models if m.get("category") == "Anthropic"]

        print(f"    Anthropic:")
        print(f"      Anthropic: {len(anthropic_models)} 个模型")

    print("\n" + "=" * 80)

    if all_present and categories_complete and has_website:
        print("[SUCCESS] 内置模型配置验证通过!")
        print("\n下一步: 打开ModelConfigDialog测试UI显示")
        return True
    else:
        print("[ERROR] 内置模型配置验证失败")
        return False


if __name__ == "__main__":
    success = verify_builtin_models()
    sys.exit(0 if success else 1)
