# -*- coding: utf-8 -*-
"""
控制面板组件
提供所有操作按钮和控制功能
"""

import tkinter as tk
from tkinter import ttk
from config.settings import Config


class ControlPanel(ttk.LabelFrame):
    """控制面板组件，包含所有操作按钮"""
    
    def __init__(self, parent, app):
        super().__init__(parent, text="操作控制", padding="10")
        self.app = app
        self.config = Config
        
        self._create_buttons()
        self._init_button_states()
    
    def _create_buttons(self):
        """创建所有按钮"""
        # 按钮区域
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X)
        
        # 第一行按钮
        first_row = ttk.Frame(button_frame)
        first_row.pack(fill=tk.X, pady=(0, 5))
        
        self.scan_button = ttk.Button(
            first_row, 
            text=f"{self.config.ICONS['scan']} 开始扫描", 
            command=self.app.start_scan, 
            width=15
        )
        self.scan_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.analyze_button = ttk.Button(
            first_row, 
            text=f"{self.config.ICONS['analyze']} 统计分析", 
            command=self.app.start_analyze, 
            width=15
        )
        self.analyze_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.upload_button = ttk.Button(
            first_row, 
            text=f"{self.config.ICONS['upload']} 全部上传", 
            command=lambda: self.app.start_upload("all"), 
            width=15
        )
        self.upload_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 第二行按钮
        second_row = ttk.Frame(button_frame)
        second_row.pack(fill=tk.X, pady=(0, 5))
        
        self.upload_selected_button = ttk.Button(
            second_row, 
            text=f"{self.config.ICONS['confirm']} 上传选中", 
            command=lambda: self.app.start_upload("selected"), 
            width=15
        )
        self.upload_selected_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.upload_failed_button = ttk.Button(
            second_row, 
            text=f"{self.config.ICONS['retry']} 重传失败", 
            command=lambda: self.app.start_upload("failed"), 
            width=15
        )
        self.upload_failed_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(
            second_row, 
            text=f"{self.config.ICONS['clear']} 清空重置", 
            command=self.app.clear_all_data, 
            width=15
        )
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 第三行按钮
        third_row = ttk.Frame(button_frame)
        third_row.pack(fill=tk.X)
        
        self.export_button = ttk.Button(
            third_row, 
            text=f"{self.config.ICONS['export']} 导出结果", 
            command=self.app.export_results, 
            width=15
        )
        self.export_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.debug_button = ttk.Button(
            third_row, 
            text=f"{self.config.ICONS['debug']} 调试模式", 
            command=self.app.toggle_debug_mode, 
            width=15
        )
        self.debug_button.pack(side=tk.LEFT)
    
    def _init_button_states(self):
        """初始化按钮状态"""
        self.scan_button.config(state='normal')
        self.analyze_button.config(state='disabled')
        self.upload_button.config(state='disabled')
        self.upload_selected_button.config(state='disabled')
        self.upload_failed_button.config(state='disabled')
        self.export_button.config(state='disabled')
        self.clear_button.config(state='normal')
        self.debug_button.config(state='normal')
    
    def update_button_states(self, can_scan=True, can_analyze=False, 
                           can_upload=False, has_failed_data=False,
                           has_selected_data=False, can_export=False):
        """
        更新按钮状态
        
        Args:
            can_scan: 是否可以扫描
            can_analyze: 是否可以分析
            can_upload: 是否可以上传
            has_failed_data: 是否有失败数据
            has_selected_data: 是否有选中数据
            can_export: 是否可以导出
        """
        self.scan_button.config(state='normal' if can_scan else 'disabled')
        self.analyze_button.config(state='normal' if can_analyze else 'disabled')
        self.upload_button.config(state='normal' if can_upload else 'disabled')
        self.upload_selected_button.config(state='normal' if has_selected_data else 'disabled')
        self.upload_failed_button.config(state='normal' if has_failed_data else 'disabled')
        self.export_button.config(state='normal' if can_export else 'disabled')