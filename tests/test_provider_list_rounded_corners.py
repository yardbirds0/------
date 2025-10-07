#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提供商列表圆角背景测试
验证:
1. 悬浮时圆角灰色背景
2. 选中时圆角灰色背景
3. 6px圆角效果
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
    """运行圆角背景测试"""
    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("提供商列表圆角背景测试")
    window.setGeometry(100, 100, 450, 600)

    layout = QVBoxLayout(window)
    layout.setContentsMargins(20, 20, 20, 20)

    # 说明标签
    info_label = QLabel(
        "请验证圆角背景效果:\n\n"
        "1. [悬浮] 鼠标悬浮时:\n"
        "   - 显示浅灰色圆角背景 (#F5F5F5)\n"
        "   - 背景具有6px圆角\n\n"
        "2. [选中] 点击选中时:\n"
        "   - 显示灰色圆角背景 (#F0F0F0)\n"
        "   - 背景具有6px圆角\n"
        "   - 文字加粗\n\n"
        "3. [默认] 未悬浮未选中时:\n"
        "   - 背景透明\n"
    )
    info_label.setStyleSheet(f"""
        QLabel {{
            color: {COLORS['text_primary']};
            padding: 15px;
            background-color: #E6F7FF;
            border-radius: 6px;
            border: 1px solid #91D5FF;
        }}
    """)
    layout.addWidget(info_label)

    # 创建提供商列表
    provider_list = QListWidget()
    provider_list.setSpacing(0)
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
        }}
        QListWidget::item:hover {{
            background-color: transparent;
        }}
        QListWidget::item:selected {{
            background-color: transparent;
        }}
    """)

    # 监听选中状态变化
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
    print("提供商列表圆角背景测试")
    print("=" * 80)
    print("\n关键验证点:")
    print("1. [圆角] 悬浮和选中时背景必须是圆角矩形 (6px)")
    print("2. [悬浮] 悬浮时浅灰色 #F5F5F5")
    print("3. [选中] 选中时灰色 #F0F0F0 且文字加粗")
    print("4. [平滑] 圆角边缘平滑无锯齿\n")
    print("实现方式:")
    print("  - 使用paintEvent绘制圆角背景")
    print("  - QPainterPath.addRoundedRect(rect, 6, 6)")
    print("  - 抗锯齿渲染 (Antialiasing)")
    print("  - enterEvent/leaveEvent处理hover状态\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
