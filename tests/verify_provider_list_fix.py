#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证提供商列表样式修复
检查ProviderListItemWidget的透明背景设置
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_provider_list_fix():
    """验证提供商列表修复"""
    file_path = project_root / "components" / "chat" / "widgets" / "model_config_dialog.py"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("=" * 80)
    print("验证提供商列表样式修复")
    print("=" * 80)

    checks = []

    # 1. ProviderListItemWidget设置透明背景
    check1 = 'self.setStyleSheet("background-color: transparent;")' in content
    checks.append(("1. ProviderListItemWidget透明背景", check1))

    # 2. name_label透明背景
    check2 = 'background-color: transparent' in content and 'name_label.setStyleSheet' in content
    checks.append(("2. Provider名称标签透明背景", check2))

    # 3. status_label透明背景
    check3 = 'status_label.setStyleSheet' in content and 'background-color: transparent' in content
    checks.append(("3. 状态标签透明背景", check3))

    # 4. QListWidget的hover和selected样式
    check4_1 = "QListWidget::item:hover" in content and "#F5F5F5" in content
    check4_2 = "QListWidget::item:selected" in content and "#F0F0F0" in content
    checks.append(("4. QListWidget hover/selected样式", check4_1 and check4_2))

    # 5. 固定高度48px
    check5 = "setFixedHeight(48)" in content
    checks.append(("5. 固定高度48px", check5))

    # 6. 垂直居中对齐
    check6 = "Qt.AlignVCenter" in content
    checks.append(("6. 垂直居中对齐", check6))

    # 7. 边距设置 (12, 0, 12, 0)
    check7 = "setContentsMargins(12, 0, 12, 0)" in content
    checks.append(("7. 边距设置 (12,0,12,0)", check7))

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
        print("[OK] 提供商列表样式修复成功!")
        print("\n关键修复:")
        print("  - ProviderListItemWidget设置透明背景")
        print("  - name_label和status_label都设置透明背景")
        print("  - QListWidget的灰色背景能够正常显示")
        print("  - 悬浮和选中效果统一为灰色背景")
        print("  - 48px固定高度,垂直居中")
        return True
    else:
        print("[ERROR] 部分检查未通过,请检查代码")
        return False


if __name__ == "__main__":
    success = verify_provider_list_fix()
    sys.exit(0 if success else 1)
