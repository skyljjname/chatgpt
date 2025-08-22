# -*- coding: utf-8 -*-
"""
主窗口模块
整合所有功能，提供统一的UI界面
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from datetime import datetime

# 导入配置和事件系统
from config.settings import Config
from utils.event_bus import event_bus, Events, ProgressEventData, LogEventData

# 导入核心模块
from core.data_manager import DataManager
from core.file_scanner import FileScanner, AsyncFileScanner
from core.content_analyzer import ContentAnalyzer, AsyncContentAnalyzer
from core.uploader import DataUploader, AsyncDataUploader
from core.crypto_utils import CryptoUtils

# 导入UI组件
from ui.components.control_panel import ControlPanel
from ui.components.progress_panel import ProgressPanel
from ui.components.results_panel import ResultsPanel


class MainApplication:
    """主应用程序类，整合所有功能"""
    
    def __init__(self, root):
        self.root = root
        self.config = Config
        
        # 初始化核心组件
        self._init_core_components()
        
        # 设置主窗口
        self._setup_window()
        
        # 创建UI组件
        self._create_ui_components()
        
        # 绑定事件
        self._bind_events()
        
        # 初始化状态
        self._init_state()
    
    def _init_core_components(self):
        """初始化核心组件"""
        # 数据管理器
        self.data_manager = DataManager()
        
        # 文件扫描器
        self.file_scanner = FileScanner()
        self.async_scanner = AsyncFileScanner(self.file_scanner)
        
        # 内容分析器
        self.content_analyzer = ContentAnalyzer()
        self.async_analyzer = AsyncContentAnalyzer(self.content_analyzer)
        
        # 数据上传器
        self.uploader = DataUploader()
        self.async_uploader = AsyncDataUploader(self.uploader)
        
        # 加密工具
        self.crypto_utils = CryptoUtils()
        
        # 当前工作目录
        self.current_directory = ""
    
    def _setup_window(self):
        """设置主窗口属性"""
        self.root.title(self.config.WINDOW_TITLE)
        self.root.geometry(self.config.WINDOW_SIZE)
        
        # 设置窗口图标（如果有的话）
        try:
            # self.root.iconbitmap("icon.ico")  # 可选
            pass
        except Exception:
            pass
        
        # 设置关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_ui_components(self):
        """创建UI组件"""
        # 创建头部区域
        self._create_header()
        
        # 创建控制面板
        self.control_panel = ControlPanel(self.root, self)
        self.control_panel.pack(fill=tk.X, padx=10, pady=5)
        
        # 创建进度面板
        self.progress_panel = ProgressPanel(self.root)
        self.progress_panel.pack(fill=tk.X, padx=10, pady=5)
        
        # 创建结果面板
        self.results_panel = ResultsPanel(self.root, self)
        self.results_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建日志面板
        self._create_log_panel()
    
    def _create_header(self):
        """创建头部区域"""
        from tkinter import ttk
        
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)
        
        # 标题
        title_label = ttk.Label(header_frame, text="文件内容提取与上传工具", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        # 目录选择
        dir_frame = ttk.LabelFrame(header_frame, text="目录选择", padding="10")
        dir_frame.pack(fill=tk.X, pady=(10, 0))
        
        dir_select_frame = ttk.Frame(dir_frame)
        dir_select_frame.pack(fill=tk.X)
        
        ttk.Label(dir_select_frame, text="目标目录:").pack(side=tk.LEFT)
        
        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(dir_select_frame, textvariable=self.dir_var, width=60)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        ttk.Button(dir_select_frame, text="浏览", 
                  command=self._browse_directory).pack(side=tk.RIGHT)
    
    def _create_log_panel(self):
        """创建日志面板"""
        from tkinter import ttk, scrolledtext
        
        log_frame = ttk.LabelFrame(self.root, text="操作日志", padding="10")
        log_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def _bind_events(self):
        """绑定事件处理"""
        # 进度相关事件
        event_bus.subscribe(Events.SCAN_PROGRESS, self._on_scan_progress)
        event_bus.subscribe(Events.ANALYSIS_PROGRESS, self._on_analysis_progress)
        event_bus.subscribe(Events.UPLOAD_PROGRESS, self._on_upload_progress)
        
        # 状态更新事件
        event_bus.subscribe(Events.SCAN_STARTED, self._on_operation_started)
        event_bus.subscribe(Events.ANALYSIS_STARTED, self._on_operation_started)
        event_bus.subscribe(Events.UPLOAD_STARTED, self._on_operation_started)
        
        # 完成事件
        event_bus.subscribe(Events.SCAN_COMPLETED, self._on_scan_completed)
        event_bus.subscribe(Events.ANALYSIS_COMPLETED, self._on_analysis_completed)
        event_bus.subscribe(Events.UPLOAD_COMPLETED, self._on_upload_completed)
        
        # 上传单项事件
        event_bus.subscribe(Events.UPLOAD_SUCCESS, self._on_upload_item)
        event_bus.subscribe(Events.UPLOAD_FAILED, self._on_upload_item)
        
        # 数据更新事件
        event_bus.subscribe(Events.DATA_UPDATED, self._on_data_updated)
        event_bus.subscribe(Events.SELECTION_CHANGED, self._on_selection_changed)
        
        # 日志事件
        event_bus.subscribe(Events.LOG_MESSAGE, self._on_log_message)
    
    def _init_state(self):
        """初始化状态"""
        self.log_message("应用程序已启动，准备就绪", "SUCCESS")
        self._update_ui_state()
    
    # ==================== 事件处理方法 ====================
    
    def _on_scan_progress(self, data: ProgressEventData):
        """处理扫描进度事件"""
        self.progress_panel.update_progress(data.current, data.total, data.message)
    
    def _on_analysis_progress(self, data: ProgressEventData):
        """处理分析进度事件"""
        self.progress_panel.update_progress(data.current, data.total, data.message)
    
    def _on_upload_progress(self, data: ProgressEventData):
        """处理上传进度事件"""
        self.progress_panel.update_progress(data.current, data.total, data.message)
    
    def _on_operation_started(self, data: LogEventData):
        """处理操作开始事件"""
        self.progress_panel.set_status("进行中", data.message)
        self._update_ui_state()
    
    def _on_scan_completed(self, data):
        """处理扫描完成事件"""
        self.progress_panel.set_status("扫描完成", 
                                     f"新增 {data['new_files']} 个，删除 {data['deleted_files']} 个")
        self._update_ui_state()
    
    def _on_analysis_completed(self, data):
        """处理分析完成事件"""
        self.progress_panel.set_status("分析完成", 
                                     f"找到 {data['total_matches']} 个匹配项")
        self._update_ui_state()
    
    def _on_upload_completed(self, data):
        """处理上传完成事件"""
        status_msg = f"成功: {data['success']}"
        if data.get('skipped', 0) > 0:
            status_msg += f", 跳过: {data['skipped']}"
        if data.get('failed', 0) > 0:
            status_msg += f", 失败: {data['failed']}"
        
        self.progress_panel.set_status("上传完成", status_msg)
        self._update_ui_state()
        
        # 显示完成对话框
        if data.get('failed', 0) > 0:
            messagebox.showwarning("上传完成", 
                                 f"上传完成!\n{status_msg}\n\n可使用'上传失败数据'按钮重传失败的数据。")
        else:
            messagebox.showinfo("上传成功", f"所有 {data['success']} 条数据上传成功!")
    
    def _on_upload_item(self, data):
        """处理单项上传事件"""
        # 更新 data_manager
        self.data_manager.mark_upload_status(
            data.file_path, data.data_index,
            'success' if data.success else 'failed',
            data.error_msg
        )

        # 同步显示到上传结果面板
        self.results_panel.add_upload_result(
            data.file_path, data.data_index,
            data.success, data.error_msg
        )

        # 同步刷新数据详情颜色
        if self.results_panel.current_selected_file == data.file_path:
            self.results_panel._refresh_data_tree()

    
    def _on_data_updated(self, data):
        """处理数据更新事件"""
        self.results_panel.refresh_data()
    
    def _on_selection_changed(self, data):
        """处理选择变化事件"""
        self.results_panel.refresh_selection()
    
    def _on_log_message(self, data: LogEventData):
        """处理日志消息事件"""
        self.log_message(data.message, data.level)
    
    # ==================== UI操作方法 ====================
    
    def _browse_directory(self):
        """浏览目录对话框"""
        directory = filedialog.askdirectory()
        if directory:
            self.dir_var.set(directory)
            self.current_directory = directory
    
    def log_message(self, message: str, level: str = "INFO"):
        """在日志区域添加消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_icons = {
            "INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", 
            "WARNING": "⚠️", "DEBUG": "🔧"
        }
        icon = level_icons.get(level, "ℹ️")
        formatted_message = f"[{timestamp}] {icon} {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def _update_ui_state(self):
        """更新UI状态"""
        # 检查是否有操作正在进行
        is_scanning = self.async_scanner.is_scanning()
        is_analyzing = self.async_analyzer.is_analyzing()
        is_uploading = self.async_uploader.is_uploading()
        
        any_operation = is_scanning or is_analyzing or is_uploading
        
        # 更新控制面板按钮状态
        self.control_panel.update_button_states(
            can_scan=not any_operation,
            can_analyze=not any_operation and len(self.data_manager.scanned_files) > 0,
            can_upload=not any_operation and len(self.data_manager.file_match_data) > 0,
            has_failed_data=len(self.data_manager.failed_data) > 0
        )
        
        # 更新结果面板
        self.results_panel.update_stats()
    
    # ==================== 业务操作方法 ====================
    
    def start_scan(self):
        """开始扫描"""
        directory = self.dir_var.get().strip()
        if not directory:
            messagebox.showerror("错误", "请选择一个目录！")
            return
        
        self.current_directory = directory
        
        def scan_callback(new_files, deleted_files):
            # 更新数据管理器
            self.data_manager.add_scanned_files(new_files)
            self.data_manager.remove_scanned_files(deleted_files)
            self._update_ui_state()
        
        self.async_scanner.start_scan(
            directory, 
            self.data_manager.scanned_files,
            scan_callback
        )
    
    def start_analyze(self):
        """开始分析"""
        if not self.data_manager.scanned_files:
            messagebox.showerror("错误", "请先进行文件扫描！")
            return
        
        def analyze_callback(results):
            # 更新匹配数据
            for file_path, matches in results.items():
                self.data_manager.set_file_matches(file_path, matches)
            self._update_ui_state()
        
        self.async_analyzer.start_analysis(
            list(self.data_manager.scanned_files),
            analyze_callback
        )
    
    def start_upload(self, upload_type: str = "all"):
        """
        开始上传
        
        Args:
            upload_type: 上传类型 ("all", "selected", "failed")
        """
        self.results_panel.upload_tree.delete(*self.results_panel.upload_tree.get_children())

        if upload_type == "all":
            data_items = self.data_manager.get_all_matches()
        elif upload_type == "selected":
            data_items = self.data_manager.get_selected_data()
        elif upload_type == "failed":
            data_items = self.data_manager.get_failed_data()
        else:
            messagebox.showerror("错误", f"未知的上传类型: {upload_type}")
            return
        
        if not data_items:
            messagebox.showinfo("提示", "没有可上传的数据！")
            return
        
        # 检查已上传数据
        if upload_type == "all":
            already_uploaded = self._check_already_uploaded(data_items)
            if already_uploaded:
                choice = self._show_upload_choice_dialog(already_uploaded, len(data_items))
                if choice == "cancel":
                    return
                elif choice == "skip":
                    skip_uploaded = True
                else:  # overwrite
                    skip_uploaded = False
            else:
                skip_uploaded = False
        else:
            skip_uploaded = False
        
        # 确认上传
        if not self._confirm_upload(len(data_items), upload_type):
            return
        
        def upload_callback(stats):
            self._update_ui_state()
        
        def progress_callback(file_path, data_index, success, error_msg):
            # 进度回调在事件处理中已经处理
            pass
        
        self.async_uploader.start_upload(
            data_items,
            skip_uploaded,
            self.data_manager.upload_status,
            upload_callback,
            progress_callback
        )
    
    def _check_already_uploaded(self, data_items):
        """检查已上传的数据"""
        already_uploaded = []
        for file_path, data_index, _ in data_items:
            if self.data_manager.upload_status.get(file_path, {}).get(data_index) == 'success':
                already_uploaded.append((file_path, data_index))
        return already_uploaded
    
    def _show_upload_choice_dialog(self, already_uploaded, total_count):
        """显示上传选择对话框"""
        # 这里应该创建一个自定义对话框
        # 为简化，直接使用messagebox
        message = f"发现 {len(already_uploaded)} 条数据已经上传过。\n\n"
        message += f"总数据: {total_count} 条\n"
        message += f"已上传: {len(already_uploaded)} 条\n"
        message += f"未上传: {total_count - len(already_uploaded)} 条\n\n"
        message += "选择操作："
        
        result = messagebox.askyesnocancel(
            "上传确认", 
            message + "\n\n是: 重新上传所有数据\n否: 只上传未上传数据\n取消: 取消上传"
        )
        
        if result is True:
            return "overwrite"
        elif result is False:
            return "skip"
        else:
            return "cancel"
    
    def _confirm_upload(self, count, upload_type):
        """确认上传操作"""
        type_names = {
            "all": "全部",
            "selected": "选中",
            "failed": "失败"
        }
        
        return messagebox.askyesno(
            "确认上传",
            f"即将上传 {count} 条{type_names[upload_type]}数据到服务器。\n\n"
            f"上传地址: {self.config.UPLOAD_URL}\n\n"
            "确定要继续吗？"
        )
    
    def clear_all_data(self):
        """清空所有数据"""
        if messagebox.askyesno("确认", "确定要清空所有数据并重置吗？"):
            self.data_manager.clear_all_data()
            self.log_text.delete(1.0, tk.END)
            self._update_ui_state()
            self.log_message("所有数据已清空，状态已重置", "SUCCESS")
    
    def toggle_debug_mode(self):
        """切换调试模式"""
        current_mode = self.content_analyzer.debug_mode
        new_mode = not current_mode
        
        self.content_analyzer.set_debug_mode(new_mode)
        self.uploader.set_debug_mode(new_mode)
        self.crypto_utils.set_debug_mode(new_mode)
        
        mode_text = "开启" if new_mode else "关闭"
        self.log_message(f"调试模式已{mode_text}", "INFO")
    
    def export_results(self):
        """导出结果"""
        if not self.data_manager.file_match_data:
            messagebox.showerror("错误", "没有可导出的数据！")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            self._do_export_results(filename)
    
    def _do_export_results(self, filename):
        """执行导出操作"""
        try:
            stats = self.data_manager.get_upload_stats()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("文件内容提取结果报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"扫描目录: {self.current_directory}\n")
                f.write(f"总文件数: {stats['total_files']}\n")
                f.write(f"有匹配文件数: {stats['files_with_matches']}\n")
                f.write(f"总匹配条目数: {stats['total_matches']}\n")
                f.write(f"成功上传: {stats['uploaded_success']}\n")
                f.write(f"上传失败: {stats['uploaded_failed']}\n\n")
                
                f.write("详细统计:\n")
                f.write("-" * 30 + "\n")
                
                for file_path, matches in self.data_manager.file_match_data.items():
                    import os
                    rel_path = os.path.relpath(file_path, self.current_directory) if self.current_directory else file_path
                    
                    f.write(f"\n文件: {os.path.basename(file_path)}\n")
                    f.write(f"路径: {rel_path}\n")
                    f.write(f"匹配数: {len(matches)}\n")
                    
                    # 添加上传状态信息
                    if file_path in self.data_manager.upload_status:
                        success_count = sum(1 for status in self.data_manager.upload_status[file_path].values() if status == 'success')
                        failed_count = sum(1 for status in self.data_manager.upload_status[file_path].values() if status == 'failed')
                        f.write(f"上传成功: {success_count}, 上传失败: {failed_count}\n")
                    
                    f.write("匹配内容:\n")
                    for i, match in enumerate(matches, 1):
                        status_indicator = ""
                        if file_path in self.data_manager.upload_status and (i-1) in self.data_manager.upload_status[file_path]:
                            if self.data_manager.upload_status[file_path][i-1] == 'success':
                                status_indicator = " [已上传]"
                            else:
                                status_indicator = " [失败]"
                        f.write(f"  {i:3d}. {match}{status_indicator}\n")
            
            self.log_message(f"结果已导出到: {filename}", "SUCCESS")
            messagebox.showinfo("导出成功", f"结果已成功导出到:\n{filename}")
            
        except Exception as e:
            self.log_message(f"导出失败: {str(e)}", "ERROR")
            messagebox.showerror("导出失败", f"导出过程中出现错误: {str(e)}")
    
    def _on_closing(self):
        """处理窗口关闭事件"""
        # 停止所有正在进行的操作
        self.async_scanner.stop_scan()
        self.async_analyzer.stop_analysis()
        self.async_uploader.stop_upload()
        
        # 清理事件总线
        event_bus.clear_all()
        
        # 关闭窗口
        self.root.destroy()