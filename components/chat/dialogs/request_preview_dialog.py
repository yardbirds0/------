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

import json

from controllers.request_preview_service import RequestPreviewState
from ..styles.cherry_theme import COLORS, FONTS, SPACING, get_global_stylesheet

try:  # tiktoken is optional but recommended for accurate estimation
    import tiktoken
except ImportError:  # pragma: no cover - fall back gracefully when package missing
    tiktoken = None


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
        self._raw_text_mode = False
        self._prompt_tokens = 0

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

        self._token_label = QLabel()
        self._token_label.setFont(FONTS["caption"])
        self._token_label.setAlignment(Qt.AlignCenter)
        self._token_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        button_row.addWidget(self._token_label, stretch=0)
        button_row.addStretch()

        copy_all = QPushButton("复制")
        copy_all.clicked.connect(self._copy_all)
        button_row.addWidget(copy_all)

        layout.addLayout(button_row)
        self._update_token_label(0)

    # ------------------------------------------------------------------
    def set_preview(self, state: Optional[RequestPreviewState]) -> None:
        self._state = state
        self._raw_text_mode = False
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

        prompt_tokens = self._derive_usage_from_state(state)
        self._update_token_label(prompt_tokens)

    def set_text_content(self, text: str, *, placeholder: str = PLACEHOLDER_TEXT) -> None:
        """直接设置原始文本内容，用于非 RequestPreviewState 的展示。"""
        self._state = None
        self._raw_text_mode = True
        if text:
            self.preview_edit.setPlainText(text)
        else:
            self.preview_edit.setPlainText("")
            self.preview_edit.setPlaceholderText(placeholder)

        prompt_tokens = self._estimate_tokens(text)
        self._update_token_label(prompt_tokens)

    def _copy_all(self) -> None:
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.preview_edit.toPlainText())

    # ------------------------------------------------------------------
    def _derive_usage_from_state(self, state: Optional[RequestPreviewState]) -> int:
        if not state:
            return 0

        messages = self._gather_messages(state.payload)
        if not messages and state.raw_text:
            messages = self._gather_messages(self._parse_json(state.raw_text))
        if not messages and state.display_text:
            messages = self._gather_messages(self._parse_json(state.display_text))

        token_count = self._tokens_from_messages(messages)
        if token_count:
            return token_count

        source_text = state.display_text or state.raw_text or ""
        return self._estimate_tokens(source_text)

    def _gather_messages(self, data: Optional[object]) -> Optional[list]:
        if isinstance(data, dict):
            messages = data.get("messages")
            if isinstance(messages, list):
                return messages
            for key in ("payload", "request", "data", "body", "message", "context"):
                nested = self._gather_messages(data.get(key))
                if nested:
                    return nested
        elif isinstance(data, list):
            for item in data:
                nested = self._gather_messages(item)
                if nested:
                    return nested
        return None

    def _parse_json(self, text: Optional[str]) -> Optional[object]:
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _tokens_from_messages(self, messages: Optional[list]) -> int:
        if not messages:
            return 0
        total = 0
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = message.get('role')
            if role not in {'system', 'user'}:
                continue
            content = message.get('content')
            text_segments: list[str] = []
            if isinstance(content, str):
                text_segments.append(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        value = part.get('text') or part.get('content')
                        if isinstance(value, str):
                            text_segments.append(value)
                    elif isinstance(part, str):
                        text_segments.append(part)
            elif content is not None:
                text_segments.append(str(content))

            for segment in text_segments:
                total += self._estimate_tokens(segment)
        return total

    def _estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        if tiktoken:
            try:
                encoding = tiktoken.encoding_for_model("gpt-4o")
            except Exception:  # pragma: no cover - fallback when model not found
                encoding = tiktoken.get_encoding("cl100k_base")
            try:
                return len(encoding.encode(text))
            except Exception:
                pass
        # Fallback: simple whitespace tokenisation
        return len(text.split())

    def _update_token_label(self, prompt_tokens: int) -> None:
        self._prompt_tokens = prompt_tokens
        number_style = f"color:{COLORS['accent_green']}; font-weight:600;"
        text = f"TOKEN预估值:<span style='{number_style}'>{prompt_tokens}</span>"
        self._token_label.setText(text)
