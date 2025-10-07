# -*- coding: utf-8 -*-
"""
测试: US3.3 Right Panel - Provider Configuration
验证Provider配置面板的UI和功能
"""

import sys
import io
from pathlib import Path
from PySide6.QtWidgets import QApplication, QLineEdit
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# 设置stdout为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.chat.widgets.model_config_dialog import ModelConfigDialog
from components.chat.controllers.config_controller import ConfigController


def test_right_panel_structure():
    """测试: 右面板结构完整"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证Header组件存在
    assert hasattr(dialog, 'header_widget'), "Header widget应存在"
    assert hasattr(dialog, 'provider_name_label'), "Provider名称标签应存在"
    assert hasattr(dialog, 'external_link_btn'), "外部链接按钮应存在"
    assert hasattr(dialog, 'provider_toggle'), "Provider Toggle应存在"

    # 验证API配置区域存在
    assert hasattr(dialog, 'api_key_section'), "API密钥区域应存在"
    assert hasattr(dialog, 'api_key_input'), "API密钥输入框应存在"
    assert hasattr(dialog, 'api_url_section'), "API地址区域应存在"
    assert hasattr(dialog, 'api_url_input'), "API地址输入框应存在"

    dialog.close()
    print("✓ 右面板结构测试通过")


def test_header_section():
    """测试: Header区域显示和样式"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证Header高度
    assert dialog.header_widget.height() == 60, f"Header高度应为60px,实际{dialog.header_widget.height()}px"

    # 验证Provider名称标签
    assert dialog.provider_name_label.text() != "", "Provider名称不应为空"

    # 验证外部链接按钮
    assert dialog.external_link_btn.size().width() == 28, "外部链接按钮宽度应为28px"
    assert dialog.external_link_btn.size().height() == 28, "外部链接按钮高度应为28px"

    # 验证Toggle开关
    assert dialog.provider_toggle is not None, "Toggle开关应存在"

    dialog.close()
    print("✓ Header区域测试通过")


def test_api_key_section():
    """测试: API密钥区域"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证输入框高度
    assert dialog.api_key_input.height() == 40, f"API密钥输入框高度应为40px,实际{dialog.api_key_input.height()}px"

    # 验证密码模式
    assert dialog.api_key_input.echoMode() == QLineEdit.Password, "API密钥应为密码模式"

    # 验证占位符
    assert dialog.api_key_input.placeholderText() != "", "API密钥输入框应有占位符"

    dialog.close()
    print("✓ API密钥区域测试通过")


def test_api_url_section():
    """测试: API地址区域"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证输入框高度
    assert dialog.api_url_input.height() == 40, f"API地址输入框高度应为40px,实际{dialog.api_url_input.height()}px"

    # 验证占位符
    assert "https://" in dialog.api_url_input.placeholderText(), "API地址占位符应包含https://"

    dialog.close()
    print("✓ API地址区域测试通过")


def test_provider_config_loading():
    """测试: Provider配置加载"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 获取第一个provider
    controller = ConfigController.instance()
    providers = controller.get_providers()

    if len(providers) == 0:
        print("⚠ 跳过配置加载测试: 无provider")
        dialog.close()
        return

    first_provider = providers[0]
    provider_id = first_provider.get("id", "")

    # 加载配置
    dialog._load_provider_config(provider_id)
    QTest.qWait(50)

    # 验证Provider名称已更新
    expected_name = first_provider.get("name", "")
    assert dialog.provider_name_label.text() == expected_name, \
        f"Provider名称应为'{expected_name}',实际为'{dialog.provider_name_label.text()}'"

    dialog.close()
    print(f"✓ Provider配置加载测试通过: {expected_name}")


def test_immediate_save():
    """测试: 立即保存功能"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 选择第一个provider
    if dialog.provider_list.count() == 0:
        print("⚠ 跳过立即保存测试: 无provider")
        dialog.close()
        return

    first_item = dialog.provider_list.item(0)
    first_item.setSelected(True)
    QTest.qWait(50)

    provider_id = first_item.data(Qt.UserRole)

    # 修改API Key
    test_key = "test_key_12345"
    dialog.api_key_input.setText(test_key)
    QTest.qWait(50)

    # 验证已保存到ConfigController
    controller = ConfigController.instance()
    provider = controller.get_provider(provider_id)
    assert provider["api_key"] == test_key, "API Key应立即保存"

    # 修改API URL
    test_url = "https://test.api.com"
    dialog.api_url_input.setText(test_url)
    QTest.qWait(50)

    # 验证已保存
    provider = controller.get_provider(provider_id)
    assert provider["api_url"] == test_url, "API URL应立即保存"

    dialog.close()
    print("✓ 立即保存测试通过")


def test_toggle_sync():
    """测试: Toggle开关同步"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    if dialog.provider_list.count() == 0:
        print("⚠ 跳过Toggle同步测试: 无provider")
        dialog.close()
        return

    # 选择第一个provider
    first_item = dialog.provider_list.item(0)
    first_item.setSelected(True)
    QTest.qWait(50)

    provider_id = first_item.data(Qt.UserRole)

    # 切换Header Toggle
    original_state = dialog.provider_toggle.isChecked()
    dialog.provider_toggle.setChecked(not original_state)
    QTest.qWait(50)

    # 验证已保存到ConfigController
    controller = ConfigController.instance()
    provider = controller.get_provider(provider_id)
    assert provider["enabled"] == (not original_state), "Toggle状态应同步保存"

    dialog.close()
    print("✓ Toggle同步测试通过")


def test_visual_styling():
    """测试: 视觉样式符合Cherry Studio主题"""
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = ModelConfigDialog()
    dialog.show()
    QTest.qWait(100)

    # 验证Header样式
    header_style = dialog.header_widget.styleSheet()
    assert "background-color" in header_style, "Header应有背景色样式"
    assert "border-bottom" in header_style, "Header应有底部边框"

    # 验证输入框样式
    api_key_style = dialog.api_key_input.styleSheet()
    assert "border-radius" in api_key_style, "输入框应有圆角"

    api_url_style = dialog.api_url_input.styleSheet()
    assert "border-radius" in api_url_style, "输入框应有圆角"

    dialog.close()
    print("✓ 视觉样式测试通过")


def run_all_tests():
    """运行所有US3.3测试"""
    print("=" * 60)
    print("US3.3: Right Panel - Provider Configuration - 测试")
    print("=" * 60)

    test_right_panel_structure()
    test_header_section()
    test_api_key_section()
    test_api_url_section()
    test_provider_config_loading()
    test_immediate_save()
    test_toggle_sync()
    test_visual_styling()

    print("=" * 60)
    print("✅ 所有US3.3测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    # 运行自动化测试
    run_all_tests()

    # 可视化验证说明
    print("\n" + "=" * 60)
    print("可视化验证说明")
    print("=" * 60)
    print("\n验证项:")
    print("1. Header: Provider名称 (18px) + 外部链接按钮 + Toggle开关")
    print("2. API密钥区域: 标签 + 设置按钮 + 密码输入框 + 检测按钮")
    print("3. API地址区域: 标签 + 设置按钮 + 文本输入框")
    print("4. 输入框高度均为40px")
    print("5. 检测按钮宽度为80px")
    print("6. 修改配置立即保存")
    print("7. 整体风格: 与AI参数设置面板一致")
    print("=" * 60)
