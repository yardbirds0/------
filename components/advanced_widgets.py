#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级交互组件 - PySide6版本
实现拖放、自动补全、语法高亮等高级交互功能
"""

from typing import Dict, List, Optional, Any, Tuple
import re

from PySide6.QtWidgets import (
    QTreeView,
    QTextEdit,
    QLineEdit,
    QCompleter,
    QAbstractItemView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QScrollArea,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QGroupBox,
    QDialog,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QHeaderView,
    QDialogButtonBox,
    QStyleOptionHeader,
    QStyle,
    QSizePolicy,
    QCheckBox,
)
from PySide6.QtCore import (
    Qt,
    QMimeData,
    QModelIndex,
    Signal,
    QStringListModel,
    QAbstractListModel,
    QTimer,
    QPoint,
    QRect,
    QSize,
)
from PySide6.QtGui import (
    QDrag,
    QPainter,
    QColor,
    QBrush,
    QFont,
    QTextCursor,
    QTextDocument,
    QSyntaxHighlighter,
    QTextCharFormat,
    QPalette,
    QPixmap,
    QFontMetrics,
    QKeySequence,
    QAction,
    QStandardItemModel,
    QStandardItem,
    QPen,
    QLinearGradient,
)

from models.data_models import TargetItem, SourceItem, WorkbookManager
from utils.excel_utils import (
    build_formula_reference_v2,
    parse_formula_references_v2,
    build_formula_reference_three_segment,
    parse_formula_references_three_segment,
    validate_formula_syntax_three_segment
)


ROW_NUMBER_COLUMN_WIDTH = 70  # "行次"列固定宽度


def ensure_interactive_header(
    header: Optional[QHeaderView], stretch_last: bool = False, minimum_size: int = 40
) -> None:
    """确保表头支持拖动列宽并可选地保持最后一列自适应"""
    if header is None:
        return

    header.setSectionsMovable(True)
    header.setSectionsClickable(True)
    header.setHighlightSections(False)
    header.setStretchLastSection(stretch_last)
    if minimum_size is not None:
        header.setMinimumSectionSize(max(1, minimum_size))


def schedule_row_resize(view: Any, delay_ms: int = 80) -> None:
    """调度在稍后执行按内容调整行高"""
    if view is None:
        return

    timer = getattr(view, "_row_resize_timer", None)
    if timer is None:
        timer = QTimer(view)
        timer.setSingleShot(True)

        def apply_resize():
            if isinstance(view, QTableView):
                view.resizeRowsToContents()
            elif isinstance(view, QTreeView):
                view.doItemsLayout()

        timer.timeout.connect(apply_resize)
        view._row_resize_timer = timer

    if timer.isActive():
        timer.stop()
    timer.start(max(10, delay_ms))


def ensure_word_wrap(view: Any, track_header: bool = True) -> None:
    """启用多行显示并自动调整行高"""
    if view is None:
        return

    if hasattr(view, "setWordWrap"):
        view.setWordWrap(True)

    if isinstance(view, QTreeView):
        view.setUniformRowHeights(False)
        view.setTextElideMode(Qt.ElideNone)
    elif isinstance(view, QTableView):
        view.setTextElideMode(Qt.ElideNone)

    header = None
    if hasattr(view, "horizontalHeader"):
        header = view.horizontalHeader()
    elif hasattr(view, "header"):
        header = view.header()

    if (
        track_header
        and header is not None
        and not getattr(view, "_row_resize_connected", False)
    ):
        header.sectionResized.connect(lambda *_: schedule_row_resize(view, 60))
        view._row_resize_connected = True

    schedule_row_resize(view, 40)


def distribute_columns_evenly(
    view: Any,
    exclude_columns: Optional[List[int]] = None,
    min_widths: Optional[Dict[int, int]] = None,
    max_widths: Optional[Dict[int, int]] = None,
) -> None:
    """
    均匀分配列宽以占满表格可用宽度

    Args:
        view: QTableView/QTreeView/QTableWidget实例
        exclude_columns: 不参与自动调整的列索引列表
        min_widths: 各列最小宽度 {column_index: min_width}
        max_widths: 各列最大宽度 {column_index: max_width}
    """
    if view is None:
        return

    # 获取表头
    header = None
    if hasattr(view, "horizontalHeader"):
        header = view.horizontalHeader()
    elif hasattr(view, "header"):
        header = view.header()

    if header is None:
        return

    # 获取列数
    if hasattr(view, "columnCount"):
        column_count = view.columnCount()
    elif hasattr(view, "model") and view.model():
        column_count = view.model().columnCount()
    else:
        return

    if column_count == 0:
        return

    # 初始化参数
    exclude_columns = exclude_columns or []
    min_widths = min_widths or {}
    max_widths = max_widths or {}

    # 计算可用宽度
    viewport_width = view.viewport().width()
    if viewport_width <= 0:
        return

    # 计算参与自动调整的列
    adjustable_columns = [i for i in range(column_count) if i not in exclude_columns]
    if not adjustable_columns:
        return

    # 计算被排除列占用的总宽度
    excluded_width = sum(
        view.columnWidth(i) if hasattr(view, "columnWidth") else header.sectionSize(i)
        for i in exclude_columns
    )

    # 可用于分配的宽度
    available_width = viewport_width - excluded_width

    # 先按内容调整列宽，获取理想宽度
    ideal_widths = {}
    for col in adjustable_columns:
        # 临时设置为ResizeToContents获取内容宽度
        old_mode = header.sectionResizeMode(col)
        header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        if hasattr(view, "resizeColumnToContents"):
            view.resizeColumnToContents(col)
        ideal_width = (
            view.columnWidth(col)
            if hasattr(view, "columnWidth")
            else header.sectionSize(col)
        )

        # 应用最小/最大宽度限制
        if col in min_widths:
            ideal_width = max(ideal_width, min_widths[col])
        if col in max_widths:
            ideal_width = min(ideal_width, max_widths[col])

        ideal_widths[col] = ideal_width
        header.setSectionResizeMode(col, old_mode)

    # 计算理想总宽度
    total_ideal_width = sum(ideal_widths.values())

    # 判断是扩展还是压缩
    # 如果理想宽度小于可用宽度，需要扩展（不应用max限制）
    # 如果理想宽度大于等于可用宽度，需要压缩（应用max限制）
    if total_ideal_width < available_width and total_ideal_width > 0:
        # 扩展场景：按比例扩展以填满空间，只应用min限制
        scale_factor = available_width / total_ideal_width
        for col in adjustable_columns:
            new_width = int(ideal_widths[col] * scale_factor)

            # 只应用最小宽度限制
            if col in min_widths:
                new_width = max(new_width, min_widths[col])

            if hasattr(view, "setColumnWidth"):
                view.setColumnWidth(col, new_width)
            else:
                header.resizeSection(col, new_width)
    else:
        # 压缩场景：使用理想宽度，应用min和max限制
        for col in adjustable_columns:
            width = ideal_widths[col]

            # 应用最小和最大宽度限制
            if col in min_widths:
                width = max(width, min_widths[col])
            if col in max_widths:
                width = min(width, max_widths[col])

            if hasattr(view, "setColumnWidth"):
                view.setColumnWidth(col, width)
            else:
                header.resizeSection(col, width)


class MultiRowHeaderView(QHeaderView):
    """支持多行与合并显示的表头视图"""

    def __init__(self, orientation: Qt.Orientation, parent=None):
        super().__init__(orientation, parent)
        self._layout: Dict[int, Dict[str, Any]] = {}
        self._row_count: int = 1
        self._painted_primary_groups: set = set()

    def set_header_layout(
        self, layout_map: Dict[int, Dict[str, Any]], row_count: int = 1
    ) -> None:
        self._layout = layout_map or {}
        self._row_count = max(1, row_count or 1)
        self.updateGeometry()
        self.viewport().update()

    def paintEvent(self, event) -> None:
        self._painted_primary_groups = set()
        super().paintEvent(event)

    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        if self.orientation() == Qt.Horizontal and self._row_count > 1:
            fm = self.fontMetrics()
            min_height = (fm.height() + 6) * self._row_count
            if hint.height() < min_height:
                hint.setHeight(min_height)
        return hint

    def sectionSizeFromContents(self, logicalIndex: int) -> QSize:
        size = super().sectionSizeFromContents(logicalIndex)
        if self.orientation() == Qt.Horizontal and self._row_count > 1:
            fm = self.fontMetrics()
            min_height = (fm.height() + 6) * self._row_count
            if size.height() < min_height:
                size.setHeight(min_height)
        return size

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int) -> None:
        layout_entry = self._layout.get(logicalIndex)
        if (
            self.orientation() != Qt.Horizontal
            or not layout_entry
            or self._row_count <= 1
        ):
            super().paintSection(painter, rect, logicalIndex)
            return

        row_count = max(1, self._row_count)
        row_heights = self._calculate_row_heights(rect.height(), row_count)

        primary_info = layout_entry.get("primary", {}) or {}
        primary_row_span = (
            max(1, min(primary_info.get("row_span", 1), row_count))
            if primary_info
            else 1
        )

        top_rect = None
        if primary_info:
            top_rect = self._compute_group_rect(
                primary_info.get("members") or [logicalIndex],
                rect,
                0,
                primary_row_span,
                row_heights,
            )

        # 🔧 修复：使用自定义背景绘制代替style().drawControl()，避免CSS冲突覆盖文字
        top_painted = False
        if (
            primary_info
            and primary_info.get("col_span", 1) > 1
            and top_rect is not None
        ):
            group_key = tuple(primary_info.get("members") or [logicalIndex])
            if (
                primary_info.get("is_group_start", True)
                or group_key not in self._painted_primary_groups
            ):
                self._draw_background(painter, top_rect)
                self._painted_primary_groups.add(group_key)
                top_painted = True
        elif top_rect is not None:
            self._draw_background(painter, top_rect)
            top_painted = True

        remaining_height = rect.height() - sum(row_heights[:primary_row_span])
        if remaining_height > 0:
            bottom_rect = QRect(
                rect.x(),
                rect.y() + sum(row_heights[:primary_row_span]),
                rect.width(),
                remaining_height,
            )
            self._draw_background(painter, bottom_rect)
        elif not top_painted:
            self._draw_background(painter, rect)

        # 绘制文字（在背景之后）
        painter.save()
        self._paint_primary_cell(
            painter, None, rect, logicalIndex, primary_info, row_heights, row_count
        )
        self._paint_secondary_cell(
            painter,
            None,
            rect,
            logicalIndex,
            layout_entry.get("secondary", {}),
            row_heights,
            row_count,
        )
        painter.restore()

    def _calculate_row_heights(self, total_height: int, total_rows: int) -> List[int]:
        if total_rows <= 0:
            return [total_height]
        base = total_height // total_rows
        remainder = total_height - base * total_rows
        heights: List[int] = []
        for idx in range(total_rows):
            extra = 1 if idx < remainder else 0
            heights.append(base + extra)
        return heights

    def _visible_members(self, members: List[int]) -> List[int]:
        visible: List[int] = []
        for logical in members:
            if logical < 0 or logical >= self.count():
                continue
            if self.isSectionHidden(logical):
                continue
            if self.visualIndex(logical) == -1:
                continue
            visible.append(logical)
        return visible

    def _compute_group_rect(
        self,
        members: List[int],
        original_rect: QRect,
        start_row: int,
        row_span: int,
        row_heights: List[int],
    ) -> Optional[QRect]:
        visible_members = self._visible_members(members)
        if not visible_members:
            return None

        positions = [
            (
                self.sectionViewportPosition(logical),
                self.sectionSize(logical),
                self.visualIndex(logical),
            )
            for logical in visible_members
        ]
        positions = [pos for pos in positions if pos[2] != -1]
        if not positions:
            return None

        positions.sort(key=lambda item: item[2])
        contiguous = all(
            positions[i + 1][2] - positions[i][2] == 1
            for i in range(len(positions) - 1)
        )
        if contiguous:
            start_x = positions[0][0]
            end_x = positions[-1][0] + positions[-1][1]
        else:
            start_x = self.sectionViewportPosition(visible_members[0])
            end_x = start_x + self.sectionSize(visible_members[0])

        y_offset = sum(row_heights[:start_row])
        height = sum(row_heights[start_row : start_row + row_span])
        if height <= 0:
            return None

        return QRect(
            int(start_x),
            original_rect.y() + int(y_offset),
            int(end_x - start_x),
            int(height),
        )

    def _draw_background(self, painter: QPainter, rect: QRect) -> None:
        """直接绘制背景，避免CSS主题冲突"""
        painter.save()

        # 创建渐变背景（glass theme效果 - 淡粉色系）
        gradient = QLinearGradient(
            rect.x(), rect.y(), rect.x(), rect.y() + rect.height()
        )
        gradient.setColorAt(0, QColor(255, 250, 253, 235))  # rgba(255, 250, 253, 0.92)
        gradient.setColorAt(1, QColor(254, 245, 251, 224))  # rgba(254, 245, 251, 0.88)

        painter.fillRect(rect, gradient)

        # 绘制边框（淡粉色系）
        painter.setPen(
            QPen(QColor(230, 200, 215, 89), 1)
        )  # rgba(230, 200, 215, 0.35) for right
        painter.drawLine(rect.topRight(), rect.bottomRight())

        painter.setPen(
            QPen(QColor(230, 200, 215, 115), 1)
        )  # rgba(230, 200, 215, 0.45) for bottom
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

        painter.restore()

    def _draw_text(
        self,
        painter: QPainter,
        rect: QRect,
        text: str,
        bold: bool = False,
        color: Optional[QColor] = None,
    ) -> None:
        if not text:
            return
        painter.save()
        font = painter.font()
        font.setPointSize(12)  # 显式设置为12pt以匹配QHeaderView::section
        if bold:
            font.setBold(True)
        painter.setFont(font)

        # 🔧 修复：强制使用深色文字并设置QPen，避免被CSS主题覆盖导致不可见
        if color is not None:
            painter.setPen(QPen(color))
        else:
            # 强制使用深色，且明确创建QPen对象
            pen = QPen(QColor(44, 62, 80))  # #2c3e50
            pen.setWidth(1)
            painter.setPen(pen)

        painter.drawText(
            rect.adjusted(4, 0, -4, 0), Qt.AlignCenter | Qt.TextWordWrap, text
        )
        painter.restore()

    def _paint_primary_cell(
        self,
        painter: QPainter,
        option: Optional[QStyleOptionHeader],
        rect: QRect,
        logical_index: int,
        primary: Dict[str, Any],
        row_heights: List[int],
        total_rows: int,
    ) -> None:
        if not primary:
            return
        members = primary.get("members") or [logical_index]
        row_span = max(1, min(primary.get("row_span", 1), total_rows))
        group_rect = self._compute_group_rect(members, rect, 0, row_span, row_heights)
        if group_rect is None:
            return

        text = primary.get("text", "")
        if primary.get("is_group_start", True) and text:
            # 🔧 修复：不传color参数，使用_draw_text中的默认深色
            self._draw_text(painter, group_rect, text, bold=True)

        if total_rows > row_span:
            divider_y = group_rect.y() + sum(row_heights[:row_span])
            painter.save()
            # 🔧 使用固定颜色代替palette，避免CSS冲突
            painter.setPen(QPen(QColor(190, 200, 215, 115), 1))
            painter.drawLine(
                group_rect.x(),
                divider_y,
                group_rect.x() + group_rect.width(),
                divider_y,
            )
            painter.restore()

    def _paint_secondary_cell(
        self,
        painter: QPainter,
        option: Optional[QStyleOptionHeader],
        rect: QRect,
        logical_index: int,
        secondary: Dict[str, Any],
        row_heights: List[int],
        total_rows: int,
    ) -> None:
        if not secondary or secondary.get("row_span", 0) <= 0:
            return
        if secondary.get("col_span", 1) > 1 and not secondary.get(
            "is_group_start", True
        ):
            return

        members = secondary.get("members") or [logical_index]
        row_span = max(1, min(secondary.get("row_span", 1), total_rows))
        start_row = max(0, total_rows - row_span)
        group_rect = self._compute_group_rect(
            members, rect, start_row, row_span, row_heights
        )
        if group_rect is None:
            return

        text = secondary.get("text", "")
        # 🔧 修复：不传color参数，使用_draw_text中的默认深色
        self._draw_text(painter, group_rect, text, bold=False)


def derive_header_layout_from_metadata(
    metadata_entries: List[Dict[str, Any]], base_offset: int = 0
) -> Tuple[Dict[int, Dict[str, Any]], int]:
    """根据列元数据生成多行表头布局"""
    if not metadata_entries:
        return {}, 1

    if not any("primary_col_span" in entry for entry in metadata_entries):
        return {}, 1

    header_rows = max(entry.get("header_row_count", 1) for entry in metadata_entries)
    has_secondary = any(
        (entry.get("secondary_header") or "") for entry in metadata_entries
    )
    split_primary = any(
        entry.get("primary_row_span", 1) < header_rows for entry in metadata_entries
    )
    row_count = 2 if header_rows >= 2 and (has_secondary or split_primary) else 1

    index_map = {
        entry.get("column_index"): idx for idx, entry in enumerate(metadata_entries)
    }
    layout: Dict[int, Dict[str, Any]] = {}

    for idx, entry in enumerate(metadata_entries):
        section_index = base_offset + idx

        primary_start_col = entry.get("primary_start_column") or entry.get(
            "column_index"
        )
        primary_span = max(1, entry.get("primary_col_span", 1))
        primary_members: List[int] = []
        for offset in range(primary_span):
            col_number = primary_start_col + offset
            if col_number in index_map:
                primary_members.append(base_offset + index_map[col_number])
        if not primary_members:
            primary_members = [section_index]

        secondary_start_col = entry.get("secondary_start_column") or entry.get(
            "column_index"
        )
        secondary_span = max(1, entry.get("secondary_col_span", 1))
        secondary_members: List[int] = []
        for offset in range(secondary_span):
            col_number = secondary_start_col + offset
            if col_number in index_map:
                secondary_members.append(base_offset + index_map[col_number])
        if not secondary_members:
            secondary_members = [section_index]

        layout[section_index] = {
            "primary": {
                "text": entry.get("primary_header", ""),
                "col_span": entry.get("primary_col_span", 1),
                "row_span": entry.get("primary_row_span", 1),
                "is_group_start": entry.get("primary_is_group_start", True),
                "members": primary_members,
            },
            "secondary": {
                "text": entry.get("secondary_header", ""),
                "col_span": entry.get("secondary_col_span", 1),
                "row_span": entry.get("secondary_row_span", 0),
                "is_group_start": entry.get("secondary_is_group_start", True),
                "members": secondary_members,
            },
        }

    if row_count < 2:
        for section_index, entry in layout.items():
            entry["secondary"] = {}

    return layout, max(1, min(2, row_count))


def apply_multirow_header(
    view: Any,
    layout_map: Dict[int, Dict[str, Any]],
    row_count: int = 1,
    stretch_last: bool = False,
) -> None:
    """在视图上应用多行表头布局"""
    header: Optional[QHeaderView] = None
    if hasattr(view, "header"):
        header = view.header()
    elif hasattr(view, "horizontalHeader"):
        header = view.horizontalHeader()

    if not isinstance(header, MultiRowHeaderView):
        return

    header.set_header_layout(layout_map, row_count)
    ensure_interactive_header(header, stretch_last=stretch_last)


class DragDropTreeView(QTreeView):
    """支持拖放的树视图组件"""

    # 自定义信号
    itemDropped = Signal(QModelIndex, str)  # 项目被拖放
    dragStarted = Signal(QModelIndex)  # 开始拖拽

    def __init__(self, parent=None):
        super().__init__(parent)
        multi_header = MultiRowHeaderView(Qt.Horizontal, self)
        self.setHeader(multi_header)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)

        ensure_interactive_header(self.header(), stretch_last=False)
        ensure_word_wrap(self)
        schedule_row_resize(self, 40)

        # 标记是否为主数据网格（用于列宽调整）
        self._is_main_grid = False
        self._fixed_columns = {}  # {column_index: width}
        self._column_constraints = {}  # {column_index: (min_width, max_width)}

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

    def resizeEvent(self, event):
        """窗口大小变化时自动调整列宽"""
        super().resizeEvent(event)
        # 延迟调整列宽，避免在初始化时出错
        if self.model() and self.model().columnCount() > 0:
            QTimer.singleShot(50, self._auto_adjust_columns)

    def _auto_adjust_columns(self):
        """自动调整列宽以占满可用空间"""
        if not self.model() or self.model().columnCount() == 0:
            return

        # 获取配置
        # 每次自动调整前清理上一轮的固定列配置，确保根据当前列集重新评估
        self._fixed_columns = {}

        exclude_columns = []
        min_widths = {}
        max_widths = {}

        # 如果是主数据网格，应用特殊的列配置
        if self._is_main_grid:
            model = self.model()
            column_count = model.columnCount() if model else 0
            headers = getattr(model, "headers", []) if model else []

            exclude_set: set[int] = set()
            detected_by_header = False
            row_number_found = False

            def get_column_name(col_index: int) -> str:
                """根据模型获取列名，优先使用headers属性"""
                name = ""
                if 0 <= col_index < len(headers) and headers[col_index]:
                    name = str(headers[col_index])
                elif model is not None:
                    try:
                        header_value = model.headerData(
                            col_index, Qt.Horizontal, Qt.DisplayRole
                        )
                    except TypeError:
                        header_value = None
                    if header_value:
                        name = str(header_value)
                return name.strip()

            def apply_fixed(col_index: int, width: int) -> None:
                if col_index < 0 or col_index >= column_count:
                    return
                self.setColumnWidth(col_index, width)
                exclude_set.add(col_index)
                self._fixed_columns[col_index] = width
                header_view = self.header() if hasattr(self, "header") else None
                if isinstance(header_view, QHeaderView):
                    header_view.setSectionResizeMode(col_index, QHeaderView.Fixed)
                    header_view.setMinimumSectionSize(
                        max(1, header_view.minimumSectionSize())
                    )

            def ensure_min_width(col_index: int, value: int) -> None:
                if col_index < 0 or col_index >= column_count:
                    return
                min_widths[col_index] = max(min_widths.get(col_index, 0), value)

            for col in range(column_count):
                column_name = get_column_name(col)
                if not column_name:
                    continue

                detected_by_header = True

                if column_name == "状态":
                    apply_fixed(col, 70)
                elif column_name == "级别":
                    apply_fixed(col, 70)
                elif (
                    "行次" in column_name
                    or "行号" in column_name
                    or "序号" in column_name
                ):
                    apply_fixed(col, ROW_NUMBER_COLUMN_WIDTH)
                    row_number_found = True
                elif "名称" in column_name or "项目" in column_name:
                    ensure_min_width(col, 200)
                elif "公式" in column_name:
                    ensure_min_width(col, 240)
                elif any(keyword in column_name for keyword in ("预览", "值", "结果")):
                    ensure_min_width(col, 120)

            if not detected_by_header and column_count > 0:
                apply_fixed(0, 70)
                if column_count > 1:
                    apply_fixed(1, 70)
                if column_count > 2:
                    ensure_min_width(2, 200)
                if column_count > 3:
                    ensure_min_width(3, 240)
                if column_count > 4:
                    ensure_min_width(4, 120)

            if not row_number_found and column_count > 0:
                # 兼容旧结构：若列名缺失但位于默认位置，则锁定该列宽度
                for candidate_index in (2, 3, 4):
                    if candidate_index >= column_count:
                        continue
                    candidate_name = get_column_name(candidate_index)
                    if not candidate_name or any(
                        keyword in candidate_name
                        for keyword in ("行次", "行号", "序号")
                    ):
                        apply_fixed(candidate_index, ROW_NUMBER_COLUMN_WIDTH)
                        row_number_found = True
                        break

            exclude_columns = list(exclude_set)
        else:
            # 其他表格（如来源项库）：应用自定义的约束
            for col, (min_w, max_w) in self._column_constraints.items():
                if min_w is not None:
                    min_widths[col] = min_w
                if max_w is not None:
                    max_widths[col] = max_w

        # 先设置固定列宽
        for col, width in self._fixed_columns.items():
            self.setColumnWidth(col, width)

        distribute_columns_evenly(
            self,
            exclude_columns=exclude_columns,
            min_widths=min_widths,
            max_widths=max_widths,
        )


class AutoResizeTableWidget(QTableWidget):
    """自动调整列宽的表格组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._resize_timer = None
        self._min_widths = {}
        self._max_widths = {}

    def set_column_constraints(
        self,
        min_widths: Optional[Dict[int, int]] = None,
        max_widths: Optional[Dict[int, int]] = None,
    ):
        """设置列的最小/最大宽度约束"""
        self._min_widths = min_widths or {}
        self._max_widths = max_widths or {}

    def resizeEvent(self, event):
        """窗口大小变化时自动调整列宽"""
        super().resizeEvent(event)
        # 延迟调整列宽，避免频繁调整
        if self._resize_timer is None:
            self._resize_timer = QTimer(self)
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._auto_adjust_columns)

        if self._resize_timer.isActive():
            self._resize_timer.stop()
        self._resize_timer.start(50)

    def _auto_adjust_columns(self):
        """自动调整列宽以占满可用空间"""
        if self.columnCount() == 0:
            return

        distribute_columns_evenly(
            self,
            exclude_columns=[],
            min_widths=self._min_widths,
            max_widths=self._max_widths,
        )


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
        if text in ["[", "!", '"']:
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
        """
        分析补全上下文 - 支持三段式引用

        三段式格式: [工作表名]![项目名]![列名]
        触发规则:
        1. 输入 [ → 补全工作表名
        2. 输入 ]![ → 补全项目名(需解析前面的工作表名)
        3. 输入 ]![]![ → 补全列名(需解析工作表名和项目名)
        """
        import re

        # 规则1: 输入 [ 触发工作表名补全
        if text.endswith("["):
            # 检查是否是三段式的开始(不是 ]![ 的一部分)
            if not text.endswith("]!["):
                return "sheets"

        # 规则2: 输入 ]![ 触发项目名补全
        if text.endswith("]!["):
            # 解析前面的工作表名
            # 匹配最后一个 [工作表名]![ 模式
            match = re.search(r'\[([^\]]+)\]!\[$', text)
            if match:
                sheet_name = match.group(1).strip()
                return f"items:{sheet_name}"

        # 规则3: 输入 ]![]![ 触发列名补全
        if text.endswith("]![]!["):
            # 解析前面的工作表名和项目名
            # 匹配最后一个 [工作表名]![项目名]![ 模式
            match = re.search(r'\[([^\]]+)\]!\[([^\]]+)\]!\[$', text)
            if match:
                sheet_name = match.group(1).strip()
                item_name = match.group(2).strip()
                return f"columns:{sheet_name}:{item_name}"

        # 兼容旧格式(v2/v3)
        if ':"' in text and text.endswith('"'):
            # 提取工作表名
            match = re.search(r'\[([^\]]+):"[^"]*$', text)
            if match:
                return f"items_old:{match.group(1)}"
        elif text.endswith("]("):
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
        """
        获取补全项 - 支持三段式

        completion_type格式:
        - "sheets": 工作表名列表
        - "items:{sheet_name}": 指定工作表的项目名列表
        - "columns:{sheet}:{item}": 指定项目的列名列表
        - "items_old:{sheet}": 旧格式兼容
        - "cell_addresses": 单元格地址列表
        """
        if not self.workbook_manager:
            return []

        # 1. 工作表名补全
        if completion_type == "sheets":
            return list(self.workbook_manager.worksheets.keys())

        # 2. 项目名补全(三段式)
        elif completion_type.startswith("items:"):
            sheet_name = completion_type[6:]  # 移除 "items:" 前缀
            items = []
            for source in self.workbook_manager.source_items.values():
                if source.sheet_name == sheet_name:
                    if source.name not in items:  # 去重
                        items.append(source.name)
            return items

        # 3. 列名补全(三段式) ⭐核心新功能
        elif completion_type.startswith("columns:"):
            parts = completion_type.split(":")
            if len(parts) >= 3:
                sheet_name = parts[1]
                item_name = parts[2]

                # 查找对应的来源项
                for source in self.workbook_manager.source_items.values():
                    if source.sheet_name == sheet_name and source.name == item_name:
                        # 从source.values字典中获取所有列名
                        if hasattr(source, 'values') and isinstance(source.values, dict):
                            return list(source.values.keys())
                        break
            return []

        # 4. 旧格式项目名补全(兼容)
        elif completion_type.startswith("items_old:"):
            sheet_name = completion_type[10:]
            items = []
            for source in self.workbook_manager.source_items.values():
                if source.sheet_name == sheet_name:
                    items.append(source.name)
            return items

        # 5. 单元格地址补全(兼容旧格式)
        elif completion_type == "cell_addresses":
            addresses = []
            for col in ["A", "B", "C", "D", "E"]:
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
        """
        插入补全文本 - 支持三段式引用

        根据上下文智能插入:
        1. 工作表名后 → 插入 ]![
        2. 项目名后 → 插入 ]![
        3. 列名后 → 插入 ]
        4. 旧格式兼容
        """
        cursor = self.textCursor()
        current_text = self.toPlainText()
        cursor_pos = cursor.position()

        # 获取光标前的文本以判断上下文
        text_before_cursor = current_text[:cursor_pos]

        # 判断1: 工作表名补全 - 检查是否刚输入了 [
        if text_before_cursor.endswith("[") and not text_before_cursor.endswith("]!["):
            # 三段式格式: 插入工作表名后加 ]![
            cursor.insertText(f'{text}]![')

        # 判断2: 项目名补全 - 检查是否刚输入了 ]![
        elif text_before_cursor.endswith("]!["):
            # 三段式格式: 插入项目名后加 ]![
            cursor.insertText(f'{text}]![')

        # 判断3: 列名补全 - 检查是否刚输入了 ]![]![
        elif text_before_cursor.endswith("]![]!["):
            # 三段式格式: 插入列名后加 ] 并在后面添加空格
            cursor.insertText(f'{text}] ')

        # 兼容旧格式1: 工作表名补全(旧格式)
        elif cursor_pos > 0 and current_text[cursor_pos - 1] == "[" and ':"' not in text_before_cursor[-10:]:
            # 旧格式: 插入 :"
            cursor.insertText(f'{text}:"')

        # 兼容旧格式2: 项目名补全(旧格式)
        elif ':"' in text_before_cursor and current_text[cursor_pos - 1] == '"':
            # 旧格式: 插入 "]("")
            cursor.insertText(f'{text}"]("")')
            # 将光标移动到括号内
            new_pos = cursor.position() - 2
            cursor.setPosition(new_pos)
            self.setTextCursor(cursor)

        # 兼容旧格式3: 单元格地址补全
        elif cursor_pos > 0 and current_text[cursor_pos - 1 : cursor_pos + 1] == "](":
            cursor.insertText(text)

        # 默认: 直接插入
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
            reference_text = (
                event.mimeData().data("application/x-sourceitem").data().decode()
            )

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
        self.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #ccc;
                background-color: white;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
        """
        )

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
        """
        设置高亮规则 - 支持三段式引用

        新格式(三段式): [工作表名]![项目名]![列名]
        旧格式兼容: [工作表名:"项目名"](单元格)
        """
        self.highlighting_rules = []

        # ==================== 三段式引用高亮 (最高优先级) ====================

        # 完整三段式引用: [工作表名]![项目名]![列名]
        three_segment_format = QTextCharFormat()
        three_segment_format.setForeground(QColor(0, 120, 215))  # 蓝色
        three_segment_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((
            r'\[([^\]]+)\]!\[([^\]]+)\]!\[([^\]]+)\]',
            three_segment_format
        ))

        # ==================== 旧格式兼容高亮 ====================

        # 工作表引用格式: [工作表名] (旧格式,仅在不是三段式时匹配)
        sheet_format = QTextCharFormat()
        sheet_format.setForeground(QColor(0, 120, 215))  # 蓝色
        sheet_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((r"\[[^\]]+\](?=:)", sheet_format))

        # 项目名引用格式: "项目名" (旧格式)
        item_format = QTextCharFormat()
        item_format.setForeground(QColor(0, 128, 0))  # 绿色
        self.highlighting_rules.append((r'"[^"]*"', item_format))

        # 单元格地址格式: (A1) (旧格式)
        cell_format = QTextCharFormat()
        cell_format.setForeground(QColor(128, 0, 128))  # 紫色
        self.highlighting_rules.append((r"\([A-Z]+\d+\)", cell_format))

        # ==================== 通用高亮 ====================

        # 运算符
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor(255, 140, 0))  # 橙色
        operator_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((r"[+\-*/()]", operator_format))

        # 数字
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(181, 137, 0))  # 金色
        self.highlighting_rules.append((r"\b\d+\.?\d*\b", number_format))

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
        open_brackets = text.count("[")
        close_brackets = text.count("]")
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

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        """创建编辑器"""
        model = index.model()
        column_meta = getattr(model, "_column_meta_at", None)
        if callable(column_meta) and column_meta(index.column()):
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

    def updateEditorGeometry(
        self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """更新编辑器几何形状"""
        if isinstance(editor, FormulaEditor):
            # 扩大编辑器区域
            rect = option.rect
            rect.setHeight(max(rect.height(), 80))
            editor.setGeometry(rect)
        else:
            super().updateEditorGeometry(editor, option, index)

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """绘制单元格"""
        model = index.model()
        column_meta = getattr(model, "_column_meta_at", None)
        if callable(column_meta) and column_meta(index.column()):
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


class ColumnConfigDialog(QDialog):
    """数据列设置对话框 - 支持拖拽排序、可见性和可编辑性控制"""

    def __init__(
        self,
        available_headers: List[str],
        current_config: Optional[List[Dict[str, Any]]],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("数据列设置")
        self.setModal(True)
        self.resize(580, 620)

        # 应用玻璃主题样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 240, 245, 0.95),
                    stop:1 rgba(245, 230, 240, 0.95)
                );
                border-radius: 12px;
            }
            QLabel {
                color: #4a4a4a;
                font-size: 11pt;
            }
            QLabel#title {
                font-size: 13pt;
                font-weight: bold;
                color: #c2185b;
            }
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(235, 145, 190, 0.3);
                border-radius: 10px;
                selection-background-color: rgba(235, 145, 190, 0.35);
                gridline-color: rgba(235, 145, 190, 0.2);
                font-size: 11pt;
            }
            QTableWidget::item:hover {
                background-color: rgba(235, 145, 190, 0.15);
            }
            QTableWidget::item:selected {
                background-color: rgba(235, 145, 190, 0.35);
            }
            QHeaderView::section {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(235, 145, 190, 0.4),
                    stop:1 rgba(235, 145, 190, 0.25)
                );
                color: #4a4a4a;
                font-weight: bold;
                font-size: 11pt;
                border: none;
                border-right: 1px solid rgba(235, 145, 190, 0.2);
                border-bottom: 1px solid rgba(235, 145, 190, 0.3);
                padding: 6px;
            }
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(235, 145, 190, 0.3),
                    stop:1 rgba(235, 145, 190, 0.2)
                );
                border: 1px solid rgba(235, 145, 190, 0.4);
                border-radius: 8px;
                color: #4a4a4a;
                font-size: 10pt;
                font-weight: 500;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(235, 145, 190, 0.45),
                    stop:1 rgba(235, 145, 190, 0.35)
                );
            }
            QPushButton:pressed {
                background: rgba(235, 145, 190, 0.5);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("数据列设置")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 提示信息
        tips = QLabel("🔹 拖拽调整显示顺序  🔹 勾选控制列的可见性和可编辑性")
        tips.setWordWrap(True)
        tips.setAlignment(Qt.AlignCenter)
        layout.addWidget(tips)

        # 批量操作按钮行
        batch_layout = QHBoxLayout()
        batch_layout.setSpacing(10)

        self.btn_all_visible = QPushButton("✓ 全部显示")
        self.btn_all_hidden = QPushButton("✗ 全部隐藏")
        self.btn_all_editable = QPushButton("✎ 全部可编辑")
        self.btn_all_readonly = QPushButton("🔒 全部只读")

        self.btn_all_visible.clicked.connect(self._set_all_visible)
        self.btn_all_hidden.clicked.connect(self._set_all_hidden)
        self.btn_all_editable.clicked.connect(self._set_all_editable)
        self.btn_all_readonly.clicked.connect(self._set_all_readonly)

        batch_layout.addWidget(self.btn_all_visible)
        batch_layout.addWidget(self.btn_all_hidden)
        batch_layout.addWidget(self.btn_all_editable)
        batch_layout.addWidget(self.btn_all_readonly)
        layout.addLayout(batch_layout)

        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["列名", "显示", "可编辑"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 100)
        self.table.setDragDropMode(QAbstractItemView.InternalMove)
        self.table.setDragEnabled(True)
        self.table.setAcceptDrops(True)
        self.table.setDropIndicatorShown(True)
        self.table.setDefaultDropAction(Qt.MoveAction)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        # 添加网格线样式
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
        """)
        self.table.setShowGrid(True)  # 确保显示网格线

        layout.addWidget(self.table)

        self._populate_table(available_headers, current_config)

        # 底部按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # 连接信号：可见性改变时更新可编辑复选框状态
        self.table.itemChanged.connect(self._on_item_changed)

    def _populate_table(
        self,
        available_headers: List[str],
        current_config: Optional[List[Dict[str, Any]]],
    ):
        """填充表格数据"""
        config_map = {}
        ordered_entries: List[Dict[str, Any]] = []

        if current_config:
            for entry in current_config:
                name = entry.get("name")
                if name in available_headers and name not in config_map:
                    config_map[name] = entry
                    ordered_entries.append(entry)

        # 添加缺失的列（使用默认值）
        readonly_columns = ["项目", "行次", "状态", "级别"]
        for header in available_headers:
            if header not in config_map:
                entry = {
                    "name": header,
                    "enabled": True,
                    "editable": header not in readonly_columns
                }
                ordered_entries.append(entry)
                config_map[header] = entry

        self.table.setRowCount(len(ordered_entries))

        # 临时阻止信号，避免填充时触发 _on_item_changed
        self.table.blockSignals(True)

        for row, entry in enumerate(ordered_entries):
            name = entry.get("name", "")
            enabled = entry.get("enabled", True)
            editable = entry.get("editable", True)

            # 列名（第0列）
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # 列名不可编辑
            self.table.setItem(row, 0, name_item)

            # ✅ 显示复选框（第1列）- 使用真正的QCheckBox widget
            visible_checkbox = QCheckBox()
            visible_checkbox.setChecked(enabled)
            visible_checkbox.setStyleSheet("""
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)
            # 创建一个容器widget来居中复选框
            visible_widget = QWidget()
            visible_layout = QHBoxLayout(visible_widget)
            visible_layout.addWidget(visible_checkbox)
            visible_layout.setAlignment(Qt.AlignCenter)
            visible_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 1, visible_widget)

            # 连接信号
            visible_checkbox.stateChanged.connect(
                lambda state, r=row: self._on_visible_changed(r, state)
            )

            # ✅ 可编辑复选框（第2列）- 使用真正的QCheckBox widget
            editable_checkbox = QCheckBox()
            editable_checkbox.setChecked(editable)
            editable_checkbox.setEnabled(enabled)  # 如果列不可见，禁用可编辑复选框
            editable_checkbox.setStyleSheet("""
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)
            # 创建一个容器widget来居中复选框
            editable_widget = QWidget()
            editable_layout = QHBoxLayout(editable_widget)
            editable_layout.addWidget(editable_checkbox)
            editable_layout.setAlignment(Qt.AlignCenter)
            editable_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 2, editable_widget)

        self.table.blockSignals(False)

    def _on_visible_changed(self, row: int, state: int):
        """当可见性复选框改变时，更新可编辑复选框的启用状态"""
        # 获取可编辑列的widget
        editable_widget = self.table.cellWidget(row, 2)
        if editable_widget:
            # 从容器中找到QCheckBox
            editable_checkbox = editable_widget.findChild(QCheckBox)
            if editable_checkbox:
                # 如果列显示，启用可编辑复选框；否则禁用
                editable_checkbox.setEnabled(state == Qt.Checked)

    def _on_item_changed(self, item: QTableWidgetItem):
        """保留此方法以避免破坏现有连接，但不再使用"""
        pass

    def _set_all_visible(self):
        """全部显示"""
        for row in range(self.table.rowCount()):
            visible_widget = self.table.cellWidget(row, 1)
            editable_widget = self.table.cellWidget(row, 2)
            if visible_widget:
                visible_checkbox = visible_widget.findChild(QCheckBox)
                if visible_checkbox:
                    visible_checkbox.setChecked(True)
            if editable_widget:
                editable_checkbox = editable_widget.findChild(QCheckBox)
                if editable_checkbox:
                    editable_checkbox.setEnabled(True)

    def _set_all_hidden(self):
        """全部隐藏"""
        for row in range(self.table.rowCount()):
            visible_widget = self.table.cellWidget(row, 1)
            editable_widget = self.table.cellWidget(row, 2)
            if visible_widget:
                visible_checkbox = visible_widget.findChild(QCheckBox)
                if visible_checkbox:
                    visible_checkbox.setChecked(False)
            if editable_widget:
                editable_checkbox = editable_widget.findChild(QCheckBox)
                if editable_checkbox:
                    editable_checkbox.setEnabled(False)

    def _set_all_editable(self):
        """全部可编辑"""
        for row in range(self.table.rowCount()):
            visible_widget = self.table.cellWidget(row, 1)
            editable_widget = self.table.cellWidget(row, 2)
            # 只有显示的列才能设置为可编辑
            if visible_widget and editable_widget:
                visible_checkbox = visible_widget.findChild(QCheckBox)
                editable_checkbox = editable_widget.findChild(QCheckBox)
                if visible_checkbox and editable_checkbox and visible_checkbox.isChecked():
                    editable_checkbox.setChecked(True)

    def _set_all_readonly(self):
        """全部只读"""
        for row in range(self.table.rowCount()):
            editable_widget = self.table.cellWidget(row, 2)
            if editable_widget:
                editable_checkbox = editable_widget.findChild(QCheckBox)
                if editable_checkbox:
                    editable_checkbox.setChecked(False)

    def get_selection(self) -> List[Dict[str, Any]]:
        """获取用户配置"""
        selection: List[Dict[str, Any]] = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            visible_widget = self.table.cellWidget(row, 1)
            editable_widget = self.table.cellWidget(row, 2)

            # 获取列名
            name = name_item.text() if name_item else ""

            # 获取可见性状态
            enabled = True
            if visible_widget:
                visible_checkbox = visible_widget.findChild(QCheckBox)
                if visible_checkbox:
                    enabled = visible_checkbox.isChecked()

            # 获取可编辑状态
            editable = True
            if editable_widget:
                editable_checkbox = editable_widget.findChild(QCheckBox)
                if editable_checkbox:
                    editable = editable_checkbox.isChecked()

            selection.append({
                "name": name,
                "enabled": enabled,
                "editable": editable,
            })
        return selection



