# -*- coding: utf-8 -*-
"""
Cherry Studio Light Theme
精确复刻 cherry-studio-ui.png 的视觉风格
"""

from PySide6.QtGui import QFont
from PySide6.QtCore import QEasingCurve

# ==================== 颜色系统 ====================
# 基于 cherry-studio-ui.png 提取的颜色值

COLORS = {
    # 背景色
    "bg_main": "#FFFFFF",  # 主背景 - 白色
    "bg_sidebar": "#F7F8FA",  # 侧边栏背景 - 浅灰
    "bg_input": "#F7F8FA",  # 输入框背景 - 浅灰
    "bg_hover": "#F0F1F3",  # 悬停背景
    "bg_active": "#E8E9EB",  # 激活背景
    "bg_drawer": "#FFFFFF",  # 抽屉背景 - 白色
    # 文字颜色
    "text_primary": "#1F2937",  # 主文字 - 深灰
    "text_secondary": "#6B7280",  # 次要文字 - 中灰
    "text_tertiary": "#9CA3AF",  # 三级文字 - 浅灰
    "text_disabled": "#D1D5DB",  # 禁用文字
    "text_inverse": "#FFFFFF",  # 反色文字 - 白色
    # 强调色
    "accent_blue": "#3B82F6",  # 主强调色 - 蓝色
    "accent_green": "#10B981",  # 成功/开关 - 绿色
    "accent_red": "#EF4444",  # 危险/错误 - 红色
    "accent_yellow": "#F59E0B",  # 警告 - 黄色
    # 边框颜色
    "border": "#E5E7EB",  # 默认边框
    "border_light": "#F3F4F6",  # 浅色边框
    "border_focus": "#3B82F6",  # 聚焦边框
    # 消息气泡颜色
    "bubble_user_bg": "#3B82F6",  # 用户消息背景 - 蓝色
    "bubble_user_text": "#FFFFFF",  # 用户消息文字 - 白色
    "bubble_ai_bg": "#F7F8FA",  # AI消息背景 - 浅灰
    "bubble_ai_text": "#1F2937",  # AI消息文字 - 深灰
    # 代码块颜色
    "code_bg": "#F3F4F6",  # 代码背景
    "code_border": "#E5E7EB",  # 代码边框
    # 建议芯片颜色
    "chip_bg": "#FFFFFF",  # 芯片背景
    "chip_border": "#E5E7EB",  # 芯片边框
    "chip_hover_bg": "#F7F8FA",  # 芯片悬停背景
}

# ==================== 字体系统 ====================

# 字体家族（优先级顺序）
FONT_FAMILY = [
    "Microsoft YaHei",  # 微软雅黑（Windows中文首选）
    "PingFang SC",  # 苹方（macOS中文首选）
    "Segoe UI",  # Windows系统字体
    "Helvetica Neue",  # macOS系统字体
    "Arial",  # 跨平台后备
    "sans-serif",  # 系统默认
]

FONT_FAMILY_MONO = [
    "Consolas",  # Windows等宽字体
    "Monaco",  # macOS等宽字体
    "Courier New",  # 跨平台等宽字体
    "monospace",  # 系统默认等宽
]


def create_font(size: int, weight: int = QFont.Normal, family: str = None) -> QFont:
    """
    创建字体对象

    Args:
        size: 字体大小（像素）
        weight: 字体粗细
        family: 字体家族（可选，默认使用FONT_FAMILY）
    """
    font = QFont(family or FONT_FAMILY[0], size)
    font.setWeight(weight)
    return font


FONTS = {
    # 标题字体
    "title": create_font(16, QFont.DemiBold),  # 窗口标题、标签页
    "subtitle": create_font(14, QFont.DemiBold),  # 子标题
    # 正文字体
    "body": create_font(14, QFont.Normal),  # 正文内容
    "body_small": create_font(12, QFont.Normal),  # 小号正文
    # 按钮字体
    "button": create_font(14, QFont.Medium),  # 按钮文字
    "button_small": create_font(12, QFont.Medium),  # 小按钮
    # 输入框字体
    "input": create_font(14, QFont.Normal),  # 输入框
    # 标签字体
    "label": create_font(12, QFont.Normal),  # 标签
    "caption": create_font(11, QFont.Normal),  # 说明文字
    # 代码字体
    "code": create_font(13, QFont.Normal, FONT_FAMILY_MONO[0]),  # 代码块
}

# ==================== 尺寸系统 ====================

