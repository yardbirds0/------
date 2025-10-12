#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI辅助财务报表数据映射与填充工具 - PySide6版本
基于程序要求.md的完整实现
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
import json
from datetime import datetime
import requests
import threading
import time

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTreeView,
    QTableView,
    QTextEdit,
    QPlainTextEdit,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QDockWidget,
    QFormLayout,
    QLabel,
    QProgressBar,
    QStatusBar,
    QMenuBar,
    QToolBar,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QStyle,
    QHeaderView,
    QAbstractItemView,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QSpinBox,
    QCheckBox,
    QMenu,
    QDialog,
    QComboBox,
    QScrollArea,
    QSlider,
    QDoubleSpinBox,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
)
from PySide6.QtCore import (
    Qt,
    QAbstractItemModel,
    QModelIndex,
    Signal,
    QThread,
    QTimer,
    QSettings,
    QMimeData,
    QSize,  # ⭐ 添加QSize支持自动行高
)
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QStandardItemModel,
    QStandardItem,
    QFont,
    QColor,
    QBrush,
    QPalette,
    QSyntaxHighlighter,
    QTextCharFormat,
    QDrag,
    QAction,
    QPainter,
    QPen,
)

# 项目模块导入
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models.data_models import (
    TargetItem,
    SourceItem,
    MappingFormula,
    WorkbookManager,
    SheetType,
    FormulaStatus,
    MappingTemplate,
    TemplateManager,
)
from modules.file_manager import FileManager
# AI Integration
from modules.ai_integration.api_providers.base_provider import ProviderConfig
from controllers.chat_controller import ChatController
from modules.data_extractor import DataExtractor
from modules.calculation_engine import CalculationEngine
from components.advanced_widgets import (
    DragDropTreeView,
    FormulaEditor,
    FormulaSyntaxHighlighter,
    FormulaEditorDelegate,
    SearchableSourceTree,
    PropertyTableWidget,
    FormulaEditDialog,
    ColumnConfigDialog,
    AutoResizeTableWidget,
    ensure_interactive_header,
    ensure_word_wrap,
    schedule_row_resize,
    apply_multirow_header,
    derive_header_layout_from_metadata,
    distribute_columns_evenly,  # 添加智能填充函数
    ROW_NUMBER_COLUMN_WIDTH,
)
from components.sheet_explorer import SheetClassificationDialog

# ==================== 全局表格样式 ====================

# 统一的表格网格线样式
TABLE_GRID_STYLE = """
    QTableWidget {
        gridline-color: #d0d0d0;
        border: 1px solid #dee2e6;
        border-radius: 4px;
    }
    QTableWidget::item {
        padding: 4px;
        border: none;
    }
    QTableView {
        gridline-color: #d0d0d0;
        border: 1px solid #dee2e6;
        border-radius: 4px;
    }
    QTableView::item {
        padding: 4px;
        border: none;
    }
"""

# ==================== AI Parameter Control Classes ====================


