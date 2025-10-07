#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 - 企业财务快报利润因素分析表的级别识别
"""

import sys
import os
import io

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from models.data_models import generate_hierarchical_numbers

def debug_profit_analysis_levels():
    """调试利润因素分析表的级别识别"""

    print("=" * 80)
    print("企业财务快报利润因素分析表 - 级别识别调试")
    print("=" * 80)

    # 1. 加载文件
    excel_path = r"d:\Code\快报填写程序\（科电）国资委、财政快报模板-纯净版 的副本.xlsx"
    print(f"\n加载文件: {os.path.basename(excel_path)}")

    # 设置UTF-8输出
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    fm = FileManager()
    success, error_msg = fm.load_excel_files([excel_path])

    if not success:
        print(f"加载失败: {error_msg}")
        return

    workbook_manager = fm.workbook_manager
    if not workbook_manager:
        print("WorkbookManager未初始化")
        return

    # 2. 提取数据
    print("\n提取数据...")
    extractor = DataExtractor(workbook_manager)
    extractor.extract_all_data()

    # 3. 生成层级编号
    all_target_items = list(workbook_manager.target_items.values())
    generate_hierarchical_numbers(all_target_items)

    # 4. 查找"企业财务快报利润因素分析表"的所有项目
    target_sheet = "企业财务快报利润因素分析表"
    sheet_items = []

    for tid, item in workbook_manager.target_items.items():
        if item.sheet_name == target_sheet:
            sheet_items.append(item)

    # 按行号排序
    sheet_items.sort(key=lambda x: x.row)

    print(f"\n找到 {len(sheet_items)} 个目标项")

    # 5. 显示前20行的详细信息
    print("\n" + "=" * 80)
    print("前20行项目详细信息")
    print("=" * 80)
    print(f"{'序号':<5} {'原始编号':<15} {'项目名称':<40} {'层级':<5} {'识别结果':<10}")
    print("-" * 80)

    for idx, item in enumerate(sheet_items[:20], 1):
        original_num = item.display_index or "(无)"
        indent_marker = ""
        if item.original_text:
            leading_spaces = len(item.original_text) - len(item.original_text.lstrip())
            if leading_spaces > 0:
                indent_marker = f"[缩进{leading_spaces}]"

        marker = ""
        # 标记问题项
        if "2.销售价格" in item.name:
            marker = ">>> 问题1: 应该是2.2"
        elif "原材料成本" in item.name:
            marker = ">>> 问题2: 应该是3.1"

        print(f"{idx:<5} {original_num:<15} {item.name:<40} {item.hierarchical_level:<5} {item.hierarchical_number:<10} {indent_marker} {marker}")

    # 6. 分析关键项目
    print("\n" + "=" * 80)
    print("关键项目分析")
    print("=" * 80)

    key_items = [
        "利润增加因素合计",
        "1.销售数量同比上升增加利润",
        "2.销售价格同比上升增加利润",
        "3.销售成本同比上升减少利润",
        "原材料成本同比上升减少利润"
    ]

    for key_name in key_items:
        for item in sheet_items:
            if key_name in item.name:
                print(f"\n项目: {item.name}")
                print(f"  原始文本: {repr(item.original_text)}")
                print(f"  原始编号: {repr(item.display_index)}")
                print(f"  缩进值(level): {item.level}")
                print(f"  层级(hierarchical_level): {item.hierarchical_level}")
                print(f"  显示编号: {item.hierarchical_number}")
                print(f"  行号: {item.row}")
                break

    print("\n" + "=" * 80)
    print("分析结论")
    print("=" * 80)
    print("""
问题1: "2.销售价格同比上升增加利润"
  - 前面有"其中:1.销售数量..."被识别为2.1
  - 当前项"2.销售价格..."应该识别为2.2，而不是3
  - 需要识别"连续编号"模式(1., 2., 3.等)

问题2: "原材料成本同比上升减少利润"
  - 前面项"3.销售成本..."被识别为3
  - 当前项"其中:原材料成本..."应该是3.1，不应该跳到3.1.1
  - 需要防止级别跳跃
    """)

if __name__ == "__main__":
    debug_profit_analysis_levels()
