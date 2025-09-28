#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI显示验证脚本
模拟实际程序运行时的数据显示情况
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.file_manager import FileManager
from modules.data_extractor import DataExtractor
from components.advanced_widgets import SearchableSourceTree
from PySide6.QtWidgets import QApplication
import json

class GUIDisplayVerifier:
    """GUI显示验证器"""

    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.file_manager = FileManager()
        self.source_tree = None

    def verify_gui_display(self):
        """验证GUI显示情况"""
        print(f"[GUI_VERIFY] 开始验证GUI显示情况...")
        print(f"[GUI_VERIFY] Excel文件: {self.excel_file_path}")

        # 1. 完整数据提取流程
        print(f"\n[STEP 1] 执行完整数据提取流程...")
        success, message = self.file_manager.load_excel_files([self.excel_file_path])

        if not success:
            print(f"[ERROR] 数据加载失败: {message}")
            return

        workbook_manager = self.file_manager.workbook_manager
        extractor = DataExtractor(workbook_manager)
        success = extractor.extract_all_data()

        if not success:
            print(f"[ERROR] 数据提取失败!")
            return

        print(f"[SUCCESS] 数据提取完成，总共{len(workbook_manager.source_items)}个源项目")

        # 2. 创建SearchableSourceTree并填充数据
        print(f"\n[STEP 2] 创建SearchableSourceTree组件...")

        # 注意：这里不创建QApplication，因为这是一个验证脚本
        self.source_tree = SearchableSourceTree()

        # 填充数据
        print(f"[INFO] 填充数据到SearchableSourceTree...")
        self.source_tree.populate_source_items(workbook_manager.source_items)

        # 3. 验证下拉菜单选项
        print(f"\n[STEP 3] 验证下拉菜单选项...")
        combo_items = []
        for i in range(self.source_tree.sheet_combo.count()):
            combo_items.append(self.source_tree.sheet_combo.itemText(i))

        print(f"[COMBO] 下拉菜单选项 ({len(combo_items)} 个):")
        for i, item in enumerate(combo_items):
            print(f"  {i+1:2d}. '{item}'")

        # 4. 验证"全部工作表"模式的显示
        print(f"\n[STEP 4] 验证'全部工作表'模式...")
        self.source_tree.current_sheet = "全部工作表"
        self.source_tree.refresh_display()

        all_mode_model = self.source_tree.model()
        if all_mode_model:
            print(f"[ALL_MODE] 全部工作表模式 - 根节点数量: {all_mode_model.rowCount()}")
            for i in range(all_mode_model.rowCount()):
                root_item = all_mode_model.item(i)
                child_count = root_item.rowCount() if root_item else 0
                print(f"  第{i+1}个根节点: '{root_item.text()}' (子项目: {child_count})")

        # 5. 验证单个工作表模式的显示（重点测试科目余额表）
        print(f"\n[STEP 5] 验证单个工作表模式...")

        trial_balance_sheets = [item for item in combo_items if '科目余额' in item]
        if trial_balance_sheets:
            test_sheet = trial_balance_sheets[0]
            print(f"[SINGLE_MODE] 测试工作表: '{test_sheet}'")

            # 切换到单个工作表
            self.source_tree.current_sheet = test_sheet
            self.source_tree.refresh_display()

            single_mode_model = self.source_tree.model()
            if single_mode_model:
                row_count = single_mode_model.rowCount()
                print(f"[SINGLE_MODE] 单工作表模式 - 直接显示项目数量: {row_count}")

                # 显示前10个项目的详细信息
                print(f"[SAMPLE] 前10个项目:")
                for i in range(min(10, row_count)):
                    item = single_mode_model.item(i, 0)  # 第一列（名称列）
                    if item:
                        user_data = item.data(0x0100)  # Qt.UserRole
                        account_code = getattr(user_data, 'account_code', 'N/A') if user_data else 'N/A'
                        print(f"  {i+1:2d}. {item.text()[:50]:<50} (代码: {account_code})")

                # 检查是否有大量数据被隐藏
                if row_count < 100:
                    print(f"[WARNING] 显示项目数({row_count})少于预期(应该有580个)")
                else:
                    print(f"[SUCCESS] 显示项目数正常({row_count}个)")

        # 6. 保存验证结果
        self.save_verification_results(workbook_manager, combo_items, trial_balance_sheets)

    def save_verification_results(self, workbook_manager, combo_items, trial_balance_sheets):
        """保存验证结果"""
        verification_data = {
            "verification_summary": {
                "total_source_items": len(workbook_manager.source_items),
                "combo_items_count": len(combo_items),
                "trial_balance_sheets_count": len(trial_balance_sheets)
            },
            "combo_items": combo_items,
            "trial_balance_sheets": trial_balance_sheets,
            "sheet_item_counts": {}
        }

        # 统计每个工作表的项目数
        for source_id, source in workbook_manager.source_items.items():
            sheet_name = source.sheet_name
            if sheet_name not in verification_data["sheet_item_counts"]:
                verification_data["sheet_item_counts"][sheet_name] = 0
            verification_data["sheet_item_counts"][sheet_name] += 1

        # 保存到文件
        output_file = os.path.join(os.path.dirname(__file__), "gui_display_verification.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(verification_data, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVE] GUI显示验证结果已保存到: {output_file}")

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

    # 创建验证器并运行（不需要QApplication）
    verifier = GUIDisplayVerifier(excel_file)
    verifier.verify_gui_display()

    print(f"\n[DONE] GUI显示验证完成!")

if __name__ == "__main__":
    main()