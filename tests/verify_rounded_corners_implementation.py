#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证圆角背景实现
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_rounded_corners():
    """验证圆角背景实现"""
    file_path = project_root / "components" / "chat" / "widgets" / "model_config_dialog.py"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("=" * 80)
    print("验证圆角背景实现")
    print("=" * 80)

    checks = []

    # 1. _is_hovered状态变量
    check1 = "self._is_hovered = False" in content
    checks.append(("1. _is_hovered状态变量", check1))

    # 2. _is_selected状态变量
    check2 = "self._is_selected = False" in content
    checks.append(("2. _is_selected状态变量", check2))

    # 3. setMouseTracking启用
    check3 = "self.setMouseTracking(True)" in content
    checks.append(("3. Mouse tracking已启用", check3))

    # 4. enterEvent实现
    check4 = "def enterEvent(self, event):" in content and "self._is_hovered = True" in content
    checks.append(("4. enterEvent已实现", check4))

    # 5. leaveEvent实现
    check5 = "def leaveEvent(self, event):" in content and "self._is_hovered = False" in content
    checks.append(("5. leaveEvent已实现", check5))

    # 6. paintEvent实现
    check6 = "def paintEvent(self, event):" in content
    checks.append(("6. paintEvent已实现", check6))

    # 7. QPainterPath使用
    check7 = "QPainterPath" in content and "addRoundedRect" in content
    checks.append(("7. QPainterPath圆角绘制", check7))

    # 8. 6px圆角
    check8 = "addRoundedRect(rect, 6, 6)" in content
    checks.append(("8. 6px圆角参数", check8))

    # 9. 抗锯齿
    check9 = "setRenderHint(QPainter.Antialiasing)" in content
    checks.append(("9. 抗锯齿渲染", check9))

    # 10. 颜色设置
    check10_1 = '"#F0F0F0"' in content  # 选中
    check10_2 = '"#F5F5F5"' in content  # 悬浮
    checks.append(("10. 背景颜色设置", check10_1 and check10_2))

    # 11. QListWidget::item背景透明
    check11 = "QListWidget::item:hover" in content and "background-color: transparent" in content
    checks.append(("11. QListWidget::item背景透明", check11))

    # 12. update()调用
    check12 = content.count("self.update()") >= 3
    checks.append(("12. update()触发重绘", check12))

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
        print("[SUCCESS] 圆角背景实现完整!")
        print("\n关键实现:")
        print("  - 状态跟踪: _is_hovered, _is_selected")
        print("  - 事件处理: enterEvent, leaveEvent")
        print("  - 自定义绘制: paintEvent + QPainterPath")
        print("  - 圆角参数: 6px")
        print("  - 抗锯齿: QPainter.Antialiasing")
        print("  - 颜色方案: #F5F5F5 (hover), #F0F0F0 (selected)")
        print("\n预期效果:")
        print("  [OK] 悬浮时显示浅灰色圆角背景")
        print("  [OK] 选中时显示灰色圆角背景+文字加粗")
        print("  [OK] 背景边缘平滑无锯齿")
        print("  [OK] 6px圆角效果")
        return True
    else:
        print("[ERROR] 部分检查未通过")
        return False


if __name__ == "__main__":
    success = verify_rounded_corners()
    sys.exit(0 if success else 1)
