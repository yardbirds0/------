# -*- coding: utf-8 -*-
"""
主界面版本的分析面板
与AI助手窗口的分析面板功能相同，但样式适配主界面
"""

from typing import Dict, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QGroupBox,
)

from models import (
    AnalysisPanelState,
    AnalysisTargetColumn,
    AnalysisSourceSheet,
    AnalysisSourceColumn,
)


class SimpleToggleSwitch(QWidget):
    """简化版的开关控件 - 主界面风格"""

    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(44, 24)
        self.setCursor(Qt.PointingHandCursor)

    def setChecked(self, checked: bool):
        self._checked = checked
        self.update()

    def isChecked(self) -> bool:
        return self._checked

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QColor, QPen

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景轨道
        if self._checked:
            bg_color = QColor("#10B981")  # 绿色
        else:
            bg_color = QColor("#D1D5DB")  # 灰色

        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(0, 0, 44, 24, 12, 12)

        # 滑块
        circle_x = 22 if self._checked else 2
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(circle_x, 2, 20, 20)


class MainAnalysisPanel(QWidget):
    """主界面版本的分析面板 - 功能与AI助手一致，样式适配主界面"""

    target_sheet_changed = Signal(str)
    target_column_toggled = Signal(str, bool)
    source_column_toggled = Signal(str, str, bool)
    apply_requested = Signal()
    auto_parse_requested = Signal()
    export_json_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._state = AnalysisPanelState()
        self._updating = False
        self._target_toggle_map: Dict[str, SimpleToggleSwitch] = {}
        self._source_toggle_map: Dict[str, Dict[str, SimpleToggleSwitch]] = {}
        self._source_section_widgets: Dict[str, QWidget] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        """构建UI - 主界面风格"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)

        # ========== 分析表格区域 ==========
        target_group = QGroupBox("📊 分析表格")
        target_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        target_layout = QVBoxLayout(target_group)
        target_layout.setContentsMargins(10, 15, 10, 10)
        target_layout.setSpacing(8)

        # 工作表选择
        combo_row = QHBoxLayout()
        combo_row.setSpacing(8)

        combo_label = QLabel("当前表格：")
        combo_label.setStyleSheet("font-weight: normal; font-size: 12px;")
        self.target_combo = QComboBox()
        self.target_combo.setMinimumHeight(28)
        self.target_combo.currentTextChanged.connect(self._on_target_sheet_changed)

        combo_row.addWidget(combo_label)
        combo_row.addWidget(self.target_combo, 1)
        target_layout.addLayout(combo_row)

        # 目标列列表
        self.target_scroll = QScrollArea()
        self.target_scroll.setWidgetResizable(True)
        self.target_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.target_scroll.setFrameShape(QFrame.StyledPanel)
        self.target_scroll.setStyleSheet("QScrollArea { border: 1px solid #e0e0e0; border-radius: 3px; }")

        target_scroll_content = QWidget()
        self.target_list_layout = QVBoxLayout(target_scroll_content)
        self.target_list_layout.setContentsMargins(5, 5, 5, 5)
        self.target_list_layout.setSpacing(4)
        self.target_list_layout.addStretch()
        self.target_scroll.setWidget(target_scroll_content)

        self.target_placeholder = QLabel("暂无可选择的列")
        self.target_placeholder.setAlignment(Qt.AlignCenter)
        self.target_placeholder.setStyleSheet("color: #999; padding: 20px;")

        target_layout.addWidget(self.target_scroll)
        target_layout.addWidget(self.target_placeholder)
        self.target_placeholder.hide()

        main_layout.addWidget(target_group)

        # ========== 来源项表区域 ==========
        source_group = QGroupBox("📋 来源项表")
        source_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        source_layout = QVBoxLayout(source_group)
        source_layout.setContentsMargins(10, 15, 10, 10)
        source_layout.setSpacing(8)

        # 来源列列表
        self.source_scroll = QScrollArea()
        self.source_scroll.setWidgetResizable(True)
        self.source_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.source_scroll.setFrameShape(QFrame.StyledPanel)
        self.source_scroll.setStyleSheet("QScrollArea { border: 1px solid #e0e0e0; border-radius: 3px; }")

        source_scroll_content = QWidget()
        self.source_list_layout = QVBoxLayout(source_scroll_content)
        self.source_list_layout.setContentsMargins(5, 5, 5, 5)
        self.source_list_layout.setSpacing(6)
        self.source_list_layout.addStretch()
        self.source_scroll.setWidget(source_scroll_content)

        self.source_placeholder = QLabel("暂无来源项数据")
        self.source_placeholder.setAlignment(Qt.AlignCenter)
        self.source_placeholder.setStyleSheet("color: #999; padding: 20px;")

        source_layout.addWidget(self.source_scroll)
        source_layout.addWidget(self.source_placeholder)
        self.source_placeholder.hide()

        main_layout.addWidget(source_group, 1)

        # ========== 警告提示区域 ==========
        self.warning_frame = QFrame()
        self.warning_frame.setStyleSheet("""
            QFrame {
                background-color: #FFF7ED;
                border: 1px solid #F59E0B;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        self.warning_frame.setMaximumHeight(120)

        warning_layout = QVBoxLayout(self.warning_frame)
        warning_layout.setContentsMargins(8, 8, 8, 8)
        warning_layout.setSpacing(4)

        warning_title = QLabel("⚠️ 标识符提示")
        warning_title.setStyleSheet("color: #F59E0B; font-weight: bold;")
        warning_layout.addWidget(warning_title)

        self.warning_label = QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #1F2937; font-size: 12px;")
        warning_layout.addWidget(self.warning_label)

        self.warning_frame.hide()
        main_layout.addWidget(self.warning_frame)

        # ========== 操作按钮区域 ==========
        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        # 一键解析
        self.auto_parse_button = QPushButton("🚀 一键解析")
        self.auto_parse_button.setMinimumHeight(32)
        self.auto_parse_button.setCursor(Qt.PointingHandCursor)
        self.auto_parse_button.clicked.connect(self.auto_parse_requested.emit)
        self.auto_parse_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
            QPushButton:disabled {
                background-color: #E5E7EB;
                color: #9CA3AF;
            }
        """)
        button_row.addWidget(self.auto_parse_button)

        # 导出JSON
        self.export_json_button = QPushButton("📄 导出JSON")
        self.export_json_button.setMinimumHeight(32)
        self.export_json_button.setCursor(Qt.PointingHandCursor)
        self.export_json_button.clicked.connect(self.export_json_requested.emit)
        self.export_json_button.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
            QPushButton:disabled {
                background-color: #E5E7EB;
                color: #9CA3AF;
            }
        """)
        button_row.addWidget(self.export_json_button)

        button_row.addStretch()

        # 解析应用
        self.apply_button = QPushButton("解析应用")
        self.apply_button.setMinimumHeight(32)
        self.apply_button.setCursor(Qt.PointingHandCursor)
        self.apply_button.clicked.connect(self.apply_requested.emit)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #1F2937;
                border: 1px solid #D1D5DB;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
            QPushButton:pressed {
                background-color: #D1D5DB;
            }
            QPushButton:disabled {
                background-color: #F9FAFB;
                color: #9CA3AF;
            }
        """)
        button_row.addWidget(self.apply_button)

        main_layout.addLayout(button_row)

        self._update_placeholders()
        self._update_button_states()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_state(self, state: AnalysisPanelState) -> None:
        """刷新UI状态"""
        self._state = state
        self._updating = True

        try:
            self._populate_target_combo(state)
            self._populate_target_columns(state.target_columns)
            self._populate_source_sheets(state.source_sheets)
            self._update_warnings(state.warnings if hasattr(state, "warnings") else [])

            self.apply_button.setEnabled(state.has_workbook)
            self.auto_parse_button.setEnabled(state.has_workbook and bool(state.target_columns))
            self.export_json_button.setEnabled(state.has_workbook and bool(state.target_columns))
        finally:
            self._updating = False

        self._update_placeholders()
        self._update_button_states()

    def block_interactions(self, blocked: bool) -> None:
        """锁定/解锁面板交互"""
        self.setEnabled(not blocked)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _populate_target_combo(self, state: AnalysisPanelState) -> None:
        self.target_combo.blockSignals(True)
        self.target_combo.clear()

        if not state.has_workbook or not state.target_sheets:
            self.target_combo.addItem("暂无待写入表格")
            self.target_combo.setEnabled(False)
        else:
            for sheet_name in state.target_sheets:
                self.target_combo.addItem(sheet_name)

            if state.current_target_sheet and state.current_target_sheet in state.target_sheets:
                self.target_combo.setCurrentText(state.current_target_sheet)
            else:
                self.target_combo.setCurrentIndex(0)
            self.target_combo.setEnabled(True)

        self.target_combo.blockSignals(False)

    def _populate_target_columns(self, columns: list) -> None:
        self._clear_layout(self.target_list_layout, preserve_stretch=True)
        self._target_toggle_map.clear()

        if not columns:
            self.target_scroll.hide()
            self.target_placeholder.show()
            return

        for column in columns:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 2, 4, 2)
            row_layout.setSpacing(8)

            label = QLabel(column.display_name)
            label.setStyleSheet("color: #1F2937; font-size: 13px;")
            row_layout.addWidget(label)
            row_layout.addStretch(1)

            toggle = SimpleToggleSwitch()
            toggle.setChecked(column.checked)
            toggle.setEnabled(not column.disabled)
            if column.tooltip:
                row.setToolTip(column.tooltip)
            toggle.toggled.connect(
                lambda state, key=column.key: self._on_target_column_toggled(key, state)
            )
            row_layout.addWidget(toggle)

            self._target_toggle_map[column.key] = toggle
            self.target_list_layout.insertWidget(self.target_list_layout.count() - 1, row)

        self.target_scroll.show()
        self.target_placeholder.hide()

    def _populate_source_sheets(self, sheets: list) -> None:
        self._clear_layout(self.source_list_layout, preserve_stretch=True)
        self._source_toggle_map.clear()
        self._source_section_widgets.clear()

        if not sheets:
            self.source_scroll.hide()
            self.source_placeholder.show()
            return

        for sheet in sheets:
            section_widget = QWidget()
            section_layout = QVBoxLayout(section_widget)
            section_layout.setContentsMargins(0, 0, 0, 0)
            section_layout.setSpacing(4)

            # 工作表标题（可折叠）
            header_button = QToolButton()
            header_button.setText(sheet.display_name)
            header_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            header_button.setCheckable(True)
            header_button.setChecked(sheet.expanded)
            header_button.setArrowType(Qt.DownArrow if sheet.expanded else Qt.RightArrow)
            header_button.setStyleSheet("""
                QToolButton {
                    background-color: transparent;
                    border: none;
                    color: #1F2937;
                    font-weight: bold;
                    text-align: left;
                    padding: 4px;
                }
                QToolButton:hover {
                    color: #3B82F6;
                }
            """)
            section_layout.addWidget(header_button)

            # 列列表容器
            columns_container = QWidget()
            columns_layout = QVBoxLayout(columns_container)
            columns_layout.setContentsMargins(16, 0, 8, 4)
            columns_layout.setSpacing(4)

            toggle_map: Dict[str, SimpleToggleSwitch] = {}
            for column in sheet.columns:
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(4, 2, 4, 2)
                row_layout.setSpacing(8)

                label = QLabel(column.display_name)
                label.setStyleSheet("color: #374151; font-size: 12px;")
                row_layout.addWidget(label)
                row_layout.addStretch(1)

                toggle = SimpleToggleSwitch()
                toggle.setChecked(column.checked)
                if column.tooltip:
                    row.setToolTip(column.tooltip)
                toggle.toggled.connect(
                    lambda state, sheet_name=sheet.sheet_name, key=column.key:
                    self._on_source_column_toggled(sheet_name, key, state)
                )
                row_layout.addWidget(toggle)

                columns_layout.addWidget(row)
                toggle_map[column.key] = toggle

            columns_layout.addStretch()
            columns_container.setVisible(sheet.expanded)
            header_button.toggled.connect(
                lambda checked, container=columns_container, btn=header_button:
                self._toggle_section(container, btn, checked)
            )

            section_layout.addWidget(columns_container)
            self.source_list_layout.insertWidget(
                self.source_list_layout.count() - 1, section_widget
            )

            self._source_toggle_map[sheet.sheet_name] = toggle_map
            self._source_section_widgets[sheet.sheet_name] = section_widget

        self.source_scroll.show()
        self.source_placeholder.hide()

    def _update_warnings(self, warnings: list) -> None:
        if warnings:
            formatted = "\n".join(f"• {message}" for message in warnings)
            self.warning_label.setText(formatted)
            self.warning_frame.show()
        else:
            self.warning_label.clear()
            self.warning_frame.hide()

    def _toggle_section(self, container: QWidget, button: QToolButton, expanded: bool) -> None:
        container.setVisible(expanded)
        button.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)

    def _on_target_sheet_changed(self, sheet_name: str) -> None:
        if self._updating:
            return
        if not sheet_name or not self.target_combo.isEnabled():
            return
        self.target_sheet_changed.emit(sheet_name)

    def _on_target_column_toggled(self, column_key: str, checked: bool) -> None:
        if self._updating:
            return
        self.target_column_toggled.emit(column_key, checked)

    def _on_source_column_toggled(self, sheet_name: str, column_key: str, checked: bool) -> None:
        if self._updating:
            return
        self.source_column_toggled.emit(sheet_name, column_key, checked)

    def _update_placeholders(self) -> None:
        show_target_placeholder = not self._state.has_workbook or not self._state.target_columns
        self.target_placeholder.setVisible(show_target_placeholder)
        self.target_scroll.setVisible(not show_target_placeholder)

        show_source_placeholder = not self._state.has_workbook or not self._state.source_sheets
        self.source_placeholder.setVisible(show_source_placeholder)
        self.source_scroll.setVisible(not show_source_placeholder)

    def _update_button_states(self) -> None:
        self.apply_button.setEnabled(self._state.has_workbook)
        self.auto_parse_button.setEnabled(
            self._state.has_workbook and bool(self._state.target_columns)
        )
        self.export_json_button.setEnabled(
            self._state.has_workbook and bool(self._state.target_columns)
        )

    @staticmethod
    def _clear_layout(layout: QVBoxLayout, *, preserve_stretch: bool = False) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                MainAnalysisPanel._clear_layout(item.layout())
            if preserve_stretch and layout.count() == 0:
                break
        if preserve_stretch:
            layout.addStretch()
