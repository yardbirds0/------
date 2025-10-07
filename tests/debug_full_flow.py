# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.file_manager import FileManager
from models.data_models import WorkbookManager
from main import TargetItemModel
from PySide6.QtCore import Qt

def main():
    print("=" * 80)
    print("DEBUG: Full data flow analysis")
    print("=" * 80)

    # Step 1: Load file using FileManager (same as main.py)
    excel_file = "（科电）国资委、财政快报模板-纯净版 的副本.xlsx"
    print(f"\n[1] Loading file: {excel_file}")

    file_manager = FileManager()
    success, message = file_manager.load_excel_files([excel_file])

    if not success:
        print(f"FAILED: {message}")
        return

    print(f"SUCCESS: {message}")

    workbook_manager = file_manager.workbook_manager
    if not workbook_manager:
        print("ERROR: workbook_manager is None")
        return

    # Step 2: Check flash report classification
    print("\n[2] Checking flash report classification")
    print(f"Flash reports: {workbook_manager.flash_report_sheets}")

    if "财政局-快报" not in workbook_manager.flash_report_sheets:
        print("WARNING: '财政局-快报' not in flash_report_sheets!")
    else:
        print("✓ '财政局-快报' IS in flash_report_sheets")

    # Step 3: Check target_sheet_columns
    print("\n[3] Checking target_sheet_columns['财政局-快报']")

    if "财政局-快报" in workbook_manager.target_sheet_columns:
        columns = workbook_manager.target_sheet_columns["财政局-快报"]
        print(f"Total columns: {len(columns)}")
        for i, col in enumerate(columns):
            display_name = col['display_name']
            key = col['key']
            col_letter = col.get('column_letter', 'N/A')
            print(f"  [{i}] display_name='{display_name}', key='{key}', col_letter='{col_letter}'")

            if '行次' in display_name:
                print(f"      >>> FOUND ROW NUMBER COLUMN! <<<")
    else:
        print("ERROR: '财政局-快报' not in target_sheet_columns")
        return

    # Step 4: Create TargetItemModel and check headers
    print("\n[4] Creating TargetItemModel and checking headers")

    target_model = TargetItemModel(workbook_manager)
    target_model.set_active_sheet("财政局-快报")

    print(f"static_headers: {target_model.static_headers}")
    print(f"dynamic_columns count: {len(target_model.dynamic_columns)}")

    print(f"\nheaders list ({len(target_model.headers)} total):")
    for i, header in enumerate(target_model.headers):
        print(f"  [{i}] '{header}'")
        if '行次' in header:
            print(f"      >>> FOUND IN HEADERS! <<<")

    # Step 5: Check headerData() vs headers[]
    print("\n[5] Comparing headerData() and headers[]")
    print(f"_header_row_count: {target_model._header_row_count}")
    print(f"_header_layout keys: {list(target_model._header_layout.keys())[:10]}")  # First 10

    for i in range(min(len(target_model.headers), 8)):  # Check first 8 columns
        header_data = target_model.headerData(i, Qt.Horizontal, Qt.DisplayRole)
        headers_value = target_model.headers[i]

        match = "✓" if header_data == headers_value else "✗"
        print(f"  [{i}] {match} headerData()='{header_data}' | headers[{i}]='{headers_value}'")

    # Step 6: Simulate adjust_main_table_columns() logic
    print("\n[6] Simulating adjust_main_table_columns() column detection")

    print("\nMethod 1: Using model.headers (FIXED CODE)")
    found_index = None
    for column in range(len(target_model.headers)):
        column_name = target_model.headers[column] if column < len(target_model.headers) else ""
        if column_name == "行次":
            found_index = column
            print(f"  ✓ FOUND at index {column}: '{column_name}'")
            break
    if found_index is None:
        print(f"  ✗ NOT FOUND")

    print("\nMethod 2: Using model.headerData() (OLD CODE - will fail for multi-row headers)")
    found_index = None
    for column in range(len(target_model.headers)):
        column_name = target_model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
        if column_name == "行次":
            found_index = column
            print(f"  ✓ FOUND at index {column}: '{column_name}'")
            break
        elif not column_name and column < len(target_model.headers):
            headers_val = target_model.headers[column]
            if headers_val == "行次":
                print(f"  ⚠ headerData() returned empty for index {column}, but headers[{column}]='{headers_val}'")

    if found_index is None:
        print(f"  ✗ NOT FOUND using headerData()")

    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if "行次" in target_model.headers:
        idx = target_model.headers.index("行次")
        print(f"✓ '行次' column EXISTS in headers at index {idx}")
        print(f"  - This means the fixed code WILL work")
    else:
        print(f"✗ '行次' column NOT FOUND in headers")
        print(f"  - Available headers: {target_model.headers}")

if __name__ == "__main__":
    main()
