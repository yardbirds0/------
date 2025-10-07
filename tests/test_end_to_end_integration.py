# -*- coding: utf-8 -*-
"""
End-to-End Integration Test
端到端集成测试：标题栏 → 对话框 → 模型切换 → 配置保存

测试完整的用户工作流程
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

from components.chat.widgets.title_bar import CherryTitleBar
from components.chat.widgets.model_config_dialog import ModelConfigDialog
from components.chat.controllers.config_controller import ConfigController


class EndToEndTestWindow(QMainWindow):
    """端到端测试主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("End-to-End Integration Test")
        self.resize(800, 600)

        # 创建标题栏
        self.title_bar = CherryTitleBar()
        self.setMenuWidget(self.title_bar)

        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 测试信息显示
        self.info_label = QLabel("准备开始端到端测试...")
        self.info_label.setStyleSheet(
            "padding: 20px; font-size: 14px; background-color: #F5F5F5; border-radius: 5px;"
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # ConfigController
        self.controller = ConfigController.instance()

        # 测试结果
        self.test_results = []

    def log(self, message: str, success: bool = True):
        """记录测试结果"""
        prefix = "[OK]" if success else "[FAIL]"
        self.test_results.append(f"{prefix} {message}")
        print(f"{prefix} {message}")

    def run_automated_tests(self):
        """运行自动化测试"""
        self.log("=== 开始端到端集成测试 ===")

        # 测试1: 验证标题栏模型指示器显示
        self.test_title_bar_indicator()

        # 测试2: 验证ConfigController初始状态
        self.test_config_controller_state()

        # 测试3: 模拟点击标题栏打开对话框
        QTimer.singleShot(1000, self.test_open_dialog)

    def test_title_bar_indicator(self):
        """测试1: 标题栏模型指示器显示"""
        self.log("测试1: 标题栏模型指示器")

        # 检查indicator是否存在
        if hasattr(self.title_bar, 'model_indicator'):
            self.log("  - TitleBarModelIndicator 已添加到标题栏", True)
        else:
            self.log("  - TitleBarModelIndicator 未找到", False)
            return

        # 检查indicator显示内容
        indicator = self.title_bar.model_indicator
        model_text = indicator.model_label.text()
        provider_text = indicator.provider_label.text()

        if model_text and provider_text:
            self.log(f"  - 显示模型: {model_text} | {provider_text}", True)
        else:
            self.log("  - 模型显示文本为空", False)

    def test_config_controller_state(self):
        """测试2: ConfigController状态"""
        self.log("测试2: ConfigController 状态")

        # 获取当前模型
        provider_id, model_id = self.controller.get_current_model()
        if provider_id and model_id:
            self.log(f"  - 当前模型: {provider_id}/{model_id}", True)
        else:
            self.log("  - 未配置当前模型", False)

        # 获取providers
        providers = self.controller.get_providers()
        if len(providers) > 0:
            self.log(f"  - 加载了 {len(providers)} 个 providers", True)
        else:
            self.log("  - Providers 列表为空", False)

    def test_open_dialog(self):
        """测试3: 打开对话框"""
        self.log("测试3: 打开模型配置对话框")

        # 创建对话框
        dialog = ModelConfigDialog(self)

        # 检查对话框创建
        if dialog:
            self.log("  - ModelConfigDialog 创建成功", True)
        else:
            self.log("  - ModelConfigDialog 创建失败", False)
            return

        # 检查对话框大小
        if dialog.width() == 1200 and dialog.height() == 800:
            self.log("  - 对话框尺寸正确 (1200x800)", True)
        else:
            self.log(f"  - 对话框尺寸错误: {dialog.width()}x{dialog.height()}", False)

        # 检查provider列表
        provider_count = dialog.provider_list.count()
        if provider_count > 0:
            self.log(f"  - Provider列表已填充 ({provider_count} 项)", True)
        else:
            self.log("  - Provider列表为空", False)

        # 延迟执行模型选择测试
        QTimer.singleShot(500, lambda: self.test_model_selection(dialog))

        # 显示对话框
        dialog.show()

    def test_model_selection(self, dialog):
        """测试4: 模型选择"""
        self.log("测试4: 模型选择和立即应用")

        # 获取初始模型
        initial_provider, initial_model = self.controller.get_current_model()
        self.log(f"  - 初始模型: {initial_provider}/{initial_model}")

        # 选择第一个provider (如果不是当前的)
        if dialog.provider_list.count() > 0:
            first_item = dialog.provider_list.item(0)
            first_provider_id = first_item.data(Qt.UserRole)

            if first_provider_id != initial_provider:
                # 模拟选择
                first_item.setSelected(True)
                self.log(f"  - 选择了 provider: {first_provider_id}")

                # 延迟检查模型列表
                QTimer.singleShot(300, lambda: self.test_model_tree(dialog, first_provider_id))
            else:
                # 如果第一个是当前的,选择第二个
                if dialog.provider_list.count() > 1:
                    second_item = dialog.provider_list.item(1)
                    second_provider_id = second_item.data(Qt.UserRole)
                    second_item.setSelected(True)
                    self.log(f"  - 选择了 provider: {second_provider_id}")

                    QTimer.singleShot(300, lambda: self.test_model_tree(dialog, second_provider_id))
                else:
                    self.log("  - 只有一个 provider, 跳过切换测试")
                    QTimer.singleShot(1000, lambda: self.test_persistence(dialog))

    def test_model_tree(self, dialog, provider_id):
        """测试5: 模型树加载"""
        self.log("测试5: 模型树加载")

        # 检查是否有模型卡片
        models_container = dialog.models_container_layout
        model_card_count = models_container.count() - 1  # 减去stretch

        if model_card_count > 0:
            self.log(f"  - 加载了 {model_card_count} 个模型分类卡片", True)

            # 尝试选择第一个模型
            # 获取第一个分类卡片
            first_card = models_container.itemAt(0).widget()
            if first_card and hasattr(first_card, 'radio_buttons'):
                radio_buttons = first_card.radio_buttons
                if len(radio_buttons) > 0:
                    # 选择第一个模型
                    first_radio = radio_buttons[0]
                    first_radio.setChecked(True)
                    self.log("  - 已选择第一个模型", True)

                    # 延迟检查配置更新
                    QTimer.singleShot(300, lambda: self.test_persistence(dialog))
                else:
                    self.log("  - 分类卡片没有 radio buttons", False)
                    QTimer.singleShot(1000, lambda: self.test_persistence(dialog))
            else:
                self.log("  - 无法获取分类卡片", False)
                QTimer.singleShot(1000, lambda: self.test_persistence(dialog))
        else:
            self.log("  - 模型树为空", False)
            QTimer.singleShot(1000, lambda: self.test_persistence(dialog))

    def test_persistence(self, dialog):
        """测试6: 配置持久化"""
        self.log("测试6: 配置持久化")

        # 获取当前模型
        current_provider, current_model = self.controller.get_current_model()
        self.log(f"  - 当前模型: {current_provider}/{current_model}")

        # 检查配置文件
        config_path = Path("config/ai_models.json")
        if config_path.exists():
            self.log("  - 配置文件存在", True)

            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            saved_provider = config.get("current_provider")
            saved_model = config.get("current_model")

            if saved_provider == current_provider and saved_model == current_model:
                self.log("  - 配置已正确保存到文件", True)
            else:
                self.log(
                    f"  - 配置不一致: 内存({current_provider}/{current_model}) vs 文件({saved_provider}/{saved_model})",
                    False
                )
        else:
            self.log("  - 配置文件不存在", False)

        # 关闭对话框
        dialog.close()

        # 显示测试结果
        QTimer.singleShot(500, self.show_test_results)

    def show_test_results(self):
        """显示测试结果"""
        self.log("=== 端到端集成测试完成 ===")

        # 统计结果
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.startswith("[OK]"))
        failed = total - passed

        results_text = "\n".join(self.test_results)
        results_text += f"\n\n总计: {total} | 通过: {passed} | 失败: {failed}"

        self.info_label.setText(results_text)

        # 如果有失败,标记为红色
        if failed > 0:
            self.info_label.setStyleSheet(
                "padding: 20px; font-size: 14px; background-color: #FFEBEE; "
                "border-radius: 5px; color: #C62828;"
            )
        else:
            self.info_label.setStyleSheet(
                "padding: 20px; font-size: 14px; background-color: #E8F5E9; "
                "border-radius: 5px; color: #2E7D32;"
            )


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 创建测试窗口
    window = EndToEndTestWindow()
    window.show()

    # 延迟启动自动化测试
    QTimer.singleShot(500, window.run_automated_tests)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
