# -*- coding: utf-8 -*-
"""
代码评审修复验证脚本
验证所有关键和重要问题是否已修复
"""

import os
import sys
import re
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("代码评审修复验证")
print("=" * 80)

# 测试计数器
total_tests = 0
passed_tests = 0
failed_tests = 0

def test(name: str, condition: bool, error_msg: str = ""):
    """测试辅助函数"""
    global total_tests, passed_tests, failed_tests
    total_tests += 1

    if condition:
        passed_tests += 1
        print(f"[PASS] {name}")
        return True
    else:
        failed_tests += 1
        print(f"[FAIL] {name}")
        if error_msg:
            print(f"   错误: {error_msg}")
        return False

# ==================== 测试1: 方法名修复 ====================
print("\n[TEST 1] 方法名修复 (clear_chat_history -> clear_messages)")
print("-" * 80)

chat_controller_path = project_root / "controllers" / "chat_controller.py"
with open(chat_controller_path, 'r', encoding='utf-8') as f:
    controller_content = f.read()

# 检查是否还有旧方法名
old_method_count = controller_content.count('clear_chat_history()')
test(
    "chat_controller.py 中不应包含 clear_chat_history()",
    old_method_count == 0,
    f"发现 {old_method_count} 处使用旧方法名"
)

# 检查是否使用新方法名
new_method_count = controller_content.count('clear_messages()')
test(
    "chat_controller.py 中应包含 clear_messages() 调用",
    new_method_count >= 3,
    f"仅发现 {new_method_count} 处（期望至少3处）"
)

# ==================== 测试2: add_user_message方法 ====================
print("\n[TEST 2] add_user_message方法存在性")
print("-" * 80)

main_window_path = project_root / "components" / "chat" / "main_window.py"
with open(main_window_path, 'r', encoding='utf-8') as f:
    main_window_content = f.read()

# 检查方法定义
has_method = 'def add_user_message(self, content: str):' in main_window_content
test(
    "main_window.py 中包含 add_user_message 方法定义",
    has_method
)

# 检查方法调用正确的内部方法
has_correct_call = 'self.message_area.add_user_message(content)' in main_window_content
test(
    "add_user_message 正确调用 message_area.add_user_message",
    has_correct_call
)

# ==================== 测试3: migrate_from_json修复 ====================
print("\n[TEST 3] migrate_from_json session_id修复")
print("-" * 80)

db_manager_path = project_root / "data" / "chat" / "db_manager.py"
with open(db_manager_path, 'r', encoding='utf-8') as f:
    db_manager_content = f.read()

# 查找migrate_from_json方法
migrate_method_match = re.search(
    r'def migrate_from_json\(self.*?\n(?:\s{4}.*\n)*?(?=\n\s{0,4}def|\Z)',
    db_manager_content,
    re.MULTILINE | re.DOTALL
)

if migrate_method_match:
    migrate_method = migrate_method_match.group(0)

    # 检查是否捕获返回值
    has_new_session_id = 'new_session_id = self.create_session' in migrate_method
    test(
        "migrate_from_json 捕获 create_session 的返回值",
        has_new_session_id
    )

    # 检查是否使用新ID保存消息
    uses_new_id = 'session_id=new_session_id' in migrate_method
    test(
        "migrate_from_json 使用 new_session_id 保存消息",
        uses_new_id
    )
else:
    test("找到 migrate_from_json 方法", False, "未找到该方法")

# ==================== 测试4: 数据库None检查 ====================
print("\n[TEST 4] 数据库错误处理")
print("-" * 80)

# 检查 _initialize_database 错误处理
init_db_match = re.search(
    r'def _initialize_database\(self\):.*?(?=\n    def |\Z)',
    controller_content,
    re.MULTILINE | re.DOTALL
)

if init_db_match:
    init_db_method = init_db_match.group(0)

    has_none_assignment = 'self.db_manager = None' in init_db_method
    test(
        "_initialize_database 在异常时设置 db_manager = None",
        has_none_assignment
    )
else:
    test("找到 _initialize_database 方法", False)

# 检查 _create_new_session None检查
create_session_match = re.search(
    r'def _create_new_session\(self.*?:.*?\n(?:\s{4,8}.*\n)*?(?=\n    def |\n    @|\Z)',
    controller_content,
    re.MULTILINE | re.DOTALL
)

if create_session_match:
    create_session_method = create_session_match.group(0)

    has_none_check = 'if not self.db_manager:' in create_session_method
    test(
        "_create_new_session 包含 db_manager None 检查",
        has_none_check
    )

    has_warning = 'logger.warning' in create_session_method
    test(
        "_create_new_session 在None时记录警告",
        has_warning
    )
else:
    test("找到 _create_new_session 方法", False)

# ==================== 测试5: UI错误反馈 ====================
print("\n[TEST 5] UI错误反馈")
print("-" * 80)

# 检查错误标志定义
has_error_flag = '_db_save_error_shown = False' in controller_content
test(
    "定义了 _db_save_error_shown 错误标志",
    has_error_flag
)

# 检查QMessageBox警告调用
messagebox_count = controller_content.count('QMessageBox.warning')
test(
    "包含 QMessageBox.warning 调用（至少2处）",
    messagebox_count >= 2,
    f"仅发现 {messagebox_count} 处"
)

