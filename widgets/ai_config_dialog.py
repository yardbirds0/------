#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI配置界面 - 支持所有OpenAI参数和流式输出
根据openai接口.md的完整规范实现
"""

import sys
import os
import json
from typing import Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QSlider, QCheckBox,
    QTextEdit, QComboBox, QPushButton, QLabel, QTabWidget,
    QWidget, QSplitter, QScrollArea, QMessageBox, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QSettings
from PySide6.QtGui import QFont, QTextCursor
import requests


class QCollapsibleGroupBox(QGroupBox):
    """可折叠的分组框"""

    def __init__(self, title="", collapsed=True):
        super().__init__(title)
        self.collapsed = collapsed
        self.setup_ui()

    def setup_ui(self):
        self.setCheckable(True)
        self.setChecked(not self.collapsed)
        self.toggled.connect(self.toggle_content)

        # 初始状态
        if self.collapsed:
            self.setMaximumHeight(30)

    def toggle_content(self, checked):
        if checked:
            self.setMaximumHeight(16777215)  # 恢复最大高度
        else:
            self.setMaximumHeight(30)  # 只显示标题栏


class AITestThread(QThread):
    """AI连接测试线程"""

    finished = Signal(bool, str)  # 成功标志, 响应内容
    progress = Signal(str)  # 进度信息

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config

    def run(self):
        try:
            self.progress.emit("正在连接AI服务...")

            # 构建请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config['api_key']}"
            }

            payload = {
                "model": self.config['model'],
                "messages": [
                    {"role": "user", "content": "HI"}
                ]
            }

            # 添加选中的参数
            for param, value in self.config.items():
                if param not in ['api_url', 'api_key', 'model'] and value is not None:
                    payload[param] = value

            self.progress.emit("发送测试请求...")

            # 发送请求
            response = requests.post(
                self.config['api_url'],
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                self.finished.emit(True, f"连接成功！AI回复: {content}")
            else:
                self.finished.emit(False, f"请求失败: {response.status_code} - {response.text}")

        except Exception as e:
            self.finished.emit(False, f"连接失败: {str(e)}")


class ParameterWidget(QWidget):
    """参数控件组合"""

    def __init__(self, param_name: str, param_config: Dict[str, Any]):
        super().__init__()
        self.param_name = param_name
        self.param_config = param_config
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 参数头部：复选框 + 参数名
        header_layout = QHBoxLayout()

        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.setChecked(self.param_config.get('required', False))
        self.enable_checkbox.toggled.connect(self.on_enable_toggled)
        header_layout.addWidget(self.enable_checkbox)

        title_label = QLabel(f"{self.param_name}")
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(title_label)

        # 必需标记
        if self.param_config.get('required', False):
            required_label = QLabel("*")
            required_label.setStyleSheet("color: red; font-weight: bold;")
            header_layout.addWidget(required_label)
            self.enable_checkbox.setEnabled(False)  # 必需参数不能取消选择

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 参数描述
        if 'description' in self.param_config:
            desc_label = QLabel(self.param_config['description'])
            desc_label.setStyleSheet("color: #666; font-size: 11px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # 控件容器
        self.controls_widget = QWidget()
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        # 根据参数类型创建控件
        param_type = self.param_config.get('type', 'string')

        if param_type in ['number', 'float']:
            self.create_number_controls(controls_layout)
        elif param_type == 'integer':
            self.create_integer_controls(controls_layout)
        elif param_type == 'boolean':
            self.create_boolean_controls(controls_layout)
        elif param_type == 'array':
            self.create_array_controls(controls_layout)
        else:  # string
            self.create_string_controls(controls_layout)

        layout.addWidget(self.controls_widget)

        # 初始启用状态
        self.on_enable_toggled(self.enable_checkbox.isChecked())

    def create_number_controls(self, layout):
        """创建数字类型控件"""
        min_val = self.param_config.get('min', 0.0)
        max_val = self.param_config.get('max', 2.0)
        default_val = self.param_config.get('default', 1.0)
        step = self.param_config.get('step', 0.1)

        # 滑块
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(int(min_val * 100))
        self.slider.setMaximum(int(max_val * 100))
        self.slider.setValue(int(default_val * 100))
        layout.addWidget(self.slider)

        # 数值输入框
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setMinimum(min_val)
        self.spinbox.setMaximum(max_val)
        self.spinbox.setSingleStep(step)
        self.spinbox.setValue(default_val)
        self.spinbox.setDecimals(2)
        layout.addWidget(self.spinbox)

        # 双向绑定
        self.slider.valueChanged.connect(lambda v: self.spinbox.setValue(v / 100.0))
        self.spinbox.valueChanged.connect(lambda v: self.slider.setValue(int(v * 100)))

    def create_integer_controls(self, layout):
        """创建整数类型控件"""
        min_val = self.param_config.get('min', 1)
        max_val = self.param_config.get('max', 100)
        default_val = self.param_config.get('default', 1)

        # 滑块
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(default_val)
        layout.addWidget(self.slider)

        # 整数输入框
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(min_val)
        self.spinbox.setMaximum(max_val)
        self.spinbox.setValue(default_val)
        layout.addWidget(self.spinbox)

        # 双向绑定
        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)

    def create_boolean_controls(self, layout):
        """创建布尔类型控件"""
        self.checkbox = QCheckBox("启用")
        self.checkbox.setChecked(self.param_config.get('default', False))
        layout.addWidget(self.checkbox)

    def create_string_controls(self, layout):
        """创建字符串类型控件"""
        if 'choices' in self.param_config:
            # 下拉选择
            self.combobox = QComboBox()
            self.combobox.addItems(self.param_config['choices'])
            if 'default' in self.param_config:
                self.combobox.setCurrentText(str(self.param_config['default']))
            layout.addWidget(self.combobox)
        else:
            # 文本输入
            self.lineedit = QLineEdit()
            if 'default' in self.param_config:
                self.lineedit.setText(str(self.param_config['default']))
            layout.addWidget(self.lineedit)

    def create_array_controls(self, layout):
        """创建数组类型控件"""
        self.textedit = QTextEdit()
        self.textedit.setMaximumHeight(60)
        if 'default' in self.param_config:
            self.textedit.setPlainText(json.dumps(self.param_config['default']))
        layout.addWidget(self.textedit)

    def on_enable_toggled(self, enabled):
        """启用/禁用控件"""
        self.controls_widget.setEnabled(enabled)

    def is_enabled(self) -> bool:
        """检查参数是否启用"""
        return self.enable_checkbox.isChecked()

    def get_value(self) -> Any:
        """获取参数值"""
        if not self.is_enabled():
            return None

        param_type = self.param_config.get('type', 'string')

        if param_type in ['number', 'float']:
            return self.spinbox.value()
        elif param_type == 'integer':
            return self.spinbox.value()
        elif param_type == 'boolean':
            return self.checkbox.isChecked()
        elif param_type == 'array':
            try:
                return json.loads(self.textedit.toPlainText())
            except:
                return []
        else:  # string
            if hasattr(self, 'combobox'):
                return self.combobox.currentText()
            else:
                return self.lineedit.text()


class AIConfigurationDialog(QDialog):
    """AI配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI配置 - 完整参数设置")
        self.setFixedSize(1200, 800)
        self.setModal(True)

        self.settings = QSettings("FinancialTool", "AI_Mapper")
        self.parameter_widgets = {}

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 创建选项卡
        tab_widget = QTabWidget()

        # 基础配置选项卡
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "基础配置")

        # 高级参数选项卡
        advanced_tab = self.create_advanced_tab()
        tab_widget.addTab(advanced_tab, "高级参数")

        # 调试信息选项卡
        debug_tab = self.create_debug_tab()
        tab_widget.addTab(debug_tab, "调试信息")

        layout.addWidget(tab_widget)

        # 底部按钮
        button_layout = QHBoxLayout()

        # 测试连接按钮
        self.test_btn = QPushButton("🔗 测试连接")
        self.test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_btn)

        # 连接状态标签
        self.status_label = QLabel("未测试")
        button_layout.addWidget(self.status_label)

        button_layout.addStretch()

        # 确定和取消按钮
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self.save_and_accept)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def create_basic_tab(self) -> QWidget:
        """创建基础配置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 必需参数组
        required_group = QGroupBox("必需参数")
        required_layout = QFormLayout(required_group)

        # API URL
        self.api_url_edit = QLineEdit("https://api.openai.com/v1/chat/completions")
        required_layout.addRow("API URL *:", self.api_url_edit)

        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("输入API密钥...")
        required_layout.addRow("API Key *:", self.api_key_edit)

        # 模型
        self.model_edit = QLineEdit("gpt-4")
        required_layout.addRow("模型 *:", self.model_edit)

        layout.addWidget(required_group)

        # System Prompt
        prompt_group = QGroupBox("System Prompt")
        prompt_layout = QVBoxLayout(prompt_group)

        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setMaximumHeight(150)
        self.system_prompt_edit.setPlainText("你是一个专业的财务数据分析助手。")
        prompt_layout.addWidget(self.system_prompt_edit)

        layout.addWidget(prompt_group)

        # 流式输出选项
        stream_group = QGroupBox("输出选项")
        stream_layout = QFormLayout(stream_group)

        self.stream_checkbox = QCheckBox("启用流式输出")
        self.stream_checkbox.setToolTip("实时接收AI响应，提升用户体验")
        stream_layout.addRow("流式输出:", self.stream_checkbox)

        layout.addWidget(stream_group)

        layout.addStretch()
        return widget

    def create_advanced_tab(self) -> QWidget:
        """创建高级参数选项卡"""
        widget = QWidget()

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # 定义所有OpenAI参数
        parameters = {
            'temperature': {
                'type': 'number',
                'min': 0.0,
                'max': 2.0,
                'default': 1.0,
                'step': 0.1,
                'description': '采样温度，控制输出随机性。0-2之间，越高越随机。'
            },
            'top_p': {
                'type': 'number',
                'min': 0.0,
                'max': 1.0,
                'default': 1.0,
                'step': 0.1,
                'description': '核采样参数，控制候选token的概率质量。'
            },
            'max_tokens': {
                'type': 'integer',
                'min': 1,
                'max': 4096,
                'default': 1000,
                'description': '最大生成token数量，控制响应长度。'
            },
            'max_completion_tokens': {
                'type': 'integer',
                'min': 1,
                'max': 4096,
                'default': 1000,
                'description': '补全中最大token数，包括输出和推理token。'
            },
            'presence_penalty': {
                'type': 'number',
                'min': -2.0,
                'max': 2.0,
                'default': 0.0,
                'step': 0.1,
                'description': '存在惩罚，鼓励讨论新主题。-2到2之间。'
            },
            'frequency_penalty': {
                'type': 'number',
                'min': -2.0,
                'max': 2.0,
                'default': 0.0,
                'step': 0.1,
                'description': '频率惩罚，减少重复内容。-2到2之间。'
            },
            'n': {
                'type': 'integer',
                'min': 1,
                'max': 10,
                'default': 1,
                'description': '生成的候选响应数量。'
            },
            'stop': {
                'type': 'array',
                'default': [],
                'description': '停止序列，最多4个字符串。遇到时停止生成。'
            },
            'logprobs': {
                'type': 'boolean',
                'default': False,
                'description': '是否返回token的对数概率。'
            },
            'user': {
                'type': 'string',
                'default': '',
                'description': '最终用户的唯一标识符。'
            }
        }

        # 创建参数控件
        for param_name, param_config in parameters.items():
            param_widget = ParameterWidget(param_name, param_config)
            self.parameter_widgets[param_name] = param_widget

            # 添加分隔线
            if param_name != list(parameters.keys())[-1]:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                layout.addWidget(separator)

            layout.addWidget(param_widget)

        scroll.setWidget(content_widget)

        main_layout = QVBoxLayout(widget)
        main_layout.addWidget(scroll)

        return widget

    def create_debug_tab(self) -> QWidget:
        """创建调试信息选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 请求头信息
        request_group = QCollapsibleGroupBox("请求头", collapsed=True)
        request_layout = QVBoxLayout(request_group)

        self.request_headers_edit = QTextEdit()
        self.request_headers_edit.setMaximumHeight(120)
        self.request_headers_edit.setReadOnly(True)
        request_layout.addWidget(self.request_headers_edit)

        layout.addWidget(request_group)

        # 接收信息
        response_group = QCollapsibleGroupBox("接收信息", collapsed=True)
        response_layout = QVBoxLayout(response_group)

        self.received_messages_edit = QTextEdit()
        self.received_messages_edit.setMaximumHeight(120)
        self.received_messages_edit.setReadOnly(True)
        response_layout.addWidget(self.received_messages_edit)

        layout.addWidget(response_group)

        # JSON数据
        json_group = QCollapsibleGroupBox("JSON数据", collapsed=True)
        json_layout = QVBoxLayout(json_group)

        self.json_data_edit = QTextEdit()
        self.json_data_edit.setMaximumHeight(120)
        self.json_data_edit.setReadOnly(True)
        json_layout.addWidget(self.json_data_edit)

        layout.addWidget(json_group)

        # AI响应结果
        ai_response_group = QCollapsibleGroupBox("AI响应结果", collapsed=True)
        ai_response_layout = QVBoxLayout(ai_response_group)

        self.ai_response_edit = QTextEdit()
        self.ai_response_edit.setReadOnly(True)
        ai_response_layout.addWidget(self.ai_response_edit)

        layout.addWidget(ai_response_group)

        return widget

    def test_connection(self):
        """测试AI连接"""
        try:
            config = self.get_configuration()

            if not config['api_key']:
                QMessageBox.warning(self, "警告", "请输入API密钥！")
                return

            self.test_btn.setEnabled(False)
            self.status_label.setText("测试中...")

            # 更新调试信息
            self.update_debug_info(config)

            # 创建测试线程
            self.test_thread = AITestThread(config)
            self.test_thread.finished.connect(self.on_test_finished)
            self.test_thread.progress.connect(self.status_label.setText)
            self.test_thread.start()

        except Exception as e:
            self.on_test_finished(False, f"配置错误: {str(e)}")

    def on_test_finished(self, success: bool, message: str):
        """测试完成回调"""
        self.test_btn.setEnabled(True)

        if success:
            self.status_label.setText("✅ 连接成功")
            self.status_label.setStyleSheet("color: green;")

            # 更新AI响应信息
            self.ai_response_edit.setPlainText(message)

        else:
            self.status_label.setText("❌ 连接失败")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "连接失败", message)

    def update_debug_info(self, config: Dict[str, Any]):
        """更新调试信息"""
        # 更新请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key'][:10]}..."
        }
        self.request_headers_edit.setPlainText(json.dumps(headers, indent=2))

        # 更新JSON数据
        json_data = {
            "model": config['model'],
            "messages": [
                {"role": "user", "content": "HI"}
            ]
        }

        # 添加启用的参数
        for param, value in config.items():
            if param not in ['api_url', 'api_key', 'model'] and value is not None:
                json_data[param] = value

        self.json_data_edit.setPlainText(json.dumps(json_data, indent=2, ensure_ascii=False))

    def get_configuration(self) -> Dict[str, Any]:
        """获取当前配置"""
        config = {
            'api_url': self.api_url_edit.text().strip(),
            'api_key': self.api_key_edit.text().strip(),
            'model': self.model_edit.text().strip(),
            'system_prompt': self.system_prompt_edit.toPlainText().strip(),
            'stream': self.stream_checkbox.isChecked()
        }

        # 添加高级参数
        for param_name, widget in self.parameter_widgets.items():
            if widget.is_enabled():
                config[param_name] = widget.get_value()

        return config

    def save_settings(self):
        """保存设置"""
        config = self.get_configuration()

        # 保存到QSettings（不包含API密钥）
        for key, value in config.items():
            if key != 'api_key':
                self.settings.setValue(f"ai_config/{key}", value)

        # API密钥单独处理（可以选择是否保存）
        # self.settings.setValue("ai_config/api_key", config['api_key'])

    def load_settings(self):
        """加载设置"""
        # 加载基础设置
        self.api_url_edit.setText(
            self.settings.value("ai_config/api_url", "https://api.openai.com/v1/chat/completions")
        )
        self.model_edit.setText(
            self.settings.value("ai_config/model", "gpt-4")
        )
        self.system_prompt_edit.setPlainText(
            self.settings.value("ai_config/system_prompt", "你是一个专业的财务数据分析助手。")
        )
        self.stream_checkbox.setChecked(
            self.settings.value("ai_config/stream", False, type=bool)
        )

        # 加载高级参数
        # 这里可以添加从设置加载参数的逻辑

    def save_and_accept(self):
        """保存并接受"""
        self.save_settings()
        self.accept()


def main():
    """测试函数"""
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    dialog = AIConfigurationDialog()
    dialog.show()
    app.exec()


if __name__ == "__main__":
    main()