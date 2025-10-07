# -*- coding: utf-8 -*-
"""
ModelBrowserDialog - Dialog for browsing and managing AI models
Following Cherry Studio reference UI design
"""

from typing import Dict, List, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QScrollArea, QFrame,
    QSizePolicy, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QCursor, QFont

from ..controllers.config_controller import ConfigController
from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING
from .add_model_dialog import AddModelDialog


class ModelRow(QWidget):
    """
    Single model row widget
    Layout: [Category Icon] [Model Name] [Tags] [Spacer] [⚙ Settings] [- Delete]
    """

    edit_clicked = Signal(str, str, str)  # provider_id, model_id, category
    delete_clicked = Signal(str, str)     # provider_id, model_id

    def __init__(self, provider_id: str, model_id: str, model_name: str,
                 category: str, parent=None):
        super().__init__(parent)

        self.provider_id = provider_id
        self.model_id = model_id
        self.model_name = model_name
        self.category = category

        self._setup_ui()

    def _setup_ui(self):
        """Setup model row UI"""
        self.setFixedHeight(56)

        # Row layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Category icon
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setScaledContents(True)

        # Load category icon
        icon_path = self._get_category_icon_path(self.category)
        if Path(icon_path).exists():
            pixmap = QPixmap(icon_path)
        else:
            # Fallback to default
            default_path = "assets/icons/categories/default.png"
            if Path(default_path).exists():
                pixmap = QPixmap(default_path)
            else:
                # Create gray placeholder
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.gray)

        icon_label.setPixmap(pixmap)
        layout.addWidget(icon_label)

        # Model name
        name_label = QLabel(self.model_name)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: 500;
                color: #111827;
            }
        """)
        layout.addWidget(name_label)

        # Spacer
        layout.addStretch(1)

        # Settings button (使用文字 "编辑")
        settings_btn = QPushButton("编辑")
        settings_btn.setFixedSize(56, 32)
        settings_btn.setCursor(QCursor(Qt.PointingHandCursor))
        settings_btn.setToolTip("编辑此模型")
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                border: none;
                font-size: 12px;
                font-weight: 500;
                color: white;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        settings_btn.clicked.connect(self._on_edit_clicked)
        layout.addWidget(settings_btn)

        # Delete button (使用文字 "删除")
        delete_btn = QPushButton("删除")
        delete_btn.setFixedSize(56, 32)
        delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        delete_btn.setToolTip("删除此模型")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                border: none;
                font-size: 12px;
                font-weight: 500;
                color: white;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:pressed {
                background-color: #B91C1C;
            }
        """)
        delete_btn.clicked.connect(self._on_delete_clicked)
        layout.addWidget(delete_btn)

        # Row styling - GREEN BACKGROUND
        self.setStyleSheet("""
            ModelRow {
                background-color: #D1FAE5;
                border-radius: 8px;
            }
            ModelRow:hover {
                background-color: #A7F3D0;
            }
        """)

    def _get_category_icon_path(self, category: str) -> str:
        """Get category icon file path"""
        filename = category.replace(" ", "-").lower()
        return f"assets/icons/categories/{filename}.png"

    def _on_edit_clicked(self):
        """Handle edit button click"""
        self.edit_clicked.emit(self.provider_id, self.model_id, self.category)

    def _on_delete_clicked(self):
        """Handle delete button click"""
        self.delete_clicked.emit(self.provider_id, self.model_id)


