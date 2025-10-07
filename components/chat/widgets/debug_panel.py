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

    PLACEHOLDER_TEXT = "暂无请求头数据"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._is_placeholder = True
        self._last_text = ""
        self._init_ui()

    def _init_ui(self) -> None:
        self.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"]
        )
        layout.setSpacing(SPACING["md"])

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
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(
            SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"]
        )
        frame_layout.setSpacing(SPACING["sm"])

        title = QLabel("调试")
        title_font = FONTS["subtitle"].__class__(FONTS["subtitle"])
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        title.setWordWrap(False)
        title.setSizePolicy(title.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
        title.setFixedHeight(title.fontMetrics().height())
        frame_layout.addWidget(title)

        self.preview_edit = _PreviewTextEdit()
        self.preview_edit.setReadOnly(True)
        code_font = FONTS["code"].__class__(FONTS["code"])
        self.preview_edit.setFont(code_font)
        self.preview_edit.setFixedHeight(100)
        self.preview_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.preview_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.preview_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.preview_edit.setStyleSheet(
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
        self.preview_edit.clicked.connect(self.panel_clicked.emit)
        frame_layout.addWidget(self.preview_edit)

        layout.addWidget(frame)
        layout.addStretch(1)
        self._apply_placeholder()

    # ------------------------------------------------------------------
    def set_preview_text(self, text: str, *, is_placeholder: bool) -> None:
        if is_placeholder:
            self._apply_placeholder()
            return

        if text == self._last_text and not self._is_placeholder:
            return

        self._is_placeholder = False
        self._last_text = text
        self.preview_edit.blockSignals(True)
        self.preview_edit.setPlainText(text)
        self.preview_edit.blockSignals(False)
        palette = self.preview_edit.palette()
        palette.setColor(QPalette.Text, QColor(COLORS["text_primary"]))
        self.preview_edit.setPalette(palette)

    def _apply_placeholder(self) -> None:
        self._is_placeholder = True
        self._last_text = ""
        self.preview_edit.blockSignals(True)
        self.preview_edit.setPlainText(self.PLACEHOLDER_TEXT)
        self.preview_edit.blockSignals(False)
        palette = self.preview_edit.palette()
        palette.setColor(QPalette.Text, QColor(COLORS["text_secondary"]))
        self.preview_edit.setPalette(palette)
