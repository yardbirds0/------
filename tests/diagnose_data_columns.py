#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据列诊断脚本
检查data_columns键名与TableColumnRules定义的标准键名是否匹配
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from utils.table_column_rules import TableColumnRules
import json

class DataColumnsDiagnostic:
    """数据列诊断器"""

    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.file_manager = FileManager()

    def diagnose(self):
        """执行诊断"""
        print(f"[诊断] 开始诊断数据列键名匹配问题...")
        print(f"[诊断] Excel文件: {self.excel_file_path}")

        # 1. 加载和提取数据
        print(f"\n[步骤1] 数据加载与提取...")
        success, message = self.file_manager.load_excel_files([self.excel_file_path])

        if not success:
            print(f"[错误] 数据加载失败: {message}")
            return

        workbook_manager = self.file_manager.workbook_manager
        extractor = DataExtractor(workbook_manager)
        success = extractor.extract_all_data()

        if not success:
            print(f"[错误] 数据提取失败!")
            return

        print(f"[成功] 数据提取完成，总共{len(workbook_manager.source_items)}个源项目")

        # 2. 分析不同工作表的数据列
        print(f"\n[步骤2] 分析各工作表的数据列...")

        # 按工作表分组
        sheets_data = {}
        for source_id, source in workbook_manager.source_items.items():
            sheet_name = source.sheet_name
            if sheet_name not in sheets_data:
                sheets_data[sheet_name] = []
            sheets_data[sheet_name].append(source)

        # 分析每个工作表
        for sheet_name, sources in sheets_data.items():
            print(f"\n[工作表] {sheet_name}")
            print(f"  项目数量: {len(sources)}")

            # 检测表类型
            table_type = TableColumnRules.detect_table_type(sheet_name)
            print(f"  检测到的表类型: {table_type}")

            if table_type:
                # 获取标准列键
                expected_keys = TableColumnRules.get_ordered_column_keys(table_type)
                print(f"  期望的列键: {expected_keys}")

                # 检查实际数据列
                sample_source = None
                for source in sources:
                    if hasattr(source, 'data_columns') and source.data_columns:
                        sample_source = source
                        break

                if sample_source:
                    actual_keys = list(sample_source.data_columns.keys())
                    print(f"  实际的列键: {actual_keys}")

                    # 对比分析
                    missing_keys = set(expected_keys) - set(actual_keys)
                    extra_keys = set(actual_keys) - set(expected_keys)

                    if missing_keys:
                        print(f"  缺失的键: {list(missing_keys)}")
                    if extra_keys:
                        print(f"  多余的键: {list(extra_keys)}")

                    # 数据值示例
                    print(f"  数据值示例:")
                    for key, value in sample_source.data_columns.items():
                        print(f"    '{key}': {value}")

                    # 检查键名匹配情况
                    print(f"  键名匹配情况:")
                    for expected_key in expected_keys:
                        if expected_key in actual_keys:
                            print(f"    ✓ '{expected_key}' 匹配")
                        else:
                            print(f"    ✗ '{expected_key}' 缺失")
                else:
                    print(f"  [警告] 没有找到包含data_columns的项目")
            else:
                print(f"  [警告] 未识别的表类型")

                # 显示第一个有数据的项目的键
                sample_source = None
                for source in sources:
                    if hasattr(source, 'data_columns') and source.data_columns:
                        sample_source = source
                        break

                if sample_source:
                    actual_keys = list(sample_source.data_columns.keys())
                    print(f"  实际的列键: {actual_keys}")

        # 3. 生成诊断报告
        print(f"\n[步骤3] 生成诊断报告...")

        diagnostic_result = {
            "summary": {
                "total_sheets": len(sheets_data),
                "total_items": len(workbook_manager.source_items),
                "recognized_table_types": []
            },
            "sheets_analysis": {}
        }

        for sheet_name, sources in sheets_data.items():
            table_type = TableColumnRules.detect_table_type(sheet_name)
            analysis = {
                "sheet_name": sheet_name,
                "table_type": table_type,
                "items_count": len(sources),
                "has_data_columns": False,
                "actual_keys": [],
                "expected_keys": [],
                "key_match_status": {}
            }

            if table_type:
                diagnostic_result["summary"]["recognized_table_types"].append(table_type)
                analysis["expected_keys"] = TableColumnRules.get_ordered_column_keys(table_type)

            # 获取实际键名
            for source in sources:
                if hasattr(source, 'data_columns') and source.data_columns:
                    analysis["has_data_columns"] = True
                    analysis["actual_keys"] = list(source.data_columns.keys())
                    break

            # 分析键名匹配
            if analysis["expected_keys"] and analysis["actual_keys"]:
                for expected_key in analysis["expected_keys"]:
                    analysis["key_match_status"][expected_key] = expected_key in analysis["actual_keys"]

            diagnostic_result["sheets_analysis"][sheet_name] = analysis

        # 保存诊断报告
        output_file = os.path.join(os.path.dirname(__file__), "data_columns_diagnostic.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(diagnostic_result, f, ensure_ascii=False, indent=2)

        print(f"\n[完成] 诊断报告已保存到: {output_file}")

        # 输出总结
        print(f"\n[总结]")
        print(f"  - 共分析 {len(sheets_data)} 个工作表")
        print(f"  - 识别出的表类型: {diagnostic_result['summary']['recognized_table_types']}")

        has_mismatch = False
        for sheet_name, analysis in diagnostic_result["sheets_analysis"].items():
            if analysis["key_match_status"]:
                mismatch_count = sum(1 for matched in analysis["key_match_status"].values() if not matched)
                if mismatch_count > 0:
                    print(f"  - {sheet_name}: {mismatch_count} 个键名不匹配")
                    has_mismatch = True

        if has_mismatch:
            print(f"  [结论] 确认存在键名不匹配问题，需要修复_generate_column_key方法")
        else:
            print(f"  [结论] 键名匹配正常，问题可能在其他地方")

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

    # 创建诊断器并运行
    diagnostic = DataColumnsDiagnostic(excel_file)
    diagnostic.diagnose()

    print(f"\n[完成] 数据列诊断完成!")

if __name__ == "__main__":
    main()