# -*- coding: utf-8 -*-
"""Modal dialog used to display the full request preview."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QTextOption

from controllers.request_preview_service import RequestPreviewState
from ..styles.cherry_theme import COLORS, FONTS, SPACING, get_global_stylesheet


PLACEHOLDER_TEXT = "暂无请求头数据"


class RequestPreviewDialog(QDialog):
    """Displays masked/raw request preview content with copy helpers."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("请求头详情")
        self.setModal(True)
        self.resize(500, 900)

        base_stylesheet = get_global_stylesheet()
        self.setStyleSheet(
            base_stylesheet
            + f"""
            QDialog {{
                background-color: {COLORS['bg_main']};
            }}
            QPushButton {{
                min-height: 36px;
                border-radius: 6px;
                padding: 0 16px;
                background-color: {COLORS['accent_blue']};
                color: {COLORS['text_inverse']};
                border: none;
            }}
            QPushButton:hover {{
                background-color: #2563EB;
            }}
            QPushButton:pressed {{
                background-color: #1D4ED8;
            }}
            """
        )

        self._state: Optional[RequestPreviewState] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        header = QLabel("完整请求内容")
        header_font = FONTS["title"].__class__(FONTS["title"])
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(header)

        caption = QLabel("预览内容可直接复制到剪贴板。")
        caption.setFont(FONTS["caption"])
        caption.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(caption)

        self.preview_edit = QPlainTextEdit()
        self.preview_edit.setReadOnly(True)
        code_font = FONTS["code"].__class__(FONTS["code"])
        self.preview_edit.setFont(code_font)
        self.preview_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.preview_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.preview_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.preview_edit.setStyleSheet(
            f"""
            QPlainTextEdit {{
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                padding: 12px;
            }}
            QPlainTextEdit:focus {{
                border: 1px solid {COLORS['border_focus']};
            }}
            """
        )
        self.preview_edit.setPlaceholderText(PLACEHOLDER_TEXT)
        layout.addWidget(self.preview_edit, stretch=1)

        button_row = QHBoxLayout()
        button_row.setSpacing(SPACING["sm"])
        button_row.addStretch()

        copy_all = QPushButton("复制")
        copy_all.clicked.connect(self._copy_all)
        button_row.addWidget(copy_all)

        layout.addLayout(button_row)

    # ------------------------------------------------------------------
    def set_preview(self, state: Optional[RequestPreviewState]) -> None:
        self._state = state
        if not state:
            self.preview_edit.setPlainText("")
            self.preview_edit.setPlaceholderText(PLACEHOLDER_TEXT)
            return

        source_text = state.raw_text or state.display_text
        if not source_text:
            self.preview_edit.setPlainText("")
            self.preview_edit.setPlaceholderText(PLACEHOLDER_TEXT)
        else:
            self.preview_edit.setPlainText(source_text)

    def _copy_all(self) -> None:
        if not self._state:
            return
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.preview_edit.toPlainText())
