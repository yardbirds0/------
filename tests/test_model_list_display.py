#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试模型列表显示
验证:
1. 模型列表正确显示内置模型
2. 分类卡片按正确顺序排列
3. 分类卡片可折叠
4. 所有样式正确（无边框、圆角背景等）
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMessageBox
from components.chat.widgets.model_config_dialog import ModelConfigDialog


def main():
    """运行模型列表显示测试"""
    app = QApplication(sys.argv)

    print("=" * 80)
    print("模型列表显示测试")
    print("=" * 80)
    print("\n关键验证点:")
    print("1. [分类] 模型按以下顺序分类:")
    print("   DeepSeek, Anthropic, Doubao, Embedding,")
    print("   Openai, Gemini, Gemma, Llama-3.2, BAAI, Qwen")
    print("2. [卡片] 每个分类使用卡片包裹，显示分类名称和模型数量")
    print("3. [折叠] 点击分类标题可折叠/展开模型列表")
    print("4. [样式] 无边框、无下划线，悬浮时灰色背景")
    print("5. [圆角] Provider列表悬浮/选中时显示圆角灰色背景")
    print("\n操作指南:")
    print("- 默认选中 '硅基流动' provider")
    print("- 查看右侧模型列表是否显示所有分类卡片")
    print("- 尝试点击分类标题折叠/展开")
    print("- 切换不同provider查看对应模型")
    print("- 验证悬浮/选中效果")
    print("\n" + "=" * 80 + "\n")

    # 创建并显示对话框
    dialog = ModelConfigDialog()

    # 显示说明
    QMessageBox.information(
        None,
        "测试说明",
        "请验证以下内容:\n\n"
        "1. 模型列表显示了所有分类（DeepSeek, Qwen等）\n"
        "2. 每个分类卡片可以折叠/展开\n"
        "3. Provider列表有圆角灰色背景效果\n"
        "4. 所有样式符合要求（无边框、灰色悬浮）\n\n"
        "点击OK开始测试"
    )

    result = dialog.exec()

    if result:
        print("\n[OK] 用户点击了应用")
    else:
        print("\n[CANCEL] 用户取消了")

    print("\n模型列表显示测试完成")
    sys.exit(0)


if __name__ == "__main__":
    main()
