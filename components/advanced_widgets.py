#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级交互组件 - PySide6版本
实现拖放、自动补全、语法高亮等高级交互功能
"""

from typing import Dict, List, Optional, Any, Tuple
import re

from PySide6.QtWidgets import (
    QTreeView, QTextEdit, QLineEdit, QCompleter, QAbstractItemView,
    QStyledItemDelegate, QStyleOptionViewItem, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QFrame, QScrollArea,
    QListWidget, QListWidgetItem, QSplitter, QGroupBox, QDialog,
    QTableView, QComboBox, QHeaderView
)
from PySide6.QtCore import (
    Qt, QMimeData, QModelIndex, Signal, QStringListModel,
    QAbstractListModel, QTimer, QPoint, QRect
)
from PySide6.QtGui import (
    QDrag, QPainter, QColor, QFont, QTextCursor, QTextDocument,
    QSyntaxHighlighter, QTextCharFormat, QPalette, QPixmap,
    QFontMetrics, QKeySequence, QAction, QStandardItemModel, QStandardItem
)

from models.data_models import TargetItem, SourceItem, WorkbookManager
from utils.excel_utils_v2 import build_formula_reference_v2, parse_formula_references_v2


class DragDropTreeView(QTreeView):
    """支持拖放的树视图组件"""

    # 自定义信号
    itemDropped = Signal(QModelIndex, str)  # 项目被拖放
    dragStarted = Signal(QModelIndex)       # 开始拖拽

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)

    def startDrag(self, supportedActions):
        """开始拖拽"""
        indexes = self.selectedIndexes()
        if not indexes:
            return

        # 发送拖拽开始信号
        self.dragStarted.emit(indexes[0])

        # 创建拖拽数据
        drag = QDrag(self)
        mimeData = QMimeData()

        # 获取拖拽的数据
        item = indexes[0].internalPointer()
        if isinstance(item, SourceItem):
            # 来源项：创建引用字符串
            reference_text = item.to_reference_string()
            mimeData.setText(reference_text)
            mimeData.setData("application/x-sourceitem", reference_text.encode())

        elif isinstance(item, str):
            # 工作表名
            mimeData.setText(item)
            mimeData.setData("application/x-sheetname", item.encode())

        drag.setMimeData(mimeData)

        # 创建拖拽图标
        pixmap = self.create_drag_pixmap(indexes[0])
        drag.setPixmap(pixmap)

        # 执行拖拽
        drag.exec_(supportedActions)

    def create_drag_pixmap(self, index: QModelIndex) -> QPixmap:
        """创建拖拽时的图标"""
        rect = self.visualRect(index)
        pixmap = QPixmap(rect.size())
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setOpacity(0.8)

        # 绘制背景
        painter.fillRect(pixmap.rect(), QColor(200, 200, 255, 150))

        # 绘制文本
        painter.setPen(Qt.black)
        text = index.data(Qt.DisplayRole)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, str(text))

        painter.end()
        return pixmap

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """拖放事件"""
        if event.mimeData().hasText():
            drop_index = self.indexAt(event.pos())
            dropped_text = event.mimeData().text()

            # 发送拖放信号
            self.itemDropped.emit(drop_index, dropped_text)

            event.acceptProposedAction()
        else:
            event.ignore()


class FormulaEditor(QTextEdit):
    """公式编辑器 - 支持自动补全和语法高亮"""

    # 自定义信号
    formulaChanged = Signal(str)  # 公式内容变化
    autoCompleteRequested = Signal(str, QPoint)  # 请求自动补全

    def __init__(self, parent=None):
        super().__init__(parent)
        self.workbook_manager: Optional[WorkbookManager] = None
        self.setup_editor()
        self.setup_auto_complete()

        # 自动补全相关
        self.completion_popup = None
        self.current_completion_prefix = ""

    def setup_editor(self):
        """设置编辑器"""
        # 字体设置
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        # 样式设置
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setTabStopDistance(40)

        # 连接信号
        self.textChanged.connect(self.on_text_changed)

    def setup_auto_complete(self):
        """设置自动补全"""
        # 创建自动补全定时器
        self.completion_timer = QTimer()
        self.completion_timer.setSingleShot(True)
        self.completion_timer.timeout.connect(self.trigger_auto_complete)

    def set_workbook_manager(self, workbook_manager: WorkbookManager):
        """设置工作簿管理器"""
        self.workbook_manager = workbook_manager

    def keyPressEvent(self, event):
        """按键事件处理"""
        key = event.key()
        text = event.text()

        # 处理自动补全触发
        if text in ['[', '!', '"']:
            super().keyPressEvent(event)
            self.trigger_auto_complete()
            return

        # 处理自动补全选择
        if self.completion_popup and self.completion_popup.isVisible():
            if key in [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab]:
                self.accept_completion()
                return
            elif key == Qt.Key_Escape:
                self.completion_popup.hide()
                return

        super().keyPressEvent(event)

    def trigger_auto_complete(self):
        """触发自动补全"""
        if not self.workbook_manager:
            return

        cursor = self.textCursor()
        cursor_pos = cursor.position()

        # 获取当前行的文本
        cursor.select(QTextCursor.LineUnderCursor)
        line_text = cursor.selectedText()

        # 获取光标前的文本
        line_start = cursor.selectionStart()
        prefix_pos = cursor_pos - line_start
        prefix_text = line_text[:prefix_pos]

        # 分析需要什么类型的补全
        completion_type = self.analyze_completion_context(prefix_text)

        if completion_type:
            global_pos = self.mapToGlobal(self.cursorRect().bottomLeft())
            self.show_completion_popup(completion_type, global_pos)

    def analyze_completion_context(self, text: str) -> Optional[str]:
        """分析补全上下文"""
        if text.endswith('['):
            return "sheet_names"
        elif ':"' in text and text.endswith('"'):
            # 提取工作表名
            match = re.search(r'\[([^\]]+):"[^"]*$', text)
            if match:
                return f"items:{match.group(1)}"
        elif text.endswith(']('):
            return "cell_addresses"

        return None

    def show_completion_popup(self, completion_type: str, position: QPoint):
        """显示补全弹窗"""
        if not self.completion_popup:
            self.completion_popup = CompletionPopup(self)

        # 获取补全项
        items = self.get_completion_items(completion_type)

        if items:
            self.completion_popup.set_items(items)
            self.completion_popup.move(position)
            self.completion_popup.show()

    def get_completion_items(self, completion_type: str) -> List[str]:
        """获取补全项"""
        if not self.workbook_manager:
            return []

        if completion_type == "sheet_names":
            return list(self.workbook_manager.worksheets.keys())

        elif completion_type.startswith("items:"):
            sheet_name = completion_type[6:]  # 移除 "items:" 前缀
            items = []
            for source in self.workbook_manager.source_items.values():
                if source.sheet_name == sheet_name:
                    items.append(source.name)
            return items

        elif completion_type == "cell_addresses":
            # 提供常见的单元格地址
            addresses = []
            for col in ['A', 'B', 'C', 'D', 'E']:
                for row in range(1, 21):
                    addresses.append(f"{col}{row}")
            return addresses

        return []

    def accept_completion(self):
        """接受补全"""
        if not self.completion_popup or not self.completion_popup.isVisible():
            return

        selected_item = self.completion_popup.get_selected_item()
        if selected_item:
            self.insert_completion(selected_item)

        self.completion_popup.hide()

    def insert_completion(self, text: str):
        """插入补全文本"""
        cursor = self.textCursor()

        # 根据上下文插入不同的格式
        current_text = self.toPlainText()
        cursor_pos = cursor.position()

        # 分析当前位置的上下文
        if cursor_pos > 0 and current_text[cursor_pos - 1] == '[':
            # 工作表名补全
            cursor.insertText(f'{text}:"')
        elif ':"' in current_text[:cursor_pos] and current_text[cursor_pos - 1] == '"':
            # 项目名补全
            cursor.insertText(f'{text}"]("")')
            # 将光标移动到括号内
            new_pos = cursor.position() - 2
            cursor.setPosition(new_pos)
            self.setTextCursor(cursor)
        elif cursor_pos > 0 and current_text[cursor_pos - 1:cursor_pos + 1] == '](':
            # 单元格地址补全
            cursor.insertText(text)
        else:
            cursor.insertText(text)

    def on_text_changed(self):
        """文本变化处理"""
        text = self.toPlainText()
        self.formulaChanged.emit(text)

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasFormat("application/x-sourceitem"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasFormat("application/x-sourceitem"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """拖放事件"""
        if event.mimeData().hasFormat("application/x-sourceitem"):
            # 获取拖放的引用文本
            reference_text = event.mimeData().data("application/x-sourceitem").data().decode()

            # 在当前光标位置插入引用
            cursor = self.textCursor()
            cursor.insertText(reference_text)

            event.acceptProposedAction()
        else:
            event.ignore()


class CompletionPopup(QListWidget):
    """自动补全弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_popup()

    def setup_popup(self):
        """设置弹窗"""
        self.setWindowFlags(Qt.Popup)
        self.setMaximumHeight(200)
        self.setMinimumWidth(200)

        # 样式设置
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                background-color: white;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
        """)

    def set_items(self, items: List[str]):
        """设置补全项"""
        self.clear()
        for item in items:
            self.addItem(item)

        if items:
            self.setCurrentRow(0)

    def get_selected_item(self) -> Optional[str]:
        """获取选中的项"""
        current_item = self.currentItem()
        return current_item.text() if current_item else None

    def keyPressEvent(self, event):
        """按键事件"""
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.parent().accept_completion()
        elif event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.parent().accept_completion()


class FormulaSyntaxHighlighter(QSyntaxHighlighter):
    """公式语法高亮器 - 增强版"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_highlighting_rules()

    def setup_highlighting_rules(self):
        """设置高亮规则"""
        self.highlighting_rules = []

        # 工作表引用格式: [工作表名]
        sheet_format = QTextCharFormat()
        sheet_format.setForeground(QColor(0, 120, 215))  # 蓝色
        sheet_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((r'\[[^\]]+\](?=:)', sheet_format))

        # 项目名引用格式: "项目名"
        item_format = QTextCharFormat()
        item_format.setForeground(QColor(0, 128, 0))  # 绿色
        self.highlighting_rules.append((r'"[^"]*"', item_format))

        # 单元格地址格式: (A1)
        cell_format = QTextCharFormat()
        cell_format.setForeground(QColor(128, 0, 128))  # 紫色
        self.highlighting_rules.append((r'\([A-Z]+\d+\)', cell_format))

        # 运算符
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor(255, 140, 0))  # 橙色
        operator_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((r'[+\-*/()]', operator_format))

        # 数字
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(181, 137, 0))  # 金色
        self.highlighting_rules.append((r'\b\d+\.?\d*\b', number_format))

        # 错误高亮（未闭合的引用等）
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(255, 0, 0))  # 红色
        error_format.setUnderlineStyle(QTextCharFormat.WaveUnderline)
        error_format.setUnderlineColor(QColor(255, 0, 0))

    def highlightBlock(self, text):
        """应用语法高亮"""
        for pattern, format_obj in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format_obj)

        # 检查语法错误
        self.highlight_errors(text)

    def highlight_errors(self, text):
        """高亮语法错误"""
        error_format = QTextCharFormat()
        error_format.setUnderlineStyle(QTextCharFormat.WaveUnderline)
        error_format.setUnderlineColor(QColor(255, 0, 0))

        # 检查未闭合的引用
        open_brackets = text.count('[')
        close_brackets = text.count(']')
        if open_brackets != close_brackets:
            # 高亮整行作为错误
            self.setFormat(0, len(text), error_format)

        # 检查未闭合的引号
        if text.count('"') % 2 != 0:
            self.setFormat(0, len(text), error_format)


