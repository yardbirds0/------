#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提供商列表最终修复测试
验证:
1. 文字垂直居中对齐
2. 圆角背景效果
3. 悬浮变灰效果
4. 选中时文字加粗
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Qt
from components.chat.widgets.model_config_dialog import ProviderListItemWidget
from components.chat.styles.cherry_theme import COLORS


def main():
    """运行最终修复测试"""
    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("提供商列表最终修复测试")
    window.setGeometry(100, 100, 450, 600)

    layout = QVBoxLayout(window)
    layout.setContentsMargins(20, 20, 20, 20)

    # 说明标签
    info_label = QLabel(
        "请验证以下改进:\n\n"
        "1. [对齐] 文字垂直居中,不超出灰色边框\n"
        "2. [圆角] 列表项有6px圆角\n"
        "3. [悬浮] 鼠标悬浮时整行变浅灰色 (#F5F5F5)\n"
        "4. [选中] 点击选中时:\n"
        "   - 整行变灰色 (#F0F0F0)\n"
        "   - 文字加粗显示\n"
        "5. [间距] 列表项之间有适当间距\n"
    )
    info_label.setStyleSheet(f"""
        QLabel {{
            color: {COLORS['text_primary']};
            padding: 15px;
            background-color: #FFF9E6;
            border-radius: 6px;
            border: 1px solid #FFE58F;
        }}
    """)
    layout.addWidget(info_label)

    # 创建提供商列表
    provider_list = QListWidget()
    provider_list.setSpacing(0)  # 移除spacing，改用item的margin
    provider_list.setStyleSheet(f"""
        QListWidget {{
            background-color: #FFFFFF;
            border: none;
            padding: 4px;
        }}
        QListWidget::item {{
            background-color: transparent;
            border: none;
            padding: 0px;
            margin: 2px 0px;
            border-radius: 6px;
        }}
        QListWidget::item:hover {{
            background-color: #F5F5F5;
        }}
        QListWidget::item:selected {{
            background-color: #F0F0F0;
        }}
    """)

    # 监听选中状态变化，实现文字加粗
    def on_selection_changed():
        for i in range(provider_list.count()):
            item = provider_list.item(i)
            widget = provider_list.itemWidget(item)
            if isinstance(widget, ProviderListItemWidget):
                is_selected = item.isSelected()
                widget.set_selected(is_selected)

    provider_list.itemSelectionChanged.connect(on_selection_changed)

    # 添加测试数据
    test_providers = [
        ("openai", "OpenAI", True),
        ("anthropic", "Anthropic", True),
        ("gemini", "Gemini", False),
        ("deepseek", "DeepSeek", True),
        ("doubao", "Doubao", False),
        ("qwen", "Qwen", True),
        ("baai", "BAAI", False),
    ]

    for provider_id, provider_name, enabled in test_providers:
        widget = ProviderListItemWidget(provider_id, provider_name, enabled)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        provider_list.addItem(item)
        provider_list.setItemWidget(item, widget)

    layout.addWidget(provider_list)

    window.show()

    print("=" * 80)
    print("提供商列表最终修复测试")
    print("=" * 80)
    print("\n请在窗口中验证:")
    print("1. [OK] 文字垂直居中,不超出灰色边框")
    print("2. [OK] 列表项有6px圆角")
    print("3. [OK] 悬浮时整行变浅灰色 (#F5F5F5)")
    print("4. [OK] 选中时整行变灰色 (#F0F0F0)且文字加粗")
    print("5. [OK] 列表项之间有2px间距\n")
    print("修复要点:")
    print("  - widget高度: 44px")
    print("  - 上下margins: 8px")
    print("  - item margin: 2px 0px")
    print("  - border-radius: 6px")
    print("  - 选中时文字Bold\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
