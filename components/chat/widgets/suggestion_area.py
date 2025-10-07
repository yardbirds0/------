# -*- coding: utf-8 -*-
"""
Cherry Studio Suggestion Area
建议芯片区域 - 显示快捷建议,点击填充到输入框
"""

from typing import List
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QScrollArea, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..styles.cherry_theme import COLORS, FONTS, SIZES, SPACING


class SuggestionChip(QPushButton):
    """
    建议芯片按钮
    圆角按钮,点击时发射建议文本
    """

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)

        self._text = text
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setFont(FONTS['body_small'])

        # 芯片样式
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 16px;
                padding: 6px 16px;
                font-size: 13px;
                text-align: center;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                border: 1px solid {COLORS['border_focus']};
                color: {COLORS['accent_blue']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['bg_active']};
                border: 1px solid {COLORS['accent_blue']};
            }}
        """)

    def get_text(self) -> str:
        """获取建议文本"""
        return self._text


class CherrySuggestionArea(QWidget):
    """
    Cherry Studio 建议芯片区域
    水平滚动显示多个建议芯片
    """

    # 信号定义
    suggestion_clicked = Signal(str)  # 建议被点击,发射建议文本

    def __init__(self, parent=None):
        super().__init__(parent)

        # 默认建议列表
        self._suggestions: List[str] = []

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet(f"background-color: {COLORS['bg_main']};")

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING['md'], 0, SPACING['md'], SPACING['sm'])
        main_layout.setSpacing(SPACING['xs'])

        # 标题
        title_label = QLabel("💡 建议提示")
        title_label.setFont(FONTS['caption'])
        title_label.setStyleSheet(f"color: {COLORS['text_tertiary']}; background: transparent;")
        main_layout.addWidget(title_label)

        # 水平滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFixedHeight(56)  # 固定高度
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: {COLORS['bg_main']};
                border: none;
            }}
            QScrollBar:horizontal {{
                height: 6px;
                background: {COLORS['bg_sidebar']};
                border-radius: 3px;
            }}
            QScrollBar::handle:horizontal {{
                background: {COLORS['border']};
                border-radius: 3px;
                min-width: 40px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {COLORS['text_tertiary']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)

        # 芯片容器
        self.chips_container = QWidget()
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 4, 0, 4)
        self.chips_layout.setSpacing(SPACING['sm'])
        self.chips_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 添加弹性空间(初始为空时显示)
        self.chips_layout.addStretch()

        scroll_area.setWidget(self.chips_container)
        main_layout.addWidget(scroll_area)

        # 设置默认建议
        self.set_suggestions([
            "帮我分析这份财务报表的数据结构",
            "生成营业收入的映射公式",
            "如何提取利润表中的数据?",
            "解释快报表的填充逻辑",
        ])

    def set_suggestions(self, suggestions: List[str]):
        """
        设置建议列表

        Args:
            suggestions: 建议文本列表
        """
        # 清空现有芯片
        self.clear_suggestions()

        self._suggestions = suggestions

        # 创建芯片按钮
        for suggestion in suggestions:
            chip = SuggestionChip(suggestion)
            chip.clicked.connect(lambda checked, text=suggestion: self._on_chip_clicked(text))
            self.chips_layout.insertWidget(self.chips_layout.count() - 1, chip)

    def add_suggestion(self, text: str):
        """
        添加单个建议

        Args:
            text: 建议文本
        """
        self._suggestions.append(text)

        chip = SuggestionChip(text)
        chip.clicked.connect(lambda checked, t=text: self._on_chip_clicked(t))
        self.chips_layout.insertWidget(self.chips_layout.count() - 1, chip)

    def clear_suggestions(self):
        """清空所有建议"""
        # 删除所有芯片widget
        for i in reversed(range(self.chips_layout.count())):
            item = self.chips_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), SuggestionChip):
                item.widget().deleteLater()

        self._suggestions.clear()

    def _on_chip_clicked(self, text: str):
        """芯片被点击"""
        self.suggestion_clicked.emit(text)

    def get_suggestions(self) -> List[str]:
        """获取所有建议文本"""
        return self._suggestions.copy()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QVBoxLayout, QLabel, QPushButton

    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("Cherry Studio Suggestion Area Test")
    window.resize(900, 400)

    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # 测试说明区域
    info_label = QLabel("测试说明:\n"
                       "1. 点击建议芯片,下方会显示选中的建议\n"
                       "2. 点击'切换建议'测试动态更新\n"
                       "3. 点击'清空建议'测试清空功能")
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

    # 选中建议显示区域
    selected_label = QLabel("等待选择建议...")
    selected_label.setFont(QFont(FONTS['body'].family(), 16))
    selected_label.setAlignment(Qt.AlignCenter)
    selected_label.setWordWrap(True)
    selected_label.setStyleSheet(f"""
        QLabel {{
            background: {COLORS['bg_main']};
            color: {COLORS['text_primary']};
            padding: {SPACING['lg']}px;
            font-weight: 600;
        }}
    """)
    layout.addWidget(selected_label, stretch=1)

    # 添加建议区域
    suggestion_area = CherrySuggestionArea()
    layout.addWidget(suggestion_area)

    # 测试按钮区域
    test_btn_container = QWidget()
    test_btn_layout = QHBoxLayout(test_btn_container)
    test_btn_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
    test_btn_layout.setSpacing(SPACING['sm'])

    # 切换建议按钮
    suggestion_sets = [
        [
            "帮我分析这份财务报表的数据结构",
            "生成营业收入的映射公式",
            "如何提取利润表中的数据?",
            "解释快报表的填充逻辑",
        ],
        [
            "什么是资产负债表?",
            "现金流量表包含哪些项目?",
            "如何计算利润总额?",
            "税金及附加是什么?",
        ],
        [
            "如何使用AI助手?",
            "支持哪些文件格式?",
            "映射公式的语法规则",
        ]
    ]
    current_set_index = [0]

    def toggle_suggestions():
        current_set_index[0] = (current_set_index[0] + 1) % len(suggestion_sets)
        suggestion_area.set_suggestions(suggestion_sets[current_set_index[0]])
        selected_label.setText(f"已切换到建议集 {current_set_index[0] + 1}")

    toggle_btn = QPushButton("切换建议")
    toggle_btn.setFont(FONTS['body'])
    toggle_btn.clicked.connect(toggle_suggestions)
    test_btn_layout.addWidget(toggle_btn)

    # 清空建议按钮
    clear_btn = QPushButton("清空建议")
    clear_btn.setFont(FONTS['body'])
    clear_btn.clicked.connect(lambda: (
        suggestion_area.clear_suggestions(),
        selected_label.setText("建议已清空")
    ))
    test_btn_layout.addWidget(clear_btn)

    # 添加建议按钮
    add_btn = QPushButton("添加建议")
    add_btn.setFont(FONTS['body'])
    add_counter = [1]

    def add_suggestion():
        new_suggestion = f"新建议 #{add_counter[0]}"
        suggestion_area.add_suggestion(new_suggestion)
        selected_label.setText(f"已添加: {new_suggestion}")
        add_counter[0] += 1

    add_btn.clicked.connect(add_suggestion)
    test_btn_layout.addWidget(add_btn)

    test_btn_layout.addStretch()

    layout.addWidget(test_btn_container)

    # 连接信号测试
    def on_suggestion_clicked(text):
        selected_label.setText(f"✅ 选中建议:\n\n{text}")

    suggestion_area.suggestion_clicked.connect(on_suggestion_clicked)

    window.show()
    sys.exit(app.exec())
