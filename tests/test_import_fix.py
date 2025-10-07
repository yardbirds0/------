#!/usr/bin/env python
"""快速验证程序是否能正常启动"""

import sys

try:
    # 尝试导入主模块
    from components.advanced_widgets import SearchableSourceTree, Signal
    print("✅ 成功导入 SearchableSourceTree")

    # 检查 sheetChanged 信号是否存在
    if hasattr(SearchableSourceTree, 'sheetChanged'):
        print("✅ SearchableSourceTree 具有 sheetChanged 信号")
    else:
        print("❌ SearchableSourceTree 缺少 sheetChanged 信号")

    # 尝试导入主窗口
    from main import MainWindow
    print("✅ 成功导入 MainWindow")

    print("\n✨ 所有导入测试通过！程序应该可以正常启动。")

except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 其他错误: {e}")
    sys.exit(1)