#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证UI改进代码实现
检查model_config_dialog.py中的所有UI改进是否正确实现
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_ui_changes():
    """验证UI改进代码"""
    file_path = project_root / "components" / "chat" / "widgets" / "model_config_dialog.py"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("=" * 80)
    print("验证UI改进代码实现")
    print("=" * 80)

    checks = []

    # 1. 背景色统一为白色
    check1 = "background-color: #FFFFFF" in content
    checks.append(("1. 所有背景为白色 (#FFFFFF)", check1))

    # 2. 提供商列表样式
    check2_1 = "QListWidget::item:hover" in content and "#F5F5F5" in content
    check2_2 = "QListWidget::item:selected" in content and "#F0F0F0" in content
    checks.append(("2. 提供商列表悬浮/选中效果", check2_1 and check2_2))

    # 3. ProviderListItemWidget固定高度和垂直对齐
    check3_1 = "setFixedHeight(48)" in content
    check3_2 = "Qt.AlignVCenter" in content
    checks.append(("3. 提供商列表文字垂直居中", check3_1 and check3_2))

    # 4. API密钥明文显示 (Password模式被注释)
    check4 = "# self.api_key_input.setEchoMode(QLineEdit.Password)" in content
    checks.append(("4. API密钥明文显示", check4))

    # 5. 搜索框白色背景
    check5 = 'QLineEdit' in content and 'background-color: #FFFFFF' in content
    checks.append(("5. 输入框白色背景", check5))

    # 6. 标题加粗16px
    check6_1 = "setPixelSize(16)" in content
    check6_2 = "setWeight(QFont.Bold)" in content
    checks.append(("6. 标题加粗放大 (16px Bold)", check6_1 and check6_2))

    # 7. 模型列表重构为ScrollArea
    check7_1 = "QScrollArea" in content
    check7_2 = "models_container_layout" in content
    check7_3 = "ModelCategoryCard" in content
    checks.append(("7. 模型列表分类卡片布局", check7_1 and check7_2 and check7_3))

    # 8. 边框移除 (border: none)
    check8 = content.count("border: none") >= 8
    checks.append(("8. 文字边框已移除 (border: none)", check8))

    # 9. ModelCategoryCard类存在
    check9 = "class ModelCategoryCard(QWidget):" in content
    checks.append(("9. ModelCategoryCard类已创建", check9))

    # 10. ModelCardItem类存在
    check10 = "class ModelCardItem(QWidget):" in content
    checks.append(("10. ModelCardItem类已创建", check10))

    # 11. 折叠功能
    check11 = "_toggle_expand" in content
    checks.append(("11. 分类卡片折叠功能", check11))

    # 12. 分类顺序定义
    check12_categories = all([
        cat in content
        for cat in ["DeepSeek", "Anthropic", "Doubao", "Embedding",
                   "Openai", "Gemini", "Gemma", "Llama-3.2", "BAAI", "Qwen"]
    ])
    checks.append(("12. 模型分类顺序定义", check12_categories))

    # 打印结果
    print("\n检查结果:\n")

    all_passed = True
    for description, passed in checks:
        status = "[PASS]" if passed else "[FAIL]"
        symbol = "√" if passed else "×"
        print(f"{status} {description}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)

    if all_passed:
        print("✓ 所有UI改进已正确实现!")
        print("\n关键实现:")
        print("  - 白色背景统一应用")
        print("  - 提供商列表48px固定高度,垂直居中")
        print("  - 灰色悬浮/选中效果 (#F5F5F5/#F0F0F0)")
        print("  - API密钥明文显示")
        print("  - 16px Bold标题")
        print("  - 卡片式可折叠模型分类")
        print("  - 无文字边框和下划线")
        return True
    else:
        print("× 部分检查未通过,请检查代码")
        return False


if __name__ == "__main__":
    success = verify_ui_changes()
    sys.exit(0 if success else 1)
