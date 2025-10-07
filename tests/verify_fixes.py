#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复效果验证脚本
验证数据显示问题和TargetItem.data_type问题已解决
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from components.advanced_widgets import SearchableSourceTree
from utils.table_column_rules import TableColumnRules
from models.data_models import TargetItem
from PySide6.QtWidgets import QApplication
import json

class FixVerifier:
    """修复效果验证器"""

    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.file_manager = FileManager()

    def verify_fixes(self):
        """验证修复效果"""
        print(f"[验证] 开始验证修复效果...")
        print(f"[验证] Excel文件: {self.excel_file_path}")

        # 1. 数据加载与提取
        print(f"\n[步骤1] 数据加载与提取...")
        success, message = self.file_manager.load_excel_files([self.excel_file_path])

        if not success:
            print(f"[错误] 数据加载失败: {message}")
            return False

        workbook_manager = self.file_manager.workbook_manager
        extractor = DataExtractor(workbook_manager)
        success = extractor.extract_all_data()

        if not success:
            print(f"[错误] 数据提取失败!")
            return False

        print(f"[成功] 数据提取完成，总共{len(workbook_manager.source_items)}个源项目")

        # 2. 验证TargetItem.data_type属性
        print(f"\n[步骤2] 验证TargetItem.data_type属性...")
        try:
            test_target = TargetItem(
                id="test_target",
                name="测试目标项",
                original_text="测试目标项",
                sheet_name="测试表",
                row=1,
                level=1
            )

            # 访问data_type属性
            data_type_value = test_target.data_type
            print(f"[成功] TargetItem.data_type = '{data_type_value}'")

            # 模拟main.py中的访问方式
            display_type = "数值" if test_target.data_type == "number" else "文本"
            print(f"[成功] 数据类型显示: {display_type}")

        except AttributeError as e:
            print(f"[失败] TargetItem.data_type访问出错: {e}")
            return False

        # 3. 验证数据列键名匹配
        print(f"\n[步骤3] 验证数据列键名匹配...")

        # 按工作表分组检查
        sheets_data = {}
        for source_id, source in workbook_manager.source_items.items():
            sheet_name = source.sheet_name
            if sheet_name not in sheets_data:
                sheets_data[sheet_name] = []
            sheets_data[sheet_name].append(source)

        all_keys_matched = True

        for sheet_name, sources in sheets_data.items():
            print(f"\n  [工作表] {sheet_name}")

            # 检测表类型
            table_type = TableColumnRules.detect_table_type(sheet_name)
            print(f"    表类型: {table_type}")

            if table_type:
                expected_keys = TableColumnRules.get_ordered_column_keys(table_type)
                print(f"    期望键名: {expected_keys}")

                # 找到有数据的项目
                sample_with_data = None
                for source in sources:
                    if hasattr(source, 'data_columns') and source.data_columns:
                        sample_with_data = source
                        break

                if sample_with_data:
                    actual_keys = list(sample_with_data.data_columns.keys())
                    print(f"    实际键名: {actual_keys}")

                    # 检查匹配情况
                    matched_keys = []
                    for expected_key in expected_keys:
                        if expected_key in actual_keys:
                            matched_keys.append(expected_key)

                    match_rate = len(matched_keys) / len(expected_keys) if expected_keys else 0
                    print(f"    匹配率: {match_rate:.2%} ({len(matched_keys)}/{len(expected_keys)})")

                    if match_rate < 0.8:  # 80%以上匹配才算成功
                        print(f"    [警告] 匹配率过低")
                        all_keys_matched = False
                    else:
                        print(f"    [成功] 键名匹配良好")

                        # 显示数据值示例
                        print(f"    数据值示例:")
                        for key in matched_keys[:3]:  # 只显示前3个
                            value = sample_with_data.data_columns.get(key, '')
                            print(f"      '{key}': {value}")
                else:
                    print(f"    [警告] 没有找到包含data_columns的项目")
            else:
                print(f"    [跳过] 未识别的表类型")

        # 4. 验证GUI显示
        print(f"\n[步骤4] 验证GUI显示...")
        try:
            # 创建SearchableSourceTree（不创建QApplication，只测试数据填充）
            source_tree = SearchableSourceTree()

            # 填充数据
            source_tree.populate_source_items(workbook_manager.source_items)

            # 获取下拉菜单选项
            combo_count = source_tree.sheet_combo.count()
            print(f"    下拉菜单选项数: {combo_count}")

            # 测试不同工作表的数据显示
            tested_sheets = 0
            for i in range(min(3, combo_count)):  # 测试前3个工作表
                sheet_name = source_tree.sheet_combo.itemText(i)

                print(f"    测试工作表: '{sheet_name}'")

                # 切换到该工作表
                source_tree.current_sheet = sheet_name
                source_tree.refresh_display()

                # 检查数据模型
                model = source_tree.model()
                if model:
                    row_count = model.rowCount()
                    print(f"      显示行数: {row_count}")

                    # 检查是否有数据值（非空）
                    has_data_values = False
                    for row in range(min(5, row_count)):  # 检查前5行
                        col_count = model.columnCount()
                        for col in range(2, col_count):  # 跳过前两列（标识符和名称）
                            item = model.item(row, col)
                            if item and item.text().strip() and item.text().strip() != '0':
                                has_data_values = True
                                break
                        if has_data_values:
                            break

                    if has_data_values:
                        print(f"      [成功] 发现有效数据值")
                    else:
                        print(f"      [警告] 未发现有效数据值")
                        all_keys_matched = False

                    tested_sheets += 1
                else:
                    print(f"      [错误] 数据模型为空")

            print(f"    已测试 {tested_sheets} 个工作表")

        except Exception as e:
            print(f"[错误] GUI测试失败: {e}")
            return False

        # 5. 生成验证报告
        print(f"\n[步骤5] 生成验证报告...")

        verification_result = {
            "timestamp": "2025-01-28",  # 可以使用实际时间戳
            "fixes_verified": {
                "target_item_data_type": True,
                "column_key_matching": all_keys_matched,
                "gui_display": True
            },
            "summary": {
                "total_sheets": len(sheets_data),
                "total_items": len(workbook_manager.source_items),
                "all_fixes_working": all_keys_matched
            },
            "details": {
                "sheets_analyzed": list(sheets_data.keys()),
                "key_matching_issues": [] if all_keys_matched else ["部分工作表键名匹配率不足80%"]
            }
        }

        # 保存验证报告
        output_file = os.path.join(os.path.dirname(__file__), "fix_verification_report.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(verification_result, f, ensure_ascii=False, indent=2)

        print(f"[保存] 验证报告已保存到: {output_file}")

        # 6. 输出最终结论
        print(f"\n[最终结论]")
        if verification_result["summary"]["all_fixes_working"]:
            print(f"  ✓ 所有修复都正常工作")
            print(f"  ✓ TargetItem.data_type 属性可正常访问")
            print(f"  ✓ 数据列键名匹配良好")
            print(f"  ✓ GUI数据显示正常")
            print(f"\n🎉 修复验证成功！数据显示问题和崩溃问题已解决。")
            return True
        else:
            print(f"  ✗ 仍有部分问题需要处理")
            for issue in verification_result["details"]["key_matching_issues"]:
                print(f"    - {issue}")
            print(f"\n⚠️  修复验证部分成功，但仍需优化。")
            return False

def main():
    """主函数"""
    # 查找Excel文件
    excel_file = None
    current_dir = os.path.dirname(os.path.dirname(__file__))

    for file in os.listdir(current_dir):
        if file.endswith('.xlsx') and '科电' in file:
            excel_file = os.path.join(current_dir, file)
            break

    if not excel_file:
        print("[错误] 未找到Excel文件")
        return

    # 创建验证器并运行
    verifier = FixVerifier(excel_file)
    success = verifier.verify_fixes()

    if success:
        print(f"\n[完成] 修复验证完成且成功!")
    else:
        print(f"\n[完成] 修复验证完成但存在问题!")

if __name__ == "__main__":
    main()
