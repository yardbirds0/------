# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from main import TargetItemModel

def main():
    print("=" * 80)
    print("FINAL DEBUG: Check exact '行次' column name")
    print("=" * 80)

    # Load file
    excel_file = "（科电）国资委、财政快报模板-纯净版 的副本.xlsx"
    file_manager = FileManager()
    success, _ = file_manager.load_excel_files([excel_file])

    if not success:
        print("Failed to load file")
        return

    workbook_manager = file_manager.workbook_manager

    # Extract data
    extractor = DataExtractor(workbook_manager)
    extractor.extract_all_data()

    # Create model
    target_model = TargetItemModel(workbook_manager)
    target_model.set_active_sheet("财政局-快报")

    # Check headers
    print(f"\nTotal {len(target_model.headers)} columns in headers:")
    print("="  * 80)

    for i, header in enumerate(target_model.headers):
        # Show repr() to see exact characters
        print(f"[{i}] {repr(header)}")

        # Check if contains '行次'
        if '行次' in header:
            print(f"     ^ Contains '行次' (len={len(header)}, exact_match={header=='行次'})")

            # Show character breakdown
            print(f"     Characters: {[hex(ord(c)) for c in header]}")

    print("\n" + "=" * 80)
    print("Testing exact match")
    print("=" * 80)

    row_num_col = None
    for i, header in enumerate(target_model.headers):
        if header == "行次":
            row_num_col = i
            print(f"✓ EXACT MATCH found at index {i}")
            break

    if row_num_col is None:
        print("✗ NO EXACT MATCH for '行次'")
        print("\nTrying substring match...")
        for i, header in enumerate(target_model.headers):
            if '行次' in header:
                print(f"  Found substring at index {i}: {repr(header)}")

if __name__ == "__main__":
    main()