class SearchableSourceTree(DragDropTreeView):
    """可搜索的来源项树（增强版）"""

    # 添加工作表变化信号
    sheetChanged = Signal(str)
    # 添加三段式引用插入信号
    threeSegmentReferenceRequested = Signal(str, str, str, str)  # (sheet, item, column, full_reference)

    def __init__(self, parent=None):
        # 先初始化依赖字段，确保后续初始化流程可安全访问
        self.base_headers: List[str] = []  # 删除所有基础列，改为完全动态
        self.current_headers: List[str] = []  # 初始为空
        self.all_source_items: Dict[str, Any] = {}
        self.current_sheet: Optional[str] = None
        self.available_sheets: List[str] = []
        self.sheet_column_configs: Dict[str, List[Dict[str, Any]]] = {}
        self.sheet_column_metadata: Dict[str, List[Dict[str, Any]]] = {}

        super().__init__(parent)
        self.setup_search()
        self.setup_enhanced_display()

    def setup_search(self):
        """设置搜索功能（新增下拉菜单模式）"""
        # 创建搜索框
        self.search_widget = QWidget()
        layout = QVBoxLayout(self.search_widget)

        # 工作表选择区域（新增）
        sheet_control_layout = QHBoxLayout()

        # 工作表选择下拉菜单
        self.sheet_label = QLabel("选择工作表:")
        self.sheet_label.setStyleSheet("font-size: 12pt;")
        self.sheet_combo = QComboBox()
        self.sheet_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.sheet_combo.setMinimumWidth(200)
        self.sheet_combo.setMinimumHeight(35)  # 设置下拉框最小高度为35px
        self.sheet_combo.currentTextChanged.connect(self.on_sheet_changed)

        sheet_control_layout.addWidget(self.sheet_label)
        sheet_control_layout.addWidget(self.sheet_combo, 1)  # ✅ 添加stretch factor让combobox占满空间

        layout.addLayout(sheet_control_layout)

        # 搜索控制区域
        search_control_layout = QHBoxLayout()

        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("搜索来源项...")
        self.search_line.setMinimumHeight(35)  # 设置搜索框最小高度为35px
        self.search_line.textChanged.connect(self.filter_items)
        search_control_layout.addWidget(self.search_line)

        self.column_config_btn = QPushButton("⚙️ 展示信息")
        self.column_config_btn.setToolTip("配置当前工作表显示的列并调整顺序")
        self.column_config_btn.setMinimumHeight(35)  # 按钮也设置相同高度
        self.column_config_btn.clicked.connect(self.open_column_config_dialog)
        search_control_layout.addWidget(self.column_config_btn)

        layout.addLayout(search_control_layout)
        layout.addWidget(self)

    def setup_enhanced_display(self):
        """设置增强显示"""
        # 设置多列显示
        self.setHeaderHidden(False)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        self.current_headers = []  # 初始为空，完全由元数据驱动

        ensure_interactive_header(self.header(), stretch_last=False)
        ensure_word_wrap(self)

    def open_column_config_dialog(self):
        """打开列配置弹窗"""
        sheet_name = self.current_sheet
        if not sheet_name:
            return
        # 获取当前 sheet 的可用列
        source_items = self._get_items_for_sheet(sheet_name)
        available_headers = (
            self._get_sheet_specific_headers(source_items)
            if source_items
            else self.current_headers
        )

        dialog = ColumnConfigDialog(
            available_headers, self.sheet_column_configs.get(sheet_name), self
        )
        if dialog.exec() == QDialog.Accepted:
            self.sheet_column_configs[sheet_name] = dialog.get_selection()
            self.refresh_display()

    def _get_items_for_sheet(self, sheet_name: str) -> Dict[str, Any]:
        if not sheet_name:
            sheet_name = self.available_sheets[0] if self.available_sheets else None
        if not sheet_name:
            return {}

        return {
            key: item
            for key, item in self.all_source_items.items()
            if getattr(item, "sheet_name", None) == sheet_name
        }

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

    def set_column_metadata(self, metadata: Dict[str, List[Dict[str, Any]]]):
        """设置外部提供的列元数据"""
        self.sheet_column_metadata = metadata or {}

        # 清理已失效的列配置
        valid_sheets = set(self.sheet_column_metadata.keys())
        if valid_sheets:
            self.sheet_column_configs = {
                sheet: config
                for sheet, config in self.sheet_column_configs.items()
                if sheet in valid_sheets
            }

        if self.all_source_items:
            self.refresh_display()

    def _update_sheet_combo(self, source_items: Dict[str, Any]):
        """更新工作表下拉菜单选项"""
        # 收集所有工作表名称
        sheet_names = set()
        for item in source_items.values():
            if hasattr(item, "sheet_name"):
                sheet_names.add(item.sheet_name)

        # 更新下拉菜单
        current_selection = self.sheet_combo.currentText()
        self.sheet_combo.clear()

        sorted_sheets = sorted(sheet_names)
        self.available_sheets = sorted_sheets
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
        else:
            self.current_sheet = None
            self.sheet_combo.setCurrentIndex(-1)

    def _adjust_column_widths(self):
        """调整列宽"""
        model = self.model()
        header = self.header()
        if not model or not header:
            return

        ensure_interactive_header(header, stretch_last=False)

        column_count = model.columnCount()
        if column_count == 0:
            return

        column_limits = {
            0: (80, 160),  # 级别/科目代码
            1: (220, 520),  # 项目名称
        }
        default_limits = (110, 260)

        for column in range(column_count):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            self.resizeColumnToContents(column)

            width = self.columnWidth(column)
            min_w, max_w = column_limits.get(column, default_limits)
            bounded_width = max(min_w, min(width, max_w))
            self.setColumnWidth(column, bounded_width)
            header.setSectionResizeMode(column, QHeaderView.Interactive)

    def filter_items(self, text: str):
        """过滤项目（增强版）"""
        model = self.model()
        if not model or not text.strip():
            self._clear_highlight(model)
            # 显示所有项目
            self._show_all_items(model)
            schedule_row_resize(self)
            return

        # 隐藏不匹配的项目
        self._filter_model_items(model, text.lower())
        schedule_row_resize(self)

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
        self._clear_highlight(model)
        for i in range(model.rowCount()):
            parent_item = model.item(i)
            is_visible = self._filter_item_recursive(parent_item, filter_text)
            self.setRowHidden(i, QModelIndex(), not is_visible)

    def _filter_item_recursive(self, item: QStandardItem, filter_text: str) -> bool:
        if not item:
            return False

        row_match = self._match_row(item, filter_text)
        child_visible = False

        index = item.index()
        for row in range(item.rowCount()):
            child_item = item.child(row)
            visible = self._filter_item_recursive(child_item, filter_text)
            self.setRowHidden(row, index, not visible)
            if visible:
                child_visible = True

        return row_match or child_visible

    def _match_row(self, item: QStandardItem, filter_text: str) -> bool:
        model = item.model()
        if not model:
            return False

        index = item.index()
        parent_index = index.parent()
        # 🔧 修复：使用更明显的高亮颜色，避免被主题覆盖
        highlight_color = QColor("#ffeb3b")  # 亮黄色，更加明显
        highlight_brush = QBrush(highlight_color)
        row = index.row()

        matched = False
        modified_indices = []

        for col in range(model.columnCount()):
            cell_index = model.index(row, col, parent_index)
            cell_text = model.data(cell_index, Qt.DisplayRole)
            cell_lower = str(cell_text).lower() if cell_text is not None else ""

            if filter_text in cell_lower and filter_text:
                matched = True
                # 使用QBrush设置背景色，更加可靠
                model.setData(cell_index, highlight_brush, Qt.BackgroundRole)
                modified_indices.append(cell_index)
            else:
                # 清除背景色
                model.setData(cell_index, None, Qt.BackgroundRole)
                modified_indices.append(cell_index)

        # 🔧 修复：触发视图更新，确保高亮显示
        if modified_indices:
            # 发送dataChanged信号，强制视图刷新
            top_left = modified_indices[0]
            bottom_right = modified_indices[-1]
            if hasattr(model, "dataChanged"):
                model.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])

        return matched

    def _clear_highlight(self, model: Optional[QStandardItemModel]):
        """清除所有高亮显示"""
        if not model:
            return

        modified_indices = []

        def _clear_item(item: QStandardItem):
            if not item:
                return
            idx = item.index()
            parent_idx = idx.parent()
            for col in range(model.columnCount()):
                cell_index = model.index(idx.row(), col, parent_idx)
                model.setData(cell_index, None, Qt.BackgroundRole)
                modified_indices.append(cell_index)
            for child_row in range(item.rowCount()):
                _clear_item(item.child(child_row))

        for row in range(model.rowCount()):
            _clear_item(model.item(row))

        # 🔧 修复：批量触发dataChanged信号，提升性能并确保刷新
        if modified_indices and hasattr(model, "dataChanged"):
            # 发送整个模型的dataChanged信号
            top_left = model.index(0, 0)
            bottom_right = model.index(model.rowCount() - 1, model.columnCount() - 1)
            model.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])

    def get_search_widget(self) -> QWidget:
        """获取包含搜索框的组件"""
        return self.search_widget

    def on_sheet_changed(self, sheet_name: str):
        """处理工作表选择变化"""
        self.current_sheet = sheet_name
        self.refresh_display()
        # 发出工作表变化信号，通知主窗口更新主表格列宽
        self.sheetChanged.emit(sheet_name)

    def refresh_display(self):
        """刷新显示内容"""
        if not self.all_source_items:
            return

        if not self.current_sheet and self.available_sheets:
            self.current_sheet = self.available_sheets[0]
            if self.sheet_combo.count() > 0:
                self.sheet_combo.blockSignals(True)
                self.sheet_combo.setCurrentText(self.current_sheet)
                self.sheet_combo.blockSignals(False)

        sheet_name = self.current_sheet
        if not sheet_name:
            filtered_items = {}
        else:
            filtered_items = {
                key: item
                for key, item in self.all_source_items.items()
                if getattr(item, "sheet_name", None) == sheet_name
            }

        if (
            not filtered_items
            and sheet_name
            and sheet_name not in self.available_sheets
        ):
            self.current_sheet = None
            self.refresh_display()
            return

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

        headers = self._get_sheet_specific_headers(source_items)
        active_headers = self._apply_column_config(self.current_sheet, headers)
        model.setHorizontalHeaderLabels(active_headers)
        self.current_headers = active_headers

        metadata = self._get_metadata_for_sheet(self.current_sheet or "")
        metadata_by_display = {
            entry.get("display_name"): entry
            for entry in metadata
            if entry.get("display_name")
        }
        dynamic_metadata: List[Dict[str, Any]] = [
            metadata_by_display[name]
            for name in active_headers
            if name in metadata_by_display  # 不再需要排除base_headers
        ]
        base_count = 0  # 不再有基础列，所有列都是动态的
        layout_map, row_count = derive_header_layout_from_metadata(
            dynamic_metadata, base_offset=base_count
        )

        # 直接显示项目（不再包装在sheet节点下）
        items = list(source_items.values())
        if any(
            hasattr(item, "hierarchy_level") and item.hierarchy_level > 0
            for item in items
        ):
            self._add_direct_hierarchical_items(model, items, headers, active_headers)
        else:
            self._add_direct_flat_items(model, items, headers, active_headers)

        self.setModel(model)
        apply_multirow_header(self, layout_map, row_count, stretch_last=False)
        self._adjust_column_widths()
        ensure_word_wrap(self)
        schedule_row_resize(self)

    def _get_sheet_specific_headers(self, source_items: Dict[str, Any]) -> List[str]:
        """获取特定工作表的列头（完全基于元数据动态生成）"""
        if not source_items:
            return []  # 无数据时返回空列表

        sheet_name = self.current_sheet or ""
        if not sheet_name:
            sample_item = next(iter(source_items.values()))
            sheet_name = getattr(sample_item, "sheet_name", "")

        headers = []  # 不再有基础列，完全基于元数据
        metadata = self._get_metadata_for_sheet(sheet_name)

        for entry in metadata:
            display = entry.get("display_name")
            if display and display not in headers:
                headers.append(display)

        # 如果元数据为空，从items中收集headers作为后备
        if not headers:
            extra_headers = self._collect_headers_from_items(source_items)
            headers.extend(extra_headers)

        return headers

    def _apply_column_config(self, sheet_name: str, headers: List[str]) -> List[str]:
        """应用列配置（完全基于用户配置）"""
        config = self.sheet_column_configs.get(sheet_name)
        if not config:
            return headers  # 无配置时直接返回所有headers

        selection: List[str] = []
        seen = set()

        for entry in config:
            name = entry.get("name")
            if name in headers:
                seen.add(name)
                if entry.get("enabled", True) and name not in selection:
                    selection.append(name)

        # 添加未在配置中的headers
        for header in headers:
            if header not in seen and header not in selection:
                selection.append(header)

        return selection if selection else headers

    def _default_active_headers(self, sheet_name: str, headers: List[str]) -> List[str]:
        metadata = self._get_metadata_for_sheet(sheet_name)

        data_headers = [
            entry.get("display_name")
            for entry in metadata
            if entry.get("is_data_column")
        ]
        if not data_headers:
            data_headers = [
                entry.get("display_name")
                for entry in metadata
                if entry.get("display_name")
            ]

        ordered: List[str] = []
        for base in self.base_headers:
            if base in headers and base not in ordered:
                ordered.append(base)

        for header in data_headers:
            if header in headers and header not in ordered:
                ordered.append(header)

        for header in headers:
            if header not in ordered:
                ordered.append(header)

        return ordered

    def _get_metadata_for_sheet(self, sheet_name: str) -> List[Dict[str, Any]]:
        if not self.sheet_column_metadata:
            return []

        if sheet_name and sheet_name in self.sheet_column_metadata:
            return self.sheet_column_metadata[sheet_name]

        if not sheet_name and self.available_sheets:
            first_sheet = self.available_sheets[0]
            return self.sheet_column_metadata.get(first_sheet, [])

        return []

    def _collect_headers_from_items(self, source_items: Dict[str, Any]) -> List[str]:
        headers: List[str] = []
        seen = set()
        for item in source_items.values():
            data_columns = (
                getattr(item, "data_columns", {})
                if hasattr(item, "data_columns")
                else {}
            )
            for key in data_columns.keys():
                if key not in seen:
                    headers.append(key)
                    seen.add(key)
        return headers

    def _format_value(self, value: Any) -> str:
        if value is None or value == "":
            return ""

        if isinstance(value, (int, float)):
            if value == 0:
                return "0"
            abs_value = abs(value)
            if abs_value >= 10000:
                return f"{value:,.0f}"
            return f"{value:.2f}".rstrip("0").rstrip(".")

        return str(value)

    def _add_direct_hierarchical_items(
        self,
        model: QStandardItemModel,
        items: List[Any],
        headers: List[str],
        active_headers: List[str],
    ):
        """直接添加层级项目到模型（不使用sheet节点）"""
        # 按原始行号排序，保持原sheet顺序
        sorted_items = sorted(items, key=lambda x: getattr(x, "row", 0))

        for item in sorted_items:
            row_map = self._create_item_row_enhanced(item, headers)
            row_items = [
                self._clone_item(row_map.get(header)) for header in active_headers
            ]
            model.appendRow(row_items)

    def _add_direct_flat_items(
        self,
        model: QStandardItemModel,
        items: List[Any],
        headers: List[str],
        active_headers: List[str],
    ):
        """直接添加平面项目到模型（不使用sheet节点）"""
        # 按原始行号排序，保持原sheet顺序
        sorted_items = sorted(items, key=lambda x: getattr(x, "row", 0))

        for item in sorted_items:
            row_map = self._create_item_row_enhanced(item, headers)
            row_items = [
                self._clone_item(row_map.get(header)) for header in active_headers
            ]
            model.appendRow(row_items)

    def _clone_item(self, item: Optional[QStandardItem]) -> QStandardItem:
        if item is None:
            clone = QStandardItem("")
        else:
            clone = item.clone()
        clone.setEditable(False)
        return clone

    def _create_item_row_enhanced(
        self, item: Any, headers: List[str]
    ) -> Dict[str, QStandardItem]:
        """创建增强的数据行映射（完全基于Excel元数据动态生成）"""
        row_map: Dict[str, QStandardItem] = {}

        # 获取item的data_columns字典
        data_columns = (
            getattr(item, "data_columns", {}) if hasattr(item, "data_columns") else {}
        )

        # 遍历所有headers，完全基于元数据填充
        for header in headers:
            # 尝试从data_columns获取数据
            value = data_columns.get(header, "")

            # 如果data_columns中没有，尝试从item的属性获取
            if not value and header:
                # 尝试常见的字段映射
                if header in ["名称", "项目名称", "name", "项目"]:
                    value = getattr(item, "name", "")
                elif header in ["层级", "级别", "level", "hierarchy_level"]:
                    value = getattr(item, "hierarchy_level", "")
                elif header in ["科目代码", "代码", "account_code", "code"]:
                    value = getattr(item, "account_code", "")
                elif header in ["工作表", "sheet", "sheet_name"]:
                    value = getattr(item, "sheet_name", "")
                elif header in ["数值", "值", "value"]:
                    value = getattr(item, "value", "")

            formatted = self._format_value(value)
            data_item = QStandardItem(formatted)
            data_item.setEditable(False)

            # 如果是"项目名称"或"名称"列，设置层级缩进和UserRole
            if header in ["名称", "项目名称", "name", "项目"]:
                data_item.setData(item, Qt.UserRole)
                if hasattr(item, "hierarchy_level") and item.hierarchy_level > 0:
                    indent = "  " * item.hierarchy_level
                    display_name = f"{indent}{value}" if value else indent
                    data_item.setText(display_name)

            row_map[header] = data_item

        return row_map

    def mouseDoubleClickEvent(self, event):
        """
        双击来源项弹出列名选择菜单

        需求: 用户双击来源项库中的项目时,弹出该项目所有列名的选择菜单,
             选择后将完整的三段式引用插入到当前激活的公式编辑器中
        """
        from PySide6.QtWidgets import QMenu

        # 获取双击的索引
        index = self.indexAt(event.pos())
        if not index.isValid():
            super().mouseDoubleClickEvent(event)
            return

        model = self.model()
        if not model:
            super().mouseDoubleClickEvent(event)
            return

        # 尝试多种方式获取source_item
        source_item = None

        # 方法1: 从UserRole获取(优先)
        item_data = model.data(index, Qt.UserRole)
        if item_data and hasattr(item_data, 'sheet_name'):
            source_item = item_data

        # 方法2: 从同行的其他列获取(备用)
        if not source_item:
            row = index.row()
            for col in range(model.columnCount()):
                alt_index = model.index(row, col)
                alt_data = model.data(alt_index, Qt.UserRole)
                if alt_data and hasattr(alt_data, 'sheet_name'):
                    source_item = alt_data
                    break

        # 方法3: 从all_source_items中根据显示文本查找(最后手段)
        if not source_item and self.all_source_items:
            display_text = model.data(index, Qt.DisplayRole)
            if display_text:
                # 去除缩进空格
                clean_text = str(display_text).strip()
                for item in self.all_source_items.values():
                    if item.name == clean_text or item.full_name_with_indent.strip() == clean_text:
                        source_item = item
                        break

        if not source_item:
            super().mouseDoubleClickEvent(event)
            return

        # 检查是否有可用的列
        # 优先使用values字典,其次使用data_columns
        available_columns = {}
        if hasattr(source_item, 'values') and isinstance(source_item.values, dict) and source_item.values:
            available_columns = source_item.values
        elif hasattr(source_item, 'data_columns') and isinstance(source_item.data_columns, dict) and source_item.data_columns:
            available_columns = source_item.data_columns

        if not available_columns:
            # 如果没有多列数据,提示用户
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "提示",
                f"来源项 '{source_item.name}' 没有可用的数据列\n请检查数据提取配置"
            )
            super().mouseDoubleClickEvent(event)
            return

        # 创建列名选择菜单
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                font-size: 11pt;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)

        # 添加列名选项
        for column_name, column_value in available_columns.items():
            # 显示列名和值(预览)
            display_text = f"{column_name}"  # 移除emoji避免编码问题
            if column_value is not None:
                # 格式化值显示
                if isinstance(column_value, (int, float)):
                    display_text += f"  ({column_value:,.2f})" if isinstance(column_value, float) else f"  ({column_value:,})"
                else:
                    value_str = str(column_value)[:20]  # 限制长度
                    display_text += f"  ({value_str})"

            action = menu.addAction(display_text)
            # 使用lambda闭包保存列名(确保使用原始name而非full_name_with_indent)
            action.triggered.connect(
                lambda checked=False, cn=column_name: self._insert_three_segment_reference(
                    source_item.sheet_name,
                    source_item.name,  # 使用原始name,不包含缩进
                    cn
                )
            )

        # 在鼠标位置显示菜单
        menu.exec_(event.globalPos())

    def _insert_three_segment_reference(self, sheet_name: str, item_name: str, column_name: str):
        """
        插入三段式引用到活跃的公式编辑器

        通过发送信号给main.py,由主窗口负责找到当前活跃的公式编辑器并插入引用
        """
        # 构建完整的三段式引用
        full_reference = build_formula_reference_three_segment(sheet_name, item_name, column_name)

        # 发送信号,让主窗口处理插入逻辑
        self.threeSegmentReferenceRequested.emit(sheet_name, item_name, column_name, full_reference)


