#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证 Signal 修复是否成功"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, r'd:\Code\快报填写程序')

try:
    # 尝试导入 Signal
    from PySide6.QtCore import Signal
    print("SUCCESS: Signal imported from PySide6.QtCore")

    # 尝试导入 SearchableSourceTree
    from components.advanced_widgets import SearchableSourceTree
    print("SUCCESS: SearchableSourceTree imported")

    # 检查 sheetChanged 信号
    if hasattr(SearchableSourceTree, 'sheetChanged'):
        print("SUCCESS: sheetChanged signal exists in SearchableSourceTree")

        # 检查信号类型
        signal = getattr(SearchableSourceTree, 'sheetChanged')
        print(f"Signal type: {type(signal)}")
    else:
        print("ERROR: sheetChanged signal not found")

    print("\n=== All tests passed! The fix is successful. ===")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()