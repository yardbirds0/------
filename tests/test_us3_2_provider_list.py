# -*- coding: utf-8 -*-
"""
测试: US3.2 Left Panel - Provider List
验证Provider列表的UI和交互功能
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

from components.chat.widgets.model_config_dialog import ModelConfigDialog, ProviderListItemWidget
from components.chat.controllers.config_controller import ConfigController


def test_left_panel_structure():
    """测试: 左面板结构完整"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证组件存在
    assert hasattr(dialog, 'search_input'), "搜索框应存在"
    assert hasattr(dialog, 'provider_list'), "Provider列表应存在"

    # 验证搜索框属性
    assert dialog.search_input.height() == 36, f"搜索框高度应为36px,实际{dialog.search_input.height()}px"
    assert dialog.search_input.placeholderText() == "🔍 搜索模型平台...", "搜索框占位符文本错误"

    # 验证列表属性
    from PySide6.QtWidgets import QAbstractItemView
    assert dialog.provider_list.dragDropMode() == QAbstractItemView.InternalMove, "应支持拖拽排序"
    assert dialog.provider_list.selectionMode() == QAbstractItemView.SingleSelection, "应为单选模式"

    dialog.close()
    print("✓ 左面板结构测试通过")


def test_provider_list_populated():
    """测试: Provider列表已填充数据"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证列表项数量
    item_count = dialog.provider_list.count()
    assert item_count > 0, f"Provider列表应有数据,当前{item_count}项"

    # 验证至少有默认的siliconflow provider
    controller = ConfigController.instance()
    providers = controller.get_providers()
    assert len(providers) > 0, "ConfigController应有默认provider"

    # 验证列表项widget
    first_item = dialog.provider_list.item(0)
    assert first_item is not None, "第一个列表项应存在"

    item_widget = dialog.provider_list.itemWidget(first_item)
    assert isinstance(item_widget, ProviderListItemWidget), "列表项应使用自定义widget"

    dialog.close()
    print(f"✓ Provider列表填充测试通过: {item_count}个provider")


def test_provider_list_item_widget():
    """测试: Provider列表项Widget显示"""
    app = QApplication.instance() or QApplication(sys.argv)

    # 创建测试widget
    item = ProviderListItemWidget("test_provider", "测试供应商", enabled=True)

    # 验证属性
    assert item.provider_id == "test_provider"
    assert item.provider_name == "测试供应商"
    assert item.is_enabled() == True

    # 验证徽章文本（首字母）
    badge_text = item._get_badge_text()
    assert badge_text == "测", f"徽章文本应为首字母'测',实际为'{badge_text}'"

    # 测试禁用provider
    item2 = ProviderListItemWidget("test2", "OpenAI", enabled=False)
    assert item2.is_enabled() == False
    assert item2._get_badge_text() == "O"

    print("✓ Provider列表项Widget测试通过")


def test_search_functionality():
    """测试: 搜索功能"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    initial_count = dialog.provider_list.count()

    # 输入搜索关键词
    dialog.search_input.setText("硅")
    QTest.qWait(50)

    filtered_count = dialog.provider_list.count()

    # 验证搜索结果
    # 应该筛选出包含"硅"的provider（如"硅基流动"）
    assert filtered_count <= initial_count, "搜索后数量应<=原数量"

    # 清空搜索
    dialog.search_input.clear()
    QTest.qWait(50)

    restored_count = dialog.provider_list.count()
    assert restored_count == initial_count, "清空搜索后应恢复所有项"

    dialog.close()
    print(f"✓ 搜索功能测试通过: {initial_count} → {filtered_count} → {restored_count}")


def test_provider_selection():
    """测试: Provider选择"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    if dialog.provider_list.count() == 0:
        print("⚠ 跳过选择测试: 无provider")
        dialog.close()
        return

    # 选择第一个provider
    first_item = dialog.provider_list.item(0)
    first_item.setSelected(True)
    QTest.qWait(50)

    # 验证选择
    assert first_item.isSelected(), "第一项应被选中"
    provider_id = first_item.data(Qt.UserRole)
    assert dialog.current_provider_id == provider_id, "当前provider_id应更新"

    dialog.close()
    print("✓ Provider选择测试通过")


def test_add_button_exists():
    """测试: 添加按钮存在并可点击"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 查找添加按钮
    add_button = None
    for child in dialog.left_panel.children():
        if hasattr(child, 'text') and child.text() == "+ 添加":
            add_button = child
            break

    assert add_button is not None, "添加按钮应存在"
    assert add_button.height() == 40, f"添加按钮高度应为40px,实际{add_button.height()}px"

    dialog.close()
    print("✓ 添加按钮测试通过")


def test_visual_styling():
    """测试: 视觉样式符合Cherry Studio主题"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证左面板对象名称已设置（用于CSS选择器）
    assert dialog.left_panel.objectName() == "left_panel", "左面板应有objectName"

    # 验证对话框全局样式表包含left_panel背景色
    dialog_style = dialog.styleSheet()
    assert "left_panel" in dialog_style, "对话框样式应包含left_panel选择器"
    assert "background-color" in dialog_style, "对话框样式应有背景色定义"

    # 验证搜索框样式
    search_style = dialog.search_input.styleSheet()
    assert "border-radius" in search_style, "搜索框应有圆角"

    # 验证列表样式
    list_style = dialog.provider_list.styleSheet()
    assert "border-radius" in list_style, "列表应有圆角"

    dialog.close()
    print("✓ 视觉样式测试通过")


def run_all_tests():
    """运行所有US3.2测试"""
    print("=" * 60)
    print("US3.2: Left Panel - Provider List - 测试")
    print("=" * 60)

    test_left_panel_structure()
    test_provider_list_populated()
    test_provider_list_item_widget()
    test_search_functionality()
    test_provider_selection()
    test_add_button_exists()
    test_visual_styling()

    print("=" * 60)
    print("✅ 所有US3.2测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    # 运行自动化测试
    run_all_tests()

    # 可视化验证说明
    print("\n" + "=" * 60)
    print("可视化验证说明")
    print("=" * 60)
    print("\n验证项:")
    print("1. 标题: '模型供应商' (16px, bold)")
    print("2. 搜索框: 36px高, '🔍 搜索模型平台...' 占位符")
    print("3. Provider列表: 白色背景 + 圆角")
    print("4. 列表项: [徽章] Provider名称 [ON]")
    print("5. 添加按钮: 蓝色边框, 40px高, '+ 添加'")
    print("6. 整体风格: 与AI参数设置面板一致")
    print("=" * 60)
