# -*- coding: utf-8 -*-
"""
Simple debug script to check column headers in Excel file
"""
import openpyxl
from pathlib import Path

def main():
    excel_file = Path("d:/Code/快报填写程序/（科电）国资委、财政快报模板-纯净版 的副本.xlsx")

    print("=" * 80)
    print("Checking Excel file column headers")
    print("=" * 80)

    wb = openpyxl.load_workbook(excel_file, data_only=True)
    sheet = wb["财政局-快报"]

    print(f"\nSheet: 财政局-快报")
    print(f"Dimensions: {sheet.dimensions}")

    print("\nRow 1:")
    for col_idx, cell in enumerate(sheet[1], start=1):
        print(f"  Col {col_idx} ({cell.column_letter}): '{cell.value}'")

    print("\nRow 2:")
    for col_idx, cell in enumerate(sheet[2], start=1):
        print(f"  Col {col_idx} ({cell.column_letter}): '{cell.value}'")

    print("\nRow 3:")
    for col_idx, cell in enumerate(sheet[3], start=1):
        print(f"  Col {col_idx} ({cell.column_letter}): '{cell.value}'")

    # Check if any column contains "行次"
    print("\n" + "=" * 80)
    print("Searching for '行次' in headers")
    print("=" * 80)

    found = False
    for row_idx in [1, 2, 3]:
        for col_idx, cell in enumerate(sheet[row_idx], start=1):
            if cell.value and '行次' in str(cell.value):
                print(f"FOUND at Row {row_idx}, Col {col_idx} ({cell.column_letter}): '{cell.value}'")
                found = True

    if not found:
        print("NOT FOUND in first 3 rows")

    wb.close()

if __name__ == "__main__":
    main()