class FormulaEditorDelegate(QStyledItemDelegate):
    """公式编辑器委托"""

    def __init__(self, workbook_manager: Optional[WorkbookManager] = None, parent=None):
        super().__init__(parent)
        self.workbook_manager = workbook_manager

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        """创建编辑器"""
        if index.column() == 2:  # 公式列
            editor = FormulaEditor(parent)
            editor.set_workbook_manager(self.workbook_manager)

            # 设置编辑器大小
            editor.setMaximumHeight(100)
            editor.setMinimumHeight(60)

            return editor

        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        """设置编辑器数据"""
        if isinstance(editor, FormulaEditor):
            value = index.model().data(index, Qt.EditRole)
            editor.setPlainText(str(value) if value else "")
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model, index: QModelIndex):
        """设置模型数据"""
        if isinstance(editor, FormulaEditor):
            text = editor.toPlainText()
            model.setData(index, text, Qt.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        """更新编辑器几何形状"""
        if isinstance(editor, FormulaEditor):
            # 扩大编辑器区域
            rect = option.rect
            rect.setHeight(max(rect.height(), 80))
            editor.setGeometry(rect)
        else:
            super().updateEditorGeometry(editor, option, index)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """绘制单元格"""
        if index.column() == 2:  # 公式列
            # 应用语法高亮显示
            formula_text = index.model().data(index, Qt.DisplayRole)

            if formula_text:
                # 创建文档并应用语法高亮
                doc = QTextDocument()
                doc.setPlainText(str(formula_text))

                highlighter = FormulaSyntaxHighlighter(doc)

                # 设置文档格式
                doc.setDefaultFont(option.font)
                doc.setTextWidth(option.rect.width())

                # 绘制文档
                painter.save()
                painter.translate(option.rect.topLeft())
                doc.drawContents(painter)
                painter.restore()

                return

        super().paint(painter, option, index)


class SearchableSourceTree(DragDropTreeView):
    """可搜索的来源项树（增强版）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_search()
        self.setup_enhanced_display()

        # 数据存储（新增）
        self.all_source_items = {}
        self.current_sheet = "全部工作表"

    def setup_search(self):
        """设置搜索功能（新增下拉菜单模式）"""
        # 创建搜索框
        self.search_widget = QWidget()
        layout = QVBoxLayout(self.search_widget)

        # 工作表选择区域（新增）
        sheet_control_layout = QHBoxLayout()

        # 工作表选择下拉菜单
        self.sheet_label = QLabel("选择工作表:")
        self.sheet_combo = QComboBox()
        self.sheet_combo.addItem("全部工作表")
        self.sheet_combo.currentTextChanged.connect(self.on_sheet_changed)

        sheet_control_layout.addWidget(self.sheet_label)
        sheet_control_layout.addWidget(self.sheet_combo)
        sheet_control_layout.addStretch()

        layout.addLayout(sheet_control_layout)

        # 搜索控制区域
        search_control_layout = QHBoxLayout()

        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("搜索来源项...")
        self.search_line.textChanged.connect(self.filter_items)
        search_control_layout.addWidget(self.search_line)

        # 显示选项
        self.show_hierarchy_btn = QPushButton("🌳 层级")
        self.show_hierarchy_btn.setCheckable(True)
        self.show_hierarchy_btn.setChecked(True)
        self.show_hierarchy_btn.toggled.connect(self.toggle_hierarchy_display)
        search_control_layout.addWidget(self.show_hierarchy_btn)

        self.show_all_columns_btn = QPushButton("📊 全列")
        self.show_all_columns_btn.setCheckable(True)
        self.show_all_columns_btn.setChecked(False)
        self.show_all_columns_btn.toggled.connect(self.toggle_column_display)
        search_control_layout.addWidget(self.show_all_columns_btn)

        layout.addLayout(search_control_layout)
        layout.addWidget(self)

    def setup_enhanced_display(self):
        """设置增强显示"""
        # 设置多列显示
        self.setHeaderHidden(False)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)

        # 设置列标题
        self.default_headers = ["名称", "科目代码", "层级", "工作表", "主要数值"]
        self.extended_headers = ["名称", "科目代码", "层级", "工作表", "主要数值",
                               "年初借方", "年初贷方", "期初借方", "期初贷方",
                               "本期借方", "本期贷方", "期末借方", "期末贷方"]

        # 初始使用默认列头
        self.current_headers = self.default_headers

    def populate_source_items(self, source_items: Dict[str, Any]):
        """填充来源项数据（支持下拉菜单模式）"""
        if not source_items:
            return

        # 保存所有数据
        self.all_source_items = source_items

        # 更新下拉菜单选项
        self._update_sheet_combo(source_items)

        # 显示当前选择的数据
        self.refresh_display()

    def _update_sheet_combo(self, source_items: Dict[str, Any]):
        """更新工作表下拉菜单选项"""
        # 收集所有工作表名称
        sheet_names = set()
        for item in source_items.values():
            if hasattr(item, 'sheet_name'):
                sheet_names.add(item.sheet_name)

        # 更新下拉菜单
        current_selection = self.sheet_combo.currentText()
        self.sheet_combo.clear()

        sorted_sheets = sorted(sheet_names)
        for sheet_name in sorted_sheets:
            self.sheet_combo.addItem(sheet_name)

        # 设置默认选择为第一个有数据的工作表
        if sorted_sheets:
            if current_selection in sorted_sheets:
                self.sheet_combo.setCurrentText(current_selection)
            else:
                # 默认选择第一个工作表
                first_sheet = sorted_sheets[0]
                self.sheet_combo.setCurrentText(first_sheet)
                self.current_sheet = first_sheet

    

    def _add_hierarchical_items(self, parent_node: QStandardItem, items: List):
        """添加层级项目"""
        # 构建层级树
        level_map = {}  # account_code -> item_node

        for item in items:
            row_items = self._create_item_row(item)
            item_node = row_items[0]

            account_code = getattr(item, 'account_code', '')
            level = getattr(item, 'hierarchy_level', 0)
            parent_code = getattr(item, 'parent_code', '')

            level_map[account_code] = (item_node, row_items)

            # 寻找父节点
            parent_found = False
            if parent_code and parent_code in level_map:
                parent_item_node, _ = level_map[parent_code]
                parent_item_node.appendRow(row_items)
                parent_found = True

            if not parent_found:
                parent_node.appendRow(row_items)

    def _add_flat_items(self, parent_node: QStandardItem, items: List):
        """添加平级项目"""
        for item in items:
            row_items = self._create_item_row(item)
            parent_node.appendRow(row_items)

    def _create_item_row(self, item) -> List[QStandardItem]:
        """创建项目行"""
        # 基本信息
        name_item = QStandardItem(getattr(item, 'full_name_with_indent', item.name))
        name_item.setEditable(False)
        name_item.setData(item, Qt.UserRole)

        account_code_item = QStandardItem(getattr(item, 'account_code', ''))
        account_code_item.setEditable(False)

        level_item = QStandardItem(str(getattr(item, 'hierarchy_level', 0)))
        level_item.setEditable(False)

        sheet_item = QStandardItem(item.sheet_name)
        sheet_item.setEditable(False)

        value_item = QStandardItem(self._format_value(item.value))
        value_item.setEditable(False)

        row_items = [name_item, account_code_item, level_item, sheet_item, value_item]

        # 如果显示扩展列，添加数据列
        if self.show_all_columns_btn.isChecked():
            data_columns = getattr(item, 'data_columns', {})

            # 科目余额表相关列
            trial_balance_keys = [
                'debit_年初余额', 'credit_年初余额',
                'debit_期初余额', 'credit_期初余额',
                'debit_本期发生额', 'credit_本期发生额',
                'debit_期末余额', 'credit_期末余额'
            ]

            for key in trial_balance_keys:
                value = data_columns.get(key, '')
                col_item = QStandardItem(self._format_value(value))
                col_item.setEditable(False)
                row_items.append(col_item)

        return row_items

    def _format_value(self, value) -> str:
        """格式化数值显示"""
        if value is None or value == '':
            return ''

        if isinstance(value, (int, float)):
            if value == 0:
                return '0'
            elif abs(value) >= 10000:
                return f"{value:,.0f}"
            else:
                return f"{value:.2f}"

        return str(value)

    def toggle_hierarchy_display(self, show_hierarchy: bool):
        """切换层级显示"""
        # 重新填充数据以应用层级显示设置
        # 这里需要从父组件获取数据重新填充
        pass

    def toggle_column_display(self, show_all: bool):
        """切换列显示"""
        if show_all:
            self.current_headers = self.extended_headers
        else:
            self.current_headers = self.default_headers

        # 重新填充数据以应用新的列头
        current_model = self.model()
        if current_model:
            current_model.setHorizontalHeaderLabels(self.current_headers)
            # 这里需要重新填充数据来匹配新的列结构

    def _adjust_column_widths(self):
        """调整列宽"""
        if self.model():
            header = self.header()
            # 名称列自适应内容
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            # 其他列固定宽度
            for i in range(1, self.model().columnCount()):
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                self.setColumnWidth(i, 100)

    def filter_items(self, text: str):
        """过滤项目（增强版）"""
        model = self.model()
        if not model or not text.strip():
            # 显示所有项目
            self._show_all_items(model)
            return

        # 隐藏不匹配的项目
        self._filter_model_items(model, text.lower())

    def _show_all_items(self, model):
        """显示所有项目"""
        for i in range(model.rowCount()):
            self.setRowHidden(i, QModelIndex(), False)
            self._show_all_children(model.item(i))

    def _show_all_children(self, parent_item):
        """递归显示所有子项"""
        for i in range(parent_item.rowCount()):
            child_item = parent_item.child(i)
            parent_index = parent_item.index()
            self.setRowHidden(i, parent_index, False)
            self._show_all_children(child_item)

    def _filter_model_items(self, model, filter_text: str):
        """过滤模型项目"""
        for i in range(model.rowCount()):
            parent_item = model.item(i)
            has_visible_children = self._filter_children(parent_item, filter_text)

            # 如果有可见子项或自身匹配，则显示
            parent_matches = filter_text in parent_item.text().lower()
            self.setRowHidden(i, QModelIndex(), not (has_visible_children or parent_matches))

    def _filter_children(self, parent_item, filter_text: str) -> bool:
        """过滤子项目，返回是否有可见子项"""
        has_visible = False

        for i in range(parent_item.rowCount()):
            child_item = parent_item.child(i)
            child_matches = filter_text in child_item.text().lower()

            # 递归检查子项的子项
            has_visible_grandchildren = self._filter_children(child_item, filter_text)

            is_visible = child_matches or has_visible_grandchildren
            parent_index = parent_item.index()
            self.setRowHidden(i, parent_index, not is_visible)

            if is_visible:
                has_visible = True

        return has_visible

    def get_search_widget(self) -> QWidget:
        """获取包含搜索框的组件"""
        return self.search_widget

    def on_sheet_changed(self, sheet_name: str):
        """处理工作表选择变化"""
        self.current_sheet = sheet_name
        self.refresh_display()

    def refresh_display(self):
        """刷新显示内容"""
        if not self.all_source_items:
            return

        # 根据当前选择的工作表过滤数据
        filtered_items = {
            key: item for key, item in self.all_source_items.items()
            if item.sheet_name == self.current_sheet
        }

        # 根据过滤后的数据更新显示
        self._populate_filtered_items(filtered_items)

    def _populate_filtered_items(self, source_items: Dict[str, Any]):
        """填充过滤后的数据（单sheet模式）"""
        if not source_items:
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(["项目名称", "数据列"])
            self.setModel(model)
            return

        model = QStandardItemModel()

        # 显示该sheet的所有数据列
        headers = self._get_sheet_specific_headers(source_items)
        model.setHorizontalHeaderLabels(headers)

        # 直接显示项目（不再包装在sheet节点下）
        items = list(source_items.values())
        if any(hasattr(item, 'hierarchy_level') and item.hierarchy_level > 0 for item in items):
            self._add_direct_hierarchical_items(model, items)
        else:
            self._add_direct_flat_items(model, items)

        self.setModel(model)
        self._adjust_column_widths()

    def _get_sheet_specific_headers(self, source_items: Dict[str, Any]) -> List[str]:
        """获取特定工作表的列头（基于表类型规则）"""
        if not source_items:
            return ["项目名称"]

        # 获取sheet名称以检测表类型
        sheet_name = ""
        for item in source_items.values():
            if hasattr(item, 'sheet_name'):
                sheet_name = item.sheet_name
                break

        # 导入表列规则系统
        from utils.table_column_rules import TableColumnRules

        # 检测表类型
        table_type = TableColumnRules.detect_table_type(sheet_name) if sheet_name else None

        if table_type:
            # 使用规则系统获取标准列头
            headers = TableColumnRules.get_display_headers(table_type, include_item_name=True)
            return headers
        else:
            # 降级到原有逻辑：收集该工作表中所有可能的数据列
            all_columns = set()
            for item in source_items.values():
                if hasattr(item, 'data_columns') and item.data_columns:
                    all_columns.update(item.data_columns.keys())

            # 生成列头
            headers = ["项目名称"]
            if all_columns:
                # 按一定顺序排列常见的列
                common_orders = [
                    "年初余额_借方", "年初余额_贷方", "年初余额_合计",
                    "期初余额_借方", "期初余额_贷方", "期初余额_合计",
                    "本期发生额_借方", "本期发生额_贷方", "本期发生额_合计",
                    "期末余额_借方", "期末余额_贷方", "期末余额_合计"
                ]
                ordered_columns = []
                for col in common_orders:
                    if col in all_columns:
                        ordered_columns.append(col)
                        all_columns.remove(col)
                # 添加剩余的列
                ordered_columns.extend(sorted(all_columns))
                headers.extend(ordered_columns)

            return headers

    def _add_direct_hierarchical_items(self, model: QStandardItemModel, items: List[Any]):
        """直接添加层级项目到模型（不使用sheet节点）"""
        # 按原始行号排序，保持原sheet顺序
        sorted_items = sorted(items, key=lambda x: getattr(x, 'row', 0))

        for item in sorted_items:
            row_items = self._create_item_row_enhanced(item)
            model.appendRow(row_items)

    def _add_direct_flat_items(self, model: QStandardItemModel, items: List[Any]):
        """直接添加平面项目到模型（不使用sheet节点）"""
        # 按原始行号排序，保持原sheet顺序
        sorted_items = sorted(items, key=lambda x: getattr(x, 'row', 0))

        for item in sorted_items:
            row_items = self._create_item_row_enhanced(item)
            model.appendRow(row_items)

    def _create_item_row_enhanced(self, item: Any) -> List[QStandardItem]:
        """创建增强的数据行（支持多列数据）"""
        row_items = []

        # 导入表列规则系统
        from utils.table_column_rules import TableColumnRules

        # 获取sheet名称以检测表类型
        sheet_name = getattr(item, 'sheet_name', '')
        table_type = TableColumnRules.detect_table_type(sheet_name) if sheet_name else None

        # 第一列：总是显示标识符（科目代码、级别等）
        first_col_value = ""
        if table_type and table_type in ["科目余额表", "试算平衡表"]:
            # 科目余额表和试算平衡表显示科目代码
            first_col_value = getattr(item, 'account_code', '')
        else:
            # 其他表显示层级或行号
            level = getattr(item, 'hierarchy_level', 0)
            if level > 0:
                first_col_value = str(level)
            else:
                # 如果没有层级，显示行号
                first_col_value = str(getattr(item, 'row', ''))

        first_item = QStandardItem(first_col_value)
        first_item.setEditable(False)
        row_items.append(first_item)

        # 第二列：总是显示项目名称（包含层级缩进）
        name_item = QStandardItem(str(getattr(item, 'name', '')))
        name_item.setEditable(False)
        name_item.setData(item, Qt.UserRole)

        # 设置层级缩进显示
        if hasattr(item, 'hierarchy_level') and item.hierarchy_level > 0:
            indent = "  " * item.hierarchy_level
            display_name = f"{indent}{getattr(item, 'name', '')}"
            name_item.setText(display_name)

        row_items.append(name_item)

        # 后续列：显示数据列
        if table_type and hasattr(item, 'data_columns') and item.data_columns:
            # 使用规则系统获取数据列
            column_keys = TableColumnRules.get_ordered_column_keys(table_type)
            # 跳过第一个键（已作为第一列处理）
            data_keys = column_keys[1:] if len(column_keys) > 1 else column_keys

            for key in data_keys:
                value = item.data_columns.get(key, '')
                formatted_value = TableColumnRules.format_column_value(value)
                data_item = QStandardItem(formatted_value)
                data_item.setEditable(False)
                row_items.append(data_item)
        elif hasattr(item, 'data_columns') and item.data_columns:
            # 没有表类型规则，使用通用逻辑
            # 获取当前列头（跳过前两列：标识符和项目名称）
            current_headers = self._get_sheet_specific_headers({item.id: item})
            data_headers = current_headers[2:] if len(current_headers) > 2 else []

            for header in data_headers:
                value = item.data_columns.get(header, '')
                data_item = QStandardItem(str(value) if value is not None else '')
                data_item.setEditable(False)
                row_items.append(data_item)
        else:
            # 没有多列数据，使用主要数值
            value = getattr(item, 'value', '')
            data_item = QStandardItem(str(value) if value is not None else '')
            data_item.setEditable(False)
            row_items.append(data_item)

        return row_items


class PropertyInspector(QWidget):
    """属性检查器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_item = None

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("属性详情")
        title_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(title_label)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.property_layout = QVBoxLayout(scroll_widget)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

    def update_properties(self, item: Any):
        """更新属性显示"""
        self.current_item = item

        # 清空现有属性
        while self.property_layout.count():
            child = self.property_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not item:
            return

        # 显示属性
        if isinstance(item, TargetItem):
            self.show_target_properties(item)
        elif isinstance(item, SourceItem):
            self.show_source_properties(item)

    def show_target_properties(self, item: TargetItem):
        """显示目标项属性"""
        properties = [
            ("ID", item.id),
            ("名称", item.name),
            ("原始文本", item.original_text),
            ("工作表", item.sheet_name),
            ("行号", str(item.row)),
            ("层级", str(item.level)),
            ("目标单元格", item.target_cell_address),
            ("是否为空目标", "是" if item.is_empty_target else "否"),
            ("显示序号", item.display_index),
            ("缩进级别", str(item.indentation_level)),
            ("父项目ID", item.parent_id or "无"),
            ("子项目数", str(len(item.children_ids))),
            ("提取时间", item.extracted_time.strftime("%Y-%m-%d %H:%M:%S")),
            ("备注", item.notes or "无")
        ]

        self.add_property_group("目标项属性", properties)

    def show_source_properties(self, item: SourceItem):
        """显示来源项属性"""
        properties = [
            ("ID", item.id),
            ("名称", item.name),
            ("工作表", item.sheet_name),
            ("单元格地址", item.cell_address),
            ("行号", str(item.row)),
            ("列", item.column),
            ("数值", str(item.value) if item.value is not None else "无"),
            ("原始文本", item.original_text),
            ("值类型", item.value_type),
            ("是否计算值", "是" if item.is_calculated else "否"),
            ("引用字符串", item.to_reference_string()),
            ("提取时间", item.extracted_time.strftime("%Y-%m-%d %H:%M:%S")),
            ("备注", item.notes or "无")
        ]

        self.add_property_group("来源项属性", properties)

    def add_property_group(self, title: str, properties: List[Tuple[str, str]]):
        """添加属性组"""
        group_box = QGroupBox(title)
        group_layout = QVBoxLayout(group_box)

        for name, value in properties:
            prop_layout = QHBoxLayout()

            name_label = QLabel(f"{name}:")
            name_label.setMinimumWidth(80)
            name_label.setFont(QFont("", 9, QFont.Bold))

            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

            prop_layout.addWidget(name_label)
            prop_layout.addWidget(value_label, 1)

            group_layout.addLayout(prop_layout)

        self.property_layout.addWidget(group_box)


def create_advanced_formula_editor(workbook_manager: WorkbookManager, parent=None) -> QWidget:
    """创建高级公式编辑器组件"""
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)

    # 工具栏
    toolbar_layout = QHBoxLayout()
    validate_btn = QPushButton("验证公式")
    clear_btn = QPushButton("清空")
    help_btn = QPushButton("帮助")

    toolbar_layout.addWidget(validate_btn)
    toolbar_layout.addWidget(clear_btn)
    toolbar_layout.addStretch()
    toolbar_layout.addWidget(help_btn)

    layout.addLayout(toolbar_layout)

    # 公式编辑器
    editor = FormulaEditor()
    editor.set_workbook_manager(workbook_manager)

    # 添加语法高亮
    highlighter = FormulaSyntaxHighlighter(editor.document())

    layout.addWidget(QLabel("公式编辑器:"))
    layout.addWidget(editor)

    # 状态显示
    status_label = QLabel("就绪")
    layout.addWidget(status_label)

    # 连接信号
    validate_btn.clicked.connect(lambda: validate_formula(editor, status_label))
    clear_btn.clicked.connect(editor.clear)

    return widget


