# -*- coding: utf-8 -*-
"""
文件扫描模块
负责扫描目录、检测文件变化等
"""

import os
import threading
from typing import List, Tuple, Callable, Optional
from config.settings import Config
from utils.event_bus import event_bus, Events, ProgressEventData, LogEventData


class FileScanner:
    """文件扫描器，负责扫描目录并检测文件变化"""
    
    def __init__(self):
        self.config = Config
        self._lock = threading.RLock()
        self._is_scanning = False
        self._stop_flag = False
    
    def _canon_path(self, path: str) -> str:
        """规范化路径"""
        return os.path.normcase(os.path.abspath(path))
    
    def _is_debug_file(self, filename: str) -> bool:
        """检查是否为debug文件"""
        return filename.lower().startswith(self.config.DEBUG_FILE_PREFIX)
    
    def scan_directory(self, directory: str, 
                      discovered_files: set = None) -> Tuple[List[str], List[str]]:
        """
        扫描目录，返回新增和删除的文件
        
        Args:
            directory: 要扫描的目录
            discovered_files: 已知的文件集合（用于增量检测）
            
        Returns:
            (new_files, deleted_files)
        """
        if not os.path.exists(directory):
            raise FileNotFoundError(f"目录不存在: {directory}")
        
        with self._lock:
            self._is_scanning = True
            self._stop_flag = False
        
        try:
            return self._do_scan(directory, discovered_files or set())
        finally:
            with self._lock:
                self._is_scanning = False
    
    def _do_scan(self, directory: str, known_files: set) -> Tuple[List[str], List[str]]:
        """执行实际的扫描工作"""
        event_bus.publish(Events.SCAN_STARTED, LogEventData(
            message=f"开始扫描目录: {directory}",
            level="INFO"
        ))
        
        # 统计总目录数用于进度显示
        total_dirs = self._count_directories(directory)
        current_dir = 0
        
        # 本次扫描发现的文件集合
        discovered_set = set()
        new_files = []
        
        try:
            for root, dirs, files in os.walk(directory):
                if self._stop_flag:
                    break
                
                current_dir += 1
                
                # 发布进度事件
                event_bus.publish(Events.SCAN_PROGRESS, ProgressEventData(
                    current=current_dir,
                    total=total_dirs,
                    message=f"扫描路径: {root}"
                ))
                
                for file in files:
                    if self._is_debug_file(file):
                        file_path = self._canon_path(os.path.join(root, file))
                        discovered_set.add(file_path)
                        
                        # 检查是否为新文件
                        if file_path not in known_files:
                            new_files.append(file_path)
            
            # 计算删除的文件
            deleted_files = list(known_files - discovered_set)
            
            # 发布完成事件
            event_bus.publish(Events.SCAN_COMPLETED, {
                'new_files': len(new_files),
                'deleted_files': len(deleted_files),
                'total_files': len(discovered_set)
            })
            
            event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                message=f"扫描完成！新增 {len(new_files)} 个，删除 {len(deleted_files)} 个，总共 {len(discovered_set)} 个文件",
                level="SUCCESS"
            ))
            
            return new_files, deleted_files
            
        except Exception as e:
            event_bus.publish(Events.SCAN_ERROR, LogEventData(
                message=f"扫描过程中出错: {str(e)}",
                level="ERROR"
            ))
            raise
    
    def _count_directories(self, directory: str) -> int:
        """统计目录数量，用于进度计算"""
        count = 0
        try:
            for root, dirs, files in os.walk(directory):
                count += 1
                if count > 1000:  # 避免在大目录上花费太多时间
                    break
        except Exception:
            return 1
        return max(count, 1)
    
    def stop_scan(self):
        """停止当前扫描"""
        with self._lock:
            self._stop_flag = True
    
    def is_scanning(self) -> bool:
        """检查是否正在扫描"""
        with self._lock:
            return self._is_scanning


class AsyncFileScanner:
    """异步文件扫描器，在后台线程中执行扫描"""
    
    def __init__(self, scanner: FileScanner):
        self.scanner = scanner
        self._scan_thread: Optional[threading.Thread] = None
    
    def start_scan(self, directory: str, known_files: set = None, 
                   callback: Callable = None):
        """
        启动异步扫描
        
        Args:
            directory: 要扫描的目录
            known_files: 已知文件集合
            callback: 完成回调函数 callback(new_files, deleted_files)
        """
        if self._scan_thread and self._scan_thread.is_alive():
            self.scanner.stop_scan()
            self._scan_thread.join(timeout=1.0)
        
        def scan_worker():
            try:
                new_files, deleted_files = self.scanner.scan_directory(
                    directory, known_files
                )
                if callback:
                    callback(new_files, deleted_files)
            except Exception as e:
                event_bus.publish(Events.SCAN_ERROR, LogEventData(
                    message=f"异步扫描失败: {str(e)}",
                    level="ERROR"
                ))
        
        self._scan_thread = threading.Thread(target=scan_worker, daemon=True)
        self._scan_thread.start()
    
    def stop_scan(self):
        """停止异步扫描"""
        self.scanner.stop_scan()
        if self._scan_thread and self._scan_thread.is_alive():
            self._scan_thread.join(timeout=2.0)
    
    def is_scanning(self) -> bool:
        """检查是否正在扫描"""
        return self.scanner.is_scanning()