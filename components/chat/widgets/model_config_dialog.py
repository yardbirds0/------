# -*- coding: utf-8 -*-
"""
Model Configuration Dialog
模型配置对话框 - 精确复刻 模型选择界面.png 的两面板布局
"""

from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QFrame,
    QLineEdit,
    QListWidget,
    QPushButton,
    QListWidgetItem,
    QTreeWidgetItem,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPixmap

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING
from ..controllers.config_controller import ConfigController
from ..dialogs import AddModelDialog, ModelBrowserDialog


class ModelConfigDialog(QDialog):
    """
    模型配置对话框

    布局结构:
    ┌────────────────────────────────────────────┐
    │  设置 (1200×800)                           │
    ├──────────┬─────────────────────────────────┤
    │ Left     │ Right Panel                     │
    │ Panel    │                                 │
    │ (350px)  │ (850px)                         │
    │          │                                 │
    └──────────┴─────────────────────────────────┘
    """

    # 信号定义
    model_selected = Signal(str, str)  # (provider_id, model_id)
    provider_added = Signal(str)  # provider_id
    provider_deleted = Signal(str)  # provider_id
    provider_reordered = Signal(list)  # [provider_ids] in new order

    def __init__(self, parent=None):
        super().__init__(parent)

        # 配置控制器
        self.controller = ConfigController.instance()

        # API测试服务
        from components.chat.services import APITestService

        self.api_test_service = APITestService.instance()

        # 当前选中的provider
        self.current_provider_id = None

        # 当前搜索查询（用于保持搜索状态）
        self._current_search_query = ""

        # 搜索结果缓存（用于过滤显示）
        self._search_matched_providers = set()  # 匹配的provider IDs
        self._search_model_matches = {}  # {provider_id: [matched_model_ids]}

        # API测试按钮引用（在_create_provider_config_section中设置）
        self.api_test_btn = None

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        self._load_initial_data()

    def _setup_ui(self):
        """设置UI结构"""
        # 对话框基本设置
        self.setWindowTitle("设置")
        self.setFixedSize(1200, 800)
        self.setModal(True)

        # 主布局：水平分割（无间距，无边距）
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左面板（350px固定宽度）
        self.left_panel = self._create_left_panel()
        self.left_panel.setFixedWidth(350)
        main_layout.addWidget(self.left_panel)

        # 分隔线（1px垂直线）
        divider = self._create_divider()
        main_layout.addWidget(divider)

        # 右面板（填充剩余空间，实际850px）
        self.right_panel = self._create_right_panel()
        main_layout.addWidget(self.right_panel, stretch=1)

    def _create_left_panel(self) -> QWidget:
        """创建左面板 - Provider列表"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(
            SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"]
        )
        layout.setSpacing(SPACING["md"])

        # ==================== 标题 ====================
        title_label = QLabel("模型供应商")
        title_label.setFont(FONTS["title"])  # 16px, DemiBold
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        layout.addWidget(title_label)

        # ==================== 搜索框 ====================
        self.search_input = self._create_search_input()
        layout.addWidget(self.search_input)

        # ==================== Provider 列表 ====================
        self.provider_list = ProviderListWidget(parent=self)
        self.provider_list.setDragDropMode(QListWidget.InternalMove)  # 允许拖拽排序
        self.provider_list.setSelectionMode(QListWidget.SingleSelection)
        # 连接拖拽完成信号
        self.provider_list.order_changed.connect(self._on_provider_order_changed)
        self.provider_list.setSpacing(0)  # 移除spacing，改用item的margin
        self.provider_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: #FFFFFF;
                border: none;
                padding: 4px;
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 2px 0px;
            }}
            QListWidget::item:hover {{
                background-color: transparent;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
            }}
        """
        )
        self.provider_list.itemSelectionChanged.connect(self._on_provider_selected)
        self.provider_list.itemSelectionChanged.connect(
            self._on_provider_selection_changed
        )
        layout.addWidget(self.provider_list, stretch=1)

        # ==================== 添加按钮 ====================
        from PySide6.QtWidgets import QPushButton

        add_button = QPushButton("+ 添加")
        add_button.setFixedHeight(SIZES["button_height_large"])  # 40px
        add_button.setFont(FONTS["button"])
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['accent_blue']};
                border: 1px solid {COLORS['accent_blue']};
                border-radius: {SIZES['border_radius_small']}px;
                padding: 0px {SPACING['md']}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_blue']};
                color: {COLORS['text_inverse']};
            }}
            QPushButton:pressed {{
                background-color: #2563EB;
            }}
        """
        )
        add_button.clicked.connect(self._on_add_provider_clicked)
        layout.addWidget(add_button)

        return panel

    def _create_search_input(self) -> QWidget:
        """创建搜索输入框"""
        from PySide6.QtWidgets import QLineEdit

        search_input = QLineEdit()
        search_input.setPlaceholderText("🔍 搜索模型平台...")
        search_input.setFixedHeight(36)
        search_input.setFont(FONTS["input"])
        search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: #FFFFFF;
                color: {COLORS['text_primary']};
                border: 1px solid #E5E5E5;
                border-radius: 6px;
                padding: 0px {SPACING['md']}px;
            }}
            QLineEdit:focus {{
                border-color: #CCCCCC;
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_tertiary']};
            }}
        """
        )
        search_input.textChanged.connect(self._on_search_changed)
        return search_input

    def _create_right_panel(self) -> QWidget:
        """创建右面板 - Provider配置和模型选择"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ==================== Header Section (60px) ====================
        self.header_widget = self._create_header_section()
        layout.addWidget(self.header_widget)

        # ==================== Scrollable Content Area ====================
        from PySide6.QtWidgets import QScrollArea

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet(f"background-color: {COLORS['bg_main']};")

        # Scroll content widget
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(
            SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"]
        )
        content_layout.setSpacing(SPACING["lg"])

        # API Key Section
        self.api_key_section = self._create_api_key_section()
        content_layout.addWidget(self.api_key_section)

        # API URL Section
        self.api_url_section = self._create_api_url_section()
        content_layout.addWidget(self.api_url_section)

        # Model List Section (US3.4)
        self.model_list_section = self._create_model_list_section()
        content_layout.addWidget(self.model_list_section, stretch=1)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area, stretch=1)

        # ==================== Footer Section ====================
        footer_widget = self._create_footer_section()
        layout.addWidget(footer_widget)

        return panel

    def _create_header_section(self) -> QWidget:
        """创建右面板Header Section (60px)"""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(
            f"""
            QWidget {{
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E5E5;
            }}
        """
        )

        layout = QHBoxLayout(header)
        layout.setContentsMargins(
            SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"]
        )
        layout.setSpacing(SPACING["sm"])

        # Provider name label
        self.provider_name_label = QLabel("选择供应商")
        from PySide6.QtGui import QFont

        provider_font = QFont(FONTS["title"])
        provider_font.setPixelSize(18)
        provider_font.setWeight(QFont.DemiBold)
        self.provider_name_label.setFont(provider_font)
        self.provider_name_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; border: none;"
        )
        layout.addWidget(self.provider_name_label)

        # External link button
        from PySide6.QtWidgets import QToolButton

        self.external_link_btn = QToolButton()
        self.external_link_btn.setText("↗")
        self.external_link_btn.setFixedSize(28, 28)
        self.external_link_btn.setCursor(Qt.PointingHandCursor)
        self.external_link_btn.setStyleSheet(
            f"""
            QToolButton {{
                background-color: transparent;
                color: {COLORS['text_tertiary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 4px;
                font-size: 14px;
            }}
            QToolButton:hover {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['accent_blue']};
            }}
        """
        )
        self.external_link_btn.clicked.connect(self._on_external_link_clicked)
        layout.addWidget(self.external_link_btn)

        # Spacer
        layout.addStretch(1)

        # Toggle switch (using common_widgets.ToggleSwitch)
        from ..widgets.common_widgets import ToggleSwitch

        self.provider_toggle = ToggleSwitch()
        self.provider_toggle.setChecked(True)
        self.provider_toggle.toggled.connect(self._on_provider_toggle_changed_header)
        layout.addWidget(self.provider_toggle)

        return header

    def _create_api_key_section(self) -> QWidget:
        """创建API密钥配置区域"""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        # Label row: "API 密钥" + Settings button
        label_row = QHBoxLayout()
        label_row.setSpacing(SPACING["sm"])

        api_key_label = QLabel("API 密钥")
        from PySide6.QtGui import QFont

        label_font = QFont(FONTS["body"])
        label_font.setPixelSize(16)
        label_font.setWeight(QFont.Bold)
        api_key_label.setFont(label_font)
        api_key_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        label_row.addWidget(api_key_label)

        # Settings button (gear icon)
        from PySide6.QtWidgets import QToolButton

        settings_btn = QToolButton()
        settings_btn.setText("⚙️")
        settings_btn.setFixedSize(20, 20)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setStyleSheet(
            f"""
            QToolButton {{
                background-color: transparent;
                color: {COLORS['text_tertiary']};
                border: none;
                font-size: 16px;
            }}
            QToolButton:hover {{
                color: {COLORS['text_primary']};
            }}
        """
        )
        settings_btn.clicked.connect(lambda: self._show_placeholder_message("高级设置"))
        label_row.addWidget(settings_btn)
        label_row.addStretch(1)

        layout.addLayout(label_row)

        # Input row: Password input + Test button
        input_row = QHBoxLayout()
        input_row.setSpacing(SPACING["sm"])

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("请输入API密钥...")
        # 不隐藏密钥，改为明文显示
        # self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setFixedHeight(40)
        self.api_key_input.setFont(FONTS["input"])
        self.api_key_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: #FFFFFF;
                color: {COLORS['text_primary']};
                border: 1px solid #E5E5E5;
                border-radius: 6px;
                padding: 0px {SPACING['md']}px;
            }}
            QLineEdit:focus {{
                border-color: #CCCCCC;
            }}
        """
        )
        self.api_key_input.textChanged.connect(self._on_api_key_changed)
        input_row.addWidget(self.api_key_input, stretch=1)

        # Test button
        self.api_test_btn = QPushButton("检测")
        self.api_test_btn.setFixedSize(80, 40)
        self.api_test_btn.setFont(FONTS["button"])
        self.api_test_btn.setCursor(Qt.PointingHandCursor)
        self.api_test_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: {COLORS['text_inverse']};
                border: none;
                border-radius: {SIZES['border_radius_small']}px;
            }}
            QPushButton:hover {{
                background-color: #2563EB;
            }}
            QPushButton:pressed {{
                background-color: #1D4ED8;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['border']};
                color: {COLORS['text_tertiary']};
            }}
        """
        )
        self.api_test_btn.clicked.connect(self._on_test_api_clicked)
        input_row.addWidget(self.api_test_btn)

        layout.addLayout(input_row)

        # Hint label
        hint_label = QLabel("点击这里获取密钥 多个密钥使用逗号或空格分隔")
        from PySide6.QtGui import QFont

        hint_font = QFont(FONTS["caption"])
        hint_font.setPixelSize(12)
        hint_label.setFont(hint_font)
        hint_label.setStyleSheet(f"color: #888888;")
        layout.addWidget(hint_label)

        return section

    def _create_api_url_section(self) -> QWidget:
        """创建API地址配置区域"""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        # Label row: "API 地址" + Settings button
        label_row = QHBoxLayout()
        label_row.setSpacing(SPACING["sm"])

        api_url_label = QLabel("API 地址")
        from PySide6.QtGui import QFont

        label_font = QFont(FONTS["body"])
        label_font.setPixelSize(16)
        label_font.setWeight(QFont.Bold)
        api_url_label.setFont(label_font)
        api_url_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        label_row.addWidget(api_url_label)

        # Settings button
        from PySide6.QtWidgets import QToolButton

        settings_btn = QToolButton()
        settings_btn.setText("⚙️")
        settings_btn.setFixedSize(20, 20)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setStyleSheet(
            f"""
            QToolButton {{
                background-color: transparent;
                color: {COLORS['text_tertiary']};
                border: none;
                font-size: 16px;
            }}
            QToolButton:hover {{
                color: {COLORS['text_primary']};
            }}
        """
        )
        settings_btn.clicked.connect(lambda: self._show_placeholder_message("高级设置"))
        label_row.addWidget(settings_btn)
        label_row.addStretch(1)

        layout.addLayout(label_row)

        # Input field
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://...")
        self.api_url_input.setFixedHeight(40)
        self.api_url_input.setFont(FONTS["input"])
        self.api_url_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: #FFFFFF;
                color: {COLORS['text_primary']};
                border: 1px solid #E5E5E5;
                border-radius: 6px;
                padding: 0px {SPACING['md']}px;
            }}
            QLineEdit:focus {{
                border-color: #CCCCCC;
            }}
        """
        )
        self.api_url_input.textChanged.connect(self._on_api_url_changed)
        layout.addWidget(self.api_url_input)

        # Hint label
        hint_label = QLabel("自定义API端点 (可选)")
        from PySide6.QtGui import QFont

        hint_font = QFont(FONTS["caption"])
        hint_font.setPixelSize(12)
        hint_label.setFont(hint_font)
        hint_label.setStyleSheet(f"color: #888888;")
        layout.addWidget(hint_label)

        return section

    def _create_model_list_section(self) -> QWidget:
        """创建模型列表区域 - 重构为卡片式分类布局"""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])

        # Section label: "模型列表" (16px Bold)
        model_list_label = QLabel("模型列表")
        from PySide6.QtGui import QFont

        label_font = QFont(FONTS["body"])
        label_font.setPixelSize(16)
        label_font.setWeight(QFont.Bold)
        model_list_label.setFont(label_font)
        model_list_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(model_list_label)

        # 创建模型容器（用于放置分类卡片）
        from PySide6.QtWidgets import QScrollArea

        models_scroll = QScrollArea()
        models_scroll.setWidgetResizable(True)
        models_scroll.setFrameShape(QFrame.NoFrame)
        models_scroll.setStyleSheet("background-color: #FFFFFF; border: none;")

        models_container = QWidget()
        self.models_container_layout = QVBoxLayout(models_container)
        self.models_container_layout.setContentsMargins(0, 0, 0, 0)
        self.models_container_layout.setSpacing(12)
        self.models_container_layout.addStretch(1)

        models_scroll.setWidget(models_container)
        layout.addWidget(models_scroll, stretch=1)

        return section

    def _create_footer_section(self) -> QWidget:
        """创建底部按钮区域 (US3.4)"""
        footer = QWidget()
        footer.setFixedHeight(60)
        footer.setStyleSheet(
            f"""
            QWidget {{
                background-color: {COLORS['bg_main']};
                border-top: 1px solid {COLORS['border']};
            }}
        """
        )

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(
            SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"]
        )
        layout.setSpacing(SPACING["sm"])

        # Spacer to push buttons to the right
        layout.addStretch(1)

        # "管理模型" button (outlined style)
        manage_models_btn = QPushButton("管理模型")
        manage_models_btn.setFixedSize(100, 36)
        manage_models_btn.setCursor(Qt.PointingHandCursor)
        manage_models_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius_small']}px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                border-color: {COLORS['accent_blue']};
                color: {COLORS['accent_blue']};
            }}
        """
        )
        manage_models_btn.clicked.connect(self._on_manage_models_clicked)
        layout.addWidget(manage_models_btn)

        # "添加模型" button (primary style)
        add_model_btn = QPushButton("添加模型")
        add_model_btn.setFixedSize(100, 36)
        add_model_btn.setCursor(Qt.PointingHandCursor)
        add_model_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: #FFFFFF;
                border: none;
                border-radius: {SIZES['border_radius_small']}px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #2563EB;
            }}
        """
        )
        add_model_btn.clicked.connect(self._on_add_model_clicked)
        layout.addWidget(add_model_btn)

        return footer

    def _create_divider(self) -> QFrame:
        """创建分隔线"""
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Plain)
        divider.setFixedWidth(1)
        divider.setStyleSheet(f"background-color: {COLORS['border']};")
        return divider

    def _apply_styles(self):
        """应用Cherry Studio主题样式"""
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: #FFFFFF;
                color: {COLORS['text_primary']};
            }}

            QWidget#left_panel {{
                background-color: #FFFFFF;
            }}

            QWidget#right_panel {{
                background-color: #FFFFFF;
            }}
        """
        )

        # 设置面板对象名称以便样式应用
        self.left_panel.setObjectName("left_panel")
        self.right_panel.setObjectName("right_panel")

    def _connect_signals(self):
        """连接信号"""
        # ConfigController信号连接（后续实现）

        # API测试服务信号连接
        self.api_test_service.progress_update.connect(self._on_api_test_progress)
        self.api_test_service.test_finished.connect(self._on_api_test_finished)

    def _load_initial_data(self):
        """加载初始数据"""
        # 获取当前选中的provider
        provider_id, _ = self.controller.get_current_model()
        self.current_provider_id = provider_id

        # 加载Provider列表
        self._populate_provider_list()

        # 加载初始Provider配置到右面板
        if self.current_provider_id:
            self._load_provider_config(self.current_provider_id)

    def _populate_provider_list(self, filter_query: str = ""):
        """填充Provider列表 - 使用SearchEngine结果进行过滤"""
        self.provider_list.clear()

        # 从ConfigController获取providers
        providers = self.controller.get_providers()

        for provider in providers:
            provider_id = provider.get("id", "")
            provider_name = provider.get("name", "")
            enabled = provider.get("enabled", True)

            # 搜索过滤 - 使用SearchEngine结果
            if filter_query:
                # 如果有搜索查询，只显示匹配的providers
                if provider_id not in self._search_matched_providers:
                    continue

            # 创建列表项
            item_widget = ProviderListItemWidget(provider_id, provider_name, enabled)
            item_widget.toggle_changed.connect(
                lambda state, pid=provider_id: self._on_provider_toggle_changed(
                    pid, state
                )
            )

            # 添加到列表
            list_item = QListWidgetItem(self.provider_list)
            list_item.setSizeHint(item_widget.sizeHint())
            list_item.setData(Qt.UserRole, provider_id)  # 存储provider_id
            self.provider_list.addItem(list_item)
            self.provider_list.setItemWidget(list_item, item_widget)

            # 选中当前provider
            if provider_id == self.current_provider_id:
                list_item.setSelected(True)

    # ==================== 事件处理 ====================

    def _on_search_changed(self, query: str):
        """搜索文本变化 - 使用SearchEngine进行双重搜索"""
        from components.chat.services import SearchEngine

        self._current_search_query = query  # 保存当前搜索查询

        # 使用SearchEngine进行搜索
        providers = self.controller.get_providers()
        matched_provider_ids, model_matches = SearchEngine.search(query, providers)

        # 保存搜索结果用于过滤
        self._search_matched_providers = matched_provider_ids
        self._search_model_matches = model_matches

        # 更新provider列表和model树
        self._populate_provider_list(filter_query=query)

        # 如果有选中的provider，更新其model树显示
        if self.current_provider_id:
            self._populate_model_tree(self.current_provider_id)

    def _on_provider_selected(self):
        """Provider选择变化"""
        selected_items = self.provider_list.selectedItems()
        if not selected_items:
            return

        provider_id = selected_items[0].data(Qt.UserRole)
        self.current_provider_id = provider_id

        # 加载provider配置到右面板
        self._load_provider_config(provider_id)

    def _on_provider_selection_changed(self):
        """Provider选中状态变化 - 处理文字加粗效果"""
        # 遍历所有item，更新选中状态
        for i in range(self.provider_list.count()):
            item = self.provider_list.item(i)
            widget = self.provider_list.itemWidget(item)
            if isinstance(widget, ProviderListItemWidget):
                # 选中的item文字加粗
                is_selected = item.isSelected()
                widget.set_selected(is_selected)

    def _load_provider_config(self, provider_id: str):
        """加载Provider配置到右面板"""
        provider = self.controller.get_provider(provider_id)
        if not provider:
            return

        # 更新Header
        provider_name = provider.get("name", "未知供应商")
        self.provider_name_label.setText(provider_name)

        # 更新Toggle (阻止信号避免递归调用_populate_provider_list)
        enabled = provider.get("enabled", True)
        self.provider_toggle.blockSignals(True)
        self.provider_toggle.setChecked(enabled)
        self.provider_toggle.blockSignals(False)

        # 更新API Key
        api_key = provider.get("api_key", "")
        self.api_key_input.setText(api_key)

        # 更新API URL
        api_url = provider.get("api_url", "")
        self.api_url_input.setText(api_url)

        # 加载模型列表 (US3.4)
        self._populate_model_tree(provider_id)

    def _populate_model_tree(self, provider_id: str):
        """加载Provider的模型列表 - 改为分类卡片布局，支持搜索过滤"""
        # 清空现有内容
        while self.models_container_layout.count() > 1:  # 保留最后的stretch
            item = self.models_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        provider = self.controller.get_provider(provider_id)
        if not provider:
            return

        models = provider.get("models", [])
        if not models:
            # 显示"无可用模型"
            empty_label = QLabel("暂无可用模型")
            empty_label.setStyleSheet(
                f"color: {COLORS['text_tertiary']}; padding: 16px;"
            )
            self.models_container_layout.insertWidget(0, empty_label)
            return

        # 获取当前激活的模型
        current_provider, current_model = self.controller.get_current_model()
        is_current_provider = provider_id == current_provider

        # 获取搜索过滤的模型ID列表
        matched_model_ids = None
        if self._current_search_query and provider_id in self._search_model_matches:
            matched_model_ids = set(self._search_model_matches[provider_id])

        # 按category分组模型
        categories = {}
        for model in models:
            model_id = model.get("id", "")

            # 如果有搜索过滤，只包含匹配的模型
            if matched_model_ids is not None and model_id not in matched_model_ids:
                continue

            category = model.get("category", "其他")
            if category not in categories:
                categories[category] = []
            categories[category].append(model)

        # 创建QButtonGroup确保单选
        from PySide6.QtWidgets import QButtonGroup

        self.model_button_group = QButtonGroup(self)
        self.model_button_group.setExclusive(True)

        # 定义分类顺序
        category_order = [
            "DeepSeek",
            "Anthropic",
            "Doubao",
            "Embedding",
            "Openai",
            "Gemini",
            "Gemma",
            "Llama-3.2",
            "BAAI",
            "Qwen",
            "其他",
        ]

        # 按顺序创建分类卡片（优先显示category_order中的分类）
        displayed_categories = set()

        for category_name in category_order:
            if category_name not in categories:
                continue

            category_models = categories[category_name]
            displayed_categories.add(category_name)

            # 创建分类卡片
            # 如果有搜索查询，自动展开分类以显示匹配的模型
            auto_expand = bool(self._current_search_query)
            category_card = ModelCategoryCard(
                category_name=category_name,
                models=category_models,
                current_model=current_model if is_current_provider else None,
                provider_id=provider_id,
                parent=self,
                is_expanded=auto_expand,
            )

            # 连接模型选择信号
            category_card.model_selected.connect(
                lambda pid, mid: self._on_model_selected(pid, mid)
            )

            # 添加到button group
            for radio_btn in category_card.get_radio_buttons():
                self.model_button_group.addButton(radio_btn)

            self.models_container_layout.insertWidget(
                self.models_container_layout.count() - 1, category_card
            )

        # 添加剩余未显示的分类（按字母顺序）
        remaining_categories = sorted(set(categories.keys()) - displayed_categories)
        for category_name in remaining_categories:
            category_models = categories[category_name]

            # 创建分类卡片
            # 如果有搜索查询，自动展开分类以显示匹配的模型
            auto_expand = bool(self._current_search_query)
            category_card = ModelCategoryCard(
                category_name=category_name,
                models=category_models,
                current_model=current_model if is_current_provider else None,
                provider_id=provider_id,
                parent=self,
                is_expanded=auto_expand,
            )

            # 连接模型选择信号
            category_card.model_selected.connect(
                lambda pid, mid: self._on_model_selected(pid, mid)
            )

            # 添加到button group
            for radio_btn in category_card.get_radio_buttons():
                self.model_button_group.addButton(radio_btn)

            self.models_container_layout.insertWidget(
                self.models_container_layout.count() - 1, category_card
            )

    def _on_model_tree_item_clicked(self, item: "QTreeWidgetItem", column: int):
        """模型树项点击 - 委托给widget处理"""
        # Note: 实际的选择由ModelItemWidget的radio button处理
        # 这里只是为了支持点击整行也能选中
        widget = self.model_tree.itemWidget(item, 0)
        if widget and isinstance(widget, ModelItemWidget):
            widget.radio_btn.setChecked(True)

    def _on_model_selected(self, provider_id: str, model_id: str):
        """模型选中 - 立即应用 (US3.5)"""
        # 立即更新ConfigController
        self.controller.set_current_model(provider_id, model_id)
        print(f"Model selected: {provider_id}/{model_id}")

    def _on_provider_toggle_changed(self, provider_id: str, enabled: bool):
        """Provider列表项Toggle状态变化（已实现）"""
        provider = self.controller.get_provider(provider_id)
        if provider:
            provider["enabled"] = enabled
            self.controller.update_provider(provider_id, provider)

    def _on_provider_toggle_changed_header(self, checked: bool):
        """Header Toggle状态变化"""
        if not self.current_provider_id:
            return

        provider = self.controller.get_provider(self.current_provider_id)
        if provider:
            provider["enabled"] = checked
            self.controller.update_provider(self.current_provider_id, provider)

            # 同步更新左侧列表项的toggle状态，保持当前搜索查询
            self._populate_provider_list(filter_query=self._current_search_query)

    def _on_api_key_changed(self, text: str):
        """API Key输入变化 - 立即保存"""
        if not self.current_provider_id:
            return

        provider = self.controller.get_provider(self.current_provider_id)
        if provider:
            provider["api_key"] = text
            self.controller.update_provider(self.current_provider_id, provider)

    def _on_api_url_changed(self, text: str):
        """API URL输入变化 - 立即保存"""
        if not self.current_provider_id:
            return

        provider = self.controller.get_provider(self.current_provider_id)
        if provider:
            provider["api_url"] = text
            self.controller.update_provider(self.current_provider_id, provider)

    def _on_external_link_clicked(self):
        """打开供应商网站"""
        if not self.current_provider_id:
            return

        provider = self.controller.get_provider(self.current_provider_id)
        if provider:
            website_url = provider.get("website", "")
            if website_url:
                import webbrowser

                webbrowser.open(website_url)
            else:
                self._show_placeholder_message("未配置网站链接")

    def _show_placeholder_message(self, feature_name: str):
        """显示占位符提示信息"""
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(self, feature_name, f"{feature_name}功能即将实现...")

    def _on_manage_models_clicked(self):
        """
        Handle "管理模型" button click
        Opens the ModelBrowserDialog for browsing and selecting models
        """
        # Get current provider
        current_provider_id, _ = self.controller.get_current_model()

        # Open model browser dialog
        dialog = ModelBrowserDialog(self)
        dialog.model_selected.connect(self._on_model_activated_from_browser)
        dialog.exec()

    def _on_add_model_clicked(self):
        """
        Handle "添加模型" button click
        Opens the AddModelDialog for adding a custom model to current provider
        """
        # Get current provider
        current_provider_id, _ = self.controller.get_current_model()

        if not current_provider_id:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "无法添加模型", "请先选择一个服务商")
            return

        # Open add model dialog
        dialog = AddModelDialog(self, current_provider_id)
        dialog.model_added.connect(self._on_model_added)
        dialog.exec()

    def _on_model_added(self, model_id: str):
        """
        Handle model addition
        Refreshes the UI to show the newly added model

        Args:
            model_id: ID of the newly added model
        """
        # Refresh model tree to show new model
        if self.current_provider_id:
            self._populate_model_tree(self.current_provider_id)

        # Optionally select the new model
        current_provider_id, _ = self.controller.get_current_model()
        self.controller.set_current_model(current_provider_id, model_id)

    def _on_model_activated_from_browser(self, provider_id: str, model_id: str):
        """
        Handle model selection from browser dialog
        Updates the UI to reflect the newly selected model

        Args:
            provider_id: ID of the selected model's provider
            model_id: ID of the selected model
        """
        # The controller already set the model, just refresh UI
        self._load_providers()

    def _on_add_provider_clicked(self):
        """添加Provider按钮点击"""
        # TODO: US3.6 实现添加Provider对话框
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "添加供应商",
            "添加供应商功能即将实现...\n\n"
            "将支持:\n"
            "• 自定义供应商名称\n"
            "• 配置API地址\n"
            "• 添加API密钥\n"
            "• 导入模型列表",
        )

    def _on_provider_order_changed(self, provider_ids: list):
        """
        Provider顺序变化处理 (US4.3)

        Args:
            provider_ids: 新的provider顺序列表
        """
        # 通过ConfigController保存新的顺序
        self.controller.reorder_providers(provider_ids)

    # ==================== API测试相关方法 ====================

    def _on_test_api_clicked(self):
        """处理API测试按钮点击"""
        from PySide6.QtWidgets import QMessageBox

        # 验证输入
        if not self.current_provider_id:
            QMessageBox.warning(self, "提示", "请先选择一个供应商")
            return

        # 获取provider配置
        provider = self.controller.get_provider(self.current_provider_id)
        if not provider:
            QMessageBox.warning(self, "错误", "无法获取供应商配置")
            return

        # 获取API配置
        api_key = self.api_key_input.text().strip()
        api_url = self.api_url_input.text().strip()

        if not api_key:
            QMessageBox.warning(self, "提示", "请输入API密钥")
            self.api_key_input.setFocus()
            return

        if not api_url:
            QMessageBox.warning(self, "提示", "请输入API地址")
            self.api_url_input.setFocus()
            return

        # 获取第一个可用的模型ID
        models = provider.get("models", [])
        if not models:
            QMessageBox.warning(self, "错误", "该供应商没有配置模型")
            return

        model_id = models[0].get("id")
        if not model_id:
            QMessageBox.warning(self, "错误", "无法获取模型ID")
            return

        # 禁用按钮，显示loading状态
        self.api_test_btn.setEnabled(False)
        self.api_test_btn.setText("测试中...")

        # 启动API测试
        self.api_test_service.test_api(
            api_url=api_url, api_key=api_key, model_id=model_id
        )

    def _on_api_test_progress(self, message: str, current: int, total: int):
        """
        处理API测试进度更新

        Args:
            message: 进度消息
            current: 当前尝试次数
            total: 总尝试次数
        """
        # 更新按钮文本显示进度
        self.api_test_btn.setText(f"测试中 ({current}/{total})")

    def _on_api_test_finished(self, success: bool, message: str):
        """
        处理API测试完成

        Args:
            success: 是否成功
            message: 结果消息
        """
        from PySide6.QtWidgets import QMessageBox

        # 恢复按钮状态
        self.api_test_btn.setEnabled(True)
        self.api_test_btn.setText("检测")

        # 显示结果
        if success:
            QMessageBox.information(self, "连接成功", message)
        else:
            QMessageBox.critical(self, "连接失败", message)


# ==================== Provider List Widget with Drag-Drop ====================


class ProviderListWidget(QListWidget):
    """
    支持拖拽重排序的Provider列表 (US4.3)
    """

    # 信号定义
    order_changed = Signal(list)  # 发出新的provider_ids顺序列表

    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置拖拽起始距离阈值为10px,防止意外拖拽 (US4.3)
        from PySide6.QtWidgets import QApplication
        self.setDefaultDropAction(Qt.MoveAction)
        # 获取系统默认的拖拽距离(通常已经是合理的值)
        start_drag_distance = QApplication.startDragDistance()
        # 如果系统默认值小于10px,则设置为10px
        if start_drag_distance < 10:
            QApplication.setStartDragDistance(10)

    def dropEvent(self, event):
        """
        重写dropEvent以捕获拖拽完成后的新顺序

        Args:
            event: Drop事件
        """
        # 先执行默认的drop行为
        super().dropEvent(event)

        # 获取drop后的新顺序
        provider_ids = []
        for i in range(self.count()):
            item = self.item(i)
            provider_id = item.data(Qt.UserRole)
            if provider_id:
                provider_ids.append(provider_id)

        # 发送顺序变化信号
        if provider_ids:
            self.order_changed.emit(provider_ids)


# ==================== Provider List Item Widget ====================


class ProviderListItemWidget(QWidget):
    """
    Provider列表项Widget
    显示: [Icon] Provider Name [ON/OFF Toggle]
    """

    # 信号定义
    toggle_changed = Signal(bool)  # enabled状态变化

    def __init__(
        self, provider_id: str, provider_name: str, enabled: bool = True, parent=None
    ):
        super().__init__(parent)

        self.provider_id = provider_id
        self.provider_name = provider_name
        self._enabled = enabled
        self._is_hovered = False  # 悬浮状态
        self._is_selected = False  # 选中状态

        # 启用鼠标跟踪以检测hover
        self.setMouseTracking(True)

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        # 设置固定高度，确保所有项一致 - 减小到44px以留出margin空间
        self.setFixedHeight(44)

        # CRITICAL: 设置透明背景，让QListWidget的灰色背景能够显示
        self.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)  # 左右12px，上下8px确保垂直居中
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignVCenter)  # 垂直居中对齐

        # 拖拽手柄 "::" (US4.3)
        drag_handle = QLabel("::")
        from PySide6.QtGui import QFont
        handle_font = QFont(FONTS["body"])
        handle_font.setPixelSize(14)
        handle_font.setWeight(QFont.Bold)
        drag_handle.setFont(handle_font)
        drag_handle.setStyleSheet(
            f"color: {COLORS['text_tertiary']}; background-color: transparent; border: none;"
        )
        drag_handle.setCursor(Qt.SizeAllCursor)  # 改变光标为拖拽图标
        layout.addWidget(drag_handle, 0, Qt.AlignVCenter)

        # Provider 图标/徽章 (使用首字母)
        icon_label = QLabel(self._get_badge_text())
        icon_label.setFixedSize(28, 28)
        icon_label.setAlignment(Qt.AlignCenter)
        from PySide6.QtGui import QFont

        icon_font = QFont(FONTS["body"])
        icon_font.setPixelSize(14)
        icon_font.setWeight(QFont.Bold)
        icon_label.setFont(icon_font)
        icon_label.setStyleSheet(
            f"""
            background-color: {COLORS['accent_blue']};
            color: #FFFFFF;
            border-radius: 6px;
        """
        )
        layout.addWidget(icon_label, 0, Qt.AlignVCenter)

        # Provider 名称
        self.name_label = QLabel(self.provider_name)
        from PySide6.QtGui import QFont

        self.name_font = QFont(FONTS["body"])
        self.name_font.setPixelSize(14)
        self.name_label.setFont(self.name_font)
        self.name_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; background-color: transparent; border: none;"
        )
        layout.addWidget(self.name_label, 1, Qt.AlignVCenter)

        # ON/OFF 状态标签
        status_label = QLabel("ON" if self._enabled else "")
        from PySide6.QtGui import QFont

        status_font = QFont(FONTS["caption"])
        status_font.setPixelSize(11)
        status_font.setWeight(QFont.Bold)
        status_label.setFont(status_font)
        status_label.setStyleSheet(
            f"color: {COLORS['accent_green']}; background-color: transparent; border: none;"
        )
        layout.addWidget(status_label, 0, Qt.AlignVCenter)

        # 存储引用（用于更新）
        self.status_label = status_label

    def _get_badge_text(self) -> str:
        """获取徽章文本（首字母）"""
        if not self.provider_name:
            return "?"

        # 提取首字符（中文或英文）
        first_char = self.provider_name[0].upper()
        return first_char

    def toggle_enabled(self):
        """切换启用状态"""
        self._enabled = not self._enabled
        self.status_label.setText("ON" if self._enabled else "")
        self.toggle_changed.emit(self._enabled)

    def set_enabled(self, enabled: bool):
        """设置启用状态"""
        self._enabled = enabled
        self.status_label.setText("ON" if enabled else "")

    def is_enabled(self) -> bool:
        """获取启用状态"""
        return self._enabled

    def set_selected(self, selected: bool):
        """设置选中状态 - 选中时文字加粗"""
        from PySide6.QtGui import QFont

        self._is_selected = selected
        if selected:
            self.name_font.setWeight(QFont.Bold)
        else:
            self.name_font.setWeight(QFont.Normal)
        self.name_label.setFont(self.name_font)
        self.update()  # 触发重绘

    def enterEvent(self, event):
        """鼠标进入事件"""
        self._is_hovered = True
        self.update()  # 触发重绘
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self._is_hovered = False
        self.update()  # 触发重绘
        super().leaveEvent(event)

    def paintEvent(self, event):
        """绘制圆角背景"""
        from PySide6.QtGui import QPainter, QBrush, QColor, QPainterPath
        from PySide6.QtCore import QRectF

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿

        # 根据状态选择背景颜色
        if self._is_selected:
            bg_color = QColor("#F0F0F0")  # 选中时灰色
        elif self._is_hovered:
            bg_color = QColor("#F5F5F5")  # 悬浮时浅灰色
        else:
            bg_color = QColor("transparent")  # 默认透明

        # 绘制圆角矩形
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)  # 无边框

        # 创建圆角路径
        rect = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(rect, 15, 15)  # 6px圆角

        painter.drawPath(path)

        super().paintEvent(event)


# ==================== Model Category Card ====================


class ModelCategoryCard(QWidget):
    """
    模型分类卡片 - 可折叠的分类容器
    """

    # 信号定义
    model_selected = Signal(str, str)  # (provider_id, model_id)

    def __init__(
        self,
        category_name: str,
        models: list,
        current_model: str,
        provider_id: str,
        parent=None,
        is_expanded: bool = True,
    ):
        super().__init__(parent)

        self.category_name = category_name
        self.models = models
        self.current_model = current_model
        self.provider_id = provider_id
        self.is_expanded = is_expanded  # 支持从外部控制展开状态
        self.radio_buttons = []

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 卡片容器（带边框和圆角）
        card = QWidget()
        card.setStyleSheet(
            f"""
            QWidget {{
                background-color: #F9F9F9;
                border: 1px solid #E5E5E5;
                border-radius: 8px;
            }}
        """
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 标题栏（可点击折叠）
        header = QWidget()
        header.setFixedHeight(44)
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet(
            """
            QWidget {
                background-color: transparent;
                border: none;
            }
            QWidget:hover {
                background-color: #F0F0F0;
            }
        """
        )
        header.mousePressEvent = lambda e: self._toggle_expand()

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(8)

        # 折叠图标
        self.expand_icon = QLabel("▼" if self.is_expanded else "▶")
        from PySide6.QtGui import QFont

        icon_font = QFont(FONTS["body"])
        icon_font.setPixelSize(10)
        self.expand_icon.setFont(icon_font)
        self.expand_icon.setStyleSheet(
            f"color: {COLORS['text_secondary']}; border: none;"
        )
        header_layout.addWidget(self.expand_icon)

        # 分类标题
        title_label = QLabel(self.category_name)
        title_font = QFont(FONTS["body"])
        title_font.setPixelSize(14)
        title_font.setWeight(QFont.DemiBold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        header_layout.addWidget(title_label, stretch=1)

        # 模型数量
        count_label = QLabel(f"{len(self.models)}")
        count_font = QFont(FONTS["caption"])
        count_font.setPixelSize(12)
        count_label.setFont(count_font)
        count_label.setStyleSheet(f"color: {COLORS['text_tertiary']}; border: none;")
        header_layout.addWidget(count_label)

        card_layout.addWidget(header)

        # 模型列表容器
        self.models_container = QWidget()
        self.models_container.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        models_layout = QVBoxLayout(self.models_container)
        models_layout.setContentsMargins(0, 0, 0, 0)
        models_layout.setSpacing(0)

        # 添加模型项
        for model in self.models:
            model_id = model.get("id", "")
            model_name = model.get("name", model_id)
            context_length = model.get("context_length", 0)

            # 格式化元数据
            metadata = ""
            if context_length > 0:
                if context_length >= 1000:
                    metadata = f"{context_length // 1000}K"
                else:
                    metadata = str(context_length)

            # 检查是否为当前激活的模型
            is_active = model_id == self.current_model

            # 创建模型项
            model_widget = ModelCardItem(
                model_id=model_id,
                model_name=model_name,
                metadata=metadata,
                is_active=is_active,
                parent=self.models_container,
            )

            # 连接信号
            model_widget.model_selected.connect(
                lambda mid=model_id: self.model_selected.emit(self.provider_id, mid)
            )

            # 保存radio button引用
            self.radio_buttons.append(model_widget.radio_btn)

            models_layout.addWidget(model_widget)

        card_layout.addWidget(self.models_container)

        main_layout.addWidget(card)

    def _toggle_expand(self):
        """切换展开/折叠状态"""
        self.is_expanded = not self.is_expanded
        self.models_container.setVisible(self.is_expanded)
        self.expand_icon.setText("▼" if self.is_expanded else "▶")

    def get_radio_buttons(self):
        """获取所有radio buttons"""
        return self.radio_buttons


# ==================== Model Card Item ====================


class ModelCardItem(QWidget):
    """
    模型卡片项 - 在分类卡片内的单个模型项
    """

    # 信号定义
    model_selected = Signal(str)  # model_id

    def __init__(
        self,
        model_id: str,
        model_name: str,
        metadata: str = "",
        is_active: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self.model_id = model_id
        self.model_name = model_name
        self.metadata = metadata
        self._is_active = is_active

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setFixedHeight(40)
        self.setStyleSheet(
            """
            QWidget {
                background-color: transparent;
                border: none;
            }
            QWidget:hover {
                background-color: #F0F0F0;
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignVCenter)

        # Radio button
        from PySide6.QtWidgets import QRadioButton

        self.radio_btn = QRadioButton()
        self.radio_btn.setChecked(self._is_active)
        self.radio_btn.toggled.connect(self._on_radio_toggled)
        self.radio_btn.setStyleSheet(
            f"""
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
            }}
            QRadioButton::indicator:unchecked {{
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                background-color: #FFFFFF;
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {COLORS['accent_blue']};
                border-radius: 8px;
                background-color: {COLORS['accent_blue']};
            }}
        """
        )
        layout.addWidget(self.radio_btn, 0, Qt.AlignVCenter)

        # Model name
        name_label = QLabel(self.model_name)
        from PySide6.QtGui import QFont

        name_font = QFont(FONTS["body"])
        name_font.setPixelSize(14)
        name_label.setFont(name_font)
        name_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        layout.addWidget(name_label, 1, Qt.AlignVCenter)

        # Metadata badge
        if self.metadata:
            metadata_label = QLabel(self.metadata)
            metadata_font = QFont(FONTS["caption"])
            metadata_font.setPixelSize(11)
            metadata_label.setFont(metadata_font)
            metadata_label.setStyleSheet(
                f"""
                color: {COLORS['text_tertiary']};
                background-color: #E5E5E5;
                padding: 2px 8px;
                border-radius: 4px;
                border: none;
            """
            )
            layout.addWidget(metadata_label, 0, Qt.AlignVCenter)

    def _on_radio_toggled(self, checked: bool):
        """Radio button切换"""
        if checked:
            self.model_selected.emit(self.model_id)

    def set_active(self, active: bool):
        """设置激活状态"""
        self._is_active = active
        self.radio_btn.setChecked(active)


