#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
US4.1 可视化验收测试
手动验证API连接测试功能
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
    msg.setWindowTitle("US4.1 验收测试")
    msg.setIcon(QMessageBox.Information)

    text = """
<h2>US4.1 API连接测试服务验收测试</h2>

<p>请按以下顺序验证所有功能：</p>

<h3>准备工作</h3>
<ol>
<li>打开模型配置Dialog</li>
<li>选择任意provider (如 OpenAI 或 硅基流动)</li>
<li>确保右侧显示API配置区域</li>
</ol>

<h3>验收检查清单</h3>

<h4>AC1: "检测"按钮触发API测试</h4>
<ul>
<li>[  ] "检测"按钮存在且可点击</li>
<li>[  ] 点击按钮触发测试流程</li>
</ul>

<h4>AC2-3: 测试请求参数</h4>
<ul>
<li>[  ] 发送"hi"消息到provider API</li>
<li>[  ] 10秒超时（观察失败情况）</li>
</ul>

<h4>AC4-5: 重试逻辑</h4>
<ul>
<li>[  ] 最多3次尝试</li>
<li>[  ] 显示进度："正在测试连接... (X/3)"</li>
</ul>

<h4>AC6-7: 结果展示</h4>
<ul>
<li>[  ] 成功：显示"连接成功！"消息</li>
<li>[  ] 失败：显示错误详情（3次尝试后）</li>
</ul>

<h4>AC8: 按钮状态</h4>
<ul>
<li>[  ] 测试期间按钮禁用</li>
<li>[  ] 按钮文字显示"测试中..."和进度</li>
<li>[  ] 测试完成后按钮恢复</li>
</ul>

<h4>AC9: 非阻塞执行</h4>
<ul>
<li>[  ] 测试运行时UI不冻结</li>
<li>[  ] 可以移动dialog窗口</li>
<li>[  ] 可以切换到其他provider</li>
</ul>

<h3>测试场景</h3>

<h4>场景1: 无API密钥</h4>
<ol>
<li>清空API密钥输入框</li>
<li>点击"检测"</li>
<li>预期: 提示"请输入API密钥"</li>
</ol>

<h4>场景2: 无API地址</h4>
<ol>
<li>清空API地址输入框</li>
<li>点击"检测"</li>
<li>预期: 提示"请输入API地址"</li>
</ol>

<h4>场景3: 错误的API密钥</h4>
<ol>
<li>输入无效API密钥</li>
<li>点击"检测"</li>
<li>预期: 显示认证失败错误</li>
</ol>

<h4>场景4: 错误的API地址</h4>
<ol>
<li>输入无效URL</li>
<li>点击"检测"</li>
<li>预期: 显示连接错误</li>
</ol>

<p><b>点击OK开始验收测试</b></p>
    """

    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    result = msg.exec()

    return result == QMessageBox.Ok


def main():
    """运行可视化验收测试"""
    app = QApplication.instance() or QApplication(sys.argv)

    print("=" * 80)
    print("US4.1 API连接测试服务可视化验收测试")
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
        "请确认US4.1的所有验收标准都已满足。\n\n"
        "如果有任何项未通过，请选择No并报告问题。"
    )
    confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    confirm.setDefaultButton(QMessageBox.Yes)

    acceptance = confirm.exec()

    if acceptance == QMessageBox.Yes:
        print("\n" + "=" * 80)
        print("[SUCCESS] 验收测试通过！")
        print("=" * 80)
        print("\nUS4.1 所有验收标准已满足")
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