class ParameterControl(QWidget):
    """AI参数控制基类 - 包含启用复选框和参数值控件"""

    def __init__(
        self,
        param_name: str,
        display_name: str,
        description: str = "",
        default_value=None,
        parent=None,
    ):
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
        self.setStyleSheet(
            f"""
            ParameterControl {{
                border: 1px solid {'#3498db' if checked else '#bdc3c7'};
                border-radius: 4px;
                background-color: {'#f8f9fa' if checked else '#ffffff'};
                margin: 2px;
            }}
        """
        )

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

    def __init__(
        self,
        param_name: str,
        display_name: str,
        description: str = "",
        default_value: float = 0.0,
        min_value: float = 0.0,
        max_value: float = 1.0,
        decimals: int = 2,
        step: float = 0.1,
        parent=None,
    ):
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
        self.slider.setMinimum(int(self.min_value * (10**self.decimals)))
        self.slider.setMaximum(int(self.max_value * (10**self.decimals)))
        self.slider.setValue(int(self.default_value * (10**self.decimals)))
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
        float_value = value / (10**self.decimals)
        self.text_input.setText(f"{float_value:.{self.decimals}f}")

    def on_text_changed(self, text: str):
        """文本输入改变时更新滑块"""
        try:
            value = float(text)
            if self.min_value <= value <= self.max_value:
                slider_value = int(value * (10**self.decimals))
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
        self.slider.setValue(int(value * (10**self.decimals)))

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

    def __init__(
        self,
        param_name: str,
        display_name: str,
        description: str = "",
        default_value: str = "",
        placeholder: str = "",
        multiline: bool = False,
        parent=None,
    ):
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

    def __init__(
        self,
        param_name: str,
        display_name: str,
        description: str = "",
        default_value=None,
        options: List = None,
        parent=None,
    ):
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
        self.title_button.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                border: none;
                background: transparent;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(100, 149, 237, 0.15);
            }
        """
        )
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
        self.setStyleSheet(
            """
            UserMessageBubble {
                background-color: #007AFF;
                border-radius: 12px;
                margin-left: 50px;
                margin-right: 10px;
            }
        """
        )
        self.message_label.setStyleSheet("color: white; padding: 8px;")
        self.time_label.setStyleSheet(
            "color: #E0E0E0; font-size: 10px; padding-right: 8px;"
        )


class AssistantMessageBubble(MessageBubble):
    """AI助手消息气泡"""

    def __init__(self, message: str = "", timestamp: str = None, parent=None):
        super().__init__(message, timestamp, parent)
        self.is_streaming = False
        self.setup_style()

    def setup_style(self):
        """设置AI消息样式"""
        self.setStyleSheet(
            """
            AssistantMessageBubble {
                background-color: #F0F0F0;
                border-radius: 12px;
                margin-left: 10px;
                margin-right: 50px;
            }
        """
        )
        self.message_label.setStyleSheet("color: #333; padding: 8px;")
        self.time_label.setStyleSheet(
            "color: #888; font-size: 10px; padding-right: 8px;"
        )

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
        self.dots_label.setStyleSheet(
            "color: #888; font-size: 16px; padding-left: 10px;"
        )
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
        self.setStyleSheet(
            """
            ChatScrollArea {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
        """
        )

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
        self.session.headers.update(
            {
                "User-Agent": "AI-Report-Tool/1.0",
                "Accept": "application/json",
                "Connection": "keep-alive",
            }
        )

    def build_request_payload(
        self,
        api_url: str,
        api_key: str,
        parameters: Dict,
        system_prompt: str = "",
        user_message: str = "",
    ) -> Dict:
        """构建API请求载荷"""
        # 基础消息结构
        messages = []

        # 添加系统提示（如果有）
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})

        # 添加用户消息
        user_content = (
            user_message.strip()
            if user_message.strip()
            else "请说一句话来测试API连接。"
        )
        messages.append({"role": "user", "content": user_content})

        # 构建请求载荷
        payload = {"messages": messages}

        # 添加启用的参数
        for param_name, param_value in parameters.items():
            if param_name == "stop" and isinstance(param_value, str):
                # 处理停止序列（逗号分隔的字符串转为数组）
                if param_value.strip():
                    payload[param_name] = [
                        s.strip() for s in param_value.split(",") if s.strip()
                    ]
            elif param_name == "response_format":
                # 处理响应格式
                if param_value != "text":
                    payload[param_name] = {"type": param_value}
            else:
                payload[param_name] = param_value

        return payload

    def make_request(
        self,
        api_url: str,
        api_key: str,
        parameters: Dict,
        system_prompt: str = "",
        user_message: str = "",
        stream: bool = False,
    ) -> Dict:
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
            payload = self.build_request_payload(
                api_url, api_key, parameters, system_prompt, user_message
            )

            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }

            # 调试回调：显示请求头
            if "on_request_headers" in self.debug_callbacks:
                headers_text = json.dumps(headers, indent=2, ensure_ascii=False)
                self.debug_callbacks["on_request_headers"](headers_text)

            # 调试回调：显示JSON结构
            if "on_json_structure" in self.debug_callbacks:
                json_text = json.dumps(payload, indent=2, ensure_ascii=False)
                self.debug_callbacks["on_json_structure"](f"请求JSON:\n{json_text}")

            # 发送请求
            if stream:
                return self._handle_streaming_request(api_url, headers, payload)
            else:
                return self._handle_normal_request(api_url, headers, payload)

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "response_data": None,
                "ai_response": None,
            }

            # 调试回调：显示错误
            if "on_ai_response" in self.debug_callbacks:
                self.debug_callbacks["on_ai_response"](f"错误: {str(e)}")

            return error_result

    def _handle_normal_request(
        self, api_url: str, headers: Dict, payload: Dict
    ) -> Dict:
        """处理非流式请求"""
        response = self.session.post(api_url, headers=headers, json=payload, timeout=30)

        # 调试回调：显示接收到的数据
        if "on_received_data" in self.debug_callbacks:
            received_text = f"状态码: {response.status_code}\n\n"
            received_text += (
                f"响应头:\n{json.dumps(dict(response.headers), indent=2)}\n\n"
            )
            received_text += f"响应体:\n{response.text}"
            self.debug_callbacks["on_received_data"](received_text)

        if response.status_code == 200:
            response_data = response.json()

            # 调试回调：显示JSON结构
            if "on_json_structure" in self.debug_callbacks:
                json_text = json.dumps(response_data, indent=2, ensure_ascii=False)
                current_text = self.debug_callbacks.get("current_json_text", "")
                updated_text = f"{current_text}\n\n响应JSON:\n{json_text}"
                self.debug_callbacks["on_json_structure"](updated_text)

            # 提取AI响应
            ai_response = ""
            if "choices" in response_data and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    ai_response = choice["message"]["content"]

            # 调试回调：显示AI响应
            if "on_ai_response" in self.debug_callbacks:
                self.debug_callbacks["on_ai_response"](ai_response)

            return {
                "success": True,
                "error": None,
                "response_data": response_data,
                "ai_response": ai_response,
            }
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            return {
                "success": False,
                "error": error_msg,
                "response_data": None,
                "ai_response": None,
            }

    def _handle_streaming_request(
        self, api_url: str, headers: Dict, payload: Dict
    ) -> Dict:
        """处理流式请求"""
        # 设置流式请求参数
        payload["stream"] = True

        response = self.session.post(
            api_url, headers=headers, json=payload, stream=True, timeout=30
        )

        if response.status_code != 200:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            return {
                "success": False,
                "error": error_msg,
                "response_data": None,
                "ai_response": None,
            }

        # 处理流式响应
        accumulated_content = ""
        full_response_chunks = []

        try:
            # 调试回调：显示开始接收流式数据
            if "on_received_data" in self.debug_callbacks:
                self.debug_callbacks["on_received_data"]("开始接收流式数据...\n")

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    line = line.strip()

                    # 跳过注释行和空行
                    if not line or line.startswith(":"):
                        continue

                    # 处理SSE数据
                    if line.startswith("data: "):
                        data_content = line[6:]  # 移除 "data: " 前缀

                        # 检查是否是结束标记
                        if data_content == "[DONE]":
                            break

                        try:
                            chunk_data = json.loads(data_content)
                            full_response_chunks.append(chunk_data)

                            # 提取增量内容
                            if (
                                "choices" in chunk_data
                                and len(chunk_data["choices"]) > 0
                            ):
                                choice = chunk_data["choices"][0]
                                if "delta" in choice and "content" in choice["delta"]:
                                    content = choice["delta"]["content"]
                                    accumulated_content += content

                                    # 实时更新AI响应显示
                                    if "on_ai_response" in self.debug_callbacks:
                                        self.debug_callbacks["on_ai_response"](
                                            accumulated_content
                                        )

                            # 更新接收数据显示
                            if "on_received_data" in self.debug_callbacks:
                                received_text = f"接收到数据块 {len(full_response_chunks)}:\n{data_content}\n\n"
                                current_text = self.debug_callbacks.get(
                                    "current_received_text", ""
                                )
                                self.debug_callbacks["on_received_data"](
                                    current_text + received_text
                                )

                        except json.JSONDecodeError as e:
                            # 忽略JSON解析错误，继续处理下一行
                            continue

            # 调试回调：显示完整JSON结构
            if "on_json_structure" in self.debug_callbacks and full_response_chunks:
                json_text = json.dumps(
                    full_response_chunks, indent=2, ensure_ascii=False
                )
                current_text = self.debug_callbacks.get("current_json_text", "")
                updated_text = f"{current_text}\n\n流式响应JSON块:\n{json_text}"
                self.debug_callbacks["on_json_structure"](updated_text)

            return {
                "success": True,
                "error": None,
                "response_data": full_response_chunks,
                "ai_response": accumulated_content,
            }

        except Exception as e:
            error_msg = f"流式响应处理错误: {str(e)}"
            return {
                "success": False,
                "error": error_msg,
                "response_data": None,
                "ai_response": accumulated_content,  # 返回已接收的部分内容
            }


from utils.excel_utils import (
    validate_formula_syntax_v2,
    parse_formula_references_v2,
    parse_formula_references_v3,
    build_formula_reference_v2,
    evaluate_formula_with_values_v2,
    # 三段式公式支持
    validate_formula_syntax_three_segment,
    parse_formula_references_three_segment,
    build_formula_reference_three_segment,
    evaluate_formula_with_values_three_segment,
)


class LogManager:
    """日志管理器 - 支持操作日志和系统日志双区域"""

    def __init__(self, operation_widget: QPlainTextEdit, system_widget: QPlainTextEdit = None):
        """
        初始化日志管理器

        Args:
            operation_widget: 操作日志输出控件
            system_widget: 系统日志输出控件（可选，如果不提供则都输出到operation_widget）
        """
        self.operation_widget = operation_widget  # 操作日志区域
        self.system_widget = system_widget if system_widget else operation_widget  # 系统日志区域
        self.output_widget = operation_widget  # 向后兼容

    def log(self, message: str, level: str = "INFO", log_type: str = "system"):
        """
        添加日志消息

        Args:
            message: 日志消息
            level: 日志级别 (INFO, WARNING, ERROR, SUCCESS)
            log_type: 日志类型 ("operation" 或 "system")
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"

        # 根据日志类型选择输出控件
        if log_type == "operation":
            self.operation_widget.appendPlainText(log_entry)
        else:
            self.system_widget.appendPlainText(log_entry)

    def operation(self, message: str, level: str = "INFO"):
        """操作日志 - 用户的主动操作"""
        self.log(message, level, log_type="operation")

    def system(self, message: str, level: str = "INFO"):
        """系统日志 - 系统内部处理"""
        self.log(message, level, log_type="system")

    def info(self, message: str, log_type: str = "system"):
        """INFO级别日志"""
        self.log(message, "INFO", log_type=log_type)

    def warning(self, message: str, log_type: str = "system"):
        """WARNING级别日志"""
        self.log(message, "WARNING", log_type=log_type)

    def error(self, message: str, log_type: str = "system"):
        """ERROR级别日志"""
        self.log(message, "ERROR", log_type=log_type)

    def success(self, message: str, log_type: str = "operation"):
        """SUCCESS级别日志（默认为操作日志）"""
        self.log(message, "SUCCESS", log_type=log_type)

    def clear(self):
        """清空所有日志"""
        self.operation_widget.clear()
        if self.system_widget and self.system_widget != self.operation_widget:
            self.system_widget.clear()


class FormulaSyntaxHighlighter(QSyntaxHighlighter):
    """公式语法高亮器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # 工作表引用格式: [工作表名]A1
        sheet_format = QTextCharFormat()
        sheet_format.setForeground(QColor(0, 120, 215))  # 蓝色
        sheet_format.setFontWeight(QFont.Bold)

        cell_format = QTextCharFormat()
        cell_format.setForeground(QColor(0, 128, 0))  # 绿色

        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor(255, 140, 0))  # 橙色
        operator_format.setFontWeight(QFont.Bold)

        # 添加高亮规则
        self.highlighting_rules = [
            (r"\[[^\]]+\]", sheet_format),  # [工作表名]
            (r"(?<=\])\$?[A-Z]+\$?\d+", cell_format),  # 单元格
            (r"[+\-*/()]", operator_format),  # 运算符
        ]

    def highlightBlock(self, text):
        """应用语法高亮"""
        import re

        for pattern, format_obj in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format_obj)


class SearchHighlightDelegate(QStyledItemDelegate):
    """搜索高亮委托 - 覆盖CSS样式实现高亮显示

    根据data/importants.md的经验，Qt的CSS样式会覆盖model返回的BackgroundRole。
    解决方案：使用自定义delegate完全控制绘制流程，绕过Qt的style系统。

    核心修复：
    1. 先让Qt绘制默认内容（包括文字）
    2. 然后在文字上方叠加半透明高亮背景
    3. 这样既保留文字，又显示高亮效果
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlight_color = QColor("#ffe0f0")  # 粉色高亮，匹配主题

    def sizeHint(self, option, index: QModelIndex):
        """计算单元格大小提示（支持单元格自动换行与多行显示）。"""
        text = index.data(Qt.DisplayRole)
        if not text:
            return super().sizeHint(option, index)

        from PySide6.QtGui import QFontMetrics

        metrics = QFontMetrics(option.font)
        column_width = option.rect.width()

        if column_width <= 0 and option.widget is not None:
            try:
                column_width = option.widget.columnWidth(index.column())
            except Exception:
                column_width = 200

        available_width = max(40, column_width - 12)
        text_rect_height = metrics.boundingRect(
            0,
            0,
            available_width,
            0,
            Qt.TextWordWrap,
            str(text),
        ).height()

        total_height = text_rect_height + 12
        total_height = max(30, min(600, total_height))

        return QSize(column_width, total_height)

    def paint(self, painter: QPainter, option, index: QModelIndex):
        """重写paint方法，先绘制内容再叠加高亮背景"""
        # 检查是否有高亮背景色
        bg_data = index.data(Qt.BackgroundRole)

        # 🔧 支持QColor和QBrush两种类型
        bg_color = None
        if isinstance(bg_data, QColor):
            bg_color = bg_data
        elif isinstance(bg_data, QBrush):
            bg_color = bg_data.color()  # 从QBrush提取QColor

        if bg_color and bg_color.isValid():
            # 🔧 关键修复：先让Qt绘制默认内容（包括文字）
            # 注意：不修改option，使用原始option让文字正常显示
            super().paint(painter, option, index)

            # 🔧 然后在文字上方叠加半透明高亮背景
            painter.save()

            # 创建半透明的高亮颜色（让文字可见）
            highlight_overlay = QColor(bg_color)
            highlight_overlay.setAlpha(120)  # 设置透明度，让文字可见

            painter.fillRect(option.rect, highlight_overlay)

            # 如果是选中状态，添加额外的选中效果
            if option.state & QStyle.State_Selected:
                selection_overlay = QColor(235, 145, 190, 50)  # 更浅的半透明粉色
                painter.fillRect(option.rect, selection_overlay)

            # 如果是悬停状态，添加额外的悬停效果
            elif option.state & QStyle.State_MouseOver:
                hover_overlay = QColor(235, 145, 190, 30)  # 非常浅的半透明粉色
                painter.fillRect(option.rect, hover_overlay)

            painter.restore()
        else:
            # 没有高亮，使用默认绘制（CSS生效）
            super().paint(painter, option, index)


class TargetItemModel(QAbstractItemModel):
    """目标项树模型 - 支持层级结构和导航"""

    # 信号
    itemSelected = Signal(str)  # (target_id)
    navigationRequested = Signal(str, str)  # (category, item_name)
    formulaEdited = Signal(list)  # 更新的目标项ID列表

    def __init__(self, workbook_manager: Optional[WorkbookManager] = None):
        super().__init__()
        self.workbook_manager = workbook_manager
        self.active_sheet_name = None  # 当前激活的工作表名
        self.root_items = []
        self.category_items = {}  # 分类节点
        self.static_headers = ["状态", "级别"]  # 删除"项目名称"，改为从Excel动态列获取
        self.dynamic_columns: List[Dict[str, Any]] = []
        self.headers = list(self.static_headers)
        self._header_layout: Dict[int, Dict[str, Any]] = {}
        self._header_row_count: int = 1
        self.search_text = ""  # 搜索文本，用于高亮匹配单元格
        self.editable_columns_set: Set[str] = set()  # 可编辑列名集合

        # 添加日志管理器引用
        self.log_manager = None
        self.active_sheet_metadata = []

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

    def set_search_text(self, text: str):
        """设置搜索文本并触发数据刷新以实现高亮"""
        self.search_text = text.lower() if text else ""
        # 触发所有可见行的背景色更新
        if self.root_items:
            top_left = self.index(0, 0)
            bottom_right = self.index(len(self.root_items) - 1, self.columnCount() - 1)
            self.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])

    def set_editable_columns(self, column_config: List[Dict[str, Any]]):
        """设置可编辑列（从配置读取）"""
        self.editable_columns_set = {
            entry["name"] for entry in column_config if entry.get("editable", False)
        }

    def build_tree(self):
        """构建扁平列表 - 按原始Excel行顺序显示，不分组"""
        self.root_items = []
        self.category_items = {}

        if not self.workbook_manager:
            self.dynamic_columns = []
            self.headers = list(self.static_headers)
            self._header_layout = {}
            self._header_row_count = 1
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

        self._update_dynamic_columns(filtered_targets)

    def _update_dynamic_columns(self, filtered_targets: List[TargetItem]):
        sheet_name = self.active_sheet_name
        if not sheet_name and filtered_targets:
            sheet_name = filtered_targets[0].sheet_name

        metadata: List[Dict[str, Any]] = []
        if self.workbook_manager and sheet_name:
            metadata = self.workbook_manager.target_sheet_columns.get(sheet_name, [])

        # 表格列元数据已加载（不输出日志，避免技术细节）

        # 如果元数据为空，提供默认配置
        if not metadata and sheet_name:
            if hasattr(self, "log_manager"):
                self.log_manager.warning(
                    f"表格'{sheet_name}'的列元数据为空，使用默认配置"
                )
            # 为"企业财务快报利润因素分析表"提供特殊的默认配置
            if "利润因素分析" in sheet_name:
                metadata = [
                    {
                        "key": "指标名称",
                        "display_name": "指标名称",
                        "is_data_column": False,
                        "column_index": 0,
                        "primary_header": "指标名称",
                        "primary_col_span": 1,
                        "header_row_count": 1,
                    },
                    {
                        "key": "金额",
                        "display_name": "金额",
                        "is_data_column": True,
                        "column_index": 1,
                        "primary_header": "金额",
                        "primary_col_span": 1,
                        "header_row_count": 1,
                    },
                    {
                        "key": "备注",
                        "display_name": "备注",
                        "is_data_column": False,
                        "column_index": 2,
                        "primary_header": "备注",
                        "primary_col_span": 1,
                        "header_row_count": 1,
                    },
                ]
            else:
                # 通用默认配置
                metadata = [
                    {
                        "key": "行次",
                        "display_name": "行次",
                        "is_data_column": False,
                        "column_index": 0,
                        "primary_header": "行次",
                        "primary_col_span": 1,
                        "header_row_count": 1,
                    },
                    {
                        "key": "项目",
                        "display_name": "项目",
                        "is_data_column": False,
                        "column_index": 1,
                        "primary_header": "项目",
                        "primary_col_span": 1,
                        "header_row_count": 1,
                    },
                    {
                        "key": "数值",
                        "display_name": "数值",
                        "is_data_column": True,
                        "column_index": 2,
                        "primary_header": "数值",
                        "primary_col_span": 1,
                        "header_row_count": 1,
                    },
                ]

        self.active_sheet_metadata = metadata
        self.dynamic_columns = []
        for entry in metadata:
            key = entry.get("key")
            if not key:
                continue
            display_name = entry.get("display_name") or key
            self.dynamic_columns.append(
                {
                    "key": key,
                    "name": display_name,
                    "is_data_column": entry.get("is_data_column", False),
                    "meta": entry,
                }
            )

        # 只传递动态列的metadata，不包含静态列
        # 参考 SearchableSourceTree 的实现方式
        layout_map, row_count = derive_header_layout_from_metadata(
            metadata,  # 这里传递完整metadata，因为target_sheet_columns只包含动态列
            base_offset=len(self.static_headers),  # 动态列从第2列开始（跳过状态、级别）
        )

        self._header_layout = layout_map
        self._header_row_count = row_count

        # 确保headers至少包含静态列
        if not self.dynamic_columns:
            # 如果没有动态列，至少保证headers包含静态列
            self.headers = list(self.static_headers)
            if hasattr(self, "log_manager") and self.log_manager:
                self.log_manager.warning(f"表格'{sheet_name}'没有动态列，仅使用静态列")
        else:
            self.headers = self.static_headers + [
                col["name"] for col in self.dynamic_columns
            ]

    def get_header_layout(self) -> Tuple[Dict[int, Dict[str, Any]], int]:
        return self._header_layout, self._header_row_count

    def _column_meta_at(self, model_column: int) -> Optional[Dict[str, Any]]:
        index = model_column - len(self.static_headers)
        if index < 0 or index >= len(self.dynamic_columns):
            return None
        return self.dynamic_columns[index]

    def _resolve_target_status(self, target_item: TargetItem) -> str:
        if not self.workbook_manager:
            return "❓"

        mappings = self.workbook_manager.mapping_formulas.get(target_item.id, {})
        if not mappings:
            return "⭕"

        if isinstance(mappings, MappingFormula):
            existing_statuses = {mappings.status}
        else:
            existing_statuses = {mapping.status for mapping in mappings.values()}

        priority = [
            (FormulaStatus.ERROR, "❌"),
            (FormulaStatus.PENDING, "⏳"),
            (FormulaStatus.AI_GENERATED, "🤖"),
            (FormulaStatus.USER_MODIFIED, "✏️"),
            (FormulaStatus.VALIDATED, "✅"),
            (FormulaStatus.CALCULATED, "🟢"),
        ]

        for status, icon in priority:
            if status in existing_statuses:
                return icon

        return "⭕"

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
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
                    return self._resolve_target_status(item)
                elif column == 1:  # 级别
                    return (
                        item.hierarchical_number
                        if hasattr(item, "hierarchical_number")
                        else "1"
                    )
                else:  # column >= 2: 动态列（原来是 >= 3）
                    column_meta = self._column_meta_at(column)
                    if not column_meta or not self.workbook_manager:
                        return ""

                    # 1. 尝试获取映射公式和计算结果
                    mapping = self.workbook_manager.get_mapping(
                        item.id, column_meta["key"]
                    )
                    result_map = self.workbook_manager.calculation_results.get(
                        item.id, {}
                    )
                    result = result_map.get(column_meta["key"])

                    preview_text = ""
                    if result and result.success and result.result is not None:
                        preview_text = str(result.result)

                    # 2. 如果有映射公式，显示公式（和结果）
                    if mapping:
                        if mapping.formula:
                            if preview_text:
                                # ⭐ 三段式：多行显示，每个来源项一行（运算符跟随），结果单独一行
                                from utils.excel_utils import (
                                    parse_formula_references_three_segment,
                                )

                                refs = parse_formula_references_three_segment(
                                    mapping.formula
                                )
                                if refs:
                                    lines = []
                                    remaining_formula = mapping.formula

                                    for i, ref in enumerate(refs):
                                        full_ref = ref["full_reference"]
                                        pos = remaining_formula.find(full_ref)

                                        if pos >= 0:
                                            # 提取引用后的部分
                                            after_ref = remaining_formula[
                                                pos + len(full_ref) :
                                            ]

                                            # 如果不是最后一个引用，提取运算符
                                            operator = ""
                                            if i < len(refs) - 1:
                                                after_stripped = after_ref.strip()
                                                for op in ["+", "-", "*", "/"]:
                                                    if after_stripped.startswith(op):
                                                        operator = f" {op}"
                                                        break

                                            # 构建这一行：引用 + 运算符
                                            lines.append(full_ref + operator)

                                            # 更新剩余公式
                                            remaining_formula = after_ref

                                    lines.append(f"→ {preview_text}")
                                    return "\n".join(lines)
                                # 回退：如果解析失败，使用原格式
                                return f"{mapping.formula}\n→ {preview_text}"
                            return mapping.formula
                        if mapping.constant_value not in (None, ""):
                            return f"常量: {mapping.constant_value}"

                    # 3. 如果有计算结果但没有公式，显示结果
                    if preview_text:
                        return preview_text

                    # 4. 如果没有映射也没有结果，显示Excel原始值
                    if hasattr(item, "columns") and column_meta["key"] in item.columns:
                        entry = item.columns[column_meta["key"]]
                        if entry.source_value is not None:
                            return str(entry.source_value)

                    return ""

            if role == Qt.EditRole and column >= len(self.static_headers):
                column_meta = self._column_meta_at(column)
                if not column_meta or not self.workbook_manager:
                    return ""
                mapping = self.workbook_manager.get_mapping(item.id, column_meta["key"])
                return mapping.formula if mapping else ""

            # 搜索高亮：如果有搜索文本，检查单元格内容是否匹配
            if role == Qt.BackgroundRole and self.search_text:
                display_text = ""

                if column == 0:  # 状态列
                    display_text = self._resolve_target_status(item)
                elif column == 1:  # 级别列
                    display_text = (
                        item.hierarchical_number
                        if hasattr(item, "hierarchical_number")
                        else "1"
                    )
                else:  # 动态列
                    column_meta = self._column_meta_at(column)
                    if column_meta and self.workbook_manager:
                        mapping = self.workbook_manager.get_mapping(
                            item.id, column_meta["key"]
                        )
                        result_map = self.workbook_manager.calculation_results.get(
                            item.id, {}
                        )
                        result = result_map.get(column_meta["key"])

                        # 获取显示文本用于匹配
                        if mapping and mapping.formula:
                            display_text = mapping.formula
                        elif result and result.success and result.result is not None:
                            display_text = str(result.result)
                        elif (
                            hasattr(item, "columns")
                            and column_meta["key"] in item.columns
                        ):
                            entry = item.columns[column_meta["key"]]
                            if entry.source_value is not None:
                                display_text = str(entry.source_value)

                # 如果匹配，返回高亮颜色
                if display_text and self.search_text in str(display_text).lower():
                    return QColor("#ffe0f0")  # 浅粉色高亮，匹配主题

        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if role != Qt.EditRole or not index.isValid() or not self.workbook_manager:
            return False

        item = index.internalPointer()
        if not isinstance(item, TargetItem):
            return False

        column_meta = self._column_meta_at(index.column())
        if not column_meta:
            return False

        new_formula = (value or "").strip()
        mapping = self.workbook_manager.ensure_mapping(
            item.id, column_meta["key"], column_meta["name"]
        )

        if not new_formula:
            mapping.update_formula(
                "", status=FormulaStatus.EMPTY, column_name=column_meta["name"]
            )
            mapping.calculation_result = None
            mapping.last_calculated = None
            mapping.validation_error = ""
            mapping.constant_value = None
            result_map = self.workbook_manager.calculation_results.get(item.id)
            if result_map and column_meta["key"] in result_map:
                del result_map[column_meta["key"]]
                if not result_map:
                    self.workbook_manager.calculation_results.pop(item.id, None)
        else:
            mapping.update_formula(
                new_formula,
                status=FormulaStatus.USER_MODIFIED,
                column_name=column_meta["name"],
            )
            mapping.validation_error = ""

        left_index = index.sibling(index.row(), 0)
        right_index = index.sibling(index.row(), self.columnCount() - 1)
        self.dataChanged.emit(left_index, right_index, [Qt.DisplayRole])
        self.formulaEdited.emit([item.id])
        return True

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            # 🔧 修复：对于使用多行表头的动态列，返回空字符串，让 MultiRowHeaderView 自己绘制
            # 只有在 row_count > 1 且该列在 layout 中时，才让 MultiRowHeaderView 绘制
            if (
                section >= len(self.static_headers)
                and self._header_row_count > 1
                and section in self._header_layout
            ):
                return ""  # 返回空字符串，让 MultiRowHeaderView 绘制多行表头
            return self.headers[section]
        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        # ✅ 从配置获取可编辑性
        column = index.column()
        column_name = self.headers[column] if column < len(self.headers) else ""

        # 如果有配置，使用配置；否则使用默认只读列表
        if self.editable_columns_set:
            if column_name in self.editable_columns_set:
                flags |= Qt.ItemIsEditable
        else:
            # 默认只读列列表
            readonly_columns = ["项目", "行次", "状态", "级别"]
            if column_name not in readonly_columns:
                flags |= Qt.ItemIsEditable

        return flags

    def get_target_item(self, index: QModelIndex) -> Optional[TargetItem]:
        """获取目标项"""
        if not index.isValid():
            return None

        item = index.internalPointer()
        if isinstance(item, TargetItem):
            return item
        return None

    def get_index_for_target(self, target_id: str, column: int = 0) -> QModelIndex:
        """根据目标项ID获取模型索引"""
        for row, target_item in enumerate(self.root_items):
            if target_item.id == target_id:
                return self.createIndex(row, column, target_item)
        return QModelIndex()

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

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
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

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ):
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
        # AI Integration - 新的对话式 AI 助手
        self.chat_controller = ChatController(self)
        self.calculation_engine = None

        self._source_lookup_index: Dict[Tuple[str, str], List[SourceItem]] = {}
        self._user_column_widths: Dict[int, int] = {}
        self._main_auto_resizing = False
        self._main_resize_retry_counts: Dict[str, int] = {}
        self._target_column_config: Optional[List[Dict[str, Any]]] = None
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.timeout.connect(self._perform_autosave)
        self._autosave_suspended = False
        self._active_formula_column: Optional[str] = None

        # 初始化 AI 服务（使用默认配置或从配置文件加载）
        self._initialize_ai_service()

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
        elif hasattr(sheet_item, "name"):
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

        # 设置窗口图标（关键！）
        icon_path = Path("icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # 全屏状态标志
        self._is_fullscreen = False
        self._saved_window_state = None
        self._saved_splitter_sizes = []

        # 创建中央部件
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")  # 设置对象名称以便样式表定位
        self.setCentralWidget(central_widget)
        self.menuBar().setVisible(False)

        # 创建中央布局
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.setContentsMargins(8, 8, 8, 8)  # 添加边距使面板不贴边
        central_widget_layout.setSpacing(8)  # 添加间距

        # 创建主分割器（水平）- 改为两列布局
        self.main_splitter = QSplitter(Qt.Horizontal)  # 保存引用用于全屏切换
        central_widget_layout.addWidget(self.main_splitter)

        # 中央工作台（左侧列）
        self.create_workbench_panel(self.main_splitter)

        # 右侧工具区（右侧列）
        self.create_tools_panel(self.main_splitter)

        # 底部日志区
        self.create_output_panel(central_widget_layout)

        # 设置分割器比例 - 两列布局，中间:右侧 = 2:1
        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([1066, 533])

        # 状态栏
        self.statusBar().showMessage("就绪")

        # 🎨 应用玻璃化主题(在log_manager创建后)
        self.apply_glass_theme()

        # ✨ 应用阴影效果（在所有控件创建完成后）
        self.apply_shadow_effects()

    def apply_glass_theme(self):
        """应用玻璃质感主题样式"""
        # 主窗口整体样式 - 半透明渐变背景
        self.setStyleSheet(
            """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 245, 250, 0.85),
                    stop:0.5 rgba(254, 242, 248, 0.8),
                    stop:1 rgba(252, 238, 245, 0.75));
            }

            /* 中央部件背景透明 */
            QWidget#centralWidget {
                background: transparent;
            }

            /* 分割器样式 - 半透明手柄 */
            QSplitter::handle {
                background: rgba(230, 190, 205, 0.4);
                border-radius: 3px;
            }

            QSplitter::handle:hover {
                background: rgba(215, 130, 165, 0.5);
            }

            QSplitter::handle:horizontal {
                width: 8px;
                margin: 0 3px;
            }

            QSplitter::handle:vertical {
                height: 8px;
                margin: 3px 0;
            }

            /* QGroupBox - 玻璃质感 */
            QGroupBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 252, 254, 0.8),
                    stop:0.5 rgba(255, 250, 253, 0.75),
                    stop:1 rgba(254, 248, 252, 0.7));
                border: 1px solid rgba(240, 215, 228, 0.7);
                border-radius: 14px;
                margin-top: 20px;
                padding-top: 18px;
                font-weight: 500;
                font-size: 14pt;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 18px;
                top: 2px;
                padding: 6px 16px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(215, 120, 165, 0.92),
                    stop:1 rgba(235, 145, 190, 0.88));
                color: white;
                border-radius: 10px;
                font-weight: 700;
                font-size: 14pt !important;
            }

            /* 树形视图 - 玻璃效果（增强版） */
            QTreeView {
                background: rgba(255, 252, 254, 0.65);
                border: 1px solid rgba(230, 200, 215, 0.5);
                border-radius: 10px;
                selection-background-color: rgba(235, 145, 190, 0.35);
                outline: none;
                padding: 4px;
                font-size: 10pt;
            }

            QTreeView::item {
                padding: 8px 10px;
                border-radius: 5px;
                border-right: 1px solid rgba(230, 200, 215, 0.28);
                min-height: 28px;
            }

            QTreeView::item:hover {
                background: rgba(235, 145, 190, 0.18);
            }

            QTreeView::item:selected {
                background: rgba(235, 145, 190, 0.3);
                color: #1a1a1a;
            }

            QTreeView::branch {
                background: transparent;
            }

            /* 表格视图 - 玻璃效果（增强版） */
            QTableView, QTableWidget {
                background: rgba(255, 252, 254, 0.65);
                border: 1px solid rgba(230, 200, 215, 0.5);
                border-radius: 10px;
                gridline-color: rgba(230, 200, 215, 0.35);
                font-size: 10pt;
            }

            QTableView::item, QTableWidget::item {
                padding: 4px 8px;
                border-right: 1px solid rgba(230, 200, 215, 0.28);
                border-bottom: 1px solid rgba(230, 200, 215, 0.18);
                min-height: 22px;
            }

            QTableView::item:hover, QTableWidget::item:hover {
                background: rgba(235, 145, 190, 0.12);
            }

            QTableView::item:selected, QTableWidget::item:selected {
                background: rgba(235, 145, 190, 0.25);
                color: #1a1a1a;
            }

            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 250, 253, 0.92),
                    stop:1 rgba(254, 245, 251, 0.88));
                border: none;
                border-right: 1px solid rgba(230, 200, 215, 0.35);
                border-bottom: 1px solid rgba(230, 200, 215, 0.45);
                padding: 4px 10px;
                font-weight: 600;
                font-size: 12pt;
                color: #5a3a47;
                min-height: 0px;
            }

            QHeaderView::section:hover {
                background: rgba(235, 145, 190, 0.2);
            }

            /* 选项卡样式 */
            QTabWidget::pane {
                background: rgba(255, 252, 254, 0.65);
                border: 1px solid rgba(230, 200, 215, 0.5);
                border-radius: 10px;
                border-top-left-radius: 0;
            }

            QTabWidget::tab-bar {
                left: 10px;
            }

            QTabBar::tab {
                background: rgba(248, 235, 243, 0.75);
                border: 1px solid rgba(230, 200, 215, 0.4);
                border-bottom: none;
                padding: 9px 18px;
                margin-right: 5px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: #8b6c7d;
                font-weight: 500;
                font-size: 12pt;
            }

            QTabBar::tab:selected {
                background: rgba(255, 252, 254, 0.88);
                color: #5a3a47;
                font-weight: 600;
                border-color: rgba(215, 130, 165, 0.5);
            }

            QTabBar::tab:hover:!selected {
                background: rgba(235, 145, 190, 0.15);
            }

            /* 文本编辑器样式 */
            QTextEdit, QPlainTextEdit {
                background: rgba(255, 252, 254, 0.75);
                border: 1px solid rgba(230, 200, 215, 0.5);
                border-radius: 8px;
                padding: 8px;
                selection-background-color: rgba(235, 145, 190, 0.35);
                color: #5a3a47;
            }

            QTextEdit:focus, QPlainTextEdit:focus {
                border: 2px solid rgba(215, 130, 165, 0.7);
            }

            QLineEdit {
                background: rgba(255, 252, 254, 0.82);
                border: 1px solid rgba(230, 200, 215, 0.5);
                border-radius: 8px;
                padding: 7px 12px;
                selection-background-color: rgba(235, 145, 190, 0.35);
                color: #5a3a47;
            }

            QLineEdit:focus {
                border: 2px solid rgba(215, 130, 165, 0.7);
                background: rgba(255, 252, 254, 0.92);
            }

            QComboBox {
                background: rgba(255, 252, 254, 0.82);
                border: 1px solid rgba(230, 200, 215, 0.5);
                border-radius: 8px;
                padding: 7px 12px;
                color: #5a3a47;
                font-size: 12pt;
            }

            QComboBox:focus, QComboBox:hover {
                border: 1px solid rgba(215, 130, 165, 0.6);
                background: rgba(255, 252, 254, 0.9);
            }

            QComboBox::drop-down {
                border: none;
                width: 30px;
                background: rgba(235, 145, 190, 0.12);
                border-top-right-radius: 7px;
                border-bottom-right-radius: 7px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #8b6c7d;
                width: 0;
                height: 0;
                margin-right: 8px;
            }

            QComboBox::down-arrow:hover {
                border-top-color: #d778a5;
            }

            QComboBox QAbstractItemView {
                background: rgba(255, 252, 254, 0.95);
                border: 1px solid rgba(230, 200, 215, 0.6);
                border-radius: 6px;
                selection-background-color: rgba(235, 145, 190, 0.3);
                font-size: 12pt;
            }

            /* 按钮样式 - 玻璃质感 */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 252, 254, 0.92),
                    stop:1 rgba(252, 245, 250, 0.88));
                border: 1px solid rgba(230, 200, 215, 0.6);
                border-radius: 8px;
                padding: 7px 18px;
                color: #5a3a47;
                font-weight: 600;
                font-size: 12pt;
            }

            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(235, 145, 190, 0.25),
                    stop:1 rgba(235, 145, 190, 0.18));
                border: 1px solid rgba(215, 130, 165, 0.5);
            }

            QPushButton:pressed {
                background: rgba(235, 145, 190, 0.32);
                border: 1px solid rgba(215, 130, 165, 0.6);
            }

            QPushButton:disabled {
                background: rgba(248, 235, 243, 0.55);
                color: rgba(140, 140, 140, 0.75);
                border: 1px solid rgba(230, 200, 215, 0.35);
            }

            /* 滚动条样式 - 半透明（扩大尺寸） */
            QScrollBar:vertical {
                background: rgba(248, 235, 243, 0.35);
                width: 22px;
                border-radius: 8px;
                margin: 6px;
            }

            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(190, 140, 165, 0.6),
                    stop:1 rgba(215, 130, 165, 0.55));
                border-radius: 7px;
                min-height: 40px;
            }

            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(215, 130, 165, 0.7),
                    stop:1 rgba(235, 145, 190, 0.65));
            }

            QScrollBar:horizontal {
                background: rgba(248, 235, 243, 0.35);
                height: 22px;
                border-radius: 8px;
                margin: 6px;
            }

            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(190, 140, 165, 0.6),
                    stop:1 rgba(215, 130, 165, 0.55));
                border-radius: 7px;
                min-width: 40px;
            }

            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(215, 130, 165, 0.7),
                    stop:1 rgba(235, 145, 190, 0.65));
            }

            QScrollBar::add-line, QScrollBar::sub-line {
                background: none;
                border: none;
            }

            /* 状态栏样式 */
            QStatusBar {
                background: rgba(248, 235, 243, 0.75);
                border-top: 1px solid rgba(230, 200, 215, 0.4);
                padding: 5px;
                color: #8b6c7d;
            }

            /* 工具提示样式 */
            QToolTip {
                background: rgba(255, 252, 254, 0.96);
                border: 1px solid rgba(215, 130, 165, 0.5);
                border-radius: 8px;
                padding: 7px;
                color: #5a3a47;
            }

            /* 菜单样式 */
            QMenu {
                background: rgba(255, 252, 254, 0.96);
                border: 1px solid rgba(230, 200, 215, 0.5);
                border-radius: 10px;
                padding: 5px;
            }

            QMenu::item {
                padding: 7px 24px 7px 18px;
                border-radius: 5px;
            }

            QMenu::item:selected {
                background: rgba(235, 145, 190, 0.25);
            }

            QMenu::separator {
                height: 1px;
                background: rgba(230, 200, 215, 0.35);
                margin: 5px 10px;
            }

            /* 复选框和单选框样式 */
            QCheckBox::indicator, QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid rgba(230, 200, 215, 0.6);
                background: rgba(255, 252, 254, 0.85);
            }

            QRadioButton::indicator {
                border-radius: 9px;
            }

            QCheckBox::indicator:checked, QRadioButton::indicator:checked {
                background: rgba(215, 130, 165, 0.85);
                border: 1px solid rgba(215, 130, 165, 0.7);
            }

            /* 进度条样式 */
            QProgressBar {
                background: rgba(248, 235, 243, 0.6);
                border: 1px solid rgba(230, 200, 215, 0.4);
                border-radius: 8px;
                text-align: center;
                color: #5a3a47;
                font-weight: 600;
            }

            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(215, 130, 165, 0.75),
                    stop:1 rgba(235, 145, 190, 0.85));
                border-radius: 7px;
            }

            /* 对话框样式 - 统一玻璃质感 */
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 248, 252, 0.92),
                    stop:0.5 rgba(254, 242, 248, 0.88),
                    stop:1 rgba(252, 238, 245, 0.85));
                border: 1px solid rgba(230, 200, 215, 0.6);
                border-radius: 12px;
            }

            QDialog QLabel {
                color: #5a3a47;
            }

            QDialog QLabel[heading="true"] {
                font-size: 10pt;
                font-weight: 700;
                color: #8b4f6f;
            }
        """
        )

        # 玻璃化主题应用完成（不输出日志，避免技术细节干扰用户）

    def apply_shadow_effects(self):
        """为关键面板添加阴影效果"""
        from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGroupBox
        from PySide6.QtGui import QColor

        # 为所有QGroupBox添加阴影
        for groupbox in self.findChildren(QGroupBox):
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(18)
            shadow.setColor(QColor(0, 0, 0, 40))  # 16%透明度的黑色
            shadow.setOffset(0, 4)
            groupbox.setGraphicsEffect(shadow)

        # 阴影效果应用完成（不输出日志）

    def create_navigator_panel(self, parent_splitter):
        """创建左侧导航面板"""
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)

        # 分类摘要区域
        summary_group = QGroupBox("📋 分类摘要")
        summary_layout = QVBoxLayout(summary_group)

        self.classification_summary = QTextEdit()
        # 移除高度限制，让控件自动填满空间
        self.classification_summary.setReadOnly(True)
        # 移除灰色背景，使用简洁样式
        self.classification_summary.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
                font-size: 16px;
            }
        """
        )
        self.classification_summary.setText("请先加载Excel文件并确认工作表分类")
        summary_layout.addWidget(self.classification_summary)

        nav_layout.addWidget(summary_group)

        # 目标项结构树
        target_group = QGroupBox("🎯 目标项来源详情")
        target_layout = QVBoxLayout(target_group)

        self.target_source_description = QLabel(
            "请选择中间主表中的目标项，即可在此查看来源明细。"
        )
        self.target_source_description.setWordWrap(True)
        self.target_source_description.setStyleSheet("color: #555; font-size: 12px;")
        self._target_source_description_default = self.target_source_description.text()
        target_layout.addWidget(self.target_source_description)

        self.target_source_stack = QStackedWidget()

        # 消息页
        message_widget = QWidget()
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(8, 8, 8, 8)
        self.target_source_message = QLabel("尚未选中任何目标项。")
        self.target_source_message.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.target_source_message.setWordWrap(True)
        self.target_source_message.setStyleSheet("color: #666;")
        message_layout.addWidget(self.target_source_message)
        message_layout.addStretch()
        self._target_source_message_index = self.target_source_stack.addWidget(
            message_widget
        )

        # 表格页
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        self.target_source_table = QTableWidget()
        self.target_source_table.setColumnCount(0)
        self.target_source_table.setRowCount(0)
        self.target_source_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.target_source_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.target_source_table.setFocusPolicy(Qt.NoFocus)

        # 🔧 修复：设置按像素滚动而非按项目滚动
        self.target_source_table.setHorizontalScrollMode(
            QAbstractItemView.ScrollPerPixel
        )
        self.target_source_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        header = self.target_source_table.horizontalHeader()
        ensure_interactive_header(header, stretch_last=True)
        header.setSectionResizeMode(QHeaderView.Interactive)

        # ⭐ 垂直表头：允许用户拖动修改行高，默认30px
        v_header = self.target_source_table.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.Interactive)  # 允许拖动
        v_header.setDefaultSectionSize(30)  # 默认行高30px
        v_header.setMinimumSectionSize(20)  # 最小行高20px

        ensure_word_wrap(
            self.target_source_table, track_header=False
        )  # 禁用自动行高调整
        # 应用统一的网格线样式
        self.target_source_table.setStyleSheet(TABLE_GRID_STYLE)
        self.target_source_table.setShowGrid(True)  # 确保显示网格线
        table_layout.addWidget(self.target_source_table)
        self._target_source_table_index = self.target_source_stack.addWidget(
            table_container
        )

        target_layout.addWidget(self.target_source_stack)

        nav_layout.addWidget(target_group)

        # 设置布局拉伸因子，让控件合理分配空间
        nav_layout.setStretchFactor(summary_group, 1)  # 分类摘要占1/3空间
        nav_layout.setStretchFactor(target_group, 2)  # 目标项结构占2/3空间

        parent_splitter.addWidget(nav_widget)

    def create_workbench_panel(self, parent_splitter):
        """创建中央工作台面板"""
        # 创建垂直分割器，上方是主操作表格，下方是目标项来源详情
        vertical_splitter = QSplitter(Qt.Vertical)

        # ========== 上方：主操作区域 ==========
        workbench_widget = QWidget()
        workbench_layout = QVBoxLayout(workbench_widget)

        # 第一行工具栏：主要功能按钮
        tools_layout = QHBoxLayout()
        self.load_files_btn = QPushButton("📁 加载单个Excel")
        self.load_multiple_files_btn = QPushButton("📂 加载多个Excel")
        self.ai_assistant_btn = QPushButton("💬 AI分析助手")
        self.import_formula_btn = QPushButton("📥 导入公式")
        self.save_formula_btn = QPushButton("💾 另存公式")
        self.export_btn = QPushButton("💾 导出Excel")

        # 设置按钮样式 - 继承全局玻璃化样式
        for btn in [
            self.load_files_btn,
            self.load_multiple_files_btn,
            self.ai_assistant_btn,
            self.import_formula_btn,
            self.save_formula_btn,
            self.export_btn,
        ]:
            btn.setMinimumHeight(35)

        # 设置工具提示
        self.load_files_btn.setToolTip("加载单个Excel工作簿")
        self.load_multiple_files_btn.setToolTip("一次加载多个Excel文件，所有sheet合并处理后导出")
        self.save_formula_btn.setToolTip("将当前工作表的公式映射导出为 JSON 文件。")
        self.import_formula_btn.setToolTip("从 JSON 文件导入映射公式并应用到当前工作表。")

        # 第一行按钮布局
        tools_layout.addWidget(self.load_files_btn)
        tools_layout.addWidget(self.load_multiple_files_btn)
        tools_layout.addWidget(self.ai_assistant_btn)
        tools_layout.addWidget(self.import_formula_btn)
        tools_layout.addWidget(self.save_formula_btn)
        tools_layout.addWidget(self.export_btn)
        tools_layout.addStretch()

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        tools_layout.addWidget(self.progress_bar)

        workbench_layout.addLayout(tools_layout)

        # 主数据表工具栏
        table_toolbar_layout = QVBoxLayout()

        # 第二行：工作表选择 + 操作按钮
        sheet_select_layout = QHBoxLayout()
        target_sheet_label = QLabel("选择工作表:")
        target_sheet_label.setStyleSheet("font-size: 12pt;")
        self.target_sheet_combo = QComboBox()
        self.target_sheet_combo.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        self.target_sheet_combo.setMinimumWidth(200)
        self.target_sheet_combo.setMinimumHeight(35)  # 设置下拉框最小高度为35px
        self.target_sheet_combo.currentTextChanged.connect(self.on_target_sheet_changed)
        sheet_select_layout.addWidget(target_sheet_label)
        sheet_select_layout.addWidget(self.target_sheet_combo)

        # 全屏显示按钮
        self.fullscreen_btn = QPushButton("🖥️ 全屏显示")
        self.fullscreen_btn.setMinimumHeight(35)  # 统一按钮高度为35px
        self.fullscreen_btn.setCheckable(True)  # 设置为可切换按钮
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_btn.setToolTip("全屏显示主表格和来源详情（隐藏其他面板）")
        self.fullscreen_btn.setStyleSheet(
            """
            QPushButton {
                padding: 5px 15px;
                border-radius: 5px;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            """
        )
        sheet_select_layout.addWidget(self.fullscreen_btn)

        # 清除当前表公式按钮
        self.clear_sheet_formulas_btn = QPushButton("🗑️ 清除当前表公式")
        self.clear_sheet_formulas_btn.setMinimumHeight(35)
        self.clear_sheet_formulas_btn.setToolTip("清除当前工作表的所有公式映射")
        sheet_select_layout.addWidget(self.clear_sheet_formulas_btn)

        # 清除所有表公式按钮
        self.clear_all_formulas_btn = QPushButton("🗑️ 清除所有表公式")
        self.clear_all_formulas_btn.setMinimumHeight(35)
        self.clear_all_formulas_btn.setToolTip("清除所有工作表的公式映射")
        sheet_select_layout.addWidget(self.clear_all_formulas_btn)

        sheet_select_layout.addStretch()
        table_toolbar_layout.addLayout(sheet_select_layout)

        # 第三行：搜索框和展示列按钮（4:1布局）
        search_layout = QHBoxLayout()
        self.target_search_line = QLineEdit()
        self.target_search_line.setPlaceholderText("搜索待写入项...")
        self.target_search_line.setMinimumHeight(35)  # 设置搜索框最小高度为35px
        self.target_search_line.textChanged.connect(self.filter_target_items)
        self.target_column_config_btn = QPushButton("⚙️ 数据列设置")
        self.target_column_config_btn.setToolTip(
            "配置数据列的显示顺序、可见性和可编辑性"
        )
        self.target_column_config_btn.setMinimumHeight(35)  # 按钮也设置相同高度
        self.target_column_config_btn.setEnabled(False)
        self.target_column_config_btn.clicked.connect(self.open_target_column_config)

        # 搜索框和按钮按4:1比例分配
        search_layout.addWidget(self.target_search_line, 4)
        search_layout.addWidget(self.target_column_config_btn, 1)
        table_toolbar_layout.addLayout(search_layout)

        workbench_layout.addLayout(table_toolbar_layout)

        # 主数据网格
        self.main_data_grid = DragDropTreeView()
        self.main_data_grid._is_main_grid = True  # 标记为主数据网格
        self.main_data_grid.setAlternatingRowColors(True)
        self.main_data_grid.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.main_data_grid.setRootIsDecorated(False)
        self.main_data_grid.setAcceptDrops(True)

        # ⭐ 启用自动行高适应（QTreeView不支持verticalHeader，使用setUniformRowHeights）
        self.main_data_grid.setWordWrap(True)  # 允许单元格内换行
        self.main_data_grid.setUniformRowHeights(
            False
        )  # 允许不同行有不同高度（QTreeView专用）

        # 🔧 设置搜索高亮delegate，覆盖CSS样式
        self.search_highlight_delegate = SearchHighlightDelegate(self.main_data_grid)
        self.main_data_grid.setItemDelegate(self.search_highlight_delegate)

        # 设置右键菜单
        self.main_data_grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.main_data_grid.customContextMenuRequested.connect(self.show_context_menu)

        # 设置网格样式 - 移除灰色背景
        self.main_data_grid.setStyleSheet(
            """
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
        """
        )

        workbench_layout.addWidget(self.main_data_grid)

        # 添加主操作区域到垂直分割器
        vertical_splitter.addWidget(workbench_widget)

        # ========== 下方：目标项来源详情（转置显示） ==========
        target_detail_group = QGroupBox("🎯 目标项来源详情")
        target_detail_layout = QVBoxLayout(target_detail_group)

        self.target_source_description = QLabel(
            "请选择上方主表中的目标项，即可在此查看来源明细。"
        )
        self.target_source_description.setWordWrap(True)
        self.target_source_description.setStyleSheet("color: #555; font-size: 12px;")
        self._target_source_description_default = self.target_source_description.text()
        target_detail_layout.addWidget(self.target_source_description)

        self.target_source_stack = QStackedWidget()

        # 消息页
        message_widget = QWidget()
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(8, 8, 8, 8)
        self.target_source_message = QLabel("尚未选中任何目标项。")
        self.target_source_message.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.target_source_message.setWordWrap(True)
        self.target_source_message.setStyleSheet("color: #666;")
        message_layout.addWidget(self.target_source_message)
        message_layout.addStretch()
        self._target_source_message_index = self.target_source_stack.addWidget(
            message_widget
        )

        # 表格页（转置显示：列头为属性，行为不同来源）
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        self.target_source_table = AutoResizeTableWidget()
        # 设置列宽约束
        self.target_source_table.set_column_constraints(
            min_widths={i: 80 for i in range(10)},  # 所有列最小宽度80
            max_widths={i: 420 for i in range(10)},  # 所有列最大宽度420
        )
        self.target_source_table.setColumnCount(0)
        self.target_source_table.setRowCount(0)
        self.target_source_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.target_source_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.target_source_table.setFocusPolicy(Qt.NoFocus)

        # 🔧 修复：设置按像素滚动而非按项目滚动
        self.target_source_table.setHorizontalScrollMode(
            QAbstractItemView.ScrollPerPixel
        )
        self.target_source_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        header = self.target_source_table.horizontalHeader()
        ensure_interactive_header(header, stretch_last=True)
        header.setSectionResizeMode(QHeaderView.Interactive)

        # ⭐ 垂直表头：允许用户拖动修改行高，默认50px
        v_header = self.target_source_table.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.Interactive)  # 允许拖动
        v_header.setDefaultSectionSize(50)  # 默认行高50px（已修正）
        v_header.setMinimumSectionSize(40)  # 最小行高40px

        ensure_word_wrap(
            self.target_source_table, track_header=False
        )  # 禁用自动行高调整
        # 应用统一的网格线样式
        self.target_source_table.setStyleSheet(TABLE_GRID_STYLE)
        self.target_source_table.setShowGrid(True)  # 确保显示网格线

        table_layout.addWidget(self.target_source_table)
        self._target_source_table_index = self.target_source_stack.addWidget(
            table_container
        )

        target_detail_layout.addWidget(self.target_source_stack)

        # 添加目标项详情到垂直分割器
        vertical_splitter.addWidget(target_detail_group)

        # 设置垂直分割器比例（上方主表占大部分空间）
        vertical_splitter.setStretchFactor(0, 3)
        vertical_splitter.setStretchFactor(1, 1)
        vertical_splitter.setSizes([600, 200])

        # 添加垂直分割器到父分割器
        parent_splitter.addWidget(vertical_splitter)

    def _ensure_target_column_config(self):
        if not hasattr(self, "target_model") or not self.target_model:
            return

        # 定义默认只读列
        readonly_columns = ["项目", "行次", "状态", "级别"]

        # ✅ 优先从workbook_manager加载保存的配置
        if (
            not self._target_column_config
            and self.workbook_manager
            and self.target_model.active_sheet_name
            and self.target_model.active_sheet_name
            in self.workbook_manager.column_configs
        ):

            self._target_column_config = self.workbook_manager.column_configs[
                self.target_model.active_sheet_name
            ]
            # 确保所有配置项都有editable字段
            for config in self._target_column_config:
                if "editable" not in config:
                    config["editable"] = config["name"] not in readonly_columns
            return

        if not self._target_column_config:
            self._target_column_config = [
                {
                    "name": header,
                    "enabled": True,
                    "editable": header not in readonly_columns,  # 默认可编辑性
                }
                for header in getattr(self.target_model, "headers", [])
            ]
        else:
            # 向后兼容：为已有配置添加 editable 字段
            for config in self._target_column_config:
                if "editable" not in config:
                    config["editable"] = config["name"] not in readonly_columns

    def open_target_column_config(self):
        if not hasattr(self, "target_model") or not self.target_model:
            QMessageBox.information(self, "提示", "请先加载并提取数据。")
            return

        headers = list(getattr(self.target_model, "headers", []))
        if not headers:
            QMessageBox.information(self, "提示", "当前没有可配置的列。")
            return

        self._ensure_target_column_config()

        # ✅ 同步当前表格的真实状态到配置
        header_view = self.main_data_grid.header()
        name_to_index = {name: idx for idx, name in enumerate(headers)}

        for config in self._target_column_config:
            column_name = config.get("name")
            column_index = name_to_index.get(column_name)

            if column_index is not None:
                # 读取当前列的显示状态
                config["enabled"] = not header_view.isSectionHidden(column_index)

                # 读取当前列的可编辑状态
                if self.target_model.editable_columns_set:
                    config["editable"] = (
                        column_name in self.target_model.editable_columns_set
                    )
                else:
                    # 如果没有配置，使用默认只读列表
                    readonly_columns = ["项目", "行次", "状态", "级别"]
                    config["editable"] = column_name not in readonly_columns

        dialog = ColumnConfigDialog(headers, self._target_column_config, self)
        if dialog.exec() == QDialog.Accepted:
            self._target_column_config = dialog.get_selection()
            self.apply_target_column_config()

    def apply_target_column_config(self):
        if not hasattr(self, "target_model") or not self.target_model:
            return

        headers = list(getattr(self.target_model, "headers", []))
        if not headers:
            return

        self._ensure_target_column_config()

        header_view = self.main_data_grid.header()
        name_to_index = {name: idx for idx, name in enumerate(headers)}

        ordered_entries: List[Dict[str, Any]] = []
        seen = set()
        for entry in self._target_column_config or []:
            name = entry.get("name")
            if name in name_to_index and name not in seen:
                ordered_entries.append(entry)
                seen.add(name)

        for name in headers:
            if name not in seen:
                ordered_entries.append({"name": name, "enabled": True})

        for target_pos, entry in enumerate(ordered_entries):
            name = entry.get("name")
            enabled = entry.get("enabled", True)
            column_index = name_to_index.get(name)
            if column_index is None:
                continue

            current_visual = header_view.visualIndex(column_index)
            if current_visual != target_pos:
                header_view.moveSection(current_visual, target_pos)

            header_view.setSectionHidden(column_index, not enabled)

        # ✅ 更新模型的可编辑列配置
        self.target_model.set_editable_columns(self._target_column_config)

        # ✅ 保存列配置到workbook_manager以便持久化
        if self.workbook_manager and self.target_model.active_sheet_name:
            self.workbook_manager.column_configs[
                self.target_model.active_sheet_name
            ] = self._target_column_config

        self._apply_main_header_layout()
        self._sync_analysis_context()

    def _sync_analysis_context(self):
        """同步分析TAB所需的列状态与工作簿信息。"""
        if not hasattr(self, "chat_controller") or not self.chat_controller:
            return

        if not self.workbook_manager:
            self.chat_controller.update_analysis_context(None)
            return

        self._ensure_target_column_config()
        current_sheet = getattr(self.target_model, "active_sheet_name", None)
        target_config = self._target_column_config or []
        source_configs = getattr(self.source_tree, "sheet_column_configs", {}) or {}

        self.chat_controller.update_analysis_context(
            self.workbook_manager,
            current_sheet=current_sheet,
            target_column_config=target_config,
            source_column_configs=source_configs,
        )

    def _on_source_tree_column_config_changed(self, sheet_name: str):
        """来源项列配置发生变化时刷新分析上下文。"""
        self._sync_analysis_context()

    def apply_analysis_formulas(self, sheet_name: str, entries: List[Dict[str, str]]) -> Tuple[int, int]:
        """将 AI 返回的映射公式应用到当前工作簿。"""
        if not self.workbook_manager:
            return 0, len(entries)

        sheet_targets = [
            item
            for item in self.workbook_manager.target_items.values()
            if item.sheet_name == sheet_name
        ]
        name_map: Dict[str, List[TargetItem]] = {}
        for item in sheet_targets:
            name_map.setdefault(item.name, []).append(item)

        applied = 0
        updated_ids: List[str] = []

        for entry in entries:
            target_candidates = name_map.get(entry["target_name"], [])
            if not target_candidates:
                self.log_manager.warning(f"未找到目标项: {entry['target_name']}")
                continue

            target_item = target_candidates[0]
            column_key = entry["column_key"]
            column_display = entry["column_display"]
            formula_text = entry["formula"]

            mapping = self.workbook_manager.ensure_mapping(
                target_item.id, column_key, column_display
            )
            mapping.update_formula(
                formula_text,
                status=FormulaStatus.AI_GENERATED,
                column_name=column_display,
            )
            mapping.constant_value = None
            mapping.validation_error = ""
            if "confidence" in entry and entry["confidence"] is not None:
                try:
                    confidence_value = float(entry["confidence"])
                    mapping.ai_confidence = max(0.0, min(1.0, confidence_value))
                except (TypeError, ValueError):
                    mapping.ai_confidence = 0.0
            if entry.get("reasoning"):
                mapping.ai_reasoning = str(entry["reasoning"])
            applied += 1
            updated_ids.append(target_item.id)

        if applied:
            self.handle_formula_updates(updated_ids, reason="ai_analysis")
            self.log_manager.info(f"🤖 已应用 {applied}/{len(entries)} 条AI映射公式")

        return applied, len(entries)

    def _collect_formula_entries_for_sheet(self, sheet_name: str) -> List[Dict[str, Any]]:
        """收集指定工作表的映射公式，供导出使用。"""
        if not self.workbook_manager:
            return []

        entries: List[Dict[str, Any]] = []
        for target in self.workbook_manager.target_items.values():
            if target.sheet_name != sheet_name:
                continue
            for mapping in self.workbook_manager.iter_mappings(target.id):
                if not mapping.formula:
                    continue
                column_display = mapping.column_name or mapping.column_key or "__default__"
                entries.append(
                    {
                        "target_name": target.name,
                        "column_display": column_display,
                        "column_key": mapping.column_key or "__default__",
                        "formula": mapping.formula,
                        "confidence": mapping.ai_confidence,
                        "reasoning": mapping.ai_reasoning,
                    }
                )
        return entries

    def save_formula_snapshot_via_dialog(self) -> None:
        """通过文件对话框导出当前工作表的公式映射。"""
        sheet_name = getattr(self.target_model, "active_sheet_name", None)
        if not sheet_name:
            QMessageBox.information(self, "提示", "请先选择需要保存公式的目标表。")
            return

        entries = self._collect_formula_entries_for_sheet(sheet_name)
        if not entries:
            QMessageBox.information(self, "提示", "当前工作表没有可保存的公式映射。")
            return

        safe_sheet = self.file_manager.sanitize_filename(sheet_name)
        default_dir = self.file_manager.formula_dir
        default_dir.mkdir(parents=True, exist_ok=True)
        default_path = default_dir / f"{safe_sheet}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存公式映射",
            str(default_path),
            "JSON 文件 (*.json)",
        )
        if not file_path:
            return

        metadata = {
            "source": "manual_export",
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        }

        saved_path = self.file_manager.export_formula_snapshot(
            sheet_name=sheet_name,
            entries=entries,
            destination=Path(file_path),
            metadata=metadata,
        )

        if saved_path:
            self.log_manager.info(f"📤 公式映射已保存至 {saved_path}")
            QMessageBox.information(self, "保存成功", f"公式映射已保存到:\n{saved_path}")
        else:
            QMessageBox.warning(self, "保存失败", "无法保存公式映射，请检查日志获取详细信息。")

    def import_formula_snapshot_via_dialog(self) -> None:
        """通过文件对话框导入公式映射 JSON。"""
        sheet_name = getattr(self.target_model, "active_sheet_name", None)
        if not sheet_name:
            QMessageBox.information(self, "提示", "请先选择要导入公式的目标表。")
            return

        default_dir = self.file_manager.formula_dir
        default_dir.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入公式映射",
            str(default_dir),
            "JSON 文件 (*.json)",
        )
        if not file_path:
            return

        try:
            snapshot = self.file_manager.import_formula_snapshot(
                sheet_name=sheet_name,
                file_path=Path(file_path),
            )
        except (ValueError, FileNotFoundError) as exc:
            QMessageBox.warning(self, "导入失败", str(exc))
            self.log_manager.warning(f"导入公式映射失败: {exc}")
            return

        applied, total = self.apply_analysis_formulas(sheet_name, snapshot.get("entries", []))
        if applied:
            QMessageBox.information(
                self,
                "导入成功",
                f"已导入 {applied}/{total} 条公式映射。",
            )
            self.log_manager.info(f"📥 从 {file_path} 导入 {applied}/{total} 条公式。")
        else:
            QMessageBox.warning(
                self,
                "导入提示",
                "未能应用导入的公式，请确认文件内容与当前工作表匹配。",
            )

        # 将最新状态写回默认目录，便于后续复用
        updated_entries = self._collect_formula_entries_for_sheet(sheet_name)
        metadata = {
            "source": "manual_import",
            "imported_from": str(file_path),
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        self.file_manager.export_formula_snapshot(
            sheet_name=sheet_name,
            entries=updated_entries,
            metadata=metadata,
        )

    def schedule_autosave(self, delay_ms: int = 800):
        """调度自动保存映射公式"""
        if self._autosave_suspended or not self.workbook_manager:
            return

        if self._autosave_timer.isActive():
            self._autosave_timer.stop()

        self._autosave_timer.start(max(100, delay_ms))

    def _perform_autosave(self):
        """执行映射公式自动保存"""
        if not self.workbook_manager or not self.file_manager:
            return

        success = self.file_manager.save_mapping_formulas(self.workbook_manager)
        if success:
            self.log_manager.info("📝 映射公式已自动保存")
        else:
            self.log_manager.warning("⚠️ 自动保存映射公式失败")

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
        self.source_tree.columnConfigChanged.connect(self._on_source_tree_column_config_changed)

        # 🔧 修复：为来源项库应用SearchHighlightDelegate，确保搜索高亮可见
        self.source_highlight_delegate = SearchHighlightDelegate(self.source_tree)
        self.source_tree.setItemDelegate(self.source_highlight_delegate)

        # 使用SearchableSourceTree内置的搜索组件（包含下拉菜单）
        source_search_widget = self.source_tree.get_search_widget()
        source_layout.addWidget(source_search_widget)

        # 添加树控件本身到布局
        source_layout.addWidget(self.source_tree)

        tools_widget.addTab(source_library_widget, "📚 来源项库")

        # 选项卡二：分析（新增）
        from components.main_analysis_panel import MainAnalysisPanel
        self.main_analysis_panel = MainAnalysisPanel()
        tools_widget.addTab(self.main_analysis_panel, "📊 分析")

        # 选项卡三：分类摘要
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)

        self.classification_summary = QTextEdit()
        self.classification_summary.setReadOnly(True)
        self.classification_summary.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
                font-size: 16px;
            }
        """
        )
        self.classification_summary.setText("请先加载Excel文件并确认工作表分类")
        summary_layout.addWidget(self.classification_summary)

        tools_widget.addTab(summary_widget, "📋 分类摘要")

        # 选项卡四：单元格检查 - 已删除
        # 该TAB的功能已整合到其他地方，不再需要单独的面板

        parent_splitter.addWidget(tools_widget)

    def create_output_panel(self, parent_layout):
        """创建底部输出面板 - 双日志区域"""
        # 创建日志区域容器
        self.log_container = QWidget()  # 保存引用用于全屏切换
        self.log_container.setMaximumHeight(180)  # 限制整个日志区域高度
        container_layout = QHBoxLayout(self.log_container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(10)

        # ========== 左侧：操作日志 ==========
        operation_widget = QWidget()
        operation_layout = QVBoxLayout(operation_widget)
        operation_layout.setContentsMargins(0, 0, 0, 0)
        operation_layout.setSpacing(2)

        # 操作日志标题
        operation_label = QLabel("👤 操作日志")
        operation_label.setStyleSheet(
            """
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2563EB;
                padding: 2px 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: #EFF6FF;
            }
        """
        )
        operation_label.setFixedHeight(25)
        operation_layout.addWidget(operation_label)

        # 操作日志文本框
        self.operation_log_text = QPlainTextEdit()
        self.operation_log_text.setMaximumHeight(145)
        self.operation_log_text.setReadOnly(True)
        self.operation_log_text.setStyleSheet(
            """
            QPlainTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
                background-color: #FAFAFA;
            }
        """
        )
        operation_layout.addWidget(self.operation_log_text)

        container_layout.addWidget(operation_widget, stretch=1)

        # ========== 右侧：系统日志 ==========
        system_widget = QWidget()
        system_layout = QVBoxLayout(system_widget)
        system_layout.setContentsMargins(0, 0, 0, 0)
        system_layout.setSpacing(2)

        # 系统日志标题
        system_label = QLabel("⚙️ 系统日志")
        system_label.setStyleSheet(
            """
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #059669;
                padding: 2px 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: #F0FDF4;
            }
        """
        )
        system_label.setFixedHeight(25)
        system_layout.addWidget(system_label)

        # 系统日志文本框
        self.system_log_text = QPlainTextEdit()
        self.system_log_text.setMaximumHeight(145)
        self.system_log_text.setReadOnly(True)
        self.system_log_text.setStyleSheet(
            """
            QPlainTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
                background-color: #FAFAFA;
            }
        """
        )
        system_layout.addWidget(self.system_log_text)

        container_layout.addWidget(system_widget, stretch=1)

        # 创建日志管理器（双区域）
        self.log_manager = LogManager(self.operation_log_text, self.system_log_text)

        # 向后兼容：保留output_text引用
        self.output_text = self.operation_log_text

        # 添加到主布局
        parent_layout.addWidget(self.log_container)

    def create_menus(self):
        """旧的菜单创建方法 - 已弃用"""
        pass

    def create_toolbar(self):
        """旧的工具栏创建方法 - 已弃用"""
        pass

    def setup_models(self):
        """设置数据模型"""
        self.target_model = TargetItemModel()
        # 设置日志管理器引用
        self.target_model.log_manager = self.log_manager
        self.source_model = SourceItemModel()

        # 监听公式更新事件
        self.target_model.formulaEdited.connect(self.handle_formula_updates)
        self.target_model.layoutChanged.connect(
            lambda: self._apply_main_header_layout()
        )

        # 设置主数据网格
        self.main_data_grid.setModel(self.target_model)
        self._apply_main_header_layout()
        ensure_word_wrap(self.main_data_grid)

        # 设置公式编辑器委托
        self.formula_delegate = FormulaEditorDelegate(self.workbook_manager)
        self.main_data_grid.setItemDelegateForColumn(
            3, self.formula_delegate
        )  # 映射公式列现在是第3列

        # 设置来源项树 - 现在使用增强的显示方法
        # self.source_tree.setModel(self.source_model)  # 保留旧方法作为备用

        # 配置列宽
        header = self.main_data_grid.header()
        ensure_interactive_header(header, stretch_last=False)
        header.setStretchLastSection(False)
        self._user_column_widths.clear()
        self._main_auto_resizing = False

        # 设置默认resize模式（具体列宽会在adjust_main_table_columns中动态配置）
        # 初始状态下所有列都使用Interactive模式，允许用户调整
        # 后续adjust_main_table_columns()会根据列名动态设置每列的具体策略

        header.sectionResized.connect(self._on_main_header_section_resized)
        header.sectionPressed.connect(self._on_main_header_section_pressed)

        # 触发列宽自动调整（会调用adjust_main_table_columns）
        self.schedule_main_table_resize()

    def setup_connections(self):
        """设置信号连接"""
        # 第一行工具栏按钮
        self.load_files_btn.clicked.connect(self.load_files)
        self.load_multiple_files_btn.clicked.connect(self.load_multiple_files)
        self.ai_assistant_btn.clicked.connect(self.show_ai_assistant)
        self.import_formula_btn.clicked.connect(self.import_formula_snapshot_via_dialog)
        self.save_formula_btn.clicked.connect(self.save_formula_snapshot_via_dialog)
        self.export_btn.clicked.connect(self.export_excel)

        # 第二行操作按钮
        self.clear_sheet_formulas_btn.clicked.connect(self.clear_current_sheet_formulas)
        self.clear_all_formulas_btn.clicked.connect(self.clear_all_formulas)

        # 初始状态：只有加载按钮和 AI 助手可用
        self.ai_assistant_btn.setEnabled(True)  # AI 助手始终可用
        self.import_formula_btn.setEnabled(False)
        self.save_formula_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.clear_sheet_formulas_btn.setEnabled(False)
        self.clear_all_formulas_btn.setEnabled(False)

        # 主数据网格选择变化
        self.main_data_grid.selectionModel().currentChanged.connect(
            self.on_target_selection_changed
        )
        self.main_data_grid.doubleClicked.connect(self.on_main_grid_double_clicked)

        # 拖放信号
        self.source_tree.dragStarted.connect(self.on_drag_started)
        self.main_data_grid.itemDropped.connect(self.on_item_dropped)

        # 连接来源项工作表切换信号，确保切换时主表格列宽自动调整
        self.source_tree.sheetChanged.connect(
            lambda _: self.schedule_main_table_resize(0)
        )

        # 公式编辑器信号 - 已删除（单元格检查TAB已移除）
        # self.formula_editor.formulaChanged.connect(self.on_formula_changed)

        # 注意：搜索功能现在由SearchableSourceTree内部处理

        # 主界面分析面板信号连接（新增）
        if hasattr(self, 'main_analysis_panel'):
            # 连接到chat_controller的analysis_controller
            self.main_analysis_panel.target_sheet_changed.connect(
                lambda sheet_name: self.chat_controller.analysis_controller.handle_target_sheet_change(sheet_name)
                if self.chat_controller else None
            )
            self.main_analysis_panel.target_column_toggled.connect(
                lambda key, checked: self.chat_controller.analysis_controller.handle_target_column_toggle(key, checked)
                if self.chat_controller else None
            )
            self.main_analysis_panel.source_column_toggled.connect(
                lambda sheet_name, key, checked: self.chat_controller.analysis_controller.handle_source_column_toggle(sheet_name, key, checked)
                if self.chat_controller else None
            )
            # 连接按钮信号
            self.main_analysis_panel.auto_parse_requested.connect(self._on_main_analysis_auto_parse)
            self.main_analysis_panel.export_json_requested.connect(self._on_main_analysis_export_json)
            self.main_analysis_panel.apply_requested.connect(self._on_main_analysis_apply)

    def _apply_main_header_layout(self):
        if not hasattr(self, "main_data_grid") or not hasattr(self, "target_model"):
            return

        if not self.target_model:
            apply_multirow_header(self.main_data_grid, {}, 1, stretch_last=False)
            return

        layout_provider = getattr(self.target_model, "get_header_layout", None)
        if not callable(layout_provider):
            apply_multirow_header(self.main_data_grid, {}, 1, stretch_last=False)
            return

        layout_map, row_count = self.target_model.get_header_layout()
        apply_multirow_header(
            self.main_data_grid, layout_map, row_count, stretch_last=False
        )

    def schedule_main_table_resize(self, delay_ms: int = 0):
        """延迟调整主数据网格列宽"""
        try:
            if not hasattr(self, "_main_resize_timer"):
                self._main_resize_timer = QTimer(self)
                self._main_resize_timer.setSingleShot(True)
                self._main_resize_timer.timeout.connect(self.adjust_main_table_columns)

            # 关键修复1：先停止旧的定时器，避免多个调用排队
            if self._main_resize_timer.isActive():
                self._main_resize_timer.stop()
                # 停止之前的列宽调整定时器（不输出日志）

            # 关键修复2：增加最小延迟，确保view有足够时间更新
            actual_delay = max(200, delay_ms)  # 最小200ms延迟
            self._main_resize_timer.start(actual_delay)
            # 列宽调整定时器已启动（不输出日志）

            # 同步调整行高延迟
            schedule_row_resize(self.main_data_grid, max(40, actual_delay + 40))
        except Exception as e:
            self.log_manager.error(f"启动列宽调整定时器失败: {e}")

    def _schedule_main_resize_retry(self, sheet_name: str, delay_ms: int = 200):
        """在列头尚未就绪时安排后续重试，防止自动扩宽永久失效"""
        try:
            if not hasattr(self, "_main_resize_retry_counts"):
                self._main_resize_retry_counts = {}

            retries = 0
            if sheet_name:
                retries = self._main_resize_retry_counts.get(sheet_name, 0)
                if retries >= 5:
                    self.log_manager.warning(
                        f"工作表 '{sheet_name}' 列头仍未就绪，已停止自动扩宽重试"
                    )
                    return
                self._main_resize_retry_counts[sheet_name] = retries + 1

            # 关键修复7：增加重试延迟，给view更多时间同步
            next_delay = max(delay_ms, 200)  # 最小200ms
            if retries:
                next_delay = min(1000, next_delay + retries * 150)  # 递增延迟，最大1秒

            self.log_manager.info(
                f"列头未就绪，{sheet_name or '当前工作表'} {retries + 1}/5 次重试将在 {next_delay}ms 后执行"
            )
            self.schedule_main_table_resize(next_delay)
        except Exception as e:
            self.log_manager.warning(f"安排列宽重试失败: {e}")

    def _on_main_header_section_pressed(self, logical_index: int):
        """用户开始调整列宽时停止待触发的自动调整"""
        if hasattr(self, "_main_resize_timer") and self._main_resize_timer.isActive():
            self._main_resize_timer.stop()

    def _on_main_header_section_resized(
        self, logical_index: int, old_size: int, new_size: int
    ):
        """记录用户手动调整的列宽"""
        if self._main_auto_resizing:
            return

        if logical_index >= 2:
            self._user_column_widths[logical_index] = new_size

    def adjust_main_table_columns(self):
        """根据内容调整主数据网格列宽 - 动态识别列名并应用相应规则"""
        if not hasattr(self, "main_data_grid"):
            return

        header = self.main_data_grid.header()
        model = self.main_data_grid.model()
        if not header or not model:
            return

        current_sheet = ""
        if hasattr(model, "active_sheet_name"):
            current_sheet = getattr(model, "active_sheet_name", "") or ""
        elif hasattr(self.target_model, "active_sheet_name"):
            current_sheet = getattr(self.target_model, "active_sheet_name", "") or ""

        # 关键修复5：添加view和model同步检查
        # 检查header的列数是否与model的列数一致
        header_count = header.count() if header else 0
        model_column_count = model.columnCount() if model else 0

        if header_count != model_column_count:
            self.log_manager.warning(
                f"View和Model未同步: header列数={header_count}, model列数={model_column_count}"
            )
            # 如果不同步，安排重试
            self._schedule_main_resize_retry(current_sheet, 200)
            return

        # 检查model是否有headers属性
        if not hasattr(model, "headers"):
            self.log_manager.warning("主数据表模型缺少headers属性，使用fallback模式")
            # 使用model.columnCount()生成简单headers作为fallback
            if model.columnCount() > 0:
                headers = [f"列{i+1}" for i in range(model.columnCount())]
            else:
                self._schedule_main_resize_retry(current_sheet, 200)
                return
        else:
            headers = getattr(model, "headers", []) or []

        if not headers or model.columnCount() == 0:
            # 只在真的没有列时才重试
            if model.columnCount() == 0:
                self.log_manager.info("主数据表尚无列，将延迟重试自动扩宽")
                self._schedule_main_resize_retry(current_sheet, 200)
                return
            # 有列但没headers，生成默认headers
            self.log_manager.info("使用默认列头进行列宽调整")
            headers = [f"列{i+1}" for i in range(model.columnCount())]

        # 关键修复6：再次验证headers长度与列数是否匹配
        if len(headers) != model.columnCount():
            self.log_manager.warning(
                f"Headers长度与列数不匹配: headers={len(headers)}, columns={model.columnCount()}"
            )
            # 生成正确长度的headers
            headers = [
                headers[i] if i < len(headers) else f"列{i+1}"
                for i in range(model.columnCount())
            ]

        if current_sheet and current_sheet in self._main_resize_retry_counts:
            self._main_resize_retry_counts.pop(current_sheet, None)

        # 🔍 动态分析所有列，根据列名应用不同的宽度策略
        adjustable_columns = {}  # {column_index: (min_width, max_width)}

        self._main_auto_resizing = True
        try:
            for column in range(model.columnCount()):
                # 🔧 修复：安全获取列名，添加边界检查
                column_name = ""
                try:
                    if hasattr(model, "headers") and column < len(model.headers):
                        column_name = model.headers[column] or ""
                    else:
                        # 如果headers不存在或索引越界，尝试从headerData获取
                        header_data = model.headerData(
                            column, Qt.Horizontal, Qt.DisplayRole
                        )
                        column_name = str(header_data) if header_data else ""
                except (IndexError, AttributeError) as e:
                    self.log_manager.warning(f"获取第{column}列名称失败: {e}")
                    continue

                if not column_name:
                    continue

                # 根据列名决定处理策略
                if column_name == "状态":
                    # 状态列：固定70px，不可调整
                    self.main_data_grid.setColumnWidth(column, 70)
                    header.setSectionResizeMode(column, QHeaderView.Fixed)

                elif column_name == "级别":
                    # 级别列：固定70px，不可调整
                    self.main_data_grid.setColumnWidth(column, 70)
                    header.setSectionResizeMode(column, QHeaderView.Fixed)

                elif column_name == "行次":
                    # 行次列：固定宽度，不参与自动扩宽
                    self.main_data_grid.setColumnWidth(column, ROW_NUMBER_COLUMN_WIDTH)
                    header.setSectionResizeMode(column, QHeaderView.Fixed)
                    self._user_column_widths.pop(column, None)
                    # 不添加到adjustable_columns，因此不参与自动扩宽

                elif "名称" in column_name or "项目" in column_name:
                    # 项目名称类列：自动扩宽，范围200-520px
                    adjustable_columns[column] = (200, 520)

                elif "公式" in column_name:
                    # 公式类列：自动扩宽，范围240-600px
                    adjustable_columns[column] = (240, 600)

                elif (
                    "预览" in column_name
                    or "值" in column_name
                    or "结果" in column_name
                ):
                    # 预览值类列：自动扩宽，范围120-240px
                    adjustable_columns[column] = (120, 240)

                else:
                    # 其他列：自动扩宽，使用通用范围100-300px
                    adjustable_columns[column] = (100, 300)

            # 对需要自动扩宽的列执行内容自适应
            for column, (min_width, max_width) in adjustable_columns.items():
                if column >= model.columnCount():
                    continue

                if column in self._user_column_widths:
                    # 尊重用户手动设置的列宽
                    continue

                header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
                self.main_data_grid.resizeColumnToContents(column)
                width = self.main_data_grid.columnWidth(column)
                bounded_width = max(min_width, min(width, max_width))
                self.main_data_grid.setColumnWidth(column, bounded_width)
                header.setSectionResizeMode(column, QHeaderView.Interactive)

        except Exception as e:
            self.log_manager.error(f"调整主表格列宽时出错: {e}")
            import traceback

            self.log_manager.info(traceback.format_exc())
        finally:
            self._main_auto_resizing = False

        # ✅ 在所有列处理完成后，再次确认"行次"列的设置
        # 防止在处理其他列时被Qt的布局更新机制重置
        try:
            row_num_column_index = None
            for column in range(model.columnCount()):
                # 安全获取列名
                column_name = ""
                if hasattr(model, "headers") and column < len(model.headers):
                    column_name = model.headers[column] or ""
                if column_name == "行次":
                    row_num_column_index = column
                    break

            if row_num_column_index is not None:
                # 最后强制锁定"行次"列宽，防止被后续自动调整覆盖
                self._user_column_widths.pop(row_num_column_index, None)
                self.main_data_grid.setColumnWidth(
                    row_num_column_index, ROW_NUMBER_COLUMN_WIDTH
                )
                header.setSectionResizeMode(row_num_column_index, QHeaderView.Fixed)
        except Exception as e:
            self.log_manager.warning(f"设置行次列宽度时出错: {e}")

        # 🔧 关键修复：智能填充以占满viewport，避免右侧空白
        try:
            # 构建min_widths和max_widths字典
            min_widths_dict = {}
            max_widths_dict = {}
            exclude_cols = []

            for column in range(model.columnCount()):
                column_name = ""
                if hasattr(model, "headers") and column < len(model.headers):
                    column_name = model.headers[column] or ""

                # 固定列加入exclude列表
                if column_name in ["状态", "级别", "行次"]:
                    exclude_cols.append(column)
                else:
                    # 从adjustable_columns获取min/max值
                    if column in adjustable_columns:
                        min_width, max_width = adjustable_columns[column]
                        min_widths_dict[column] = min_width
                        max_widths_dict[column] = max_width
                    else:
                        # 如果不在adjustable_columns中，使用默认值
                        min_widths_dict[column] = 100
                        max_widths_dict[column] = 300

            # 应用智能填充，确保占满整个viewport宽度
            distribute_columns_evenly(
                self.main_data_grid,
                exclude_columns=exclude_cols,
                min_widths=min_widths_dict,
                max_widths=max_widths_dict,
            )

            # 已应用智能填充（不输出日志）

        except Exception as e:
            self.log_manager.warning(f"智能填充列宽时出错: {e}")
            import traceback

            self.log_manager.info(traceback.format_exc())

        schedule_row_resize(self.main_data_grid, 80)

    def reset_current_session(self):
        """清空当前加载的工作簿与界面状态"""
        if hasattr(self, "_autosave_timer"):
            self._autosave_timer.stop()
        self._autosave_suspended = False

        self.workbook_manager = None
        self.data_extractor = None
        self.calculation_engine = None
        self.file_manager = FileManager()

        self.target_model.set_workbook_manager(None)
        self.source_model.set_workbook_manager(None)

        empty_model = QStandardItemModel()
        self.main_data_grid.setModel(self.target_model)
        self._apply_main_header_layout()
        self.source_tree.setModel(empty_model)
        apply_multirow_header(self.source_tree, {}, 1, stretch_last=False)
        self.source_tree.all_source_items = {}
        self.source_tree.current_sheet = None
        self.source_tree.available_sheets = []
        self.source_tree.sheet_column_configs = {}
        self.source_tree.sheet_column_metadata = {}
        if hasattr(self.source_tree, "sheet_combo"):
            self.source_tree.sheet_combo.blockSignals(True)
            self.source_tree.sheet_combo.clear()
            self.source_tree.sheet_combo.blockSignals(False)
        if hasattr(self.source_tree, "search_line"):
            self.source_tree.search_line.blockSignals(True)
            self.source_tree.search_line.clear()
            self.source_tree.search_line.blockSignals(False)

        # 清空主数据表的工作表选择和搜索框
        if hasattr(self, "target_sheet_combo"):
            self.target_sheet_combo.blockSignals(True)
            self.target_sheet_combo.clear()
            self.target_sheet_combo.blockSignals(False)
        if hasattr(self, "target_search_line"):
            self.target_search_line.blockSignals(True)
            self.target_search_line.clear()
            self.target_search_line.blockSignals(False)

        if hasattr(self, "property_table"):
            self.property_table.set_properties({})

        if hasattr(self, "classification_summary"):
            self.classification_summary.setText("请先加载Excel文件并确认工作表分类")

        self._user_column_widths.clear()
        self._main_auto_resizing = False
        if hasattr(self, "_main_resize_retry_counts"):
            self._main_resize_retry_counts.clear()
        self.show_target_source_message("请选择目标项以查看来源详情。")
        self._source_lookup_index = {}

        self.update_toolbar_states()
        self.schedule_main_table_resize(0)

    def update_toolbar_states(self):
        """根据当前数据刷新工具栏按钮状态"""
        has_workbook = self.workbook_manager is not None
        has_results = bool(
            self.workbook_manager
            and getattr(self.workbook_manager, "calculation_results", {})
        )

        # 第一行按钮状态
        self.load_files_btn.setEnabled(True)
        self.ai_assistant_btn.setEnabled(True)  # AI 助手始终可用
        self.import_formula_btn.setEnabled(has_workbook)
        self.save_formula_btn.setEnabled(has_workbook)
        self.export_btn.setEnabled(has_results)

        # 第二行清除按钮的启用逻辑
        has_formulas = bool(
            self.workbook_manager and self.workbook_manager.mapping_formulas
        )
        has_current_sheet = bool(
            has_formulas
            and hasattr(self.target_model, "active_sheet_name")
            and self.target_model.active_sheet_name
        )

        self.clear_sheet_formulas_btn.setEnabled(has_current_sheet)
        self.clear_all_formulas_btn.setEnabled(has_formulas)

    def show_sheet_classification_dialog(
        self, sheet_name: str, auto_classification: str
    ) -> str:
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
        import time

        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
        )

        if not file_paths:
            return

        existing_path = None
        if self.workbook_manager and getattr(self.workbook_manager, "file_path", None):
            existing_path = Path(self.workbook_manager.file_path)

        if existing_path:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("重新加载文件")
            msg.setText(f"当前已加载文件：\n<b>{existing_path.name}</b>")
            msg.setInformativeText("重新加载将清空当前所有数据和结果，是否继续？")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            msg.setStyleSheet(
                """
                QMessageBox {
                    background-color: #fdfdfd;
                    border-radius: 12px;
                }
                QMessageBox QLabel {
                    color: #2c3e50;
                    font-size: 13px;
                }
                QMessageBox QPushButton {
                    min-width: 88px;
                    min-height: 30px;
                    border-radius: 6px;
                    background-color: #3498db;
                    color: white;
                    font-weight: bold;
                    padding: 6px 14px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #2980b9;
                }
                QMessageBox QPushButton:pressed {
                    background-color: #1f6392;
                }
            """
            )

            if msg.exec() != QMessageBox.Yes:
                self.log_manager.operation("❌ 取消重新加载文件")
                return

        self.load_files_btn.setEnabled(False)
        start_time = time.time()

        if existing_path:
            self.reset_current_session()

        try:
            # 记录操作日志
            file_name = Path(file_paths[0]).name if file_paths else "未知文件"
            self.log_manager.operation(f"📁 加载文件: {file_name}")

            if not existing_path:
                # 确保初次加载时状态干净
                self.reset_current_session()

            success, message = self.file_manager.load_excel_files(file_paths)

            if success:
                self.workbook_manager = self.file_manager.get_workbook_manager()

                # 记录加载成功（带耗时）
                elapsed = time.time() - start_time
                self.log_manager.success(f"✅ 文件加载成功 (耗时: {elapsed:.1f}秒)")

                # 直接显示拖拽式工作表分类界面
                if self.workbook_manager and (
                    self.workbook_manager.flash_report_sheets
                    or self.workbook_manager.data_source_sheets
                ):
                    self.show_classification_dialog()
                    self.log_manager.operation("📊 请调整工作表分类")

                else:
                    # 没有找到工作表
                    self.log_manager.warning("未找到任何工作表")
                    # 重置摘要显示
                    if hasattr(self, "classification_summary"):
                        self.classification_summary.setText(
                            "未找到任何工作表，请检查Excel文件"
                        )

            else:
                self.log_manager.error(f"文件加载失败: {message}")
                QMessageBox.warning(self, "加载失败", message)

        except Exception as e:
            error_msg = f"加载文件时发生异常: {str(e)}"
            self.log_manager.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
        finally:
            self.load_files_btn.setEnabled(True)
            self.update_toolbar_states()

    def load_multiple_files(self):
        """加载多个Excel文件"""
        import time

        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择多个Excel文件（可多选）", "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )

        if not file_paths:
            return

        if len(file_paths) < 2:
            QMessageBox.information(
                self, "提示",
                "只选择了一个文件，请使用[加载单个Excel]按钮。\n\n"
                "加载多个Excel功能用于合并多个独立的Excel文件。"
            )
            return

        # 确认加载
        msg_text = f"将加载 {len(file_paths)} 个Excel文件：\n\n"
        for i, fp in enumerate(file_paths[:5], 1):
            msg_text += f"{i}. {Path(fp).name}\n"
        if len(file_paths) > 5:
            msg_text += f"... 还有 {len(file_paths)-5} 个文件\n"
        msg_text += "\n所有文件的sheet将合并在一起处理，\n最终导出时会合并到一个Excel文件中。"

        reply = QMessageBox.question(
            self, "确认加载", msg_text,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            self.log_manager.operation("❌ 取消加载多个文件")
            return

        self.load_files_btn.setEnabled(False)
        self.load_multiple_files_btn.setEnabled(False)
        start_time = time.time()

        try:
            # 清空当前会话
            self.reset_current_session()

            # 记录操作日志
            self.log_manager.operation(f"📂 加载多个Excel: {len(file_paths)}个文件")

            success, message = self.file_manager.load_excel_files(file_paths)

            if success:
                self.workbook_manager = self.file_manager.get_workbook_manager()

                # 记录加载成功（带耗时）
                elapsed = time.time() - start_time
                sheet_count = len(self.workbook_manager.worksheets) if self.workbook_manager else 0
                self.log_manager.success(
                    f"✅ 多文件加载成功: {len(file_paths)}个文件, {sheet_count}个sheet (耗时: {elapsed:.1f}秒)"
                )

                # 显示分类对话框
                if self.workbook_manager and (
                    self.workbook_manager.flash_report_sheets
                    or self.workbook_manager.data_source_sheets
                ):
                    self.show_classification_dialog()
                    self.log_manager.operation("📊 请调整工作表分类")
                else:
                    self.log_manager.warning("未找到任何工作表")

            else:
                self.log_manager.error(f"加载失败: {message}")
                QMessageBox.warning(self, "加载失败", message)

        except Exception as e:
            error_msg = f"加载多个文件时发生异常: {str(e)}"
            self.log_manager.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            import traceback
            traceback.print_exc()
        finally:
            self.load_files_btn.setEnabled(True)
            self.load_multiple_files_btn.setEnabled(True)
            self.update_toolbar_states()

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
        if (
            hasattr(self.workbook_manager, "worksheets")
            and self.workbook_manager.worksheets
        ):
            all_sheets = dict(self.workbook_manager.worksheets)
        else:
            # 如果没有worksheets，从列表中重建（兼容性处理）
            for sheet in self.workbook_manager.flash_report_sheets:
                if isinstance(sheet, str):
                    # 如果是字符串，创建临时的工作表信息
                    from models.data_models import WorksheetInfo, SheetType

                    sheet_info = WorksheetInfo(
                        name=sheet, sheet_type=SheetType.FLASH_REPORT
                    )
                    all_sheets[sheet] = sheet_info
                else:
                    # 如果是对象，直接使用
                    all_sheets[sheet.name] = sheet

            for sheet in self.workbook_manager.data_source_sheets:
                if isinstance(sheet, str):
                    # 如果是字符串，创建临时的工作表信息
                    from models.data_models import WorksheetInfo, SheetType

                    sheet_info = WorksheetInfo(
                        name=sheet, sheet_type=SheetType.DATA_SOURCE
                    )
                    all_sheets[sheet] = sheet_info
                else:
                    # 如果是对象，直接使用
                    all_sheets[sheet.name] = sheet

        # 根据最终分类重新分配工作表
        for sheet_name in final_classifications["flash_reports"]:
            if sheet_name in all_sheets:
                sheet = all_sheets[sheet_name]
                sheet.sheet_type = SheetType.FLASH_REPORT
                new_flash_reports.append(sheet)

        for sheet_name in final_classifications["data_sources"]:
            if sheet_name in all_sheets:
                sheet = all_sheets[sheet_name]
                sheet.sheet_type = SheetType.DATA_SOURCE
                new_data_sources.append(sheet)

        # 更新工作簿管理器
        self.workbook_manager.flash_report_sheets = new_flash_reports
        self.workbook_manager.data_source_sheets = new_data_sources

        # 记录跳过和禁用的工作表
        if final_classifications["skipped"]:
            self.log_manager.info(
                f"跳过的工作表: {', '.join(final_classifications['skipped'])}"
            )

        if final_classifications["disabled"]:
            self.log_manager.info(
                f"禁用的工作表: {', '.join(final_classifications['disabled'])}"
            )

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
                self.workbook_manager.flash_report_sheets = classifications.get(
                    "flash_reports", []
                )
                self.workbook_manager.data_source_sheets = classifications.get(
                    "data_sources", []
                )

                # 更新分类摘要显示
                self.update_navigator_summary(classifications, status="final")

                # 如果有数据来源表，开始提取数据
                if classifications.get("data_sources"):
                    self.log_manager.info("分类确认完成，开始自动提取数据...")
                    self.extract_data()

        except Exception as e:
            self.log_manager.error(f"应用分类结果时出错: {str(e)}")

    def on_classification_changed(self, *args):
        """工作表分类发生变化时的回调（保留兼容性）"""
        # 处理不同参数格式的兼容性
        if len(args) >= 2:
            sheet_name, new_type = args[0], args[1]
            if hasattr(new_type, "value"):
                type_name = (
                    "快报表" if new_type.value == "flash_report" else "数据来源表"
                )
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

        if final_classifications["flash_reports"]:
            result_text += (
                f"📊 快报表 ({len(final_classifications['flash_reports'])} 个):\n"
            )
            for sheet in final_classifications["flash_reports"]:
                result_text += f"  • {sheet}\n"
            result_text += "\n"

        if final_classifications["data_sources"]:
            result_text += (
                f"📋 数据来源表 ({len(final_classifications['data_sources'])} 个):\n"
            )
            for sheet in final_classifications["data_sources"]:
                result_text += f"  • {sheet}\n"
            result_text += "\n"

        if final_classifications["cancelled"]:
            result_text += (
                f"❌ 已取消处理 ({len(final_classifications['cancelled'])} 个):\n"
            )
            for sheet in final_classifications["cancelled"]:
                result_text += f"  • {sheet}\n"
            result_text += "\n"

        result_text += "💡 提示: 现在可以进行数据提取操作了。"

        dialog.setText(result_text)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.exec()

        # 同时在导航区显示摘要信息
        self.update_navigator_summary(final_classifications, status="final")

    def update_navigator_summary(self, classifications, status: str = "auto"):
        """更新导航区域分类摘要"""
        if not hasattr(self, "classification_summary"):
            return

        is_final = status == "final"
        title_prefix = "✅ 分类已确认" if is_final else "🔄 自动分类结果 (待确认)"

        summary_text = f"{title_prefix}\n\n"

        flash_reports = classifications.get("flash_reports", [])
        data_sources = classifications.get("data_sources", [])
        cancelled = classifications.get("cancelled", [])

        if flash_reports:
            summary_text += f"📊 快报表 ({len(flash_reports)} 个):\n"
            for sheet in flash_reports:
                summary_text += f"  • {sheet}\n"
            summary_text += "\n"
        else:
            summary_text += "📊 快报表: 无\n\n"

        if data_sources:
            summary_text += f"📋 数据来源表 ({len(data_sources)} 个):\n"
            for sheet in data_sources:
                summary_text += f"  • {sheet}\n"
            summary_text += "\n"
        else:
            summary_text += "📋 数据来源表: 无\n\n"

        if cancelled:
            summary_text += f"❌ 已取消 ({len(cancelled)} 个):\n"
            for sheet in cancelled:
                summary_text += f"  • {sheet}\n"
            summary_text += "\n"

        if is_final:
            summary_text += "💡 分类确认完成，可继续后续操作"
        else:
            summary_text += "⚠️ 请检查分类结果并确认"

        self.classification_summary.setText(summary_text)

        if is_final:
            total_active = len(flash_reports) + len(data_sources)
            self.statusBar().showMessage(
                f"分类完成 - 活跃工作表: {total_active} 个, 已取消: {len(cancelled)} 个"
            )
        else:
            total_sheets = len(flash_reports) + len(data_sources)
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
        if (
            hasattr(self.workbook_manager, "worksheets")
            and self.workbook_manager.worksheets
        ):
            all_sheets = dict(self.workbook_manager.worksheets)
        else:
            # 如果没有worksheets，从列表中重建（兼容性处理）
            for sheet in self.workbook_manager.flash_report_sheets:
                if isinstance(sheet, str):
                    # 如果是字符串，创建临时的工作表信息
                    from models.data_models import WorksheetInfo, SheetType

                    sheet_info = WorksheetInfo(
                        name=sheet, sheet_type=SheetType.FLASH_REPORT
                    )
                    all_sheets[sheet] = sheet_info
                else:
                    # 如果是对象，直接使用
                    all_sheets[sheet.name] = sheet

            for sheet in self.workbook_manager.data_source_sheets:
                if isinstance(sheet, str):
                    # 如果是字符串，创建临时的工作表信息
                    from models.data_models import WorksheetInfo, SheetType

                    sheet_info = WorksheetInfo(
                        name=sheet, sheet_type=SheetType.DATA_SOURCE
                    )
                    all_sheets[sheet] = sheet_info
                else:
                    # 如果是对象，直接使用
                    all_sheets[sheet.name] = sheet

        # 根据最终分类重新分配工作表
        for sheet_name in final_classifications["flash_reports"]:
            if sheet_name in all_sheets:
                sheet = all_sheets[sheet_name]
                sheet.sheet_type = SheetType.FLASH_REPORT
                new_flash_reports.append(sheet)

        for sheet_name in final_classifications["data_sources"]:
            if sheet_name in all_sheets:
                sheet = all_sheets[sheet_name]
                sheet.sheet_type = SheetType.DATA_SOURCE
                new_data_sources.append(sheet)

        # 更新工作簿管理器
        self.workbook_manager.flash_report_sheets = new_flash_reports
        self.workbook_manager.data_source_sheets = new_data_sources

        # 记录取消的工作表
        if final_classifications["cancelled"]:
            self.log_manager.info(
                f"已取消的工作表: {', '.join(final_classifications['cancelled'])}"
            )

    def extract_data(self):
        """提取数据"""
        if not self.workbook_manager:
            QMessageBox.warning(self, "警告", "请先加载Excel文件")
            return

        try:
            self.log_manager.system("开始数据提取...")

            # 使用增强的数据提取器
            extractor = DataExtractor(self.workbook_manager)
            success = extractor.extract_all_data()

            if not success:
                QMessageBox.warning(self, "错误", "数据提取失败，请检查Excel文件格式")
                return

            # 显示统计信息
            targets_count = len(self.workbook_manager.target_items)
            sources_count = len(self.workbook_manager.source_items)
            self.log_manager.system(
                f"提取完成: 目标项{targets_count}个, 来源项{sources_count}个"
            )

            # 更新所有模型
            self.target_model.set_workbook_manager(self.workbook_manager)
            self._target_column_config = None
            self._ensure_target_column_config()
            self.apply_target_column_config()
            self._apply_main_header_layout()
            self.target_column_config_btn.setEnabled(True)

            loaded_count = self.file_manager.load_saved_formulas(self.workbook_manager)
            if loaded_count:
                self.log_manager.info(
                    f"已恢复 {loaded_count} 条历史映射公式，正在重新计算……"
                )
                self._autosave_suspended = True
                self.handle_formula_updates(
                    list(self.workbook_manager.mapping_formulas.keys()),
                    reason="autosave_restore",
                )
                self._autosave_suspended = False
                self.schedule_autosave()

            # 连接导航信号
            self.target_model.itemSelected.connect(self.on_target_item_selected)
            self.target_model.navigationRequested.connect(self.on_navigation_requested)

            self.source_model.set_workbook_manager(self.workbook_manager)

            # 使用增强的来源项显示
            self.source_tree.set_column_metadata(
                self.workbook_manager.source_sheet_columns
            )
            self.source_tree.populate_source_items(self.workbook_manager.source_items)
            self._rebuild_source_lookup_index()

            # 更新主数据表的工作表下拉菜单
            if hasattr(self, "target_sheet_combo"):
                self.target_sheet_combo.blockSignals(True)
                self.target_sheet_combo.clear()
                # 添加所有快报表到下拉菜单
                flash_report_sheets = self.workbook_manager.flash_report_sheets
                self.target_sheet_combo.addItems(flash_report_sheets)
                # 如果有快报表，默认选择第一个
                if flash_report_sheets:
                    self.target_sheet_combo.setCurrentIndex(0)
                self.target_sheet_combo.blockSignals(False)

                # ✅ 手动触发工作表切换，确保正确初始化第一个工作表
                if flash_report_sheets:
                    first_sheet = flash_report_sheets[0]
                    self.target_model.set_active_sheet(first_sheet)
                    self._apply_main_header_layout()
                    self.log_manager.info(f"已初始化主表格，显示工作表: {first_sheet}")

            # 更新公式编辑器的工作簿管理器 - 已删除（单元格检查TAB已移除）
            # self.formula_editor.set_workbook_manager(self.workbook_manager)
            self.formula_delegate.workbook_manager = self.workbook_manager

            self.schedule_main_table_resize(0)
            self.update_toolbar_states()
            self.refresh_target_source_summary()
            self._sync_analysis_context()

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

            # 从ChatController获取AI配置
            if not self.chat_controller or not self.chat_controller.current_config:
                QMessageBox.warning(self, "警告", "AI服务未初始化,请先配置AI")
                self.progress_bar.setVisible(False)
                return

            config = self.chat_controller.current_config
            ai_config = {
                "api_url": config.base_url,
                "api_key": config.api_key,
                "model": config.model,
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
                model=ai_config["model"],
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

                QMessageBox.information(
                    self,
                    "成功",
                    f"AI分析完成！\n生成了 {applied_count} 个公式映射\n"
                    f"有效映射: {ai_response.valid_mappings}\n"
                    f"无效映射: {ai_response.invalid_mappings}",
                )

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
                "source_items": ai_request.source_items,
            }

            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ai_request.api_key}",
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
5. formula字符串的格式必须为：[工作表名]单元格，如 [利润表]D12 + [利润表]D15。
6. 如果一个 target_item 无法从 source_items 中找到任何映射关系，请不要为它创建映射条目。
7. 分析时要特别注意 target_items 的层级关系和名称中的关键词，例如"减："、"其中："、"加："等，这些都暗示了计算逻辑。

