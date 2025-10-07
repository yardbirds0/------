#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试"企业财务快报利润因素分析表"问题是否修复
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from main import MainWindow

def test_profit_analysis_fix():
    """测试修复效果"""
    app = QApplication(sys.argv)

    # 创建主窗口
    window = MainWindow()
    window.show()

    print("=" * 80)
    print("测试步骤：")
    print("1. 程序启动后，加载Excel文件")
    print("2. 切换到'企业财务快报利润因素分析表'")
    print("3. 观察是否有错误信息")
    print("4. 再切换到其他表格，检查自动扩宽是否正常")
    print("5. 切换来源项表格，检查主表格列宽是否调整")
    print("=" * 80)

    return app.exec()

if __name__ == "__main__":
    sys.exit(test_profit_analysis_fix())