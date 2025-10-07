#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证提供商列表最终修复代码实现
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_final_fixes():
    """验证最终修复代码"""
    file_path = project_root / "components" / "chat" / "widgets" / "model_config_dialog.py"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("=" * 80)
    print("验证提供商列表最终修复代码")
    print("=" * 80)

    checks = []

    # 1. QListWidget spacing设置为0
    check1 = "self.provider_list.setSpacing(0)" in content
    checks.append(("1. QListWidget spacing = 0", check1))

    # 2. QListWidget padding = 4px
    check2 = "padding: 4px" in content and "QListWidget {" in content
    checks.append(("2. QListWidget padding = 4px", check2))

    # 3. Item margin = 2px 0px
    check3 = "margin: 2px 0px" in content
    checks.append(("3. Item margin = 2px 0px", check3))

    # 4. Item border-radius = 6px
    check4 = "border-radius: 6px" in content and "QListWidget::item" in content
    checks.append(("4. Item border-radius = 6px", check4))

    # 5. Widget高度 = 44px
    check5 = "self.setFixedHeight(44)" in content
    checks.append(("5. Widget固定高度 = 44px", check5))

    # 6. Widget上下margins = 8px
    check6 = "setContentsMargins(12, 8, 12, 8)" in content
    checks.append(("6. Widget margins = (12, 8, 12, 8)", check6))

    # 7. set_selected方法存在
    check7 = "def set_selected(self, selected: bool):" in content
    checks.append(("7. set_selected方法已实现", check7))

    # 8. 选中时文字加粗逻辑
    check8 = "setWeight(QFont.Bold)" in content and "setWeight(QFont.Normal)" in content
    checks.append(("8. 选中时文字加粗逻辑", check8))

    # 9. _on_provider_selection_changed方法存在
    check9 = "def _on_provider_selection_changed(self):" in content
    checks.append(("9. _on_provider_selection_changed方法已实现", check9))

    # 10. itemSelectionChanged连接
    check10 = "itemSelectionChanged.connect(self._on_provider_selection_changed)" in content
    checks.append(("10. itemSelectionChanged信号连接", check10))

    # 11. name_label和name_font保存为实例变量
    check11 = "self.name_label" in content and "self.name_font" in content
    checks.append(("11. name_label和name_font实例变量", check11))

    # 打印结果
    print("\n检查结果:\n")

    all_passed = True
    for description, passed in checks:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {description}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)

    if all_passed:
        print("[SUCCESS] 所有修复已正确实现!")
        print("\n关键修复:")
        print("  - Widget高度44px + 上下margins 8px")
        print("  - Item margin 2px 0px + border-radius 6px")
        print("  - QListWidget spacing 0, padding 4px")
        print("  - 选中时文字Bold (set_selected方法)")
        print("  - itemSelectionChanged信号处理")
        print("\n预期效果:")
        print("  [OK] 文字垂直居中,不超出边框")
        print("  [OK] 6px圆角背景")
        print("  [OK] 悬浮时#F5F5F5背景")
        print("  [OK] 选中时#F0F0F0背景+文字加粗")
        return True
    else:
        print("[ERROR] 部分检查未通过")
        return False


if __name__ == "__main__":
    success = verify_final_fixes()
    sys.exit(0 if success else 1)