# ==================== Model Item Widget ====================


class ModelItemWidget(QWidget):
    """
    模型列表项Widget (US3.4)
    显示: [Radio Button] Model Name [Metadata Badge]
    """

    # 信号定义
    model_selected = Signal(str)  # model_id

    def __init__(
        self,
        model_id: str,
        model_name: str,
        metadata: str = "",
        is_active: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self.model_id = model_id
        self.model_name = model_name
        self.metadata = metadata
        self._is_active = is_active

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(SPACING["sm"])

        # Radio button
        from PySide6.QtWidgets import QRadioButton

        self.radio_btn = QRadioButton()
        self.radio_btn.setChecked(self._is_active)
        self.radio_btn.toggled.connect(self._on_radio_toggled)
        self.radio_btn.setStyleSheet(
            f"""
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
            }}
            QRadioButton::indicator:unchecked {{
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                background-color: {COLORS['bg_main']};
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {COLORS['accent_blue']};
                border-radius: 8px;
                background-color: {COLORS['accent_blue']};
            }}
        """
        )
        layout.addWidget(self.radio_btn)

        # Model name
        name_label = QLabel(self.model_name)
        name_label.setFont(FONTS["body"])
        name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(name_label, stretch=1)

        # Metadata badge (e.g., "128K")
        if self.metadata:
            metadata_label = QLabel(self.metadata)
            metadata_label.setFont(FONTS["caption"])
            metadata_label.setStyleSheet(
                f"""
                color: {COLORS['text_tertiary']};
                background-color: {COLORS['bg_hover']};
                padding: 2px 6px;
                border-radius: 3px;
            """
            )
            layout.addWidget(metadata_label)

    def _on_radio_toggled(self, checked: bool):
        """Radio button切换"""
        if checked:
            self.model_selected.emit(self.model_id)

    def set_active(self, active: bool):
        """设置激活状态"""
        self._is_active = active
        self.radio_btn.setChecked(active)

    def is_active(self) -> bool:
        """获取激活状态"""
        return self._is_active


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)

    # 创建测试主窗口
    main_window = QMainWindow()
    main_window.setWindowTitle("ModelConfigDialog Test")
    main_window.resize(400, 300)

    # 创建中心部件
    central = QWidget()
    main_window.setCentralWidget(central)

    layout = QVBoxLayout(central)

    # 测试按钮
    test_button = QPushButton("打开模型配置对话框")
    test_button.clicked.connect(lambda: ModelConfigDialog(main_window).exec())
    layout.addWidget(test_button)

    # 信息标签
    info_label = QLabel(
        "US3.1: Dialog Structure Test\n\n"
        "预期看到:\n"
        "• 1200×800px 对话框\n"
        "• 左面板 350px (浅灰背景)\n"
        "• 右面板 850px (白色背景)\n"
        "• 1px 分隔线\n"
        "• Modal 行为（阻止父窗口交互）"
    )
    info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    info_label.setFont(FONTS["body_small"])
    layout.addWidget(info_label, stretch=1)

    main_window.show()
    sys.exit(app.exec())
