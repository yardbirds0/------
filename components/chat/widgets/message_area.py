# -*- coding: utf-8 -*-
"""
Cherry Studio Message Area
消息滚动区域 - 管理所有消息气泡的显示
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QFontMetrics

from models.data_models import PromptTemplate, TokenUsageInfo
from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING
from .message_bubble import MessageBubble
from .typing_indicator import TypingIndicator


class PromptBubble(QWidget):
    """提示词气泡"""

    clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("promptBubble")
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._prompt = PromptTemplate()
        self._full_line = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"]
        )
        layout.setSpacing(SPACING["sm"])

        self.group_label = QLabel()
        self.group_label.setFont(FONTS["subtitle"])
        self.group_label.setStyleSheet(
            f"color: {COLORS['accent_blue']}; background: transparent;"
        )
        layout.addWidget(self.group_label)

        self.content_label = QLabel()
        self.content_label.setFont(FONTS["body_small"])
        self.content_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; background: transparent;"
        )
        self.content_label.setWordWrap(False)
        self.content_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        layout.addWidget(self.content_label, 1)

        self._update_styles()
        self.set_prompt(self._prompt)

    def _update_styles(self):
        self.setStyleSheet(
            f"""
            QWidget#promptBubble {{
                background-color: {COLORS['bubble_ai_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: {SIZES['border_radius_large']}px;
            }}
            QWidget#promptBubble:hover {{
                background-color: {COLORS['bg_hover']};
            }}
            QWidget#promptBubble QLabel {{
                background: transparent;
            }}
            """
        )

    def set_prompt(self, prompt: PromptTemplate):
        """更新提示词内容"""
        self._prompt = prompt or PromptTemplate()
        self.group_label.setText(self._prompt.group_name or "提示词")
        line = self._prompt.first_line or self._prompt.title or ""
        self._full_line = line.strip()
        self.setToolTip(self._full_line)
        self._update_content_label()

    def prompt(self) -> PromptTemplate:
        return self._prompt

    def resizeEvent(self, event):  # noqa: D401
        """在大小变化时更新截断文本"""
        super().resizeEvent(event)
        self._update_content_label()

    def mouseReleaseEvent(self, event):  # noqa: D401
        """点击触发 Signal"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def _update_content_label(self):
        metrics = QFontMetrics(self.content_label.font())
        width = max(0, self.content_label.width())
        text = metrics.elidedText(self._full_line, Qt.ElideRight, width)
        self.content_label.setText(text)


