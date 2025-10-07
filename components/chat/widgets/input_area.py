# -*- coding: utf-8 -*-
"""
Cherry Studio Input Area
多行输入区域 + 工具栏 + 发送按钮
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QToolButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING


class CherryInputArea(QWidget):
    """
    Cherry Studio 输入区域
    包含工具栏、多行输入框、发送/停止按钮
    """

    # 信号定义
    message_sent = Signal(str)          # 发送消息
    file_uploaded = Signal(str)         # 上传文件
    help_requested = Signal()           # 请求帮助
    history_requested = Signal()        # 查看历史
    template_requested = Signal()       # 使用模板
    voice_input_requested = Signal()    # 语音输入
    stop_requested = Signal()           # 停止生成
    draft_changed = Signal(str)         # 输入草稿变化

    def __init__(self, parent=None):
        super().__init__(parent)

        self._is_generating = False  # 是否正在生成中
        self._min_input_height = 48
        self._max_input_height = 150
        self._draft_timer = QTimer(self)
        self._draft_timer.setSingleShot(True)
        self._draft_timer.setInterval(100)
        self._draft_timer.timeout.connect(self._emit_draft_changed)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_main']};
            }}
        """)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        main_layout.setSpacing(SPACING['sm'])

        # ==================== 工具栏 ====================
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(SPACING['xs'])

        # 工具栏按钮配置
        toolbar_buttons = [
            ("📎", "附加文件", self._on_attach_file),
            ("❓", "帮助提示", self._on_help),
            ("🕒", "历史记录", self._on_history),
            ("📝", "使用模板", self._on_template),
            ("🎤", "语音输入", self._on_voice),
        ]

        for icon, tooltip, callback in toolbar_buttons:
            btn = QToolButton()
            btn.setText(icon)
            btn.setToolTip(tooltip)
            btn.setFont(QFont(FONTS['body'].family(), 16))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background: transparent;
                    border: none;
                    border-radius: {SIZES['border_radius']}px;
                    padding: 4px 8px;
                    color: {COLORS['text_secondary']};
                }}
                QToolButton:hover {{
                    background-color: {COLORS['bg_hover']};
                    color: {COLORS['text_primary']};
                }}
                QToolButton:pressed {{
                    background-color: {COLORS['bg_active']};
                }}
            """)
            btn.clicked.connect(callback)
            toolbar_layout.addWidget(btn)

        # 工具栏弹性空间
        toolbar_layout.addStretch()

        main_layout.addWidget(toolbar)

        # ==================== 输入区域 ====================
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(SPACING['md'])

        # 多行文本输入框
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("输入您的问题... (Enter 发送, Shift+Enter 换行)")
        self.text_input.setFont(FONTS['body'])
        self.text_input.setMinimumHeight(self._min_input_height)
        self.text_input.setMaximumHeight(self._max_input_height)
        self.text_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.text_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 输入框样式
        self.text_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: {SIZES['border_radius']}px;
                padding: 10px 12px;
                font-size: 14px;
                line-height: 1.5;
            }}
            QTextEdit:focus {{
                border: 2px solid {COLORS['border_focus']};
            }}
        """)

        # 监听文本变化以动态调整高度
        self.text_input.textChanged.connect(self._on_text_changed)

        # 安装事件过滤器以处理 Enter 键
        self.text_input.installEventFilter(self)

        input_layout.addWidget(self.text_input, stretch=1)

        # ==================== 发送/停止按钮 ====================
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)
        button_layout.setAlignment(Qt.AlignBottom)

        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.setFont(FONTS['body'])
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.setFixedSize(80, 40)
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: {COLORS['text_inverse']};
                border: none;
                border-radius: {SIZES['border_radius']}px;
                font-weight: 600;
                font-size: 14px;
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
        """)
        self.send_button.clicked.connect(self._on_send)
        button_layout.addWidget(self.send_button)

        # 停止按钮 (初始隐藏)
        self.stop_button = QPushButton("停止")
        self.stop_button.setFont(FONTS['body'])
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setFixedSize(80, 40)
        self.stop_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_red']};
                color: {COLORS['text_inverse']};
                border: none;
                border-radius: {SIZES['border_radius']}px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            QPushButton:pressed {{
                background-color: #B91C1C;
            }}
        """)
        self.stop_button.clicked.connect(self._on_stop)
        self.stop_button.hide()
        button_layout.addWidget(self.stop_button)

        input_layout.addWidget(button_container)

        main_layout.addWidget(input_container)
        self._set_input_height(self._min_input_height)

    def _on_text_changed(self):
        """文本变化时动态调整高度"""
        # 计算内容高度
        doc = self.text_input.document()
        doc_height = doc.size().height()

        # 根据内容调整高度 (限制在最小/最大之间)
        new_height = max(self._min_input_height, min(self._max_input_height, int(doc_height + 20)))
        self._set_input_height(new_height)

        # 更新发送按钮状态
        has_text = bool(self.text_input.toPlainText().strip())
        self.send_button.setEnabled(has_text and not self._is_generating)
        self._schedule_draft_emit()

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理 Enter 键发送"""
        if obj == self.text_input and event.type() == event.Type.KeyPress:
            # Enter 发送, Shift+Enter 换行
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if event.modifiers() == Qt.ShiftModifier:
                    # Shift+Enter - 插入换行符
                    return False
                else:
                    # Enter - 发送消息
                    if self.send_button.isEnabled():
                        self._on_send()
                    return True
        return super().eventFilter(obj, event)

    def _on_send(self):
        """发送消息"""
        message = self.text_input.toPlainText().strip()
        if not message:
            return

        # 发射信号
        self.message_sent.emit(message)

        # 清空输入框
        self.text_input.clear()
        self._schedule_draft_emit()
        self._set_input_height(self._min_input_height)

    def _on_stop(self):
        """停止生成"""
        self.stop_requested.emit()

    def _schedule_draft_emit(self) -> None:
        """防抖触发草稿变化事件。"""

        self._draft_timer.start()

    def _emit_draft_changed(self) -> None:
        self.draft_changed.emit(self.get_input_text())

    def _set_input_height(self, height: int) -> None:
        height = max(self._min_input_height, min(self._max_input_height, height))
        if self.text_input.height() != height:
            self.text_input.setFixedHeight(height)

    def _on_attach_file(self):
        """附加文件"""
        # TODO: 打开文件选择对话框
        self.file_uploaded.emit("test_file.txt")

    def _on_help(self):
        """帮助"""
        self.help_requested.emit()

    def _on_history(self):
        """历史记录"""
        self.history_requested.emit()

    def _on_template(self):
        """使用模板"""
        self.template_requested.emit()

    def _on_voice(self):
        """语音输入"""
        self.voice_input_requested.emit()

    def set_generating(self, generating: bool):
        """
        设置生成状态

        Args:
            generating: True=正在生成, False=空闲
        """
        self._is_generating = generating

        if generating:
            # 显示停止按钮,隐藏发送按钮
            self.send_button.hide()
            self.stop_button.show()
            self.text_input.setEnabled(False)
        else:
            # 显示发送按钮,隐藏停止按钮
            self.stop_button.hide()
            self.send_button.show()
            self.text_input.setEnabled(True)
            self._on_text_changed()  # 更新发送按钮状态

    def set_input_text(self, text: str):
        """设置输入框文本"""
        self.text_input.setPlainText(text)
        self._schedule_draft_emit()
        if not text:
            self._set_input_height(self._min_input_height)

    def get_input_text(self) -> str:
        """获取输入框文本"""
        return self.text_input.toPlainText()

    def clear_input(self):
        """清空输入框"""
        self.text_input.clear()
        self._schedule_draft_emit()
        self._set_input_height(self._min_input_height)

    def focus_input(self):
        """聚焦到输入框"""
        self.text_input.setFocus()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QVBoxLayout, QLabel

    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("Cherry Studio Input Area Test")
    window.resize(800, 400)

    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # 测试说明区域
    info_label = QLabel("测试说明:\n"
                       "1. 输入文本,按 Enter 发送\n"
                       "2. Shift+Enter 换行\n"
                       "3. 点击工具栏按钮测试功能\n"
                       "4. 点击'模拟生成'测试停止按钮")
    info_label.setFont(FONTS['body'])
    info_label.setStyleSheet(f"""
        QLabel {{
            background: {COLORS['bg_sidebar']};
            color: {COLORS['text_secondary']};
            padding: {SPACING['md']}px;
            border-bottom: 1px solid {COLORS['border']};
        }}
    """)
    layout.addWidget(info_label)

    # 测试消息显示区域
    message_display = QLabel("等待消息...")
    message_display.setFont(FONTS['body'])
    message_display.setAlignment(Qt.AlignCenter)
    message_display.setWordWrap(True)
    message_display.setStyleSheet(f"""
        QLabel {{
            background: {COLORS['bg_main']};
            color: {COLORS['text_primary']};
            padding: {SPACING['lg']}px;
        }}
    """)
    layout.addWidget(message_display, stretch=1)

    # 添加输入区域
    input_area = CherryInputArea()
    layout.addWidget(input_area)

    # 添加测试按钮
    test_btn_container = QWidget()
    test_btn_layout = QHBoxLayout(test_btn_container)
    test_btn_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])

    generate_btn = QPushButton("模拟生成 (5秒)")
    generate_btn.setFont(FONTS['body'])
    generate_btn.clicked.connect(lambda: input_area.set_generating(True))

    def stop_generating():
        input_area.set_generating(False)
        message_display.setText("生成已停止")

    # 5秒后自动停止
    def auto_stop():
        QTimer.singleShot(5000, stop_generating)

    generate_btn.clicked.connect(auto_stop)
    test_btn_layout.addWidget(generate_btn)

    layout.addWidget(test_btn_container)

    # 连接信号测试
    def on_message_sent(msg):
        message_display.setText(f"✅ 发送消息:\n{msg}")

    def on_file_uploaded(filename):
        message_display.setText(f"📎 上传文件: {filename}")

    def on_help():
        message_display.setText("❓ 请求帮助")

    def on_history():
        message_display.setText("🕒 查看历史记录")

    def on_template():
        message_display.setText("📝 使用模板")

    def on_voice():
        message_display.setText("🎤 语音输入")

    def on_stop():
        stop_generating()

    input_area.message_sent.connect(on_message_sent)
    input_area.file_uploaded.connect(on_file_uploaded)
    input_area.help_requested.connect(on_help)
    input_area.history_requested.connect(on_history)
    input_area.template_requested.connect(on_template)
    input_area.voice_input_requested.connect(on_voice)
    input_area.stop_requested.connect(on_stop)

    window.show()
    sys.exit(app.exec())
