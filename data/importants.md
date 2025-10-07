# 重要问题记录与解决方案

## 📋 目录
- [列头文字在CSS主题下不显示问题](#列头文字在css主题下不显示问题)
- [搜索高亮导致文字消失问题](#搜索高亮导致文字消失问题)

---

## 列头文字在CSS主题下不显示问题

### 🔍 问题描述

**发现时间**：2025-09-30

**现象**：
1. 主程序运行时，来源项库（SearchableSourceTree）中数据表格的列头只显示结构（边框、跨行/跨列），但文字不显示
2. 自定义的base_headers（标识、项目名称、层级、值、单位）文字正常显示
3. 从Excel元数据生成的数据列头（科目编码、科目名称、期初余额_借方等）文字不显示
4. 测试程序无CSS时完全正常，有CSS glass theme时出现问题

**影响范围**：
- 所有使用MultiRowHeaderView的表格组件
- 应用了glass theme CSS的界面

---

### 🐛 错误原因

#### 根本原因

**Qt的`style().drawControl()`方法在应用CSS后行为异常**，导致自定义绘制的文字被覆盖或不可见。

#### 详细分析

1. **两种渲染路径的差异**：
   - **base_headers（列索引0-4）**：不在`layout_map`中，使用Qt原生`QHeaderView::paintSection()`，CSS的`color: #2c3e50`生效 ✅
   - **数据列头（列索引5+）**：在`layout_map`中，使用自定义`MultiRowHeaderView::paintSection()`

2. **自定义渲染的绘制流程**：
   ```python
   # 原有的错误流程
   1. 调用 style().drawControl(QStyle.CE_Header, ...) 绘制背景
   2. 调用 painter.drawText() 绘制文字
   ```

3. **CSS glass theme的影响**：
   ```css
   QHeaderView::section {
       background: qlineargradient(...);  /* 渐变背景 */
       color: #2c3e50;                    /* 文字颜色 */
       padding: 7px 10px;
   }
   ```

4. **冲突机制**：
   - `style().drawControl()`在应用CSS后可能会：
     - 在文字绘制后重新填充背景
     - 设置错误的painter状态（clip区域、transform）
     - 使用不透明背景覆盖已绘制的文字
   - CSS的`color`属性只对Qt原生绘制的文字有效，对`painter.drawText()`无效

5. **尝试过的失败方案**：
   - ❌ 使用`QColor("#2c3e50")`代替palette颜色
   - ❌ 使用`QPen(QColor(44, 62, 80))`显式设置pen
   - 这些方案失败的原因：文字确实被正确绘制了，但随后被`style().drawControl()`覆盖

---

### ✅ 解决方法

#### 核心思路

**完全绕过Qt的style系统**，使用`QPainter`直接控制整个绘制流程，确保：
1. 背景先绘制
2. 文字后绘制
3. 没有Qt内部逻辑干扰

#### 实施步骤

**1. 添加QLinearGradient导入**

```python
# components/advanced_widgets.py
from PySide6.QtGui import (
    ..., QPen, QLinearGradient
)
```

**2. 新增`_draw_background()`方法**

```python
def _draw_background(self, painter: QPainter, rect: QRect) -> None:
    """直接绘制背景，避免CSS主题冲突"""
    painter.save()

    # 创建渐变背景（glass theme效果）
    gradient = QLinearGradient(rect.x(), rect.y(), rect.x(), rect.y() + rect.height())
    gradient.setColorAt(0, QColor(248, 250, 253, 235))  # rgba(248, 250, 253, 0.92)
    gradient.setColorAt(1, QColor(240, 243, 250, 224))  # rgba(240, 243, 250, 0.88)

    painter.fillRect(rect, gradient)

    # 绘制边框
    painter.setPen(QPen(QColor(190, 200, 215, 89), 1))  # rgba(190, 200, 215, 0.35) for right
    painter.drawLine(rect.topRight(), rect.bottomRight())

    painter.setPen(QPen(QColor(190, 200, 215, 115), 1))  # rgba(190, 200, 215, 0.45) for bottom
    painter.drawLine(rect.bottomLeft(), rect.bottomRight())

    painter.restore()
```

**3. 重写`paintSection()`方法**

```python
def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int) -> None:
    layout_entry = self._layout.get(logicalIndex)
    if self.orientation() != Qt.Horizontal or not layout_entry or self._row_count <= 1:
        super().paintSection(painter, rect, logicalIndex)
        return

    row_count = max(1, self._row_count)
    row_heights = self._calculate_row_heights(rect.height(), row_count)

    primary_info = layout_entry.get('primary', {}) or {}
    primary_row_span = max(1, min(primary_info.get('row_span', 1), row_count)) if primary_info else 1

    top_rect = None
    if primary_info:
        top_rect = self._compute_group_rect(
            primary_info.get('members') or [logicalIndex],
            rect, 0, primary_row_span, row_heights
        )

    # 🔧 修复：使用自定义背景绘制代替style().drawControl()
    top_painted = False
    if primary_info and primary_info.get('col_span', 1) > 1 and top_rect is not None:
        group_key = tuple(primary_info.get('members') or [logicalIndex])
        if primary_info.get('is_group_start', True) or group_key not in self._painted_primary_groups:
            self._draw_background(painter, top_rect)  # ← 直接绘制背景
            self._painted_primary_groups.add(group_key)
            top_painted = True
    elif top_rect is not None:
        self._draw_background(painter, top_rect)  # ← 直接绘制背景
        top_painted = True

    remaining_height = rect.height() - sum(row_heights[:primary_row_span])
    if remaining_height > 0:
        bottom_rect = QRect(
            rect.x(),
            rect.y() + sum(row_heights[:primary_row_span]),
            rect.width(),
            remaining_height
        )
        self._draw_background(painter, bottom_rect)  # ← 直接绘制背景
    elif not top_painted:
        self._draw_background(painter, rect)  # ← 直接绘制背景

    # 绘制文字（在背景之后）
    painter.save()
    self._paint_primary_cell(painter, None, rect, logicalIndex, primary_info, row_heights, row_count)
    self._paint_secondary_cell(painter, None, rect, logicalIndex, layout_entry.get('secondary', {}), row_heights, row_count)
    painter.restore()
```

**4. 更新`_paint_primary_cell()`和`_paint_secondary_cell()`**

```python
def _paint_primary_cell(
    self,
    painter: QPainter,
    option: Optional[QStyleOptionHeader],  # ← 改为Optional
    rect: QRect,
    logical_index: int,
    primary: Dict[str, Any],
    row_heights: List[int],
    total_rows: int
) -> None:
    # ... 文字绘制逻辑不变 ...

    if total_rows > row_span:
        divider_y = group_rect.y() + sum(row_heights[:row_span])
        painter.save()
        # 🔧 使用固定颜色代替palette，避免CSS冲突
        painter.setPen(QPen(QColor(190, 200, 215, 115), 1))
        painter.drawLine(group_rect.x(), divider_y, group_rect.x() + group_rect.width(), divider_y)
        painter.restore()

# _paint_secondary_cell 同样将option改为Optional
```

---

### 📊 修改内容总结

**修改文件**：
- `components/advanced_widgets.py`

**主要变更**：

1. **导入新增**：
   - `QLinearGradient`

2. **新增方法**：
   - `MultiRowHeaderView._draw_background()` - 直接绘制渐变背景和边框

3. **修改方法**：
   - `MultiRowHeaderView.paintSection()` - 移除所有`style().drawControl()`调用，改用`_draw_background()`
   - `MultiRowHeaderView._paint_primary_cell()` - option参数改为Optional，divider颜色改为固定值
   - `MultiRowHeaderView._paint_secondary_cell()` - option参数改为Optional

4. **删除内容**：
   - 移除了`QStyleOptionHeader`的创建和初始化
   - 移除了所有`style().drawControl(QStyle.CE_Header, ...)`调用

**代码量统计**：
- 新增：约30行（`_draw_background`方法）
- 修改：约50行（`paintSection`和相关方法）
- 删除：约20行（QStyleOptionHeader相关代码）

---

### 🎯 效果验证

**测试方法**：
1. 运行`tests/test_glass_theme_headers.py`（有CSS glass theme）
2. 运行`tests/test_user_excel_gui.py`（无CSS）
3. 运行主程序`main.py`

**验证结果**：
- ✅ 所有数据列头文字正常显示
- ✅ base_headers文字正常显示
- ✅ 列头结构（边框、跨行/跨列）正常显示
- ✅ glass theme视觉效果保持一致（渐变背景、半透明边框）
- ✅ 无CSS环境下依然正常工作

---

### 💡 经验总结

#### 关键教训

1. **Qt的CSS与自定义绘制的冲突**：
   - CSS主要影响Qt原生控件的渲染
   - 自定义`paintSection()`后，不要依赖`style().drawControl()`
   - CSS的`color`属性不影响`painter.drawText()`

2. **调试思路**：
   - 对比不同场景（有CSS vs 无CSS）的行为差异
   - 分析不同数据的渲染路径差异（base_headers vs 数据列头）
   - 使用测试程序隔离问题

3. **解决原则**：
   - 遇到Qt内部行为不可控时，完全绕过使用自定义实现
   - 自定义绘制要完全控制绘制顺序和状态
   - 避免混用Qt原生渲染和自定义渲染

#### 通用方案

**当遇到类似的CSS与自定义绘制冲突时**：

```python
# ❌ 错误做法：混用style().drawControl()和painter.drawText()
def paintSection(self, painter, rect, index):
    option = QStyleOptionHeader()
    self.style().drawControl(QStyle.CE_Header, option, painter, self)  # Qt绘制背景
    painter.drawText(rect, text)  # 自定义绘制文字 ← 可能被覆盖

# ✅ 正确做法：完全自定义绘制
def paintSection(self, painter, rect, index):
    # 1. 直接绘制背景
    painter.fillRect(rect, gradient)

    # 2. 直接绘制边框
    painter.drawLine(...)

    # 3. 直接绘制文字
    painter.drawText(rect, text)
```

#### 适用场景

这个解决方案适用于：
- 自定义QHeaderView的绘制
- 需要多行表头或复杂表头布局
- 应用了CSS主题的界面
- 需要精确控制渲染顺序的场景

---

### 🔗 相关资源

- **修改文件**：[components/advanced_widgets.py](../components/advanced_widgets.py)
- **测试脚本**：[tests/test_glass_theme_headers.py](../tests/test_glass_theme_headers.py)
- **主题CSS**：[main.py:1714-1724](../main.py#L1714)

---

**记录人**：Claude Code
**日期**：2025-09-30
**优先级**：⚠️ 高（影响核心功能的用户体验）

---

## 搜索高亮导致文字消失问题

### 🔍 问题描述

**发现时间**：2025-10-02

**问题1：主表格高亮后文字消失**
- **现象**：搜索后能看到高亮背景和筛选出的行数，但所有行的文字都消失了
- **影响范围**：中间主数据表格（`main_data_grid`）的搜索功能
- **严重程度**：🔴 严重（完全无法看到搜索结果内容）

**问题2：来源项库高亮未生效**
- **现象**：右侧来源项库搜索后，没有高亮效果
- **影响范围**：右侧`SearchableSourceTree`的搜索功能
- **严重程度**：🟡 中等（影响用户体验，但内容可见）

---

### 🐛 错误原因

#### 问题1根本原因

**painter.save()/restore()和super().paint()调用顺序错误**

```python
# ❌ 错误的实现（main.py原始代码）
def paint(self, painter, option, index):
    bg_color = index.data(Qt.BackgroundRole)
    if bg_color:
        painter.save()
        painter.fillRect(option.rect, bg_color)  # 先绘制背景
        painter.restore()  # ⚠️ 恢复状态

        option_copy = QStyleOptionViewItem(option)
        option_copy.backgroundBrush = QBrush(bg_color)  # ⚠️ 设置backgroundBrush

        super().paint(painter, option_copy, index)  # 后绘制文字
        # ↑ 问题：painter状态已恢复，option_copy可能导致Qt跳过文字绘制
```

**详细分析**：

1. **painter.restore()的影响**：
   - `save()`保存painter的所有状态（画笔、画刷、变换、裁剪区域等）
   - `restore()`恢复到save()时的状态
   - 在restore()之后调用super().paint()，painter状态可能不匹配，导致文字绘制失败

2. **option_copy.backgroundBrush的问题**：
   - 设置`backgroundBrush`后，Qt可能认为背景已由style系统处理
   - Qt的默认实现可能跳过某些绘制步骤，包括文字
   - 这是Qt内部行为，不同版本可能表现不同

3. **绘制顺序错误**：
   - 正确的顺序应该是：**内容（文字）→ 效果（高亮）**
   - 错误的顺序：**效果（高亮）→ 恢复状态 → 内容（文字）**

#### 问题2根本原因

**SearchableSourceTree没有应用SearchHighlightDelegate**

- `SearchableSourceTree`的`_match_row`方法正确设置了`BackgroundRole`
- 但没有设置`SearchHighlightDelegate`来绘制高亮
- CSS样式覆盖了model的`BackgroundRole`，导致高亮不可见

---

### ✅ 解决方法

#### 核心思路

**反转绘制顺序 + 使用半透明叠加**

参考`data/importants.md`中列头文字修复的成功经验：
- 完全控制绘制流程，不依赖Qt的style系统
- 先绘制内容（文字），后绘制效果（高亮）
- 使用半透明叠加，而不是完全替换背景

#### 实施步骤

**步骤1：修复SearchHighlightDelegate.paint()方法**

```python
# ✅ 正确的实现（main.py:1053-1101）
class SearchHighlightDelegate(QStyledItemDelegate):
    """搜索高亮委托 - 覆盖CSS样式实现高亮显示

    核心修复：
    1. 先让Qt绘制默认内容（包括文字）
    2. 然后在文字上方叠加半透明高亮背景
    3. 这样既保留文字，又显示高亮效果
    """

    def paint(self, painter: QPainter, option, index: QModelIndex):
        """重写paint方法，先绘制内容再叠加高亮背景"""
        bg_color = index.data(Qt.BackgroundRole)

        if bg_color and isinstance(bg_color, QColor):
            # 🔧 关键修复：先让Qt绘制默认内容（包括文字）
            # 注意：不修改option，使用原始option让文字正常显示
            super().paint(painter, option, index)

            # 🔧 然后在文字上方叠加半透明高亮背景
            painter.save()

            # 创建半透明的高亮颜色（让文字可见）
            highlight_overlay = QColor(bg_color)
            highlight_overlay.setAlpha(120)  # 设置透明度，让文字可见

            painter.fillRect(option.rect, highlight_overlay)

            # 如果是选中状态，添加额外的选中效果
            if option.state & QStyleOptionViewItem.State_Selected:
                selection_overlay = QColor(235, 145, 190, 50)
                painter.fillRect(option.rect, selection_overlay)

            # 如果是悬停状态，添加额外的悬停效果
            elif option.state & QStyleOptionViewItem.State_MouseOver:
                hover_overlay = QColor(235, 145, 190, 30)
                painter.fillRect(option.rect, hover_overlay)

            painter.restore()
        else:
            # 没有高亮，使用默认绘制（CSS生效）
            super().paint(painter, option, index)
```

**关键变更**：
1. **删除**：`option_copy`的创建和`backgroundBrush`设置
2. **反转顺序**：先调用`super().paint()`绘制文字，再叠加背景
3. **使用半透明**：设置`alpha=120`让文字可见
4. **保持save/restore**：但放在super().paint()之后

**步骤2：为来源项库应用SearchHighlightDelegate**

```python
# main.py:2450-2452
# 🔧 修复：为来源项库应用SearchHighlightDelegate，确保搜索高亮可见
self.source_highlight_delegate = SearchHighlightDelegate(self.source_tree)
self.source_tree.setItemDelegate(self.source_highlight_delegate)
```

---

### 📊 修改内容总结

**修改文件**：
1. `main.py:1053-1101` - SearchHighlightDelegate类
2. `main.py:2450-2452` - 来源项库delegate设置

**新增测试文件**：
1. `tests/test_search_highlight_fix.py` - 修复验证脚本（约300行）
2. `tests/test_search_highlight_debug.py` - 诊断脚本（约150行）

**代码量统计**：
- **核心修复**：18行（修改15行 + 新增3行）
- **删除代码**：5行（错误的option_copy逻辑）
- **测试代码**：约450行

---

### 🎯 效果验证

**验证方法**：
1. 运行`tests/test_search_highlight_fix.py`
2. 左侧测试主表格：输入"测试"或"1000"，点击搜索
3. 右侧测试来源项库：输入"科目"或"100"，点击搜索

**问题1修复效果**：
- ✅ 搜索后文字正常显示（半透明粉色高亮背景）
- ✅ 文字清晰可见，不会消失
- ✅ 选中和悬停效果正常叠加
- ✅ CSS样式不影响高亮显示

**问题2修复效果**：
- ✅ 来源项库搜索高亮正常显示（半透明黄色）
- ✅ 文字清晰可见
- ✅ 树形结构中的所有层级均支持高亮
- ✅ CSS样式不影响高亮显示

---

### 💡 经验总结

#### 关键教训

1. **绘制顺序至关重要**：
   ```
   错误：背景 → 恢复状态 → 文字（失败）
   正确：文字（Qt默认）→ 半透明背景叠加（成功）
   ```

2. **painter.save()/restore()的正确使用**：
   - 只在需要修改painter状态时使用
   - 不要在restore()之后依赖painter状态
   - 如果需要在super().paint()后绘制，应该在super()调用之后save/restore

3. **不要混用Qt的style系统和自定义绘制**：
   - `option_copy.backgroundBrush`等设置可能导致Qt跳过某些绘制
   - 要么完全自定义绘制，要么完全使用Qt的style系统
   - 混用会导致不可预测的行为

4. **半透明叠加的优势**：
   - 文字可见（不会被完全覆盖）
   - 视觉柔和（避免过于刺眼）
   - 支持叠加（选中、悬停效果可继续叠加）

#### 通用模式

**自定义Delegate绘制高亮的标准模式**：

```python
class HighlightDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # 检查是否需要高亮
        highlight = index.data(Qt.BackgroundRole)

        if highlight:
            # ✅ 步骤1：先让Qt绘制默认内容（文字、图标等）
            super().paint(painter, option, index)

            # ✅ 步骤2：然后叠加半透明高亮效果
            painter.save()
            overlay = QColor(highlight)
            overlay.setAlpha(120)  # 半透明，让文字可见
            painter.fillRect(option.rect, overlay)
            painter.restore()
        else:
            # 无需高亮，正常绘制
            super().paint(painter, option, index)
```

#### 与列头文字修复的对比

**相同点**：
- 都是Qt的CSS与自定义绘制冲突
- 都需要完全控制绘制流程
- 都需要绕过Qt的style系统

**不同点**：
- 列头修复：完全替换`style().drawControl()`，自己绘制背景和文字
- 高亮修复：利用Qt绘制文字，只自定义绘制高亮背景
- 列头修复：不透明背景
- 高亮修复：半透明背景叠加

#### 适用场景

这个解决方案适用于：
- 需要在Qt的QAbstractItemView中实现搜索高亮
- 应用了CSS主题导致BackgroundRole被覆盖
- 需要保留文字和其他内容，只叠加高亮效果
- 需要支持选中和悬停状态的叠加效果

---

### 🔗 相关资源

- **参考文档**：[列头文字在CSS主题下不显示问题](#列头文字在css主题下不显示问题) - 相同原理的另一个应用
- **修改文件**：
  - [main.py:1053-1101](../main.py#L1053) - SearchHighlightDelegate
  - [main.py:2450-2452](../main.py#L2450) - 来源项库delegate设置
- **测试脚本**：
  - [tests/test_search_highlight_fix.py](../tests/test_search_highlight_fix.py) - 修复验证
  - [tests/test_search_highlight_debug.py](../tests/test_search_highlight_debug.py) - 诊断脚本
- **Qt文档**：
  - [QStyledItemDelegate::paint](https://doc.qt.io/qt-6/qstyleditemdelegate.html#paint)
  - [QPainter](https://doc.qt.io/qt-6/qpainter.html)
  - [QColor::setAlpha](https://doc.qt.io/qt-6/qcolor.html#setAlpha)
  - [QPainter::save/restore](https://doc.qt.io/qt-6/qpainter.html#save)

---

**记录人**：Claude Code
**日期**：2025-10-02
**优先级**：🔴 严重（问题1导致搜索功能完全不可用）

---

## 自动列宽调整功能异常与右侧空白区域问题

### 🔍 问题描述

**发现时间**：2025-10-04

**问题演进**：

#### 问题1：特定表格触发自动列宽失效
- **现象**：切换到"企业财务快报利润因素分析表"时，自动列宽功能失效，且影响其他表格
- **影响范围**：所有表格的列宽自动调整功能
- **严重程度**：🔴 严重（核心功能失效）

#### 问题2：快速切换表格时功能不稳定
- **现象**：来回切换表格时，自动列宽"有时候生效，有时候失效"
- **影响范围**：表格切换操作的用户体验
- **严重程度**：🟡 中等（影响操作流畅性）

#### 问题3：右侧空白区域问题
- **现象**：
  1. "企业财务快报利润因素分析表"右侧出现空白区域
  2. 切换到此表后，其他表格也开始出现右侧空白
  3. **关键线索**：全屏模式下所有表格都正常显示，占满容器
- **影响范围**：表格显示的视觉效果
- **严重程度**：🟡 中等（影响界面美观度）

---

### 🐛 错误原因

#### 问题1根本原因：元数据缺失关键字段

```python
# ❌ 原始的不完整元数据
if "利润因素分析" in sheet_name:
    metadata = [
        {
            "key": "指标名称",
            "display_name": "指标名称",
            "is_data_column": False,
            "column_index": 0,
            # 缺少: primary_header, primary_col_span, header_row_count
        }
    ]
```

**分析**：
- `derive_header_layout_from_metadata()`函数依赖这些字段来生成布局
- 缺失字段导致返回空的`layout_map`
- 触发重试机制，5次失败后放弃
- 状态污染传播到其他表格

#### 问题2根本原因：Qt异步更新与定时器管理缺陷

**1. Qt Model-View异步机制问题**：
```python
# Model更新是同步的
model.setActiveSheet(sheet_name)  # 立即更新

# View更新是异步的
# 视图需要等待下一个事件循环才能完成更新
# 100ms延迟可能不够，导致列宽调整时视图还未就绪
```

**2. 定时器管理缺陷**：
```python
# ❌ 错误：未停止旧定时器就启动新的
def schedule_main_table_resize(self, delay_ms: int = 0):
    self._main_resize_timer.start(delay_ms)  # 多次调用会排队多个回调
```

**3. 延迟时间不足**：
- 100ms对于复杂表格的视图更新不够
- 特别是有多行表头的表格需要更多时间

#### 问题3根本原因：列宽计算只应用边界，未填充视口

```python
# ❌ 原始的adjust_main_table_columns只设置最小/最大宽度
for column in adjustable_columns:
    min_width, max_width = adjustable_columns[column]
    header.resizeSection(column, min(max_width, max(min_width, current_width)))
    # 问题：列宽总和 < 视口宽度时，右侧出现空白
```

**详细分析**：
1. `ResizeToContents`模式根据内容设置列宽
2. 内容较少时，列宽总和小于容器宽度
3. 所有`apply_multirow_header`调用使用`stretch_last=False`
4. 全屏时视口更宽，Qt自动拉伸最后一列（默认行为）

---

### ✅ 解决方法

#### 修复1：补充完整元数据字段

```python
# main.py:1214-1275
# ✅ 为利润因素分析表添加完整元数据
if "利润因素分析" in sheet_name:
    metadata = [
        {
            "key": "指标名称",
            "display_name": "指标名称",
            "is_data_column": False,
            "column_index": 0,
            "primary_header": "指标名称",    # ✅ 新增
            "primary_col_span": 1,           # ✅ 新增
            "header_row_count": 1            # ✅ 新增
        },
        # ... 其他列同样处理
    ]

# 同时更新默认配置
return [
    {
        "key": f"column_{i}",
        "display_name": f"列{i+1}",
        "is_data_column": i > 0,
        "column_index": i,
        "primary_header": f"列{i+1}",   # ✅ 新增
        "primary_col_span": 1,           # ✅ 新增
        "header_row_count": 1            # ✅ 新增
    }
    for i in range(5)
]
```

#### 修复2：完善定时器管理与异步同步机制

**2.1 修复定时器生命周期管理**：
```python
# main.py:4045-4066
def schedule_main_table_resize(self, delay_ms: int = 0):
    """延迟调整主数据网格列宽"""
    try:
        if not hasattr(self, "_main_resize_timer"):
            self._main_resize_timer = QTimer(self)
            self._main_resize_timer.setSingleShot(True)
            self._main_resize_timer.timeout.connect(self.adjust_main_table_columns)

        # 🔧 关键修复1：停止旧定时器再启动新的
        if self._main_resize_timer.isActive():
            self._main_resize_timer.stop()
            self.log_manager.info("停止之前的列宽调整定时器")

        # 🔧 关键修复2：增加最小延迟时间
        actual_delay = max(200, delay_ms)  # 最少200ms
        self._main_resize_timer.start(actual_delay)
```

**2.2 使用QTimer.singleShot确保事件循环完成**：
```python
# main.py:5698-5727
def on_target_sheet_changed(self, sheet_name: str):
    """处理主数据表工作表选择变化"""
    if not sheet_name or not self.target_model:
        return

    # 🔧 重置重试计数器
    if hasattr(self, "_main_resize_retry_counts"):
        self._main_resize_retry_counts.pop(sheet_name, None)

    try:
        self.target_model.set_active_sheet(sheet_name)

        # 🔧 关键修复3：使用QTimer.singleShot确保事件循环完成
        QTimer.singleShot(0, lambda: self._apply_main_header_layout())

        # 🔧 关键修复4：增加延迟从100ms到300ms
        self.schedule_main_table_resize(300)
```

**2.3 增加View-Model同步检查**：
```python
# main.py:4126-4137
# 🔧 关键修复5：添加视图-模型同步检查
header_count = header.count() if header else 0
model_column_count = model.columnCount() if model else 0

if header_count != model_column_count:
    self.log_manager.warning(
        f"View和Model未同步: header列数={header_count}, model列数={model_column_count}"
    )
    self._schedule_main_resize_retry(current_sheet, 200)
    return
```

#### 修复3：实现智能填充算法占满视口

**3.1 导入智能填充函数**：
```python
# main.py:118
from components.advanced_widgets import (
    # ... 其他导入
    distribute_columns_evenly,  # ✅ 新增智能填充函数
    ROW_NUMBER_COLUMN_WIDTH,
)
```

**3.2 在adjust_main_table_columns末尾添加智能填充**：
```python
# main.py:4281-4322
# 🔧 关键修复：智能填充以占满视口，避免右侧空白
try:
    # 构建最小/最大宽度字典
    min_widths_dict = {}
    max_widths_dict = {}
    exclude_cols = []

    for column in range(model.columnCount()):
        column_name = ""
        if hasattr(model, "headers") and column < len(model.headers):
            column_name = model.headers[column] or ""

        # 将固定列添加到排除列表
        if column_name in ["状态", "级别", "行次"]:
            exclude_cols.append(column)
        else:
            # 从adjustable_columns获取最小/最大值
            if column in adjustable_columns:
                min_width, max_width = adjustable_columns[column]
                min_widths_dict[column] = min_width
                max_widths_dict[column] = max_width
            else:
                min_widths_dict[column] = 100
                max_widths_dict[column] = 300

    # 应用智能填充确保视口被填满
    distribute_columns_evenly(
        self.main_data_grid,
        exclude_columns=exclude_cols,
        min_widths=min_widths_dict,
        max_widths=max_widths_dict
    )

    self.log_manager.info("已应用智能填充，列宽占满容器宽度")
```

---

### 📊 智能填充算法详解

**distribute_columns_evenly函数原理**（components/advanced_widgets.py:152-273）：

```python
def distribute_columns_evenly(
    table_view: QTableView,
    exclude_columns: List[int] = None,
    min_widths: Dict[int, int] = None,
    max_widths: Dict[int, int] = None
) -> None:
    """
    智能分配列宽以填满视口

    算法步骤：
    1. 计算可用宽度 = 视口宽度 - 固定列宽度 - 滚动条宽度
    2. 获取可调整列的当前宽度
    3. 按比例缩放列宽：新宽度 = 当前宽度 * (可用宽度 / 当前总宽度)
    4. 应用最小/最大限制
    5. 处理舍入误差，确保精确填满
    """
```

**关键特性**：
1. **比例保持**：按当前宽度比例分配，保持相对大小关系
2. **约束遵守**：严格遵守min_widths和max_widths限制
3. **精确填充**：处理舍入误差，确保完全占满容器
4. **固定列排除**：不调整状态、级别等固定列

---

### 🎯 效果验证

**测试场景**：
1. 启动程序，切换到"企业财务快报利润因素分析表"
2. 快速在多个表格间切换
3. 调整窗口大小后检查显示
4. 切换全屏/窗口模式对比

**修复效果**：
- ✅ "利润因素分析表"自动列宽正常工作
- ✅ 不再影响其他表格的列宽功能
- ✅ 快速切换表格时功能稳定
- ✅ 右侧空白区域消除，列宽占满容器
- ✅ 窗口大小变化时自动适配

---

### 💡 经验总结

#### 关键教训

1. **元数据完整性至关重要**：
   - 任何依赖元数据的函数都要有健壮的默认值
   - 防御性编程：总是假设元数据可能不完整

2. **Qt异步机制的正确处理**：
   ```python
   # ✅ 正确的异步处理模式
   model.update()  # 同步更新
   QTimer.singleShot(0, lambda: view_operation())  # 异步视图操作
   ```

3. **定时器管理最佳实践**：
   ```python
   # ✅ 正确的定时器管理
   if timer.isActive():
       timer.stop()  # 先停止
   timer.start(delay)  # 再启动
   ```

4. **视口填充策略**：
   - 不能只设置最小/最大边界
   - 必须主动计算和分配以填满容器
   - 智能填充 > 简单拉伸最后一列

#### 通用解决模式

**处理Qt表格列宽的标准流程**：

```python
def adjust_table_columns(table_view):
    # 步骤1：基于内容设置初始宽度
    header.resizeSections(QHeaderView.ResizeToContents)

    # 步骤2：应用最小/最大限制
    for col in range(model.columnCount()):
        width = clamp(current_width, min_width, max_width)
        header.resizeSection(col, width)

    # 步骤3：智能填充视口
    distribute_columns_evenly(
        table_view,
        exclude_columns=[...],
        min_widths={...},
        max_widths={...}
    )
```

#### 诊断技巧

1. **对比不同环境**：全屏 vs 窗口模式
2. **检查异步时序**：添加延迟和日志
3. **验证元数据**：打印关键字段
4. **监控定时器**：跟踪isActive()状态

---

### 📈 性能优化建议

1. **延迟策略优化**：
   - 简单表格：100-200ms
   - 复杂表格：200-300ms
   - 大数据表格：300-500ms

2. **重试机制改进**：
   - 指数退避：100ms → 200ms → 400ms
   - 最大重试次数：5次
   - 失败后清理状态

3. **缓存优化**：
   - 缓存列宽计算结果
   - 表格未变化时跳过重算

---

### 🔗 相关资源

- **修改文件**：
  - [main.py:1214-1275](../main.py#L1214) - 元数据完整性修复
  - [main.py:4045-4066](../main.py#L4045) - 定时器管理修复
  - [main.py:4126-4137](../main.py#L4126) - View-Model同步检查
  - [main.py:4281-4322](../main.py#L4281) - 智能填充实现
  - [main.py:5698-5727](../main.py#L5698) - 事件循环同步

- **核心函数**：
  - [components/advanced_widgets.py:152-273](../components/advanced_widgets.py#L152) - distribute_columns_evenly

- **测试文件**：
  - tests/verify_fixes.py - 功能验证
  - tests/debug_full_flow.py - 完整流程测试

---

**记录人**：Claude Code
**日期**：2025-10-04
**优先级**：🔴 严重（影响核心功能的稳定性和用户体验）

---