class MessageArea(QWidget):
    """
    消息滚动区域
    管理用户消息和AI消息的显示,支持流式更新
    """

    prompt_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 消息列表
        self._messages: List[MessageBubble] = []
        self._current_streaming_bubble: MessageBubble = None
        self._typing_indicator: TypingIndicator = None
        self._typing_indicator_container: QWidget = None

        # 流式消息的AI元数据
        self._streaming_model_name: str = None
        self._streaming_provider: str = None
        self._streaming_timestamp: str = None

        # 流式更新防抖定时器
        self._stream_buffer = ""
        self._stream_timer = QTimer()
        self._stream_timer.timeout.connect(self._flush_stream_buffer)
        self._stream_timer.setInterval(50)  # 50ms批量更新

        # 提示词与欢迎区
        self._prompt_template = PromptTemplate()
        self._welcome_widget: Optional[QWidget] = None
        self._prompt_container: Optional[QWidget] = None
        self._prompt_bubble: Optional[PromptBubble] = None

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet(f"background-color: {COLORS['bg_main']};")

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(
            f"""
            QScrollArea {{
                background: {COLORS['bg_main']};
                border: none;
            }}
        """
        )

        # 滚动内容容器
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(
            SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"]
        )
        self.scroll_layout.setSpacing(SPACING["md"])
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self._create_header_widgets()
        self._ensure_bottom_spacer()

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

    def _create_header_widgets(self):
        """初始化欢迎消息与提示词气泡"""
        self._add_welcome_message()
        self._add_prompt_bubble()

    def _add_welcome_message(self):
        """添加欢迎消息"""
        if self._welcome_widget:
            return

        welcome_widget = QWidget(self.scroll_content)
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(0, SPACING["xxl"], 0, SPACING["xxl"])
        welcome_layout.setSpacing(SPACING["md"])
        welcome_layout.setAlignment(Qt.AlignCenter)

        # Logo/图标
        icon_label = QLabel("🍒")
        icon_label.setFont(QFont(FONTS["title"].family(), 48))
        icon_label.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(icon_label)

        # 标题
        title_label = QLabel("金融分析 AI 助手")
        title_label.setFont(FONTS["title"])
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        welcome_layout.addWidget(title_label)

        # 描述
        desc_label = QLabel("开始对话，让AI帮助您分析财务数据")
        desc_label.setFont(FONTS["body_small"])
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        welcome_layout.addWidget(desc_label)

        self.scroll_layout.addWidget(welcome_widget)
        self._welcome_widget = welcome_widget

    def _add_prompt_bubble(self):
        """添加提示词气泡"""
        if self._prompt_container:
            return

        container = QWidget(self.scroll_content)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        bubble = PromptBubble(container)
        bubble.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bubble.set_prompt(self._prompt_template)
        bubble.clicked.connect(self.prompt_clicked.emit)

        container_layout.addWidget(bubble)

        self.scroll_layout.addWidget(container)

        self._prompt_container = container
        self._prompt_bubble = bubble

    def _ensure_bottom_spacer(self):
        """确保底部存在弹性空间"""
        count = self.scroll_layout.count()
        if count == 0:
            self.scroll_layout.addStretch()
            return

        item = self.scroll_layout.itemAt(count - 1)
        if not item or item.spacerItem() is None:
            self.scroll_layout.addStretch()

    def _message_insert_index(self) -> int:
        """返回消息插入位置索引"""
        return max(self.scroll_layout.count() - 1, 0)

    def set_prompt(self, prompt: PromptTemplate):
        """更新提示词气泡内容"""
        self._prompt_template = prompt or PromptTemplate()
        if not self._prompt_bubble:
            self._add_prompt_bubble()
        self._prompt_bubble.set_prompt(self._prompt_template)

    def hide_welcome_message(self):
        """隐藏欢迎消息"""
        if self._welcome_widget:
            self.scroll_layout.removeWidget(self._welcome_widget)
            self._welcome_widget.deleteLater()
            self._welcome_widget = None

    def add_user_message(self, content: str):
        """
        添加用户消息

        Args:
            content: 消息内容
        """
        # 创建消息气泡
        bubble = MessageBubble(content, is_user=True)
        self._messages.append(bubble)

        # 创建右对齐容器
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addStretch()
        container_layout.addWidget(bubble)

        # 添加到布局 (在stretch之前)
        insert_index = self._message_insert_index()
        self.scroll_layout.insertWidget(insert_index, container)

        # 滚动到底部
        self._scroll_to_bottom()

    def add_ai_message(
        self,
        content: str,
        model_name: str = None,
        provider: str = None,
        timestamp: str = None,
        token_usage: Optional[TokenUsageInfo] = None,
    ):
        """
        添加AI消息 (非流式)

        Args:
            content: 消息内容
            model_name: 模型名称，如"GPT-4"
            provider: 提供商，如"OpenAI"
            timestamp: 时间戳字符串
        """
        # 创建消息气泡，传入AI元数据
        bubble = MessageBubble(
            content,
            is_user=False,
            model_name=model_name,
            provider=provider,
            timestamp=timestamp,
        )
        self._messages.append(bubble)
        bubble.set_token_usage(token_usage)

        # 创建左对齐容器
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(bubble)
        container_layout.addStretch()

        # 添加到布局
        insert_index = self._message_insert_index()
        self.scroll_layout.insertWidget(insert_index, container)

        # 滚动到底部
        self._scroll_to_bottom()

    def start_streaming_message(
        self, model_name: str = None, provider: str = None, timestamp: str = None
    ):
        """
        开始流式消息 (显示加载动画)

        Args:
            model_name: 模型名称
            provider: 提供商
            timestamp: 时间戳
        """
        # 保存AI元数据，供后续创建bubble时使用
        self._streaming_model_name = model_name
        self._streaming_provider = provider
        self._streaming_timestamp = timestamp

        # 创建加载动画
        self._typing_indicator = TypingIndicator()

        # 创建左对齐容器
        self._typing_indicator_container = QWidget()
        container_layout = QHBoxLayout(self._typing_indicator_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self._typing_indicator)
        container_layout.addStretch()

        # 添加到布局
        insert_index = self._message_insert_index()
        self.scroll_layout.insertWidget(insert_index, self._typing_indicator_container)

        # 滚动到底部
        self._scroll_to_bottom()

    def update_streaming_message(self, chunk: str):
        """
        更新流式消息

        Args:
            chunk: 新的文本片段
        """
        # 如果是第一个chunk，移除加载动画并创建消息气泡
        if self._current_streaming_bubble is None:
            # 移除加载动画
            if self._typing_indicator_container:
                self._typing_indicator_container.deleteLater()
                self._typing_indicator_container = None
                self._typing_indicator = None

            # 创建空气泡，传入AI元数据
            bubble = MessageBubble(
                "",
                is_user=False,
                model_name=self._streaming_model_name,
                provider=self._streaming_provider,
                timestamp=self._streaming_timestamp,
            )
            self._messages.append(bubble)
            self._current_streaming_bubble = bubble

            # 清空流式缓冲区
            self._stream_buffer = ""

            # 创建左对齐容器
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.addWidget(bubble)
            container_layout.addStretch()

            # 添加到布局
            insert_index = self._message_insert_index()
            self.scroll_layout.insertWidget(insert_index, container)

        # 添加到缓冲区
        self._stream_buffer += chunk

        # 启动定时器 (防抖)
        if not self._stream_timer.isActive():
            self._stream_timer.start()

    def _flush_stream_buffer(self):
        """刷新流式缓冲区到UI"""
        if self._current_streaming_bubble and self._stream_buffer:
            self._current_streaming_bubble.append_content(self._stream_buffer)
            self._stream_buffer = ""
            self._scroll_to_bottom()

    def finish_streaming_message(self, token_usage: Optional[TokenUsageInfo] = None):
        """完成流式消息"""
        # 刷新剩余缓冲区
        self._stream_timer.stop()
        self._flush_stream_buffer()

        if self._current_streaming_bubble:
            self._current_streaming_bubble.set_token_usage(token_usage)

        # 清空当前流式气泡引用
        self._current_streaming_bubble = None

        # 清空AI元数据
        self._streaming_model_name = None
        self._streaming_provider = None
        self._streaming_timestamp = None

    def clear_messages(self):
        """清空所有消息"""
        # 删除所有消息widget
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        # 清空消息列表
        self._messages.clear()
        self._current_streaming_bubble = None
        self._typing_indicator = None
        self._typing_indicator_container = None

        # 重建欢迎消息与提示词气泡
        self._welcome_widget = None
        self._prompt_bubble = None
        self._prompt_container = None

        self._create_header_widgets()
        self._ensure_bottom_spacer()
        self.set_prompt(self._prompt_template)

    def get_messages(self) -> List[MessageBubble]:
        """获取所有消息"""
        return self._messages.copy()

    def _scroll_to_bottom(self):
        """滚动到底部"""
        # 延迟滚动,确保布局更新完成
        QTimer.singleShot(
            10,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ),
        )


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QVBoxLayout, QPushButton

    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("Cherry Studio Message Area Test")
    window.resize(800, 700)

    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # 添加消息区域
    message_area = MessageArea()
    layout.addWidget(message_area, stretch=1)

    # 测试按钮区域
    button_widget = QWidget()
    button_layout = QHBoxLayout(button_widget)
    button_layout.setContentsMargins(
        SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"]
    )
    button_layout.setSpacing(SPACING["sm"])

    # 添加用户消息按钮
    add_user_btn = QPushButton("添加用户消息")
    add_user_btn.clicked.connect(
        lambda: message_area.add_user_message("这是一条测试用户消息。")
    )
    button_layout.addWidget(add_user_btn)

    # 添加AI消息按钮
    add_ai_btn = QPushButton("添加AI消息")
    add_ai_btn.clicked.connect(
        lambda: message_area.add_ai_message(
            "这是一条AI回复消息，内容较长可能需要自动换行显示。"
        )
    )
    button_layout.addWidget(add_ai_btn)

    # 流式更新测试按钮
    stream_btn = QPushButton("流式更新测试")

    def test_streaming():
        message_area.start_streaming_message()
        test_text = (
            "这是一条流式更新的AI消息，文字会逐渐出现...\n\n让我们看看效果如何！"
        )
        test_index = [0]

        def update():
            if test_index[0] < len(test_text):
                message_area.update_streaming_message(test_text[test_index[0]])
                test_index[0] += 1
            else:
                timer.stop()
                message_area.finish_streaming_message()

        timer = QTimer()
        timer.timeout.connect(update)
        timer.start(30)

    stream_btn.clicked.connect(test_streaming)
    button_layout.addWidget(stream_btn)

    # 清空消息按钮
    clear_btn = QPushButton("清空消息")
    clear_btn.clicked.connect(message_area.clear_messages)
    button_layout.addWidget(clear_btn)

    layout.addWidget(button_widget)

    window.show()
    sys.exit(app.exec())
