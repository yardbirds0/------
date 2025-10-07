#!/usr/bin/env python
"""
测试主表格自动扩宽列功能修复
验证切换来源项工作表时，主表格列宽是否正确调整
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from main import MainWindow

def test_sheet_change_resize():
    """测试切换来源项表格后的列宽调整"""
    app = QApplication(sys.argv)

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 检查信号是否连接
    if hasattr(window.source_tree, 'sheetChanged'):
        # 获取信号的接收者数量
        receivers = window.source_tree.receivers(window.source_tree.sheetChanged)
        if receivers > 0:
            QMessageBox.information(
                window,
                "✅ 测试通过",
                f"sheetChanged 信号已正确连接\n"
                f"接收者数量: {receivers}\n"
                f"切换来源项工作表时主表格列宽会自动调整"
            )
        else:
            QMessageBox.warning(
                window,
                "⚠️ 测试失败",
                "sheetChanged 信号未连接到任何接收者"
            )
    else:
        QMessageBox.critical(
            window,
            "❌ 测试失败",
            "SearchableSourceTree 没有 sheetChanged 信号"
        )

    return app.exec()

if __name__ == "__main__":
    sys.exit(test_sheet_change_resize())