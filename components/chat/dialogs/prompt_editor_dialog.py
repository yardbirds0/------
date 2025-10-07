# -*- coding: utf-8 -*-
"""
PromptEditorDialog
提示词编辑窗口
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QWidget,
    QComboBox,
)
from PySide6.QtCore import Qt, Signal

from models.data_models import PromptTemplate
from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING, get_global_stylesheet


class PromptEditorDialog(QDialog):
    """提示词编辑对话框"""

    prompt_saved = Signal(PromptTemplate)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        prompt: Optional[PromptTemplate] = None,
        history: Optional[List[Tuple[str, PromptTemplate]]] = None,
    ):
        super().__init__(parent)
        self._prompt = prompt or PromptTemplate()
        self._history_items: List[Tuple[str, PromptTemplate]] = history or []

        self.group_input: QLineEdit
        self.title_input: QLineEdit
        self.content_input: QTextEdit
        self.token_label: QLabel
        self.history_combo: Optional[QComboBox] = None

        self._init_ui()
        self._load_prompt()

    def _init_ui(self):
        self.setWindowTitle("编辑提示词")
        self.setModal(True)
        self.setFixedSize(640, 900)
        # 以全白背景为主色调
        base_stylesheet = get_global_stylesheet()
        self.setStyleSheet(
            base_stylesheet
            + """
            QDialog {
                background-color: #FFFFFF;
            }
            QLabel[role="section-title"] {
                color: #1F2937;
                font-weight: 600;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"]
        )
        main_layout.setSpacing(SPACING["md"])

        title_label = QLabel("提示词设置")
        title_label.setObjectName("sectionTitle")
        title_label.setProperty("role", "section-title")
        title_font = FONTS["title"]
        bold_title = title_font.__class__(title_font)
        bold_title.setBold(True)
        title_label.setFont(bold_title)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        main_layout.addWidget(title_label)

        main_layout.addSpacing(SPACING["sm"])

        group_field, self.group_input = self._create_input_field(
            "提示词分组名称", placeholder="例如：财务分析提示词"
        )
        main_layout.addWidget(group_field)

        title_field, self.title_input = self._create_input_field(
            "提示词标题", placeholder="用于内部标识的标题，可选"
        )
        main_layout.addWidget(title_field)

        if self._history_items:
            history_widget = self._create_history_section()
            main_layout.addWidget(history_widget)

        content_label = QLabel("提示词内容")
        content_label.setFont(self._bold_label_font())
        content_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        main_layout.addWidget(content_label)

        self.content_input = QTextEdit()
        self.content_input.setFont(FONTS["body"])
        self.content_input.setMinimumHeight(520)
        self.content_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content_input.textChanged.connect(self._update_token_counter)
        main_layout.addWidget(self.content_input)

        self.token_label = QLabel("")
        caption_font = FONTS["caption"]
        caption_bold = caption_font.__class__(caption_font)
        caption_bold.setBold(True)
        self.token_label.setFont(caption_bold)
        self.token_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        main_layout.addWidget(self.token_label)

        main_layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(SIZES["button_height_large"])
        cancel_btn.setMinimumWidth(120)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setProperty("styleClass", "primary")
        save_btn.setFixedHeight(SIZES["button_height_large"])
        save_btn.setMinimumWidth(140)
        save_btn.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(save_btn)

        main_layout.addLayout(button_layout)

        self._apply_styles()

    def _create_input_field(
        self, label_text: str, placeholder: str = ""
    ) -> Tuple[QWidget, QLineEdit]:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["xs"])

        label = QLabel(label_text)
        label.setFont(self._bold_label_font())
        label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(label)

        line_edit = QLineEdit()
        line_edit.setFont(FONTS["input"])
        line_edit.setFixedHeight(SIZES["input_height"])
        line_edit.setPlaceholderText(placeholder)
        layout.addWidget(line_edit)

        return container, line_edit

    def _create_history_section(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        label = QLabel("历史版本")
        label.setFont(self._bold_label_font())
        label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(label)

        combo = QComboBox()
        combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        combo.setMinimumWidth(260)
        combo.setFont(FONTS["body_small"])
        for item_label, prompt in self._history_items:
            combo.addItem(item_label, prompt)
        self.history_combo = combo
        layout.addWidget(combo, 1)

        restore_btn = QPushButton("恢复所选")
        restore_btn.setFixedHeight(SIZES["button_height"])
        restore_btn.clicked.connect(self._on_restore_history)
        layout.addWidget(restore_btn)

        layout.addStretch()
        return container

    def _bold_label_font(self):
        base = FONTS["label"]
        font = base.__class__(base)
        font.setBold(True)
        return font

    def _apply_styles(self):
        self.content_input.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 12px;
            }}
            QTextEdit:focus {{
                border: 1px solid {COLORS['border_focus']};
            }}
            """
        )

    def _load_prompt(self):
        self.group_input.setText(self._prompt.group_name)
        self.title_input.setText(self._prompt.title)
        self.content_input.setPlainText(self._prompt.content)
        self._update_token_counter()

    def _update_token_counter(self):
        text = self.content_input.toPlainText().strip()
        length = len(text)
        estimated_tokens = max(1, length // 3) if length else 0
        self.token_label.setText(f"字数：{length}，估算 Token：{estimated_tokens}")

    def _on_restore_history(self):
        if not self.history_combo:
            return
        prompt = self.history_combo.currentData()
        if not isinstance(prompt, PromptTemplate):
            return
        self.group_input.setText(prompt.group_name)
        self.title_input.setText(prompt.title)
        self.content_input.setPlainText(prompt.content)

    def _on_save_clicked(self):
        content = self.content_input.toPlainText().strip()
        if not content:
            # 内容为空时仍允许保存，但给出提示
            content = ""

        updated = PromptTemplate(
            group_name=self.group_input.text().strip() or "默认提示词",
            title=self.title_input.text().strip(),
            content=content,
            updated_at=datetime.now(),
        )

        self.prompt_saved.emit(updated)
        self.accept()
