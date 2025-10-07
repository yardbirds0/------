#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
可视化测试：模型列表显示
打开dialog供手动验证
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMessageBox
from components.chat.widgets.model_config_dialog import ModelConfigDialog


def main():
    """可视化测试模型列表"""
    app = QApplication.instance() or QApplication(sys.argv)

    print("=" * 80)
    print("可视化测试：模型列表显示")
    print("=" * 80)
    print("\n请在dialog中验证：")
    print("1. 选择'硅基流动'provider")
    print("2. 检查右侧模型列表是否显示'通用对话'分类")
    print("3. 检查该分类下是否有2个Qwen模型")
    print("4. 切换到'OpenAI'provider，检查是否正确显示GPT模型")
    print("5. 再次切换回'硅基流动'，验证列表刷新是否正常")
    print("\n")

    dialog = ModelConfigDialog()
    result = dialog.exec()

    # 询问验证结果
    confirm = QMessageBox()
    confirm.setWindowTitle("验证确认")
    confirm.setIcon(QMessageBox.Question)
    confirm.setText("模型列表显示是否正常？")
    confirm.setInformativeText(
        "请确认以下几点：\n\n"
        "1. 硅基流动的'通用对话'分类可以正常显示\n"
        "2. 分类下有2个Qwen模型\n"
        "3. 切换provider时列表正确刷新\n"
        "4. 没有重复的分类卡片\n"
    )
    confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

    acceptance = confirm.exec()

    if acceptance == QMessageBox.Yes:
        print("\n[SUCCESS] 模型列表显示正常")
        return 0
    else:
        print("\n[FAIL] 模型列表显示异常，需要进一步调试")
        return 1


if __name__ == "__main__":
    sys.exit(main())
