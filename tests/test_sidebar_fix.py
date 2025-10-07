# -*- coding: utf-8 -*-
"""
测试Sidebar修复 - 验证兼容性信号
"""

import sys
import io
from pathlib import Path

# 设置UTF-8编码输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from components.chat.widgets.sidebar import CherrySidebar
from components.chat.main_window import CherryMainWindow


def test_sidebar_signals():
    """测试Sidebar信号是否完整"""
    print("=" * 80)
    print("测试Sidebar信号完整性")
    print("=" * 80)

    app = QApplication(sys.argv)

    # 创建Sidebar实例
    sidebar = CherrySidebar()

    # 检查所有必需的信号
    required_signals = [
        'new_chat_requested',
        'manage_chats_requested',
        'new_session_requested',
        'session_selected',
        'session_delete_requested',
        'parameter_changed'
    ]

    print("\n检查信号:")
    all_present = True
    for signal_name in required_signals:
        has_signal = hasattr(sidebar, signal_name)
        status = "✓" if has_signal else "✗"
        print(f"  {status} {signal_name}: {has_signal}")
        if not has_signal:
            all_present = False

    if all_present:
        print("\n✓ 所有信号都存在！")
    else:
        print("\n✗ 有信号缺失！")
        return False

    # 测试信号连接
    print("\n测试信号连接:")
    signal_fired = {'new_chat': False, 'new_session': False}

    def on_new_chat():
        signal_fired['new_chat'] = True
        print("  ✓ new_chat_requested 信号触发")

    def on_new_session():
        signal_fired['new_session'] = True
        print("  ✓ new_session_requested 信号触发")

    sidebar.new_chat_requested.connect(on_new_chat)
    sidebar.new_session_requested.connect(on_new_session)

    # 触发新建会话
    print("\n点击新建会话按钮...")
    sidebar.session_list_panel.new_session_btn.click()

    # 检查信号是否都触发
    if signal_fired['new_chat'] and signal_fired['new_session']:
        print("\n✓ 兼容性信号工作正常！")
        return True
    else:
        print("\n✗ 信号触发失败！")
        print(f"  new_chat_requested: {signal_fired['new_chat']}")
        print(f"  new_session_requested: {signal_fired['new_session']}")
        return False


def test_main_window_import():
    """测试主窗口导入"""
    print("\n" + "=" * 80)
    print("测试主窗口导入")
    print("=" * 80)

    try:
        from components.chat.main_window import CherryMainWindow
        print("\n✓ CherryMainWindow 导入成功")
        return True
    except Exception as e:
        print(f"\n✗ CherryMainWindow 导入失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Sidebar 修复验证测试" + " " * 37 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    results = []

    # 测试1: Sidebar信号
    results.append(("Sidebar信号完整性", test_sidebar_signals()))

    # 测试2: 主窗口导入
    results.append(("主窗口导入", test_main_window_import()))

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status}: {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！修复成功！")
        return 0
    else:
        print("\n❌ 有测试失败，需要进一步检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())
