# -*- coding: utf-8 -*-
"""Debug panel widget shown inside the sidebar."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor, QTextOption
from PySide6.QtWidgets import QFrame, QLabel, QPlainTextEdit, QVBoxLayout, QWidget, QSizePolicy

from ..styles.cherry_theme import COLORS, FONTS, SPACING, SIZES


class _PreviewTextEdit(QPlainTextEdit):
    clicked = Signal()

    def mousePressEvent(self, event):  # type: ignore[override]
        super().mousePressEvent(event)
        self.clicked.emit()


class CherryDebugPanel(QWidget):
    """Container that mirrors the styling of a settings group."""

    panel_clicked = Signal()
    analysis_panel_clicked = Signal()

    CHAT_PLACEHOLDER = "暂无请求头数据"
    ANALYSIS_PLACEHOLDER = "暂无表格分析请求"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sections: dict[str, dict[str, object]] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        self.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"]
        )
        root_layout.setSpacing(SPACING["md"])

        chat_frame, chat_edit = self._create_section("调试请求头")
        chat_edit.clicked.connect(self.panel_clicked.emit)
        root_layout.addWidget(chat_frame)

        analysis_frame, analysis_edit = self._create_section("表格分析请求头")
        analysis_edit.clicked.connect(self.analysis_panel_clicked.emit)
        root_layout.addWidget(analysis_frame)

        root_layout.addStretch(1)

        self._sections = {
            "chat": {
                "edit": chat_edit,
                "placeholder": self.CHAT_PLACEHOLDER,
                "is_placeholder": True,
                "last_text": "",
            },
            "analysis": {
                "edit": analysis_edit,
                "placeholder": self.ANALYSIS_PLACEHOLDER,
                "is_placeholder": True,
                "last_text": "",
            },
        }

        self._apply_placeholder("chat")
        self._apply_placeholder("analysis")

    def _create_section(self, title: str) -> tuple[QFrame, _PreviewTextEdit]:
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {COLORS['bg_main']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius']}px;
            }}
            """
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(
            SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"]
        )
        layout.setSpacing(SPACING["sm"])

        title_label = QLabel(title)
        title_font = FONTS["subtitle"].__class__(FONTS["subtitle"])
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        title_label.setWordWrap(False)
        title_label.setSizePolicy(
            title_label.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed
        )
        title_label.setFixedHeight(title_label.fontMetrics().height())
        layout.addWidget(title_label)

        edit = _PreviewTextEdit()
        edit.setReadOnly(True)
        code_font = FONTS["code"].__class__(FONTS["code"])
        edit.setFont(code_font)
        edit.setFixedHeight(110)
        edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        edit.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background-color: {COLORS['bg_main']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {SIZES['border_radius']}px;
                padding: 8px;
            }}
            QPlainTextEdit:focus {{
                border: 1px solid {COLORS['border_focus']};
            }}
            """
        )
        layout.addWidget(edit)
        return frame, edit

    # ------------------------------------------------------------------
    def set_chat_preview(self, text: str, *, is_placeholder: bool) -> None:
        self._set_preview("chat", text, is_placeholder)

    def set_analysis_preview(self, text: str, *, is_placeholder: bool) -> None:
        self._set_preview("analysis", text, is_placeholder)

    def _set_preview(self, section: str, text: str, is_placeholder: bool) -> None:
        if section not in self._sections:
            return

        state = self._sections[section]
        edit: _PreviewTextEdit = state["edit"]  # type: ignore[assignment]

        if is_placeholder:
            self._apply_placeholder(section)
            return

        last_text = state["last_text"]  # type: ignore[assignment]
        if text == last_text and not state["is_placeholder"]:
            return

        state["is_placeholder"] = False
        state["last_text"] = text
        edit.blockSignals(True)
        edit.setPlainText(text)
        edit.blockSignals(False)
        palette = edit.palette()
        palette.setColor(QPalette.Text, QColor(COLORS["text_primary"]))
        edit.setPalette(palette)

    def _apply_placeholder(self, section: str) -> None:
        if section not in self._sections:
            return
        state = self._sections[section]
        edit: _PreviewTextEdit = state["edit"]  # type: ignore[assignment]
        placeholder = state["placeholder"]  # type: ignore[assignment]

        state["is_placeholder"] = True
        state["last_text"] = ""
        edit.blockSignals(True)
        edit.setPlainText(placeholder)
        edit.blockSignals(False)
        palette = edit.palette()
        palette.setColor(QPalette.Text, QColor(COLORS["text_secondary"]))
        edit.setPalette(palette)
