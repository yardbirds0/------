#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用完整FileManager工作流程的数据提取调试
验证完整的数据提取流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from typing import Dict, List, Any
import json

class FullWorkflowDebugger:
    """完整工作流程调试器"""

    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.file_manager = FileManager()
        self.extractor = None

    def debug_full_workflow(self):
        """调试完整的数据提取工作流程"""
        print(f"[DEBUG] 开始调试完整工作流程...")
        print(f"[DEBUG] Excel文件: {self.excel_file_path}")

        # 1. 使用FileManager加载文件（完整工作流程）
        print(f"\n[STEP 1] 使用FileManager加载Excel文件...")
        success, message = self.file_manager.load_excel_files([self.excel_file_path])

        if not success:
            print(f"[ERROR] FileManager加载失败: {message}")
            return

        workbook_manager = self.file_manager.workbook_manager
        print(f"[SUCCESS] FileManager加载成功")
        print(f"  快报表数量: {len(workbook_manager.flash_report_sheets)}")
        print(f"  数据来源表数量: {len(workbook_manager.data_source_sheets)}")

        # 2. 使用DataExtractor提取数据
        print(f"\n[STEP 2] 使用DataExtractor提取数据...")
        self.extractor = DataExtractor(workbook_manager)

        print(f"  开始数据提取...")
        success = self.extractor.extract_all_data()

        if not success:
            print(f"[ERROR] 数据提取失败!")
            return

        print(f"[SUCCESS] 数据提取成功")

        # 3. 分析提取结果
        print(f"\n[STEP 3] 分析提取结果...")
        total_sources = len(workbook_manager.source_items)
        total_targets = len(workbook_manager.target_items)

        print(f"  总来源项数量: {total_sources}")
        print(f"  总目标项数量: {total_targets}")

        # 按sheet分组统计
        sheet_stats = {}
        for source_id, source in workbook_manager.source_items.items():
            sheet_name = source.sheet_name
            if sheet_name not in sheet_stats:
                sheet_stats[sheet_name] = 0
            sheet_stats[sheet_name] += 1

        print(f"\n[SHEET_STATS] 按工作表统计:")
        for sheet_name, count in sheet_stats.items():
            print(f"  {sheet_name}: {count} 个项目")

        # 4. 详细分析科目余额表
        self.analyze_trial_balance_extraction(workbook_manager)

        # 5. 保存调试结果
        self.save_debug_results(workbook_manager, sheet_stats)

    def analyze_trial_balance_extraction(self, workbook_manager):
        """详细分析科目余额表的提取结果"""
        print(f"\n[TRIAL_BALANCE] 科目余额表详细分析:")

        # 找到科目余额表相关的数据来源表
        trial_balance_sheets = []
        for sheet_name in workbook_manager.data_source_sheets:
            if '科目余额' in sheet_name or '余额表' in sheet_name:
                trial_balance_sheets.append(sheet_name)

        print(f"  发现的科目余额表: {len(trial_balance_sheets)} 个")
        for sheet_name in trial_balance_sheets:
            print(f"    - '{sheet_name}'")

        # 统计来自科目余额表的源项目
        trial_balance_sources = []
        for source_id, source in workbook_manager.source_items.items():
            if any(tb_sheet in source.sheet_name for tb_sheet in trial_balance_sheets):
                trial_balance_sources.append(source)

        print(f"  科目余额表来源项数量: {len(trial_balance_sources)}")

        if trial_balance_sources:
            print(f"  [SAMPLE] 前10个科目余额表项目:")
            for i, source in enumerate(trial_balance_sources[:10]):
                account_code = getattr(source, 'account_code', 'N/A')
                name = getattr(source, 'name', source.text if hasattr(source, 'text') else 'N/A')
                data_columns = getattr(source, 'data_columns', {})
                print(f"    {i+1:2d}. 代码:{account_code} 名称:{name[:30]:<30} 数据列:{len(data_columns)}个")

            # 分析数据列结构
            first_source = trial_balance_sources[0]
            data_columns = getattr(first_source, 'data_columns', {})
            print(f"\n  [COLUMNS] 数据列结构示例 (来自第一个项目):")
            for col_key, col_value in list(data_columns.items())[:10]:
                print(f"    {col_key}: {col_value}")
        else:
            print(f"  [WARNING] 没有找到科目余额表的来源项!")

            # 如果没有找到，检查是否有相关的工作表被处理过
            print(f"  [DEBUG] 检查数据提取过程中的工作表处理:")
            for sheet_name in workbook_manager.data_source_sheets:
                if '科目余额' in sheet_name or '余额表' in sheet_name:
                    print(f"    工作表 '{sheet_name}' 应该被处理但没有生成源项目")

    def save_debug_results(self, workbook_manager, sheet_stats):
        """保存调试结果"""
        debug_data = {
            "extraction_summary": {
                "total_sources": len(workbook_manager.source_items),
                "total_targets": len(workbook_manager.target_items),
                "data_source_sheets_count": len(workbook_manager.data_source_sheets),
                "flash_report_sheets_count": len(workbook_manager.flash_report_sheets)
            },
            "data_source_sheets": workbook_manager.data_source_sheets,
            "flash_report_sheets": workbook_manager.flash_report_sheets,
            "sheet_breakdown": sheet_stats,
            "sample_sources": []
        }

        # 保存前20个项目作为样本
        for i, (source_id, source) in enumerate(list(workbook_manager.source_items.items())[:20]):
            sample = {
                "id": source_id,
                "sheet_name": source.sheet_name,
                "account_code": getattr(source, 'account_code', None),
                "name": getattr(source, 'name', getattr(source, 'text', None)),
                "data_columns_count": len(getattr(source, 'data_columns', {})),
                "data_columns_keys": list(getattr(source, 'data_columns', {}).keys())[:5]
            }
            debug_data["sample_sources"].append(sample)

        # 保存到文件
        output_file = os.path.join(os.path.dirname(__file__), "full_workflow_debug.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n[SAVE] 完整工作流程调试结果已保存到: {output_file}")

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
    debugger = FullWorkflowDebugger(excel_file)
    debugger.debug_full_workflow()

    print(f"\n[DONE] 完整工作流程调试完成!")

if __name__ == "__main__":
    main()