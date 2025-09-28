#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公式编辑器模块
提供主要的用户交互界面，包括目标项树状列表、公式编辑框、来源项搜索等功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
from typing import Dict, List, Optional, Tuple, Callable, Any
import re
from dataclasses import dataclass
from datetime import datetime

from models.data_models import TargetItem, SourceItem, MappingFormula, WorkbookManager
from utils.excel_utils import validate_formula_syntax


@dataclass
class UIState:
    """界面状态管理"""
    current_target_id: Optional[str] = None
    search_text: str = ""
    filter_sheet: str = ""
    expanded_nodes: set = None

    def __post_init__(self):
        if self.expanded_nodes is None:
            self.expanded_nodes = set()


class FormulaEditor:
    """公式编辑器主类"""

    def __init__(self, workbook_manager: WorkbookManager, parent: Optional[tk.Tk] = None):
        """
        初始化公式编辑器

        Args:
            workbook_manager: 工作簿管理器实例
            parent: 父窗口
        """
        self.workbook_manager = workbook_manager
        self.parent = parent if parent else tk.Tk()
        self.ui_state = UIState()

        # 回调函数
        self.on_formula_change: Optional[Callable[[str, str], None]] = None
        self.on_ai_mapping_request: Optional[Callable[[List[str]], None]] = None

        # UI组件
        self.main_window = None
        self.target_tree = None
        self.formula_text = None
        self.source_tree = None
        self.search_var = None
        self.filter_var = None
        self.status_var = None

        # 样式配置
        self.setup_styles()

    def setup_styles(self):
        """配置界面样式"""
        self.colors = {
            'bg': '#f0f0f0',
            'panel_bg': '#ffffff',
            'highlight': '#e3f2fd',
            'selected': '#2196f3',
            'text': '#333333',
            'border': '#cccccc'
        }

        self.fonts = {
            'default': ('微软雅黑', 9),
            'title': ('微软雅黑', 11, 'bold'),
            'code': ('Consolas', 9),
            'small': ('微软雅黑', 8)
        }

    def create_main_window(self) -> tk.Toplevel:
        """
        创建主窗口界面

        Returns:
            主窗口对象
        """
        if self.main_window:
            self.main_window.lift()
            return self.main_window

        self.main_window = tk.Toplevel(self.parent)
        self.main_window.title("财务数据映射编辑器")
        self.main_window.geometry("1400x800")
        self.main_window.configure(bg=self.colors['bg'])

        # 创建主要布局
        self._create_main_layout()

        # 绑定事件
        self._bind_events()

        # 初始化数据
        self._initialize_data()

        return self.main_window

    def _create_main_layout(self):
        """创建主要布局"""
        # 创建顶部工具栏
        toolbar = self._create_toolbar()
        toolbar.pack(fill='x', padx=5, pady=5)

        # 创建主要内容区域
        main_frame = ttk.PanedWindow(self.main_window, orient='horizontal')
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # 左侧面板：目标项树
        left_panel = self._create_target_panel(main_frame)
        main_frame.add(left_panel, weight=2)

        # 中间面板：公式编辑
        middle_panel = self._create_formula_panel(main_frame)
        main_frame.add(middle_panel, weight=2)

        # 右侧面板：来源项列表
        right_panel = self._create_source_panel(main_frame)
        main_frame.add(right_panel, weight=2)

        # 底部状态栏
        status_bar = self._create_status_bar()
        status_bar.pack(fill='x', side='bottom')

    def _create_toolbar(self) -> ttk.Frame:
        """创建工具栏"""
        toolbar = ttk.Frame(self.main_window)

        # AI映射按钮
        ai_btn = ttk.Button(
            toolbar,
            text="智能映射(AI)",
            command=self._on_ai_mapping_click
        )
        ai_btn.pack(side='left', padx=5)

        # 批量操作按钮
        batch_btn = ttk.Button(
            toolbar,
            text="批量操作",
            command=self._on_batch_operation_click
        )
        batch_btn.pack(side='left', padx=5)

        # 验证公式按钮
        validate_btn = ttk.Button(
            toolbar,
            text="验证公式",
            command=self._on_validate_formulas_click
        )
        validate_btn.pack(side='left', padx=5)

        # 分隔符
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=10)

        # 导入/导出按钮
        import_btn = ttk.Button(
            toolbar,
            text="导入公式",
            command=self._on_import_formulas_click
        )
        import_btn.pack(side='left', padx=5)

        export_btn = ttk.Button(
            toolbar,
            text="导出公式",
            command=self._on_export_formulas_click
        )
        export_btn.pack(side='left', padx=5)

        # 右侧帮助按钮
        help_btn = ttk.Button(
            toolbar,
            text="帮助",
            command=self._on_help_click
        )
        help_btn.pack(side='right', padx=5)

        return toolbar

    def _create_target_panel(self, parent) -> ttk.Frame:
        """创建目标项面板"""
        panel = ttk.Frame(parent)

        # 面板标题
        title_frame = ttk.Frame(panel)
        title_frame.pack(fill='x', pady=5)

        title_label = ttk.Label(
            title_frame,
            text="目标项列表",
            font=self.fonts['title']
        )
        title_label.pack(side='left')

        # 统计信息
        stats_label = ttk.Label(
            title_frame,
            text=f"总计: {len(self.workbook_manager.target_items)}项",
            font=self.fonts['small']
        )
        stats_label.pack(side='right')

        # 筛选器
        filter_frame = ttk.Frame(panel)
        filter_frame.pack(fill='x', pady=5)

        ttk.Label(filter_frame, text="筛选:").pack(side='left')

        filter_combo = ttk.Combobox(
            filter_frame,
            values=["全部", "空目标项", "已填充", "有错误"],
            state='readonly'
        )
        filter_combo.set("全部")
        filter_combo.pack(side='left', fill='x', expand=True, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', self._on_filter_change)

        # 目标项树形视图
        tree_frame = ttk.Frame(panel)
        tree_frame.pack(fill='both', expand=True)

        # 创建树形控件
        columns = ('formula', 'status')
        self.target_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='tree headings'
        )

        # 设置列
        self.target_tree.heading('#0', text='目标项')
        self.target_tree.heading('formula', text='公式')
        self.target_tree.heading('status', text='状态')

        self.target_tree.column('#0', width=250)
        self.target_tree.column('formula', width=200)
        self.target_tree.column('status', width=80)

        # 添加滚动条
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.target_tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.target_tree.xview)

        self.target_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.target_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        return panel

    def _create_formula_panel(self, parent) -> ttk.Frame:
        """创建公式编辑面板"""
        panel = ttk.Frame(parent)

        # 面板标题
        title_frame = ttk.Frame(panel)
        title_frame.pack(fill='x', pady=5)

        title_label = ttk.Label(
            title_frame,
            text="公式编辑器",
            font=self.fonts['title']
        )
        title_label.pack(side='left')

        # 当前目标项信息
        info_frame = ttk.LabelFrame(panel, text="当前目标项")
        info_frame.pack(fill='x', pady=5)

        self.current_target_label = ttk.Label(
            info_frame,
            text="未选择目标项",
            font=self.fonts['default']
        )
        self.current_target_label.pack(anchor='w', padx=5, pady=5)

        # 公式编辑框
        formula_frame = ttk.LabelFrame(panel, text="公式内容")
        formula_frame.pack(fill='both', expand=True, pady=5)

        # 公式文本框
        text_frame = ttk.Frame(formula_frame)
        text_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.formula_text = tk.Text(
            text_frame,
            font=self.fonts['code'],
            height=8,
            wrap='word'
        )

        # 添加滚动条
        formula_scroll = ttk.Scrollbar(text_frame, orient='vertical', command=self.formula_text.yview)
        self.formula_text.configure(yscrollcommand=formula_scroll.set)

        self.formula_text.pack(side='left', fill='both', expand=True)
        formula_scroll.pack(side='right', fill='y')

        # 公式操作按钮
        btn_frame = ttk.Frame(formula_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            btn_frame,
            text="清空",
            command=self._on_clear_formula
        ).pack(side='left', padx=2)

        ttk.Button(
            btn_frame,
            text="验证",
            command=self._on_validate_formula
        ).pack(side='left', padx=2)

        ttk.Button(
            btn_frame,
            text="保存",
            command=self._on_save_formula
        ).pack(side='left', padx=2)

        # 公式语法提示
        syntax_frame = ttk.LabelFrame(panel, text="语法提示")
        syntax_frame.pack(fill='x', pady=5)

        syntax_text = (
            "引用格式: [工作表名]![项目名]\n"
            "运算符: +、-、*、/、()等\n"
            "双击来源项可直接添加到公式中"
        )

        syntax_label = ttk.Label(
            syntax_frame,
            text=syntax_text,
            font=self.fonts['small']
        )
        syntax_label.pack(anchor='w', padx=5, pady=5)

        return panel

    def _create_source_panel(self, parent) -> ttk.Frame:
        """创建来源项面板"""
        panel = ttk.Frame(parent)

        # 面板标题
        title_frame = ttk.Frame(panel)
        title_frame.pack(fill='x', pady=5)

        title_label = ttk.Label(
            title_frame,
            text="数据来源",
            font=self.fonts['title']
        )
        title_label.pack(side='left')

        # 搜索框
        search_frame = ttk.Frame(panel)
        search_frame.pack(fill='x', pady=5)

        ttk.Label(search_frame, text="搜索:").pack(side='left')

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var
        )
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        search_entry.bind('<KeyRelease>', self._on_search_change)

        # 工作表筛选
        sheet_frame = ttk.Frame(panel)
        sheet_frame.pack(fill='x', pady=5)

        ttk.Label(sheet_frame, text="工作表:").pack(side='left')

        self.filter_var = tk.StringVar()
        sheet_combo = ttk.Combobox(
            sheet_frame,
            textvariable=self.filter_var,
            values=["全部"] + list(self.workbook_manager.worksheets.keys()),
            state='readonly'
        )
        sheet_combo.set("全部")
        sheet_combo.pack(side='left', fill='x', expand=True, padx=5)
        sheet_combo.bind('<<ComboboxSelected>>', self._on_sheet_filter_change)

        # 来源项列表
        list_frame = ttk.Frame(panel)
        list_frame.pack(fill='both', expand=True)

        # 创建列表控件
        columns = ('sheet', 'value', 'type')
        self.source_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='tree headings'
        )

        # 设置列
        self.source_tree.heading('#0', text='项目名称')
        self.source_tree.heading('sheet', text='工作表')
        self.source_tree.heading('value', text='数值')
        self.source_tree.heading('type', text='类型')

        self.source_tree.column('#0', width=200)
        self.source_tree.column('sheet', width=100)
        self.source_tree.column('value', width=100)
        self.source_tree.column('type', width=60)

        # 添加滚动条
        source_v_scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.source_tree.yview)
        source_h_scroll = ttk.Scrollbar(list_frame, orient='horizontal', command=self.source_tree.xview)

        self.source_tree.configure(yscrollcommand=source_v_scroll.set, xscrollcommand=source_h_scroll.set)

        self.source_tree.grid(row=0, column=0, sticky='nsew')
        source_v_scroll.grid(row=0, column=1, sticky='ns')
        source_h_scroll.grid(row=1, column=0, sticky='ew')

        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        return panel

    def _create_status_bar(self) -> ttk.Frame:
        """创建状态栏"""
        status_bar = ttk.Frame(self.main_window)

        self.status_var = tk.StringVar()
        self.status_var.set("就绪")

        status_label = ttk.Label(
            status_bar,
            textvariable=self.status_var,
            relief='sunken',
            anchor='w'
        )
        status_label.pack(side='left', fill='x', expand=True)

        # 进度条（隐藏状态）
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_bar,
            variable=self.progress_var,
            maximum=100
        )
        # 默认不显示进度条

        return status_bar

    def _bind_events(self):
        """绑定事件处理器"""
        # 目标项树选择事件
        self.target_tree.bind('<<TreeviewSelect>>', self._on_target_select)

        # 来源项双击事件
        self.source_tree.bind('<Double-1>', self._on_source_double_click)

        # 公式文本变更事件
        self.formula_text.bind('<KeyRelease>', self._on_formula_text_change)

        # 窗口关闭事件
        if self.main_window:
            self.main_window.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _initialize_data(self):
        """初始化界面数据"""
        self._load_target_tree()
        self._load_source_list()
        self._update_status("数据加载完成")

    def _load_target_tree(self):
        """加载目标项到树形视图"""
        # 清空现有数据
        for item in self.target_tree.get_children():
            self.target_tree.delete(item)

        # 按工作表和层级组织目标项
        sheet_groups = {}
        for target_id, target in self.workbook_manager.target_items.items():
            sheet_name = target.sheet_name
            if sheet_name not in sheet_groups:
                sheet_groups[sheet_name] = []
            sheet_groups[sheet_name].append(target)

        # 添加到树形视图
        for sheet_name, targets in sheet_groups.items():
            # 创建工作表节点
            sheet_node = self.target_tree.insert(
                '',
                'end',
                text=f"[{sheet_name}]",
                values=('', f"{len(targets)}项"),
                tags=('sheet_node',)
            )

            # 按层级排序目标项
            targets.sort(key=lambda x: (x.level, x.name))

            # 创建层级结构
            level_nodes = {0: sheet_node}

            for target in targets:
                # 确定父节点
                parent_node = sheet_node
                for level in range(1, target.level + 1):
                    if level not in level_nodes:
                        level_nodes[level] = parent_node
                    parent_node = level_nodes[level]

                # 获取公式信息
                formula_text = ""
                status = "空"

                if target.id in self.workbook_manager.mapping_formulas:
                    formula = self.workbook_manager.mapping_formulas[target.id]
                    formula_text = formula.formula[:30] + "..." if len(formula.formula) > 30 else formula.formula
                    status = formula.status.value
                elif not target.is_empty_target:
                    status = "已填充"

                # 添加目标项节点
                target_node = self.target_tree.insert(
                    parent_node,
                    'end',
                    text=target.name,
                    values=(formula_text, status),
                    tags=('target_item', status.lower())
                )

                # 存储目标项ID
                self.target_tree.set(target_node, '#1', target.id)

                # 更新层级节点映射
                level_nodes[target.level + 1] = target_node

        # 配置标签样式
        self.target_tree.tag_configure('sheet_node', background='#e8f4fd')
        self.target_tree.tag_configure('空', foreground='red')
        self.target_tree.tag_configure('已填充', foreground='green')
        self.target_tree.tag_configure('错误', foreground='orange')

    def _load_source_list(self):
        """加载来源项到列表"""
        # 清空现有数据
        for item in self.source_tree.get_children():
            self.source_tree.delete(item)

        # 按工作表分组
        sheet_groups = {}
        for source_id, source in self.workbook_manager.source_items.items():
            sheet_name = source.sheet_name
            if sheet_name not in sheet_groups:
                sheet_groups[sheet_name] = []
            sheet_groups[sheet_name].append(source)

        # 添加到列表
        for sheet_name, sources in sheet_groups.items():
            # 创建工作表分组节点
            sheet_node = self.source_tree.insert(
                '',
                'end',
                text=f"[{sheet_name}]",
                values=('', f"{len(sources)}项", ''),
                tags=('sheet_group',)
            )

            # 添加来源项
            for source in sources:
                # 获取第一个有值的列
                value_text = ""
                data_type = "None"

                if source.values:
                    first_col = list(source.values.keys())[0]
                    value = source.values[first_col]
                    if value is not None:
                        value_text = str(value)
                        if len(value_text) > 15:
                            value_text = value_text[:12] + "..."
                        data_type = type(value).__name__

                source_node = self.source_tree.insert(
                    sheet_node,
                    'end',
                    text=source.name,
                    values=(sheet_name, value_text, data_type),
                    tags=('source_item',)
                )

                # 存储来源项ID
                self.source_tree.set(source_node, '#1', source.id)

        # 配置样式
        self.source_tree.tag_configure('sheet_group', background='#f0f8ff')

    def _on_target_select(self, event):
        """处理目标项选择事件"""
        selected_items = self.target_tree.selection()
        if not selected_items:
            return

        item_id = selected_items[0]
        tags = self.target_tree.item(item_id)['tags']

        if 'target_item' in tags:
            # 获取目标项ID
            target_id = self.target_tree.item(item_id)['values'][1] if len(self.target_tree.item(item_id)['values']) > 1 else None

            if target_id and target_id in self.workbook_manager.target_items:
                self.ui_state.current_target_id = target_id
                self._load_current_target()

    def _load_current_target(self):
        """加载当前选中的目标项"""
        if not self.ui_state.current_target_id:
            return

        target = self.workbook_manager.target_items.get(self.ui_state.current_target_id)
        if not target:
            return

        # 更新目标项信息
        info_text = f"工作表: {target.sheet_name}  |  项目: {target.name}  |  行号: {target.row}"
        self.current_target_label.config(text=info_text)

        # 加载公式内容
        formula_text = ""
        if target.id in self.workbook_manager.mapping_formulas:
            formula = self.workbook_manager.mapping_formulas[target.id]
            formula_text = formula.formula

        # 更新公式编辑框
        self.formula_text.delete(1.0, tk.END)
        self.formula_text.insert(1.0, formula_text)

        # 更新状态
        self._update_status(f"已选择目标项: {target.name}")

    def _on_source_double_click(self, event):
        """处理来源项双击事件"""
        selected_items = self.source_tree.selection()
        if not selected_items:
            return

        item_id = selected_items[0]
        tags = self.source_tree.item(item_id)['tags']

        if 'source_item' in tags:
            # 获取来源项信息
            item_text = self.source_tree.item(item_id)['text']
            sheet_name = self.source_tree.item(item_id)['values'][0]

            # 构建引用格式
            reference = f"[{sheet_name}]![{item_text}]"

            # 插入到公式编辑框
            current_pos = self.formula_text.index(tk.INSERT)
            self.formula_text.insert(current_pos, reference)

            # 更新状态
            self._update_status(f"已添加引用: {reference}")

    def _on_formula_text_change(self, event):
        """处理公式文本变更事件"""
        if hasattr(self, '_formula_change_after_id'):
            self.main_window.after_cancel(self._formula_change_after_id)

        # 延迟处理，避免频繁触发
        self._formula_change_after_id = self.main_window.after(500, self._process_formula_change)

    def _process_formula_change(self):
        """处理公式变更"""
        if not self.ui_state.current_target_id:
            return

        formula_content = self.formula_text.get(1.0, tk.END).strip()

        # 触发回调
        if self.on_formula_change:
            self.on_formula_change(self.ui_state.current_target_id, formula_content)

    def _on_search_change(self, event):
        """处理搜索变更事件"""
        search_text = self.search_var.get().lower()
        self.ui_state.search_text = search_text

        # 延迟执行搜索
        if hasattr(self, '_search_after_id'):
            self.main_window.after_cancel(self._search_after_id)

        self._search_after_id = self.main_window.after(300, self._apply_source_filter)

    def _on_sheet_filter_change(self, event):
        """处理工作表筛选变更事件"""
        self.ui_state.filter_sheet = self.filter_var.get()
        self._apply_source_filter()

    def _apply_source_filter(self):
        """应用来源项筛选"""
        # 这里应该重新加载来源项列表，应用搜索和筛选条件
        # 为简化实现，这里只是更新状态
        filter_info = []
        if self.ui_state.search_text:
            filter_info.append(f"搜索: {self.ui_state.search_text}")
        if self.ui_state.filter_sheet and self.ui_state.filter_sheet != "全部":
            filter_info.append(f"工作表: {self.ui_state.filter_sheet}")

        if filter_info:
            self._update_status(f"筛选条件: {', '.join(filter_info)}")
        else:
            self._update_status("显示全部来源项")

    def _on_filter_change(self, event):
        """处理目标项筛选变更事件"""
        # 这里应该重新加载目标项树，应用筛选条件
        # 为简化实现，这里只是更新状态
        self._update_status("目标项筛选已变更")

    # 工具栏事件处理器
    def _on_ai_mapping_click(self):
        """处理AI映射按钮点击"""
        # 获取空目标项
        empty_targets = [tid for tid, target in self.workbook_manager.target_items.items()
                        if target.is_empty_target]

        if not empty_targets:
            messagebox.showinfo("提示", "没有找到需要填充的空目标项")
            return

        # 触发AI映射回调
        if self.on_ai_mapping_request:
            self.on_ai_mapping_request(empty_targets[:10])  # 限制数量
            self._update_status(f"正在处理AI映射请求...")

    def _on_batch_operation_click(self):
        """处理批量操作按钮点击"""
        self._update_status("批量操作功能待实现")

    def _on_validate_formulas_click(self):
        """处理验证公式按钮点击"""
        self._update_status("正在验证所有公式...")
        # 这里应该验证所有公式
        self._update_status("公式验证完成")

    def _on_import_formulas_click(self):
        """处理导入公式按钮点击"""
        self._update_status("导入公式功能待实现")

    def _on_export_formulas_click(self):
        """处理导出公式按钮点击"""
        self._update_status("导出公式功能待实现")

    def _on_help_click(self):
        """处理帮助按钮点击"""
        help_text = """
财务数据映射编辑器 - 帮助

基本操作：
1. 在左侧目标项列表中选择需要编辑的项目
2. 在中间公式编辑框中输入或修改公式
3. 在右侧数据来源中搜索和选择引用项
4. 双击来源项可直接添加到公式中

公式语法：
- 引用格式：[工作表名]![项目名]
- 支持基本运算：+、-、*、/、()
- 示例：[利润表]![营业收入] + [利润表]![其他收入]

快捷功能：
- 智能映射：使用AI自动生成映射建议
- 批量操作：对多个目标项进行批量设置
- 公式验证：检查公式语法和引用有效性
        """

        messagebox.showinfo("帮助", help_text)

    # 公式编辑操作
    def _on_clear_formula(self):
        """清空公式"""
        self.formula_text.delete(1.0, tk.END)
        self._update_status("公式已清空")

    def _on_validate_formula(self):
        """验证当前公式"""
        formula_content = self.formula_text.get(1.0, tk.END).strip()

        if not formula_content:
            messagebox.showwarning("提示", "公式内容为空")
            return

        # 验证公式语法
        is_valid, error_msg = validate_formula_syntax(formula_content)

        if is_valid:
            messagebox.showinfo("验证结果", "公式语法正确")
            self._update_status("公式验证通过")
        else:
            messagebox.showerror("验证结果", f"公式语法错误：\n{error_msg}")
            self._update_status("公式验证失败")

    def _on_save_formula(self):
        """保存当前公式"""
        if not self.ui_state.current_target_id:
            messagebox.showwarning("提示", "请先选择目标项")
            return

        formula_content = self.formula_text.get(1.0, tk.END).strip()

        # 创建或更新映射公式
        if self.ui_state.current_target_id not in self.workbook_manager.mapping_formulas:
            mapping_formula = MappingFormula(
                target_id=self.ui_state.current_target_id,
                formula=formula_content
            )
        else:
            mapping_formula = self.workbook_manager.mapping_formulas[self.ui_state.current_target_id]
            mapping_formula.formula = formula_content
            mapping_formula.last_modified = datetime.now()

        # 保存到管理器
        self.workbook_manager.mapping_formulas[self.ui_state.current_target_id] = mapping_formula

        # 更新界面
        self._refresh_target_tree()

        self._update_status("公式已保存")

    def _on_window_close(self):
        """处理窗口关闭事件"""
        if messagebox.askokcancel("确认", "是否关闭编辑器？"):
            self.main_window.destroy()

    # 辅助方法
    def _update_status(self, message: str):
        """更新状态栏"""
        if hasattr(self, 'status_var'):
            self.status_var.set(f"{datetime.now().strftime('%H:%M:%S')} - {message}")

    def _refresh_target_tree(self):
        """刷新目标项树"""
        # 保存当前展开状态
        expanded_items = []
        for item in self.target_tree.get_children():
            if self.target_tree.item(item)['open']:
                expanded_items.append(self.target_tree.item(item)['text'])

        # 重新加载
        self._load_target_tree()

        # 恢复展开状态
        for item in self.target_tree.get_children():
            if self.target_tree.item(item)['text'] in expanded_items:
                self.target_tree.item(item, open=True)

    def set_formula_change_callback(self, callback: Callable[[str, str], None]):
        """设置公式变更回调函数"""
        self.on_formula_change = callback

    def set_ai_mapping_callback(self, callback: Callable[[List[str]], None]):
        """设置AI映射请求回调函数"""
        self.on_ai_mapping_request = callback

    def update_ai_mapping_result(self, results: List[MappingFormula]):
        """更新AI映射结果"""
        if not results:
            return

        updated_count = 0
        for formula in results:
            if formula.target_id in self.workbook_manager.target_items:
                self.workbook_manager.mapping_formulas[formula.target_id] = formula
                updated_count += 1

        # 刷新界面
        self._refresh_target_tree()

        # 如果当前选中的目标项被更新，重新加载
        if (self.ui_state.current_target_id and
            self.ui_state.current_target_id in [f.target_id for f in results]):
            self._load_current_target()

        self._update_status(f"AI映射完成，已更新{updated_count}个公式")
        messagebox.showinfo("AI映射结果", f"成功生成{updated_count}个映射公式")


def create_formula_editor_window(workbook_manager: WorkbookManager, parent: Optional[tk.Tk] = None) -> FormulaEditor:
    """
    创建公式编辑器窗口

    Args:
        workbook_manager: 工作簿管理器
        parent: 父窗口

    Returns:
        公式编辑器实例
    """
    editor = FormulaEditor(workbook_manager, parent)
    editor.create_main_window()
    return editor