class PropertyTableWidget(QTableWidget):
    """属性表格，紧凑展示键值信息"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["属性", "值"])
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        ensure_interactive_header(self.horizontalHeader(), stretch_last=True)
        ensure_word_wrap(self)

    def set_properties(self, properties: Optional[Dict[str, Any]]):
        self.setRowCount(0)

        if not properties:
            self._append_row("提示", "请选择目标项以查看属性")
            schedule_row_resize(self, 40)
            return

        for key, value in properties.items():
            display = "" if value is None else str(value)
            self._append_row(key, display)

        schedule_row_resize(self, 60)

    def _append_row(self, name: str, value: str):
        row = self.rowCount()
        self.insertRow(row)

        name_item = QTableWidgetItem(str(name))
        name_font = QFont()
        name_font.setBold(True)
        name_item.setFont(name_font)
        name_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(row, 0, name_item)

        value_item = QTableWidgetItem(str(value))
        value_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        value_item.setFlags(value_item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.setItem(row, 1, value_item)


def create_advanced_formula_editor(
    workbook_manager: WorkbookManager, parent=None
) -> QWidget:
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
        # ⭐ 解析公式引用（三段式）
        references = parse_formula_references_three_segment(formula)

        if references:
            status_label.setText(f"公式有效 - 包含 {len(references)} 个引用")
        else:
            status_label.setText("警告 - 公式中无引用")

    except Exception as e:
        status_label.setText(f"公式无效: {str(e)}")


class FormulaEditDialog(QDialog):
    """公式编辑对话框 - 双击弹出的高级公式编辑窗口"""

    def __init__(
        self,
        target_item,
        workbook_manager,
        parent=None,
        column_key="__default__",
        column_name="",
    ):
        super().__init__(parent)
        self.target_item = target_item
        self.workbook_manager = workbook_manager
        self.column_key = column_key or "__default__"
        self.column_name = column_name or self.column_key

        # 初始化计算引擎
        from modules.calculation_engine import CalculationEngine

        self.calculation_engine = CalculationEngine(workbook_manager)

        self.current_formula = ""
        self.init_ui()
        self.load_current_formula()
        self.load_sheet_data()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"编辑公式 - {self.target_item.name} · {self.column_name}")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 900)

        layout = QVBoxLayout(self)

        # 公式输入行
        formula_group = QGroupBox("公式编辑")
        formula_layout = QVBoxLayout(formula_group)

        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText(
            "请输入公式，如：[工作表1]D16 + [工作表2]D17"
        )
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
        self.sheet_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.sheet_combo.setMinimumWidth(200)
        self.sheet_combo.currentTextChanged.connect(self.on_sheet_changed)
        sheet_layout.addWidget(self.sheet_combo)
        data_layout.addLayout(sheet_layout)

        # 数据列表
        self.data_table = QTableView()
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.doubleClicked.connect(self.on_data_double_clicked)
        ensure_interactive_header(
            self.data_table.horizontalHeader(), stretch_last=False
        )
        ensure_word_wrap(self.data_table)
        # 设置自适应行高
        self.data_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        # 添加网格线样式
        self.data_table.setStyleSheet("""
            QTableView {
                gridline-color: #d0d0d0;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QTableView::item {
                padding: 4px;
                border: none;
            }
        """)
        self.data_table.setShowGrid(True)  # 确保显示网格线
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
        data_splitter.setSizes([1100, 260])

        layout.addWidget(data_splitter)

        # 预览结果 - 改为横向布局
        preview_group = QGroupBox("预览")
        preview_layout = QHBoxLayout(preview_group)

        # 左侧：来源显示表格
        self.reference_table = QTableWidget()
        self.reference_table.setColumnCount(5)
        self.reference_table.setHorizontalHeaderLabels(
            ["表格", "层级", "项目 / 科目代码", "单元格", "数值"]
        )
        self.reference_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.reference_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.reference_table.setFocusPolicy(Qt.NoFocus)
        header = self.reference_table.horizontalHeader()
        ensure_interactive_header(header, stretch_last=True)
        # 设置列宽自动扩展
        header.setStretchLastSection(True)
        for column in range(self.reference_table.columnCount() - 1):
            header.setSectionResizeMode(column, QHeaderView.Stretch)
        ensure_word_wrap(self.reference_table)
        # 设置自适应行高
        self.reference_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        # 添加网格线样式
        self.reference_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
        """)
        self.reference_table.setShowGrid(True)  # 确保显示网格线
        preview_layout.addWidget(self.reference_table, 2)  # 占2份空间

        # 右侧：公式验证区块
        validation_widget = QWidget()
        validation_layout = QVBoxLayout(validation_widget)
        validation_layout.setContentsMargins(0, 0, 0, 0)

        validation_label = QLabel("公式检验")
        validation_label.setStyleSheet(
            "font-size: 12pt; font-weight: 600; padding: 4px;"
        )
        validation_layout.addWidget(validation_label)

        self.preview_formula_label = QLabel("公式预览将在这里显示")
        self.preview_formula_label.setStyleSheet(
            "background-color: white; "
            "padding: 12px; "
            "border: 1px solid #dee2e6; "
            "border-radius: 6px; "
            "font-size: 11pt;"
        )
        self.preview_formula_label.setWordWrap(True)
        self.preview_formula_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        validation_layout.addWidget(self.preview_formula_label)

        preview_layout.addWidget(validation_widget, 1)  # 占1份空间

        layout.addWidget(preview_group)

        # 设置拉伸因子，优化高度分配
        layout.setStretch(0, 1)  # formula_group - 公式编辑区，保持固定
        layout.setStretch(1, 4)  # data_splitter - 数据选择区，增加空间
        layout.setStretch(2, 2)  # preview_group - 预览区，减少空间

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
        mapping = self.workbook_manager.get_mapping(
            self.target_item.id, self.column_key
        )
        if mapping and mapping.formula:
            self.current_formula = mapping.formula
            self.formula_input.setText(self.current_formula)

    def load_sheet_data(self):
        """加载工作表数据 - 使用计算引擎获取工作表名称"""
        # 使用计算引擎获取工作表名称
        sheet_names = self.calculation_engine.get_sheet_names()
        self.sheet_combo.addItems(sheet_names)

        if sheet_names:
            self.on_sheet_changed(sheet_names[0])

    def on_sheet_changed(self, sheet_name):
        """工作表切换事件 - 使用动态列显示原sheet的数据结构"""
        if not sheet_name:
            return

        # 获取该sheet的列元数据
        column_metadata = self.workbook_manager.source_sheet_columns.get(sheet_name, [])

        # 如果没有列元数据，使用默认的4列显示
        if not column_metadata:
            # 创建默认的数据模型
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(["项目名称", "单元格", "数值", "引用格式"])

            # 使用计算引擎获取该工作表的引用数据
            references = self.calculation_engine.get_available_references(sheet_name)

            for ref_info in references:
                name_item = QStandardItem(ref_info["name"])
                cell_item = QStandardItem(ref_info["cell_address"])
                value_item = QStandardItem(
                    str(ref_info["value"]) if ref_info["value"] is not None else ""
                )
                ref_item = QStandardItem(ref_info["reference_string"])

                model.appendRow([name_item, cell_item, value_item, ref_item])
        else:
            # 使用动态列显示原sheet的完整数据结构
            # 构建列标题：项目名称 + 数据列
            headers = ["项目名称"]  # 第一列固定为项目名称
            data_column_keys = []  # 记录数据列的key

            for col_meta in column_metadata:
                if col_meta.get("is_data_column", False):
                    display_name = col_meta.get("display_name", f"列{col_meta.get('column_letter', '')}")
                    headers.append(display_name)
                    data_column_keys.append(col_meta.get("key"))

            # 不再添加"引用格式"列，因为现在是动态构建三段式引用

            # 创建模型
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(headers)

            # 获取该sheet的所有源数据项
            sheet_sources = []
            for source_id, source_item in self.workbook_manager.source_items.items():
                if source_item.sheet_name == sheet_name:
                    sheet_sources.append(source_item)

            # 按行号排序，保持原始顺序
            sheet_sources.sort(key=lambda x: x.row)

            # 填充数据
            for source_item in sheet_sources:
                row_items = []

                # 第一列：项目名称（保留层级缩进）
                name_with_indent = source_item.full_name_with_indent or source_item.name
                name_item = QStandardItem(name_with_indent)
                # ⭐ 关键：将完整的source_item对象存储到UserRole，避免后续通过文本解析匹配
                name_item.setData(source_item, Qt.UserRole)
                row_items.append(name_item)

                # 数据列：从source_item.data_columns获取
                for col_key in data_column_keys:
                    value = source_item.data_columns.get(col_key, "")
                    if value is None:
                        value = ""
                    value_item = QStandardItem(str(value))
                    row_items.append(value_item)

                # 不再添加引用格式列

                model.appendRow(row_items)

        self.data_table.setModel(model)

        # 调整列宽
        header = self.data_table.horizontalHeader()
        ensure_interactive_header(header, stretch_last=False)
        for column in range(model.columnCount()):
            header.setSectionResizeMode(
                column,
                (
                    QHeaderView.ResizeToContents
                    if column != 0
                    else QHeaderView.ResizeToContents
                ),
            )
            self.data_table.resizeColumnToContents(column)
            header.setSectionResizeMode(column, QHeaderView.Interactive)

        # 应用智能填充，确保数据选择表格占满容器宽度
        # 为所有列设置合理的最小和最大宽度
        min_widths = {}
        max_widths = {}

        if not column_metadata:
            # 默认4列的宽度设置
            for column in range(model.columnCount()):
                if column == 0:  # 项目名称列
                    min_widths[column] = 150
                    max_widths[column] = 400
                elif column == 1:  # 单元格列
                    min_widths[column] = 80
                    max_widths[column] = 120
                elif column == 2:  # 数值列
                    min_widths[column] = 100
                    max_widths[column] = 200
                else:  # 引用格式列
                    min_widths[column] = 150
                    max_widths[column] = 300
        else:
            # 动态列的宽度设置
            for column in range(model.columnCount()):
                if column == 0:  # 项目名称列
                    min_widths[column] = 200  # 需要更宽以显示缩进
                    max_widths[column] = 500
                elif column == model.columnCount() - 1:  # 引用格式列
                    min_widths[column] = 150
                    max_widths[column] = 300
                else:  # 数据列
                    min_widths[column] = 100
                    max_widths[column] = 200

        # 应用智能填充算法
        distribute_columns_evenly(
            self.data_table,
            exclude_columns=[],  # 不排除任何列
            min_widths=min_widths,
            max_widths=max_widths
        )
        # 行高已设置为自适应，无需手动调整

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
        """
        添加选中的数据项到公式 - 支持三段式引用

        策略：
        1. 如果表格有多个数据列，需要用户选择要引用哪一列
        2. 如果只有一个数据列，直接使用该列
        3. 构建三段式引用：[工作表名]![项目名]![列名]
        """
        from PySide6.QtWidgets import QMenu, QMessageBox

        selected_indexes = self.data_table.selectionModel().selectedRows()
        if not selected_indexes:
            return

        model = self.data_table.model()

        for index in selected_indexes:
            row = index.row()

            # ⭐ 直接从UserRole获取完整的source_item对象，避免文本解析匹配问题
            source_item = model.item(row, 0).data(Qt.UserRole)

            if not source_item:
                # 备选方案：尝试从文本解析（兼容旧数据）
                name_with_indent = model.item(row, 0).text()
                item_name = name_with_indent.strip()
                sheet_name = self.sheet_combo.currentText()

                for src in self.workbook_manager.source_items.values():
                    if src.sheet_name == sheet_name and src.name == item_name:
                        source_item = src
                        break

            if not source_item:
                QMessageBox.warning(self, "错误", f"无法获取来源项数据")
                continue

            # 获取工作表名（可能与source_item.sheet_name一致，但以界面选择为准）
            sheet_name = self.sheet_combo.currentText()

            # ⭐ 优先从source_item获取可用的数据列
            available_columns = {}

            # 方式1: 从values字典获取（三段式引用的标准数据源）
            if hasattr(source_item, 'values') and isinstance(source_item.values, dict):
                available_columns = source_item.values

            # 方式2: 从data_columns获取（备选）
            elif hasattr(source_item, 'data_columns') and isinstance(source_item.data_columns, dict):
                available_columns = source_item.data_columns

            # 方式3: 从表头推断数据列（兼容模式）
            else:
                column_count = model.columnCount()
                headers = []
                for col in range(column_count):
                    headers.append(model.headerData(col, Qt.Horizontal))

                # 识别数据列（排除"项目名称"和"引用格式"）
                for col_idx, header_text in enumerate(headers):
                    if header_text not in ["项目名称", "引用格式", "单元格", "科目代码", "层级"]:
                        # 这是数据列
                        value_text = model.item(row, col_idx).text() if model.item(row, col_idx) else ""
                        available_columns[header_text] = value_text

            # 根据数据列数量决定策略
            if not available_columns:
                # 没有数据列，使用旧格式（兼容）
                ref_string = f"[{sheet_name}]![{source_item.name}]"
                self._insert_reference_to_formula(ref_string)

            elif len(available_columns) == 1:
                # 只有一个数据列，直接使用
                column_name = list(available_columns.keys())[0]
                ref_string = build_formula_reference_three_segment(
                    sheet_name,
                    source_item.name,
                    column_name
                )
                self._insert_reference_to_formula(ref_string)

            else:
                # 多个数据列，弹出选择菜单
                menu = QMenu(self)
                menu.setStyleSheet("""
                    QMenu {
                        background-color: white;
                        border: 1px solid #ccc;
                        padding: 5px;
                    }
                    QMenu::item {
                        padding: 8px 25px;
                        font-size: 11pt;
                    }
                    QMenu::item:selected {
                        background-color: #4CAF50;
                        color: white;
                    }
                """)

                # 添加列选项（从available_columns字典）
                for col_name, col_value in available_columns.items():
                    # 格式化显示文本
                    display_text = f"{col_name}"  # 移除emoji避免编码问题
                    if col_value is not None and str(col_value).strip():
                        display_text += f"  ({col_value})"

                    action = menu.addAction(display_text)
                    action.triggered.connect(
                        lambda checked=False, cn=col_name: self._insert_three_segment_reference(
                            sheet_name,
                            source_item.name,
                            cn
                        )
                    )

                # 在鼠标位置显示菜单
                menu.exec_(self.data_table.mapToGlobal(self.data_table.visualRect(index).center()))

    def _insert_three_segment_reference(self, sheet_name: str, item_name: str, column_name: str):
        """插入三段式引用到公式输入框"""
        ref_string = build_formula_reference_three_segment(sheet_name, item_name, column_name)
        self._insert_reference_to_formula(ref_string)

    def _insert_reference_to_formula(self, ref_string: str):
        """插入引用到公式输入框"""
        current_text = self.formula_input.text()
        if current_text and not current_text.endswith(" "):
            current_text += " "

        self.formula_input.setText(current_text + ref_string)

    def on_data_double_clicked(self, index):
        """双击数据项"""
        self.add_selected_item()

    def on_formula_changed(self, text):
        """公式内容变化"""
        self.preview_calculation()

    def preview_calculation(self):
        """预览计算结果 - 使用实时计算引擎"""
        formula = self.formula_input.text().strip()
        self.reference_table.setRowCount(0)

        if not formula:
            self.preview_formula_label.setText("请输入公式")
            return

        try:
            result = self.calculation_engine.calculate_formula_realtime(formula)

            lines = [f"公式: {formula}"]

            if result["validation"]["is_valid"]:
                lines.append("✅ 语法验证: 通过")
                if result["success"]:
                    lines.append(f"🎯 计算结果: {result['value']}")
                else:
                    lines.append(f"❌ 计算错误: {result['error'] or '未知错误'}")
            else:
                lines.append(
                    f"❌ 语法错误: {result['validation']['error_message'] or '未知错误'}"
                )

            lines.append(f"⏱️ 计算耗时: {result['calculation_time']:.2f}ms")

            references = result.get("references") or []
            lines.append(f"📋 引用数量: {len(references)}")

            self.preview_formula_label.setText("\n".join(lines))
            self._populate_reference_table(references)

        except Exception as e:
            self.preview_formula_label.setText(f"预览异常: {str(e)}")
            self.reference_table.setRowCount(0)

    def validate_formula(self):
        """验证公式 - 使用实时计算引擎"""
        formula = self.formula_input.text().strip()
        if not formula:
            self.preview_formula_label.setText("公式不能为空")
            self.reference_table.setRowCount(0)
            return False

        try:
            # 使用计算引擎进行验证
            result = self.calculation_engine.calculate_formula_realtime(formula)

            if result["validation"]["is_valid"] and result["success"]:
                self.preview_formula_label.setText(
                    f"✅ 公式验证通过\n计算结果: {result['value']}"
                )
                self._populate_reference_table(result.get("references") or [])
                return True
            else:
                error_msg = result["validation"]["error_message"] or result["error"]
                self.preview_formula_label.setText(f"❌ 公式验证失败: {error_msg}")
                self.reference_table.setRowCount(0)
                return False

        except Exception as e:
            self.preview_formula_label.setText(f"❌ 公式验证异常: {str(e)}")
            self.reference_table.setRowCount(0)
            return False

    def _populate_reference_table(self, references: List[Any]):
        """将引用信息填充到表格"""
        self.reference_table.setRowCount(0)

        if not references:
            return

        rows = []
        for ref in references:
            if isinstance(ref, dict):
                ref_data = ref
            else:
                # ⭐ 使用三段式解析
                parsed = parse_formula_references_three_segment(str(ref))
                ref_data = (
                    parsed[0]
                    if parsed
                    else {
                        "sheet_name": "",
                        "item_name": None,
                        "column_name": None,  # 三段式使用column_name
                        "column_key": None,   # 保留兼容
                        "cell_address": "",
                        "full_reference": str(ref),
                    }
                )

            sheet_name = ref_data.get("sheet_name", "") or ""
            item_name = ref_data.get("item_name")
            # ⭐ 三段式：优先使用column_name
            column_name = ref_data.get("column_name")
            column_key = ref_data.get("column_key")  # 回退到旧格式
            cell_address = (ref_data.get("cell_address") or "").upper()
            full_ref = ref_data.get("full_reference") or str(ref)

            source_item = self._lookup_source_item(
                sheet_name, item_name, column_key, cell_address
            )

            if source_item:
                display_name = source_item.name or item_name or full_ref
                if getattr(source_item, "account_code", ""):
                    display_name = f"{display_name} ({source_item.account_code})"

                raw_value = self._extract_reference_value(source_item, column_key)
                rows.append(
                    {
                        "sheet": sheet_name
                        or getattr(source_item, "sheet_name", "")
                        or "-",
                        "level": str(getattr(source_item, "hierarchy_level", ""))
                        or "-",
                        "project": display_name,
                        "cell": source_item.cell_address or cell_address or "-",
                        "value_text": self._format_reference_value(raw_value),
                        "is_numeric": isinstance(raw_value, (int, float)),
                        "missing": False,
                    }
                )
            else:
                rows.append(
                    {
                        "sheet": sheet_name or "-",
                        "level": "-",
                        "project": item_name or full_ref,
                        "cell": cell_address or "-",
                        "value_text": "-",
                        "is_numeric": False,
                        "missing": True,
                    }
                )

        self.reference_table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            column_values = [
                row["sheet"],
                row["level"],
                row["project"],
                row["cell"],
                row["value_text"],
            ]
            for col_idx, text in enumerate(column_values):
                item = QTableWidgetItem(text)
                if col_idx == 4 and row["is_numeric"]:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                if row["missing"]:
                    item.setForeground(QBrush(QColor("#c0392b")))

                item.setToolTip(text)
                self.reference_table.setItem(row_idx, col_idx, item)

        ensure_word_wrap(self.reference_table)
        # 行高已设置为自适应，无需手动调整

    def _lookup_source_item(
        self,
        sheet_name: str,
        item_name: Optional[str],
        column_key: Optional[str],
        cell_address: str,
    ) -> Optional[SourceItem]:
        if not self.workbook_manager:
            return None

        normalized_cell = cell_address.strip().upper() if cell_address else ""

        if item_name:
            for source in self.workbook_manager.source_items.values():
                if source.sheet_name == sheet_name and source.name == item_name:
                    return source

        if normalized_cell:
            for source in self.workbook_manager.source_items.values():
                if (
                    source.sheet_name == sheet_name
                    and getattr(source, "cell_address", "").upper() == normalized_cell
                ):
                    return source

        return None

    def _extract_reference_value(
        self, source_item: SourceItem, column_key: Optional[str]
    ):
        if not source_item:
            return None

        if column_key and getattr(source_item, "data_columns", None):
            return source_item.data_columns.get(column_key)

        return getattr(source_item, "value", None)

    def _format_reference_value(self, value: Any) -> str:
        if value is None or value == "":
            return "-"

        if isinstance(value, (int, float)):
            if value == 0:
                return "0"
            if abs(value) >= 10000:
                return f"{value:,.0f}"
            return f"{value:,.2f}"

        return str(value)

    def apply_formula(self):
        """应用公式"""
        if not self.validate_formula():
            return

        formula_text = self.formula_input.text().strip()

        # 更新或创建公式
        from models.data_models import FormulaStatus

        mapping = self.workbook_manager.ensure_mapping(
            self.target_item.id,
            self.column_key,
            self.column_name,
        )
        mapping.update_formula(
            formula_text, FormulaStatus.USER_MODIFIED, column_name=self.column_name
        )
        mapping.constant_value = None
        mapping.validation_error = ""

        self.preview_formula_label.setText("✅ 公式已应用")
        self.reference_table.setRowCount(0)

    def accept(self):
        """确定按钮"""
        self.apply_formula()
        super().accept()

    def get_formula(self):
        """获取公式"""
        return self.formula_input.text().strip()
