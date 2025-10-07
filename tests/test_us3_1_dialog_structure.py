# -*- coding: utf-8 -*-
"""
测试: US3.1 Dialog Structure and Layout
验证ModelConfigDialog的基础结构和布局
"""

import sys
import io
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# 设置stdout为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.chat.widgets.model_config_dialog import ModelConfigDialog
from components.chat.styles.cherry_theme import COLORS


def test_dialog_size():
    """测试: 对话框固定大小为1200×800"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()

    assert dialog.width() == 1200, f"宽度应为1200px,实际为{dialog.width()}px"
    assert dialog.height() == 800, f"高度应为800px,实际为{dialog.height()}px"

    # 验证固定大小（不可调整）
    dialog.show()
    QTest.qWait(100)

    assert dialog.minimumWidth() == 1200
    assert dialog.maximumWidth() == 1200
    assert dialog.minimumHeight() == 800
    assert dialog.maximumHeight() == 800

    dialog.close()
    print("✓ 对话框大小测试通过: 1200×800px (固定)")


def test_modal_behavior():
    """测试: Modal行为（阻止父窗口交互）"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()

    assert dialog.isModal(), "对话框应为Modal"
    assert dialog.windowModality() == Qt.ApplicationModal, "应阻止所有窗口交互"

    print("✓ Modal行为测试通过")


def test_two_panel_layout():
    """测试: 两面板水平布局"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证左面板存在且宽度为350px
    assert dialog.left_panel is not None, "左面板应存在"
    assert dialog.left_panel.width() == 350, f"左面板宽度应为350px,实际为{dialog.left_panel.width()}px"

    # 验证右面板存在
    assert dialog.right_panel is not None, "右面板应存在"

    # 验证主布局
    main_layout = dialog.layout()
    assert main_layout is not None, "主布局应存在"
    assert main_layout.spacing() == 0, "主布局间距应为0"
    assert main_layout.contentsMargins().left() == 0, "主布局边距应为0"

    dialog.close()
    print("✓ 两面板布局测试通过: 左350px | 右850px")


def test_window_title():
    """测试: 窗口标题为'设置'"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()

    assert dialog.windowTitle() == "设置", f"窗口标题应为'设置',实际为'{dialog.windowTitle()}'"

    print("✓ 窗口标题测试通过: '设置'")


def test_divider_exists():
    """测试: 面板间存在1px分隔线"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 检查布局中是否有3个widget（左面板 + 分隔线 + 右面板）
    main_layout = dialog.layout()
    widget_count = main_layout.count()

    assert widget_count == 3, f"主布局应有3个元素(左面板+分隔线+右面板),实际有{widget_count}个"

    # 获取分隔线（第2个widget，索引1）
    divider = main_layout.itemAt(1).widget()
    assert divider is not None, "分隔线应存在"
    assert divider.width() == 1, f"分隔线宽度应为1px,实际为{divider.width()}px"

    dialog.close()
    print("✓ 分隔线测试通过: 1px垂直线")


def test_visual_styling():
    """测试: Cherry Studio主题样式应用"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证面板对象名称已设置（用于CSS选择器）
    assert dialog.left_panel.objectName() == "left_panel", "左面板应有objectName"
    assert dialog.right_panel.objectName() == "right_panel", "右面板应有objectName"

    # 验证样式表已应用
    assert dialog.styleSheet() != "", "对话框应有样式表"

    dialog.close()
    print("✓ 主题样式测试通过")


def test_pixel_perfect_layout():
    """测试: 像素级精确布局验证"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(200)

    # 验证总宽度分配
    left_width = dialog.left_panel.width()
    divider_width = 1  # 分隔线
    right_width = dialog.right_panel.width()

    total_content_width = left_width + divider_width + right_width

    # 总宽度应等于对话框宽度（考虑可能的边距）
    dialog_inner_width = dialog.width() - dialog.layout().contentsMargins().left() - dialog.layout().contentsMargins().right()

    assert total_content_width == dialog_inner_width, \
        f"内容总宽度({total_content_width})应等于对话框内部宽度({dialog_inner_width})"

    # 左面板精确350px
    assert left_width == 350, f"左面板宽度偏差: {left_width - 350}px"

    # 右面板应约850px（1200 - 350 - 1 = 849，允许±5px误差）
    expected_right_width = 849  # 1200 - 350 - 1
    deviation = abs(right_width - expected_right_width)
    assert deviation <= 5, f"右面板宽度偏差过大: {deviation}px (预期{expected_right_width}px, 实际{right_width}px)"

    dialog.close()
    print(f"✓ 像素级精确度测试通过: 偏差≤5px (实际右面板={right_width}px)")


def run_all_tests():
    """运行所有US3.1测试"""
    print("=" * 60)
    print("US3.1: Dialog Structure and Layout - 测试")
    print("=" * 60)

    test_dialog_size()
    test_modal_behavior()
    test_two_panel_layout()
    test_window_title()
    test_divider_exists()
    test_visual_styling()
    test_pixel_perfect_layout()

    print("=" * 60)
    print("✅ 所有US3.1测试通过!")
    print("=" * 60)


def visual_verification():
    """可视化验证 - 打开对话框进行人工检查"""
    print("\n" + "=" * 60)
    print("可视化验证")
    print("=" * 60)
    print("\n请人工验证以下内容:")
    print("1. 对话框大小为1200×800px")
    print("2. 左面板背景为浅灰色（#F7F8FA）")
    print("3. 右面板背景为白色（#FFFFFF）")
    print("4. 面板间有1px灰色分隔线")
    print("5. 对话框为Modal（无法与后面的窗口交互）")
    print("6. 窗口标题为'设置'")
    print("\n按任意键关闭...")
    print("=" * 60)

    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.exec()


if __name__ == "__main__":
    # 运行自动化测试
    run_all_tests()

    # 可视化验证说明（仅提示，不实际执行）
    print("\n" + "=" * 60)
    print("可视化验证说明")
    print("=" * 60)
    print("\n如需人工验证，请运行:")
    print("  python -c \"from tests.test_us3_1_dialog_structure import visual_verification; visual_verification()\"")
    print("\n验证项:")
    print("1. 对话框大小为1200×800px")
    print("2. 左面板背景为浅灰色（#F7F8FA）")
    print("3. 右面板背景为白色（#FFFFFF）")
    print("4. 面板间有1px灰色分隔线")
    print("5. 对话框为Modal（无法与后面的窗口交互）")
    print("6. 窗口标题为'设置'")
    print("=" * 60)
