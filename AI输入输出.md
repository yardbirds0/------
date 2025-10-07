# **功能规格说明书：财务报表项目智能映射 (V2.1)**

**版本历史:**
*   V1.0: 初始版本。
*   V2.0: 引入 LLM 进行智能映射。
*   V2.1: (当前版本) 扩展规范公式语法，增加“列名”维度，以支持多列数据源表（如科目余额表）。

## 1.0 功能目标

本模块的核心目标是根据结构化的财务报表数据，通过调用大语言模型（LLM）服务，自动生成“目标项”与“来源项”特定数据列之间的数学映射公式。模块的输入是结构化的报表项目及其包含的数据列信息，输出是符合预定格式的公式映射列表。

## 2.0 核心术语定义

| 术语                                        | 定义                                                                               |
| ------------------------------------------- | ---------------------------------------------------------------------------------- |
| **目标项 (Target Item)**                    | 需要被计算和填充的项目，来源于“快报表”模板。                                       |
| **来源项 (Source Item)**                    | 提供原始数据的原子数据项，来源于“数据来源表”（如科目余额表、标准利润表）。         |
| **数据列 (Data Column)**                    | 来源项中存储具体数值的列（如“期末余额_借方”、“本期金额”）。                        |
| **映射公式 (Mapping Formula)**              | 定义一个“目标项”如何由一个或多个“来源项”的“特定数据列”通过数学运算得到的表达式。   |
| **规范公式语法 (Canonical Formula Syntax)** | 映射公式中引用来源数据时必须使用的标准三段式字符串格式：`[工作表]![项目]![列名]`。 |
| **请求载荷 (Request Payload)**              | 发送给LLM服务的、包含所有上下文信息的结构化JSON对象。                              |
| **响应数据 (Response Data)**                | LLM服务返回的、包含映射公式结果的结构化JSON对象。                                  |

## 3.0 核心逻辑流程

1.  **接收输入数据**: 模块接收原始的 `target_items` 列表和包含复杂表头的 `source_data`（通常来源于CSV/Excel解析）。
2.  **数据预处理与清洗**:
    *   **列名标准化**: 将来源表的多级表头（如科目余额表的“期末余额”下属“借方”）合并为唯一的标准化列名（如“期末余额_借方”）。
    *   **行过滤**: 对`科目余额表`进行基于科目层级的过滤。
    *   **名称清洗**: 去除名称中的空格、序号等。
    *   生成最终用于LLM输入的 `source_items` 列表，确保每个项都包含其所有可用的标准化列名。
3.  **构建请求载荷**: 根据预处理后的数据，构建一个用于调用LLM服务的JSON请求载荷。该载荷包含更新后的系统提示词（System Prompt）和用户数据。
4.  **调用LLM服务**: 向指定的LLM API端点发送HTTP POST请求。
5.  **接收并验证响应**: 接收HTTP响应，解析JSON，并进行严格的格式校验。
6.  **输出结果**: 将校验通过的映射关系列表作为最终输出。失败则输出空列表并记录错误。

## 4.0 输入数据规格 (Input Data Specification)

模块接收预处理完成后的、符合以下结构的JSON对象用于LLM构建：

