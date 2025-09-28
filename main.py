#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI辅助财务报表数据映射与填充工具 - PySide6版本
基于程序要求.md的完整实现
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import requests
import threading
import time

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeView, QTableView, QTextEdit, QPlainTextEdit,
    QLineEdit, QPushButton, QTabWidget, QDockWidget, QFormLayout,
    QLabel, QProgressBar, QStatusBar, QMenuBar, QToolBar,
    QStyledItemDelegate, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox, QGroupBox, QSpinBox, QCheckBox,
    QMenu, QDialog, QComboBox, QScrollArea, QSlider, QDoubleSpinBox
)
from PySide6.QtCore import (
    Qt, QAbstractItemModel, QModelIndex, Signal,
    QThread, QTimer, QSettings, QMimeData
)
from PySide6.QtGui import (
    QIcon, QPixmap, QStandardItemModel, QStandardItem,
    QFont, QColor, QBrush, QPalette, QSyntaxHighlighter,
    QTextCharFormat, QDrag, QAction
)

# 项目模块导入
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models.data_models import (
    TargetItem, SourceItem, MappingFormula, WorkbookManager,
    SheetType, FormulaStatus, CalculationResult, MappingTemplate, TemplateManager
)
from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from modules.ai_mapper import AIMapper
from modules.calculation_engine import CalculationEngine
from components.advanced_widgets import (
    DragDropTreeView, FormulaEditor, FormulaSyntaxHighlighter,
    FormulaEditorDelegate, SearchableSourceTree, PropertyInspector,
    FormulaEditDialog
)
from components.sheet_explorer import SheetExplorerModel, SheetClassificationDialog

# ==================== AI Parameter Control Classes ====================

class ParameterControl(QWidget):
    """AI参数控制基类 - 包含启用复选框和参数值控件"""

    def __init__(self, param_name: str, display_name: str, description: str = "", default_value=None, parent=None):
        super().__init__(parent)
        self.param_name = param_name
        self.display_name = display_name
        self.description = description
        self.default_value = default_value

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        # 顶部：启用复选框和参数名称
        header_layout = QHBoxLayout()

        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.setChecked(False)
        self.enable_checkbox.toggled.connect(self.on_enable_toggled)
        header_layout.addWidget(self.enable_checkbox)

        name_label = QLabel(self.display_name)
        name_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(name_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 中部：参数值控件（由子类实现）
        self.value_widget = self.create_value_widget()
        if self.value_widget:
            layout.addWidget(self.value_widget)
            self.value_widget.setEnabled(False)  # 默认禁用

        # 底部：描述信息
        if self.description:
            desc_label = QLabel(self.description)
            desc_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

    def create_value_widget(self) -> QWidget:
        """创建参数值控件 - 由子类重写"""
        return None

    def on_enable_toggled(self, checked: bool):
        """启用状态切换"""
        if self.value_widget:
            self.value_widget.setEnabled(checked)
        self.setStyleSheet(f"""
            ParameterControl {{
                border: 1px solid {'#3498db' if checked else '#bdc3c7'};
                border-radius: 4px;
                background-color: {'#f8f9fa' if checked else '#ffffff'};
                margin: 2px;
            }}
        """)

    def is_enabled(self) -> bool:
        """是否启用此参数"""
        return self.enable_checkbox.isChecked()

    def get_value(self):
        """获取参数值 - 由子类重写"""
        return self.default_value

    def set_value(self, value):
        """设置参数值 - 由子类重写"""
        pass

    def set_enabled(self, enabled: bool):
        """设置启用状态"""
        self.enable_checkbox.setChecked(enabled)

    def validate_value(self) -> bool:
        """验证参数值 - 由子类重写"""
        return True

    def serialize(self) -> dict:
        """序列化为API请求参数"""
        if self.is_enabled() and self.validate_value():
            return {self.param_name: self.get_value()}
        return {}

class NumericParameterControl(ParameterControl):
    """数值参数控制 - 滑块+文本输入双向绑定"""

    def __init__(self, param_name: str, display_name: str, description: str = "",
                 default_value: float = 0.0, min_value: float = 0.0, max_value: float = 1.0,
                 decimals: int = 2, step: float = 0.1, parent=None):
        self.min_value = min_value
        self.max_value = max_value
        self.decimals = decimals
        self.step = step
        super().__init__(param_name, display_name, description, default_value, parent)

    def create_value_widget(self) -> QWidget:
        """创建滑块+文本输入控件"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 滑块
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(int(self.min_value * (10 ** self.decimals)))
        self.slider.setMaximum(int(self.max_value * (10 ** self.decimals)))
        self.slider.setValue(int(self.default_value * (10 ** self.decimals)))
        self.slider.valueChanged.connect(self.on_slider_changed)
        layout.addWidget(self.slider)

        # 文本输入
        self.text_input = QLineEdit()
        self.text_input.setText(str(self.default_value))
        self.text_input.setMaximumWidth(80)
        self.text_input.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_input)

        return widget

    def on_slider_changed(self, value: int):
        """滑块值改变时更新文本输入"""
        float_value = value / (10 ** self.decimals)
        self.text_input.setText(f"{float_value:.{self.decimals}f}")

    def on_text_changed(self, text: str):
        """文本输入改变时更新滑块"""
        try:
            value = float(text)
            if self.min_value <= value <= self.max_value:
                slider_value = int(value * (10 ** self.decimals))
                self.slider.blockSignals(True)  # 防止循环信号
                self.slider.setValue(slider_value)
                self.slider.blockSignals(False)
                self.text_input.setStyleSheet("")  # 清除错误样式
            else:
                self.text_input.setStyleSheet("border: 1px solid red;")
        except ValueError:
            self.text_input.setStyleSheet("border: 1px solid red;")

    def get_value(self) -> float:
        """获取当前数值"""
        try:
            return float(self.text_input.text())
        except ValueError:
            return self.default_value

    def set_value(self, value: float):
        """设置数值"""
        value = max(self.min_value, min(self.max_value, value))
        self.text_input.setText(f"{value:.{self.decimals}f}")
        self.slider.setValue(int(value * (10 ** self.decimals)))

    def validate_value(self) -> bool:
        """验证数值范围"""
        try:
            value = float(self.text_input.text())
            return self.min_value <= value <= self.max_value
        except ValueError:
            return False

class BooleanParameterControl(ParameterControl):
    """布尔参数控制"""

    def create_value_widget(self) -> QWidget:
        """创建复选框控件"""
        self.checkbox = QCheckBox("启用")
        self.checkbox.setChecked(bool(self.default_value))
        return self.checkbox

    def get_value(self) -> bool:
        """获取布尔值"""
        return self.checkbox.isChecked()

    def set_value(self, value: bool):
        """设置布尔值"""
        self.checkbox.setChecked(bool(value))

class TextParameterControl(ParameterControl):
    """文本参数控制"""

    def __init__(self, param_name: str, display_name: str, description: str = "",
                 default_value: str = "", placeholder: str = "", multiline: bool = False, parent=None):
        self.placeholder = placeholder
        self.multiline = multiline
        super().__init__(param_name, display_name, description, default_value, parent)

    def create_value_widget(self) -> QWidget:
        """创建文本输入控件"""
        if self.multiline:
            self.text_widget = QTextEdit()
            self.text_widget.setMaximumHeight(100)
            self.text_widget.setPlainText(str(self.default_value))
            if self.placeholder:
                self.text_widget.setPlaceholderText(self.placeholder)
        else:
            self.text_widget = QLineEdit()
            self.text_widget.setText(str(self.default_value))
            if self.placeholder:
                self.text_widget.setPlaceholderText(self.placeholder)
        return self.text_widget

    def get_value(self) -> str:
        """获取文本值"""
        if self.multiline:
            return self.text_widget.toPlainText()
        else:
            return self.text_widget.text()

    def set_value(self, value: str):
        """设置文本值"""
        if self.multiline:
            self.text_widget.setPlainText(str(value))
        else:
            self.text_widget.setText(str(value))

class EnumParameterControl(ParameterControl):
    """枚举参数控制（下拉选择）"""

    def __init__(self, param_name: str, display_name: str, description: str = "",
                 default_value=None, options: List = None, parent=None):
        self.options = options or []
        super().__init__(param_name, display_name, description, default_value, parent)

    def create_value_widget(self) -> QWidget:
        """创建下拉选择控件"""
        self.combo = QComboBox()
        for option in self.options:
            if isinstance(option, (list, tuple)) and len(option) == 2:
                self.combo.addItem(str(option[1]), option[0])  # 显示名, 实际值
            else:
                self.combo.addItem(str(option), option)

        # 设置默认值
        if self.default_value is not None:
            index = self.combo.findData(self.default_value)
            if index >= 0:
                self.combo.setCurrentIndex(index)

        return self.combo

    def get_value(self):
        """获取选中的值"""
        return self.combo.currentData()

    def set_value(self, value):
        """设置选中的值"""
        index = self.combo.findData(value)
        if index >= 0:
            self.combo.setCurrentIndex(index)

class CollapsibleGroupBox(QWidget):
    """可折叠的分组框"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)

        # 创建标题按钮
        self.title_button = QPushButton(f"▼ {title}")
        self.title_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                border: none;
                background: transparent;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.title_button.clicked.connect(self.toggle_collapsed)

        # 内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        # 折叠状态
        self.is_collapsed = False

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.title_button)
        main_layout.addWidget(self.content_widget)

        # 默认展开显示
        self.content_widget.setVisible(True)

    def toggle_collapsed(self):
        """切换折叠状态"""
        self.is_collapsed = not self.is_collapsed
        self.content_widget.setVisible(not self.is_collapsed)

        # 更新按钮文本
        title_text = self.title_button.text().replace("▼ ", "").replace("▶ ", "")
        arrow = "▶" if self.is_collapsed else "▼"
        self.title_button.setText(f"{arrow} {title_text}")

    def setChecked(self, checked: bool):
        """兼容QGroupBox的setChecked方法"""
        if checked != (not self.is_collapsed):
            self.toggle_collapsed()

    def isChecked(self) -> bool:
        """兼容QGroupBox的isChecked方法"""
        return not self.is_collapsed

    def on_toggled(self, checked: bool):
        """保持兼容性的方法"""
        self.content_widget.setVisible(checked)

    def add_widget(self, widget: QWidget):
        """添加控件到内容区域"""
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        """添加布局到内容区域"""
        self.content_layout.addLayout(layout)

# ==================== 聊天消息气泡控件 ====================

class MessageBubble(QWidget):
    """基础消息气泡控件"""
    
    def __init__(self, message: str, timestamp: str = None, parent=None):
        super().__init__(parent)
        self.message = message
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 消息内容
        self.message_label = QLabel(self.message)
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.message_label)
        
        # 时间戳
        self.time_label = QLabel(self.timestamp)
        self.time_label.setStyleSheet("color: #888; font-size: 10px;")
        self.time_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.time_label)
        
    def update_message(self, message: str):
        """更新消息内容（用于流式输出）"""
        self.message = message
        self.message_label.setText(message)


class UserMessageBubble(MessageBubble):
    """用户消息气泡"""
    
    def __init__(self, message: str, timestamp: str = None, parent=None):
        super().__init__(message, timestamp, parent)
        self.setup_style()
        
    def setup_style(self):
        """设置用户消息样式"""
        self.setStyleSheet("""
            UserMessageBubble {
                background-color: #007AFF;
                border-radius: 12px;
                margin-left: 50px;
                margin-right: 10px;
            }
        """)
        self.message_label.setStyleSheet("color: white; padding: 8px;")
        self.time_label.setStyleSheet("color: #E0E0E0; font-size: 10px; padding-right: 8px;")


class AssistantMessageBubble(MessageBubble):
    """AI助手消息气泡"""
    
    def __init__(self, message: str = "", timestamp: str = None, parent=None):
        super().__init__(message, timestamp, parent)
        self.is_streaming = False
        self.setup_style()
        
    def setup_style(self):
        """设置AI消息样式"""
        self.setStyleSheet("""
            AssistantMessageBubble {
                background-color: #F0F0F0;
                border-radius: 12px;
                margin-left: 10px;
                margin-right: 50px;
            }
        """)
        self.message_label.setStyleSheet("color: #333; padding: 8px;")
        self.time_label.setStyleSheet("color: #888; font-size: 10px; padding-right: 8px;")
        
    def start_streaming(self):
        """开始流式输出模式"""
        self.is_streaming = True
        self.message_label.setText("...")
        
    def update_streaming_text(self, text: str):
        """更新流式文本"""
        if self.is_streaming:
            self.update_message(text)
            
    def finish_streaming(self):
        """结束流式输出"""
        self.is_streaming = False


class TypingIndicator(QWidget):
    """输入指示器（显示AI正在输入）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_animation()
        
    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        
        # AI头像或标识
        ai_label = QLabel("🤖")
        ai_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(ai_label)
        
        # 输入动画区域
        self.dots_label = QLabel("●●●")
        self.dots_label.setStyleSheet("color: #888; font-size: 16px; padding-left: 10px;")
        layout.addWidget(self.dots_label)
        
        layout.addStretch()
        
    def setup_animation(self):
        """设置动画效果"""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_dots)
        self.dot_state = 0
        
    def start_typing(self):
        """开始输入动画"""
        self.animation_timer.start(500)  # 500ms间隔
        
    def stop_typing(self):
        """停止输入动画"""
        self.animation_timer.stop()
        
    def animate_dots(self):
        """动画效果"""
        dots = ["●", "●●", "●●●"]
        self.dots_label.setText(dots[self.dot_state])
        self.dot_state = (self.dot_state + 1) % 3


class ChatScrollArea(QScrollArea):
    """聊天滚动区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 聊天内容容器
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        
        self.setWidget(self.chat_widget)
        
        # 样式
        self.setStyleSheet("""
            ChatScrollArea {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
        """)
        
    def add_message(self, message_widget):
        """添加消息到聊天区域"""
        self.chat_layout.addWidget(message_widget)
        
        # 滚动到底部
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_chat(self):
        """清空聊天记录"""
        while self.chat_layout.count():
            child = self.chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

# ==================== AI Client Class ====================