def validate_formula(editor: FormulaEditor, status_label: QLabel):
    """验证公式"""
    formula = editor.toPlainText()

    if not formula.strip():
        status_label.setText("公式为空")
        return

    try:
        # 解析公式引用
        references = parse_formula_references_v2(formula)

        if references:
            status_label.setText(f"公式有效 - 包含 {len(references)} 个引用")
        else:
            status_label.setText("警告 - 公式中无引用")

    except Exception as e:
        status_label.setText(f"公式无效: {str(e)}")


class FormulaEditDialog(QDialog):
    """公式编辑对话框 - 双击弹出的高级公式编辑窗口"""

    def __init__(self, target_item, workbook_manager, parent=None):
        super().__init__(parent)
        self.target_item = target_item
        self.workbook_manager = workbook_manager

        # 初始化计算引擎
        from modules.calculation_engine import CalculationEngine
        self.calculation_engine = CalculationEngine(workbook_manager)

        self.current_formula = ""
        self.init_ui()
        self.load_current_formula()
        self.load_sheet_data()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"编辑公式 - {self.target_item.name}")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # 公式输入行
        formula_group = QGroupBox("公式编辑")
        formula_layout = QVBoxLayout(formula_group)

        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("请输入公式，如：[工作表1]:D16 + [工作表2]:D17")
        self.formula_input.textChanged.connect(self.on_formula_changed)

        # 添加语法高亮
        formula_layout.addWidget(QLabel("公式:"))
        formula_layout.addWidget(self.formula_input)

        # 快捷按钮
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("+ 加")
        self.subtract_btn = QPushButton("- 减")
        self.multiply_btn = QPushButton("× 乘")
        self.divide_btn = QPushButton("÷ 除")
        self.bracket_btn = QPushButton("( )")

        self.add_btn.clicked.connect(lambda: self.insert_operator(" + "))
        self.subtract_btn.clicked.connect(lambda: self.insert_operator(" - "))
        self.multiply_btn.clicked.connect(lambda: self.insert_operator(" * "))
        self.divide_btn.clicked.connect(lambda: self.insert_operator(" / "))
        self.bracket_btn.clicked.connect(lambda: self.insert_operator("()"))

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.subtract_btn)
        button_layout.addWidget(self.multiply_btn)
        button_layout.addWidget(self.divide_btn)
        button_layout.addWidget(self.bracket_btn)
        button_layout.addStretch()

        formula_layout.addLayout(button_layout)
        layout.addWidget(formula_group)

        # 数据选择区域
        data_splitter = QSplitter(Qt.Horizontal)

        # 左侧：Sheet选择和数据列表
        data_group = QGroupBox("数据选择")
        data_layout = QVBoxLayout(data_group)

        # Sheet选择
        sheet_layout = QHBoxLayout()
        sheet_layout.addWidget(QLabel("工作表:"))
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentTextChanged.connect(self.on_sheet_changed)
        sheet_layout.addWidget(self.sheet_combo)
        data_layout.addLayout(sheet_layout)

        # 数据列表
        self.data_table = QTableView()
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.doubleClicked.connect(self.on_data_double_clicked)
        data_layout.addWidget(self.data_table)

        data_splitter.addWidget(data_group)

        # 右侧：操作按钮
        action_group = QGroupBox("操作")
        action_layout = QVBoxLayout(action_group)

        self.add_item_btn = QPushButton("➕ 添加选中项")
        self.add_item_btn.clicked.connect(self.add_selected_item)

        self.preview_btn = QPushButton("👁️ 预览计算")
        self.preview_btn.clicked.connect(self.preview_calculation)

        self.validate_btn = QPushButton("✅ 验证公式")
        self.validate_btn.clicked.connect(self.validate_formula)

        action_layout.addWidget(self.add_item_btn)
        action_layout.addWidget(self.preview_btn)
        action_layout.addWidget(self.validate_btn)
        action_layout.addStretch()

        data_splitter.addWidget(action_group)
        data_splitter.setSizes([600, 200])

        layout.addWidget(data_splitter)

        # 预览结果
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_label = QLabel("公式预览将在这里显示")
        self.preview_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc;")
        preview_layout.addWidget(self.preview_label)
        layout.addWidget(preview_group)

        # 对话框按钮
        button_box_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        self.apply_btn = QPushButton("应用")

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.apply_btn.clicked.connect(self.apply_formula)

        button_box_layout.addStretch()
        button_box_layout.addWidget(self.apply_btn)
        button_box_layout.addWidget(self.ok_btn)
        button_box_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_box_layout)

    def load_current_formula(self):
        """加载当前公式"""
        if self.target_item.id in self.workbook_manager.mapping_formulas:
            formula = self.workbook_manager.mapping_formulas[self.target_item.id]
            self.current_formula = formula.formula
            self.formula_input.setText(self.current_formula)

    def load_sheet_data(self):
        """加载工作表数据 - 使用计算引擎获取工作表名称"""
        # 使用计算引擎获取工作表名称
        sheet_names = self.calculation_engine.get_sheet_names()
        self.sheet_combo.addItems(sheet_names)

        if sheet_names:
            self.on_sheet_changed(sheet_names[0])

    def on_sheet_changed(self, sheet_name):
        """工作表切换事件 - 使用计算引擎获取引用数据"""
        if not sheet_name:
            return

        # 创建数据模型显示该工作表的数据
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["项目名称", "单元格", "数值", "引用格式"])

        # 使用计算引擎获取该工作表的引用数据
        references = self.calculation_engine.get_available_references(sheet_name)

        for ref_info in references:
            name_item = QStandardItem(ref_info["name"])
            cell_item = QStandardItem(ref_info["cell_address"])
            value_item = QStandardItem(str(ref_info["value"]) if ref_info["value"] is not None else "")
            ref_item = QStandardItem(ref_info["reference_string"])

            model.appendRow([name_item, cell_item, value_item, ref_item])

        self.data_table.setModel(model)

        # 调整列宽
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

    def insert_operator(self, operator):
        """插入运算符"""
        cursor_pos = self.formula_input.cursorPosition()
        current_text = self.formula_input.text()

        if operator == "()":
            new_text = current_text[:cursor_pos] + "()" + current_text[cursor_pos:]
            self.formula_input.setText(new_text)
            self.formula_input.setCursorPosition(cursor_pos + 1)
        else:
            new_text = current_text[:cursor_pos] + operator + current_text[cursor_pos:]
            self.formula_input.setText(new_text)
            self.formula_input.setCursorPosition(cursor_pos + len(operator))

    def add_selected_item(self):
        """添加选中的数据项到公式"""
        selected_indexes = self.data_table.selectionModel().selectedRows()
        if not selected_indexes:
            return

        # 获取选中行的引用格式
        model = self.data_table.model()
        for index in selected_indexes:
            reference = model.item(index.row(), 3).text()  # 引用格式列

            # 添加到公式末尾
            current_text = self.formula_input.text()
            if current_text and not current_text.endswith(" "):
                current_text += " "

            self.formula_input.setText(current_text + reference)

    def on_data_double_clicked(self, index):
        """双击数据项"""
        self.add_selected_item()

    def on_formula_changed(self, text):
        """公式内容变化"""
        self.preview_calculation()

    def preview_calculation(self):
        """预览计算结果 - 使用实时计算引擎"""
        formula = self.formula_input.text().strip()
        if not formula:
            self.preview_label.setText("请输入公式")
            return

        try:
            # 使用计算引擎进行实时计算
            result = self.calculation_engine.calculate_formula_realtime(formula)

            preview_text = f"公式: {formula}\n\n"

            if result["validation"]["is_valid"]:
                preview_text += "✅ 语法验证: 通过\n"

                if result["success"]:
                    preview_text += f"🎯 计算结果: {result['value']}\n"
                    preview_text += f"⏱️ 计算耗时: {result['calculation_time']:.2f}ms\n"

                    # 显示引用信息
                    if result["references"]:
                        preview_text += f"\n📋 引用数量: {len(result['references'])} 个\n"
                        preview_text += "引用列表:\n"
                        for ref in result["references"][:5]:  # 只显示前5个
                            preview_text += f"  • {ref}\n"
                        if len(result["references"]) > 5:
                            preview_text += f"  ... 还有 {len(result['references']) - 5} 个引用\n"
                else:
                    preview_text += f"❌ 计算错误: {result['error']}\n"
            else:
                preview_text += f"❌ 语法错误: {result['validation']['error_message']}\n"

            self.preview_label.setText(preview_text)

        except Exception as e:
            self.preview_label.setText(f"预览异常: {str(e)}")

    def validate_formula(self):
        """验证公式 - 使用实时计算引擎"""
        formula = self.formula_input.text().strip()
        if not formula:
            self.preview_label.setText("公式不能为空")
            return False

        try:
            # 使用计算引擎进行验证
            result = self.calculation_engine.calculate_formula_realtime(formula)

            if result["validation"]["is_valid"] and result["success"]:
                self.preview_label.setText(f"✅ 公式验证通过\n计算结果: {result['value']}")
                return True
            else:
                error_msg = result["validation"]["error_message"] or result["error"]
                self.preview_label.setText(f"❌ 公式验证失败: {error_msg}")
                return False

        except Exception as e:
            self.preview_label.setText(f"❌ 公式验证异常: {str(e)}")
            return False

    def apply_formula(self):
        """应用公式"""
        if not self.validate_formula():
            return

        formula_text = self.formula_input.text().strip()

        # 更新或创建公式
        from models.data_models import MappingFormula, FormulaStatus
        if self.target_item.id not in self.workbook_manager.mapping_formulas:
            self.workbook_manager.mapping_formulas[self.target_item.id] = MappingFormula(
                target_id=self.target_item.id,
                formula=formula_text,
                status=FormulaStatus.USER_MODIFIED
            )
        else:
            formula = self.workbook_manager.mapping_formulas[self.target_item.id]
            formula.update_formula(formula_text, FormulaStatus.USER_MODIFIED)

        self.preview_label.setText("✅ 公式已应用")

    def accept(self):
        """确定按钮"""
        self.apply_formula()
        super().accept()

    def get_formula(self):
        """获取公式"""
        return self.formula_input.text().strip()