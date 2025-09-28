#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试FileManager的工作表分类逻辑
验证科目余额表为什么没有被分类为数据来源表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
import json

class FileManagerDebugger:
    """FileManager分类逻辑调试器"""

    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.file_manager = FileManager()

    def debug_classification(self):
        """调试分类逻辑"""
        print(f"[DEBUG] 开始调试FileManager分类逻辑...")
        print(f"[DEBUG] Excel文件: {self.excel_file_path}")

        # 加载Excel文件
        success, message = self.file_manager.load_excel_files([self.excel_file_path])

        if not success:
            print(f"[ERROR] 加载文件失败: {message}")
            return

        print(f"\n[DEBUG] ========== 工作表分类结果 ==========")

        workbook_manager = self.file_manager.workbook_manager

        print(f"[STATS] 总工作表数: {len(workbook_manager.worksheets)}")
        print(f"[STATS] 快报表数: {len(workbook_manager.flash_report_sheets)}")
        print(f"[STATS] 数据来源表数: {len(workbook_manager.data_source_sheets)}")

        print(f"\n[FLASH_REPORTS] 快报表列表:")
        for i, sheet_name in enumerate(workbook_manager.flash_report_sheets):
            print(f"  {i+1}. '{sheet_name}'")

        print(f"\n[DATA_SOURCES] 数据来源表列表:")
        for i, sheet_name in enumerate(workbook_manager.data_source_sheets):
            print(f"  {i+1}. '{sheet_name}'")

        print(f"\n[ALL_SHEETS] 所有工作表及其分类:")
        for sheet_name, sheet_info in workbook_manager.worksheets.items():
            sheet_type = getattr(sheet_info, 'sheet_type', 'UNKNOWN')
            is_flash = self.file_manager._is_flash_report_sheet(sheet_name)
            print(f"  '{sheet_name}' -> {sheet_type} (is_flash: {is_flash})")

        # 重点分析科目余额表
        print(f"\n[TRIAL_BALANCE] 科目余额表分析:")
        trial_balance_sheets = []
        for sheet_name in workbook_manager.worksheets.keys():
            if '科目余额' in sheet_name or '余额表' in sheet_name:
                trial_balance_sheets.append(sheet_name)
                is_flash = self.file_manager._is_flash_report_sheet(sheet_name)
                sheet_info = workbook_manager.worksheets[sheet_name]
                sheet_type = getattr(sheet_info, 'sheet_type', 'UNKNOWN')

                in_flash_list = sheet_name in workbook_manager.flash_report_sheets
                in_data_list = sheet_name in workbook_manager.data_source_sheets

                print(f"  科目余额表: '{sheet_name}'")
                print(f"    分类结果: {sheet_type}")
                print(f"    is_flash_report: {is_flash}")
                print(f"    在快报表列表中: {in_flash_list}")
                print(f"    在数据来源表列表中: {in_data_list}")

        # 保存调试结果
        self.save_debug_results(workbook_manager, trial_balance_sheets)

    def save_debug_results(self, workbook_manager, trial_balance_sheets):
        """保存调试结果"""
        debug_data = {
            "total_sheets": len(workbook_manager.worksheets),
            "flash_report_count": len(workbook_manager.flash_report_sheets),
            "data_source_count": len(workbook_manager.data_source_sheets),
            "flash_report_sheets": workbook_manager.flash_report_sheets,
            "data_source_sheets": workbook_manager.data_source_sheets,
            "trial_balance_sheets_found": trial_balance_sheets,
            "all_sheets_classification": {}
        }

        for sheet_name, sheet_info in workbook_manager.worksheets.items():
            debug_data["all_sheets_classification"][sheet_name] = {
                "sheet_type": str(getattr(sheet_info, 'sheet_type', 'UNKNOWN')),
                "is_flash_report": self.file_manager._is_flash_report_sheet(sheet_name),
                "in_flash_list": sheet_name in workbook_manager.flash_report_sheets,
                "in_data_list": sheet_name in workbook_manager.data_source_sheets
            }

        output_file = os.path.join(os.path.dirname(__file__), "file_manager_classification_debug.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n[SAVE] 分类调试结果已保存到: {output_file}")

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
        print("[ERROR] 未找到Excel文件")
        return

    # 创建调试器并运行
    debugger = FileManagerDebugger(excel_file)
    debugger.debug_classification()

    print(f"\n[DONE] FileManager分类调试完成!")

if __name__ == "__main__":
    main()