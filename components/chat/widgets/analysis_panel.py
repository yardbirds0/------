# -*- coding: utf-8 -*-
"""
Analysis tab widget used inside the Cherry sidebar.
"""

from __future__ import annotations

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
)

from ..styles.cherry_theme import COLORS, FONTS, SPACING, SIZES
from models import (
    AnalysisPanelState,
    AnalysisTargetColumn,
    AnalysisSourceSheet,
    AnalysisSourceColumn,
)
from .common_widgets import ToggleSwitch


class _CardFrame(QFrame):
    """Matches the visual style of settings groups."""

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {COLORS['bg_main']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius']}px;
            }}
            """
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(
            SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"]
        )
        self._layout.setSpacing(SPACING["md"])

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING["sm"])

        title_label = QLabel(title)
        title_font = FONTS["subtitle"].__class__(FONTS["subtitle"])
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        header_layout.addWidget(title_label, stretch=1)
        self._layout.addLayout(header_layout)

    @property
    def body_layout(self) -> QVBoxLayout:
        return self._layout


class AnalysisPanel(QWidget):
    """Analysis tab with target/source selections and action buttons."""

    target_sheet_changed = Signal(str)
    target_column_toggled = Signal(str, bool)
    source_column_toggled = Signal(str, str, bool)
    apply_requested = Signal()
    auto_parse_requested = Signal()  # 一键解析信号
    export_json_requested = Signal()  # 导出JSON信号

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._state = AnalysisPanelState()
        self._updating = False
        self._target_toggle_map: Dict[str, ToggleSwitch] = {}
        self._source_toggle_map: Dict[str, Dict[str, ToggleSwitch]] = {}
        self._source_section_widgets: Dict[str, QWidget] = {}

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"]
        )
        root_layout.setSpacing(SPACING["md"])

        # Target group
        self.target_card = _CardFrame("分析表格", self)
        target_layout = self.target_card.body_layout

        combo_row = QHBoxLayout()
        combo_row.setContentsMargins(0, 0, 0, 0)
        combo_row.setSpacing(SPACING["sm"])

        self.target_combo = QComboBox()
        self.target_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.target_combo.setMinimumHeight(34)
        self.target_combo.currentTextChanged.connect(self._on_target_sheet_changed)
        combo_row.addWidget(QLabel("当前表格："))
        combo_row.addWidget(self.target_combo)

        target_layout.addLayout(combo_row)

        self.target_placeholder = QLabel("暂无可选择的列")
        self.target_placeholder.setAlignment(Qt.AlignCenter)
        self.target_placeholder.setStyleSheet(
            f"color: {COLORS['text_tertiary']}; padding: {SPACING['md']}px;"
        )

        self.target_scroll = QScrollArea()
        self.target_scroll.setWidgetResizable(True)
        self.target_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.target_scroll.setFrameShape(QFrame.NoFrame)
        target_scroll_content = QWidget()
        self.target_list_layout = QVBoxLayout(target_scroll_content)
        self.target_list_layout.setContentsMargins(0, 0, 0, 0)
        self.target_list_layout.setSpacing(SPACING["xs"])
        self.target_list_layout.addStretch()
        self.target_scroll.setWidget(target_scroll_content)
        target_layout.addWidget(self.target_scroll)

        root_layout.addWidget(self.target_card)

        # Source group
        self.source_card = _CardFrame("来源项表", self)
        source_layout = self.source_card.body_layout

        self.source_placeholder = QLabel("暂无来源项数据")
        self.source_placeholder.setAlignment(Qt.AlignCenter)
        self.source_placeholder.setStyleSheet(
            f"color: {COLORS['text_tertiary']}; padding: {SPACING['md']}px;"
        )

        self.source_scroll = QScrollArea()
        self.source_scroll.setWidgetResizable(True)
        self.source_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.source_scroll.setFrameShape(QFrame.NoFrame)
        source_scroll_content = QWidget()
        self.source_list_layout = QVBoxLayout(source_scroll_content)
        self.source_list_layout.setContentsMargins(0, 0, 0, 0)
        self.source_list_layout.setSpacing(SPACING["sm"])
        self.source_list_layout.addStretch()
        self.source_scroll.setWidget(source_scroll_content)
        source_layout.addWidget(self.source_scroll)

        root_layout.addWidget(self.source_card, stretch=1)

        self.warning_frame = QFrame()
        self.warning_frame.setObjectName("analysis-warning-frame")
        self.warning_frame.setStyleSheet(
            "#analysis-warning-frame {"
            f"background-color: rgba(245, 158, 11, 0.08);"
            f"border: 1px solid {COLORS['accent_yellow']};"
            f"border-radius: {SIZES['border_radius']}px;"
            "}"
        )
        self.warning_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.warning_frame.setMaximumHeight(180)

        warning_layout = QVBoxLayout(self.warning_frame)
        warning_layout.setContentsMargins(
            SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"]
        )
        warning_layout.setSpacing(SPACING["xs"])

        warning_title = QLabel("标识符提示")
        warning_title.setStyleSheet(
            f"color: {COLORS['accent_yellow']}; font-weight: 600;"
        )
        warning_layout.addWidget(warning_title)

        self.warning_scroll = QScrollArea()
        self.warning_scroll.setWidgetResizable(True)
        self.warning_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.warning_scroll.setFrameShape(QFrame.NoFrame)
        self.warning_scroll.setStyleSheet(
            f"background-color: transparent; border: none;"
        )

        warning_content = QWidget()
        warning_content_layout = QVBoxLayout(warning_content)
        warning_content_layout.setContentsMargins(0, 0, 0, 0)
        warning_content_layout.setSpacing(0)

        self.warning_label = QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.warning_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 13px;"
        )
        warning_content_layout.addWidget(self.warning_label)

        self.warning_scroll.setWidget(warning_content)
        warning_layout.addWidget(self.warning_scroll)

        self.warning_frame.hide()
        root_layout.addWidget(self.warning_frame)

        # Buttons
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(SPACING["sm"])

        # 一键解析按钮（左侧）
        self.auto_parse_button = QPushButton("🚀 一键解析")
        self.auto_parse_button.setMinimumHeight(36)
        self.auto_parse_button.clicked.connect(self.auto_parse_requested.emit)
        self.auto_parse_button.setCursor(Qt.PointingHandCursor)
        self.auto_parse_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: {SIZES['border_radius']}px;
                padding: 0px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2563EB;
            }}
            QPushButton:pressed {{
                background-color: #1D4ED8;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_tertiary']};
            }}
        """)
        button_row.addWidget(self.auto_parse_button)

        # 导出JSON按钮（一键解析右侧）
        self.export_json_button = QPushButton("📄 导出JSON")
        self.export_json_button.setMinimumHeight(36)
        self.export_json_button.clicked.connect(self.export_json_requested.emit)
        self.export_json_button.setCursor(Qt.PointingHandCursor)
        self.export_json_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_green']};
                color: white;
                border: none;
                border-radius: {SIZES['border_radius']}px;
                padding: 0px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
            QPushButton:pressed {{
                background-color: #047857;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_tertiary']};
            }}
        """)
        button_row.addWidget(self.export_json_button)

        button_row.addStretch()

        self.apply_button = QPushButton("解析应用")
        self.apply_button.setMinimumHeight(36)
        self.apply_button.clicked.connect(self.apply_requested.emit)
        self.apply_button.setCursor(Qt.PointingHandCursor)
        button_row.addWidget(self.apply_button)

        root_layout.addLayout(button_row)
        root_layout.addStretch()

        self._update_placeholders()
        self._update_button_states()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_state(self, state: AnalysisPanelState) -> None:
        """Refreshes the UI based on the provided state."""

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

    def _populate_target_columns(self, columns: list[AnalysisTargetColumn]) -> None:
        self._clear_layout(self.target_list_layout, preserve_stretch=True)
        self._target_toggle_map.clear()

        if not columns:
            self.target_scroll.hide()
            return

        for column in columns:
            row = QWidget()
            row.setAttribute(Qt.WA_StyledBackground, True)
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(SPACING["sm"])

            label = QLabel(column.display_name)
            label.setStyleSheet(
                f"color: {COLORS['text_primary']}; font-size: 14px; background: transparent;"
            )
            row_layout.addWidget(label)
            row_layout.addStretch(1)

            toggle = ToggleSwitch()
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

    def _populate_source_sheets(self, sheets: list[AnalysisSourceSheet]) -> None:
        self._clear_layout(self.source_list_layout, preserve_stretch=True)
        self._source_toggle_map.clear()
        self._source_section_widgets.clear()

        if not sheets:
            self.source_scroll.hide()
            return

        for sheet in sheets:
            section_widget = QWidget()
            section_layout = QVBoxLayout(section_widget)
            section_layout.setContentsMargins(0, 0, 0, 0)
            section_layout.setSpacing(SPACING["xs"])

            header_button = QToolButton()
            header_button.setText(sheet.display_name)
            header_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            header_button.setCheckable(True)
            header_button.setChecked(sheet.expanded)
            header_button.setArrowType(Qt.DownArrow if sheet.expanded else Qt.RightArrow)
            header_button.setStyleSheet(
                f"""
                QToolButton {{
                    background-color: transparent;
                    border: none;
                    color: {COLORS['text_primary']};
                    font-weight: bold;
                    text-align: left;
                    padding: {SPACING['xs']}px;
                }}
                QToolButton:hover {{
                    color: {COLORS['accent_blue']};
                }}
                """
            )
            section_layout.addWidget(header_button)

            columns_container = QWidget()
            columns_layout = QVBoxLayout(columns_container)
            columns_layout.setContentsMargins(
                SPACING["sm"], 0, SPACING["sm"], SPACING["xs"]
            )
            columns_layout.setSpacing(SPACING["xs"])

            toggle_map: Dict[str, ToggleSwitch] = {}
            for column in sheet.columns:
                row = QWidget()
                row.setAttribute(Qt.WA_StyledBackground, True)
                row.setStyleSheet("background: transparent;")
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(SPACING["xs"])

                label = QLabel(column.display_name)
                label.setStyleSheet(
                    f"color: {COLORS['text_primary']}; font-size: 13px; background: transparent;"
                )
                row_layout.addWidget(label)
                row_layout.addStretch(1)

                toggle = ToggleSwitch()
                toggle.setChecked(column.checked)
                if column.tooltip:
                    row.setToolTip(column.tooltip)
                toggle.toggled.connect(
                    lambda state, sheet_name=sheet.sheet_name, key=column.key: self._on_source_column_toggled(
                        sheet_name, key, state
                    )
                )
                row_layout.addWidget(toggle)

                columns_layout.addWidget(row)
                toggle_map[column.key] = toggle

            columns_layout.addStretch()
            columns_container.setVisible(sheet.expanded)
            header_button.toggled.connect(
                lambda checked, container=columns_container, btn=header_button: self._toggle_section(
                    container, btn, checked
                )
            )

            section_layout.addWidget(columns_container)
            self.source_list_layout.insertWidget(
                self.source_list_layout.count() - 1, section_widget
            )

            self._source_toggle_map[sheet.sheet_name] = toggle_map
            self._source_section_widgets[sheet.sheet_name] = section_widget

        self.source_scroll.show()

    def _update_warnings(self, warnings: list[str]) -> None:
        if warnings:
            formatted = "\n".join(f"• {message}" for message in warnings)
            self.warning_label.setText(formatted)
            self.warning_frame.show()
            if hasattr(self.warning_scroll, "verticalScrollBar"):
                self.warning_scroll.verticalScrollBar().setValue(0)
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

    def _on_source_column_toggled(
        self, sheet_name: str, column_key: str, checked: bool
    ) -> None:
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

        if show_target_placeholder and self.target_placeholder.parent() != self.target_card:
            self.target_card.layout().addWidget(self.target_placeholder)
        if show_source_placeholder and self.source_placeholder.parent() != self.source_card:
            self.source_card.layout().addWidget(self.source_placeholder)

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
                AnalysisPanel._clear_layout(item.layout())
            if preserve_stretch and layout.count() == 0:
                break
        if preserve_stretch:
            layout.addStretch()