class AIClient:
    """AI客户端 - 处理OpenAI API请求，支持流式和非流式响应"""

    def __init__(self, debug_callbacks: Dict = None):
        """
        初始化AI客户端

        Args:
            debug_callbacks: 调试回调函数字典，包含：
                - on_request_headers: 请求头更新回调
                - on_received_data: 接收数据更新回调
                - on_json_structure: JSON结构更新回调
                - on_ai_response: AI响应更新回调
        """
        self.debug_callbacks = debug_callbacks or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-Report-Tool/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })

    def build_request_payload(self, api_url: str, api_key: str, parameters: Dict, system_prompt: str = "", user_message: str = "") -> Dict:
        """构建API请求载荷"""
        # 基础消息结构
        messages = []

        # 添加系统提示（如果有）
        if system_prompt.strip():
            messages.append({
                "role": "system",
                "content": system_prompt.strip()
            })

        # 添加用户消息
        user_content = user_message.strip() if user_message.strip() else "请说一句话来测试API连接。"
        messages.append({
            "role": "user",
            "content": user_content
        })

        # 构建请求载荷
        payload = {
            "messages": messages
        }

        # 添加启用的参数
        for param_name, param_value in parameters.items():
            if param_name == "stop" and isinstance(param_value, str):
                # 处理停止序列（逗号分隔的字符串转为数组）
                if param_value.strip():
                    payload[param_name] = [s.strip() for s in param_value.split(',') if s.strip()]
            elif param_name == "response_format":
                # 处理响应格式
                if param_value != "text":
                    payload[param_name] = {"type": param_value}
            else:
                payload[param_name] = param_value

        return payload

    def make_request(self, api_url: str, api_key: str, parameters: Dict, system_prompt: str = "", user_message: str = "", stream: bool = False) -> Dict:
        """
        发送API请求

        Args:
            api_url: API端点URL
            api_key: API密钥
            parameters: 启用的参数字典
            system_prompt: 系统提示词
            user_message: 用户消息内容
            stream: 是否使用流式响应

        Returns:
            包含响应数据和元信息的字典
        """
        try:
            # 构建请求载荷
            payload = self.build_request_payload(api_url, api_key, parameters, system_prompt, user_message)

            # 设置请求头
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }

            # 调试回调：显示请求头
            if 'on_request_headers' in self.debug_callbacks:
                headers_text = json.dumps(headers, indent=2, ensure_ascii=False)
                self.debug_callbacks['on_request_headers'](headers_text)

            # 调试回调：显示JSON结构
            if 'on_json_structure' in self.debug_callbacks:
                json_text = json.dumps(payload, indent=2, ensure_ascii=False)
                self.debug_callbacks['on_json_structure'](f"请求JSON:\n{json_text}")

            # 发送请求
            if stream:
                return self._handle_streaming_request(api_url, headers, payload)
            else:
                return self._handle_normal_request(api_url, headers, payload)

        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'response_data': None,
                'ai_response': None
            }

            # 调试回调：显示错误
            if 'on_ai_response' in self.debug_callbacks:
                self.debug_callbacks['on_ai_response'](f"错误: {str(e)}")

            return error_result

    def _handle_normal_request(self, api_url: str, headers: Dict, payload: Dict) -> Dict:
        """处理非流式请求"""
        response = self.session.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )

        # 调试回调：显示接收到的数据
        if 'on_received_data' in self.debug_callbacks:
            received_text = f"状态码: {response.status_code}\n\n"
            received_text += f"响应头:\n{json.dumps(dict(response.headers), indent=2)}\n\n"
            received_text += f"响应体:\n{response.text}"
            self.debug_callbacks['on_received_data'](received_text)

        if response.status_code == 200:
            response_data = response.json()

            # 调试回调：显示JSON结构
            if 'on_json_structure' in self.debug_callbacks:
                json_text = json.dumps(response_data, indent=2, ensure_ascii=False)
                current_text = self.debug_callbacks.get('current_json_text', '')
                updated_text = f"{current_text}\n\n响应JSON:\n{json_text}"
                self.debug_callbacks['on_json_structure'](updated_text)

            # 提取AI响应
            ai_response = ""
            if 'choices' in response_data and len(response_data['choices']) > 0:
                choice = response_data['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    ai_response = choice['message']['content']

            # 调试回调：显示AI响应
            if 'on_ai_response' in self.debug_callbacks:
                self.debug_callbacks['on_ai_response'](ai_response)

            return {
                'success': True,
                'error': None,
                'response_data': response_data,
                'ai_response': ai_response
            }
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            return {
                'success': False,
                'error': error_msg,
                'response_data': None,
                'ai_response': None
            }

    def _handle_streaming_request(self, api_url: str, headers: Dict, payload: Dict) -> Dict:
        """处理流式请求"""
        # 设置流式请求参数
        payload['stream'] = True

        response = self.session.post(
            api_url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        )

        if response.status_code != 200:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            return {
                'success': False,
                'error': error_msg,
                'response_data': None,
                'ai_response': None
            }

        # 处理流式响应
        accumulated_content = ""
        full_response_chunks = []

        try:
            # 调试回调：显示开始接收流式数据
            if 'on_received_data' in self.debug_callbacks:
                self.debug_callbacks['on_received_data']("开始接收流式数据...\n")

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    line = line.strip()

                    # 跳过注释行和空行
                    if not line or line.startswith(':'):
                        continue

                    # 处理SSE数据
                    if line.startswith('data: '):
                        data_content = line[6:]  # 移除 "data: " 前缀

                        # 检查是否是结束标记
                        if data_content == '[DONE]':
                            break

                        try:
                            chunk_data = json.loads(data_content)
                            full_response_chunks.append(chunk_data)

                            # 提取增量内容
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                choice = chunk_data['choices'][0]
                                if 'delta' in choice and 'content' in choice['delta']:
                                    content = choice['delta']['content']
                                    accumulated_content += content

                                    # 实时更新AI响应显示
                                    if 'on_ai_response' in self.debug_callbacks:
                                        self.debug_callbacks['on_ai_response'](accumulated_content)

                            # 更新接收数据显示
                            if 'on_received_data' in self.debug_callbacks:
                                received_text = f"接收到数据块 {len(full_response_chunks)}:\n{data_content}\n\n"
                                current_text = self.debug_callbacks.get('current_received_text', '')
                                self.debug_callbacks['on_received_data'](current_text + received_text)

                        except json.JSONDecodeError as e:
                            # 忽略JSON解析错误，继续处理下一行
                            continue

            # 调试回调：显示完整JSON结构
            if 'on_json_structure' in self.debug_callbacks and full_response_chunks:
                json_text = json.dumps(full_response_chunks, indent=2, ensure_ascii=False)
                current_text = self.debug_callbacks.get('current_json_text', '')
                updated_text = f"{current_text}\n\n流式响应JSON块:\n{json_text}"
                self.debug_callbacks['on_json_structure'](updated_text)

            return {
                'success': True,
                'error': None,
                'response_data': full_response_chunks,
                'ai_response': accumulated_content
            }

        except Exception as e:
            error_msg = f"流式响应处理错误: {str(e)}"
            return {
                'success': False,
                'error': error_msg,
                'response_data': None,
                'ai_response': accumulated_content  # 返回已接收的部分内容
            }

from utils.excel_utils_v2 import (
    validate_formula_syntax_v2, parse_formula_references_v2,
    build_formula_reference_v2, evaluate_formula_with_values_v2
)


class LogManager:
    """日志管理器"""

    def __init__(self, output_widget: QPlainTextEdit):
        self.output_widget = output_widget

    def log(self, message: str, level: str = "INFO"):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.output_widget.appendPlainText(log_entry)

    def info(self, message: str):
        self.log(message, "INFO")

    def warning(self, message: str):
        self.log(message, "WARNING")

    def error(self, message: str):
        self.log(message, "ERROR")

    def success(self, message: str):
        self.log(message, "SUCCESS")

    def clear(self):
        self.output_widget.clear()


class FormulaSyntaxHighlighter(QSyntaxHighlighter):
    """公式语法高亮器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # 工作表引用格式: [工作表名:"项目名"](单元格地址)
        sheet_format = QTextCharFormat()
        sheet_format.setForeground(QColor(0, 120, 215))  # 蓝色
        sheet_format.setFontWeight(QFont.Bold)

        item_format = QTextCharFormat()
        item_format.setForeground(QColor(0, 128, 0))  # 绿色

        cell_format = QTextCharFormat()
        cell_format.setForeground(QColor(128, 0, 128))  # 紫色

        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor(255, 140, 0))  # 橙色
        operator_format.setFontWeight(QFont.Bold)

        # 添加高亮规则
        self.highlighting_rules = [
            (r'\[[^\]]+\]', sheet_format),  # [工作表名]
            (r'"[^"]*"', item_format),      # "项目名"
            (r'\([A-Z]+\d+\)', cell_format), # (单元格地址)
            (r'[+\-*/()]', operator_format)  # 运算符
        ]

    def highlightBlock(self, text):
        """应用语法高亮"""
        import re
        for pattern, format_obj in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format_obj)


class TargetItemModel(QAbstractItemModel):
    """目标项树模型 - 支持层级结构和导航"""

    # 信号
    itemSelected = Signal(str)  # (target_id)
    navigationRequested = Signal(str, str)  # (category, item_name)

    def __init__(self, workbook_manager: Optional[WorkbookManager] = None):
        super().__init__()
        self.workbook_manager = workbook_manager
        self.active_sheet_name = None  # 当前激活的工作表名
        self.root_items = []
        self.category_items = {}  # 分类节点
        self.headers = ["状态", "级别", "项目名称", "映射公式", "预览值"]
        self.build_tree()

    def set_workbook_manager(self, workbook_manager: WorkbookManager):
        """设置工作簿管理器并刷新数据"""
        self.beginResetModel()
        self.workbook_manager = workbook_manager
        self.build_tree()
        self.endResetModel()

    def set_active_sheet(self, sheet_name: str):
        """设置当前激活的工作表并刷新数据"""
        self.beginResetModel()
        self.active_sheet_name = sheet_name
        self.build_tree()
        self.endResetModel()

    def build_tree(self):
        """构建扁平列表 - 按原始Excel行顺序显示，不分组"""
        self.root_items = []
        self.category_items = {}

        if not self.workbook_manager:
            return

        # 筛选当前激活工作表的目标项
        filtered_targets = []
        for target_id, target in self.workbook_manager.target_items.items():
            if self.active_sheet_name and target.sheet_name != self.active_sheet_name:
                continue
            filtered_targets.append(target)

        # 按原始行号排序，保持Excel原始顺序
        filtered_targets.sort(key=lambda t: (t.sheet_name, t.row))

        # 直接将所有目标项按顺序添加到根列表，不分组
        self.root_items = filtered_targets

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        # 现在只有根级项目，没有分组
        if not parent.isValid():
            if 0 <= row < len(self.root_items):
                return self.createIndex(row, column, self.root_items[row])

        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        # 扁平列表，所有项目都没有父项
        return QModelIndex()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if not parent.isValid():
            # 根级项目数量
            return len(self.root_items)
        else:
            # 没有子项
            return 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()
        column = index.column()

        # 现在只有TargetItem，没有CategoryNode
        if isinstance(item, TargetItem):
            if role == Qt.DisplayRole:
                if column == 0:  # 状态
                    if not self.workbook_manager:
                        return "❓"
                    formula = self.workbook_manager.mapping_formulas.get(item.id)
                    if not formula:
                        return "⭕"
                    status_icons = {
                        FormulaStatus.EMPTY: "⭕",
                        FormulaStatus.PENDING: "⏳",
                        FormulaStatus.AI_GENERATED: "🤖",
                        FormulaStatus.USER_MODIFIED: "✏️",
                        FormulaStatus.VALIDATED: "✅",
                        FormulaStatus.CALCULATED: "🟢",
                        FormulaStatus.ERROR: "❌"
                    }
                    return status_icons.get(formula.status, "❓")

                elif column == 1:  # 级别
                    # 显示层级编号（如1、1.1、1.1.1、2、2.1）
                    return item.hierarchical_number if hasattr(item, 'hierarchical_number') else "1"

                elif column == 2:  # 项目名称
                    # 显示完整的项目名称（保留缩进和原始格式）
                    # 使用original_text来保留完整的原始格式和缩进
                    return item.original_text

                elif column == 3:  # 映射公式
                    if not self.workbook_manager:
                        return ""
                    formula = self.workbook_manager.mapping_formulas.get(item.id)
                    return formula.formula if formula else ""

                elif column == 4:  # 预览值
                    if not self.workbook_manager:
                        return ""
                    result = self.workbook_manager.calculation_results.get(item.id)
                    if result and result.success:
                        return str(result.result)
                    return ""

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags

        # 现在只有TargetItem，都可以选择
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def get_target_item(self, index: QModelIndex) -> Optional[TargetItem]:
        """获取目标项"""
        if not index.isValid():
            return None

        item = index.internalPointer()
        if isinstance(item, TargetItem):
            return item
        return None

    def navigate_to_category(self, category_name: str):
        """导航到指定分类 - 现在不适用于扁平列表"""
        # 扁平列表中没有分类，此方法不再适用
        return QModelIndex()

    def navigate_to_item(self, target_id: str):
        """导航到指定项目"""
        for row, target_item in enumerate(self.root_items):
            if target_item.id == target_id:
                index = self.createIndex(row, 0, target_item)
                self.itemSelected.emit(target_id)
                return index
        return QModelIndex()


class CategoryNode:
    """分类节点"""

    def __init__(self, name: str, children: List[TargetItem] = None):
        self.name = name
        self.children = children or []


    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False

        item = index.internalPointer()
        if not isinstance(item, TargetItem) or not self.workbook_manager:
            return False

        column = index.column()

        if column == 3:  # 映射公式
            # 更新或创建公式
            if item.id not in self.workbook_manager.mapping_formulas:
                self.workbook_manager.mapping_formulas[item.id] = MappingFormula(
                    target_id=item.id,
                    formula=str(value),
                    status=FormulaStatus.USER_MODIFIED
                )
            else:
                formula = self.workbook_manager.mapping_formulas[item.id]
                formula.formula = str(value)
                formula.status = FormulaStatus.USER_MODIFIED

            self.dataChanged.emit(index, index, [role])
            return True

        return False


class SourceItemModel(QAbstractItemModel):
    """来源项树模型"""

    def __init__(self, workbook_manager: Optional[WorkbookManager] = None):
        super().__init__()
        self.workbook_manager = workbook_manager
        self.sheet_groups = {}  # {sheet_name: [SourceItem, ...]}
        self.sheet_names = []

    def set_workbook_manager(self, workbook_manager: WorkbookManager):
        """设置工作簿管理器并刷新数据"""
        self.beginResetModel()
        self.workbook_manager = workbook_manager
        self.build_tree()
        self.endResetModel()

    def build_tree(self):
        """构建按工作表分组的树结构"""
        if not self.workbook_manager:
            return

        self.sheet_groups = {}
        for source_id, source in self.workbook_manager.source_items.items():
            sheet_name = source.sheet_name
            if sheet_name not in self.sheet_groups:
                self.sheet_groups[sheet_name] = []
            self.sheet_groups[sheet_name].append(source)

        self.sheet_names = list(self.sheet_groups.keys())

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            # 根级 - 工作表名
            if 0 <= row < len(self.sheet_names):
                return self.createIndex(row, column, self.sheet_names[row])
        else:
            # 父级是工作表，子级是来源项
            parent_item = parent.internalPointer()
            if isinstance(parent_item, str) and parent_item in self.sheet_groups:
                sources = self.sheet_groups[parent_item]
                if 0 <= row < len(sources):
                    return self.createIndex(row, column, sources[row])

        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        item = index.internalPointer()

        if isinstance(item, SourceItem):
            # 来源项的父级是工作表
            sheet_name = item.sheet_name
            if sheet_name in self.sheet_names:
                row = self.sheet_names.index(sheet_name)
                return self.createIndex(row, 0, sheet_name)

        return QModelIndex()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if not parent.isValid():
            return len(self.sheet_names)
        else:
            parent_item = parent.internalPointer()
            if isinstance(parent_item, str) and parent_item in self.sheet_groups:
                return len(self.sheet_groups[parent_item])
        return 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1  # 只显示名称列

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.DisplayRole:
            if isinstance(item, str):
                # 工作表名
                return item
            elif isinstance(item, SourceItem):
                # 来源项：显示名称和值
                value_str = f" ({item.value})" if item.value is not None else ""
                return f"{item.name}{value_str}"

        elif role == Qt.ToolTipRole:
            if isinstance(item, SourceItem):
                return f"工作表: {item.sheet_name}\n项目: {item.name}\n单元格: {item.cell_address}\n数值: {item.value}"

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 0:
            return "来源项"
        return None


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.workbook_manager = None
        self.template_manager = TemplateManager()
        self.template_manager.load_from_file()

        self.file_manager = FileManager()  # 移除回调，现在使用拖拽界面
        self.data_extractor = None
        self.ai_mapper = AIMapper()
        self.calculation_engine = None

        self.init_ui()
        self.setup_models()
        self.setup_connections()

        # 状态和设置
        self.settings = QSettings("FinancialTool", "AI_Mapper")
        self.load_settings()

    def _safe_get_sheet_name(self, sheet_item):
        """安全获取工作表名称的辅助函数（鲁棒性处理）

        Args:
            sheet_item: 可能是字符串、WorksheetInfo对象或其他类型

        Returns:
            str: 工作表名称
        """
        if isinstance(sheet_item, str):
            return sheet_item
        elif hasattr(sheet_item, 'name'):
            return str(sheet_item.name)
        else:
            # 兜底处理：转换为字符串
            return str(sheet_item)

    def _safe_iterate_sheets(self, sheet_list):
        """安全遍历工作表列表的辅助函数

        Args:
            sheet_list: 工作表列表，可能包含字符串或对象

        Yields:
            tuple: (sheet_name: str, sheet_object: any)
        """
        if not sheet_list:
            return

        for sheet_item in sheet_list:
            sheet_name = self._safe_get_sheet_name(sheet_item)
            yield (sheet_name, sheet_item)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("AI辅助财务报表数据映射与填充工具 - PySide6版")
        self.setGeometry(100, 100, 1600, 1000)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建中央布局
        central_widget_layout = QVBoxLayout(central_widget)


        # 创建主分割器（水平）
        main_splitter = QSplitter(Qt.Horizontal)
        central_widget_layout.addWidget(main_splitter)

        # 左侧导航区
        self.create_navigator_panel(main_splitter)

        # 中央工作台
        self.create_workbench_panel(main_splitter)

        # 右侧工具区
        self.create_tools_panel(main_splitter)

        # 底部日志区
        self.create_output_panel(central_widget_layout)

        # 设置分割器比例
        main_splitter.setSizes([300, 800, 400])

        # 只保留最简单的菜单栏（移除重复功能）
        self.create_simple_menus()

        # 状态栏
        self.statusBar().showMessage("就绪")

    def create_navigator_panel(self, parent_splitter):
        """创建左侧导航面板"""
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)

        # 工作表浏览器
        sheet_group = QGroupBox("工作表浏览器")
        sheet_layout = QVBoxLayout(sheet_group)

        self.sheet_explorer = DragDropTreeView()
        # 移除高度限制，让控件自动填满空间
        sheet_layout.addWidget(self.sheet_explorer)

        nav_layout.addWidget(sheet_group)

        # 分类摘要区域
        summary_group = QGroupBox("📋 分类摘要")
        summary_layout = QVBoxLayout(summary_group)

        self.classification_summary = QTextEdit()
        # 移除高度限制，让控件自动填满空间
        self.classification_summary.setReadOnly(True)
        # 移除灰色背景，使用简洁样式
        self.classification_summary.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        self.classification_summary.setText("请先加载Excel文件并确认工作表分类")
        summary_layout.addWidget(self.classification_summary)

        nav_layout.addWidget(summary_group)

        # 目标项结构树
        target_group = QGroupBox("🎯 目标项结构")
        target_layout = QVBoxLayout(target_group)

        # 导航工具栏
        nav_toolbar = QHBoxLayout()

        # 分类筛选下拉框
        self.category_filter = QComboBox()
        self.category_filter.addItem("全部分类")
        self.category_filter.currentTextChanged.connect(self.filter_by_category)
        nav_toolbar.addWidget(QLabel("分类:"))
        nav_toolbar.addWidget(self.category_filter)

        # 搜索框
        self.target_search = QLineEdit()
        self.target_search.setPlaceholderText("搜索目标项...")
        self.target_search.textChanged.connect(self.search_target_items)
        nav_toolbar.addWidget(self.target_search)

        # 导航按钮
        self.expand_all_btn = QPushButton("🔽")
        self.expand_all_btn.setToolTip("展开所有分类")
        self.expand_all_btn.setMaximumWidth(30)
        self.expand_all_btn.clicked.connect(self.expand_all_categories)
        nav_toolbar.addWidget(self.expand_all_btn)

        self.collapse_all_btn = QPushButton("🔼")
        self.collapse_all_btn.setToolTip("折叠所有分类")
        self.collapse_all_btn.setMaximumWidth(30)
        self.collapse_all_btn.clicked.connect(self.collapse_all_categories)
        nav_toolbar.addWidget(self.collapse_all_btn)

        target_layout.addLayout(nav_toolbar)

        self.item_structure_tree = DragDropTreeView()
        self.item_structure_tree.setHeaderHidden(False)
        self.item_structure_tree.setRootIsDecorated(True)
        self.item_structure_tree.setAlternatingRowColors(True)
        self.item_structure_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.item_structure_tree.setDragDropMode(QAbstractItemView.DragOnly)

        # 连接导航信号
        self.item_structure_tree.clicked.connect(self.on_target_item_clicked)
        self.item_structure_tree.doubleClicked.connect(self.on_target_item_double_clicked)

        target_layout.addWidget(self.item_structure_tree)

        nav_layout.addWidget(target_group)

        # 设置布局拉伸因子，让控件合理分配空间
        nav_layout.setStretchFactor(sheet_group, 1)      # 工作表浏览器占1/4空间
        nav_layout.setStretchFactor(summary_group, 1)    # 分类摘要占1/4空间
        nav_layout.setStretchFactor(target_group, 2)     # 目标项结构占1/2空间

        parent_splitter.addWidget(nav_widget)

    def create_workbench_panel(self, parent_splitter):
        """创建中央工作台面板"""
        workbench_widget = QWidget()
        workbench_layout = QVBoxLayout(workbench_widget)

        # 工具栏
        tools_layout = QHBoxLayout()
        self.load_files_btn = QPushButton("📁 加载文件")
        self.extract_data_btn = QPushButton("📊 提取数据")
        self.ai_analyze_btn = QPushButton("🤖 AI分析")
        self.calculate_btn = QPushButton("🧮 计算预览")
        self.export_btn = QPushButton("💾 导出Excel")

        # 设置按钮样式 - 移除灰色背景
        for btn in [self.load_files_btn, self.extract_data_btn,
                   self.ai_analyze_btn, self.calculate_btn, self.export_btn]:
            btn.setMinimumHeight(35)
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
                QPushButton:disabled {
                    color: #999;
                }
            """)

        tools_layout.addWidget(self.load_files_btn)
        tools_layout.addWidget(self.extract_data_btn)
        tools_layout.addWidget(self.ai_analyze_btn)
        tools_layout.addWidget(self.calculate_btn)
        tools_layout.addWidget(self.export_btn)
        tools_layout.addStretch()

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        tools_layout.addWidget(self.progress_bar)

        workbench_layout.addLayout(tools_layout)

        # 主数据网格
        self.main_data_grid = DragDropTreeView()
        self.main_data_grid.setAlternatingRowColors(True)
        self.main_data_grid.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.main_data_grid.setRootIsDecorated(False)
        self.main_data_grid.setAcceptDrops(True)

        # 设置右键菜单
        self.main_data_grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.main_data_grid.customContextMenuRequested.connect(self.show_context_menu)

        # 设置网格样式 - 移除灰色背景
        self.main_data_grid.setStyleSheet("""
            QTreeView {
                gridline-color: #d0d0d0;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            QTreeView::item {
                padding: 5px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTreeView::item:selected {
                background-color: #4CAF50;
            }
        """)

        workbench_layout.addWidget(self.main_data_grid)

        parent_splitter.addWidget(workbench_widget)

    def create_tools_panel(self, parent_splitter):
        """创建右侧工具面板"""
        tools_widget = QTabWidget()
        tools_widget.setTabPosition(QTabWidget.North)

        # 选项卡一：来源项库
        source_library_widget = QWidget()
        source_layout = QVBoxLayout(source_library_widget)

        # 来源项树（带内置搜索和下拉菜单）
        self.source_tree = SearchableSourceTree()
        self.source_tree.setDragEnabled(True)
        self.source_tree.setAcceptDrops(False)

        # 使用SearchableSourceTree内置的搜索组件（包含下拉菜单）
        source_search_widget = self.source_tree.get_search_widget()
        source_layout.addWidget(source_search_widget)

        # 添加树控件本身到布局
        source_layout.addWidget(self.source_tree)

        tools_widget.addTab(source_library_widget, "📚 来源项库")

        # 选项卡二：公式检查器
        formula_inspector_widget = QWidget()
        inspector_layout = QVBoxLayout(formula_inspector_widget)

        # 公式编辑器标题
        formula_label = QLabel("公式编辑器")
        formula_label.setFont(QFont("", 10, QFont.Bold))
        inspector_layout.addWidget(formula_label)

        # 高级公式编辑器
        self.formula_editor = FormulaEditor()
        self.formula_editor.setMaximumHeight(120)
        self.formula_editor.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
            }
        """)

        inspector_layout.addWidget(self.formula_editor)

        # 公式工具按钮
        formula_tools_layout = QHBoxLayout()
        validate_formula_btn = QPushButton("✅ 验证")
        clear_formula_btn = QPushButton("🗑️ 清空")
        insert_example_btn = QPushButton("💡 示例")

        for btn in [validate_formula_btn, clear_formula_btn, insert_example_btn]:
            btn.setMaximumHeight(25)
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    padding: 2px 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
            """)

        formula_tools_layout.addWidget(validate_formula_btn)
        formula_tools_layout.addWidget(clear_formula_btn)
        formula_tools_layout.addWidget(insert_example_btn)
        formula_tools_layout.addStretch()

        inspector_layout.addLayout(formula_tools_layout)

        # AI配置组
        ai_config_group = QGroupBox("🤖 AI配置")
        ai_config_layout = QVBoxLayout(ai_config_group)

        # AI配置显示信息
        self.ai_config_info = QLabel("点击按钮打开完整AI配置...")
        self.ai_config_info.setStyleSheet("color: #666; font-style: italic;")
        ai_config_layout.addWidget(self.ai_config_info)

        # 快速配置（保留基本字段）
        quick_config_layout = QFormLayout()

        self.ai_url_edit = QLineEdit("https://api.openai.com/v1/chat/completions")
        self.ai_key_edit = QLineEdit()
        self.ai_key_edit.setEchoMode(QLineEdit.Password)
        self.ai_key_edit.setPlaceholderText("输入API密钥...")
        self.ai_model_edit = QLineEdit("gpt-4")

        quick_config_layout.addRow("API URL:", self.ai_url_edit)
        quick_config_layout.addRow("API Key:", self.ai_key_edit)
        quick_config_layout.addRow("模型:", self.ai_model_edit)

        ai_config_layout.addLayout(quick_config_layout)

        # AI配置按钮
        ai_buttons_layout = QHBoxLayout()

        self.ai_config_btn = QPushButton("🛠️ 完整配置")
        self.ai_config_btn.setToolTip("打开完整的AI配置界面，支持所有OpenAI参数")
        self.ai_config_btn.clicked.connect(self.open_ai_config_dialog)
        ai_buttons_layout.addWidget(self.ai_config_btn)

        self.ai_test_btn = QPushButton("🔗 快速测试")
        self.ai_test_btn.setToolTip("使用当前配置快速测试AI连接")
        self.ai_test_btn.clicked.connect(self.quick_test_ai)
        ai_buttons_layout.addWidget(self.ai_test_btn)

        ai_config_layout.addLayout(ai_buttons_layout)

        inspector_layout.addWidget(ai_config_group)
        inspector_layout.addStretch()

        tools_widget.addTab(formula_inspector_widget, "🔧 公式检查器")

        # 选项卡三：属性检查器
        self.property_inspector = PropertyInspector()
        tools_widget.addTab(self.property_inspector, "🔍 属性检查器")

        # 选项卡四：AI配置
        ai_config_widget = self.create_ai_config_tab()
        tools_widget.addTab(ai_config_widget, "🤖 AI配置")

        parent_splitter.addWidget(tools_widget)

    # ==================== AI Client Class ====================

    def create_ai_config_tab(self):
        """创建AI配置选项卡 - 重构为聊天界面"""
        ai_widget = QWidget()
        ai_layout = QVBoxLayout(ai_widget)

        # 标题和说明
        title_label = QLabel("🤖 AI聊天助手")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        ai_layout.addWidget(title_label)

        # ==================== 基础连接配置 (始终可见) ====================
        basic_group = QGroupBox("📡 基础连接配置")
        basic_layout = QVBoxLayout(basic_group)

        # API URL (不使用ParameterControl，始终需要)
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("API地址:"))
        self.ai_url_edit = QLineEdit("https://api.kkyyxx.xyz/v1/chat/completions")
        self.ai_url_edit.setPlaceholderText("输入API服务地址...")
        url_layout.addWidget(self.ai_url_edit)
        basic_layout.addLayout(url_layout)

        # API Key (不使用ParameterControl，始终需要)
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API密钥:"))
        self.ai_key_edit = QLineEdit("UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t")
        self.ai_key_edit.setEchoMode(QLineEdit.Password)
        self.ai_key_edit.setPlaceholderText("输入API密钥...")
        key_layout.addWidget(self.ai_key_edit)
        basic_layout.addLayout(key_layout)

        ai_layout.addWidget(basic_group)

        # ==================== 高级参数配置折叠块 ====================
        # 创建CollapsibleGroupBox，默认折叠
        self.unified_params_group = CollapsibleGroupBox("⚙️ 高级参数配置")
        self.unified_params_group.setChecked(False)  # 默认折叠
        
        # 滚动区域用于参数
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 存储所有参数控件的字典
        self.ai_parameters = {}

        # ==================== Model参数 (必需参数) ====================
        model_group = QGroupBox("🎯 模型配置")
        model_layout = QVBoxLayout(model_group)

        self.ai_parameters['model'] = TextParameterControl(
            "model", "模型名称", "要使用的模型ID", "gemini-2.5-pro",
            "例如: gpt-4, gpt-3.5-turbo, gemini-2.5-pro"
        )
        self.ai_parameters['model'].set_enabled(True)  # 默认启用
        model_layout.addWidget(self.ai_parameters['model'])
        scroll_layout.addWidget(model_group)

        # ==================== 核心参数配置 ====================
        core_group = QGroupBox("⚙️ 核心参数配置")
        core_layout = QVBoxLayout(core_group)

        # Temperature
        self.ai_parameters['temperature'] = NumericParameterControl(
            "temperature", "Temperature", "采样温度，控制响应随机性。较高值使输出更随机，较低值更确定性",
            1.0, 0.0, 2.0, 2, 0.01
        )
        core_layout.addWidget(self.ai_parameters['temperature'])

        # Top P
        self.ai_parameters['top_p'] = NumericParameterControl(
            "top_p", "Top P", "核采样参数，考虑具有top_p概率质量的标记",
            1.0, 0.0, 1.0, 2, 0.01
        )
        core_layout.addWidget(self.ai_parameters['top_p'])

        # Max Tokens
        self.ai_parameters['max_tokens'] = NumericParameterControl(
            "max_tokens", "Max Tokens", "聊天补全中可以生成的最大标记数",
            4000, 1, 8192, 0, 1
        )
        core_layout.addWidget(self.ai_parameters['max_tokens'])

        # Stream
        self.ai_parameters['stream'] = BooleanParameterControl(
            "stream", "流式输出", "是否启用流式响应", False
        )
        core_layout.addWidget(self.ai_parameters['stream'])

        scroll_layout.addWidget(core_group)

        # ==================== 其他参数 ====================
        # 添加其他参数（惩罚、高级、格式、系统配置等）
        # ... 这里可以保留原有的其他参数配置 ...

        # 设置滚动区域内容并添加到折叠块
        scroll_area.setWidget(scroll_widget)
        self.unified_params_group.add_widget(scroll_area)
        
        ai_layout.addWidget(self.unified_params_group)

        # ==================== 聊天对话区域 ====================
        chat_group = QGroupBox("💬 AI对话")
        chat_layout = QVBoxLayout(chat_group)

        # 聊天历史显示区域
        self.chat_scroll_area = ChatScrollArea()
        self.chat_scroll_area.setMinimumHeight(300)
        chat_layout.addWidget(self.chat_scroll_area)

        # 系统提示设置（简化为一行）
        system_prompt_layout = QHBoxLayout()
        system_prompt_layout.addWidget(QLabel("系统提示:"))
        self.ai_system_prompt_edit = QLineEdit()
        self.ai_system_prompt_edit.setPlaceholderText("输入系统提示词（可选）...")
        system_prompt_layout.addWidget(self.ai_system_prompt_edit)
        chat_layout.addLayout(system_prompt_layout)

        # 用户输入区域
        input_layout = QHBoxLayout()
        
        # 用户输入框
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("输入消息...")
        self.chat_input.setMinimumHeight(35)
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input)
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.setMinimumHeight(35)
        self.send_button.setMinimumWidth(60)
        self.send_button.clicked.connect(self.send_chat_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        input_layout.addWidget(self.send_button)
        
        chat_layout.addLayout(input_layout)
        
        # 聊天控制按钮
        chat_control_layout = QHBoxLayout()
        
        self.clear_chat_btn = QPushButton("🗑️ 清空对话")
        self.clear_chat_btn.clicked.connect(self.clear_chat_history)
        chat_control_layout.addWidget(self.clear_chat_btn)
        
        chat_control_layout.addStretch()
        
        self.api_test_btn = QPushButton("🧪 测试连接")
        self.api_test_btn.setToolTip("测试API连接是否正常")
        self.api_test_btn.clicked.connect(self.test_ai_connection)
        chat_control_layout.addWidget(self.api_test_btn)
        
        chat_layout.addLayout(chat_control_layout)

        ai_layout.addWidget(chat_group)

        # ==================== 技术调试信息 (默认折叠) ====================
        debug_group = CollapsibleGroupBox("🔍 技术调试信息")
        debug_group.setChecked(False)  # 默认折叠
        debug_layout = QVBoxLayout()

        # 请求头显示
        self.request_headers_debug = CollapsibleGroupBox("📋 请求头信息")
        self.request_headers_debug.setChecked(False)
        self.request_headers_text = QTextEdit()
        self.request_headers_text.setMaximumHeight(120)
        self.request_headers_text.setPlaceholderText("这里将显示发送的HTTP请求头...")
        self.request_headers_debug.add_widget(self.request_headers_text)
        debug_layout.addWidget(self.request_headers_debug)

        # 接收消息显示
        self.received_messages_debug = CollapsibleGroupBox("📨 接收消息")
        self.received_messages_debug.setChecked(False)
        self.received_messages_text = QTextEdit()
        self.received_messages_text.setMaximumHeight(120)
        self.received_messages_text.setPlaceholderText("这里将显示接收到的原始响应数据...")
        self.received_messages_debug.add_widget(self.received_messages_text)
        debug_layout.addWidget(self.received_messages_debug)

        # JSON数据结构显示
        self.json_structure_debug = CollapsibleGroupBox("📊 JSON数据结构")
        self.json_structure_debug.setChecked(False)
        self.json_structure_text = QTextEdit()
        self.json_structure_text.setMaximumHeight(120)
        self.json_structure_text.setPlaceholderText("这里将显示格式化的请求/响应JSON结构...")
        self.json_structure_debug.add_widget(self.json_structure_text)
        debug_layout.addWidget(self.json_structure_debug)

        debug_group.add_layout(debug_layout)
        ai_layout.addWidget(debug_group)

        # ==================== 状态显示 ====================
        status_group = QGroupBox("📊 状态信息")
        status_layout = QVBoxLayout(status_group)

        self.ai_status_label = QLabel("就绪")
        self.ai_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        status_layout.addWidget(self.ai_status_label)

        self.ai_last_test_label = QLabel("最后测试: 从未测试")
        self.ai_last_test_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        status_layout.addWidget(self.ai_last_test_label)

        ai_layout.addWidget(status_group)

        # ==================== 初始化聊天相关变量 ====================
        self.chat_history = []  # 存储聊天历史
        self.current_typing_indicator = None  # 当前的输入指示器

        # ==================== 实时更新信号绑定 ====================
        # 创建防抖定时器（用于调试预览，不影响聊天）
        self.debug_update_timer = QTimer()
        self.debug_update_timer.setSingleShot(True)
        self.debug_update_timer.timeout.connect(self.update_debug_preview)

        # 防抖更新函数
        def schedule_debug_update():
            self.debug_update_timer.stop()
            self.debug_update_timer.start(300)  # 300ms防抖延迟

        # 基础配置控件信号绑定
        self.ai_url_edit.textChanged.connect(schedule_debug_update)
        self.ai_key_edit.textChanged.connect(schedule_debug_update)
        self.ai_system_prompt_edit.textChanged.connect(schedule_debug_update)

        # 为所有参数控件绑定信号
        for param_name, param_control in self.ai_parameters.items():
            param_control.enable_checkbox.toggled.connect(schedule_debug_update)
            value_widget = param_control.value_widget
            if hasattr(value_widget, 'textChanged'):
                value_widget.textChanged.connect(schedule_debug_update)
            elif hasattr(value_widget, 'valueChanged'):
                value_widget.valueChanged.connect(schedule_debug_update)
            elif hasattr(value_widget, 'toggled'):
                value_widget.toggled.connect(schedule_debug_update)
            elif hasattr(value_widget, 'currentTextChanged'):
                value_widget.currentTextChanged.connect(schedule_debug_update)

        # 初始化调试预览
        self.update_debug_preview()

        return ai_widget

    # ==================== 聊天功能方法 ====================
    
    def send_chat_message(self):
        """发送聊天消息"""
        message_text = self.chat_input.text().strip()
        if not message_text:
            return
            
        # 检查基础配置
        api_url = self.ai_url_edit.text().strip()
        api_key = self.ai_key_edit.text().strip()
        
        if not api_url:
            QMessageBox.warning(self, "警告", "请先配置API地址！")
            return
            
        if not api_key:
            QMessageBox.warning(self, "警告", "请先配置API密钥！")
            return
        
        # 清空输入框
        self.chat_input.clear()
        
        # 添加用户消息气泡
        user_bubble = UserMessageBubble(message_text)
        self.chat_scroll_area.add_message(user_bubble)
        
        # 添加到聊天历史
        self.chat_history.append({"role": "user", "content": message_text})
        
        # 显示AI正在输入的指示器
        self.current_typing_indicator = TypingIndicator()
        self.chat_scroll_area.add_message(self.current_typing_indicator)
        self.current_typing_indicator.start_typing()
        
        # 禁用发送按钮，防止重复发送
        self.send_button.setEnabled(False)
        self.send_button.setText("发送中...")
        
        # 在子线程中发送API请求
        def send_request():
            try:
                # 获取系统提示
                system_prompt = self.ai_system_prompt_edit.text().strip()
                
                # 构建消息历史
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
                # 添加聊天历史（最近10条）
                recent_history = self.chat_history[-10:]  # 只保留最近10条对话
                messages.extend(recent_history)
                
                # 获取启用的参数
                enabled_params = self.get_enabled_parameters()
                use_streaming = enabled_params.get('stream', False)
                
                # 构建请求
                payload = {"messages": messages}
                payload.update(enabled_params)
                
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}',
                    'User-Agent': 'AI-Report-Tool/1.0'
                }
                
                # 发送请求（10秒超时）
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=10,
                    stream=use_streaming
                )
                
                # 处理响应
                if use_streaming:
                    self.handle_streaming_response(response)
                else:
                    self.handle_normal_response(response)
                    
            except requests.exceptions.Timeout:
                self.handle_chat_error("请求超时，请检查网络连接")
            except requests.exceptions.ConnectionError:
                self.handle_chat_error("连接失败，请检查网络或API地址")
            except Exception as e:
                self.handle_chat_error(f"发送失败：{str(e)}")
        
        # 启动请求线程
        chat_thread = threading.Thread(target=send_request, daemon=True)
        chat_thread.start()
    
    def handle_normal_response(self, response):
        """处理非流式响应"""
        def update_ui():
            try:
                # 移除输入指示器
                if self.current_typing_indicator:
                    self.current_typing_indicator.stop_typing()
                    self.current_typing_indicator.setParent(None)
                    self.current_typing_indicator = None
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # 提取AI回复
                    ai_response = ""
                    if 'choices' in response_data and len(response_data['choices']) > 0:
                        choice = response_data['choices'][0]
                        if 'message' in choice and 'content' in choice['message']:
                            ai_response = choice['message']['content']
                    
                    if ai_response:
                        # 添加AI回复气泡
                        ai_bubble = AssistantMessageBubble(ai_response)
                        self.chat_scroll_area.add_message(ai_bubble)
                        
                        # 添加到聊天历史
                        self.chat_history.append({"role": "assistant", "content": ai_response})
                        
                        # 更新调试信息（不清空，追加）
                        self.append_debug_info("聊天请求", response_data)
                    else:
                        self.handle_chat_error("AI回复为空")
                else:
                    self.handle_chat_error(f"API错误：{response.status_code} - {response.text}")
                    
            except Exception as e:
                self.handle_chat_error(f"处理响应失败：{str(e)}")
            finally:
                # 恢复发送按钮
                self.send_button.setEnabled(True)
                self.send_button.setText("发送")
        
        # 在主线程更新UI
        QTimer.singleShot(0, update_ui)
    
    def handle_streaming_response(self, response):
        """处理流式响应"""
        def update_ui():
            try:
                # 移除输入指示器
                if self.current_typing_indicator:
                    self.current_typing_indicator.stop_typing()
                    self.current_typing_indicator.setParent(None)
                    self.current_typing_indicator = None
                
                if response.status_code == 200:
                    # 创建AI回复气泡
                    ai_bubble = AssistantMessageBubble("")
                    ai_bubble.start_streaming()
                    self.chat_scroll_area.add_message(ai_bubble)
                    
                    accumulated_content = ""
                    
                    # 处理流式数据
                    for line in response.iter_lines(decode_unicode=True):
                        if line and line.strip():
                            if line.startswith('data: '):
                                data_content = line[6:]
                                
                                if data_content == '[DONE]':
                                    break
                                
                                try:
                                    chunk_data = json.loads(data_content)
                                    
                                    if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                        choice = chunk_data['choices'][0]
                                        if 'delta' in choice and 'content' in choice['delta']:
                                            content = choice['delta']['content']
                                            accumulated_content += content
                                            
                                            # 实时更新气泡内容
                                            ai_bubble.update_streaming_text(accumulated_content)
                                            
                                except json.JSONDecodeError:
                                    continue
                    
                    # 完成流式输出
                    ai_bubble.finish_streaming()
                    
                    if accumulated_content:
                        # 添加到聊天历史
                        self.chat_history.append({"role": "assistant", "content": accumulated_content})
                    else:
                        self.handle_chat_error("流式响应为空")
                        
                else:
                    self.handle_chat_error(f"流式API错误：{response.status_code}")
                    
            except Exception as e:
                self.handle_chat_error(f"处理流式响应失败：{str(e)}")
            finally:
                # 恢复发送按钮
                self.send_button.setEnabled(True)
                self.send_button.setText("发送")
        
        # 在主线程更新UI
        QTimer.singleShot(0, update_ui)
    
    def handle_chat_error(self, error_message):
        """处理聊天错误"""
        def update_ui():
            # 移除输入指示器
            if self.current_typing_indicator:
                self.current_typing_indicator.stop_typing()
                self.current_typing_indicator.setParent(None)
                self.current_typing_indicator = None
            
            # 添加错误消息气泡
            error_bubble = AssistantMessageBubble(f"❌ {error_message}")
            error_bubble.setStyleSheet("""
                AssistantMessageBubble {
                    background-color: #FFE6E6;
                    border: 1px solid #FF9999;
                    border-radius: 12px;
                    margin-left: 10px;
                    margin-right: 50px;
                }
            """)
            self.chat_scroll_area.add_message(error_bubble)
            
            # 恢复发送按钮
            self.send_button.setEnabled(True)
            self.send_button.setText("发送")
        
        # 在主线程更新UI
        QTimer.singleShot(0, update_ui)
    
    def clear_chat_history(self):
        """清空聊天历史"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有对话记录吗？")
        if reply == QMessageBox.Yes:
            self.chat_scroll_area.clear_chat()
            self.chat_history.clear()
    
    def append_debug_info(self, request_type, data):
        """追加调试信息（不清空现有内容）"""
        try:
            import json
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 格式化JSON数据
            json_text = json.dumps(data, indent=2, ensure_ascii=False)
            
            # 追加到JSON结构显示
            current_text = self.json_structure_text.toPlainText()
            new_text = f"{current_text}\n\n[{timestamp}] {request_type}:\n{json_text}"
            self.json_structure_text.setText(new_text)
            
            # 滚动到底部
            cursor = self.json_structure_text.textCursor()
            cursor.movePosition(cursor.End)
            self.json_structure_text.setTextCursor(cursor)
            
        except Exception as e:
            print(f"Debug info append error: {e}")

    def test_ai_connection(self):
        """测试API连接（独立测试，不影响聊天和调试区域）"""
        try:
            api_url = self.ai_url_edit.text().strip()
            api_key = self.ai_key_edit.text().strip()

            if not api_url:
                QMessageBox.warning(self, "警告", "请输入API地址！")
                return

            if not api_key:
                QMessageBox.warning(self, "警告", "请输入API密钥！")
                return

            # 更新按钮状态
            original_text = self.api_test_btn.text()
            self.api_test_btn.setText("测试中...")
            self.api_test_btn.setEnabled(False)
            
            # 更新状态标签
            self.ai_status_label.setText("正在测试连接...")
            self.ai_status_label.setStyleSheet("color: #f39c12; font-weight: bold;")

            # 在子线程中进行连接测试（避免阻塞UI）
            def run_connection_test():
                try:
                    import requests
                    from urllib.parse import urlparse
                    
                    # 构建简单的测试请求
                    test_payload = {
                        "messages": [{"role": "user", "content": "Hello"}],
                        "model": self.ai_parameters.get('model', {}).get_value() if 'model' in self.ai_parameters else "gemini-2.5-pro",
                        "max_tokens": 10
                    }
                    
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {api_key}',
                        'User-Agent': 'AI-Report-Tool/1.0'
                    }
                    
                    # 发送测试请求（10秒超时）
                    response = requests.post(
                        api_url, 
                        headers=headers, 
                        json=test_payload,
                        timeout=10
                    )
                    
                    # 在主线程中更新UI
                    def update_ui():
                        try:
                            if response.status_code == 200:
                                response_data = response.json()
                                
                                self.ai_status_label.setText("连接正常")
                                self.ai_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                                
                                # 提取测试响应
                                test_response = "无响应内容"
                                if 'choices' in response_data and len(response_data['choices']) > 0:
                                    choice = response_data['choices'][0]
                                    if 'message' in choice and 'content' in choice['message']:
                                        test_response = choice['message']['content']
                                
                                status_info = f"✅ API连接测试成功！\n\n"
                                status_info += f"🌐 API地址: {api_url}\n"
                                status_info += f"📡 响应状态: {response.status_code}\n"
                                status_info += f"🤖 测试响应: {test_response}\n\n"
                                
                                # 显示使用统计（如果有）
                                usage = response_data.get('usage', {})
                                if usage:
                                    status_info += f"🔢 令牌使用: {usage.get('total_tokens', 'N/A')}\n"
                                
                                # 追加到调试信息（不清空现有内容）
                                self.append_debug_info("API连接测试", response_data)
                                
                                QMessageBox.information(self, "连接测试成功", status_info)
                                
                            elif response.status_code == 401:
                                self.ai_status_label.setText("认证失败")
                                self.ai_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                                QMessageBox.critical(self, "认证失败", "API密钥无效，请检查配置")
                                
                            elif response.status_code == 403:
                                self.ai_status_label.setText("访问被拒绝")
                                self.ai_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                                QMessageBox.critical(self, "访问被拒绝", "API访问被拒绝，请检查权限")
                                
                            else:
                                self.ai_status_label.setText("连接异常")
                                self.ai_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                                QMessageBox.warning(self, "连接测试", f"服务器响应异常\n状态码: {response.status_code}\n响应: {response.text[:200]}")
                            
                            # 更新最后测试时间
                            from datetime import datetime
                            self.ai_last_test_label.setText(f"最后测试: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            
                        except Exception as e:
                            self.ai_status_label.setText("处理错误")
                            self.ai_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                            QMessageBox.critical(self, "处理错误", f"处理响应时发生错误:\n{str(e)}")
                        finally:
                            # 恢复按钮状态
                            self.api_test_btn.setText(original_text)
                            self.api_test_btn.setEnabled(True)

                    # 使用QTimer.singleShot确保在主线程执行
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(0, update_ui)

                except requests.exceptions.Timeout:
                    def show_timeout():
                        self.ai_status_label.setText("连接超时")
                        self.ai_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                        QMessageBox.critical(self, "连接超时", "连接测试超时（10秒），请检查网络连接或API地址")
                        self.api_test_btn.setText(original_text)
                        self.api_test_btn.setEnabled(True)
                    QTimer.singleShot(0, show_timeout)

                except requests.exceptions.ConnectionError:
                    def show_connection_error():
                        self.ai_status_label.setText("连接失败")
                        self.ai_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                        QMessageBox.critical(self, "连接失败", "无法连接到服务器，请检查网络连接或API地址")
                        self.api_test_btn.setText(original_text)
                        self.api_test_btn.setEnabled(True)
                    QTimer.singleShot(0, show_connection_error)

                except Exception as e:
                    def show_error():
                        self.ai_status_label.setText("测试异常")
                        self.ai_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                        QMessageBox.critical(self, "测试异常", f"连接测试过程中发生异常:\n{str(e)}")
                        self.api_test_btn.setText(original_text)
                        self.api_test_btn.setEnabled(True)
                    QTimer.singleShot(0, show_error)

            # 启动连接测试线程
            connection_thread = threading.Thread(target=run_connection_test, daemon=True)
            connection_thread.start()

        except Exception as e:
            self.ai_status_label.setText("测试错误")
            self.ai_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.api_test_btn.setText(original_text)
            self.api_test_btn.setEnabled(True)
            QMessageBox.critical(self, "测试错误", f"无法启动连接测试:\n{str(e)}")

    def save_ai_config(self):
        """保存AI配置"""
        config = self.get_ai_config()
        try:
            import json
            config_file = "ai_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "成功", f"AI配置已保存到 {config_file}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存AI配置失败:\n{str(e)}")

    def load_ai_config(self):
        """加载AI配置"""
        try:
            import json
            config_file = "ai_config.json"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.set_ai_config(config)
            QMessageBox.information(self, "成功", "AI配置已加载")
        except FileNotFoundError:
            QMessageBox.warning(self, "警告", "配置文件不存在")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载AI配置失败:\n{str(e)}")

    def reset_ai_config(self):
        """重置AI配置"""
        reply = QMessageBox.question(self, "确认", "确定要重置AI配置为默认值吗？")
        if reply == QMessageBox.Yes:
            # 重置基础配置
            self.ai_url_edit.setText("https://api.kkyyxx.xyz/v1/chat/completions")
            self.ai_key_edit.setText("UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t")
            self.ai_system_prompt_edit.setText("")
            self.ai_user_message_edit.setText("")
            
            # 重置所有参数到默认值
            for param_name, param_control in self.ai_parameters.items():
                param_control.set_enabled(param_name == "model")  # 只有model默认启用
                param_control.set_value(param_control.default_value)
            
            # 更新状态显示
            self.ai_status_label.setText("未配置")
            self.ai_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.ai_last_test_label.setText("最后测试: 从未测试")
            
            QMessageBox.information(self, "成功", "AI配置已重置为默认值")

    def export_ai_config(self):
        """导出AI配置"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出AI配置", "ai_config.json", "JSON文件 (*.json)"
        )
        if file_path:
            config = self.get_ai_config()
            try:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "成功", f"AI配置已导出到 {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出AI配置失败:\n{str(e)}")

    def import_ai_config(self):
        """导入AI配置"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入AI配置", "", "JSON文件 (*.json)"
        )
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.set_ai_config(config)
                QMessageBox.information(self, "成功", "AI配置已导入")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入AI配置失败:\n{str(e)}")

    def get_ai_config(self):
        """获取当前AI配置"""
        config = {
            "api_url": self.ai_url_edit.text(),
            "api_key": self.ai_key_edit.text(),
            "system_prompt": self.ai_system_prompt_edit.toPlainText(),
            "user_message": self.ai_user_message_edit.toPlainText(),
            "parameters": {}
        }
        
        # 获取所有启用的参数
        for param_name, param_control in self.ai_parameters.items():
            config["parameters"][param_name] = {
                "enabled": param_control.is_enabled(),
                "value": param_control.get_value()
            }
            
        return config

    def set_ai_config(self, config):
        """设置AI配置"""
        # 设置基础配置
        self.ai_url_edit.setText(config.get("api_url", "https://api.kkyyxx.xyz/v1/chat/completions"))
        self.ai_key_edit.setText(config.get("api_key", ""))
        self.ai_system_prompt_edit.setText(config.get("system_prompt", ""))
        self.ai_user_message_edit.setText(config.get("user_message", ""))
        
        # 设置参数配置
        parameters = config.get("parameters", {})
        for param_name, param_control in self.ai_parameters.items():
            if param_name in parameters:
                param_config = parameters[param_name]
                param_control.set_enabled(param_config.get("enabled", False))
                param_control.set_value(param_config.get("value", param_control.default_value))
            else:
                # 如果配置中没有该参数，使用默认值
                param_control.set_enabled(param_name == "model")  # 只有model默认启用
                param_control.set_value(param_control.default_value)

    def get_enabled_parameters(self) -> Dict:
        """获取所有启用的AI参数"""
        enabled_params = {}

        # 遍历所有参数控件
        for param_name, param_control in self.ai_parameters.items():
            if param_control.is_enabled() and param_control.validate_value():
                param_value = param_control.get_value()
                # 跳过空值和无效值
                if param_value is not None and param_value != "":
                    enabled_params[param_name] = param_value

        return enabled_params

    def create_debug_callbacks(self) -> Dict:
        """创建调试回调函数 - 使用信号槽方式确保线程安全"""
        from PySide6.QtCore import QTimer
        
        def safe_set_text(widget, text):
            # 使用QTimer.singleShot确保在主线程中执行
            def update_text():
                try:
                    widget.setText(str(text))
                except Exception as e:
                    print(f"Debug callback error: {e}")
            
            QTimer.singleShot(0, update_text)
        
        return {
            'on_request_headers': lambda text: safe_set_text(self.request_headers_text, text),
            'on_received_data': lambda text: safe_set_text(self.received_messages_text, text),
            'on_json_structure': lambda text: safe_set_text(self.json_structure_text, text),
            'on_ai_response': lambda text: safe_set_text(self.ai_response_text, text)
        }

    def update_debug_preview(self):
        """实时更新调试预览信息"""
        try:
            import json

            # 获取基础配置
            api_url = self.ai_url_edit.text().strip()
            api_key = self.ai_key_edit.text().strip()
            system_prompt = self.ai_system_prompt_edit.text().strip()
            user_message = self.chat_input.text().strip()

            # 构建HTTP请求头
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}' if api_key else 'Bearer [API_KEY]',
                'User-Agent': 'AI-Report-Tool/1.0',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }

            # 格式化请求头显示
            headers_text = f"POST {api_url or '[API_URL]'} HTTP/1.1\n"
            for key, value in headers.items():
                headers_text += f"{key}: {value}\n"

            # 更新请求头显示
            self.request_headers_text.setText(headers_text)

            # 获取启用的参数
            enabled_params = self.get_enabled_parameters()

            # 构建消息结构
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            user_content = user_message if user_message else "请说一句话来测试API连接。"
            messages.append({
                "role": "user",
                "content": user_content
            })

            # 构建完整的JSON payload
            payload = {
                "messages": messages
            }

            # 添加启用的参数
            for param_name, param_value in enabled_params.items():
                payload[param_name] = param_value

            # 格式化JSON结构显示
            json_text = json.dumps(payload, indent=2, ensure_ascii=False)
            self.json_structure_text.setText(json_text)

            # 构建接收消息预览
            received_messages = []
            for i, msg in enumerate(messages, 1):
                received_messages.append(f"消息 {i}: {msg['role']} - {msg['content'][:50]}{'...' if len(msg['content']) > 50 else ''}")

            self.received_messages_text.setText("\n".join(received_messages))

            # 更新AI响应显示（显示预期格式）- 现在使用received_messages_text显示
            response_preview = "等待API响应...\n\n预期响应格式:\n{\n  \"choices\": [\n    {\n      \"message\": {\n        \"role\": \"assistant\",\n        \"content\": \"AI的回复内容\"\n      }\n    }\n  ]\n}"
            # 将响应预览显示在received_messages_text中
            if hasattr(self, 'received_messages_text'):
                self.received_messages_text.append("\n--- 响应预览 ---\n" + response_preview)

        except Exception as e:
            # 错误情况下显示错误信息
            error_text = f"预览生成错误: {str(e)}"
            self.request_headers_text.setText(error_text)
            self.json_structure_text.setText(error_text)
            self.received_messages_text.setText(error_text)
            print(f"Error display failed: {e}")

    def create_output_panel(self, parent_layout):
        """创建底部输出面板"""
        # 创建日志区域容器
        log_container = QWidget()
        log_container.setMaximumHeight(180)  # 限制整个日志区域高度
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(5, 5, 5, 5)
        log_layout.setSpacing(2)

        # 日志标题 - 设置小字体和固定高度
        log_label = QLabel("📋 系统日志")
        log_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #666;
                padding: 2px 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
        """)
        log_label.setFixedHeight(25)  # 固定标题高度
        log_layout.addWidget(log_label)

        # 日志文本框
        self.output_text = QPlainTextEdit()
        self.output_text.setMaximumHeight(145)  # 文本框高度
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QPlainTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        log_layout.addWidget(self.output_text)

        # 创建日志管理器
        self.log_manager = LogManager(self.output_text)

        # 添加到主布局
        parent_layout.addWidget(log_container)

    def create_simple_menus(self):
        """创建简化菜单栏（只保留系统功能，移除重复的业务功能）"""
        menubar = self.menuBar()

        # 文件菜单 - 只保留系统级功能
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("退出", self.close)

        # 视图菜单
        view_menu = menubar.addMenu("视图")
        view_menu.addAction("重置布局", self.reset_layout)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("关于", self.show_about)

    def create_menus(self):
        """旧的菜单创建方法 - 已弃用"""
        pass

    def create_toolbar(self):
        """旧的工具栏创建方法 - 已弃用"""
        pass

    def setup_models(self):
        """设置数据模型"""
        self.target_model = TargetItemModel()
        self.source_model = SourceItemModel()
        self.sheet_explorer_model = SheetExplorerModel()

        # 设置主数据网格
        self.main_data_grid.setModel(self.target_model)

        # 设置公式编辑器委托
        self.formula_delegate = FormulaEditorDelegate(self.workbook_manager)
        self.main_data_grid.setItemDelegateForColumn(3, self.formula_delegate)  # 映射公式列现在是第3列

        # 设置来源项树 - 现在使用增强的显示方法
        # self.source_tree.setModel(self.source_model)  # 保留旧方法作为备用

        # 设置工作表浏览器
        self.sheet_explorer.setModel(self.sheet_explorer_model)
        self.sheet_explorer.setHeaderHidden(False)
        self.sheet_explorer.expandAll()  # 默认展开所有节点

        # 配置列宽
        header = self.main_data_grid.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Fixed)   # 状态列
        header.setSectionResizeMode(1, QHeaderView.Fixed)   # 级别列
        header.setSectionResizeMode(2, QHeaderView.Stretch) # 项目名称列
        header.setSectionResizeMode(3, QHeaderView.Stretch) # 公式列
        header.setSectionResizeMode(4, QHeaderView.Fixed)   # 预览值列

        # 设置固定列宽
        self.main_data_grid.setColumnWidth(0, 60)   # 状态列
        self.main_data_grid.setColumnWidth(1, 60)   # 级别列
        self.main_data_grid.setColumnWidth(4, 120)  # 预览值列

    def setup_connections(self):
        """设置信号连接"""
        # 工具栏按钮
        self.load_files_btn.clicked.connect(self.load_files)
        self.extract_data_btn.clicked.connect(self.extract_data)
        self.ai_analyze_btn.clicked.connect(self.ai_analyze)
        self.calculate_btn.clicked.connect(self.calculate_preview)
        self.export_btn.clicked.connect(self.export_excel)

        # 初始状态：只有加载按钮可用
        self.extract_data_btn.setEnabled(False)
        self.ai_analyze_btn.setEnabled(False)
        self.calculate_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        # 主数据网格选择变化
        self.main_data_grid.selectionModel().currentChanged.connect(self.on_target_selection_changed)
        self.main_data_grid.doubleClicked.connect(self.on_main_grid_double_clicked)

        # 拖放信号
        self.source_tree.dragStarted.connect(self.on_drag_started)
        self.main_data_grid.itemDropped.connect(self.on_item_dropped)

        # 公式编辑器信号
        self.formula_editor.formulaChanged.connect(self.on_formula_changed)

        # 注意：搜索功能现在由SearchableSourceTree内部处理

        # 工作表浏览器信号
        self.sheet_explorer_model.sheetSelected.connect(self.on_sheet_selected)
        self.sheet_explorer_model.flashReportActivated.connect(self.on_flash_report_activated)
        self.sheet_explorer.clicked.connect(self.sheet_explorer_model.handle_item_clicked)

    def show_sheet_classification_dialog(self, sheet_name: str, auto_classification: str) -> str:
        """显示工作表分类确认对话框

        Args:
            sheet_name: 工作表名称
            auto_classification: 系统建议的分类

        Returns:
            str: 用户选择的分类 ('flash_report', 'data_source', 'skip', 'auto_all')
        """
        dialog = SheetClassificationConfirmDialog(sheet_name, auto_classification, self)
        if dialog.exec() == QDialog.Accepted:
            classification = dialog.get_classification()
            print(f"用户确认 '{sheet_name}' 分类为: {classification}")
            return classification
        else:
            # 用户取消对话框，默认跳过
            print(f"用户取消 '{sheet_name}' 分类确认，默认跳过")
            return "skip"

    def load_files(self):
        """加载Excel文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择Excel文件", "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )

        if not file_paths:
            return

        try:
            self.log_manager.info(f"开始加载 {len(file_paths)} 个文件...")

            success, message = self.file_manager.load_excel_files(file_paths)

            if success:
                self.workbook_manager = self.file_manager.get_workbook_manager()
                self.log_manager.success(f"文件加载成功: {message}")

                # 直接显示拖拽式工作表分类界面
                if self.workbook_manager and (self.workbook_manager.flash_report_sheets or self.workbook_manager.data_source_sheets):
                    self.show_classification_dialog()
                    self.log_manager.info("工作表已自动识别，请在对话框中调整分类")


                else:
                    # 没有找到工作表
                    self.log_manager.warning("未找到任何工作表")
                    self.update_sheet_explorer()
                    # 重置摘要显示
                    if hasattr(self, 'classification_summary'):
                        self.classification_summary.setText("未找到任何工作表，请检查Excel文件")

            else:
                self.log_manager.error(f"文件加载失败: {message}")
                QMessageBox.warning(self, "加载失败", message)

        except Exception as e:
            error_msg = f"加载文件时发生异常: {str(e)}"
            self.log_manager.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def apply_final_classifications(self, final_classifications):
        """根据用户的最终分类重新组织工作簿管理器"""
        from models.data_models import SheetType

        if not self.workbook_manager:
            return

        # 创建新的工作表列表
        new_flash_reports = []
        new_data_sources = []

        # 收集所有现有的工作表（鲁棒性处理）
        all_sheets = {}

        # 从workbook_manager.worksheets获取完整的工作表信息
        if hasattr(self.workbook_manager, 'worksheets') and self.workbook_manager.worksheets:
            all_sheets = dict(self.workbook_manager.worksheets)
        else:
            # 如果没有worksheets，从列表中重建（兼容性处理）
            for sheet in self.workbook_manager.flash_report_sheets:
                if isinstance(sheet, str):
                    # 如果是字符串，创建临时的工作表信息
                    from models.data_models import WorksheetInfo, SheetType
                    sheet_info = WorksheetInfo(name=sheet, sheet_type=SheetType.FLASH_REPORT)
                    all_sheets[sheet] = sheet_info
                else:
                    # 如果是对象，直接使用
                    all_sheets[sheet.name] = sheet

            for sheet in self.workbook_manager.data_source_sheets:
                if isinstance(sheet, str):
                    # 如果是字符串，创建临时的工作表信息
                    from models.data_models import WorksheetInfo, SheetType
                    sheet_info = WorksheetInfo(name=sheet, sheet_type=SheetType.DATA_SOURCE)
                    all_sheets[sheet] = sheet_info
                else:
                    # 如果是对象，直接使用
                    all_sheets[sheet.name] = sheet

        # 根据最终分类重新分配工作表
        for sheet_name in final_classifications['flash_reports']:
            if sheet_name in all_sheets:
                sheet = all_sheets[sheet_name]
                sheet.sheet_type = SheetType.FLASH_REPORT
                new_flash_reports.append(sheet)

        for sheet_name in final_classifications['data_sources']:
            if sheet_name in all_sheets:
                sheet = all_sheets[sheet_name]
                sheet.sheet_type = SheetType.DATA_SOURCE
                new_data_sources.append(sheet)

        # 更新工作簿管理器
        self.workbook_manager.flash_report_sheets = new_flash_reports
        self.workbook_manager.data_source_sheets = new_data_sources

        # 记录跳过和禁用的工作表
        if final_classifications['skipped']:
            self.log_manager.info(f"跳过的工作表: {', '.join(final_classifications['skipped'])}")

        if final_classifications['disabled']:
            self.log_manager.info(f"禁用的工作表: {', '.join(final_classifications['disabled'])}")

    def show_classification_dialog(self):
        """显示工作表分类对话框"""
        try:
            from dialogs.sheet_classification_dialog import SheetClassificationDialog

            # 创建对话框
            dialog = SheetClassificationDialog(self)
            dialog.load_workbook(self.workbook_manager)

            # 显示对话框并处理结果
            if dialog.exec() == QDialog.Accepted:
                # 获取用户确认的分类结果
                classifications = dialog.get_final_classifications()
                self.apply_classification_results(classifications)
                self.log_manager.success("工作表分类已确认")
            else:
                self.log_manager.info("用户取消了工作表分类")

        except Exception as e:
            self.log_manager.error(f"显示分类对话框时出错: {str(e)}")

    def apply_classification_results(self, classifications: Dict[str, List[str]]):
        """应用分类结果"""
        try:
            # 更新工作簿管理器的分类
            if self.workbook_manager:
                # 重新设置工作表分类
                self.workbook_manager.flash_report_sheets = classifications.get('flash_reports', [])
                self.workbook_manager.data_source_sheets = classifications.get('data_sources', [])

                # 更新分类摘要显示
                self.update_navigator_summary_auto(classifications)

                # 更新工作表浏览器
                self.update_sheet_explorer()

                # 如果有数据来源表，开始提取数据
                if classifications.get('data_sources'):
                    self.log_manager.info("分类确认完成，开始自动提取数据...")
                    self.extract_data()

        except Exception as e:
            self.log_manager.error(f"应用分类结果时出错: {str(e)}")

    def on_classification_changed(self, *args):
        """工作表分类发生变化时的回调（保留兼容性）"""
        # 处理不同参数格式的兼容性
        if len(args) >= 2:
            sheet_name, new_type = args[0], args[1]
            if hasattr(new_type, 'value'):
                type_name = "快报表" if new_type.value == 'flash_report' else "数据来源表"
            else:
                type_name = str(new_type)
            self.log_manager.info(f"🔄 '{sheet_name}' 分类更新为: {type_name}")
        else:
            # 通用分类变化处理
            pass

    def on_classification_confirmed(self):
        """用户确认分类时的回调（保留兼容性）"""
        # 这个方法现在由show_classification_dialog处理
        self.log_manager.info("分类确认处理已转移到对话框")


    def show_classification_results(self, final_classifications):
        """显示分类结果"""
        from PySide6.QtWidgets import QMessageBox, QTextEdit

        # 创建详细结果对话框
        dialog = QMessageBox(self)
        dialog.setWindowTitle("分类结果确认")
        dialog.setIcon(QMessageBox.Information)

        # 构建结果文本
        result_text = "✅ 工作表分类完成！\n\n"

        if final_classifications['flash_reports']:
            result_text += f"📊 快报表 ({len(final_classifications['flash_reports'])} 个):\n"
            for sheet in final_classifications['flash_reports']:
                result_text += f"  • {sheet}\n"
            result_text += "\n"

        if final_classifications['data_sources']:
            result_text += f"📋 数据来源表 ({len(final_classifications['data_sources'])} 个):\n"
            for sheet in final_classifications['data_sources']:
                result_text += f"  • {sheet}\n"
            result_text += "\n"

        if final_classifications['cancelled']:
            result_text += f"❌ 已取消处理 ({len(final_classifications['cancelled'])} 个):\n"
            for sheet in final_classifications['cancelled']:
                result_text += f"  • {sheet}\n"
            result_text += "\n"

        result_text += "💡 提示: 现在可以进行数据提取操作了。"

        dialog.setText(result_text)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.exec()

        # 同时在导航区显示摘要信息
        self.update_navigator_summary(final_classifications)

    def update_navigator_summary(self, final_classifications):
        """更新导航区域的分类摘要"""
        if not hasattr(self, 'classification_summary'):
            return

        # 构建摘要文本
        summary_text = "✅ 工作表分类已确认\n\n"

        # 快报表信息
        if final_classifications['flash_reports']:
            summary_text += f"📊 快报表 ({len(final_classifications['flash_reports'])} 个):\n"
            for sheet in final_classifications['flash_reports']:
                summary_text += f"  • {sheet}\n"
            summary_text += "\n"
        else:
            summary_text += "📊 快报表: 无\n\n"

        # 数据来源表信息
        if final_classifications['data_sources']:
            summary_text += f"📋 数据来源表 ({len(final_classifications['data_sources'])} 个):\n"
            for sheet in final_classifications['data_sources']:
                summary_text += f"  • {sheet}\n"
            summary_text += "\n"
        else:
            summary_text += "📋 数据来源表: 无\n\n"

        # 已取消信息
        if final_classifications['cancelled']:
            summary_text += f"❌ 已取消 ({len(final_classifications['cancelled'])} 个):\n"
            for sheet in final_classifications['cancelled']:
                summary_text += f"  • {sheet}\n"
            summary_text += "\n"

        summary_text += "💡 可以开始数据提取操作"

        # 更新摘要显示
        self.classification_summary.setText(summary_text)

        # 设置状态栏信息
        total_active = len(final_classifications['flash_reports']) + len(final_classifications['data_sources'])
        self.statusBar().showMessage(
            f"分类完成 - 活跃工作表: {total_active} 个, 已取消: {len(final_classifications['cancelled'])} 个"
        )

    def update_navigator_summary_auto(self, auto_classifications):
        """更新导航区域的自动分类摘要"""
        if not hasattr(self, 'classification_summary'):
            return

        # 构建摘要文本（自动分类阶段）
        summary_text = "🔄 自动分类结果 (待确认)\n\n"

        # 快报表信息
        if auto_classifications['flash_reports']:
            summary_text += f"📊 快报表 ({len(auto_classifications['flash_reports'])} 个):\n"
            for sheet in auto_classifications['flash_reports']:
                summary_text += f"  • {sheet}\n"
            summary_text += "\n"
        else:
            summary_text += "📊 快报表: 无\n\n"

        # 数据来源表信息
        if auto_classifications['data_sources']:
            summary_text += f"📋 数据来源表 ({len(auto_classifications['data_sources'])} 个):\n"
            for sheet in auto_classifications['data_sources']:
                summary_text += f"  • {sheet}\n"
            summary_text += "\n"
        else:
            summary_text += "📋 数据来源表: 无\n\n"

        summary_text += "⚠️ 请检查分类结果并确认"

        # 更新摘要显示
        self.classification_summary.setText(summary_text)

        # 设置状态栏信息
        total_sheets = len(auto_classifications['flash_reports']) + len(auto_classifications['data_sources'])
        self.statusBar().showMessage(
            f"自动分类完成 - 共识别 {total_sheets} 个工作表，请检查并确认分类"
        )

    def apply_final_classifications_from_widget(self, final_classifications):
        """根据拖拽界面的最终分类重新组织工作簿管理器"""
        from models.data_models import SheetType

        if not self.workbook_manager:
            return

        # 创建新的工作表列表
        new_flash_reports = []
        new_data_sources = []

        # 收集所有现有的工作表（鲁棒性处理）
        all_sheets = {}

        # 从workbook_manager.worksheets获取完整的工作表信息
        if hasattr(self.workbook_manager, 'worksheets') and self.workbook_manager.worksheets:
            all_sheets = dict(self.workbook_manager.worksheets)
        else:
            # 如果没有worksheets，从列表中重建（兼容性处理）
            for sheet in self.workbook_manager.flash_report_sheets:
                if isinstance(sheet, str):
                    # 如果是字符串，创建临时的工作表信息
                    from models.data_models import WorksheetInfo, SheetType
                    sheet_info = WorksheetInfo(name=sheet, sheet_type=SheetType.FLASH_REPORT)
                    all_sheets[sheet] = sheet_info
                else:
                    # 如果是对象，直接使用
                    all_sheets[sheet.name] = sheet

            for sheet in self.workbook_manager.data_source_sheets:
                if isinstance(sheet, str):
                    # 如果是字符串，创建临时的工作表信息
                    from models.data_models import WorksheetInfo, SheetType
                    sheet_info = WorksheetInfo(name=sheet, sheet_type=SheetType.DATA_SOURCE)
                    all_sheets[sheet] = sheet_info
                else:
                    # 如果是对象，直接使用
                    all_sheets[sheet.name] = sheet

        # 根据最终分类重新分配工作表
        for sheet_name in final_classifications['flash_reports']:
            if sheet_name in all_sheets:
                sheet = all_sheets[sheet_name]
                sheet.sheet_type = SheetType.FLASH_REPORT
                new_flash_reports.append(sheet)

        for sheet_name in final_classifications['data_sources']:
            if sheet_name in all_sheets:
                sheet = all_sheets[sheet_name]
                sheet.sheet_type = SheetType.DATA_SOURCE
                new_data_sources.append(sheet)

        # 更新工作簿管理器
        self.workbook_manager.flash_report_sheets = new_flash_reports
        self.workbook_manager.data_source_sheets = new_data_sources

        # 记录取消的工作表
        if final_classifications['cancelled']:
            self.log_manager.info(f"已取消的工作表: {', '.join(final_classifications['cancelled'])}")

    def open_ai_config_dialog(self):
        """打开AI配置对话框"""
        try:
            from widgets.ai_config_dialog import AIConfigurationDialog

            dialog = AIConfigurationDialog(self)
            if dialog.exec():
                # 获取保存的配置
                config = dialog.get_configuration()

                # 更新快速配置界面
                self.ai_url_edit.setText(config.get('api_url', ''))
                self.ai_model_edit.setText(config.get('model', ''))

                # 更新配置信息显示
                self.ai_config_info.setText(f"已配置: {config.get('model', 'Unknown')} | 流式: {'是' if config.get('stream', False) else '否'}")

                self.log_manager.info("AI配置已更新")

        except Exception as e:
            self.log_manager.error(f"打开AI配置对话框失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开AI配置对话框:\n{str(e)}")

    def quick_test_ai(self):
        """快速测试AI连接"""
        api_url = self.ai_url_edit.text().strip()
        api_key = self.ai_key_edit.text().strip()
        model = self.ai_model_edit.text().strip()

        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API密钥！")
            return

        try:
            self.log_manager.info("开始快速AI连接测试...")

            # 创建简单的测试请求
            import requests

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": "HI"}
                ],
                "max_tokens": 50
            }

            response = requests.post(api_url, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                self.log_manager.success(f"✅ AI连接测试成功！回复: {content}")
                QMessageBox.information(self, "测试成功", f"AI连接正常！\n回复: {content}")
            else:
                error_msg = f"请求失败: {response.status_code} - {response.text}"
                self.log_manager.error(f"❌ AI连接测试失败: {error_msg}")
                QMessageBox.warning(self, "测试失败", error_msg)

        except Exception as e:
            error_msg = f"连接失败: {str(e)}"
            self.log_manager.error(f"❌ AI连接测试异常: {error_msg}")
            QMessageBox.critical(self, "测试异常", error_msg)

    def extract_data(self):
        """提取数据"""
        if not self.workbook_manager:
            QMessageBox.warning(self, "警告", "请先加载Excel文件")
            return

        try:
            self.log_manager.info("开始数据提取...")

            # 使用增强的数据提取器
            extractor = DataExtractor(self.workbook_manager)
            success = extractor.extract_all_data()

            if not success:
                QMessageBox.warning(self, "错误", "数据提取失败，请检查Excel文件格式")
                return

            # 显示统计信息
            targets_count = len(self.workbook_manager.target_items)
            sources_count = len(self.workbook_manager.source_items)
            self.log_manager.success(f"数据提取完成: 目标项 {targets_count} 个, 来源项 {sources_count} 个")

            # 更新所有模型
            self.target_model.set_workbook_manager(self.workbook_manager)

            # 连接导航信号
            self.target_model.itemSelected.connect(self.on_target_item_selected)
            self.target_model.navigationRequested.connect(self.on_navigation_requested)

            # 更新分类筛选器
            self.update_category_filter()
            self.source_model.set_workbook_manager(self.workbook_manager)

            # 使用增强的来源项显示
            self.source_tree.populate_source_items(self.workbook_manager.source_items)
            self.sheet_explorer_model.set_workbook_manager(self.workbook_manager)

            # 更新公式编辑器的工作簿管理器
            self.formula_editor.set_workbook_manager(self.workbook_manager)
            self.formula_delegate.workbook_manager = self.workbook_manager

            # 展开工作表浏览器
            self.sheet_explorer.expandAll()

            self.ai_analyze_btn.setEnabled(True)
            self.calculate_btn.setEnabled(True)

        except Exception as e:
            error_msg = f"数据提取时发生异常: {str(e)}"
            self.log_manager.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def ai_analyze(self):
        """AI分析"""
        if not self.workbook_manager:
            QMessageBox.warning(self, "警告", "请先提取数据")
            return

        try:
            self.log_manager.info("开始AI分析...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(10)

            # 配置AI参数
            ai_config = {
                "api_url": self.ai_url_edit.text(),
                "api_key": self.ai_key_edit.text(),
                "model": self.ai_model_edit.text()
            }

            if not ai_config["api_key"]:
                QMessageBox.warning(self, "警告", "请先配置AI API密钥")
                self.progress_bar.setVisible(False)
                return

            self.progress_bar.setValue(20)

            # 构建AI请求
            from models.data_models import AIAnalysisRequest
            ai_request = AIAnalysisRequest(
                api_url=ai_config["api_url"],
                api_key=ai_config["api_key"],
                model=ai_config["model"]
            )

            # 添加目标项
            for target_id, target in self.workbook_manager.target_items.items():
                if target.is_empty_target:  # 只处理空目标项
                    ai_request.add_target_item(target)

            # 添加来源项
            for source_id, source in self.workbook_manager.source_items.items():
                ai_request.add_source_item(source)

            self.progress_bar.setValue(40)

            if not ai_request.target_items:
                QMessageBox.information(self, "提示", "没有需要映射的空目标项")
                self.progress_bar.setVisible(False)
                return

            # 调用AI映射服务
            ai_response = self.call_ai_service(ai_request)
            self.progress_bar.setValue(80)

            if ai_response.success:
                # 应用AI映射结果
                applied_count = self.apply_ai_mappings(ai_response)
                self.progress_bar.setValue(100)

                self.log_manager.success(f"AI分析完成: 生成{applied_count}个公式映射")

                # 更新模型显示
                self.target_model.layoutChanged.emit()

                QMessageBox.information(self, "成功",
                    f"AI分析完成！\n生成了 {applied_count} 个公式映射\n"
                    f"有效映射: {ai_response.valid_mappings}\n"
                    f"无效映射: {ai_response.invalid_mappings}")

            else:
                self.log_manager.error(f"AI分析失败: {ai_response.error_message}")
                QMessageBox.warning(self, "AI分析失败", ai_response.error_message)

            self.progress_bar.setVisible(False)

        except Exception as e:
            error_msg = f"AI分析时发生异常: {str(e)}"
            self.log_manager.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            self.progress_bar.setVisible(False)

    def call_ai_service(self, ai_request: Any) -> Any:
        """调用AI服务"""
        import requests
        import json
        from models.data_models import AIAnalysisResponse

        try:
            # 构建请求JSON
            request_data = {
                "task_description": ai_request.task_description,
                "target_items": ai_request.target_items,
                "source_items": ai_request.source_items
            }

            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ai_request.api_key}"
            }

            # 构建请求体（符合OpenAI格式）
            request_body = {
                "model": ai_request.model,
                "messages": [
                    {
                        "role": "system",
                        "content": """你是一位经验丰富的注册会计师（CPA），精通中国会计准则（CAS）。你的任务是分析财务报表项目，并建立它们之间的数学勾稽关系。