class CategoryBlock(QWidget):
    """
    Category block widget with gray header and green model rows
    """

    edit_model = Signal(str, str, str)    # provider_id, model_id, category
    delete_model = Signal(str, str)       # provider_id, model_id

    def __init__(self, category: str, models: List[Dict], parent=None):
        super().__init__(parent)

        self.category = category
        self.models = models
        self.is_collapsed = False

        self._setup_ui()

    def _setup_ui(self):
        """Setup category block UI"""
        # Add border and shadow to make block stand out
        self.setStyleSheet("""
            CategoryBlock {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
        """)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Category header - GRAY BACKGROUND
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet("""
            QWidget {
                background-color: #E5E7EB;
                border-radius: 8px;
            }
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        # Collapse arrow
        self.collapse_btn = QPushButton("∨")
        self.collapse_btn.setFixedSize(24, 24)
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 12px;
                color: #6B7280;
            }
        """)
        self.collapse_btn.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self.collapse_btn)

        # Category name
        name_label = QLabel(self.category)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: 700;
                color: #111827;
            }
        """)
        header_layout.addWidget(name_label)

        # Model count - GREEN
        count_label = QLabel(str(len(self.models)))
        count_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #10B981;
            }
        """)
        header_layout.addWidget(count_label)

        header_layout.addStretch()

        # Delete category button
        delete_btn = QPushButton("−")
        delete_btn.setFixedSize(32, 32)
        delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        delete_btn.setToolTip("删除分类")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 20px;
                color: #6B7280;
            }
            QPushButton:hover {
                color: #EF4444;
            }
        """)
        header_layout.addWidget(delete_btn)

        layout.addWidget(header)

        # Models container
        self.models_container = QWidget()
        models_layout = QVBoxLayout(self.models_container)
        models_layout.setContentsMargins(8, 8, 8, 8)  # Add padding inside block
        models_layout.setSpacing(6)  # Increase spacing between model rows

        # Model rows
        for model_data in self.models:
            provider_id = model_data.get("provider_id", "")
            model_id = model_data.get("id", "")
            model_name = model_data.get("name", "")

            row = ModelRow(provider_id, model_id, model_name, self.category)
            row.edit_clicked.connect(self.edit_model.emit)
            row.delete_clicked.connect(self.delete_model.emit)

            models_layout.addWidget(row)

        layout.addWidget(self.models_container)

    def _toggle_collapse(self):
        """Toggle category collapse state"""
        self.is_collapsed = not self.is_collapsed
        self.models_container.setVisible(not self.is_collapsed)
        self.collapse_btn.setText(">" if self.is_collapsed else "∨")


class ModelBrowserDialog(QDialog):
    """
    Dialog for browsing and managing AI models
    Following Cherry Studio reference UI design
    """

    model_selected = Signal(str, str)  # provider_id, model_id

    # Category filters matching PNG design
    CATEGORY_FILTERS = {
        "全部": None,
        "推理": ["DeepSeek", "Qwen", "GPT", "Claude", "Gemini", "Llama", "Gemma", "Doubao"],
        "视觉": ["Vision"],
        "联网": ["Web"],
        "免费": ["Free"],
        "嵌入": ["Embedding"],
        "重排": ["Rerank"],
        "工具": ["Tool"]
    }

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.controller = ConfigController.instance()

        # State
        self.search_query = ""
        self.current_filter = "全部"
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._on_search_timeout)

        self._init_ui()
        self._load_models()

    def _init_ui(self):
        """Initialize user interface"""
        # Window properties
        self.setWindowTitle("硅基流动模型")
        self.setFixedSize(1000, 680)
        self.setModal(True)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Search bar with icons
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        # Search icon
        search_icon = QLabel("🔍")
        search_icon.setFixedSize(24, 24)
        search_layout.addWidget(search_icon)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索模型 ID 或名称")
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                color: #1F2937;
            }
            QLineEdit:focus {
                border: 1px solid #10B981;
                background-color: white;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input, 1)

        # Refresh button (清空搜索并刷新)
        refresh_btn = QPushButton("清空")
        refresh_btn.setFixedHeight(40)
        refresh_btn.setCursor(QCursor(Qt.PointingHandCursor))
        refresh_btn.setToolTip("清空搜索并刷新列表")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                color: white;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        refresh_btn.clicked.connect(self._on_refresh_clicked)
        search_layout.addWidget(refresh_btn)

        main_layout.addLayout(search_layout)

        # Category tabs
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(8)

        self.category_buttons = {}
        for category in self.CATEGORY_FILTERS.keys():
            btn = QPushButton(category)
            btn.setFixedHeight(36)
            btn.setMinimumWidth(60)
            btn.setCursor(QCursor(Qt.PointingHandCursor))

            is_active = (category == "全部")
            btn.setProperty("active", is_active)

            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"#10B981" if is_active else "#F3F4F6"};
                    color: {"white" if is_active else "#6B7280"};
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {"#059669" if is_active else "#E5E7EB"};
                }}
            """)

            btn.clicked.connect(lambda checked, cat=category: self._on_category_clicked(cat))
            self.category_buttons[category] = btn
            tabs_layout.addWidget(btn)

        tabs_layout.addStretch()
        main_layout.addLayout(tabs_layout)

        # Scroll area for category blocks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F9FAFB;
            }
            QScrollArea > QWidget {
                background-color: #F9FAFB;
            }
        """)

        # Scroll content
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(20)  # Increased spacing between category blocks
        self.scroll_layout.addStretch()

        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll, 1)

        # Dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

    def _on_category_clicked(self, category: str):
        """Handle category tab click"""
        # Update button states
        for cat, btn in self.category_buttons.items():
            is_active = (cat == category)
            btn.setProperty("active", is_active)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"#10B981" if is_active else "#F3F4F6"};
                    color: {"white" if is_active else "#6B7280"};
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {"#059669" if is_active else "#E5E7EB"};
                }}
            """)

        self.current_filter = category
        self._load_models()

    def _on_search_changed(self, text: str):
        """Handle search text change with debouncing"""
        self.search_timer.stop()
        self.search_timer.start(300)

    def _on_search_timeout(self):
        """Handle search timer timeout"""
        self.search_query = self.search_input.text().strip().lower()
        self._load_models()

    def _on_refresh_clicked(self):
        """Handle refresh button click - clear search and reset filters"""
        # Clear search box
        self.search_input.clear()

        # Reset to "全部" category
        self._on_category_changed("全部")

        # Reload config and models
        self.controller._load_config()
        self._load_models()

    def _load_models(self):
        """Load and display models grouped by category"""
        # Clear existing content
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get all providers and models
        providers = self.controller.get_providers()

        # Group models by category
        category_models: Dict[str, List[Dict]] = {}

        for provider in providers:
            provider_id = provider.get("id", "")
            provider_name = provider.get("name", "")
            models = provider.get("models", [])

            for model in models:
                model_id = model.get("id", "")
                model_name = model.get("name", "")
                category = model.get("category", "其他")

                # Apply search filter
                if self.search_query:
                    if (self.search_query not in model_id.lower() and
                        self.search_query not in model_name.lower()):
                        continue

                # Apply category filter
                if self.current_filter != "全部":
                    filter_categories = self.CATEGORY_FILTERS.get(self.current_filter, [])
                    if filter_categories is not None:
                        if not any(fc.lower() in category.lower() for fc in filter_categories):
                            continue

                # Add provider info
                model_with_provider = {
                    **model,
                    "provider_id": provider_id,
                    "provider_name": provider_name
                }

                if category not in category_models:
                    category_models[category] = []

                category_models[category].append(model_with_provider)

        # Create category blocks
        for category, models in sorted(category_models.items()):
            block = CategoryBlock(category, models)
            block.edit_model.connect(self._on_edit_model)
            block.delete_model.connect(self._on_delete_model)

            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, block)

    def _on_edit_model(self, provider_id: str, model_id: str, category: str):
        """Handle edit model request"""
        provider = self.controller.get_provider(provider_id)
        if not provider:
            QMessageBox.warning(self, "错误", f"未找到提供商: {provider_id}")
            return

        models = provider.get("models", [])
        model = next((m for m in models if m.get("id") == model_id), None)

        if not model:
            QMessageBox.warning(self, "错误", f"未找到模型: {model_id}")
            return

        # Open AddModelDialog with pre-filled data
        dialog = AddModelDialog(self)

        # Pre-fill form
        dialog.model_id_input.setText(model_id)
        dialog.model_name_input.setText(model.get("name", ""))
        dialog.category_input.setText(model.get("category", ""))
        dialog.context_input.setValue(model.get("context_length", 4096))
        dialog.max_tokens_input.setValue(model.get("max_tokens", 2048))

        dialog.setWindowTitle(f"编辑模型 - {model.get('name', model_id)}")

        dialog._original_model_id = model_id
        dialog._provider_id = provider_id

        def update_model():
            """Update existing model"""
            new_model_id = dialog.model_id_input.text().strip()
            new_model_name = dialog.model_name_input.text().strip()
            new_category = dialog.category_input.text().strip()
            new_context = dialog.context_input.value()
            new_max_tokens = dialog.max_tokens_input.value()

            if not new_model_id or not new_model_name:
                QMessageBox.warning(dialog, "错误", "模型ID和名称不能为空")
                return

            # Update model
            models = provider.get("models", [])
            for i, m in enumerate(models):
                if m.get("id") == dialog._original_model_id:
                    models[i] = {
                        "id": new_model_id,
                        "name": new_model_name,
                        "category": new_category,
                        "context_length": new_context,
                        "max_tokens": new_max_tokens
                    }
                    break

            self.controller._save_config()
            self._load_models()
            dialog.accept()

        # Replace confirm handler
        dialog.confirm_btn.clicked.disconnect()
        dialog.confirm_btn.clicked.connect(update_model)

        dialog.exec()

    def _on_delete_model(self, provider_id: str, model_id: str):
        """Handle delete model request"""
        provider = self.controller.get_provider(provider_id)
        if not provider:
            return

        models = provider.get("models", [])
        model = next((m for m in models if m.get("id") == model_id), None)

        if not model:
            return

        model_name = model.get("name", model_id)

        # Confirmation
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除模型 \"{model_name}\" 吗？\n\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Delete model
        provider["models"] = [m for m in models if m.get("id") != model_id]
        self.controller._save_config()
        self._load_models()

        QMessageBox.information(self, "删除成功", f"模型 \"{model_name}\" 已删除。")
