#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
US3.1-US3.5 最终可视化验收测试
真实打开dialog，手动验证所有功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMessageBox
from components.chat.widgets.model_config_dialog import ModelConfigDialog


def show_instructions():
    """显示测试说明"""
    msg = QMessageBox()
    msg.setWindowTitle("US3.1-US3.5 验收测试")
    msg.setIcon(QMessageBox.Information)

    text = """
<h2>US3.1-US3.5 验收测试说明</h2>

<p>请按以下顺序验证所有功能：</p>

<h3>US3.1: Dialog Structure (Dialog结构)</h3>
<ul>
<li>[  ] Dialog尺寸: 1200×800px</li>
<li>[  ] Modal模式: 阻止主窗口交互</li>
<li>[  ] 左面板: 350px宽</li>
<li>[  ] 右面板: 850px宽</li>
<li>[  ] 面板分隔线</li>
<li>[  ] 窗口标题: "设置"</li>
</ul>

<h3>US3.2: Provider List (Provider列表)</h3>
<ul>
<li>[  ] 标题: "模型供应商" (16px粗体)</li>
<li>[  ] 搜索框: 带placeholder</li>
<li>[  ] Provider列表: 显示所有provider</li>
<li>[  ] 每项显示: icon + 名称 + toggle</li>
<li>[  ] 悬浮/选中: 圆角灰色背景</li>
<li>[  ] "添加"按钮: 底部</li>
</ul>

<h3>US3.3: Provider Configuration (Provider配置)</h3>
<ul>
<li>[  ] Header: Provider名称 + 外链 + toggle</li>
<li>[  ] API密钥区域: 标题 + 输入框 + "检测"按钮</li>
<li>[  ] API密钥提示文字</li>
<li>[  ] API地址区域: 标题 + 输入框</li>
<li>[  ] 输入框高度: 40px</li>
<li>[  ] 无"保存"按钮（立即应用）</li>
</ul>

<h3>US3.4: Model Selection (模型选择)</h3>
<ul>
<li>[  ] 标题: "模型列表"</li>
<li>[  ] 分类卡片: DeepSeek, Qwen等</li>
<li>[  ] 每个模型: Radio button + 名称</li>
<li>[  ] 可折叠: 点击分类标题</li>
<li>[  ] 当前模型: 预选中</li>
</ul>

<h3>US3.5: Immediate Application (立即应用)</h3>
<ul>
<li>[  ] 选择模型: 立即生效</li>
<li>[  ] 无Save按钮</li>
<li>[  ] Dialog保持打开</li>
<li>[  ] 配置立即保存</li>
</ul>

<p><b>点击OK开始验收测试</b></p>
    """

    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    result = msg.exec()

    return result == QMessageBox.Ok


def main():
    """运行最终可视化验收测试"""
    app = QApplication.instance() or QApplication(sys.argv)

    print("=" * 80)
    print("US3.1-US3.5 最终可视化验收测试")
    print("=" * 80)
    print("\n请按照弹出的说明进行手动验收测试\n")

    # 显示说明
    if not show_instructions():
        print("用户取消测试")
        return 1

    # 打开dialog
    dialog = ModelConfigDialog()

    print("\n[INFO] Dialog已打开，请按照说明进行验证")
    print("[INFO] 关闭dialog后，将提示您输入验收结果\n")

    result = dialog.exec()

    # 验收确认
    confirm = QMessageBox()
    confirm.setWindowTitle("验收确认")
    confirm.setIcon(QMessageBox.Question)
    confirm.setText("所有验收项是否都通过？")
    confirm.setInformativeText(
        "请确认所有US3.1-US3.5的验收标准都已满足。\n\n"
        "如果有任何项未通过，请选择No并报告问题。"
    )
    confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    confirm.setDefaultButton(QMessageBox.Yes)

    acceptance = confirm.exec()

    if acceptance == QMessageBox.Yes:
        print("\n" + "=" * 80)
        print("[SUCCESS] 验收测试通过！")
        print("=" * 80)
        print("\nUS3.1-US3.5 所有验收标准已满足")
        print("\n下一步:")
        print("1. 更新03-sprint-plan.md中的勾选框")
        print("2. 生成验收报告文档")
        print("3. 提交代码和文档")
        return 0
    else:
        print("\n" + "=" * 80)
        print("[FAIL] 验收测试未通过")
        print("=" * 80)
        print("\n请记录失败项并修复问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())
