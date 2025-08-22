# -*- coding: utf-8 -*-
"""
结果面板组件
显示扫描和分析结果，提供数据选择和预览功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from config.settings import Config
from datetime import datetime

class ResultsPanel(ttk.LabelFrame):
    """结果面板组件，包含概览、详细统计、上传结果等页面"""
    
    def __init__(self, parent, app):
        super().__init__(parent, text="统计结果", padding="10")
        self.app = app
        self.config = Config
        
        self._create_notebook()
        self._create_overview_tab()
        self._create_details_tab()
        self._create_upload_tab()
        
        # 当前选中的文件
        self.current_selected_file = None
    
    def _create_notebook(self):
        """创建分页控件"""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
    
    def _create_overview_tab(self):
        """创建概览页面"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="概览")
        
        # 统计卡片区域
        cards_frame = ttk.Frame(overview_frame, padding="10")
        cards_frame.pack(fill=tk.X)
        
        # 文件总数卡片
        self.files_card = self._create_stat_card(cards_frame, "文件总数", "0", "文件")
        self.files_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 匹配条目卡片
        self.matches_card = self._create_stat_card(cards_frame, "匹配条目", "0", "匹配")
        self.matches_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 上传成功卡片
        self.success_card = self._create_stat_card(cards_frame, "上传成功", "0", "成功")
        self.success_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 上传失败卡片
        self.failed_card = self._create_stat_card(cards_frame, "上传失败", "0", "失败")
        self.failed_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
    def _create_stat_card(self, parent, title, value, category):
        """创建统计卡片"""
        card_frame = ttk.LabelFrame(parent, text=f"{title}", padding="10")
        
        value_label = ttk.Label(card_frame, text=value, font=("Arial", 18, "bold"))
        value_label.pack()
        
        # 存储值标签的引用以便更新
        card_frame.value_label = value_label
        
        return card_frame
    
    def _create_details_tab(self):
        """创建详细统计页面"""
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="详细统计")
        
        # 顶部工具栏
        toolbar_frame = ttk.Frame(details_frame, padding="5")
        toolbar_frame.pack(fill=tk.X)
        
        # 选择控制按钮
        select_frame = ttk.LabelFrame(toolbar_frame, text="选择控制", padding="5")
        select_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(select_frame, text="全选文件", 
                  command=self._select_all_files, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="全选数据", 
                  command=self._select_all_data, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="取消全选", 
                  command=self._deselect_all, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="反选", 
                  command=self._invert_selection, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="选择失败数据", 
                  command=self._select_failed_data, width=12).pack(side=tk.LEFT, padx=5)
        
        # 统计信息
        stats_frame = ttk.LabelFrame(toolbar_frame, text="选择统计", padding="5")
        stats_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.selection_stats_var = tk.StringVar()
        self.selection_stats_var.set("已选: 0 文件, 0 条数据")
        ttk.Label(stats_frame, textvariable=self.selection_stats_var).pack()
        
        # 创建双面板布局
        paned_window = ttk.PanedWindow(details_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧：文件列表
        self._create_file_list(paned_window)
        
        # 右侧：数据详情
        self._create_data_details(paned_window)
    
    def _create_file_list(self, parent):
        """创建文件列表"""
        left_frame = ttk.LabelFrame(parent, text="文件列表", padding="5")
        parent.add(left_frame, weight=1)
        
        # 文件树视图
        file_tree_container = ttk.Frame(left_frame)
        file_tree_container.pack(fill=tk.BOTH, expand=True)
        
        file_columns = ("select", "filename", "matches", "status")
        self.file_tree = ttk.Treeview(file_tree_container, columns=file_columns, 
                                     show="headings", height=15)
        
        # 文件列表列定义
        self.file_tree.heading("select", text="选择")
        self.file_tree.heading("filename", text="文件名")
        self.file_tree.heading("matches", text="匹配数")
        self.file_tree.heading("status", text="状态")
        
        self.file_tree.column("select", width=60, anchor="center")
        self.file_tree.column("filename", width=200)
        self.file_tree.column("matches", width=80, anchor="center")
        self.file_tree.column("status", width=80, anchor="center")
        
        # 文件列表滚动条
        file_scroll_y = ttk.Scrollbar(file_tree_container, orient="vertical", 
                                     command=self.file_tree.yview)
        file_scroll_x = ttk.Scrollbar(file_tree_container, orient="horizontal", 
                                     command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=file_scroll_y.set, 
                                xscrollcommand=file_scroll_x.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        file_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定事件
        self.file_tree.bind('<<TreeviewSelect>>', self._on_file_select)
        self.file_tree.bind('<Button-1>', self._on_file_click)
    
    def _create_data_details(self, parent):
        """创建数据详情面板"""
        right_frame = ttk.LabelFrame(parent, text="数据详情", padding="5")
        parent.add(right_frame, weight=2)
        
        # 数据操作工具栏
        data_toolbar = ttk.Frame(right_frame)
        data_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(data_toolbar, text="全选当前", 
                  command=self._select_current_file_data, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(data_toolbar, text="清空当前", 
                  command=self._deselect_current_file_data, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(data_toolbar, text="预览数据", 
                  command=self._preview_selected_data, width=12).pack(side=tk.LEFT, padx=(0, 5))
        
        # 当前文件信息
        self.current_file_var = tk.StringVar()
        self.current_file_var.set("请选择文件查看数据详情")
        ttk.Label(data_toolbar, textvariable=self.current_file_var, 
                 font=("Arial", 9, "italic")).pack(side=tk.RIGHT)
        
        # 数据列表
        data_tree_container = ttk.Frame(right_frame)
        data_tree_container.pack(fill=tk.BOTH, expand=True)
        
        data_columns = ("select", "index", "preview", "length", "status")
        self.data_tree = ttk.Treeview(data_tree_container, columns=data_columns, 
                                     show="headings", height=15)
        
        # 数据列表列定义
        self.data_tree.heading("select", text="选择")
        self.data_tree.heading("index", text="序号")
        self.data_tree.heading("preview", text="数据预览")
        self.data_tree.heading("length", text="长度")
        self.data_tree.heading("status", text="上传状态")
        
        self.data_tree.column("select", width=60, anchor="center")
        self.data_tree.column("index", width=60, anchor="center")
        self.data_tree.column("preview", width=250)
        self.data_tree.column("length", width=80, anchor="center")
        self.data_tree.column("status", width=100, anchor="center")
        
        # 数据列表滚动条
        data_scroll_y = ttk.Scrollbar(data_tree_container, orient="vertical", 
                                     command=self.data_tree.yview)
        data_scroll_x = ttk.Scrollbar(data_tree_container, orient="horizontal", 
                                     command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=data_scroll_y.set, 
                                xscrollcommand=data_scroll_x.set)
        
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        data_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        data_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定事件
        self.data_tree.bind('<Button-1>', self._on_data_click)
        
        # 配置标签颜色
        self.data_tree.tag_configure('success', foreground='green')
        self.data_tree.tag_configure('failed', foreground='red')
    
    def _create_upload_tab(self):
        """创建上传结果页面"""
        upload_frame = ttk.Frame(self.notebook)
        self.notebook.add(upload_frame, text="上传结果")

        upload_container = ttk.Frame(upload_frame, padding="10")
        upload_container.pack(fill=tk.BOTH, expand=True)

        # 上传结果 Treeview
        columns = ("time", "file", "index", "status")
        self.upload_tree = ttk.Treeview(upload_container, columns=columns, show="headings", height=15)

        for col, width, anchor, text in [
            ("time", 80, "center", "时间"),
            ("file", 200, "w", "文件"),
            ("index", 60, "center", "数据索引"),
            ("status", 120, "center", "上传状态")
        ]:
            self.upload_tree.heading(col, text=text)
            self.upload_tree.column(col, width=width, anchor=anchor)

        scroll_y = ttk.Scrollbar(upload_container, orient="vertical", command=self.upload_tree.yview)
        scroll_x = ttk.Scrollbar(upload_container, orient="horizontal", command=self.upload_tree.xview)
        self.upload_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.upload_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 配置标签颜色
        self.upload_tree.tag_configure('success', foreground='green')
        self.upload_tree.tag_configure('failed', foreground='red')


    # ==================== 数据更新方法 ====================
    
    def update_stats(self):
        """更新统计信息"""
        stats = self.app.data_manager.get_upload_stats()
        
        self.files_card.value_label.config(text=str(stats['total_files']))
        self.matches_card.value_label.config(text=str(stats['total_matches']))
        self.success_card.value_label.config(text=str(stats['uploaded_success']))
        self.failed_card.value_label.config(text=str(stats['uploaded_failed']))
    
    def refresh_data(self):
        """刷新所有数据显示"""
        self._refresh_file_tree()
        self._refresh_data_tree()
        self.update_stats()
    
    def refresh_selection(self):
        """刷新选择状态"""
        self._update_selection_display()
        self._update_selection_stats()
    
    def _refresh_file_tree(self):
        """刷新文件树"""
        # 清空现有项目
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # 添加文件项目
        for file_path in self.app.data_manager.scanned_files:
            matches = self.app.data_manager.get_file_matches(file_path)
            
            # 计算文件状态
            status = self._get_file_upload_status(file_path)
            
            # 选择状态
            select_status = "☑" if file_path in self.app.data_manager.selected_files else "☐"
            
            # 相对路径显示
            if self.app.current_directory:
                rel_path = os.path.relpath(file_path, self.app.current_directory)
            else:
                rel_path = os.path.basename(file_path)
            
            item_id = self.file_tree.insert("", "end", values=(
                select_status,
                rel_path,
                len(matches),
                status
            ))
            
            # 更新映射
            self.app.data_manager.item_to_path[item_id] = file_path
            self.app.data_manager.path_to_item[file_path] = item_id
    
    def _get_file_upload_status(self, file_path):
        """获取文件上传状态"""
        if file_path not in self.app.data_manager.upload_status:
            return "未上传"
        
        status_counts = {'success': 0, 'failed': 0}
        for status in self.app.data_manager.upload_status[file_path].values():
            if status in status_counts:
                status_counts[status] += 1
        
        total_data = len(self.app.data_manager.get_file_matches(file_path))
        success_count = status_counts['success']
        failed_count = status_counts['failed']
        
        if success_count + failed_count == 0:
            return "未上传"
        elif failed_count == 0:
            return "全部成功"
        elif success_count == 0:
            return "全部失败"
        else:
            return f"部分失败({failed_count})"
    
    def _refresh_data_tree(self):
        """刷新数据树"""
        if self.current_selected_file:
            self._load_file_data(self.current_selected_file)
    
    def _load_file_data(self, file_path):
        """加载文件数据到数据树"""
        # 清空现有项目
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        matches = self.app.data_manager.get_file_matches(file_path)
        if not matches:
            self.current_file_var.set("该文件无匹配数据")
            return
        
        filename = os.path.basename(file_path)
        self.current_file_var.set(f"当前文件: {filename} ({len(matches)} 条数据)")
        
        selected_indices = self.app.data_manager.selected_data.get(file_path, set())
        
        for i, match_data in enumerate(matches):
            preview = (match_data[:50] + "...") if len(match_data) > 50 else match_data
            preview = preview.replace('\n', '\\n').replace('\t', '\\t')
            
            select_status = "☑" if i in selected_indices else "☐"
            
            # 确定上传状态
            upload_status = "未上传"
            item_tags = ()
            
            if (file_path in self.app.data_manager.upload_status and 
                i in self.app.data_manager.upload_status[file_path]):
                if self.app.data_manager.upload_status[file_path][i] == 'success':
                    upload_status = "已成功"
                    item_tags = ('success',)
                elif self.app.data_manager.upload_status[file_path][i] == 'failed':
                    upload_status = "失败"
                    item_tags = ('failed',)
            
            self.data_tree.insert("", "end", values=(
                select_status,
                str(i + 1),
                preview,
                len(match_data),
                upload_status
            ), tags=item_tags)
    
    # ==================== 事件处理方法 ====================
    
    def _on_file_select(self, event):
        """处理文件选择事件"""
        selection = self.file_tree.selection()
        if selection:
            item = selection[0]
            file_path = self.app.data_manager.item_to_path.get(item)
            if file_path:
                self.current_selected_file = file_path
                self._load_file_data(file_path)
    
    def _on_file_click(self, event):
        """处理文件点击事件"""
        region = self.file_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.file_tree.identify_column(event.x)
        if column != '#1':  # 只处理选择列的点击
            return

        item = self.file_tree.identify_row(event.y)
        if not item:
            return

        file_path = self.app.data_manager.item_to_path.get(item)
        if file_path:
            self.app.data_manager.toggle_file_selection(file_path)
        
        return "break"
    
    def _on_data_click(self, event):
        """处理数据点击事件"""
        region = self.data_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.data_tree.identify_column(event.x)
        if column != '#1':  # 只处理选择列的点击
            return

        item = self.data_tree.identify_row(event.y)
        if not item or not self.current_selected_file:
            return

        values = self.data_tree.item(item, "values")
        data_index = int(values[1]) - 1
        
        self.app.data_manager.toggle_data_selection(self.current_selected_file, data_index)
        
        return "break"
    
    # ==================== 选择操作方法 ====================
    
    def _select_all_files(self):
        """选择所有文件"""
        self.app.data_manager.select_all_files()
    
    def _select_all_data(self):
        """选择所有数据"""
        self.app.data_manager.select_all_files()  # select_all_files已经包含了所有数据
    
    def _deselect_all(self):
        """取消所有选择"""
        self.app.data_manager.clear_all_selections()
    
    def _invert_selection(self):
        """反选"""
        # 实现反选逻辑
        current_selected = self.app.data_manager.selected_files.copy()
        self.app.data_manager.clear_all_selections()
        
        for file_path in self.app.data_manager.scanned_files:
            if file_path not in current_selected:
                self.app.data_manager.toggle_file_selection(file_path)
    
    def _select_failed_data(self):
        """选择失败数据"""
        self.app.data_manager.select_failed_data()
    
    def _select_current_file_data(self):
        """选择当前文件的所有数据"""
        if not self.current_selected_file:
            return
        
        matches = self.app.data_manager.get_file_matches(self.current_selected_file)
        for i in range(len(matches)):
            self.app.data_manager.toggle_data_selection(self.current_selected_file, i)
    
    def _deselect_current_file_data(self):
        """取消当前文件的所有数据选择"""
        if not self.current_selected_file:
            return
        
        if self.current_selected_file in self.app.data_manager.selected_data:
            self.app.data_manager.selected_data[self.current_selected_file].clear()
            self.app.data_manager.selected_files.discard(self.current_selected_file)
    
    def _preview_selected_data(self):
        """预览选中的数据"""
        selected_data = self.app.data_manager.get_selected_data()
        if not selected_data:
            messagebox.showinfo("预览", "没有选择任何数据！")
            return
        
        # 这里应该打开预览窗口，为简化只显示消息
        messagebox.showinfo("预览", f"将预览 {len(selected_data)} 条选中数据")
    
    def add_upload_result(self, file_path, data_index, success, error_msg=""):
        """
        添加单条上传结果到上传结果区

        Args:
            file_path: 文件路径
            data_index: 数据索引（0基索引）
            success: bool 上传是否成功
            error_msg: 上传失败时的错误信息
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_text = "成功" if success else f"失败: {error_msg}"
        tag = 'success' if success else 'failed'

        display_index = data_index + 1  # 给用户显示从1开始
        rel_path = os.path.relpath(file_path, self.app.current_directory) \
                if self.app.current_directory else file_path

        self.upload_tree.insert("", "end",
                                values=(timestamp, rel_path, display_index, status_text),
                                tags=(tag,))
        self.upload_tree.yview_moveto(1)



    def _update_selection_display(self):
        """更新选择状态显示"""
        self._refresh_file_tree()
        self._refresh_data_tree()
    
    def _update_selection_stats(self):
        """更新选择统计"""
        selected_file_count = len(self.app.data_manager.selected_files)
        selected_data_count = sum(len(indices) for indices in self.app.data_manager.selected_data.values())
        
        self.selection_stats_var.set(f"已选: {selected_file_count} 文件, {selected_data_count} 条数据")
        
        # 更新控制面板按钮状态
        self.app.control_panel.update_button_states(
            has_selected_data=selected_data_count > 0
        )