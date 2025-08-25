# -*- coding: utf-8 -*-
"""
进度面板组件
显示操作进度和状态信息
"""

import tkinter as tk
from tkinter import ttk


class ProgressPanel(ttk.LabelFrame):
    """进度面板组件，显示进度条和状态信息"""
    
    def __init__(self, parent):
        super().__init__(parent, text="进度状态", padding="10")
        
        self._create_widgets()
        self._init_state()
    
    def _create_widgets(self):
        """创建组件"""
        # 状态信息
        self.status_var = tk.StringVar()
        status_label = ttk.Label(self, textvariable=self.status_var, 
                                font=("Arial", 10, "bold"))
        status_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 当前操作信息
        self.current_operation_var = tk.StringVar()
        current_op_label = ttk.Label(self, textvariable=self.current_operation_var, 
                                    font=("Arial", 9), foreground="blue")
        current_op_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 进度条
        progress_container = ttk.Frame(self)
        progress_container.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_container, mode='determinate')
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        self.progress_label = ttk.Label(progress_container, text="0%", width=6)
        self.progress_label.pack(side=tk.RIGHT, padx=(5, 0))
    
    def _init_state(self):
        """初始化状态"""
        self.status_var.set("准备就绪")
        self.current_operation_var.set("")
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0%")
    
    def set_status(self, status: str, operation: str = ""):
        """
        设置状态信息
        
        Args:
            status: 主状态文本
            operation: 当前操作描述
        """
        self.status_var.set(status)
        self.current_operation_var.set(operation)
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """
        更新进度
        
        Args:
            current: 当前进度
            total: 总进度
            message: 进度消息
        """
        if total > 0:
            progress = (current / total) * 100
            self.progress_bar['value'] = progress
            self.progress_label.config(text=f"{progress:.1f}%")
        else:
            self.progress_bar['value'] = 0
            self.progress_label.config(text="0%")
        
        if message:
            self.current_operation_var.set(message)
    
    def reset_progress(self):
        """重置进度"""
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0%")
        self.current_operation_var.set("")
    
    def complete_progress(self):
        """完成进度"""
        self.progress_bar['value'] = 100
        self.progress_label.config(text="100%")