请像一名严谨的会计师一样思考，确保公式的准确性。""",
                    },
                    {
                        "role": "user",
                        "content": json.dumps(request_data, ensure_ascii=False),
                    },
                ],
                "temperature": ai_request.temperature,
                "max_tokens": ai_request.max_tokens,
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
                timeout=ai_request.timeout,
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
                ai_content = (
                    response_data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )

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
                        mappings_payload = mapping_data["mappings"]
                        ai_response.mappings = mappings_payload

                        if isinstance(mappings_payload, dict):
                            ai_response.processed_mappings = sum(
                                len(columns) if isinstance(columns, dict) else 1
                                for columns in mappings_payload.values()
                            )
                        elif isinstance(mappings_payload, list):
                            ai_response.processed_mappings = len(mappings_payload)
                        else:
                            ai_response.processed_mappings = 0
                    else:
                        ai_response.success = False
                        ai_response.error_message = "AI响应缺少mappings字段"

                except json.JSONDecodeError as e:
                    ai_response.success = False
                    ai_response.error_message = f"AI响应JSON解析失败: {str(e)}"
                    self.log_manager.error(f"AI原始响应: {ai_content}")

                # 统计token使用量
                if "usage" in response_data:
                    ai_response.tokens_used = response_data["usage"].get(
                        "total_tokens", 0
                    )

                return ai_response

            else:
                ai_response = AIAnalysisResponse()
                ai_response.success = False
                ai_response.error_message = (
                    f"API请求失败: {response.status_code} - {response.text}"
                )
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
        from models.data_models import FormulaStatus, TargetItem
        from utils.excel_utils import validate_formula_syntax_three_segment

        if not self.workbook_manager:
            return 0

        applied_count = 0
        valid_count = 0
        invalid_count = 0
        updated_targets: Set[str] = set()

        mappings_payload = getattr(ai_response, "mappings", {})

        if isinstance(mappings_payload, dict):
            # 新结构：{ target_name: { column_name: {formula, confidence, reasoning} } }
            target_lookup: Dict[str, List[TargetItem]] = {}
            for item in self.workbook_manager.target_items.values():
                target_lookup.setdefault(item.name, []).append(item)

            for target_name, column_map in mappings_payload.items():
                if not isinstance(column_map, dict):
                    column_map = {"__default__": column_map}

                candidates = target_lookup.get(target_name, [])
                if not candidates:
                    self.log_manager.warning(f"AI映射目标未匹配: {target_name}")
                    continue

                target_item = candidates[0]

                for column_label, mapping_info in column_map.items():
                    if isinstance(mapping_info, dict):
                        formula_text = str(mapping_info.get("formula", "")).strip()
                        confidence_value = mapping_info.get("confidence", 0.0)
                        reasoning_text = str(mapping_info.get("reasoning", "")).strip()
                    else:
                        formula_text = str(mapping_info).strip()
                        confidence_value = 0.0
                        reasoning_text = ""

                    if not formula_text:
                        continue

                    if not reasoning_text:
                        reasoning_text = str(
                            getattr(ai_response, "model_used", "")
                        ).strip()
                        if reasoning_text:
                            reasoning_text = f"AI生成 (模型: {reasoning_text})"
                        else:
                            reasoning_text = "AI生成结果，缺少详细推理。"

                    is_valid, error_msg = validate_formula_syntax_three_segment(
                        formula_text, self.workbook_manager
                    )
                    if not is_valid:
                        invalid_count += 1
                        self.log_manager.warning(
                            f"AI生成的公式无效: {formula_text} - {error_msg}"
                        )
                        continue

                    column_key = column_label
                    column_display = column_label
                    for key, column_entry in (target_item.columns or {}).items():
                        if column_entry.display_name == column_label or key == column_label:
                            column_key = key
                            column_display = column_entry.display_name or column_label
                            break

                    mapping = self.workbook_manager.ensure_mapping(
                        target_item.id, column_key, column_display
                    )
                    mapping.update_formula(
                        formula_text,
                        status=FormulaStatus.AI_GENERATED,
                        column_name=column_display,
                    )
                    mapping.constant_value = None
                    mapping.validation_error = ""

                    try:
                        confidence_float = float(confidence_value)
                    except (TypeError, ValueError):
                        confidence_float = 0.0
                    mapping.ai_confidence = max(0.0, min(1.0, confidence_float))
                    mapping.ai_reasoning = reasoning_text

                    applied_count += 1
                    valid_count += 1
                    updated_targets.add(target_item.id)
                    self.log_manager.info(
                        f"应用AI映射: {target_item.name}[{column_display}] = {formula_text}"
                    )

        elif isinstance(mappings_payload, list):
            # 旧结构兼容：[{"target_id": str, "formula": str, ...}]
            for mapping in mappings_payload:
                if not isinstance(mapping, dict):
                    continue

                target_id = mapping.get("target_id") or mapping.get("targetId")
                formula_text = str(mapping.get("formula", "")).strip()

                if not target_id or not formula_text:
                    continue

                if target_id not in self.workbook_manager.target_items:
                    self.log_manager.warning(f"目标项不存在: {target_id}")
                    continue

                is_valid, error_msg = validate_formula_syntax_three_segment(
                    formula_text, self.workbook_manager
                )
                if not is_valid:
                    invalid_count += 1
                    self.log_manager.warning(
                        f"AI生成的公式无效: {formula_text} - {error_msg}"
                    )
                    continue

                mapping_formula = self.workbook_manager.ensure_mapping(
                    target_id, "__default__", ""
                )
                mapping_formula.update_formula(
                    formula_text,
                    status=FormulaStatus.AI_GENERATED,
                )
                mapping_formula.constant_value = None
                mapping_formula.validation_error = ""

                try:
                    confidence_float = float(mapping.get("confidence", 0.0))
                except (TypeError, ValueError):
                    confidence_float = 0.0
                if mapping.get("reasoning"):
                    reasoning_text = str(mapping.get("reasoning", "")).strip()
                else:
                    model_label = str(getattr(ai_response, "model_used", "")).strip()
                    reasoning_text = (
                        f"AI生成 (模型: {model_label})"
                        if model_label
                        else "AI生成结果，缺少详细推理。"
                    )

                mapping_formula.ai_confidence = max(0.0, min(1.0, confidence_float))
                mapping_formula.ai_reasoning = reasoning_text

                applied_count += 1
                valid_count += 1
                updated_targets.add(target_id)

                target_name = self.workbook_manager.target_items[target_id].name
                self.log_manager.info(
                    f"应用AI映射: {target_name} = {formula_text}"
                )

        else:
            self.log_manager.warning("AI响应mappings结构无效，未应用任何公式。")

        # 更新响应统计
        ai_response.valid_mappings = valid_count
        ai_response.invalid_mappings = invalid_count

        if updated_targets:
            self.handle_formula_updates(list(updated_targets), reason="ai")

        return applied_count

    def export_excel(self):
        """导出Excel - 导出所有待写入表的公式"""
        if not self.workbook_manager:
            QMessageBox.warning(self, "警告", "请先加载并提取数据")
            return

        if not getattr(self.workbook_manager, "calculation_results", {}):
            QMessageBox.warning(self, "提示", "暂无计算结果，请先生成或刷新计算数据。")
            return

        # 检查是否有待写入表
        flash_report_sheets = self.workbook_manager.flash_report_sheets or []
        if not flash_report_sheets:
            QMessageBox.warning(self, "警告", "没有待写入表（快报表），无法导出")
            return

        # 获取保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Excel文件", "", "Excel Files (*.xlsx);;All Files (*)"
        )

        if not file_path:
            return

        try:
            import time
            import os
            start_time = time.time()

            # 记录操作日志
            file_name = os.path.basename(file_path)
            flash_count = len(flash_report_sheets)
            self.log_manager.operation(f"📤 导出Excel: {file_name} ({flash_count}个待写入表)")

            # 使用新的智能公式导出器
            from modules.excel_exporter import ExcelFormulaWriter, ExportOptions

            writer = ExcelFormulaWriter()
            options = ExportOptions(
                include_metadata_sheet=False,  # ❌ 不要添加元数据工作表
                preserve_values_on_error=True,
                auto_validate=False,  # 暂不自动验证，避免需要Excel计算引擎
                error_handling_mode="preserve",  # 转换失败时保留计算值
                use_absolute_path=False,  # ❌ 使用相对引用，不要绝对路径
                add_formula_comments=False
            )

            # 导出所有待写入表
            self.log_manager.system(f"处理{flash_count}个待写入表...")
            result = writer.export_all_flash_reports_with_formulas(
                workbook_manager=self.workbook_manager,
                output_path=file_path,
                options=options
            )

            if result.success:
                # 记录导出成功（带详细统计和耗时）
                elapsed = time.time() - start_time
                success_rate = (result.converted_formulas / result.total_formulas * 100) if result.total_formulas > 0 else 0
                self.log_manager.success(
                    f"✅ 导出完成: {flash_count}个表, {result.total_formulas}个公式, "
                    f"{result.converted_formulas}个成功 ({success_rate:.0f}%) (耗时: {elapsed:.1f}秒)"
                )

                # 生成详细的成功消息
                success_rate = (result.converted_formulas / result.total_formulas * 100) if result.total_formulas > 0 else 0
                detail_msg = (
                    f"数据已导出到：\n<b>{file_path}</b>\n\n"
                    f"导出的待写入表: {len(flash_report_sheets)} 个\n"
                    f"  ({', '.join(flash_report_sheets)})\n\n"
                    f"总公式数: {result.total_formulas}\n"
                    f"成功转换: {result.converted_formulas} ({success_rate:.1f}%)\n"
                    f"失败转换: {len(result.failed_conversions)}\n"
                    f"耗时: {result.execution_time:.2f}秒"
                )

                if result.failed_conversions:
                    self.log_manager.warning(f"有 {len(result.failed_conversions)} 个公式转换失败，已使用计算值替代")

                    # 生成失败报告文件名
                    base_path = os.path.splitext(file_path)[0]
                    report_path = f"{base_path}_导出失败报告.txt"

                    # 统计错误类型
                    error_types = {}
                    for error in result.failed_conversions:
                        error_type = error.error_type
                        if error_type not in error_types:
                            error_types[error_type] = 0
                        error_types[error_type] += 1

                    # 构建详细的失败信息
                    detail_msg += f"\n\n⚠️ {len(result.failed_conversions)} 个公式转换失败，已使用计算值替代\n\n"
                    detail_msg += "失败原因统计：\n"
                    for error_type, count in error_types.items():
                        error_type_cn = {
                            "cell_not_found": "未找到单元格",
                            "syntax_error": "语法错误",
                            "reference_error": "引用错误",
                            "security_error": "安全错误",
                            "cell_bounds_error": "单元格越界"
                        }.get(error_type, error_type)
                        detail_msg += f"  • {error_type_cn}: {count} 个\n"

                    detail_msg += f"\n前 {min(5, len(result.failed_conversions))} 个失败示例：\n"
                    for i, error in enumerate(result.failed_conversions[:5], 1):
                        target_name = error.target_item.name if error.target_item else "未知"
                        target_cell = error.target_item.target_cell_address if error.target_item else "未知"
                        detail_msg += f"{i}. {target_name} ({target_cell})\n"
                        detail_msg += f"   错误: {error.error_message[:60]}...\n" if len(error.error_message) > 60 else f"   错误: {error.error_message}\n"

                    if len(result.failed_conversions) > 5:
                        detail_msg += f"\n...还有 {len(result.failed_conversions) - 5} 个失败项\n"

                    detail_msg += f"\n详细失败报告已保存到：\n<b>{report_path}</b>"

                QMessageBox.information(self, "导出完成", detail_msg)
            else:
                self.log_manager.error("导出失败")

                error_details = "导出失败，详细信息：\n\n"
                if result.failed_conversions:
                    error_details += f"失败的公式数: {len(result.failed_conversions)}\n"
                    # 显示前3个错误
                    for i, error in enumerate(result.failed_conversions[:3]):
                        error_details += f"\n{i+1}. {error.error_message}\n"
                    if len(result.failed_conversions) > 3:
                        error_details += f"\n...还有 {len(result.failed_conversions) - 3} 个错误"

                QMessageBox.warning(self, "导出失败", error_details)

        except Exception as e:
            error_msg = f"导出Excel时发生异常: {str(e)}"
            self.log_manager.error(error_msg)

            import traceback
            traceback_str = traceback.format_exc()
            self.log_manager.error(f"详细错误:\n{traceback_str}")

            QMessageBox.critical(self, "错误", error_msg)
        finally:
            self.update_toolbar_states()

    def export_json(self):
        """导出JSON"""
        if not self.calculation_engine:
            QMessageBox.warning(self, "警告", "请先进行计算")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存JSON文件", "", "JSON Files (*.json);;All Files (*)"
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
            if hasattr(self, "property_table"):
                self.property_table.set_properties({})
            # 阻止信号，避免触发公式更新循环 - 已删除（单元格检查TAB已移除）
            # if hasattr(self, "formula_editor") and self.formula_editor:
            #     self.formula_editor.blockSignals(True)
            #     self.formula_editor.setPlainText("")
            #     self.formula_editor.blockSignals(False)
            self.show_target_source_message("请选择目标项以查看来源详情。")
            return

        item = current.internalPointer()
        if not isinstance(item, TargetItem) or not self.workbook_manager:
            if hasattr(self, "property_table"):
                self.property_table.set_properties({})
            return

        # 更新属性表格
        self.update_property_inspector(item)

        # 更新公式检查器
        selected_formula = ""
        self._active_formula_column = None

        column_meta_lookup = getattr(self.target_model, "_column_meta_at", None)
        selected_meta = (
            column_meta_lookup(current.column())
            if callable(column_meta_lookup)
            else None
        )

        preferred_key = selected_meta["key"] if selected_meta else None
        column_key, mapping = self._get_mapping_for_item(item, preferred_key)
        if column_key:
            self._active_formula_column = column_key

        if mapping and mapping.formula:
            selected_formula = mapping.formula

        # 阻止信号，避免触发公式更新循环 - 已删除（单元格检查TAB已移除）
        # if hasattr(self, "formula_editor") and self.formula_editor:
        #     self.formula_editor.blockSignals(True)
        #     self.formula_editor.setPlainText(selected_formula)
        #     self.formula_editor.blockSignals(False)

        self.update_target_source_panel(item)

    def on_drag_started(self, index: QModelIndex):
        """拖拽开始处理"""
        self.log_manager.info(f"开始拖拽: {index.data(Qt.DisplayRole)}")

    def on_item_dropped(self, target_index: QModelIndex, dropped_text: str):
        """项目拖放处理"""
        if not target_index.isValid():
            return

        column_meta = getattr(target_index.model(), "_column_meta_at", None)
        if not callable(column_meta) or not column_meta(target_index.column()):
            return

        current_text = target_index.data(Qt.DisplayRole) or ""
        new_text = f"{current_text} + {dropped_text}" if current_text else dropped_text

        # 更新模型数据
        target_index.model().setData(target_index, new_text, Qt.EditRole)

        self.log_manager.info(f"已添加引用: {dropped_text}")

    def handle_formula_updates(self, target_ids: List[str], reason: str = "manual"):
        """统一处理公式更新后的逻辑"""
        if not self.workbook_manager or not target_ids:
            return

        unique_ids: List[str] = []
        for target_id in target_ids:
            if (
                target_id
                and target_id in self.workbook_manager.target_items
                and target_id not in unique_ids
            ):
                unique_ids.append(target_id)

        if not unique_ids:
            return

        self.recalculate_targets(unique_ids, reason=reason)
        self.schedule_autosave()

    def recalculate_targets(self, target_ids: List[str], reason: str = "manual"):
        """增量计算指定目标项的预览值"""
        if not self.workbook_manager:
            return

        from modules.calculation_engine import create_calculation_engine

        if not self.calculation_engine:
            self.calculation_engine = create_calculation_engine(self.workbook_manager)
        else:
            # 重置上下文确保使用最新数据
            self.calculation_engine.workbook_manager = self.workbook_manager
            self.calculation_engine.calculation_context.value_cache.clear()
            self.calculation_engine.calculation_context.calculation_order.clear()
            self.calculation_engine.calculation_context.errors.clear()
            self.calculation_engine.calculation_context.warnings.clear()

        engine = self.calculation_engine

        successful: List[Tuple[str, str, str]] = (
            []
        )  # (target_id, column_key, column_name)
        cleared: List[Tuple[str, str, str]] = []  # (target_id, column_key, column_name)
        errors: List[Tuple[str, str, str, str]] = (
            []
        )  # (target_id, column_key, column_name, message)

        for target_id in target_ids:
            column_map = self.workbook_manager.mapping_formulas.get(target_id, {})
            if isinstance(column_map, MappingFormula):
                column_map = {column_map.column_key or "__default__": column_map}

            if not column_map:
                self.workbook_manager.calculation_results.pop(target_id, None)
                continue

            for column_key, formula_obj in column_map.items():
                if not formula_obj.formula or not formula_obj.formula.strip():
                    formula_obj.update_formula(
                        "",
                        status=FormulaStatus.EMPTY,
                        column_name=formula_obj.column_name,
                    )
                    formula_obj.calculation_result = None
                    formula_obj.last_calculated = None
                    formula_obj.validation_error = ""

                    result_map = self.workbook_manager.calculation_results.get(
                        target_id
                    )
                    if result_map and column_key in result_map:
                        del result_map[column_key]
                        if not result_map:
                            self.workbook_manager.calculation_results.pop(
                                target_id, None
                            )
                    cleared.append(
                        (target_id, column_key, formula_obj.column_name or column_key)
                    )
                    continue

                is_valid, error_msg = validate_formula_syntax_three_segment(
                    formula_obj.formula, self.workbook_manager
                )
                if not is_valid:
                    formula_obj.set_validation_result(False, error_msg)
                    result_map = self.workbook_manager.calculation_results.get(
                        target_id
                    )
                    if result_map and column_key in result_map:
                        del result_map[column_key]
                        if not result_map:
                            self.workbook_manager.calculation_results.pop(
                                target_id, None
                            )
                    errors.append(
                        (
                            target_id,
                            column_key,
                            formula_obj.column_name or column_key,
                            error_msg,
                        )
                    )
                    continue

                formula_obj.set_validation_result(True, "")

                result = engine.calculate_single_formula(target_id, formula_obj)
                result_map = self.workbook_manager.calculation_results.setdefault(
                    target_id, {}
                )
                result_map[column_key] = result

                if result.success:
                    successful.append(
                        (target_id, column_key, formula_obj.column_name or column_key)
                    )
                else:
                    formula_obj.status = FormulaStatus.ERROR
                    formula_obj.validation_error = result.error_message or "计算失败"
                    errors.append(
                        (
                            target_id,
                            column_key,
                            formula_obj.column_name or column_key,
                            formula_obj.validation_error,
                        )
                    )

        # 更新界面显示
        if self.target_model:
            for target_id in target_ids:
                index = self.target_model.get_index_for_target(target_id, 0)
                if index.isValid():
                    left = index.sibling(index.row(), 0)
                    right = index.sibling(
                        index.row(), self.target_model.columnCount() - 1
                    )
                    self.target_model.dataChanged.emit(left, right, [Qt.DisplayRole])

        # 若当前选中项被更新，刷新属性检查器
        current_index = self.main_data_grid.currentIndex()
        if current_index.isValid():
            current_item = self.target_model.get_target_item(current_index)
            if current_item and current_item.id in target_ids:
                self.update_property_inspector(current_item)
                self.update_target_source_panel(current_item)

        # 日志反馈
        if successful:
            if len(successful) == 1:
                target_id, _column_key, column_name = successful[0]
                name = self.workbook_manager.target_items[target_id].name
                self.log_manager.success(f"🧮 预览已更新: {name} · {column_name}")
            else:
                self.log_manager.success(f"🧮 已更新 {len(successful)} 个列的预览值")

        if cleared:
            if len(cleared) == 1:
                target_id, _column_key, column_name = cleared[0]
                name = self.workbook_manager.target_items[target_id].name
                self.log_manager.info(f"⭕ 已清空公式预览: {name} · {column_name}")
            else:
                self.log_manager.info(f"⭕ 已清空 {len(cleared)} 个列的公式预览")

        for target_id, _column_key, column_name, message in errors:
            name = self.workbook_manager.target_items[target_id].name
            self.log_manager.warning(f"❌ {name} · {column_name} 计算失败: {message}")

        self.schedule_main_table_resize(0)
        self.update_toolbar_states()

    def on_formula_changed(self, formula: str):
        """公式变化处理"""
        # 实时验证公式（支持三段式）
        if formula.strip():
            is_valid, error = validate_formula_syntax_three_segment(
                formula, self.workbook_manager
            )
            if not is_valid:
                self.log_manager.warning(f"公式语法错误: {error}")

        # 更新当前选中项的公式
        current_index = self.main_data_grid.currentIndex()
        if not current_index.isValid():
            return

        model = current_index.model()
        meta_lookup = getattr(model, "_column_meta_at", None)
        column_meta = (
            meta_lookup(current_index.column()) if callable(meta_lookup) else None
        )

        if not column_meta:
            if not callable(meta_lookup) or not self.target_model.dynamic_columns:
                return
            formula_column = len(self.target_model.static_headers)
            target_index = current_index.sibling(current_index.row(), formula_column)
        else:
            target_index = current_index

        if target_index.isValid():
            target_index.model().setData(target_index, formula, Qt.EditRole)

    def on_sheet_selected(self, sheet_name: str, sheet_type):
        """工作表选择处理"""
        self.log_manager.info(
            f"选择工作表: {sheet_name} (类型: {'快报表' if sheet_type.value == 'flash_report' else '数据来源表'})"
        )

        # 如果选择的是快报表，更新目标项模型
        if sheet_type.value == "flash_report" and self.target_model and sheet_name:
            self.target_model.set_active_sheet(sheet_name)
            self._apply_main_header_layout()

    def on_flash_report_activated(self, sheet_name: str):
        """快报表激活处理"""
        self.log_manager.info(f"激活快报表: {sheet_name}")
        # 更新目标项模型以显示该工作表的项目
        if self.target_model and sheet_name:
            self.target_model.set_active_sheet(sheet_name)
            self._apply_main_header_layout()

    def toggle_fullscreen(self):
        """切换全屏显示模式"""
        if self._is_fullscreen:
            # 退出全屏，恢复正常显示
            self._is_fullscreen = False
            self.fullscreen_btn.setText("🖥️ 全屏显示")
            self.fullscreen_btn.setChecked(False)

            # 恢复窗口状态
            if self._saved_window_state:
                self.restoreGeometry(self._saved_window_state)

            # 显示右侧工具区（main_splitter的第二个widget）
            if self.main_splitter.count() >= 2:
                self.main_splitter.widget(1).setVisible(True)

            # 显示底部日志区
            if hasattr(self, "log_container"):
                self.log_container.setVisible(True)

            # 恢复splitter比例
            if self._saved_splitter_sizes:
                self.main_splitter.setSizes(self._saved_splitter_sizes)

            self.log_manager.info("退出全屏模式")
        else:
            # 进入全屏显示
            self._is_fullscreen = True
            self.fullscreen_btn.setText("❌ 取消全屏显示")
            self.fullscreen_btn.setChecked(True)

            # 保存当前窗口状态
            self._saved_window_state = self.saveGeometry()

            # 保存splitter比例
            self._saved_splitter_sizes = self.main_splitter.sizes()

            # 窗口最大化
            self.showMaximized()

            # 隐藏右侧工具区
            if self.main_splitter.count() >= 2:
                self.main_splitter.widget(1).setVisible(False)

            # 隐藏底部日志区
            if hasattr(self, "log_container"):
                self.log_container.setVisible(False)

            self.log_manager.info("进入全屏模式：只显示主表格和来源详情")

    def on_target_sheet_changed(self, sheet_name: str):
        """处理主数据表工作表选择变化"""
        if not sheet_name or not self.target_model:
            return

        # 重置当前sheet的重试计数，防止失败状态传播
        if hasattr(self, "_main_resize_retry_counts"):
            self._main_resize_retry_counts.pop(sheet_name, None)
            self.log_manager.info(f"重置工作表'{sheet_name}'的列宽调整重试计数")

        self.log_manager.info(f"主数据表切换工作表: {sheet_name}")
        try:
            # 切换当前显示的工作表
            self.target_model.set_active_sheet(sheet_name)

            # 关键修复3：使用QTimer.singleShot确保在事件循环完成后执行header操作
            # 这确保view完全更新后才应用header布局
            QTimer.singleShot(0, lambda: self._apply_main_header_layout())

            # 清空搜索框
            if hasattr(self, "target_search_line"):
                self.target_search_line.clear()

            # 关键修复4：增加延迟以确保view完全刷新
            # 原来是100ms，现在改为300ms，给view更多时间完成异步更新
            self.schedule_main_table_resize(300)
            self._sync_analysis_context()
        except Exception as e:
            self.log_manager.error(f"切换到工作表'{sheet_name}'时出错: {e}")
            import traceback

            self.log_manager.info(traceback.format_exc())

    def filter_target_items(self, filter_text: str):
        """过滤主数据表中的待写入项（增强版：隐藏+高亮）"""
        if not self.main_data_grid.model():
            return

        model = self.main_data_grid.model()
        filter_lower = filter_text.lower()

        # 设置搜索文本到model（触发高亮）
        if hasattr(model, "set_search_text"):
            model.set_search_text(filter_lower)

        # 遍历所有行，根据筛选文本显示/隐藏
        for row in range(model.rowCount()):
            row_matched = False
            # 检查所有列是否包含搜索文本
            for col in range(model.columnCount()):
                index = model.index(row, col)
                cell_text = str(model.data(index, Qt.DisplayRole) or "")
                if filter_lower in cell_text.lower():
                    row_matched = True
                    break

            # 🔧 修复：QTreeView的setRowHidden需要三个参数(row, parent_index, hide)
            # 使用QModelIndex()作为parent表示顶层项目
            should_hide = (not row_matched) if filter_text else False
            self.main_data_grid.setRowHidden(row, QModelIndex(), should_hide)

    def clear_current_sheet_formulas(self):
        """清除当前工作表的所有公式"""
        if not self.workbook_manager:
            QMessageBox.warning(self, "提示", "请先加载文件")
            return

        # 获取当前激活的工作表名
        if (
            not hasattr(self.target_model, "active_sheet_name")
            or not self.target_model.active_sheet_name
        ):
            QMessageBox.warning(self, "提示", "请先选择一个快报表")
            return

        current_sheet = self.target_model.active_sheet_name

        # 查找当前工作表的所有目标项ID
        sheet_target_ids = [
            target_id
            for target_id, target_item in self.workbook_manager.target_items.items()
            if target_item.sheet_name == current_sheet
        ]

        # 统计当前工作表的公式数量
        formula_count = sum(
            len(self.workbook_manager.mapping_formulas.get(target_id, {}))
            for target_id in sheet_target_ids
        )

        if formula_count == 0:
            QMessageBox.information(self, "提示", f"工作表 '{current_sheet}' 没有公式")
            return

        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认操作",
            f"🗑️ 将清除工作表 '{current_sheet}' 的 {formula_count} 个公式，是否继续？\n\n"
            f"注意：此操作不会修改Excel文件，只清除程序中的映射关系。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 清除当前工作表的所有公式
            cleared_ids = []
            for target_id in sheet_target_ids:
                if target_id in self.workbook_manager.mapping_formulas:
                    self.workbook_manager.remove_mapping(target_id, None)
                    cleared_ids.append(target_id)

            # 更新界面
            if cleared_ids:
                self.handle_formula_updates(cleared_ids, reason="clear_sheet")

            self.log_manager.info(
                f"🗑️ 已清除工作表 '{current_sheet}' 的 {formula_count} 个公式"
            )

    def clear_all_formulas(self):
        """清除所有公式"""
        if not self.workbook_manager:
            return

        reply = QMessageBox.question(
            self,
            "确认操作",
            "🗑️ 将清除所有工作表的所有公式，是否继续？\n\n"
            "注意：此操作不会修改Excel文件，只清除程序中的映射关系。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            cleared_ids = (
                list(self.workbook_manager.mapping_formulas.keys())
                if self.workbook_manager
                else []
            )
            self.workbook_manager.mapping_formulas.clear()
            if self.workbook_manager:
                self.workbook_manager.calculation_results.clear()
            if cleared_ids:
                self.handle_formula_updates(cleared_ids, reason="clear_all")
            else:
                self.target_model.layoutChanged.emit()
            self.log_manager.info("已清除所有公式")

    def reset_layout(self):
        """重置布局"""
        self.log_manager.info("布局重置功能开发中...")

    def update_property_inspector(self, target_item: Optional[TargetItem]):
        """更新属性表格"""
        if not hasattr(self, "property_table"):
            return

        if not target_item:
            self.property_table.set_properties({})
            return

        properties = {
            "目标项ID": target_item.id,
            "项目名称": target_item.name,
            "所属表格": target_item.sheet_name,
            "单元格地址": target_item.cell_address,
            "数据类型": (
                "数值"
                if getattr(target_item, "data_type", "text") == "number"
                else "文本"
            ),
            "是否必填": "是" if getattr(target_item, "required", False) else "否",
        }

        if self.workbook_manager:
            column_map = self.workbook_manager.mapping_formulas.get(target_item.id, {})
            result_map = self.workbook_manager.calculation_results.get(
                target_item.id, {}
            )

            if column_map:
                column_descriptions: List[str] = []
                for column_key, mapping in column_map.items():
                    column_name = mapping.column_name or column_key
                    if mapping.formula:
                        descriptor = mapping.formula
                    elif mapping.constant_value not in (None, ""):
                        descriptor = f"常量: {mapping.constant_value}"
                    else:
                        descriptor = "未设置"

                    column_status = mapping.status.value
                    preview = ""
                    result = result_map.get(column_key)
                    if result:
                        if result.success and result.result is not None:
                            preview = f"结果: {result.result}"
                        elif result.success:
                            preview = "结果: 成功"
                        elif result.error_message:
                            preview = f"错误: {result.error_message}"
                        else:
                            preview = "错误: 计算失败"

                    parts = [descriptor, f"状态: {column_status}"]
                    if preview:
                        parts.append(preview)

                    column_descriptions.append(f"{column_name} → " + " | ".join(parts))

                properties["列映射"] = "\n".join(column_descriptions)
            else:
                properties["列映射"] = "未配置任何列映射"

        self.property_table.set_properties(properties)

    def show_target_source_message(self, message: str):
        """在来源详情面板中展示提示信息"""
        if not hasattr(self, "target_source_stack"):
            return

        self.target_source_message.setText(message)
        if hasattr(self, "_target_source_message_index"):
            self.target_source_stack.setCurrentIndex(self._target_source_message_index)

        if hasattr(self, "target_source_description"):
            self.target_source_description.setText(
                self._target_source_description_default
            )

    def refresh_target_source_summary(self):
        """根据当前选中项刷新来源详情"""
        if not hasattr(self, "target_source_stack"):
            return

        if not self.workbook_manager or not self.main_data_grid:
            self.show_target_source_message("请选择目标项以查看来源详情。")
            return

        current_index = self.main_data_grid.currentIndex()
        if not current_index.isValid():
            self.show_target_source_message("请选择目标项以查看来源详情。")
            return

        target_item = self.target_model.get_target_item(current_index)
        self.update_target_source_panel(target_item)

    def update_target_source_panel(self, target_item: Optional[TargetItem]):
        """更新左侧来源详情面板内容"""
        if not hasattr(self, "target_source_stack"):
            return

        if not target_item or not self.workbook_manager:
            self.show_target_source_message("请选择目标项以查看来源详情。")
            return

        column_map = self.workbook_manager.mapping_formulas.get(target_item.id, {})
        if isinstance(column_map, MappingFormula):
            column_map = {column_map.column_key or "__default__": column_map}
        if not column_map:
            self.show_target_source_message("当前选中项没有填写来源项。")
            return

        current_index = self.main_data_grid.currentIndex()
        target_column_key = None
        column_name = ""
        if current_index.isValid():
            column_meta = getattr(self.target_model, "_column_meta_at", None)
            if callable(column_meta):
                meta = column_meta(current_index.column())
                if meta and meta["key"] in column_map:
                    target_column_key = meta["key"]
                    column_name = meta["name"]

        mapping = None
        if target_column_key:
            mapping = column_map.get(target_column_key)

        if not mapping or not mapping.formula:
            # 回退到第一个有公式的列
            for key, candidate in column_map.items():
                if candidate.formula:
                    mapping = candidate
                    target_column_key = key
                    column_name = candidate.column_name or key
                    break

        if not mapping or not mapping.formula:
            self.show_target_source_message("当前选中列没有填写来源项。")
            return

        # ⭐ 使用三段式解析（新版）
        references = parse_formula_references_three_segment(mapping.formula)

        if not references:
            self.show_target_source_message("当前映射公式未包含来源引用。")
            return

        seen_keys = set()
        sources_info: List[Dict[str, Any]] = []

        for ref in references:
            # ⭐ 三段式：使用full_reference或构建唯一key
            ref_key = (
                ref.get("full_reference")
                or f"{ref.get('sheet_name')}::{ref.get('item_name')}::{ref.get('column_name')}"
            )
            if ref_key in seen_keys:
                continue
            seen_keys.add(ref_key)
            sources_info.append(self._build_source_reference_info(ref))

        if not sources_info:
            self.show_target_source_message(
                "未能在来源项库中找到对应的来源，请检查映射设置。"
            )
            return

        self._active_formula_column = target_column_key
        self._render_target_source_table(target_item, sources_info)

    def _build_source_reference_info(self, reference: Dict[str, Any]) -> Dict[str, Any]:
        """构建来源引用信息（支持三段式）"""
        sheet_name = reference.get("sheet_name", "")
        item_name = reference.get("item_name") or ""

        # ⭐ 三段式：使用column_name而不是column_key
        column_name = reference.get("column_name")  # 三段式的列名
        column_key = reference.get("column_key")  # 旧格式的column_key（可能为None）
        cell_address = reference.get("cell_address", "")

        candidates = self._find_source_candidates(sheet_name, item_name, cell_address)
        source_item = candidates[0] if candidates else None

        # 优先使用column_name（三段式），回退到column_key（旧格式）
        column_label = column_name or column_key or "主要数值"
        column_description = ""
        raw_value: Any = None

        if source_item:
            # ⭐ 三段式：从values字典获取值（column_name作为key）
            if (
                column_name
                and hasattr(source_item, "values")
                and isinstance(source_item.values, dict)
            ):
                # 对列名进行strip比对查找
                column_name_stripped = (
                    column_name.strip() if isinstance(column_name, str) else column_name
                )
                for col_key, col_value in source_item.values.items():
                    col_key_stripped = (
                        col_key.strip() if isinstance(col_key, str) else col_key
                    )
                    if col_key_stripped == column_name_stripped:
                        raw_value = col_value
                        column_label = col_key  # 使用原始key（保留空格）
                        break
            # 回退：旧格式column_key
            elif column_key:
                if hasattr(source_item, "data_columns"):
                    raw_value = source_item.data_columns.get(column_key)
                if hasattr(source_item, "column_info"):
                    column_description = source_item.column_info.get(column_key, "")
            # 回退：使用主值
            else:
                raw_value = getattr(source_item, "value", None)

        formatted_value = self._format_source_value(raw_value)
        column_display = column_label
        if column_description:
            column_display = f"{column_label} ({column_description})"

        header_text = self._format_source_header(
            source_item, sheet_name, item_name, column_key or column_name
        )

        return {
            "header": header_text,
            "sheet": source_item.sheet_name if source_item else sheet_name or "-",
            "level": str(source_item.hierarchy_level) if source_item else "-",
            "item": source_item.name if source_item else item_name or "-",
            "identifier": source_item.identifier if source_item and source_item.identifier else "-",
            "account_code": source_item.account_code if source_item else "-",
            "column": column_display,
            "cell": source_item.cell_address if source_item else cell_address or "-",
            "value": formatted_value,
            "is_numeric": isinstance(raw_value, (int, float)),
            "missing": source_item is None,
        }

    def _render_target_source_table(
        self, target_item: TargetItem, sources_info: List[Dict[str, Any]]
    ):
        if not hasattr(self, "target_source_table"):
            return

        # 🔧 直接使用source_info中的键来构建attributes，确保与数据结构匹配
        attributes = [
            ("工作表", "sheet", lambda info: info.get("sheet", "-")),
            ("项目名称", "item", lambda info: info.get("item", "-")),
            ("标识符", "identifier", lambda info: info.get("identifier", "-")),
            ("科目代码", "account_code", lambda info: info.get("account_code", "-")),
            ("数据列", "column", lambda info: info.get("column", "-")),
            ("单元格", "cell", lambda info: info.get("cell", "-")),
            ("数值", "value", lambda info: info.get("value", "-")),
        ]

        self.target_source_table.clear()
        # 🔧 转置显示：行为不同的来源，列为各种属性
        self.target_source_table.setRowCount(len(sources_info))
        self.target_source_table.setColumnCount(len(attributes))

        # 列头显示为属性名
        self.target_source_table.setHorizontalHeaderLabels(
            [label for label, _, _ in attributes]
        )
        # 行头显示为来源编号（第1项、第2项...）
        self.target_source_table.setVerticalHeaderLabels(
            [f"第{i+1}项" for i in range(len(sources_info))]
        )

        # 填充数据：遍历每个来源（行），然后填充各个属性（列）
        for row, info in enumerate(sources_info):
            for col, (_, key, value_getter) in enumerate(attributes):
                display_value = value_getter(info)
                item = QTableWidgetItem(display_value)

                # 检查是否为数值类型
                is_numeric = isinstance(display_value, (int, float)) or (
                    isinstance(display_value, str)
                    and display_value.replace(".", "", 1)
                    .replace(",", "")
                    .replace("-", "", 1)
                    .isdigit()
                )

                if is_numeric:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                if info.get("missing"):
                    item.setForeground(QBrush(QColor("#c0392b")))

                item.setToolTip(display_value)
                self.target_source_table.setItem(row, col, item)

        header = self.target_source_table.horizontalHeader()
        ensure_interactive_header(header, stretch_last=False)
        # 设置所有列为Interactive模式，允许自动调整
        for column in range(self.target_source_table.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
        # 触发自动列宽调整
        QTimer.singleShot(100, self.target_source_table._auto_adjust_columns)
        # ⭐ 不自动调整行高，保持用户设置的30px默认行高
        # schedule_row_resize(self.target_source_table, 60)  # 注释掉，避免覆盖用户设置

        # ⭐ 强制设置所有行为40px高度，确保数据更新后行高保持固定
        v_header = self.target_source_table.verticalHeader()
        for row in range(self.target_source_table.rowCount()):
            v_header.resizeSection(row, 40)

        if hasattr(self, "_target_source_table_index"):
            self.target_source_stack.setCurrentIndex(self._target_source_table_index)

        if hasattr(self, "target_source_description"):
            missing_count = sum(1 for info in sources_info if info.get("missing"))
            total_sources = len(sources_info)

            ai_status = "未经过"
            confidence_text = "--"
            reasoning_text = "--"

            if self.workbook_manager:
                active_column = getattr(self, "_active_formula_column", None) or "__default__"
                mapping_obj = self.workbook_manager.get_mapping(target_item.id, active_column)
                if mapping_obj:
                    try:
                        confidence_value = float(mapping_obj.ai_confidence)
                        confidence_value = max(0.0, min(1.0, confidence_value))
                        confidence_text = f"{confidence_value * 100:.2f}%"
                    except (TypeError, ValueError):
                        confidence_text = "--"

                    if mapping_obj.ai_reasoning:
                        reasoning_text = self._shorten_text(mapping_obj.ai_reasoning, 120)

                    if (
                        mapping_obj.status == FormulaStatus.AI_GENERATED
                        or confidence_text != "--"
                        or mapping_obj.ai_reasoning
                    ):
                        ai_status = "经过"

            # 使用HTML格式化文本，添加间距和下划线
            summary_lines: List[str] = []
            line_style = "font-size:13px;color:#000;margin-bottom:12px;"

            confidence_display = confidence_text if confidence_text != "--" else confidence_text
            reasoning_display = reasoning_text if reasoning_text != "--" else reasoning_text

            separator = '；' + '&nbsp;' * 10
            summary_lines.append(
                f'<div style="{line_style}">来源数量：<u>{total_sources}个</u>'
                f'{separator}'
                f'AI回报回归率：<u>{confidence_display}</u></div>'
            )

            summary_lines.append(
                f'<div style="{line_style}">当前项经过AI解析状态：<u>{ai_status}</u>'
                f'{separator}'
                f'AI认为回报率理由为：<u>{reasoning_display}</u></div>'
            )

            if missing_count:
                summary_lines.append(
                    f'<div style="{line_style}color:#ff6b6b;">存在<u>{missing_count}个</u>来源缺失</div>'
                )

            summary = "".join(summary_lines)

            self.target_source_description.setText(summary)

    def _extract_source_value_for_key(
        self, source_info: Dict[str, Any], column_key: str
    ) -> str:
        """从source_info中提取特定列的值"""
        # 先尝试从source_info直接获取（可能已经预处理过）
        if column_key in source_info:
            value = source_info[column_key]
            return self._format_source_value(value)

        # 尝试获取source_item对象
        source_item = source_info.get("source_item")
        if not source_item:
            # 如果没有source_item，说明是missing的来源
            return "-"

        # 从source_item的data_columns获取
        if hasattr(source_item, "data_columns"):
            value = source_item.data_columns.get(column_key)
            if value is not None:
                return self._format_source_value(value)

        # 尝试从常见属性获取
        attr_mapping = {
            "name": ["name", "名称", "项目名称", "项目"],
            "hierarchy_level": ["hierarchy_level", "level", "层级", "级别"],
            "account_code": ["account_code", "code", "科目代码", "代码"],
            "sheet_name": ["sheet_name", "sheet", "工作表"],
            "value": ["value", "main_value", "数值", "值"],
        }

        for attr, possible_keys in attr_mapping.items():
            if column_key in possible_keys:
                value = getattr(source_item, attr, None)
                if value is not None:
                    return self._format_source_value(value)

        return "-"

    def _format_source_value(self, value: Any) -> str:
        if value is None or value == "":
            return "-"

        if isinstance(value, (int, float)):
            if value == 0:
                return "0"
            if abs(value) >= 10000:
                return f"{value:,.0f}"
            return f"{value:,.2f}"

        return str(value)

    def _format_source_header(
        self,
        source_item: Optional[SourceItem],
        sheet_name: str,
        item_name: str,
        column_key: Optional[str],
    ) -> str:
        if source_item:
            base_name = f"{source_item.sheet_name} · {source_item.name}"
        else:
            display_item = item_name or "?"
            base_name = f"{sheet_name or '-'} · {display_item}"

        if column_key:
            base_name = f"{base_name} | {column_key}"

        return base_name

    def _shorten_text(self, text: str, max_length: int = 36) -> str:
        if not text:
            return "-"
        text = str(text)
        if len(text) <= max_length:
            return text
        return f"{text[:max_length - 1]}…"

    def _rebuild_source_lookup_index(self):
        self._source_lookup_index = {}
        if not self.workbook_manager:
            return

        for source_item in self.workbook_manager.source_items.values():
            key = (
                getattr(source_item, "sheet_name", ""),
                getattr(source_item, "name", ""),
            )
            if key not in self._source_lookup_index:
                self._source_lookup_index[key] = []
            self._source_lookup_index[key].append(source_item)

    def _find_source_candidates(
        self, sheet_name: str, item_name: str, cell_address: Optional[str] = None
    ) -> List[SourceItem]:
        if not self._source_lookup_index:
            self._rebuild_source_lookup_index()

        key = (sheet_name, item_name)
        if key in self._source_lookup_index:
            return self._source_lookup_index[key]

        alt_key = (
            sheet_name.strip() if sheet_name else sheet_name,
            item_name.strip() if item_name else item_name,
        )
        matches = self._source_lookup_index.get(alt_key, [])

        if matches or not cell_address:
            return matches

        normalized_cell = cell_address.strip().upper()
        fallback: List[SourceItem] = []
        if self.workbook_manager:
            for source in self.workbook_manager.source_items.values():
                if (
                    getattr(source, "sheet_name", "") == sheet_name
                    and getattr(source, "cell_address", "").upper() == normalized_cell
                ):
                    fallback.append(source)

        return fallback

    def show_context_menu(self, position):
        """显示右键上下文菜单"""
        index = self.main_data_grid.indexAt(position)
        if not index.isValid():
            return

        column_meta_lookup = getattr(self.target_model, "_column_meta_at", None)
        self._active_formula_column = None
        if callable(column_meta_lookup):
            meta = column_meta_lookup(index.column())
            if meta:
                self._active_formula_column = meta.get("key")

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
            _, formula_obj = self._get_mapping_for_item(
                selected_item, self._active_formula_column
            )
            has_formula = bool(
                formula_obj and formula_obj.formula and formula_obj.formula.strip()
            )

            copy_action = menu.addAction("📋 复制公式", self.copy_formula)
            delete_action = menu.addAction("🗑️ 删除公式", self.delete_formula)
            validate_action = menu.addAction("✅ 验证公式", self.validate_formula)

            if not has_formula:
                tooltip = "当前项目暂无公式"
                for action in (copy_action, delete_action, validate_action):
                    action.setEnabled(False)
                    action.setToolTip(tooltip)
            else:
                copy_action.setToolTip("复制该项目的映射公式")
                delete_action.setToolTip("删除该项目的映射公式")
                validate_action.setToolTip("验证该项目公式的语法")

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
        status_menu.addAction(
            "标记为待处理", lambda: self.batch_set_status(FormulaStatus.PENDING)
        )
        status_menu.addAction(
            "标记为已验证", lambda: self.batch_set_status(FormulaStatus.VALIDATED)
        )
        status_menu.addAction(
            "标记为错误", lambda: self.batch_set_status(FormulaStatus.ERROR)
        )

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
            if hasattr(self.target_model, "get_target_item"):
                item = self.target_model.get_target_item(index)
                if item:
                    selected_items.append(item)

        return selected_items

    def _get_mapping_for_item(
        self, target_item: TargetItem, preferred_column: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[MappingFormula]]:
        if not self.workbook_manager:
            return None, None

        column_map = self.workbook_manager.mapping_formulas.get(target_item.id, {})
        if isinstance(column_map, MappingFormula):
            return column_map.column_key or "__default__", column_map

        if not column_map:
            return None, None

        if preferred_column and preferred_column in column_map:
            return preferred_column, column_map[preferred_column]

        # 优先返回有公式的列
        for key, mapping in column_map.items():
            if mapping.formula:
                return key, mapping

        # 否则返回任意列
        key, mapping = next(iter(column_map.items()))
        return key, mapping

    def _iter_mappings_for_item(self, target_item: TargetItem):
        if not self.workbook_manager:
            return []
        column_map = self.workbook_manager.mapping_formulas.get(target_item.id, {})
        if isinstance(column_map, MappingFormula):
            return [(column_map.column_key or "__default__", column_map)]
        return list(column_map.items())

    def edit_formula(self):
        """编辑公式 - 使用专用的公式编辑对话框"""
        selected_items = self.get_selected_target_items()
        if len(selected_items) == 1:
            target_item = selected_items[0]
            self.log_manager.info(f"📝 编辑公式: {target_item.name}")

            current_index = self.main_data_grid.currentIndex()
            column_meta_lookup = getattr(self.target_model, "_column_meta_at", None)
            meta = (
                column_meta_lookup(current_index.column())
                if current_index.isValid() and callable(column_meta_lookup)
                else None
            )

            column_key = meta["key"] if meta else None
            column_name = meta["name"] if meta else None

            if not column_key:
                column_key, mapping = self._get_mapping_for_item(
                    target_item, self._active_formula_column
                )
                column_name = (
                    (mapping.column_name if mapping else None)
                    or column_key
                    or "__default__"
                )
            else:
                mapping = self.workbook_manager.get_mapping(target_item.id, column_key)

            self._active_formula_column = column_key or "__default__"

            dialog = FormulaEditDialog(
                target_item,
                self.workbook_manager,
                self,
                column_key=self._active_formula_column,
                column_name=column_name or self._active_formula_column,
            )

            if dialog.exec() == QDialog.Accepted:
                self.handle_formula_updates([target_item.id], reason="dialog")
        else:
            self.log_manager.warning("请选择一个目标项进行公式编辑")

    def view_details(self):
        """查看详情"""
        selected_items = self.get_selected_target_items()
        if len(selected_items) == 1:
            target_item = selected_items[0]

            # 获取公式信息
            formula_lines: List[str] = []
            for column_key, mapping in self._iter_mappings_for_item(target_item):
                formula_text = mapping.formula or (
                    f"常量 {mapping.constant_value}"
                    if mapping.constant_value not in (None, "")
                    else "(空)"
                )
                status = mapping.status.value
                line = f"{mapping.column_name or column_key}: {formula_text} | 状态: {status}"
                if mapping.validation_error:
                    line += f" | 错误: {mapping.validation_error}"
                formula_lines.append(line)

            formula_info = "\n".join(formula_lines) if formula_lines else "无公式"

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
        if len(selected_items) != 1 or not self.workbook_manager:
            return

        target_item = selected_items[0]
        column_key, mapping = self._get_mapping_for_item(
            target_item, self._active_formula_column
        )

        if not mapping:
            self.log_manager.warning("当前项目没有可复制的公式")
            return

        value_text = mapping.formula or (
            str(mapping.constant_value)
            if mapping.constant_value not in (None, "")
            else ""
        )
        if not value_text:
            self.log_manager.warning("当前列没有可复制的公式或常量")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(value_text)
        self.copied_formulas = [
            {
                "column_key": column_key,
                "column_name": mapping.column_name or column_key,
                "formula": mapping.formula,
                "constant": mapping.constant_value,
            }
        ]
        self.log_manager.info(f"📋 已复制公式: {value_text}")

    def delete_formula(self):
        """删除公式"""
        selected_items = self.get_selected_target_items()
        if len(selected_items) != 1 or not self.workbook_manager:
            return

        target_item = selected_items[0]
        column_key, mapping = self._get_mapping_for_item(
            target_item, self._active_formula_column
        )

        if not mapping or (
            not mapping.formula and mapping.constant_value in (None, "")
        ):
            self.log_manager.warning("当前项目没有可删除的公式")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除项目 '{target_item.name}' 的列映射（{mapping.column_name or column_key}）吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.workbook_manager.remove_mapping(target_item.id, column_key)
            self.handle_formula_updates([target_item.id], reason="delete")
            self.log_manager.info(
                f"🗑️ 已删除公式: {target_item.name} · {mapping.column_name or column_key}"
            )

    def validate_formula(self):
        """验证公式"""
        selected_items = self.get_selected_target_items()
        if len(selected_items) != 1 or not self.workbook_manager:
            return

        target_item = selected_items[0]
        column_key, mapping = self._get_mapping_for_item(
            target_item, self._active_formula_column
        )

        if not mapping or not mapping.formula:
            self.log_manager.warning("当前项目没有可验证的公式")
            return

        is_valid, error_msg = validate_formula_syntax_three_segment(
            mapping.formula, self.workbook_manager
        )

        if is_valid:
            mapping.set_validation_result(True, "")
            self.log_manager.success(f"✅ 公式验证通过: {mapping.formula}")
        else:
            mapping.set_validation_result(False, error_msg)
            self.log_manager.error(f"❌ 公式验证失败: {error_msg}")
            QMessageBox.warning(self, "验证失败", f"公式存在语法问题:\n{error_msg}")

        index = self.target_model.get_index_for_target(target_item.id, 0)
        if index.isValid():
            left = index.sibling(index.row(), 0)
            right = index.sibling(index.row(), self.target_model.columnCount() - 1)
            self.target_model.dataChanged.emit(left, right, [Qt.DisplayRole])

        if self.main_data_grid.currentIndex().isValid():
            current_item = self.target_model.get_target_item(
                self.main_data_grid.currentIndex()
            )
            if current_item and current_item.id == target_item.id:
                self.update_property_inspector(current_item)

    def insert_formula_example(self):
        """在公式编辑器中插入示例公式"""
        if not hasattr(self, "formula_editor") or not self.formula_editor:
            return

        sample_formula = "[利润表]A12 + [上年科目余额表]A4"
        cursor = self.formula_editor.textCursor()
        if cursor.position() > 0:
            cursor.insertText(
                " "
                if not self.formula_editor.toPlainText().endswith((" ", "\n"))
                else ""
            )
        cursor.insertText(sample_formula)
        self.formula_editor.setTextCursor(cursor)
        self.log_manager.info(f"💡 已插入示例公式: {sample_formula}")

    def on_main_grid_double_clicked(self, index: QModelIndex):
        """主数据网格双击事件处理 - 只允许数据列编辑公式"""
        if not index.isValid():
            return

        column = index.column()
        target_item = self.target_model.get_target_item(index)
        if not target_item:
            return

        column_meta_lookup = getattr(self.target_model, "_column_meta_at", None)
        meta = column_meta_lookup(column) if callable(column_meta_lookup) else None

        # ✅ 明确排除不可编辑的列（基于列名）
        if meta:
            column_name = meta.get("name", "")

            # 项目列、行次列、状态列、级别列不允许编辑公式
            non_editable_columns = ["项目", "行次", "状态", "级别"]

            if column_name in non_editable_columns:
                self.log_manager.info(f"'{column_name}'列不支持编辑公式")
                return

            # 其他列：检查is_data_column
            if meta.get("is_data_column", False):
                column_key = meta["key"]
                self._active_formula_column = column_key

                self.log_manager.info(
                    f"双击编辑公式: {target_item.name} · {column_name}"
                )

                dialog = FormulaEditDialog(
                    target_item,
                    self.workbook_manager,
                    self,
                    column_key=column_key,
                    column_name=column_name,
                )
                if dialog.exec() == QDialog.Accepted:
                    self.handle_formula_updates([target_item.id], reason="dialog")
            else:
                # 非数据列
                self.log_manager.info(f"'{column_name}'列不支持编辑公式")
        else:
            # 双击静态列，显示详情
            self.log_manager.info(f"双击查看详情: {target_item.name}")
            self.view_details()

    def batch_ai_mapping(self):
        """批量AI映射"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        reply = QMessageBox.question(
            self,
            "确认操作",
            f"🤖 将对选中的 {len(selected_items)} 个项目执行AI映射，是否继续？",
            QMessageBox.Yes | QMessageBox.No,
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

        copied_entries: List[Dict[str, Any]] = []
        for item in selected_items:
            column_key, mapping = self._get_mapping_for_item(
                item, self._active_formula_column
            )
            if mapping and (
                mapping.formula or mapping.constant_value not in (None, "")
            ):
                copied_entries.append(
                    {
                        "column_key": column_key,
                        "column_name": mapping.column_name or column_key,
                        "formula": mapping.formula,
                        "constant": mapping.constant_value,
                    }
                )

        if copied_entries:
            self.copied_formulas = copied_entries
            clipboard_text = "\n".join(
                entry["formula"] if entry["formula"] else str(entry["constant"])
                for entry in copied_entries
            )
            QApplication.clipboard().setText(clipboard_text)
            self.log_manager.info(f"📋 已复制 {len(copied_entries)} 个公式/常量")

    def paste_formulas(self):
        """粘贴公式"""
        if not hasattr(self, "copied_formulas") or not self.copied_formulas:
            QMessageBox.information(self, "提示", "没有可粘贴的公式")
            return

        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        count = 0
        updated_ids: List[str] = []
        entry_count = len(self.copied_formulas)
        for i, item in enumerate(selected_items):
            entry = self.copied_formulas[min(i, entry_count - 1)]
            column_key = entry["column_key"] or "__default__"
            column_name = entry.get("column_name", column_key)

            mapping = self.workbook_manager.ensure_mapping(
                item.id, column_key, column_name
            )
            if entry.get("formula"):
                mapping.update_formula(
                    entry["formula"],
                    status=FormulaStatus.USER_MODIFIED,
                    column_name=column_name,
                )
                mapping.constant_value = None
            else:
                mapping.update_formula(
                    "", status=FormulaStatus.USER_MODIFIED, column_name=column_name
                )
                mapping.constant_value = entry.get("constant")
            mapping.validation_error = ""
            count += 1
            updated_ids.append(item.id)

        self.log_manager.info(f"📋 已粘贴 {count} 个公式")
        if updated_ids:
            self.handle_formula_updates(updated_ids, reason="paste")

    def clear_formulas(self):
        """清空公式"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        reply = QMessageBox.question(
            self,
            "确认操作",
            f"🗑️ 将清空选中的 {len(selected_items)} 个项目的公式，是否继续？",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            count = 0
            cleared_ids: List[str] = []
            for item in selected_items:
                if not self.workbook_manager:
                    continue

                if self._active_formula_column:
                    if self.workbook_manager.get_mapping(
                        item.id, self._active_formula_column
                    ):
                        self.workbook_manager.remove_mapping(
                            item.id, self._active_formula_column
                        )
                        count += 1
                        cleared_ids.append(item.id)
                else:
                    if item.id in self.workbook_manager.mapping_formulas:
                        self.workbook_manager.remove_mapping(item.id, None)
                        count += 1
                        cleared_ids.append(item.id)

            self.log_manager.info(f"🗑️ 已清空 {count} 个列映射")
            if cleared_ids:
                self.handle_formula_updates(cleared_ids, reason="clear")

    def batch_set_status(self, status: FormulaStatus):
        """批量设置状态"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        count = 0
        for item in selected_items:
            for _, mapping in self._iter_mappings_for_item(item):
                mapping.status = status
                count += 1

        status_text = {
            FormulaStatus.PENDING: "待处理",
            FormulaStatus.VALIDATED: "已验证",
            FormulaStatus.ERROR: "错误",
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

        target_ids = [
            item.id for item in selected_items if self._iter_mappings_for_item(item)
        ]
        if not target_ids:
            self.log_manager.warning("🧮 选中的项目中没有可计算的公式")
            return

        self.handle_formula_updates(target_ids, reason="batch")

    def perform_batch_validation(self, selected_items: List[TargetItem]):
        """执行批量验证"""
        if not self.workbook_manager:
            return

        valid_count = 0
        for item in selected_items:
            for _, mapping in self._iter_mappings_for_item(item):
                if not mapping.formula:
                    continue
                is_valid, _ = validate_formula_syntax_three_segment(
                    mapping.formula, self.workbook_manager
                )
                if is_valid:
                    mapping.status = FormulaStatus.VALIDATED
                    mapping.validation_error = ""
                    valid_count += 1
                else:
                    mapping.status = FormulaStatus.ERROR

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
        self.log_manager.info(
            f"📋 模板 '{template_name}' 已应用到 {applied_count} 个项目"
        )
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
            self,
            "确认操作",
            f"🔧 将重置选中的 {len(selected_items)} 个项目的映射关系，是否继续？",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            count = 0
            cleared_ids: List[str] = []
            for item in selected_items:
                for column_key, mapping in self._iter_mappings_for_item(item):
                    mapping.update_formula(
                        "", status=FormulaStatus.EMPTY, column_name=mapping.column_name
                    )
                    mapping.constant_value = None
                    mapping.calculation_result = None
                    mapping.last_calculated = None
                    mapping.validation_error = ""
                    count += 1
                    if item.id not in cleared_ids:
                        cleared_ids.append(item.id)

            self.log_manager.info(f"🔧 已重置 {count} 个映射关系")
            if cleared_ids:
                self.handle_formula_updates(cleared_ids, reason="reset")

    def find_references(self):
        """查找引用关系"""
        selected_items = self.get_selected_target_items()
        if not selected_items:
            return

        self.log_manager.info(f"🔧 查找 {len(selected_items)} 个项目的引用关系")

    def refresh_main_table(self):
        """刷新主表格"""
        if hasattr(self, "target_model") and self.target_model:
            self.target_model.layoutChanged.emit()
        self.schedule_main_table_resize(0)

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

    def _initialize_ai_service(self):
        """初始化 AI 服务配置"""
        try:
            # 从配置文件加载或使用默认值
            # TODO: 实现配置文件读取
            default_config = ProviderConfig(
                api_key="UFXLzCFM2BtvfvAc1ZC5zRkJLPJKvFlKeBKYfI5evJNqMO7t",  # Gemini转发服务
                base_url="https://api.kkyyxx.xyz/v1",
                model="gemini-2.5-pro",
                temperature=0.3,
                max_tokens=2000,
                timeout=30
            )

            # 初始化控制器
            self.chat_controller.initialize(default_config)

        except Exception as e:
            print(f"AI 服务初始化警告: {e}")
            # 不阻止程序启动，仅记录警告

    def show_ai_assistant(self):
        """显示 AI 分析助手对话窗口"""
        try:
            self.chat_controller.show_chat_window()
        except Exception as e:
            QMessageBox.warning(
                self,
                "AI 助手错误",
                f"无法启动 AI 助手:\n{str(e)}\n\n请检查 API 配置。"
            )

    def _on_main_analysis_auto_parse(self):
        """主界面分析面板：一键解析"""
        if not self.chat_controller:
            QMessageBox.warning(self, "提示", "AI服务未初始化")
            return

        # 显示AI助手窗口并触发一键解析
        self.chat_controller.show_chat_window()
        # 触发AI助手窗口的一键解析功能
        if self.chat_controller.chat_window:
            # 通过信号触发
            self.chat_controller.chat_window.sidebar.analysis_auto_parse_requested.emit()

    def _on_main_analysis_export_json(self):
        """主界面分析面板：导出JSON"""
        if not self.chat_controller:
            QMessageBox.warning(self, "提示", "AI服务未初始化")
            return

        # 直接调用chat_controller的导出JSON方法
        self.chat_controller._on_analysis_export_json_requested()

    def _on_main_analysis_apply(self):
        """主界面分析面板：解析应用"""
        if not self.chat_controller:
            QMessageBox.warning(self, "提示", "AI服务未初始化")
            return

        # 直接调用chat_controller的解析应用方法
        self.chat_controller._on_analysis_apply_requested()

    def show_about(self):
        """显示关于信息"""
        QMessageBox.about(
            self,
            "关于",
            "AI辅助财务报表数据映射与填充工具\n"
            "版本: PySide6 v1.0\n"
            "基于程序要求.md开发",
        )

    def load_settings(self):
        """加载设置"""
        try:
            # AI配置现在由ChatController管理,这里不再需要加载
            pass
        except:
            pass

    def save_settings(self):
        """保存设置"""
        try:
            # AI配置现在由ChatController管理,这里不再需要保存
            pass
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

    # 设置应用程序图标（关键！这样所有窗口都会使用这个图标）
    icon_path = Path("icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

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
        self.template_list.setHorizontalHeaderLabels(
            ["模板名称", "来源表格", "映射数量", "创建时间"]
        )
        template_header = self.template_list.horizontalHeader()
        ensure_interactive_header(template_header, stretch_last=True)
        ensure_word_wrap(self.template_list)
        self.template_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.template_list.setAlternatingRowColors(True)
        # 应用统一的网格线样式
        self.template_list.setStyleSheet(TABLE_GRID_STYLE)
        self.template_list.setShowGrid(True)  # 确保显示网格线
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
        self.target_sheet_combo.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        self.target_sheet_combo.setMinimumWidth(200)
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
        mapping_preview_header = self.mapping_preview.horizontalHeader()
        ensure_interactive_header(mapping_preview_header, stretch_last=True)
        ensure_word_wrap(self.mapping_preview)
        # 应用统一的网格线样式
        self.mapping_preview.setStyleSheet(TABLE_GRID_STYLE)
        self.mapping_preview.setShowGrid(True)  # 确保显示网格线
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
            time_item = QTableWidgetItem(
                template.created_time.strftime("%Y-%m-%d %H:%M")
            )
            self.template_list.setItem(row, 3, time_item)

        self.template_list.resizeColumnsToContents()
        template_header = self.template_list.horizontalHeader()
        ensure_interactive_header(template_header, stretch_last=True)
        for column in range(self.template_list.columnCount()):
            template_header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            self.template_list.resizeColumnToContents(column)
            template_header.setSectionResizeMode(column, QHeaderView.Interactive)
        schedule_row_resize(self.template_list, 60)

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
            schedule_row_resize(self.mapping_preview, 40)

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
        preview_header = self.mapping_preview.horizontalHeader()
        ensure_interactive_header(preview_header, stretch_last=True)
        for column in range(self.mapping_preview.columnCount()):
            preview_header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            self.mapping_preview.resizeColumnToContents(column)
            preview_header.setSectionResizeMode(column, QHeaderView.Interactive)

    def update_target_sheets(self):
        """更新目标表格下拉框"""
        self.target_sheet_combo.clear()

        if self.workbook_manager:
            # 添加所有快报表（使用安全辅助函数）
            for sheet_name, _ in self._safe_iterate_sheets(
                self.workbook_manager.flash_report_sheets
            ):
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
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                template = MappingTemplate.from_dict(data)
                self.template_manager.add_template(template)
                self.template_manager.save_to_file()
                self.refresh_template_list()

                QMessageBox.information(
                    self, "成功", f"模板 '{template.name}' 导入成功"
                )

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
                with open(file_path, "w", encoding="utf-8") as f:
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
            self,
            "确认应用",
            f"将模板 '{template.name}' 应用到表格 '{target_sheet}'？\n"
            f"包含 {len(template.mappings)} 个映射关系。",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            applied_count = self.template_manager.apply_template_to_sheet(
                template, self.workbook_manager, target_sheet
            )

            QMessageBox.information(
                self,
                "应用完成",
                f"成功应用 {applied_count} 个映射关系到表格 '{target_sheet}'",
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
                self,
                "确认删除",
                f"确定要删除模板 '{template.name}' 吗？\n此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
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
        self.source_sheet_combo.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        self.source_sheet_combo.setMinimumWidth(200)
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
                    sheet_name = getattr(sheet, "name", str(sheet))
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
                self,
                "警告",
                f"表格 '{source_sheet}' 中没有找到映射关系。\n是否仍要创建空模板？",
                QMessageBox.Yes | QMessageBox.No,
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
        mapping_header = self.mapping_table.horizontalHeader()
        ensure_interactive_header(mapping_header, stretch_last=False)
        for column in range(self.mapping_table.columnCount()):
            mapping_header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            self.mapping_table.resizeColumnToContents(column)
            mapping_header.setSectionResizeMode(column, QHeaderView.Interactive)
        ensure_word_wrap(self.mapping_table)
        # 应用统一的网格线样式
        self.mapping_table.setStyleSheet(TABLE_GRID_STYLE)
        self.mapping_table.setShowGrid(True)  # 确保显示网格线
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
        schedule_row_resize(self.mapping_table, 60)
        mapping_header = self.mapping_table.horizontalHeader()
        ensure_interactive_header(mapping_header, stretch_last=False)
        for column in range(self.mapping_table.columnCount()):
            mapping_header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            self.mapping_table.resizeColumnToContents(column)
            mapping_header.setSectionResizeMode(column, QHeaderView.Interactive)

    def delete_mapping(self, row: int):
        """删除映射"""
        self.mapping_table.removeRow(row)
        schedule_row_resize(self.mapping_table, 40)

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
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin: 10px; color: #2E86AB;"
        )
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 说明
        info_label = QLabel(
            f"文件：{self.workbook_manager.file_name}\n"
            "请确认每个工作表的分类。您可以调整系统的自动识别结果，或取消不需要的工作表。"
        )
        info_label.setStyleSheet(
            "color: #666; font-size: 12px; margin: 10px; padding: 10px; border: 1px solid #dee2e6; border-radius: 5px;"
        )
        layout.addWidget(info_label)

        # 创建表格
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor

        self.sheets_table = QTableWidget()
        self.sheets_table.setColumnCount(4)
        self.sheets_table.setHorizontalHeaderLabels(
            ["工作表名称", "系统建议", "用户分类", "是否启用"]
        )

        # 设置表格属性
        header = self.sheets_table.horizontalHeader()
        ensure_interactive_header(header, stretch_last=False)
        for column in range(4):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            self.sheets_table.resizeColumnToContents(column)
            header.setSectionResizeMode(column, QHeaderView.Interactive)
        header.setStretchLastSection(False)

        self.sheets_table.setAlternatingRowColors(True)
        self.sheets_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sheets_table.verticalHeader().setVisible(False)
        ensure_word_wrap(self.sheets_table)
        # 应用统一的网格线样式
        self.sheets_table.setStyleSheet(TABLE_GRID_STYLE)
        self.sheets_table.setShowGrid(True)  # 确保显示网格线

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
        self.confirm_btn.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; font-weight: bold; padding: 8px 16px; }"
        )
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
                "suggestion": suggestion,
                "combo": classification_combo,
                "checkbox": enable_checkbox,
                "original_type": sheet_type,
            }

        self.update_stats()
        self.sheets_table.resizeColumnsToContents()
        header = self.sheets_table.horizontalHeader()
        column_limits = {0: (240, 420), 1: (120, 200), 2: (140, 260), 3: (100, 160)}
        for column, (min_w, max_w) in column_limits.items():
            current_width = self.sheets_table.columnWidth(column)
            bounded_width = max(min_w, min(current_width, max_w))
            self.sheets_table.setColumnWidth(column, bounded_width)
            header.setSectionResizeMode(column, QHeaderView.Interactive)

        ensure_word_wrap(self.sheets_table)
        schedule_row_resize(self.sheets_table, 60)

    def update_stats(self):
        """更新统计信息"""
        flash_report_count = 0
        data_source_count = 0
        skip_count = 0
        enabled_count = 0

        for sheet_name, info in self.sheet_classifications.items():
            if info["checkbox"].isChecked():
                enabled_count += 1
                classification = info["combo"].currentText()
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
            info["checkbox"].setChecked(True)

    def deselect_all_sheets(self):
        """取消选择所有工作表"""
        for info in self.sheet_classifications.values():
            info["checkbox"].setChecked(False)

    def use_auto_classification(self):
        """使用系统自动分类"""
        for info in self.sheet_classifications.values():
            info["combo"].setCurrentText(info["suggestion"])

    def confirm_classifications(self):
        """确认分类设置"""
        # 检查是否至少启用了一个工作表
        enabled_sheets = [
            name
            for name, info in self.sheet_classifications.items()
            if info["checkbox"].isChecked()
        ]

        if not enabled_sheets:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "警告", "请至少启用一个工作表！")
            return

        # 检查是否有快报表
        flash_reports = [
            name
            for name, info in self.sheet_classifications.items()
            if info["checkbox"].isChecked() and info["combo"].currentText() == "快报表"
        ]

        if not flash_reports:
            from PySide6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "确认",
                "没有选择任何快报表，这意味着只会处理数据来源表。是否继续？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self.accept()

    def get_final_classifications(self):
        """获取最终的分类结果"""
        result = {
            "flash_reports": [],
            "data_sources": [],
            "skipped": [],
            "disabled": [],
        }

        for sheet_name, info in self.sheet_classifications.items():
            if not info["checkbox"].isChecked():
                result["disabled"].append(sheet_name)
                continue

            classification = info["combo"].currentText()
            if classification == "快报表":
                result["flash_reports"].append(sheet_name)
            elif classification == "数据来源表":
                result["data_sources"].append(sheet_name)
            else:
                result["skipped"].append(sheet_name)

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
        self.setMinimumSize(540, 380)
        self.resize(640, 420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 标题
        title_label = QLabel(f"请确认工作表的类型")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 工作表信息
        info_group = QGroupBox("工作表信息")
        info_layout = QFormLayout(info_group)
        info_layout.setContentsMargins(16, 12, 16, 12)
        info_layout.setSpacing(12)
        info_group.setStyleSheet(
            "QGroupBox { border: none; font-weight: bold; margin-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 0; padding: 0 0 6px 0; }"
        )

        # 工作表名称
        sheet_label = QLabel(self.sheet_name)
        sheet_label.setWordWrap(True)
        sheet_label.setStyleSheet("font-weight: bold; color: #2E86AB;")
        sheet_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        info_layout.addRow("工作表名称:", sheet_label)

        # 建议分类
        suggestion_label = QLabel(self.auto_classification)
        suggestion_label.setWordWrap(True)
        suggestion_label.setStyleSheet("font-weight: bold; color: #F24236;")
        info_layout.addRow("系统建议:", suggestion_label)

        layout.addWidget(info_group)

        # 分类选择
        classification_group = QGroupBox("请选择正确的分类")
        classification_layout = QVBoxLayout(classification_group)
        classification_layout.setContentsMargins(16, 12, 16, 12)
        classification_layout.setSpacing(10)
        classification_group.setStyleSheet(
            "QGroupBox { border: none; font-weight: bold; margin-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 0; padding: 0 0 6px 0; }"
        )

        # 选项说明
        help_label = QLabel(
            "• 快报表：需要填写数据的目标表格\n"
            "• 数据来源表：提供源数据的参考表格\n"
            "• 跳过：既不是快报表也不是数据来源表"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 12px; margin: 0px;")
        classification_layout.addWidget(help_label)

        # 单选按钮
        from PySide6.QtWidgets import QRadioButton, QButtonGroup

        self.button_group = QButtonGroup()

        self.flash_report_radio = QRadioButton("[表] 快报表（要填写的表）")
        self.flash_report_radio.setStyleSheet("font-size: 14px; padding: 6px 4px;")
        self.flash_report_radio.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button_group.addButton(self.flash_report_radio, 1)
        classification_layout.addWidget(self.flash_report_radio)

        self.data_source_radio = QRadioButton("[数据] 数据来源表")
        self.data_source_radio.setStyleSheet("font-size: 14px; padding: 6px 4px;")
        self.data_source_radio.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button_group.addButton(self.data_source_radio, 2)
        classification_layout.addWidget(self.data_source_radio)

        self.skip_radio = QRadioButton("[跳过] 跳过此表（不进行处理）")
        self.skip_radio.setStyleSheet("font-size: 14px; padding: 6px 4px;")
        self.skip_radio.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.setSpacing(12)

        # 全部使用建议按钮
        self.auto_all_btn = QPushButton("[AI] 全部使用系统建议")
        self.auto_all_btn.setToolTip("对所有剩余工作表都使用系统建议，不再询问")
        self.auto_all_btn.setMinimumHeight(32)
        self.auto_all_btn.clicked.connect(self.auto_classify_all)
        button_layout.addWidget(self.auto_all_btn)

        button_layout.addStretch()

        # 确认按钮
        self.confirm_btn = QPushButton("[OK] 确认")
        self.confirm_btn.setDefault(True)
        self.confirm_btn.setMinimumHeight(34)
        self.confirm_btn.clicked.connect(self.confirm_classification)
        button_layout.addWidget(self.confirm_btn)

        # 取消按钮
        self.cancel_btn = QPushButton("[X] 取消")
        self.cancel_btn.setMinimumHeight(34)
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
