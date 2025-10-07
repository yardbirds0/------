# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor

def main():
    print("=" * 80)
    print("分析财政局快报的级别识别问题")
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

    # 查看财政局快报的目标项
    print("\n财政局-快报的前20个项目分析：")
    print("=" * 80)
    print(f"{'行号':<6} {'原始文本':<30} {'原始编号':<10} {'层级':<6} {'最终编号':<10}")
    print("-" * 80)

    targets = [t for t in workbook_manager.target_items.values() if t.sheet_name == "财政局-快报"]
    targets.sort(key=lambda x: x.row)

    for i, item in enumerate(targets[:20]):
        row = item.row
        original = item.original_text[:28] if len(item.original_text) <= 28 else item.original_text[:25] + "..."
        # display_index存储原始编号
        orig_num = item.display_index or ""
        level = item.hierarchical_level
        final_num = item.hierarchical_number

        print(f"{row:<6} {original:<30} {orig_num:<10} {level:<6} {final_num:<10}")

    # 特别关注"税金及附加"
    print("\n" + "=" * 80)
    print("查找'税金及附加'相关项目：")
    print("=" * 80)

    for item in targets:
        if "税金" in item.name or "税金" in item.original_text:
            print(f"\n找到项目：")
            print(f"  行号: {item.row}")
            print(f"  原始文本: '{item.original_text}'")
            print(f"  清理后名称: '{item.name}'")
            print(f"  原始编号: '{item.display_index}'")
            print(f"  层级深度: {item.hierarchical_level}")
            print(f"  最终显示编号: '{item.hierarchical_number}'")
            print(f"  缩进值(level): {item.level}")
            print(f"  父项ID: {item.parent_id}")

if __name__ == "__main__":
    main()
