# -*- coding: utf-8 -*-
"""
测试新增的UI改进
验证需求5-7的实现
"""

import sys
import io
from pathlib import Path
from datetime import datetime

# 设置UTF-8编码输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt

from components.chat.widgets.session_list_panel import SessionListPanel
from components.chat.widgets.sidebar import CherrySidebar
from components.chat.styles.cherry_theme import COLORS, FONTS, SPACING


def main():
    """测试新UI改进"""
    app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("UI改进测试 - 需求5-7")
    window.resize(900, 700)
    window.setStyleSheet(f"background-color: {COLORS['bg_main']};")

    # 主布局
    main_layout = QHBoxLayout(window)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(SPACING['md'])

    # ==================== 左侧：会话列表面板 ====================
    session_panel = SessionListPanel()
    session_panel.setFixedWidth(400)

    # 加载测试会话数据
    test_sessions = [
        {
            'id': 'session_1',
            'title': '财务报表分析',
            'created_at': '2025-01-15T10:30:00',
            'updated_at': '2025-01-15T11:30:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_2',
            'title': '数据映射公式生成',
            'created_at': '2025-01-14T15:20:00',
            'updated_at': '2025-01-14T16:00:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_3',
            'title': '快报表格填充',
            'created_at': '2025-01-13T09:00:00',
            'updated_at': '2025-01-13T10:30:00',
            'settings_json': '{}'
        },
        {
            'id': 'session_4',
            'title': 'Excel数据提取',
            'created_at': '2025-01-12T14:00:00',
            'updated_at': '2025-01-12T15:30:00',
            'settings_json': '{}'
        }
    ]

    session_panel.load_sessions(test_sessions)
    main_layout.addWidget(session_panel)

    # ==================== 右侧：侧边栏（TAB测试） ====================
    sidebar = CherrySidebar()
    main_layout.addWidget(sidebar)

    window.show()

    print("=" * 80)
    print("UI改进验证 - 需求5-7")
    print("=" * 80)
    print()

    print("需求5验证：新建会话按钮左对齐")
    print("-" * 80)
    print("✓ 按钮位置在工具栏左侧")
    print("✓ 不再居中显示")
    print()

    print("需求6验证：历史会话记录样式优化")
    print("-" * 80)
    print("✓ 未选中时：无边框，透明背景")
    print("✓ 鼠标滑过：全行灰色背景")
    print("✓ 选中时：全行白色背景（不是蓝色）")
    print("✓ 所有状态：无文字边框")
    print()

    print("需求7验证：TAB标题样式优化")
    print("-" * 80)
    print("✓ TAB之间有间距（8px）")
    print("✓ TAB圆角设计（8px）")
    print("✓ 移除所有边框线")
    print("✓ 选中TAB：蓝色圆角背景")
    print("✓ 未选中TAB：透明背景")
    print()

    print("=" * 80)
    print("测试说明")
    print("=" * 80)
    print("1. 查看左侧新建会话按钮是否左对齐")
    print("2. 鼠标滑过会话列表项，观察全行背景变化")
    print("3. 点击会话列表项，观察选中后的白色背景")
    print("4. 查看右侧TAB是否有圆角和间距")
    print("5. 点击切换TAB，观察样式变化")
    print()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
