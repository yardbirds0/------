# -*- coding: utf-8 -*-
"""
Cherry Studio Message Bubble
消息气泡组件 - 用户消息(蓝色) / AI消息(灰色)
支持Markdown渲染和代码语法高亮
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser,
    QPushButton, QGraphicsOpacityEffect, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QTextCursor, QFontMetrics
)

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING
from models.data_models import TokenUsageInfo
from ..renderers import MarkdownRenderer


class MessageBubble(QWidget):
    """
    消息气泡组件
    支持用户消息和AI消息两种样式
    AI消息支持Markdown渲染和代码高亮
    """

    def __init__(
        self,
        content: str,
        is_user: bool = False,
        model_name: str = None,
        provider: str = None,
        timestamp: str = None,
        parent=None
    ):
        super().__init__(parent)

        self._content = content
        self._is_user = is_user
        self._is_hovered = False

        # AI消息的元数据
        self._model_name = model_name
        self._provider = provider
        self._timestamp = timestamp

        # 仅AI消息使用Markdown渲染
        self._markdown_renderer = None if is_user else MarkdownRenderer()

        # 复制按钮相关
        self._copy_button = None
        self._controls_animation = None
        self._controls_container = None
        self._usage_label = None
        self._token_usage: TokenUsageInfo = TokenUsageInfo.missing()

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        # 对于AI消息,设置最大宽度;对于用户消息,将根据内容动态设置
        if not self._is_user:
            self.setMaximumWidth(SIZES['bubble_max_width'])

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING['sm'])

        # ==================== AI消息标题 ====================
        if not self._is_user and (self._model_name or self._provider or self._timestamp):
            header_widget = self._create_ai_header()
            layout.addWidget(header_widget)

        # 消息内容显示框（使用 QTextBrowser 支持 HTML）
        self.text_edit = QTextBrowser()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(FONTS['body'])
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setOpenExternalLinks(True)  # 允许打开外部链接

        # 根据消息类型渲染内容
        if self._is_user:
            # 用户消息 - 纯文本
            self.text_edit.setPlainText(self._content)
        else:
            # AI消息 - Markdown渲染
            if self._markdown_renderer and self._content:
                html = self._markdown_renderer.render(self._content)
                self.text_edit.setHtml(html)
            else:
                self.text_edit.setPlainText(self._content)

        # 设置样式
        if self._is_user:
            # 用户消息 - 蓝色背景
            bg_color = COLORS['bubble_user_bg']
            text_color = COLORS['bubble_user_text']
        else:
            # AI消息 - 浅灰背景
            bg_color = COLORS['bubble_ai_bg']
            text_color = COLORS['bubble_ai_text']

        self.text_edit.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: {SIZES['border_radius_large']}px;
                padding: {SIZES['bubble_padding']}px;
                font-size: 14px;
                line-height: 1.6;
            }}
        """)

        # 对于用户消息,动态调整宽度
        if self._is_user:
            self._adjust_width()

        # 自动调整高度
        self._adjust_height()

        layout.addWidget(self.text_edit)

        # ==================== 复制按钮与用量标签 ====================
        self._copy_button = QPushButton("📋 复制")
        self._copy_button.setFont(FONTS['caption'])
        self._copy_button.setFixedHeight(24)
        self._copy_button.setCursor(Qt.PointingHandCursor)
        self._copy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_blue']};
                color: {COLORS['text_inverse']};
                border-color: {COLORS['accent_blue']};
            }}
        """)
        self._copy_button.clicked.connect(self._copy_to_clipboard)

        self._usage_label: Optional[QLabel] = None
        if not self._is_user:
            usage_label = QLabel(TokenUsageInfo.PLACEHOLDER_TEXT)
            usage_label.setFont(FONTS['caption'])
            usage_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            usage_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            self._usage_label = usage_label

        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(SPACING['xs'])
        controls_layout.addStretch()
        if self._usage_label:
            controls_layout.addWidget(self._usage_label)
        controls_layout.addWidget(self._copy_button)

        controls_container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.0)
        controls_container.setGraphicsEffect(opacity_effect)
        controls_container.hide()

        self._controls_container = controls_container
        self._controls_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self._controls_animation.setDuration(200)  # 200ms动画

        layout.addWidget(self._controls_container, alignment=Qt.AlignRight)

        if not self._is_user:
            self._update_usage_display()
        else:
            self._ensure_minimum_width_for_controls()

    def _adjust_height(self):
        """自动调整高度以适应内容"""
        # 计算文档高度
        doc = self.text_edit.document()
        doc.setTextWidth(self.text_edit.viewport().width())
        height = doc.size().height() + 2 * SIZES['bubble_padding']

        # 设置固定高度
        self.text_edit.setFixedHeight(int(height))

    def _adjust_width(self):
        """
        动态调整宽度以适应用户消息内容
        短消息使用较窄气泡,长消息使用较宽气泡,但不超过最大宽度
        """
        # 获取字体度量
        fm = QFontMetrics(FONTS['body'])

        # 按行分割内容
        lines = self._content.split('\n')

        # 计算最长行的宽度
        max_line_width = 0
        for line in lines:
            line_width = fm.horizontalAdvance(line)
            max_line_width = max(max_line_width, line_width)

        # 加上padding和边距
        total_padding = 2 * SIZES['bubble_padding'] + 20  # 额外20px留白
        content_width = max_line_width + total_padding

        # 设置最小宽度和最大宽度
        min_width = 80  # 最小宽度80px
        max_width = SIZES['bubble_max_width']

        # 限制宽度范围
        final_width = max(min_width, min(content_width, max_width))

        controls_width = self._required_controls_width()
        if controls_width:
            final_width = max(final_width, controls_width)

        # 设置宽度，确保底部控件完整显示
        self.setMaximumWidth(int(final_width))
        self.setMinimumWidth(int(final_width))

    def _create_ai_header(self) -> QWidget:
        """
        创建AI消息标题
        包含左侧logo和右侧元数据（模型名称|提供商、时间）
        """
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING['sm'])

        # ==================== 左侧：Logo ====================
        logo_label = QLabel("🤖")
        logo_label.setFont(QFont(FONTS['title'].family(), 24))  # 大号emoji
        logo_label.setFixedSize(48, 48)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(f"""
            QLabel {{
                background-color: #7C3AED;  /* 紫色 */
                border-radius: 8px;
            }}
        """)
        header_layout.addWidget(logo_label)

        # ==================== 右侧：文本信息 ====================
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        # 第一行：模型名称 | 提供商
        if self._model_name or self._provider:
            model_text = self._model_name or ""
            provider_text = self._provider or ""
            if model_text and provider_text:
                title_text = f"{model_text} | {provider_text}"
            else:
                title_text = model_text or provider_text

            title_label = QLabel(title_text)
            title_label.setFont(FONTS['body'])
            title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
            text_layout.addWidget(title_label)

        # 第二行：时间
        if self._timestamp:
            time_label = QLabel(self._timestamp)
            time_label.setFont(FONTS['caption'])
            time_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
            text_layout.addWidget(time_label)

        header_layout.addWidget(text_container)
        header_layout.addStretch()

        return header

    def get_content(self) -> str:
        """获取消息内容"""
        return self._content

    def set_content(self, content: str):
        """
        设置消息内容

        Args:
            content: 消息文本
        """
        self._content = content

        # 根据消息类型渲染内容
        if self._is_user:
            # 用户消息 - 纯文本
            self.text_edit.setPlainText(content)
        else:
            # AI消息 - Markdown渲染
            if self._markdown_renderer:
                html = self._markdown_renderer.render(content)
                self.text_edit.setHtml(html)
            else:
                self.text_edit.setPlainText(content)

        self._adjust_height()

    def append_content(self, chunk: str):
        """
        追加内容 (用于流式更新)

        Args:
            chunk: 要追加的文本片段
        """
        self._content += chunk

        # 根据消息类型渲染内容
        if self._is_user:
            # 用户消息 - 纯文本
            self.text_edit.setPlainText(self._content)
        else:
            # AI消息 - Markdown渲染
            if self._markdown_renderer:
                html = self._markdown_renderer.render(self._content)
                self.text_edit.setHtml(html)
            else:
                self.text_edit.setPlainText(self._content)

        self._adjust_height()

        # 滚动到底部
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.text_edit.setTextCursor(cursor)

    def is_user_message(self) -> bool:
        """是否为用户消息"""
        return self._is_user

    def set_token_usage(self, usage_info: Optional[TokenUsageInfo]):
        if usage_info is None:
            usage_info = TokenUsageInfo.missing()
        self._token_usage = usage_info
        self._update_usage_display()

    def _update_usage_display(self):
        if not self._usage_label:
            self._ensure_minimum_width_for_controls()
            return

        self._usage_label.setText(self._token_usage.as_text())
        self._ensure_minimum_width_for_controls()

    def _ensure_minimum_width_for_controls(self):
        if not self._controls_container:
            return

        required_width = self._required_controls_width()
        if required_width <= 0:
            return

        if required_width > self.minimumWidth():
            self.setMinimumWidth(required_width)

        if self._is_user and required_width > self.maximumWidth():
            self.setMaximumWidth(required_width)

    def resizeEvent(self, event):
        """窗口大小变化时重新调整高度"""
        super().resizeEvent(event)
        self._adjust_height()

    def enterEvent(self, event):
        """鼠标进入时显示复制按钮"""
        self._is_hovered = True
        self._show_controls()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时隐藏复制按钮"""
        self._is_hovered = False
        self._hide_controls()
        super().leaveEvent(event)

    def _show_controls(self):
        """显示复制按钮和用量信息（淡入动画）"""
        if not self._controls_container:
            return

        self._controls_container.show()
        self._controls_animation.stop()
        self._controls_animation.setStartValue(0.0)
        self._controls_animation.setEndValue(1.0)
        self._controls_animation.start()

    def _hide_controls(self):
        """隐藏复制按钮和用量信息（淡出动画）"""
        if not self._controls_container:
            return

        self._controls_animation.stop()
        self._controls_animation.setStartValue(1.0)
        self._controls_animation.setEndValue(0.0)

        # 动画结束后隐藏按钮
        def on_animation_finished():
            if not self._is_hovered:
                self._controls_container.hide()

        # 断开之前的连接
        try:
            self._controls_animation.finished.disconnect()
        except:
            pass

        self._controls_animation.finished.connect(on_animation_finished)
        self._controls_animation.start()

    def _required_controls_width(self) -> int:
        button_width = self._copy_button.sizeHint().width() if self._copy_button else 0
        usage_width = 0
        if self._usage_label:
            metrics = QFontMetrics(self._usage_label.font())
            usage_width = metrics.horizontalAdvance(self._usage_label.text())

        spacing = SPACING['xs'] if self._usage_label and self._copy_button else 0
        padding = SIZES['bubble_padding'] * 2
        base = button_width + padding
        if usage_width:
            base += usage_width + spacing
        return base

    def _copy_to_clipboard(self):
        """复制内容到剪贴板"""
        if not self._content:
            return

        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(self._content)

        # 显示复制成功提示
        original_text = self._copy_button.text()
        self._copy_button.setText("✓ 已复制")

        # 2秒后恢复原文本
        QTimer.singleShot(2000, lambda: self._copy_button.setText(original_text))


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QVBoxLayout, QScrollArea

    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("Cherry Studio Message Bubble Test")
    window.resize(700, 600)
    window.setStyleSheet(f"background-color: {COLORS['bg_main']};")

    # 滚动区域
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setStyleSheet("border: none;")

    scroll_content = QWidget()
    scroll_layout = QVBoxLayout(scroll_content)
    scroll_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
    scroll_layout.setSpacing(SPACING['md'])
    scroll_layout.setAlignment(Qt.AlignTop)

    # 添加测试消息气泡

    # 用户消息1
    user_bubble1 = MessageBubble("你好！请帮我分析这份财务报表。", is_user=True)
    user_container1 = QWidget()
    user_layout1 = QHBoxLayout(user_container1)
    user_layout1.setContentsMargins(0, 0, 0, 0)
    user_layout1.addStretch()
    user_layout1.addWidget(user_bubble1)
    scroll_layout.addWidget(user_container1)

    # AI消息1
    ai_bubble1 = MessageBubble(
        "您好！我是Cherry Studio AI助手，很高兴为您服务。\n\n"
        "我可以帮助您：\n"
        "- 📊 分析财务数据结构\n"
        "- 🔍 生成智能映射公式\n"
        "- 💡 解答技术问题\n\n"
        "请上传您的财务报表文件，我将为您提供详细分析。",
        is_user=False
    )
    ai_container1 = QWidget()
    ai_layout1 = QHBoxLayout(ai_container1)
    ai_layout1.setContentsMargins(0, 0, 0, 0)
    ai_layout1.addWidget(ai_bubble1)
    ai_layout1.addStretch()
    scroll_layout.addWidget(ai_container1)

    # 用户消息2 (长文本测试)
    user_bubble2 = MessageBubble(
        "这份报表包含多个工作表：资产负债表、利润表、现金流量表。\n"
        "我需要提取利润表中的营业收入、营业成本、税金及附加等数据，\n"
        "然后填充到快报表格中。你能帮我自动生成映射公式吗？",
        is_user=True
    )
    user_container2 = QWidget()
    user_layout2 = QHBoxLayout(user_container2)
    user_layout2.setContentsMargins(0, 0, 0, 0)
    user_layout2.addStretch()
    user_layout2.addWidget(user_bubble2)
    scroll_layout.addWidget(user_container2)

    # AI消息2 (流式更新测试)
    ai_bubble2 = MessageBubble("", is_user=False)
    ai_container2 = QWidget()
    ai_layout2 = QHBoxLayout(ai_container2)
    ai_layout2.setContentsMargins(0, 0, 0, 0)
    ai_layout2.addWidget(ai_bubble2)
    ai_layout2.addStretch()
    scroll_layout.addWidget(ai_container2)

    # 模拟流式更新
    from PySide6.QtCore import QTimer
    test_text = "当然可以！让我为您分析这些工作表的结构，并生成映射公式...\n\n"
    test_index = [0]

    def update_stream():
        if test_index[0] < len(test_text):
            ai_bubble2.append_content(test_text[test_index[0]])
            test_index[0] += 1
        else:
            timer.stop()

    timer = QTimer()
    timer.timeout.connect(update_stream)
    timer.start(50)  # 每50ms添加一个字符

    scroll_layout.addStretch()
    scroll_area.setWidget(scroll_content)

    main_layout = QVBoxLayout(window)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(scroll_area)

    window.show()
    sys.exit(app.exec())
