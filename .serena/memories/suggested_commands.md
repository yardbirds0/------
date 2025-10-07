# 常用命令
## 环境准备（Windows PowerShell）
- `python -m venv .venv`
- `.\.venv\Scripts\activate`
- `pip install -r requirements_pyside6.txt`

## 运行与调试
- `python main.py` —— 启动完整 PySide6 应用界面。
- `python tests\debug_full_workflow.py` —— 从加载 Excel 到计算的全流程诊断。
- `python tests\verify_gui_display.py` —— 检查来源项树/下拉列表显示。
- `python tests\simple_test.py` —— 快速验证数据模型与列规则。
- `python -m pytest` —— 按需运行 `tests/` 下兼容的 Pytest 用例。

## 工具脚本
- `python tests\list_sheet_names.py` / `tests\analyze_sheet_structure.py` —— 分析 Excel 表头与结构。
- `python tests\debug_file_manager_classification.py` —— 排查工作表自动分类。
- `python tests\diagnose_data_columns.py` —— 检查科目余额表列识别结果。

运行脚本前确认 `workbook_config.json` 或命令行参数指向正确的 Excel 文件；大部分脚本会在 `tests/` 下生成对应的 `*.json` 报告或日志。