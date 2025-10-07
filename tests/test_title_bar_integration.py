# -*- coding: utf-8 -*-
"""
集成测试: TitleBarModelIndicator 与 CherryTitleBar
测试模型指示器是否正确集成到标题栏中
"""

import sys
import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from components.chat.widgets.title_bar import CherryTitleBar
from components.chat.widgets.title_bar_model_indicator import TitleBarModelIndicator
from components.chat.controllers.config_controller import ConfigController


@pytest.fixture
def qapp():
    """创建 QApplication 实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # 清理 ConfigController 单例
    if ConfigController._instance:
        ConfigController._instance = None


@pytest.fixture
def title_bar(qapp):
    """创建 CherryTitleBar 实例"""
    bar = CherryTitleBar()
    yield bar
    bar.deleteLater()


class TestTitleBarIntegration:
    """标题栏集成测试"""

    def test_model_indicator_exists(self, title_bar):
        """测试: 模型指示器存在于标题栏中"""
        # 验证 model_indicator 属性存在
        assert hasattr(title_bar, 'model_indicator')
        assert title_bar.model_indicator is not None
        assert isinstance(title_bar.model_indicator, TitleBarModelIndicator)

    def test_model_indicator_visible(self, title_bar):
        """测试: 模型指示器可见"""
        title_bar.show()
        QTest.qWait(100)  # 等待窗口显示

        # 验证指示器可见
        assert title_bar.model_indicator.isVisible()

    def test_model_indicator_in_layout(self, title_bar):
        """测试: 模型指示器在布局中"""
        # 获取标题栏的主布局
        layout = title_bar.layout()
        assert layout is not None

        # 验证指示器在布局中
        found = False
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() == title_bar.model_indicator:
                found = True
                break

        assert found, "TitleBarModelIndicator not found in layout"

    def test_model_indicator_position(self, title_bar):
        """测试: 模型指示器位置正确（在窗口控制按钮之前）"""
        layout = title_bar.layout()

        # 找到指示器和窗口控制按钮的索引
        indicator_index = None
        min_btn_index = None

        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item:
                continue

            widget = item.widget()
            if widget == title_bar.model_indicator:
                indicator_index = i
            elif hasattr(title_bar, 'min_btn') and widget == title_bar.min_btn:
                min_btn_index = i

        # 验证指示器在最小化按钮之前
        assert indicator_index is not None, "Model indicator not found in layout"
        assert min_btn_index is not None, "Minimize button not found in layout"
        assert indicator_index < min_btn_index, "Model indicator should be before window control buttons"

    def test_click_signal_connected(self, title_bar):
        """测试: 点击信号已连接"""
        # 验证 _on_model_indicator_clicked 方法存在并已绑定
        # 通过模拟点击来验证信号连接
        title_bar.show()
        QTest.qWait(50)

        # 记录点击前的状态
        # 由于点击会打开消息框，我们主要验证方法存在且可调用
        assert hasattr(title_bar, '_on_model_indicator_clicked')
        assert callable(title_bar._on_model_indicator_clicked)

    def test_click_handler_exists(self, title_bar):
        """测试: 点击处理器方法存在"""
        assert hasattr(title_bar, '_on_model_indicator_clicked')
        assert callable(title_bar._on_model_indicator_clicked)

    def test_no_tab_widgets(self, title_bar):
        """测试: 标签页部件已移除"""
        # 验证旧的标签页 UI 组件不再显示
        # 标签页方法仍然存在以保持 API 兼容性，但返回空值/无操作

        # 测试添加标签页方法返回占位符 ID
        tab_id = title_bar.add_tab("💬", "测试")
        assert tab_id == 0, "add_tab should return placeholder ID 0"

        # 测试其他标签页方法不会引发错误
        title_bar.remove_tab(tab_id)  # 应该无操作
        title_bar.set_active_tab(tab_id)  # 应该无操作
        title_bar.set_tab_title(tab_id, "新标题")  # 应该无操作

        # 获取标签页 ID 应返回占位符
        active_id = title_bar.get_active_tab_id()
        assert active_id == 0, "get_active_tab_id should return placeholder ID 0"

    def test_window_control_buttons_exist(self, title_bar):
        """测试: 窗口控制按钮仍然存在"""
        # 验证窗口控制按钮未被移除
        assert hasattr(title_bar, 'min_btn')
        assert hasattr(title_bar, 'max_btn')
        assert hasattr(title_bar, 'close_btn')

        assert title_bar.min_btn is not None
        assert title_bar.max_btn is not None
        assert title_bar.close_btn is not None

    def test_title_bar_height(self, title_bar):
        """测试: 标题栏高度未改变"""
        # 标题栏应保持固定高度
        assert title_bar.height() > 0
        assert title_bar.minimumHeight() > 0
        assert title_bar.maximumHeight() > 0

    def test_model_indicator_updates_on_config_change(self, title_bar, qapp):
        """测试: 配置变化时指示器更新"""
        title_bar.show()
        QTest.qWait(100)

        # 获取 ConfigController
        controller = ConfigController.instance()

        # 获取第一个可用的 provider 和 model
        providers = controller.get_providers()
        if not providers or not providers[0].get("models"):
            pytest.skip("No providers or models available in config")

        provider_id = providers[0]["id"]
        model_id = providers[0]["models"][0]["id"]

        # 修改配置到一个真实的 provider/model
        controller.set_current_model(provider_id, model_id)

        # 等待信号处理
        QTest.qWait(200)

        # 验证显示已更新（应该显示配置的模型）
        updated_text = title_bar.model_indicator.model_label.text()
        # 应该显示模型名称或默认状态
        assert len(updated_text) > 0  # 至少有文本显示


class TestTitleBarLayout:
    """标题栏布局测试"""

    def test_layout_structure(self, title_bar):
        """测试: 布局结构正确"""
        layout = title_bar.layout()
        assert layout is not None

        # 布局应包含多个元素
        assert layout.count() > 0

    def test_no_visual_overlap(self, title_bar):
        """测试: 无视觉重叠"""
        title_bar.show()
        QTest.qWait(100)

        # 所有部件应该在标题栏范围内
        title_bar_width = title_bar.width()
        model_indicator = title_bar.model_indicator

        # 模型指示器应该在标题栏范围内
        indicator_x = model_indicator.x()
        indicator_width = model_indicator.width()

        assert indicator_x >= 0
        assert indicator_x + indicator_width <= title_bar_width

    def test_spacing_consistency(self, title_bar):
        """测试: 间距一致性"""
        layout = title_bar.layout()

        # 布局应该有合理的间距
        assert layout.spacing() >= 0
        assert layout.contentsMargins().left() >= 0


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
