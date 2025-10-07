# 样式与约定
- **沟通/语言**：遵循根目录 `AGENTS.md` —— 默认使用中文描述，技术关键词保留英文；处理前先在 `progress.md` 记录任务、勾选进度并写明“问题来源/解决方法/解决原理”。
- **Shell 前置**：首次运行 PowerShell 命令必须执行 `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`。所有源文件需保持 UTF-8，无 BOM。
- **命名 & 结构**：类使用 `CamelCase`，函数/变量为 `snake_case`；广泛使用 `@dataclass`、`Enum`、`typing` 类型注解与三引号文档字符串，保持中文说明。
- **公式/数据格式**：映射引用使用 `[工作表]![项目]`（界面展示）和 `build_formula_reference_v2` 生成的 `[Sheet:"Item"](Cell)` 字符串（内部计算）；修改相关逻辑需同步 `excel_utils_v2`、`MappingFormula`、`CalculationEngine`。
- **模块交互**：`WorkbookManager` 是核心状态容器，被 `DataExtractor`、`AIMapper`、`CalculationEngine`、界面组件共享；新增功能需避免破坏其字典结构（`target_items`、`source_items`、`mapping_formulas` 等）。
- **界面风格**：`main.py` 使用 `QMainWindow` + `QDockWidget` + `QSplitter` 构建四象限布局；新增面板应遵循现有 `DockWidget` 样式和信号槽模式。
- **测试脚本**：`tests/` 下脚本多为可直接运行的诊断工具；若新建测试，保持独立运行、打印友好日志的风格，必要时补充 `pytest` 兼容接口。