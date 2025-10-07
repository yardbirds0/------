# 任务完成检查
1. **验证功能**：针对修改的模块运行聚焦脚本（如 `python tests\simple_test.py`、`python tests\debug_full_workflow.py`），必要时执行 `python -m pytest` 与 UI 手动验证（`python main.py` 加载示例工作簿）。
2. **检查数据文件**：确认 `workbook_config.json`、`data/memory/*.json` 等状态文件是否需要同步更新或保持原样，避免意外覆盖示例数据。
3. **记录进度**：在根目录 `progress.md` 内更新对应任务块的复选框，并补充“问题来源/解决方法/解决原理”说明。
4. **编码规范**：确保所有新增/修改文件保存为 UTF-8，无 BOM；若执行 PowerShell 命令，确认已设置 `OutputEncoding`。
5. **提交说明**：向用户汇报更改点、测试结果以及可能的后续风险或待办，保持中文描述、英文技术词。