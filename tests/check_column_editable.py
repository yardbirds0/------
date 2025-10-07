# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor

def main():
    print("=" * 80)
    print("检查财政局快报各列的is_data_column属性")
    print("=" * 80)

    excel_file = "（科电）国资委、财政快报模板-纯净版 的副本.xlsx"
    file_manager = FileManager()
    success, _ = file_manager.load_excel_files([excel_file])

    if not success:
        print("加载失败")
        return

    workbook_manager = file_manager.workbook_manager
    extractor = DataExtractor(workbook_manager)
    extractor.extract_all_data()

    # 检查财政局-快报的列元数据
    sheet_name = "财政局-快报"
    if sheet_name in workbook_manager.target_sheet_columns:
        columns = workbook_manager.target_sheet_columns[sheet_name]

        print(f"\n{sheet_name} 的列信息：")
        print("=" * 80)
        print(f"{'索引':<6} {'列名':<20} {'is_data_column':<15} {'is_numeric':<12} {'data_type':<12}")
        print("-" * 80)

        for i, col in enumerate(columns):
            display_name = col.get('display_name', '')
            is_data = col.get('is_data_column', False)
            is_numeric = col.get('is_numeric', False)
            data_type = col.get('data_type', 'unknown')

            print(f"{i:<6} {display_name:<20} {str(is_data):<15} {str(is_numeric):<12} {data_type:<12}")

        # 特别标记问题列
        print("\n" + "=" * 80)
        print("需要关注的列：")
        for i, col in enumerate(columns):
            display_name = col.get('display_name', '')
            is_data = col.get('is_data_column', False)

            if display_name in ["项目", "行次"]:
                print(f"  [{i}] {display_name}: is_data_column={is_data}")
                if is_data:
                    print(f"      ⚠️ 警告：该列被标记为数据列，但不应该允许编辑！")
    else:
        print(f"未找到 {sheet_name} 的列信息")

if __name__ == "__main__":
    main()
