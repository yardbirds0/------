# -*- coding: utf-8 -*-
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from models.data_models import WorkbookManager
from main import TargetItemModel
from PySide6.QtCore import Qt

def main():
    print("=" * 80)
    print("Debug: Column Detection Test")
    print("=" * 80)

    # Load Excel file
    excel_file = "（科电）国资委、财政快报模板-纯净版 的副本.xlsx"
    print(f"\nLoading file: {excel_file}")

    file_manager = FileManager()
    success, message = file_manager.load_excel_files([excel_file])

    if not success:
        print(f"Failed to load file: {message}")
        return

    print(f"Success: {message}")

    # Get workbook_manager from file_manager
    workbook_manager = file_manager.workbook_manager
    if not workbook_manager:
        print("ERROR: workbook_manager is None")
        return

    data_extractor = DataExtractor(workbook_manager)

    target_sheets = ["财政局-快报"]
    source_sheets = [name for name in file_manager.current_workbook.sheetnames
                     if name not in target_sheets]

    print(f"\nTarget sheets: {target_sheets}")
    print(f"Source sheets: {source_sheets}")

    data_extractor.extract_all_data(target_sheets, source_sheets)

    # Check target_sheet_columns
    print("\n" + "=" * 80)
    print("Checking target_sheet_columns")
    print("=" * 80)

    sheet_name = "财政局-快报"
    if sheet_name in workbook_manager.target_sheet_columns:
        columns = workbook_manager.target_sheet_columns[sheet_name]
        print(f"\nTotal {len(columns)} columns:")
        for i, col in enumerate(columns):
            display_name = col['display_name']
            key = col['key']
            col_letter = col.get('column_letter', 'N/A')
            print(f"  [{i}] key='{key}', display_name='{display_name}', column_letter='{col_letter}'")

            # Check if this is row number column
            if '行次' in display_name:
                print(f"      >>> FOUND ROW NUMBER COLUMN! <<<")
    else:
        print(f"Sheet not found: {sheet_name}")
        return

    # Check TargetItemModel.headers
    print("\n" + "=" * 80)
    print("Checking TargetItemModel.headers")
    print("=" * 80)

    target_model = TargetItemModel(workbook_manager)
    target_model.set_active_sheet(sheet_name)

    print(f"\nstatic_headers: {target_model.static_headers}")
    print(f"dynamic_columns count: {len(target_model.dynamic_columns)}")
    print(f"\nheaders list (total {len(target_model.headers)} columns):")
    for i, header in enumerate(target_model.headers):
        print(f"  [{i}] '{header}'")
        if '行次' in header:
            print(f"      >>> FOUND ROW NUMBER IN HEADERS! <<<")

    # Check headerData() return values
    print("\n" + "=" * 80)
    print("Checking headerData() return values")
    print("=" * 80)

    print(f"\n_header_row_count: {target_model._header_row_count}")
    print(f"_header_layout keys: {list(target_model._header_layout.keys())}")

    for i in range(len(target_model.headers)):
        header_data = target_model.headerData(i, Qt.Horizontal, Qt.DisplayRole)
        headers_value = target_model.headers[i]
        print(f"  [{i}] headerData()='{header_data}' | headers[{i}]='{headers_value}'")

    # Simulate adjust_main_table_columns() logic
    print("\n" + "=" * 80)
    print("Simulating adjust_main_table_columns() column name detection")
    print("=" * 80)

    print("\nMethod 1: Using model.headers (FIXED CODE)")
    found = False
    for column in range(len(target_model.headers)):
        column_name = target_model.headers[column] if column < len(target_model.headers) else ""
        if '行次' in column_name:
            print(f"  SUCCESS! Found row number column at index: {column}")
            found = True
            break
    if not found:
        print(f"  FAILED: Row number column not found")

    print("\nMethod 2: Using model.headerData() (OLD CODE)")
    found = False
    for column in range(len(target_model.headers)):
        column_name = target_model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
        if not column_name:
            print(f"  WARNING: Column {column} headerData() returns empty string")
        if '行次' in str(column_name):
            print(f"  SUCCESS! Found row number column at index: {column}")
            found = True
            break
    if not found:
        print(f"  FAILED: Row number column not found")

    # Final check
    print("\n" + "=" * 80)
    print("Final check: Is row number column in headers?")
    print("=" * 80)

    row_num_found = False
    for i, h in enumerate(target_model.headers):
        if '行次' in h:
            print(f"YES! Row number column found at index {i}: '{h}'")
            row_num_found = True
            break

    if not row_num_found:
        print(f"NO! Row number column not found in headers")
        print(f"Headers content: {target_model.headers}")

if __name__ == "__main__":
    main()
