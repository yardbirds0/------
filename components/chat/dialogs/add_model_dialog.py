# -*- coding: utf-8 -*-
"""
AddModelDialog - Dialog for adding custom models to a provider
"""

import re
from typing import Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QWidget, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon

from ..controllers.config_controller import ConfigController
from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING


class AddModelDialog(QDialog):
    """
    Dialog for adding a custom model to a provider

    UI Specifications:
    - Size: 480×360px
    - Fields: Model ID* (required), Model Name, Group Name
    - Button: Green "添加模型" button

    Signals:
        model_added: Emitted when model is successfully added (model_id: str)
    """

    model_added = Signal(str)  # model_id

    def __init__(self, parent: QWidget, provider_id: str):
        """
        Initialize AddModelDialog

        Args:
            parent: Parent widget
            provider_id: ID of the provider to add model to
        """
        super().__init__(parent)

        self.provider_id = provider_id
        self.controller = ConfigController.instance()

        # Input widgets
        self.model_id_input: QLineEdit = None
        self.model_name_input: QLineEdit = None
        self.group_input: QLineEdit = None

        self._init_ui()

    def _init_ui(self):
        """Initialize user interface"""
        # Window properties
        self.setWindowTitle("添加模型")
        self.setFixedSize(480, 360)
        self.setModal(True)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            SPACING["lg"], SPACING["lg"],
            SPACING["lg"], SPACING["lg"]
        )
        main_layout.setSpacing(SPACING["md"])

        # Title
        title_label = QLabel("添加自定义模型")
        title_label.setFont(FONTS["title"])
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        main_layout.addWidget(title_label)

        # Add vertical spacing
        main_layout.addSpacing(SPACING["md"])

        # Model ID field (required)
        model_id_layout = self._create_field_layout(
            "模型 ID",
            required=True,
            help_text="格式: provider/model-name 或 model-name"
        )
        self.model_id_input = model_id_layout[1]
        main_layout.addLayout(model_id_layout[0])

        # Model Name field (optional)
        model_name_layout = self._create_field_layout(
            "模型名称",
            required=False,
            help_text="显示名称,不填则使用模型ID"
        )
        self.model_name_input = model_name_layout[1]
        main_layout.addLayout(model_name_layout[0])

        # Group Name field (optional)
        group_layout = self._create_field_layout(
            "分组名称",
            required=False,
            help_text="用于分类管理,如: Qwen, GPT-4"
        )
        self.group_input = group_layout[1]
        main_layout.addLayout(group_layout[0])

        # Add stretcher to push button to bottom
        main_layout.addStretch()

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(SIZES["button_height_large"])
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        # Submit button
        submit_btn = QPushButton("添加模型")
        submit_btn.setProperty("styleClass", "primary")
        submit_btn.setFixedHeight(SIZES["button_height_large"])
        submit_btn.setMinimumWidth(120)
        submit_btn.clicked.connect(self._on_submit_clicked)
        button_layout.addWidget(submit_btn)

        main_layout.addLayout(button_layout)

        # Apply styling
        self._apply_styling()

    def _create_field_layout(
        self,
        label_text: str,
        required: bool = False,
        help_text: str = None
    ) -> Tuple[QVBoxLayout, QLineEdit]:
        """
        Create a labeled input field with optional help text

        Args:
            label_text: Label text
            required: Whether field is required
            help_text: Optional help text to show as tooltip

        Returns:
            Tuple of (layout, input_widget)
        """
        layout = QVBoxLayout()
        layout.setSpacing(SPACING["xs"])

        # Label with required marker
        label_layout = QHBoxLayout()
        label_layout.setSpacing(SPACING["xs"])

        label = QLabel(label_text)
        label.setFont(FONTS["label"])
        label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        label_layout.addWidget(label)

        if required:
            required_mark = QLabel("*")
            required_mark.setStyleSheet(f"color: {COLORS['accent_red']};")
            required_mark.setFont(FONTS["label"])
            label_layout.addWidget(required_mark)

        if help_text:
            help_label = QLabel("(?)")
            help_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
            help_label.setFont(FONTS["label"])
            help_label.setToolTip(help_text)
            label_layout.addWidget(help_label)

        label_layout.addStretch()
        layout.addLayout(label_layout)

        # Input field
        input_field = QLineEdit()
        input_field.setFont(FONTS["input"])
        input_field.setFixedHeight(SIZES["input_height"])
        layout.addWidget(input_field)

        return (layout, input_field)

    def _validate_model_id(self, model_id: str) -> Tuple[bool, str]:
        """
        Validate model ID

        Validation rules:
        1. Non-empty
        2. Valid format (alphanumeric, hyphens, underscores, slashes)
        3. Unique within provider

        Args:
            model_id: Model ID to validate

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Check non-empty
        if not model_id or not model_id.strip():
            return (False, "模型ID不能为空")

        model_id = model_id.strip()

        # Check format (allow letters, numbers, hyphens, underscores, slashes, dots)
        # Examples: "gpt-4", "Qwen/Qwen2.5-7B", "deepseek-ai/DeepSeek-V3"
        pattern = r'^[a-zA-Z0-9/_\.\-]+$'
        if not re.match(pattern, model_id):
            return (False, "模型ID格式无效,只能包含字母、数字、连字符、下划线、斜杠和点")

        # Check uniqueness within provider
        provider = self.controller.get_provider(self.provider_id)
        if provider:
            existing_model_ids = [m.get("id", "") for m in provider.get("models", [])]
            if model_id in existing_model_ids:
                return (False, f"模型ID '{model_id}' 已存在")

        return (True, "")

    def _on_submit_clicked(self):
        """Handle submit button click"""
        # Get input values
        model_id = self.model_id_input.text().strip()
        model_name = self.model_name_input.text().strip()
        group_name = self.group_input.text().strip()

        # Validate model ID
        is_valid, error_msg = self._validate_model_id(model_id)
        if not is_valid:
            QMessageBox.warning(self, "验证失败", error_msg)
            self.model_id_input.setFocus()
            return

        # Use model_id as name if name not provided
        if not model_name:
            model_name = model_id

        # Use "Custom" as default category if not provided
        if not group_name:
            group_name = "自定义"

        # Create model data
        new_model = {
            "id": model_id,
            "name": model_name,
            "category": group_name,
            "context_length": 8192,  # Default value
            "max_tokens": 4096,      # Default value
            "custom": True           # Mark as custom model
        }

        try:
            # Get current provider
            provider = self.controller.get_provider(self.provider_id)
            if not provider:
                QMessageBox.critical(self, "错误", f"未找到服务商: {self.provider_id}")
                return

            # Add model to provider's model list
            models = provider.get("models", [])
            models.append(new_model)
            provider["models"] = models

            # Update provider configuration
            self.controller.update_provider(self.provider_id, provider)

            # Emit signal
            self.model_added.emit(model_id)

            # Show success message
            QMessageBox.information(
                self,
                "添加成功",
                f"模型 '{model_name}' 已成功添加到 {provider['name']}"
            )

            # Close dialog
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "添加失败", f"添加模型时发生错误: {str(e)}")

    def _apply_styling(self):
        """Apply cherry theme styling to dialog"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_main']};
            }}

            QLineEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 8px 12px;
                color: {COLORS['text_primary']};
            }}

            QLineEdit:focus {{
                border: 1px solid {COLORS['border_focus']};
            }}

            QPushButton {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 8px 16px;
                font-size: 14px;
            }}

            QPushButton:hover {{
                background-color: {COLORS['bg_active']};
            }}

            QPushButton[styleClass="primary"] {{
                background-color: {COLORS['accent_green']};
                color: {COLORS['text_inverse']};
                border: none;
            }}

            QPushButton[styleClass="primary"]:hover {{
                background-color: #0EA472;
            }}

            QPushButton[styleClass="primary"]:pressed {{
                background-color: #0D9368;
            }}
        """)