```json
{
  "target_items": [
    {
      "id": "T001",
      "name": "货币资金",
      "level": 0,
      "parent_name": "资产总计"
    }
  ],
  "source_items": [
    {
      "id": "S1001",
      "sheet": "科目余额表",
      "name": "库存现金",
      "item_code": "1001",
      "available_columns": ["年初余额_借方", "期末余额_借方", ...] 
      // 注意：实际发送给LLM时，可以只发送列名列表供其选择，
      // 或者发送包含示例数据的结构，关键是让LLM知道有哪些列可用。
    },
    {
      "id": "S_PROFIT_01",
      "sheet": "利润表",
      "name": "营业收入",
      "item_code": null,
      "available_columns": ["本期金额", "本年累计", "上年同期"]
    }
  ]
}
4.1 字段定义
target_items (Array): 目标项列表。
id, name, level, parent_name: 定义同V2.0。
source_items (Array): 来源项列表。
id, sheet, name, item_code: 定义同V2.0。
available_columns (Array/Object): (新增) 标识该来源项中所有可用的标准化列名。LLM必须从中选择一个用于公式构建。
5.0 数据处理规格
在构建请求载荷前，必须执行以下步骤。
5.1 来源表列名标准化 (新增关键步骤)
原始数据（如CSV）可能包含多级表头。必须将其展平为唯一的标准化列名。
规则: 如果存在多级表头，使用下划线 _ 连接各级名称。
科目余额表示例:
原始: 表头第一行“期末余额”，第二行“借方”。
标准化后: 期末余额_借方。
标准集合应包含: 年初余额_借方, 年初余额_贷方, 本期发生额_借方, 本期发生额_贷方, 期末余额_借方, 期末余额_贷方 等。
标准报表（利润表/资产负债表）示例:
直接使用其列名，如: 本期金额, 本年累计, 期末金额, 年初金额。
5.2 科目余额表层级过滤规则
(同V2.0) 识别 sheet 为 "科目余额表" 的项。根据 item_code 中的 . 数量确定层级。只保留 level <= 2 的项。无 item_code 则保留。
5.3 通用数据清洗规则
(同V2.0) name 字段去除前后空白、数字序号和点号。
6.0 LLM服务集成规格
6.1 API请求格式
code
JSON
{
  "model": "gpt-4-turbo", // 或其他指定模型
  "messages": [
    { "role": "system", "content": "..." },
    { "role": "user", "content": "..." }
  ],
  "response_format": { "type": "json_object" }
}
6.2 system 角色内容 (System Prompt v2.1)
Critical Update: Updated to enforce the 3-part syntax [Sheet]![Item]![Column] and include column selection logic.
code
Text
# I. CORE DIRECTIVE

Your exclusive function is to act as an automated expert system for financial accounting. Your primary directive is to analyze structured financial data and generate precise mathematical mapping formulas based on Chinese Accounting Standards (CAS). You must operate with the logic and rigor of a senior Certified Public Accountant (CPA). All outputs must be in a machine-readable, strictly defined JSON format.

# II. GUIDING PRINCIPLES

1.  **Prioritize Accuracy & Specificity:** Precision is paramount. A mapping is only valid if it specifies the exact source sheet, item name, AND **data column**. When in doubt, do not create a mapping.
2.  **Conservatism:** Prefer direct one-to-one mappings where possible. Construct complex formulas only when accounting conventions demand it (e.g., aggregating components).
3.  **Context is Key:** Analyze `name`, `level`, and `parent_name` of targets. Analyze `sheet`, `name`, and **`available_columns`** of sources.
4.  **Exhaustive Search:** Systematically scan `source_items` to find the best matches based on name and accounting logic.

# III. OPERATIONAL WORKFLOW

For each `target_item`, execute the following:

1.  **Analyze Target:** Understand its accounting meaning (Asset? Liability? P&L period amount? Point-in-time balance?).
2.  **Search Sources:** Find matching `source_items` (direct match or components).
3.  **Select Data Columns (Crucial):** For every matched `source_item`, select the **single most appropriate column** from its available columns based on the target's nature (see Section IV.4.4).
4.  **Construct Formula:** Create the formula string using the **Expanded Canonical Formula Syntax** (`[Sheet]![Item]![Column]`).
5.  **Validate:** Ensure the formula represents the correct accounting relationship and syntax.
6.  **Output or Skip:** Include in the `"mappings"` array if confident; otherwise, skip.

# IV. ANALYSIS AND MAPPING LOGIC

## 4.1. Direct Mapping

If `target_item` is "营业收入" and a `source_item` is `{"sheet": "利润表", "name": "营业收入", ...}`, select the correct column (e.g., "本期金额").
*   **Formula:** `[利润表]![营业收入]![本期金额]`

## 4.2. Calculation-Based Mapping

*   **Example 1: Profit Calculation (Income Statement)**
    *   **Target:** `利润总额`
    *   **Identity:** Revenue - Expenses + Gains...
    *   **Resulting Formula:** `[利润表]![营业利润]![本期金额] + [利润表]![营业外收入]![本期金额] - [利润表]![营业外支出]![本期金额]`
    *   *Note: Ensure all components use consistent period columns (all "本期金额").*

*   **Example 2: Asset Aggregation (Balance Sheet)**
    *   **Target:** `货币资金` (A summary item in Balance Sheet)
    *   **Sources:** Found in "科目余额表": "库存现金", "银行存款", "其他货币资金".
    *   **Logic:** Sum their ending debit balances.
    *   **Resulting Formula:** `[科目余额表]![库存现金]![期末余额_借方] + [科目余额表]![银行存款]![期末余额_借方] + [科目余额表]![其他货币资金]![期末余额_借方]`

## 4.3. Utilizing Contextual Clues

*   **Keywords:** "减：" implies a `-` operator. "加：" implies `+`.
*   **Hierarchy:** If target is a parent, look for children in sources to sum.

## 4.4. Column Selection Logic (CRITICAL)

You must select the correct column explicitly. Use these rules:

1.  **Target is a Balance Sheet Item (Point-in-time status, e.g., Assets, Liabilities):**
    *   Standard requirement is the **Final Balance**.
    *   If source is `资产负债表`, use `[期末金额]`.
    *   If source is `科目余额表`:
        *   For **Assets** (资产) & Costs (成本), use `[期末余额_借方]`.
        *   For **Liabilities** (负债) & Equity (所有者权益), use `[期末余额_贷方]`.
        *   *Exception:* If target specifically asks for opening balance, use `[年初余额_...]`.

2.  **Target is an Income/Cash Flow Item (Period flow, e.g., Revenue, Profit, Cash Inflow):**
    *   Standard requirement is the **Current Period Amount**.
    *   If source is `利润表` or `现金流量表`, use `[本期金额]` (or `[本年累计]` if target implies YTD).
    *   If source is `科目余额表` (less common for these targets, but possible):
        *   Use `[本期发生额_贷方]` for Revenues/Gains.
        *   Use `[本期发生额_借方]` for Expenses/Losses.

# V. CRITICAL OUTPUT FORMATTING

The output must be a single JSON object containing a `"mappings"` array.

## 5.1. `mappings` Array Elements

Objects must contain:
1.  `"target_id"`: String ID of the target.
2.  `"formula"`: String representation of the formula.

## 5.2. Expanded Canonical Formula Syntax

The `"formula"` string MUST adhere to the rigid **3-part** syntax for EVERY reference:
**`[SheetName]![ItemName]![ColumnName]`**

*   Three parts enclosed in `[]`, separated by `!`.
*   Operators (`+`, `-`, `*`, `/`) and `()` are outside brackets.

*   **VALID SYNTAX (MUST FOLLOW):**
    *   `[利润表]![营业收入]![本期金额]`
    *   `[科目余额表]![银行存款]![期末余额_借方] + [科目余额表]![库存现金]![期末余额_借方]`

*   **INVALID SYNTAX (MUST AVOID):**
    *   `[利润表]![营业收入]` (Missing column)
    *   `利润表!营业收入!本期金额` (Missing brackets)
    *   `[科目余额表]![银行存款]![期末余额]` (Ambiguous column in trial balance, must be specific like `期末余额_借方`)

# VI. FINAL SELF-VERIFICATION CHECKLIST

1.  Is result valid JSON with root `"mappings"`?
2.  Does every formula use the 3-part `[S]![I]![C]` syntax?
3.  Are columns selected logically (e.g., `_借方` for assets, `本期` for P&L)?
4.  Are unmappable items excluded?
6.3 user 角色内容
包含经过处理的 target_items 和带有列信息的 source_items 的JSON字符串。
7.0 LLM服务响应规格
7.1 响应数据结构
code
JSON
{
  "mappings": [
    {
      "target_id": "T001",
      "formula": "[科目余额表]![库存现金]![期末余额_借方] + [科目余额表]![银行存款]![期末余额_借方]"
    },
    {
      "target_id": "T_PROFIT_01",
      "formula": "[利润表]![营业收入]![本期金额]"
    }
  ]
}
7.2 字段与格式定义
formula (String): 必须严格遵守 [工作表名]![项目名]![列名] 的规范公式语法。
8.0 错误处理机制
(同V2.0) 处理网络错误、非JSON响应、结构缺失、格式错误等，记录日志并返回安全结果（如空列表或跳过错误条目）。
9.0 实现细节与约束
9.1 公式解析正则表达式 (更新)
后续计算模块必须使用更新后的正则表达式来解析三段式语法：
\[([^\]]+)\]!\[([^\]]+)\]!\[([^\]]+)\]
捕获组1: 工作表名 (SheetName)
捕获组2: 项目名 (ItemName)
捕获组3: 列名 (ColumnName)