#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试数据提取的测试脚本
验证data_extractor实际提取了多少数据项
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.data_extractor import DataExtractor
from models.data_models import WorkbookManager
from typing import Dict, List, Any
import json

class DataExtractionDebugger:
    """数据提取调试器"""

    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.workbook_manager = None
        self.extractor = None

    def debug_data_extraction(self):
        """调试数据提取过程"""
        print(f"[DEBUG] 开始调试数据提取过程...")
        print(f"[DEBUG] Excel文件: {self.excel_file_path}")

        # 创建工作簿管理器
        self.workbook_manager = WorkbookManager(self.excel_file_path)

        # 初始化数据源表列表（使用实际存在的工作表名称）
        self.workbook_manager.data_source_sheets = [
            "科目余额表（5月份未审计）",  # 注意：使用全角括号
            "现金流量表",
            "利润表",
            "资产负债表",
            "去年科目余额"
        ]

        # 创建数据提取器
        self.extractor = DataExtractor(self.workbook_manager)

        print(f"\n[DEBUG] ========== 开始数据提取 ==========")

        # 执行数据提取
        success = self.extractor.extract_all_data()

        if not success:
            print(f"[ERROR] 数据提取失败!")
            return

        print(f"\n[DEBUG] ========== 数据提取统计 ==========")

        # 统计提取结果
        total_sources = len(self.workbook_manager.source_items)
        total_targets = len(self.workbook_manager.target_items)

        print(f"[STATS] 总来源项数量: {total_sources}")
        print(f"[STATS] 总目标项数量: {total_targets}")

        # 按sheet分组统计
        sheet_stats = {}
        for source_id, source in self.workbook_manager.source_items.items():
            sheet_name = source.sheet_name
            if sheet_name not in sheet_stats:
                sheet_stats[sheet_name] = 0
            sheet_stats[sheet_name] += 1

        print(f"\n[SHEET_STATS] 按工作表统计:")
        for sheet_name, count in sheet_stats.items():
            print(f"  {sheet_name}: {count} 个项目")

        # 详细分析科目余额表
        self.analyze_trial_balance_sources()

        # 保存调试结果
        self.save_debug_results()

    def analyze_trial_balance_sources(self):
        """详细分析科目余额表的提取结果"""
        print(f"\n[DEBUG] ========== 科目余额表详细分析 ==========")

        trial_balance_sources = []
        for source_id, source in self.workbook_manager.source_items.items():
            if "科目余额表" in source.sheet_name:
                trial_balance_sources.append(source)

        print(f"[ANALYSIS] 科目余额表来源项数量: {len(trial_balance_sources)}")

        if trial_balance_sources:
            print(f"[SAMPLE] 前10个科目余额表项目:")
            for i, source in enumerate(trial_balance_sources[:10]):
                account_code = getattr(source, 'account_code', 'N/A')
                name = getattr(source, 'name', source.text if hasattr(source, 'text') else 'N/A')
                data_columns = getattr(source, 'data_columns', {})
                print(f"  {i+1}. 代码:{account_code} 名称:{name[:30]} 数据列:{len(data_columns)}个")

            # 检查数据列结构
            if trial_balance_sources:
                first_source = trial_balance_sources[0]
                data_columns = getattr(first_source, 'data_columns', {})
                print(f"\n[COLUMNS] 数据列结构 (来自第一个项目):")
                for col_key, col_value in list(data_columns.items())[:10]:
                    print(f"  {col_key}: {col_value}")

    def save_debug_results(self):
        """保存调试结果到文件"""
        debug_data = {
            "extraction_summary": {
                "total_sources": len(self.workbook_manager.source_items),
                "total_targets": len(self.workbook_manager.target_items)
            },
            "sheet_breakdown": {},
            "sample_sources": []
        }

        # 统计各sheet的数量
        for source_id, source in self.workbook_manager.source_items.items():
            sheet_name = source.sheet_name
            if sheet_name not in debug_data["sheet_breakdown"]:
                debug_data["sheet_breakdown"][sheet_name] = 0
            debug_data["sheet_breakdown"][sheet_name] += 1

        # 保存前20个项目作为样本
        for i, (source_id, source) in enumerate(list(self.workbook_manager.source_items.items())[:20]):
            sample = {
                "id": source_id,
                "sheet_name": source.sheet_name,
                "account_code": getattr(source, 'account_code', None),
                "name": getattr(source, 'name', getattr(source, 'text', None)),
                "data_columns_count": len(getattr(source, 'data_columns', {})),
                "data_columns_keys": list(getattr(source, 'data_columns', {}).keys())[:5]  # 只保存前5个键
            }
            debug_data["sample_sources"].append(sample)

        # 保存到文件
        output_file = os.path.join(os.path.dirname(__file__), "data_extraction_debug.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n[SAVE] 调试结果已保存到: {output_file}")

def main():
    """主函数"""
    # 查找Excel文件
    excel_file = None
    current_dir = os.path.dirname(os.path.dirname(__file__))

    # 寻找Excel文件
    for file in os.listdir(current_dir):
        if file.endswith('.xlsx') and '科电' in file:
            excel_file = os.path.join(current_dir, file)
            break

    if not excel_file:
        print("[ERROR] 未找到Excel文件")
        return

    # 创建调试器并运行
    debugger = DataExtractionDebugger(excel_file)
    debugger.debug_data_extraction()

    print(f"\n[DONE] 数据提取调试完成!")

if __name__ == "__main__":
    main()