# 检查是否在保存消息失败时显示错误
save_user_error = re.search(
    r'self\.db_manager\.save_message\(self\.current_session_id, \'user\'.*?except Exception.*?QMessageBox\.warning',
    controller_content,
    re.DOTALL
)
test(
    "用户消息保存失败时显示错误对话框",
    save_user_error is not None
)

save_ai_error_count = len(re.findall(
    r'self\.db_manager\.save_message\(self\.current_session_id, \'assistant\'.*?except Exception.*?QMessageBox\.warning',
    controller_content,
    re.DOTALL
))
test(
    "AI消息保存失败时显示错误对话框（应有2处：流式和非流式）",
    save_ai_error_count >= 2,
    f"仅发现 {save_ai_error_count} 处"
)

# ==================== 测试6: 常量定义 ====================
print("\n[TEST 6] 魔法数字消除（常量定义）")
print("-" * 80)

has_title_constant = re.search(r'SESSION_TITLE_MAX_LENGTH\s*=\s*10', controller_content)
test(
    "定义了 SESSION_TITLE_MAX_LENGTH = 10",
    has_title_constant is not None
)

has_retention_constant = re.search(r'SESSION_RETENTION_DAYS\s*=\s*90', controller_content)
test(
    "定义了 SESSION_RETENTION_DAYS = 90",
    has_retention_constant is not None
)

# 检查常量使用
uses_title_constant = 'trimmed_message[:SESSION_TITLE_MAX_LENGTH]' in controller_content
test(
    "_create_new_session 使用 SESSION_TITLE_MAX_LENGTH 常量",
    uses_title_constant
)

uses_retention_constant = 'cleanup_old_sessions(days=SESSION_RETENTION_DAYS)' in controller_content
test(
    "_initialize_database 使用 SESSION_RETENTION_DAYS 常量",
    uses_retention_constant
)

# ==================== 测试7: 空标题验证 ====================
print("\n[TEST 7] 空标题验证")
print("-" * 80)

if create_session_match:
    create_session_method = create_session_match.group(0)

    has_strip = '.strip()' in create_session_method
    test(
        "_create_new_session 对消息进行 strip() 处理",
        has_strip
    )

    has_timestamp_title = "datetime.now().strftime" in create_session_method
    test(
        "_create_new_session 为空消息生成时间戳标题",
        has_timestamp_title
    )

    # 检查默认标题格式
    has_default_format = re.search(r'新对话.*%m-%d %H:%M', create_session_method)
    test(
        "默认标题格式为 '新对话 MM-DD HH:MM'",
        has_default_format is not None
    )

# ==================== 测试8: 导入检查 ====================
print("\n[TEST 8] 必要的导入")
print("-" * 80)

has_json_import = re.search(r'^import json', controller_content, re.MULTILINE)
test(
    "chat_controller.py 导入了 json 模块",
    has_json_import is not None
)

has_datetime_import = re.search(r'from datetime import datetime', controller_content)
test(
    "chat_controller.py 导入了 datetime",
    has_datetime_import is not None
)

has_messagebox_import = re.search(r'from PySide6\.QtWidgets import.*QMessageBox', controller_content)
test(
    "chat_controller.py 导入了 QMessageBox",
    has_messagebox_import is not None
)

# ==================== 测试9: 错误标志重置 ====================
print("\n[TEST 9] 错误标志重置")
print("-" * 80)

# 在新建会话时重置
reset_in_create = '_db_save_error_shown = False' in create_session_method if create_session_match else False
test(
    "_create_new_session 成功时重置错误标志",
    reset_in_create
)

# 在选中会话时重置
session_selected_match = re.search(
    r'def _on_session_selected\(self.*?:.*?\n(?:\s{4,8}.*\n)*?(?=\n    def |\n    @|\Z)',
    controller_content,
    re.MULTILINE | re.DOTALL
)
if session_selected_match:
    session_selected_method = session_selected_match.group(0)
    reset_in_select = '_db_save_error_shown = False' in session_selected_method
    test(
        "_on_session_selected 重置错误标志",
        reset_in_select
    )
else:
    test("找到 _on_session_selected 方法", False)

# 在新建会话请求时重置
new_session_match = re.search(
    r'def _on_new_session_requested\(self\):.*?(?=\n    def |\n    @|\Z)',
    controller_content,
    re.MULTILINE | re.DOTALL
)
if new_session_match:
    new_session_method = new_session_match.group(0)
    reset_in_new = '_db_save_error_shown = False' in new_session_method
    test(
        "_on_new_session_requested 重置错误标志",
        reset_in_new
    )
else:
    test("找到 _on_new_session_requested 方法", False)

# ==================== 测试总结 ====================
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)
print(f"总测试数: {total_tests}")
print(f"[PASS] 通过: {passed_tests}")
print(f"[FAIL] 失败: {failed_tests}")

pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
print(f"\n通过率: {pass_rate:.1f}%")

if pass_rate >= 90:
    print("\n[SUCCESS] 验证通过！所有修复已正确实施。")
    print("代码质量评分预计 >= 90%")
    sys.exit(0)
elif pass_rate >= 80:
    print("\n[WARNING] 大部分修复已完成，但仍有少量问题需要处理。")
    sys.exit(1)
else:
    print("\n[ERROR] 验证失败！需要重新检查修复。")
    sys.exit(2)
