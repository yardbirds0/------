# -*- coding: utf-8 -*-
"""
调试搜索问题
"""

import sys
import io
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.chat.widgets.model_config_dialog import ModelConfigDialog
from components.chat.controllers.config_controller import ConfigController

app = QApplication(sys.argv)

# 获取初始provider数量
controller = ConfigController.instance()
initial_providers = controller.get_providers()
print(f"ConfigController中的Provider数量: {len(initial_providers)}")
for p in initial_providers:
    print(f"  - {p.get('id')}: {p.get('name')}")

print("\n创建对话框...")
dialog = ModelConfigDialog()
dialog.show()
QTest.qWait(100)

initial_count = dialog.provider_list.count()
print(f"对话框初始列表数量: {initial_count}")

print("\n输入搜索关键词'硅'...")
dialog.search_input.setText("硅")
QTest.qWait(50)

filtered_count = dialog.provider_list.count()
print(f"搜索后列表数量: {filtered_count}")
for i in range(filtered_count):
    item = dialog.provider_list.item(i)
    widget = dialog.provider_list.itemWidget(item)
    print(f"  - {widget.provider_name if widget else 'Unknown'}")

print("\n清空搜索...")
dialog.search_input.clear()
QTest.qWait(50)

restored_count = dialog.provider_list.count()
print(f"恢复后列表数量: {restored_count}")
for i in range(restored_count):
    item = dialog.provider_list.item(i)
    widget = dialog.provider_list.itemWidget(item)
    print(f"  - {widget.provider_name if widget else 'Unknown'}")

print(f"\n对比: initial={initial_count}, filtered={filtered_count}, restored={restored_count}")
print(f"测试{'通过' if restored_count == initial_count else '失败'}!")

dialog.close()