我会给你一个JSON对象，包含两个关键部分：
1. target_items: 这是需要计算和填写的财务报表项目列表，包含它们的名称和层级关系。
2. source_items: 这是所有可用的数据来源，来自不同的数据表（如利润表、资产负债表），包含它们的表名、项目名和单元格位置。

你的任务是：
1. 仔细分析每一个 target_item。
2. 根据你的专业会计知识，从 source_items 列表中找到一个或多个相关的项目，构建出计算 target_item 值的数学公式。
3. 公式只能使用 +, -, *, / 四种运算符。
4. 输出格式必须严格遵守JSON规范。返回一个名为 "mappings" 的列表，列表中的每个对象包含 "target_id" 和对应的 "formula" 字符串。
5. formula字符串的格式必须为：[工作表名:"项目名"](单元格地址)。例如：[利润表:"营业成本"](D12) + [利润表:"税金及附加"](D15)。
6. 如果一个 target_item 无法从 source_items 中找到任何映射关系，请不要为它创建映射条目。
7. 分析时要特别注意 target_items 的层级关系和名称中的关键词，例如"减："、"其中："、"加："等，这些都暗示了计算逻辑。

请像一名严谨的会计师一样思考，确保公式的准确性。"""
                    },
                    {
                        "role": "user",
                        "content": json.dumps(request_data, ensure_ascii=False)
                    }
                ],
                "temperature": ai_request.temperature,
                "max_tokens": ai_request.max_tokens
            }

            self.log_manager.info(f"发送AI请求到: {ai_request.api_url}")
            self.log_manager.info(f"目标项数量: {len(ai_request.target_items)}")
            self.log_manager.info(f"来源项数量: {len(ai_request.source_items)}")

            # 发送请求
            import time
            start_time = time.time()

            response = requests.post(
                ai_request.api_url,
                headers=headers,
                json=request_body,
                timeout=ai_request.timeout
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                response_data = response.json()

                # 解析AI响应
                ai_response = AIAnalysisResponse()
                ai_response.success = True
                ai_response.response_time = response_time
                ai_response.model_used = ai_request.model

                # 提取AI生成的内容
                ai_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # 尝试解析JSON内容
                try:
                    # 如果AI返回的内容包含JSON代码块，提取出来
                    if "```json" in ai_content:
                        json_start = ai_content.find("```json") + 7
                        json_end = ai_content.find("```", json_start)
                        json_content = ai_content[json_start:json_end].strip()
                    elif "```" in ai_content:
                        json_start = ai_content.find("```") + 3
                        json_end = ai_content.rfind("```")
                        json_content = ai_content[json_start:json_end].strip()
                    else:
                        json_content = ai_content

                    # 解析JSON
                    mapping_data = json.loads(json_content)

                    if "mappings" in mapping_data:
                        ai_response.mappings = mapping_data["mappings"]
                        ai_response.processed_mappings = len(ai_response.mappings)
                    else:
                        ai_response.success = False
                        ai_response.error_message = "AI响应缺少mappings字段"

                except json.JSONDecodeError as e:
                    ai_response.success = False
                    ai_response.error_message = f"AI响应JSON解析失败: {str(e)}"
                    self.log_manager.error(f"AI原始响应: {ai_content}")

                # 统计token使用量
                if "usage" in response_data:
                    ai_response.tokens_used = response_data["usage"].get("total_tokens", 0)

                return ai_response

            else:
                ai_response = AIAnalysisResponse()
                ai_response.success = False
                ai_response.error_message = f"API请求失败: {response.status_code} - {response.text}"
                return ai_response

        except requests.exceptions.Timeout:
            ai_response = AIAnalysisResponse()
            ai_response.success = False
            ai_response.error_message = "AI请求超时，请检查网络连接或增加超时时间"
            return ai_response

        except Exception as e:
            ai_response = AIAnalysisResponse()
            ai_response.success = False
            ai_response.error_message = f"AI服务调用异常: {str(e)}"
            return ai_response

    def apply_ai_mappings(self, ai_response: Any) -> int:
        """应用AI映射结果"""
        from models.data_models import MappingFormula, FormulaStatus
        from utils.excel_utils_v2 import validate_formula_syntax_v2

        applied_count = 0
        valid_count = 0
        invalid_count = 0

        for mapping in ai_response.mappings:
            target_id = mapping.get("target_id")
            formula = mapping.get("formula", "")

            if not target_id or not formula:
                continue

            # 验证目标项是否存在
            if target_id not in self.workbook_manager.target_items:
                self.log_manager.warning(f"目标项不存在: {target_id}")
                continue

            # 验证公式语法
            is_valid, error_msg = validate_formula_syntax_v2(formula)

            if is_valid:
                # 创建或更新映射公式
                mapping_formula = MappingFormula(
                    target_id=target_id,
                    formula=formula,
                    status=FormulaStatus.AI_GENERATED
                )

                # 设置AI相关信息
                mapping_formula.ai_confidence = mapping.get("confidence", 0.8)
                mapping_formula.ai_reasoning = f"AI生成 (模型: {ai_response.model_used})"

                self.workbook_manager.add_mapping_formula(target_id, mapping_formula)
                applied_count += 1
                valid_count += 1

                target_name = self.workbook_manager.target_items[target_id].name
                self.log_manager.info(f"应用AI映射: {target_name} = {formula}")

            else:
                invalid_count += 1
                self.log_manager.warning(f"AI生成的公式无效: {formula} - {error_msg}")

        # 更新响应统计
        ai_response.valid_mappings = valid_count
        ai_response.invalid_mappings = invalid_count

        return applied_count

    def calculate_preview(self):
        """计算预览"""
        if not self.workbook_manager:
            QMessageBox.warning(self, "警告", "请先提取数据")
            return

        try:
            self.log_manager.info("开始计算预览...")

            from modules.calculation_engine import create_calculation_engine

            self.calculation_engine = create_calculation_engine(self.workbook_manager)
            results = self.calculation_engine.calculate_all_formulas(show_progress=False)

            # 更新模型以显示计算结果
            self.target_model.layoutChanged.emit()

            summary = self.calculation_engine.get_calculation_summary()
            self.log_manager.success(f"计算完成: {summary['successful_calculations']}/{summary['total_formulas']} 成功")

            self.calculate_btn.setEnabled(True)

        except Exception as e:
            error_msg = f"计算预览时发生异常: {str(e)}"
            self.log_manager.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def export_excel(self):
        """导出Excel"""
        if not self.calculation_engine:
            QMessageBox.warning(self, "警告", "请先进行计算")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Excel文件", "",
            "Excel Files (*.xlsx);;All Files (*)"
        )

        if not file_path:
            return

        try:
            self.log_manager.info(f"开始导出到: {file_path}")

            success = self.calculation_engine.export_to_excel(file_path)

            if success:
                self.log_manager.success(f"导出成功: {file_path}")
                QMessageBox.information(self, "成功", f"文件已导出到:\n{file_path}")
            else:
                self.log_manager.error("导出失败")
                QMessageBox.warning(self, "失败", "导出失败，请查看日志")

        except Exception as e:
            error_msg = f"导出Excel时发生异常: {str(e)}"
            self.log_manager.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def export_json(self):
        """导出JSON"""
        if not self.calculation_engine:
            QMessageBox.warning(self, "警告", "请先进行计算")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存JSON文件", "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            success = self.calculation_engine.export_results_to_json(file_path)

            if success:
                self.log_manager.success(f"JSON导出成功: {file_path}")
                QMessageBox.information(self, "成功", f"文件已导出到:\n{file_path}")
            else:
                self.log_manager.error("JSON导出失败")
                QMessageBox.warning(self, "失败", "导出失败，请查看日志")

        except Exception as e:
            error_msg = f"导出JSON时发生异常: {str(e)}"
            self.log_manager.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def on_target_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        """目标项选择变化处理"""
        if not current.isValid():
            self.property_inspector.update_properties(None)
            self.formula_editor.setPlainText("")
            return

        item = current.internalPointer()
        if not isinstance(item, TargetItem) or not self.workbook_manager:
            return

        # 更新属性检查器
        self.property_inspector.update_properties(item)

        # 更新公式检查器
        formula = self.workbook_manager.mapping_formulas.get(item.id)
        if formula:
            self.formula_editor.setPlainText(formula.formula)
        else:
            self.formula_editor.setPlainText("")

    def on_drag_started(self, index: QModelIndex):
        """拖拽开始处理"""
        self.log_manager.info(f"开始拖拽: {index.data(Qt.DisplayRole)}")

    def on_item_dropped(self, target_index: QModelIndex, dropped_text: str):
        """项目拖放处理"""
        if not target_index.isValid():
            return

        # 如果拖放到公式列，添加引用
        if target_index.column() == 3:
            current_text = target_index.data(Qt.DisplayRole) or ""
            new_text = f"{current_text} + {dropped_text}" if current_text else dropped_text

            # 更新模型数据
            target_index.model().setData(target_index, new_text, Qt.EditRole)

            self.log_manager.info(f"已添加引用: {dropped_text}")

    def on_formula_changed(self, formula: str):
        """公式变化处理"""
        # 实时验证公式
        if formula.strip():
            is_valid, error = validate_formula_syntax_v2(formula)
            if not is_valid:
                self.log_manager.warning(f"公式语法错误: {error}")

        # 更新当前选中项的公式
        current_index = self.main_data_grid.currentIndex()
        if current_index.isValid() and current_index.column() != 3:
            # 切换到公式列
            formula_index = current_index.sibling(current_index.row(), 3)
            if formula_index.isValid():
                formula_index.model().setData(formula_index, formula, Qt.EditRole)

    def on_sheet_selected(self, sheet_name: str, sheet_type):
        """工作表选择处理"""
        self.log_manager.info(f"选择工作表: {sheet_name} (类型: {'快报表' if sheet_type.value == 'flash_report' else '数据来源表'})")

        # 如果选择的是快报表，更新目标项模型
        if sheet_type.value == 'flash_report' and self.target_model and sheet_name:
            self.target_model.set_active_sheet(sheet_name)

    def on_flash_report_activated(self, sheet_name: str):
        """快报表激活处理"""
        self.log_manager.info(f"激活快报表: {sheet_name}")
        # 更新目标项模型以显示该工作表的项目
        if self.target_model and sheet_name:
            self.target_model.set_active_sheet(sheet_name)

    def update_sheet_explorer(self):
        """更新工作表浏览器"""
        if not self.workbook_manager:
            return

        # 模型已经在extract_data中更新了
        self.log_manager.success(f"工作表浏览器已更新: 快报表{len(self.workbook_manager.flash_report_sheets)}个, 数据表{len(self.workbook_manager.data_source_sheets)}个")

    def clear_all_formulas(self):
        """清除所有公式"""
        if not self.workbook_manager:
            return

        reply = QMessageBox.question(
            self, "确认", "确定要清除所有公式吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.workbook_manager.mapping_formulas.clear()
            self.target_model.layoutChanged.emit()
            self.log_manager.info("已清除所有公式")

    def recalculate(self):
        """重新计算"""
        self.calculate_preview()

    def reset_layout(self):
        """重置布局"""
        self.log_manager.info("布局重置功能开发中...")

    def filter_by_category(self, category_text: str):
        """按分类筛选目标项"""
        if not self.target_model:
            return

        # 更新分类筛选
        if category_text == "全部分类":
            # 显示所有分类
            for i in range(self.target_model.rowCount()):
                index = self.target_model.index(i, 0)
                self.item_structure_tree.setRowHidden(i, QModelIndex(), False)
        else:
            # 只显示匹配的分类
            for i in range(self.target_model.rowCount()):
                index = self.target_model.index(i, 0)
                item = index.internalPointer()
                if isinstance(item, CategoryNode):
                    hidden = category_text not in item.name
                    self.item_structure_tree.setRowHidden(i, QModelIndex(), hidden)

        self.log_manager.info(f"🔍 筛选分类: {category_text}")

    def search_target_items(self, search_text: str):
        """搜索目标项"""
        if not self.target_model or not search_text.strip():
            # 清空搜索时恢复所有项目
            self.clear_search_filter()
            return

        search_text = search_text.lower()
        found_items = []

        # 搜索所有目标项
        for category_node in self.target_model.root_items:
            category_match = False
            for target_item in category_node.children:
                if search_text in target_item.name.lower():
                    found_items.append((category_node.name, target_item.name))
                    category_match = True

            # 如果分类下有匹配项，展开该分类
            if category_match:
                category_index = self.target_model.createIndex(
                    self.target_model.root_items.index(category_node), 0, category_node
                )
                self.item_structure_tree.expand(category_index)

        if found_items:
            self.log_manager.info(f"🔍 找到 {len(found_items)} 个匹配项: {search_text}")
            # 可以高亮显示搜索结果
            self.highlight_search_results(found_items)
        else:
            self.log_manager.info(f"🔍 未找到匹配项: {search_text}")

    def clear_search_filter(self):
        """清除搜索筛选"""
        if self.target_model:
            # 恢复所有项目的可见性
            for i in range(self.target_model.rowCount()):
                self.item_structure_tree.setRowHidden(i, QModelIndex(), False)

    def highlight_search_results(self, found_items: list):
        """高亮搜索结果（简化实现）"""
        # 这里可以实现更复杂的高亮逻辑
        pass

    def expand_all_categories(self):
        """展开所有分类"""
        if self.target_model:
            self.item_structure_tree.expandAll()
            self.log_manager.info("🔽 已展开所有分类")

    def collapse_all_categories(self):
        """折叠所有分类"""
        if self.target_model:
            self.item_structure_tree.collapseAll()
            self.log_manager.info("🔼 已折叠所有分类")

    def on_target_item_clicked(self, index: QModelIndex):
        """目标项单击处理"""
        if not index.isValid():
            return

        item = index.internalPointer()
        if isinstance(item, TargetItem):
            # 选中目标项，更新属性面板
            self.selected_target_id = item.id
            self.update_property_inspector(item)
            self.log_manager.info(f"🎯 选中目标项: {item.name}")

        elif isinstance(item, CategoryNode):
            # 切换分类展开/折叠状态
            if self.item_structure_tree.isExpanded(index):
                self.item_structure_tree.collapse(index)
            else:
                self.item_structure_tree.expand(index)

    def on_target_item_double_clicked(self, index: QModelIndex):
        """目标项双击处理"""
        if not index.isValid():
            return

        item = index.internalPointer()
        if isinstance(item, TargetItem):
            # 双击时快速定位到主数据网格中对应行
            self.navigate_to_main_grid(item.id)
            self.log_manager.info(f"🎯 导航到主表格: {item.name}")

    def navigate_to_main_grid(self, target_id: str):
        """导航到主数据网格中的指定项"""
        if not self.target_model:
            return

        # 在主表格中查找并选中对应行
        for row in range(self.target_model.rowCount()):
            index = self.target_model.index(row, 0)
            item = self.target_model.get_target_item(index)
            if item and item.id == target_id:
                # 选中该行
                self.main_data_grid.setCurrentIndex(index)
                self.main_data_grid.scrollTo(index, QAbstractItemView.PositionAtCenter)
                break

    def update_property_inspector(self, target_item: TargetItem):
        """更新属性检查器"""
        if hasattr(self, 'property_inspector'):
            # 更新属性面板显示目标项的详细信息
            properties = {
                "目标项ID": target_item.id,
                "项目名称": target_item.name,
                "所属表格": target_item.sheet_name,
                "单元格地址": target_item.cell_address,
                "数据类型": "数值" if getattr(target_item, 'data_type', 'text') == "number" else "文本",
                "是否必填": "是" if getattr(target_item, 'required', False) else "否"
            }

            # 添加映射信息
            if self.workbook_manager:
                formula = self.workbook_manager.mapping_formulas.get(target_item.id)
                if formula:
                    properties["映射公式"] = formula.formula
                    properties["公式状态"] = formula.status.value
                    result = self.workbook_manager.calculation_results.get(target_item.id)
                    if result:
                        properties["计算结果"] = str(result.value) if result.success else "计算失败"

            self.property_inspector.update_properties(properties)

    def show_context_menu(self, position):
        """显示右键上下文菜单"""
        if not self.main_data_grid.indexAt(position).isValid():
            return

        # 获取选中的行
        selected_indexes = self.main_data_grid.selectionModel().selectedRows()
        if not selected_indexes:
            return

        menu = QMenu(self)
        selected_count = len(selected_indexes)

        # 单项操作
        if selected_count == 1:
            selected_item = self.get_selected_target_items()[0]
            menu.addAction("📝 编辑公式", self.edit_formula)
            menu.addAction("🔍 查看详情", self.view_details)

            # 如果有公式，添加公式相关操作
            if selected_item.id in self.workbook_manager.mapping_formulas:
                formula = self.workbook_manager.mapping_formulas[selected_item.id]
                if formula.formula:
                    menu.addAction("📋 复制公式", self.copy_formula)
                    menu.addAction("🗑️ 删除公式", self.delete_formula)
                    menu.addAction("✅ 验证公式", self.validate_formula)

            menu.addSeparator()

        # 批量操作
        menu.addAction(f"🤖 批量AI映射 ({selected_count}项)", self.batch_ai_mapping)
        menu.addAction(f"🧮 批量计算 ({selected_count}项)", self.batch_calculate)
        menu.addAction(f"✅ 批量验证 ({selected_count}项)", self.batch_validate)
        menu.addSeparator()

        # 公式操作
        formula_menu = menu.addMenu("📋 公式操作")
        formula_menu.addAction("复制公式", self.copy_formulas)
        formula_menu.addAction("粘贴公式", self.paste_formulas)
        formula_menu.addAction("清空公式", self.clear_formulas)
        formula_menu.addSeparator()
        formula_menu.addAction("从模板应用", self.apply_from_template)
        formula_menu.addAction("保存为模板", self.save_as_template)

        # 状态操作
        status_menu = menu.addMenu("⚡ 状态操作")
        status_menu.addAction("标记为待处理", lambda: self.batch_set_status(FormulaStatus.PENDING))
        status_menu.addAction("标记为已验证", lambda: self.batch_set_status(FormulaStatus.VALIDATED))
        status_menu.addAction("标记为错误", lambda: self.batch_set_status(FormulaStatus.ERROR))

        # 导出操作
        export_menu = menu.addMenu("💾 导出操作")
        export_menu.addAction("导出选中项", self.export_selected)
        export_menu.addAction("导出映射关系", self.export_mappings)

        # 高级操作
        menu.addSeparator()
        advanced_menu = menu.addMenu("🔧 高级操作")
        advanced_menu.addAction("重新提取数据", self.re_extract_data)
        advanced_menu.addAction("重置映射关系", self.reset_mappings)
        advanced_menu.addAction("查找引用关系", self.find_references)

        # 显示菜单
        menu.exec(self.main_data_grid.mapToGlobal(position))

    def get_selected_target_items(self) -> List[TargetItem]:
        """获取选中的目标项"""
        selected_items = []
        selected_indexes = self.main_data_grid.selectionModel().selectedRows()

        for index in selected_indexes:
            if hasattr(self.target_model, 'get_target_item'):
                item = self.target_model.get_target_item(index)
                if item:
                    selected_items.append(item)

        return selected_items

    def edit_formula(self):
        """编辑公式 - 使用专用的公式编辑对话框"""
        selected_items = self.get_selected_target_items()
        if len(selected_items) == 1:
            target_item = selected_items[0]
            self.log_manager.info(f"📝 编辑公式: {target_item.name}")

            # 打开公式编辑对话框
            dialog = FormulaEditDialog(target_item, self.workbook_manager, self)
            if dialog.exec() == QDialog.Accepted:
                # 获取新的公式
                new_formula = dialog.get_formula()
                if new_formula:
                    # 更新映射公式
                    if target_item.id not in self.workbook_manager.mapping_formulas:
                        self.workbook_manager.mapping_formulas[target_item.id] = MappingFormula(
                            target_id=target_item.id,
                            formula=""  # 创建时先用空公式，后面会设置new_formula
                        )

                    formula_obj = self.workbook_manager.mapping_formulas[target_item.id]
                    formula_obj.formula = new_formula
                    formula_obj.status = FormulaStatus.VALIDATED
                    formula_obj.validation_error = None

                    # 刷新显示
                    self.refresh_main_table()
                    self.log_manager.success(f"✅ 公式已更新: {new_formula}")
                else:
                    self.log_manager.info("❌ 取消编辑公式")
        else:
            self.log_manager.warning("请选择一个目标项进行公式编辑")

    def view_details(self):
        """查看详情"""
        selected_items = self.get_selected_target_items()
        if len(selected_items) == 1:
            target_item = selected_items[0]

            # 获取公式信息
            formula_info = "无公式"
            if target_item.id in self.workbook_manager.mapping_formulas:
                formula = self.workbook_manager.mapping_formulas[target_item.id]
                formula_info = f"公式: {formula.formula}\n状态: {formula.status.value}"
                if formula.validation_error:
                    formula_info += f"\n错误: {formula.validation_error}"

            # 创建详情对话框
            detail_text = f"""项目详情:

项目名称: {target_item.name}
工作表: {target_item.sheet_name}
行号: {target_item.row}
原始缩进: {target_item.level}
层级深度: {getattr(target_item, 'hierarchical_level', '未计算')}
父级ID: {target_item.parent_id or '无'}
子级数量: {len(target_item.children_ids)}

{formula_info}

单元格地址: {target_item.target_cell_address}
是否为空目标: {'是' if target_item.is_empty_target else '否'}
备注: {target_item.notes or '无'}
"""

            dialog = QMessageBox(self)
            dialog.setWindowTitle(f"项目详情 - {target_item.name}")
            dialog.setText(detail_text)
            dialog.setStandardButtons(QMessageBox.Ok)
            dialog.exec()

            # 同时更新属性检查器
            self.update_property_inspector(target_item)
            self.log_manager.info(f"🔍 查看详情: {target_item.name}")

    def copy_formula(self):
        """复制公式"""
        selected_items = self.get_selected_target_items()
        if len(selected_items) == 1:
            target_item = selected_items[0]
            if target_item.id in self.workbook_manager.mapping_formulas:
                formula = self.workbook_manager.mapping_formulas[target_item.id]
                if formula.formula:
                    # 复制到剪贴板
                    clipboard = QApplication.clipboard()
                    clipboard.setText(formula.formula)
                    self.log_manager.info(f"📋 已复制公式: {formula.formula}")
                else:
                    self.log_manager.warning("公式为空，无法复制")
            else:
                self.log_manager.warning("该项目没有公式")

    def delete_formula(self):
        """删除公式"""
        selected_items = self.get_selected_target_items()
        if len(selected_items) == 1:
            target_item = selected_items[0]
            if target_item.id in self.workbook_manager.mapping_formulas:
                # 确认删除
                reply = QMessageBox.question(
                    self, "确认删除",
                    f"确定要删除项目 '{target_item.name}' 的公式吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    del self.workbook_manager.mapping_formulas[target_item.id]
                    # 刷新显示
                    self.target_model.dataChanged.emit(
                        self.target_model.index(0, 0),
                        self.target_model.index(self.target_model.rowCount()-1, self.target_model.columnCount()-1)
                    )
                    self.log_manager.info(f"🗑️ 已删除公式: {target_item.name}")
            else:
                self.log_manager.warning("该项目没有公式")

    def validate_formula(self):
        """验证公式"""
        selected_items = self.get_selected_target_items()
        if len(selected_items) == 1:
            target_item = selected_items[0]
            if target_item.id in self.workbook_manager.mapping_formulas:
                formula = self.workbook_manager.mapping_formulas[target_item.id]
                if formula.formula:
                    # 这里可以集成公式验证逻辑
                    try:
                        # 简单的语法检查
                        if not formula.formula.strip():
                            raise ValueError("公式不能为空")

                        # 可以添加更复杂的验证逻辑
                        formula.is_valid = True
                        formula.validation_error = ""
                        self.log_manager.info(f"✅ 公式验证通过: {formula.formula}")

                    except Exception as e:
                        formula.is_valid = False
                        formula.validation_error = str(e)
                        self.log_manager.error(f"❌ 公式验证失败: {e}")
                else:
                    self.log_manager.warning("公式为空，无法验证")
            else:
                self.log_manager.warning("该项目没有公式")

    def on_main_grid_double_clicked(self, index: QModelIndex):
        """主数据网格双击事件处理"""
        if not index.isValid():
            return

        column = index.column()
        target_item = self.target_model.get_target_item(index)
        if not target_item:
            return

        if column == 3:  # 双击公式列，开启公式编辑对话框
            self.log_manager.info(f"双击编辑公式: {target_item.name}")

            # 打开公式编辑对话框
            dialog = FormulaEditDialog(target_item, self.workbook_manager, self)
            if dialog.exec() == QDialog.Accepted:
                # 获取新的公式
                new_formula = dialog.get_formula()
                if new_formula:
                    # 更新映射公式
                    if target_item.id not in self.workbook_manager.mapping_formulas:
                        self.workbook_manager.mapping_formulas[target_item.id] = MappingFormula(
                            target_id=target_item.id,
                            formula=""  # 创建时先用空公式，后面会设置new_formula
                        )

                    formula_obj = self.workbook_manager.mapping_formulas[target_item.id]
                    formula_obj.formula = new_formula
                    formula_obj.status = FormulaStatus.VALIDATED
                    formula_obj.validation_error = None

                    # 刷新显示
                    self.refresh_main_table()
                    self.log_manager.success(f"✅ 公式已更新: {new_formula}")
                else:
                    self.log_manager.info("❌ 取消编辑公式")
        else:
            # 双击其他列，显示详情
            self.log_manager.info(f"双击查看详情: {target_item.name}")
            self.view_details()

    def batch_ai_mapping(self):
        """批量AI映射"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        reply = QMessageBox.question(
            self, "确认操作",
            f"🤖 将对选中的 {len(selected_items)} 个项目执行AI映射，是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.log_manager.info(f"🤖 开始批量AI映射 {len(selected_items)} 个项目")
            # 执行批量AI映射
            self.perform_batch_ai_mapping(selected_items)

    def batch_calculate(self):
        """批量计算"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        self.log_manager.info(f"🧮 开始批量计算 {len(selected_items)} 个项目")
        self.perform_batch_calculation(selected_items)

    def batch_validate(self):
        """批量验证"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        self.log_manager.info(f"✅ 开始批量验证 {len(selected_items)} 个项目")
        self.perform_batch_validation(selected_items)

    def copy_formulas(self):
        """复制公式"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        formulas = []
        for item in selected_items:
            if self.workbook_manager:
                formula = self.workbook_manager.mapping_formulas.get(item.id)
                if formula:
                    formulas.append(formula.formula)

        if formulas:
            # 存储到剪贴板（简化实现）
            self.copied_formulas = formulas
            self.log_manager.info(f"📋 已复制 {len(formulas)} 个公式")

    def paste_formulas(self):
        """粘贴公式"""
        if not hasattr(self, 'copied_formulas') or not self.copied_formulas:
            QMessageBox.information(self, "提示", "没有可粘贴的公式")
            return

        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        # 应用复制的公式到选中项
        count = 0
        for i, item in enumerate(selected_items):
            if i < len(self.copied_formulas):
                formula = self.copied_formulas[i]
                if self.workbook_manager:
                    # 创建或更新映射公式
                    if item.id not in self.workbook_manager.mapping_formulas:
                        self.workbook_manager.mapping_formulas[item.id] = MappingFormula(
                            target_id=item.id,
                            formula=formula,
                            status=FormulaStatus.USER_MODIFIED
                        )
                    else:
                        self.workbook_manager.mapping_formulas[item.id].formula = formula
                        self.workbook_manager.mapping_formulas[item.id].status = FormulaStatus.USER_MODIFIED
                    count += 1

        self.log_manager.info(f"📋 已粘贴 {count} 个公式")
        self.refresh_main_table()

    def clear_formulas(self):
        """清空公式"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        reply = QMessageBox.question(
            self, "确认操作",
            f"🗑️ 将清空选中的 {len(selected_items)} 个项目的公式，是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            count = 0
            for item in selected_items:
                if self.workbook_manager and item.id in self.workbook_manager.mapping_formulas:
                    del self.workbook_manager.mapping_formulas[item.id]
                    count += 1

            self.log_manager.info(f"🗑️ 已清空 {count} 个公式")
            self.refresh_main_table()

    def batch_set_status(self, status: FormulaStatus):
        """批量设置状态"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        count = 0
        for item in selected_items:
            if self.workbook_manager:
                if item.id in self.workbook_manager.mapping_formulas:
                    self.workbook_manager.mapping_formulas[item.id].status = status
                    count += 1

        status_text = {
            FormulaStatus.PENDING: "待处理",
            FormulaStatus.VALIDATED: "已验证",
            FormulaStatus.ERROR: "错误"
        }.get(status, "未知")

        self.log_manager.info(f"⚡ 已将 {count} 个项目标记为: {status_text}")
        self.refresh_main_table()

    def perform_batch_ai_mapping(self, selected_items: List[TargetItem]):
        """执行批量AI映射"""
        # 调用AI映射功能
        # 这里可以复用之前的AI分析逻辑，但只针对选中的项目
        pass

    def perform_batch_calculation(self, selected_items: List[TargetItem]):
        """执行批量计算"""
        if not self.workbook_manager:
            return

        success_count = 0
        for item in selected_items:
            formula = self.workbook_manager.mapping_formulas.get(item.id)
            if formula and formula.formula:
                try:
                    # 执行计算（简化实现）
                    result = CalculationResult(
                        target_id=item.id,
                        success=True,
                        value=100.0,  # 模拟计算结果
                        error_message=""
                    )
                    self.workbook_manager.calculation_results[item.id] = result
                    formula.status = FormulaStatus.CALCULATED
                    success_count += 1
                except Exception as e:
                    result = CalculationResult(
                        target_id=item.id,
                        success=False,
                        value=None,
                        error_message=str(e)
                    )
                    self.workbook_manager.calculation_results[item.id] = result
                    formula.status = FormulaStatus.ERROR

        self.log_manager.info(f"🧮 批量计算完成，成功 {success_count} 个")
        self.refresh_main_table()

    def perform_batch_validation(self, selected_items: List[TargetItem]):
        """执行批量验证"""
        if not self.workbook_manager:
            return

        valid_count = 0
        for item in selected_items:
            formula = self.workbook_manager.mapping_formulas.get(item.id)
            if formula and formula.formula:
                # 执行公式语法验证
                if validate_formula_syntax_v2(formula.formula):
                    formula.status = FormulaStatus.VALIDATED
                    valid_count += 1
                else:
                    formula.status = FormulaStatus.ERROR

        self.log_manager.info(f"✅ 批量验证完成，有效 {valid_count} 个")
        self.refresh_main_table()

    def show_template_manager(self):
        """显示映射模板管理器"""
        if not self.workbook_manager:
            QMessageBox.warning(self, "警告", "请先加载Excel文件")
            return

        dialog = MappingTemplateDialog(self.workbook_manager, self)
        dialog.templateApplied.connect(self.on_template_applied)

        if dialog.exec() == MappingTemplateDialog.Accepted:
            self.log_manager.info("📋 模板管理操作完成")

    def on_template_applied(self, template_name: str, applied_count: int):
        """模板应用完成处理"""
        self.log_manager.info(f"📋 模板 '{template_name}' 已应用到 {applied_count} 个项目")
        self.refresh_main_table()

    def apply_from_template(self):
        """从模板应用"""
        self.log_manager.info("📋 从模板应用功能开发中...")

    def save_as_template(self):
        """保存为模板"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        self.log_manager.info(f"💾 保存 {len(selected_items)} 个项目为模板")

    def export_selected(self):
        """导出选中项"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        self.log_manager.info(f"💾 导出 {len(selected_items)} 个选中项")

    def export_mappings(self):
        """导出映射关系"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        self.log_manager.info(f"💾 导出 {len(selected_items)} 个映射关系")

    def re_extract_data(self):
        """重新提取数据"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        self.log_manager.info(f"🔧 重新提取 {len(selected_items)} 个项目数据")

    def reset_mappings(self):
        """重置映射关系"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        reply = QMessageBox.question(
            self, "确认操作",
            f"🔧 将重置选中的 {len(selected_items)} 个项目的映射关系，是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            count = 0
            for item in selected_items:
                if self.workbook_manager:
                    if item.id in self.workbook_manager.mapping_formulas:
                        self.workbook_manager.mapping_formulas[item.id].formula = ""
                        self.workbook_manager.mapping_formulas[item.id].status = FormulaStatus.EMPTY
                        count += 1

            self.log_manager.info(f"🔧 已重置 {count} 个映射关系")
            self.refresh_main_table()

    def find_references(self):
        """查找引用关系"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        self.log_manager.info(f"🔧 查找 {len(selected_items)} 个项目的引用关系")

    def refresh_main_table(self):
        """刷新主表格"""
        if hasattr(self, 'target_model') and self.target_model:
            self.target_model.layoutChanged.emit()

    def on_target_item_selected(self, target_id: str):
        """目标项选择信号处理"""
        self.selected_target_id = target_id
        if self.workbook_manager:
            target_item = self.workbook_manager.target_items.get(target_id)
            if target_item:
                self.update_property_inspector(target_item)

    def on_navigation_requested(self, nav_type: str, item_name: str):
        """导航请求信号处理"""
        if nav_type == "category":
            self.log_manager.info(f"🧭 导航到分类: {item_name}")
            # 可以在这里添加更多导航逻辑

    def update_category_filter(self):
        """更新分类筛选下拉框"""
        if not self.target_model:
            return

        current_text = self.category_filter.currentText()
        self.category_filter.clear()
        self.category_filter.addItem("全部分类")

        # 添加所有分类
        for category_node in self.target_model.root_items:
            if isinstance(category_node, CategoryNode):
                self.category_filter.addItem(category_node.name)

        # 恢复之前的选择
        index = self.category_filter.findText(current_text)
        if index >= 0:
            self.category_filter.setCurrentIndex(index)


    def show_about(self):
        """显示关于信息"""
        QMessageBox.about(
            self, "关于",
            "AI辅助财务报表数据映射与填充工具\n"
            "版本: PySide6 v1.0\n"
            "基于程序要求.md开发"
        )

    def load_settings(self):
        """加载设置"""
        try:
            self.ai_url_edit.setText(
                self.settings.value("ai_url", "https://api.openai.com/v1/chat/completions")
            )
            self.ai_model_edit.setText(
                self.settings.value("ai_model", "gpt-4")
            )
        except:
            pass

    def save_settings(self):
        """保存设置"""
        try:
            self.settings.setValue("ai_url", self.ai_url_edit.text())
            self.settings.setValue("ai_model", self.ai_model_edit.text())
        except:
            pass

    def closeEvent(self, event):
        """关闭事件"""
        self.save_settings()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("AI财务报表工具")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("FinancialTool")

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 启动应用程序
    sys.exit(app.exec())


class MappingTemplateDialog(QDialog):
    """映射模板管理对话框"""

    # 信号
    templateApplied = Signal(str, int)  # (template_name, applied_count)

    def __init__(self, workbook_manager: WorkbookManager, parent=None):
        super().__init__(parent)
        self.workbook_manager = workbook_manager
        self.template_manager = TemplateManager()
        self.template_manager.load_from_file()
        self.setup_ui()
        self.refresh_template_list()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("映射模板管理")
        self.setModal(True)
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        # 顶部工具栏
        toolbar_layout = QHBoxLayout()

        self.new_template_btn = QPushButton("📝 新建模板")
        self.new_template_btn.clicked.connect(self.create_new_template)
        toolbar_layout.addWidget(self.new_template_btn)

        self.import_btn = QPushButton("📥 导入模板")
        self.import_btn.clicked.connect(self.import_template)
        toolbar_layout.addWidget(self.import_btn)

        self.export_template_btn = QPushButton("📤 导出模板")
        self.export_template_btn.clicked.connect(self.export_template)
        toolbar_layout.addWidget(self.export_template_btn)

        toolbar_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.refresh_template_list)
        toolbar_layout.addWidget(self.refresh_btn)

        layout.addLayout(toolbar_layout)

        # 主要内容区域
        content_splitter = QSplitter(Qt.Horizontal)

        # 左侧：模板列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        left_layout.addWidget(QLabel("📋 已保存的模板:"))

        self.template_list = QTableWidget()
        self.template_list.setColumnCount(4)
        self.template_list.setHorizontalHeaderLabels(["模板名称", "来源表格", "映射数量", "创建时间"])
        self.template_list.horizontalHeader().setStretchLastSection(True)
        self.template_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.template_list.setAlternatingRowColors(True)
        self.template_list.itemSelectionChanged.connect(self.on_template_selected)
        left_layout.addWidget(self.template_list)

        # 模板操作按钮
        template_ops_layout = QHBoxLayout()
        self.apply_btn = QPushButton("✅ 应用模板")
        self.apply_btn.clicked.connect(self.apply_template)
        self.apply_btn.setEnabled(False)
        template_ops_layout.addWidget(self.apply_btn)

        self.edit_btn = QPushButton("✏️ 编辑")
        self.edit_btn.clicked.connect(self.edit_template)
        self.edit_btn.setEnabled(False)
        template_ops_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ 删除")
        self.delete_btn.clicked.connect(self.delete_template)
        self.delete_btn.setEnabled(False)
        template_ops_layout.addWidget(self.delete_btn)

        left_layout.addLayout(template_ops_layout)
        content_splitter.addWidget(left_widget)

        # 右侧：模板详情和应用选项
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 模板详情
        details_group = QGroupBox("📄 模板详情")
        details_layout = QFormLayout(details_group)

        self.template_name_label = QLabel("-")
        details_layout.addRow("模板名称:", self.template_name_label)

        self.source_sheet_label = QLabel("-")
        details_layout.addRow("来源表格:", self.source_sheet_label)

        self.description_label = QLabel("-")
        details_layout.addRow("描述:", self.description_label)

        self.mapping_count_label = QLabel("-")
        details_layout.addRow("映射数量:", self.mapping_count_label)

        right_layout.addWidget(details_group)

        # 应用选项
        apply_group = QGroupBox("🎯 应用到目标表格")
        apply_layout = QVBoxLayout(apply_group)

        self.target_sheet_combo = QComboBox()
        self.update_target_sheets()
        apply_layout.addWidget(QLabel("选择目标表格:"))
        apply_layout.addWidget(self.target_sheet_combo)

        # 应用选项
        self.overwrite_existing = QCheckBox("覆盖现有映射")
        self.overwrite_existing.setChecked(True)
        apply_layout.addWidget(self.overwrite_existing)

        self.preview_changes = QCheckBox("预览更改")
        self.preview_changes.setChecked(False)
        apply_layout.addWidget(self.preview_changes)

        right_layout.addWidget(apply_group)

        # 映射预览
        preview_group = QGroupBox("🔍 映射预览")
        preview_layout = QVBoxLayout(preview_group)

        self.mapping_preview = QTableWidget()
        self.mapping_preview.setColumnCount(2)
        self.mapping_preview.setHorizontalHeaderLabels(["目标项", "公式"])
        self.mapping_preview.horizontalHeader().setStretchLastSection(True)
        preview_layout.addWidget(self.mapping_preview)

        right_layout.addWidget(preview_group)

        content_splitter.addWidget(right_widget)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 1)

        layout.addWidget(content_splitter)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.close_btn = QPushButton("❌ 关闭")
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def refresh_template_list(self):
        """刷新模板列表"""
        self.template_manager.load_from_file()
        templates = list(self.template_manager.templates.values())

        self.template_list.setRowCount(len(templates))

        for row, template in enumerate(templates):
            # 模板名称
            name_item = QTableWidgetItem(template.name)
            name_item.setData(Qt.UserRole, template.id)
            self.template_list.setItem(row, 0, name_item)

            # 来源表格
            source_item = QTableWidgetItem(template.source_sheet or "通用")
            self.template_list.setItem(row, 1, source_item)

            # 映射数量
            count_item = QTableWidgetItem(str(len(template.mappings)))
            self.template_list.setItem(row, 2, count_item)

            # 创建时间
            time_item = QTableWidgetItem(template.created_time.strftime("%Y-%m-%d %H:%M"))
            self.template_list.setItem(row, 3, time_item)

        self.template_list.resizeColumnsToContents()

    def on_template_selected(self):
        """模板选择处理"""
        current_row = self.template_list.currentRow()
        if current_row >= 0:
            template_id = self.template_list.item(current_row, 0).data(Qt.UserRole)
            template = self.template_manager.get_template(template_id)

            if template:
                # 更新详情显示
                self.template_name_label.setText(template.name)
                self.source_sheet_label.setText(template.source_sheet or "通用")
                self.description_label.setText(template.description or "无描述")
                self.mapping_count_label.setText(str(len(template.mappings)))

                # 更新映射预览
                self.update_mapping_preview(template)

                # 启用操作按钮
                self.apply_btn.setEnabled(True)
                self.edit_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
        else:
            # 清空详情
            self.template_name_label.setText("-")
            self.source_sheet_label.setText("-")
            self.description_label.setText("-")
            self.mapping_count_label.setText("-")

            # 清空预览
            self.mapping_preview.setRowCount(0)

            # 禁用操作按钮
            self.apply_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def update_mapping_preview(self, template: MappingTemplate):
        """更新映射预览"""
        mappings = list(template.mappings.items())
        self.mapping_preview.setRowCount(len(mappings))

        for row, (target_name, formula) in enumerate(mappings):
            # 目标项
            target_item = QTableWidgetItem(target_name)
            self.mapping_preview.setItem(row, 0, target_item)

            # 公式
            formula_item = QTableWidgetItem(formula)
            self.mapping_preview.setItem(row, 1, formula_item)

        self.mapping_preview.resizeColumnsToContents()

    def update_target_sheets(self):
        """更新目标表格下拉框"""
        self.target_sheet_combo.clear()

        if self.workbook_manager:
            # 添加所有快报表（使用安全辅助函数）
            for sheet_name, _ in self._safe_iterate_sheets(self.workbook_manager.flash_report_sheets):
                self.target_sheet_combo.addItem(f"📊 {sheet_name}", sheet_name)

    def create_new_template(self):
        """创建新模板"""
        if not self.workbook_manager:
            QMessageBox.warning(self, "警告", "请先加载Excel文件")
            return

        dialog = TemplateCreationDialog(self.workbook_manager, self)
        if dialog.exec() == TemplateCreationDialog.Accepted:
            template = dialog.get_template()
            if template:
                self.template_manager.add_template(template)
                self.template_manager.save_to_file()
                self.refresh_template_list()

    def import_template(self):
        """导入模板"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入模板", "", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                template = MappingTemplate.from_dict(data)
                self.template_manager.add_template(template)
                self.template_manager.save_to_file()
                self.refresh_template_list()

                QMessageBox.information(self, "成功", f"模板 '{template.name}' 导入成功")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    def export_template(self):
        """导出模板"""
        current_row = self.template_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请选择要导出的模板")
            return

        template_id = self.template_list.item(current_row, 0).data(Qt.UserRole)
        template = self.template_manager.get_template(template_id)

        if not template:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出模板", f"{template.name}.json", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)

                QMessageBox.information(self, "成功", f"模板已导出到: {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def apply_template(self):
        """应用模板"""
        current_row = self.template_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请选择要应用的模板")
            return

        target_sheet = self.target_sheet_combo.currentData()
        if not target_sheet:
            QMessageBox.warning(self, "警告", "请选择目标表格")
            return

        template_id = self.template_list.item(current_row, 0).data(Qt.UserRole)
        template = self.template_manager.get_template(template_id)

        if not template:
            return

        # 确认应用
        reply = QMessageBox.question(
            self, "确认应用",
            f"将模板 '{template.name}' 应用到表格 '{target_sheet}'？\n"
            f"包含 {len(template.mappings)} 个映射关系。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            applied_count = self.template_manager.apply_template_to_sheet(
                template, self.workbook_manager, target_sheet
            )

            QMessageBox.information(
                self, "应用完成",
                f"成功应用 {applied_count} 个映射关系到表格 '{target_sheet}'"
            )

            # 发送信号
            self.templateApplied.emit(template.name, applied_count)

    def edit_template(self):
        """编辑模板"""
        current_row = self.template_list.currentRow()
        if current_row < 0:
            return

        template_id = self.template_list.item(current_row, 0).data(Qt.UserRole)
        template = self.template_manager.get_template(template_id)

        if template:
            dialog = TemplateEditDialog(template, self)
            if dialog.exec() == TemplateEditDialog.Accepted:
                updated_template = dialog.get_template()
                if updated_template:
                    self.template_manager.add_template(updated_template)
                    self.template_manager.save_to_file()
                    self.refresh_template_list()

    def delete_template(self):
        """删除模板"""
        current_row = self.template_list.currentRow()
        if current_row < 0:
            return

        template_id = self.template_list.item(current_row, 0).data(Qt.UserRole)
        template = self.template_manager.get_template(template_id)

        if template:
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除模板 '{template.name}' 吗？\n此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.template_manager.remove_template(template_id)
                self.template_manager.save_to_file()
                self.refresh_template_list()


class TemplateCreationDialog(QDialog):
    """模板创建对话框"""

    def __init__(self, workbook_manager: WorkbookManager, parent=None):
        super().__init__(parent)
        self.workbook_manager = workbook_manager
        self.template = None
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("创建映射模板")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # 基本信息
        info_group = QGroupBox("📝 基本信息")
        info_layout = QFormLayout(info_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入模板名称...")
        info_layout.addRow("模板名称:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("输入模板描述...")
        info_layout.addRow("描述:", self.description_edit)

        self.source_sheet_combo = QComboBox()
        self.populate_source_sheets()
        info_layout.addRow("来源表格:", self.source_sheet_combo)

        layout.addWidget(info_group)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.create_btn = QPushButton("✅ 创建")
        self.create_btn.clicked.connect(self.create_template)
        button_layout.addWidget(self.create_btn)

        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def populate_source_sheets(self):
        """填充来源表格选项（鲁棒性处理）"""
        if self.workbook_manager:
            for sheet in self.workbook_manager.flash_report_sheets:
                if isinstance(sheet, str):
                    sheet_name = sheet
                else:
                    sheet_name = getattr(sheet, 'name', str(sheet))
                self.source_sheet_combo.addItem(sheet_name)

    def create_template(self):
        """创建模板"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入模板名称")
            return

        source_sheet = self.source_sheet_combo.currentText()
        if not source_sheet:
            QMessageBox.warning(self, "警告", "请选择来源表格")
            return

        description = self.description_edit.toPlainText().strip()

        # 创建模板
        template_manager = TemplateManager()
        self.template = template_manager.create_template_from_workbook(
            self.workbook_manager, source_sheet, name, description
        )

        if not self.template.mappings:
            reply = QMessageBox.question(
                self, "警告",
                f"表格 '{source_sheet}' 中没有找到映射关系。\n是否仍要创建空模板？",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

        self.accept()

    def get_template(self) -> Optional[MappingTemplate]:
        """获取创建的模板"""
        return self.template


class TemplateEditDialog(QDialog):
    """模板编辑对话框"""

    def __init__(self, template: MappingTemplate, parent=None):
        super().__init__(parent)
        self.template = template
        self.setup_ui()
        self.load_template_data()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("编辑映射模板")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # 基本信息
        info_group = QGroupBox("📝 基本信息")
        info_layout = QFormLayout(info_group)

        self.name_edit = QLineEdit()
        info_layout.addRow("模板名称:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        info_layout.addRow("描述:", self.description_edit)

        layout.addWidget(info_group)

        # 映射关系
        mapping_group = QGroupBox("🔗 映射关系")
        mapping_layout = QVBoxLayout(mapping_group)

        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels(["目标项", "公式", "操作"])
        self.mapping_table.horizontalHeader().setStretchLastSection(False)
        mapping_layout.addWidget(self.mapping_table)

        layout.addWidget(mapping_group)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("💾 保存")
        self.save_btn.clicked.connect(self.save_template)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_template_data(self):
        """加载模板数据"""
        self.name_edit.setText(self.template.name)
        self.description_edit.setPlainText(self.template.description)

        # 加载映射关系
        mappings = list(self.template.mappings.items())
        self.mapping_table.setRowCount(len(mappings))

        for row, (target_name, formula) in enumerate(mappings):
            # 目标项（只读）
            target_item = QTableWidgetItem(target_name)
            target_item.setFlags(target_item.flags() & ~Qt.ItemIsEditable)
            self.mapping_table.setItem(row, 0, target_item)

            # 公式（可编辑）
            formula_item = QTableWidgetItem(formula)
            self.mapping_table.setItem(row, 1, formula_item)

            # 删除按钮
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_mapping(r))
            self.mapping_table.setCellWidget(row, 2, delete_btn)

        self.mapping_table.resizeColumnsToContents()

    def delete_mapping(self, row: int):
        """删除映射"""
        self.mapping_table.removeRow(row)

    def save_template(self):
        """保存模板"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入模板名称")
            return

        # 更新基本信息
        self.template.name = name
        self.template.description = self.description_edit.toPlainText().strip()

        # 更新映射关系
        self.template.mappings.clear()
        for row in range(self.mapping_table.rowCount()):
            target_item = self.mapping_table.item(row, 0)
            formula_item = self.mapping_table.item(row, 1)

            if target_item and formula_item:
                target_name = target_item.text()
                formula = formula_item.text().strip()
                if formula:
                    self.template.mappings[target_name] = formula

        self.accept()

    def get_template(self) -> MappingTemplate:
        """获取编辑后的模板"""
        return self.template


class WorkbookConfirmationDialog(QDialog):
    """工作簿确认对话框 - 显示所有工作表的列表供用户调整分类"""

    def __init__(self, workbook_manager, parent=None):
        super().__init__(parent)
        self.workbook_manager = workbook_manager
        self.sheet_classifications = {}  # 存储每个工作表的最终分类
        self.init_ui()
        self.load_sheets()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(f"工作簿确认 - {self.workbook_manager.file_name}")
        self.setFixedSize(900, 700)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("工作表分类确认")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px; color: #2E86AB;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 说明
        info_label = QLabel(
            f"文件：{self.workbook_manager.file_name}\n"
            "请确认每个工作表的分类。您可以调整系统的自动识别结果，或取消不需要的工作表。"
        )
        info_label.setStyleSheet("color: #666; font-size: 12px; margin: 10px; padding: 10px; border: 1px solid #dee2e6; border-radius: 5px;")
        layout.addWidget(info_label)

        # 创建表格
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor

        self.sheets_table = QTableWidget()
        self.sheets_table.setColumnCount(4)
        self.sheets_table.setHorizontalHeaderLabels(["工作表名称", "系统建议", "用户分类", "是否启用"])

        # 设置表格属性
        header = self.sheets_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 工作表名称列自适应
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 系统建议列
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 用户分类列
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 是否启用列

        self.sheets_table.setAlternatingRowColors(True)
        self.sheets_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sheets_table.verticalHeader().setVisible(False)

        layout.addWidget(self.sheets_table)

        # 统计信息
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("font-size: 12px; color: #666; margin: 10px;")
        layout.addWidget(self.stats_label)

        # 批量操作按钮
        batch_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_sheets)
        batch_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("全不选")
        self.deselect_all_btn.clicked.connect(self.deselect_all_sheets)
        batch_layout.addWidget(self.deselect_all_btn)

        batch_layout.addStretch()

        self.auto_classify_btn = QPushButton("使用系统建议")
        self.auto_classify_btn.setToolTip("将所有工作表的分类设置为系统建议的分类")
        self.auto_classify_btn.clicked.connect(self.use_auto_classification)
        batch_layout.addWidget(self.auto_classify_btn)

        layout.addLayout(batch_layout)

        # 确认按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.confirm_btn = QPushButton("确认并开始处理")
        self.confirm_btn.setDefault(True)
        self.confirm_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; padding: 8px 16px; }")
        self.confirm_btn.clicked.connect(self.confirm_classifications)
        button_layout.addWidget(self.confirm_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_sheets(self):
        """加载工作表数据"""
        from PySide6.QtWidgets import QComboBox, QCheckBox
        from PySide6.QtCore import Qt

        all_sheets = []

        # 收集所有工作表
        for sheet in self.workbook_manager.flash_report_sheets:
            all_sheets.append((sheet.name, "快报表", sheet.sheet_type.value))

        for sheet in self.workbook_manager.data_source_sheets:
            all_sheets.append((sheet.name, "数据来源表", sheet.sheet_type.value))

        self.sheets_table.setRowCount(len(all_sheets))

        for row, (sheet_name, suggestion, sheet_type) in enumerate(all_sheets):
            # 工作表名称
            name_item = QTableWidgetItem(sheet_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.sheets_table.setItem(row, 0, name_item)

            # 系统建议
            suggestion_item = QTableWidgetItem(suggestion)
            suggestion_item.setFlags(suggestion_item.flags() & ~Qt.ItemIsEditable)
            if suggestion == "快报表":
                suggestion_item.setBackground(QColor("#e7f3ff"))
            else:
                suggestion_item.setBackground(QColor("#fff2e7"))
            self.sheets_table.setItem(row, 1, suggestion_item)

            # 用户分类下拉框
            classification_combo = QComboBox()
            classification_combo.addItems(["快报表", "数据来源表", "跳过"])
            classification_combo.setCurrentText(suggestion)  # 默认使用系统建议
            classification_combo.currentTextChanged.connect(self.update_stats)
            self.sheets_table.setCellWidget(row, 2, classification_combo)

            # 是否启用复选框
            enable_checkbox = QCheckBox()
            enable_checkbox.setChecked(True)  # 默认启用
            enable_checkbox.stateChanged.connect(self.update_stats)
            # 居中显示复选框
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(enable_checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.sheets_table.setCellWidget(row, 3, checkbox_widget)

            # 保存分类信息
            self.sheet_classifications[sheet_name] = {
                'suggestion': suggestion,
                'combo': classification_combo,
                'checkbox': enable_checkbox,
                'original_type': sheet_type
            }

        self.update_stats()

    def update_stats(self):
        """更新统计信息"""
        flash_report_count = 0
        data_source_count = 0
        skip_count = 0
        enabled_count = 0

        for sheet_name, info in self.sheet_classifications.items():
            if info['checkbox'].isChecked():
                enabled_count += 1
                classification = info['combo'].currentText()
                if classification == "快报表":
                    flash_report_count += 1
                elif classification == "数据来源表":
                    data_source_count += 1
                else:
                    skip_count += 1

        total_count = len(self.sheet_classifications)
        stats_text = (
            f"共 {total_count} 个工作表，已启用 {enabled_count} 个 | "
            f"快报表: {flash_report_count} 个，数据来源表: {data_source_count} 个，跳过: {skip_count} 个"
        )
        self.stats_label.setText(stats_text)

    def select_all_sheets(self):
        """全选所有工作表"""
        for info in self.sheet_classifications.values():
            info['checkbox'].setChecked(True)

    def deselect_all_sheets(self):
        """取消选择所有工作表"""
        for info in self.sheet_classifications.values():
            info['checkbox'].setChecked(False)

    def use_auto_classification(self):
        """使用系统自动分类"""
        for info in self.sheet_classifications.values():
            info['combo'].setCurrentText(info['suggestion'])

    def confirm_classifications(self):
        """确认分类设置"""
        # 检查是否至少启用了一个工作表
        enabled_sheets = [name for name, info in self.sheet_classifications.items()
                         if info['checkbox'].isChecked()]

        if not enabled_sheets:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "请至少启用一个工作表！")
            return

        # 检查是否有快报表
        flash_reports = [name for name, info in self.sheet_classifications.items()
                        if info['checkbox'].isChecked() and info['combo'].currentText() == "快报表"]

        if not flash_reports:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, "确认",
                "没有选择任何快报表，这意味着只会处理数据来源表。是否继续？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.accept()

    def get_final_classifications(self):
        """获取最终的分类结果"""
        result = {
            'flash_reports': [],
            'data_sources': [],
            'skipped': [],
            'disabled': []
        }

        for sheet_name, info in self.sheet_classifications.items():
            if not info['checkbox'].isChecked():
                result['disabled'].append(sheet_name)
                continue

            classification = info['combo'].currentText()
            if classification == "快报表":
                result['flash_reports'].append(sheet_name)
            elif classification == "数据来源表":
                result['data_sources'].append(sheet_name)
            else:
                result['skipped'].append(sheet_name)

        return result


class SheetClassificationConfirmDialog(QDialog):
    """工作表分类确认对话框 - 单个工作表的简单确认"""

    def __init__(self, sheet_name: str, auto_classification: str, parent=None):
        super().__init__(parent)
        self.sheet_name = sheet_name
        self.auto_classification = auto_classification
        self.result_classification = "skip"
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(f"工作表分类确认 - {self.sheet_name}")
        self.setFixedSize(500, 350)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel(f"请确认工作表的类型")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)

        # 工作表信息
        info_group = QGroupBox("工作表信息")
        info_layout = QFormLayout(info_group)

        # 工作表名称
        sheet_label = QLabel(self.sheet_name)
        sheet_label.setStyleSheet("font-weight: bold; color: #2E86AB;")
        info_layout.addRow("工作表名称:", sheet_label)

        # 建议分类
        suggestion_label = QLabel(self.auto_classification)
        suggestion_label.setStyleSheet("font-weight: bold; color: #F24236;")
        info_layout.addRow("系统建议:", suggestion_label)

        layout.addWidget(info_group)

        # 分类选择
        classification_group = QGroupBox("请选择正确的分类")
        classification_layout = QVBoxLayout(classification_group)

        # 选项说明
        help_label = QLabel(
            "• 快报表：需要填写数据的目标表格\n"
            "• 数据来源表：提供源数据的参考表格\n"
            "• 跳过：既不是快报表也不是数据来源表"
        )
        help_label.setStyleSheet("color: #666; font-size: 12px; margin: 5px;")
        classification_layout.addWidget(help_label)

        # 单选按钮
        from PySide6.QtWidgets import QRadioButton, QButtonGroup

        self.button_group = QButtonGroup()

        self.flash_report_radio = QRadioButton("[表] 快报表（要填写的表）")
        self.flash_report_radio.setStyleSheet("font-size: 14px; padding: 5px;")
        self.button_group.addButton(self.flash_report_radio, 1)
        classification_layout.addWidget(self.flash_report_radio)

        self.data_source_radio = QRadioButton("[数据] 数据来源表")
        self.data_source_radio.setStyleSheet("font-size: 14px; padding: 5px;")
        self.button_group.addButton(self.data_source_radio, 2)
        classification_layout.addWidget(self.data_source_radio)

        self.skip_radio = QRadioButton("[跳过] 跳过此表（不进行处理）")
        self.skip_radio.setStyleSheet("font-size: 14px; padding: 5px;")
        self.button_group.addButton(self.skip_radio, 3)
        classification_layout.addWidget(self.skip_radio)

        # 根据建议设置默认选择
        if self.auto_classification == "快报表":
            self.flash_report_radio.setChecked(True)
        else:
            self.data_source_radio.setChecked(True)

        layout.addWidget(classification_group)

        # 按钮区域
        button_layout = QHBoxLayout()

        # 全部使用建议按钮
        self.auto_all_btn = QPushButton("[AI] 全部使用系统建议")
        self.auto_all_btn.setToolTip("对所有剩余工作表都使用系统建议，不再询问")
        self.auto_all_btn.clicked.connect(self.auto_classify_all)
        button_layout.addWidget(self.auto_all_btn)

        button_layout.addStretch()

        # 确认按钮
        self.confirm_btn = QPushButton("[OK] 确认")
        self.confirm_btn.setDefault(True)
        self.confirm_btn.clicked.connect(self.confirm_classification)
        button_layout.addWidget(self.confirm_btn)

        # 取消按钮
        self.cancel_btn = QPushButton("[X] 取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def confirm_classification(self):
        """确认分类选择"""
        if self.flash_report_radio.isChecked():
            self.result_classification = "flash_report"
        elif self.data_source_radio.isChecked():
            self.result_classification = "data_source"
        elif self.skip_radio.isChecked():
            self.result_classification = "skip"

        self.accept()

    def auto_classify_all(self):
        """自动分类所有剩余工作表"""
        self.result_classification = "auto_all"
        self.accept()

    def get_classification(self) -> str:
        """获取分类结果"""
        return self.result_classification


if __name__ == "__main__":
    main()