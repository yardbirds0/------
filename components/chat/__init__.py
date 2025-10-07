# -*- coding: utf-8 -*-
"""
Cherry Studio Chat Components Package
Cherry Studio 对话界面相关的所有 UI 组件
"""

from .main_window import CherryMainWindow

# 向后兼容：ChatWindow别名
ChatWindow = CherryMainWindow

__all__ = [
    'CherryMainWindow',
    'ChatWindow',  # 向后兼容别名
]
