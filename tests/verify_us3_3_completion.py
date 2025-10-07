# -*- coding: utf-8 -*-
"""
US-3.3 完成情况验证
验证目标表项目提取的所有功能点
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from models.data_models import TargetItem

def verify_us3_3():
    """验证US-3.3所有功能点"""

    print("="*80)
    print("US-3.3 目标表项目提取 - 完成情况验证")
    print("="*80)

    # 测试文件路径 - 使用包含快报表的文件
    # 如果文件路径有问题,尝试手动分类一个sheet为快报表
    excel_file = r"D:\Code\快报填写程序\sample.xlsx"

    # 标记:需要手动将某个sheet分类为快报表才能测试
    manual_classification_needed = True

    if not os.path.exists(excel_file):
        print(f"\n[错误] 测试文件不存在: {excel_file}")
        return False

    # 加载数据
    print(f"\n[步骤1] 加载Excel文件...")
    print(f"文件: {excel_file}")

    file_manager = FileManager()
    success, message = file_manager.load_excel_files([excel_file])

    if not success:
        print(f"[失败] 文件加载失败: {message}")
        return False

    print(f"[成功] 文件加载完成")

    workbook_manager = file_manager.workbook_manager

    # 手动调整分类 - 将第一个工作表分类为快报表用于测试
    if manual_classification_needed and workbook_manager.worksheets:
        test_sheet_name = list(workbook_manager.worksheets.keys())[0]
        print(f"\n[手动调整] 将工作表 '{test_sheet_name}' 分类为快报表用于测试...")

        adjustments = {test_sheet_name: 'flash_report'}
        file_manager.adjust_classification_manual(adjustments)
        print(f"[成功] 分类调整完成")

    # 提取数据
    print(f"\n[步骤2] 提取目标表项目...")

    extractor = DataExtractor(workbook_manager)
    success = extractor.extract_all_data()

    if not success:
        print(f"[失败] 数据提取失败")
        return False

    target_count = len(workbook_manager.target_items)
    print(f"[成功] 提取到 {target_count} 个目标项")

    if target_count == 0:
        print("[警告] 未提取到任何目标项")
        return False

    # 验证功能点
    print(f"\n" + "="*80)
    print("功能点验证")
    print("="*80)

    # 选择第一个目标项进行详细检查
    sample_target = next(iter(workbook_manager.target_items.values()))

    # ===== 功能点1: 遍历目标表 =====
    print(f"\n[功能点1] 遍历所有已确认为'目标表'的工作表")
    flash_report_count = len(workbook_manager.flash_report_sheets)
    print(f"  快报表数量: {flash_report_count}")
    print(f"  快报表列表: {[sheet.get('name', str(sheet)) for sheet in workbook_manager.flash_report_sheets[:3]]}")
    print(f"  [{'通过' if flash_report_count > 0 else '失败'}]")

    # ===== 功能点2: 解析A列序号、B列项目名称、D列数值单元格 =====
    print(f"\n[功能点2] 解析A列序号、B列项目名称、D列待填写数值单元格")
    print(f"  示例项目:")
    print(f"    - 项目名称 (B列): '{sample_target.name}'")
    print(f"    - 原始文本: '{sample_target.original_text}'")
    print(f"    - 序号 (A列): '{sample_target.display_index}'")
    print(f"    - 目标单元格 (D列): '{sample_target.target_cell_address}'")
    print(f"    - 所在行号: {sample_target.row}")

    has_name = bool(sample_target.name)
    has_target_cell = bool(sample_target.target_cell_address)
    print(f"  [{'通过' if (has_name and has_target_cell) else '失败'}]")

    # ===== 功能点3: 层级关系识别 (通过前置缩进/空格数) =====
    print(f"\n[功能点3] 识别项目层级关系(通过B列前置缩进)")
    print(f"  验证层级字段...")

    # 查找有不同层级的项目
    levels_found = {}
    for target in list(workbook_manager.target_items.values())[:10]:
        level = target.level
        if level not in levels_found:
            levels_found[level] = target

    print(f"  发现的层级值: {sorted(levels_found.keys())}")

    for level, target in sorted(levels_found.items())[:5]:
        indent_display = "  " * (level // 2) if level > 0 else ""
        print(f"    层级{level}: {indent_display}'{target.name}' (hierarchical_level={target.hierarchical_level})")

    has_hierarchy = len(levels_found) > 1
    print(f"  [{'通过' if has_hierarchy else '失败'}]")

    # 检查父子关系
    print(f"\n  验证父子关系...")
    targets_with_parent = [t for t in workbook_manager.target_items.values() if t.parent_id]
    targets_with_children = [t for t in workbook_manager.target_items.values() if t.children_ids]

    print(f"    有父项的目标项: {len(targets_with_parent)}")
    print(f"    有子项的目标项: {len(targets_with_children)}")

    if targets_with_children:
        sample_parent = targets_with_children[0]
        print(f"    示例父项: '{sample_parent.name}'")
        print(f"      子项ID列表: {sample_parent.children_ids[:3]}")

    has_relationships = len(targets_with_parent) > 0 or len(targets_with_children) > 0
    print(f"  [{'通过' if has_relationships else '失败'}]")

    # ===== 功能点4: 结构化存储 =====
    print(f"\n[功能点4] 结构化存储为包含必需字段的对象")
    print(f"  检查必需字段...")

    required_fields = {
        'id': sample_target.id,
        'sheet_name': sample_target.sheet_name,
        'item_name': sample_target.name,
        'item_index': sample_target.display_index,
        'level': sample_target.level,
        'target_cell': sample_target.target_cell_address,
    }

    all_fields_present = True
    for field_name, field_value in required_fields.items():
        has_value = field_value is not None and str(field_value).strip() != ""
        status = "✓" if has_value else "✗"
        print(f"    {status} {field_name}: {repr(field_value)[:50]}")
        if not has_value and field_name not in ['item_index']:  # item_index可以为空
            all_fields_present = False

    # 检查formula和calculated_value (通过MappingFormula)
    print(f"\n  检查formula和calculated_value字段...")
    print(f"    (这些字段存储在MappingFormula对象中,通过target_id关联)")

    formula_count = len(workbook_manager.mapping_formulas)
    print(f"    当前映射公式数量: {formula_count}")

    if formula_count > 0:
        sample_formula = next(iter(workbook_manager.mapping_formulas.values()))
        print(f"    示例公式:")
        print(f"      target_id: {sample_formula.target_id}")
        print(f"      formula: {sample_formula.formula[:50] if sample_formula.formula else 'None'}")
        print(f"      calculation_result: {sample_formula.calculation_result}")

    print(f"  [{'通过' if all_fields_present else '失败'}]")

    # ===== 总体评估 =====
    print(f"\n" + "="*80)
    print("总体评估")
    print("="*80)

    checks = {
        '功能点1: 遍历目标表': flash_report_count > 0,
        '功能点2: 解析A/B/D列': has_name and has_target_cell,
        '功能点3: 层级关系识别': has_hierarchy and has_relationships,
        '功能点4: 结构化存储': all_fields_present,
    }

    for check_name, passed in checks.items():
        status = "[✓ 通过]" if passed else "[✗ 失败]"
        print(f"  {status} {check_name}")

    all_passed = all(checks.values())

    print(f"\n" + "="*80)
    if all_passed:
        print("结论: US-3.3 所有功能点已完整实现并通过验证")
    else:
        print("结论: US-3.3 部分功能点需要改进")
    print("="*80)

    return all_passed


if __name__ == '__main__':
    try:
        result = verify_us3_3()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n[异常] 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