SIZES = {
    # 圆角半径
    "border_radius": 8,  # 默认圆角
    "border_radius_small": 4,  # 小圆角
    "border_radius_large": 12,  # 大圆角
    "border_radius_pill": 999,  # 胶囊形
    # 边框宽度
    "border_width": 1,  # 默认边框
    "border_width_thick": 2,  # 粗边框
    # 图标尺寸
    "icon_small": 16,  # 小图标
    "icon_medium": 20,  # 中图标
    "icon_large": 24,  # 大图标
    # 按钮尺寸
    "button_height": 32,  # 默认按钮高度
    "button_height_small": 28,  # 小按钮高度
    "button_height_large": 40,  # 大按钮高度
    # 输入框尺寸
    "input_height": 40,  # 输入框高度
    "input_min_height": 48,  # 多行输入最小高度
    "input_max_height": 150,  # 多行输入最大高度
    # 侧边栏尺寸
    "sidebar_width": 400,  # 侧边栏宽度（增加80px以完整显示参数标签）
    "sidebar_icon_width": 56,  # Icon导航宽度
    # 消息气泡尺寸
    "bubble_max_width": 600,  # 消息气泡最大宽度
    "bubble_padding": 12,  # 气泡内边距
    # 标题栏尺寸
    "titlebar_height": 48,  # 标题栏高度
    "tab_height": 36,  # 标签页高度
}

# ==================== 间距系统 ====================
# 8px 基础间距系统

SPACING = {
    "xs": 4,  # 0.5x
    "sm": 8,  # 1x
    "md": 16,  # 2x
    "lg": 24,  # 3x
    "xl": 32,  # 4x
    "xxl": 48,  # 6x
}

# ==================== 阴影系统 ====================

SHADOWS = {
    # 轻阴影
    "sm": "0 1px 2px rgba(0, 0, 0, 0.05)",
    # 中阴影
    "md": "0 2px 8px rgba(0, 0, 0, 0.1)",
    # 重阴影
    "lg": "0 4px 16px rgba(0, 0, 0, 0.15)",
    # 抽屉阴影
    "drawer": "0 -4px 16px rgba(0, 0, 0, 0.1)",
}

# ==================== 动画系统 ====================

ANIMATIONS = {
    # 持续时间（毫秒）
    "duration_fast": 150,  # 快速动画
    "duration_normal": 250,  # 普通动画
    "duration_slow": 350,  # 慢速动画
    "duration_drawer": 300,  # 抽屉动画
    # 缓动曲线
    "easing_standard": QEasingCurve.OutCubic,  # 标准缓动
    "easing_decelerate": QEasingCurve.OutQuad,  # 减速
    "easing_accelerate": QEasingCurve.InQuad,  # 加速
}

# ==================== 全局样式表 ====================


def get_global_stylesheet() -> str:
    """
    生成全局 QSS 样式表

    Returns:
        str: 完整的QSS样式表字符串
    """
    return f"""
        /* ==================== 全局样式 ==================== */
        QWidget {{
            background-color: {COLORS['bg_main']};
            color: {COLORS['text_primary']};
            font-family: '{FONT_FAMILY[0]}';
            font-size: 14px;
        }}

        /* ==================== 滚动条样式 ==================== */
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background: {COLORS['border']};
            border-radius: 4px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {COLORS['text_tertiary']};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: none;
        }}

        QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
            margin: 0px;
        }}

        QScrollBar::handle:horizontal {{
            background: {COLORS['border']};
            border-radius: 4px;
            min-width: 30px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {COLORS['text_tertiary']};
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* ==================== 按钮基础样式 ==================== */
        QPushButton {{
            background-color: {COLORS['bg_hover']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            padding: 8px 16px;
            font-size: 14px;
        }}

        QPushButton:hover {{
            background-color: {COLORS['bg_active']};
        }}

        QPushButton:pressed {{
            background-color: {COLORS['border']};
        }}

        QPushButton:disabled {{
            background-color: {COLORS['bg_hover']};
            color: {COLORS['text_disabled']};
        }}

        /* ==================== 主要按钮样式 ==================== */
        QPushButton[styleClass="primary"] {{
            background-color: {COLORS['accent_blue']};
            color: {COLORS['text_inverse']};
            border: none;
        }}

        QPushButton[styleClass="primary"]:hover {{
            background-color: #2563EB;
        }}

        QPushButton[styleClass="primary"]:pressed {{
            background-color: #1D4ED8;
        }}

        /* ==================== 危险按钮样式 ==================== */
        QPushButton[styleClass="danger"] {{
            background-color: {COLORS['accent_red']};
            color: {COLORS['text_inverse']};
            border: none;
        }}

        QPushButton[styleClass="danger"]:hover {{
            background-color: #DC2626;
        }}

        /* ==================== 输入框样式 ==================== */
        QLineEdit, QTextEdit {{
            background-color: {COLORS['bg_input']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: {SIZES['border_radius']}px;
            padding: 8px 12px;
            font-size: 14px;
        }}

        QLineEdit:focus, QTextEdit:focus {{
            border: 1px solid {COLORS['border_focus']};
        }}

        QLineEdit:disabled, QTextEdit:disabled {{
            background-color: {COLORS['bg_hover']};
            color: {COLORS['text_disabled']};
        }}

        /* ==================== 工具提示样式 ==================== */
        QToolTip {{
            background-color: {COLORS['text_primary']};
            color: {COLORS['text_inverse']};
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 12px;
        }}
    """


# ==================== 导出符号 ====================

__all__ = [
    "COLORS",
    "FONTS",
    "SIZES",
    "SPACING",
    "SHADOWS",
    "ANIMATIONS",
    "get_global_stylesheet",
    "create_font",
    "FONT_FAMILY",
    "FONT_FAMILY_MONO",
]
