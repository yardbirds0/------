#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提供商列表可视化测试
验证透明背景和灰色悬浮/选中效果
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
    """运行可视化测试"""
    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("提供商列表样式测试")
    window.setGeometry(100, 100, 400, 500)

    layout = QVBoxLayout(window)
    layout.setContentsMargins(20, 20, 20, 20)

    # 说明标签
    info_label = QLabel("请验证:\n"
                       "1. 悬浮时整行变灰色 (#F5F5F5)\n"
                       "2. 选中时整行变灰色 (#F0F0F0)\n"
                       "3. 文字和图标背景透明,灰色背景覆盖整行\n"
                       "4. 没有白色背景块")
    info_label.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 10px; background-color: #FFF9E6; border-radius: 6px;")
    layout.addWidget(info_label)

    # 创建提供商列表
    provider_list = QListWidget()
    provider_list.setStyleSheet(f"""
        QListWidget {{
            background-color: #FFFFFF;
            border: none;
            padding: 0px;
        }}
        QListWidget::item {{
            background-color: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        }}
        QListWidget::item:hover {{
            background-color: #F5F5F5;
        }}
        QListWidget::item:selected {{
            background-color: #F0F0F0;
        }}
    """)

    # 添加测试数据
    test_providers = [
        ("openai", "OpenAI", True),
        ("anthropic", "Anthropic", True),
        ("gemini", "Gemini", False),
        ("deepseek", "DeepSeek", True),
        ("doubao", "Doubao", False),
    ]

    for provider_id, provider_name, enabled in test_providers:
        item = QListWidgetItem()
        item.setSizeHint(ProviderListItemWidget(provider_id, provider_name, enabled).sizeHint())
        provider_list.addItem(item)

        widget = ProviderListItemWidget(provider_id, provider_name, enabled)
        provider_list.setItemWidget(item, widget)

    layout.addWidget(provider_list)

    window.show()

    print("=" * 80)
    print("提供商列表可视化测试")
    print("=" * 80)
    print("\n请在窗口中验证:")
    print("1. 鼠标悬浮时,整行变成浅灰色 (#F5F5F5)")
    print("2. 点击选中时,整行变成灰色 (#F0F0F0)")
    print("3. 文字和状态标签背景都是透明的")
    print("4. 没有白色背景块突兀显示")
    print("5. 灰色背景覆盖整个列表项\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
