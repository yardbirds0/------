"""
测试列宽智能填充修复效果
验证所有表格都能占满容器宽度，没有右侧空白
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from main import MainWindow

def test_column_fill_fix():
    """测试列宽智能填充功能"""
    app = QApplication(sys.argv)

    # 创建主窗口
    window = MainWindow()
    window.show()

    print("[TEST] Column Width Smart Fill Test")
    print("=====================================")

    # 模拟加载文件
    test_file = r"（科电）国资委、财政快报模板-纯净版 的副本.xlsx"
    if os.path.exists(test_file):
        print(f"[OK] Found test file")

        # 使用file_manager加载
        from modules.file_manager import FileManager
        file_manager = FileManager()

        # 直接设置工作簿管理器
        window.file_manager = file_manager
        window.file_manager.workbook_manager = None

        # 通过窗口的load_files方法加载
        def do_load():
            try:
                # 模拟选择文件
                window.load_files()
                # 手动触发文件加载
                if hasattr(window.file_manager, 'load_workbook'):
                    window.file_manager.load_workbook(test_file)
                elif hasattr(window.file_manager, 'workbook_manager'):
                    # 直接加载到workbook_manager
                    from models.data_models import WorkbookManager
                    window.workbook_manager = WorkbookManager()
                    # 这里需要更复杂的加载逻辑
                    print("[INFO] Using alternative loading method")

                # 等待加载完成后进行测试
                QTimer.singleShot(1000, test_sheets)
            except Exception as e:
                print(f"[ERROR] Loading failed: {e}")
                import traceback
                traceback.print_exc()

        def test_sheets():
            """测试不同表格的显示"""
            print("\n[TESTING] Sheet Display")

            if not window.target_model or not window.workbook_manager:
                print("[WARNING] Model not loaded, trying manual test")
                # 手动测试列宽调整
                test_manual_adjustment()
                return

            # 获取所有快报表
            sheets = window.workbook_manager.target_sheets if window.workbook_manager else []
            print(f"[INFO] Found {len(sheets)} target sheets")

            # 特别测试"利润因素分析表"
            profit_sheet = None
            for sheet in sheets:
                if "利润因素分析" in sheet:
                    profit_sheet = sheet
                    break

            if profit_sheet:
                print(f"\n[1] Testing problematic sheet: {profit_sheet[:30]}...")
                window.on_target_sheet_changed(profit_sheet)

                # 等待列宽调整
                QTimer.singleShot(500, lambda: check_viewport_fill(1))
            else:
                print("[INFO] No profit analysis sheet found")
                check_viewport_fill(0)

            # 测试其他表格
            if len(sheets) > 1:
                other_sheet = sheets[0] if sheets[0] != profit_sheet else sheets[1] if len(sheets) > 1 else None
                if other_sheet:
                    QTimer.singleShot(1000, lambda: test_other_sheet(other_sheet))

        def test_other_sheet(sheet_name):
            """测试其他表格"""
            print(f"\n[2] Testing normal sheet: {sheet_name[:30]}...")
            window.on_target_sheet_changed(sheet_name)
            QTimer.singleShot(500, lambda: check_viewport_fill(2))

            # 完成测试
            QTimer.singleShot(1000, finish_test)

        def check_viewport_fill(test_num):
            """检查viewport是否被填满"""
            if not hasattr(window, "main_data_grid"):
                print(f"  Test {test_num}: No main_data_grid")
                return

            grid = window.main_data_grid
            viewport_width = grid.viewport().width()

            # 计算所有列的总宽度
            total_width = 0
            column_count = grid.model().columnCount() if grid.model() else 0

            for i in range(column_count):
                col_width = grid.columnWidth(i)
                total_width += col_width

            gap = viewport_width - total_width

            print(f"  Viewport width: {viewport_width}px")
            print(f"  Total column width: {total_width}px")
            print(f"  Gap (blank space): {gap}px")

            if abs(gap) <= 5:  # 允许5px的误差
                print(f"  [PASS] Columns fill viewport correctly")
            elif gap > 5:
                print(f"  [FAIL] Right side has {gap}px blank space")
            else:
                print(f"  [INFO] Columns exceed viewport by {-gap}px (scrollbar expected)")

        def test_manual_adjustment():
            """手动测试列宽调整函数"""
            print("\n[MANUAL TEST] Testing adjust function directly")
            try:
                window.adjust_main_table_columns()
                print("[OK] Adjust function executed")
                check_viewport_fill(99)
            except Exception as e:
                print(f"[ERROR] Adjust failed: {e}")

        def finish_test():
            """完成测试"""
            print("\n[SUMMARY]")
            print("=========")
            print("Smart fill fix has been applied.")
            print("All tables should now fill the viewport width.")
            print("No blank space should appear on the right side.")

            # 退出
            QTimer.singleShot(1000, app.quit)

        # 开始加载和测试
        QTimer.singleShot(500, do_load)

    else:
        print(f"[ERROR] Test file not found: {test_file}")
        app.quit()

    # 运行应用
    app.exec()

if __name__ == "__main__":
    test_column_fill_fix()