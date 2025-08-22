# -*- coding: utf-8 -*-
"""
事件系统模块
实现观察者模式，用于模块间通信
"""

import threading
from typing import Callable, Any, Dict, List
from enum import Enum


class Events(Enum):
    """事件类型定义"""
    # 文件扫描相关
    SCAN_STARTED = "scan_started"
    SCAN_PROGRESS = "scan_progress"
    SCAN_COMPLETED = "scan_completed"
    SCAN_ERROR = "scan_error"
    
    # 文件分析相关
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_ERROR = "analysis_error"
    
    # 数据上传相关
    UPLOAD_STARTED = "upload_started"
    UPLOAD_PROGRESS = "upload_progress"
    UPLOAD_SUCCESS = "upload_success"
    UPLOAD_FAILED = "upload_failed"
    UPLOAD_COMPLETED = "upload_completed"
    
    # 数据管理相关
    DATA_UPDATED = "data_updated"
    SELECTION_CHANGED = "selection_changed"
    
    # UI相关
    STATUS_UPDATE = "status_update"
    LOG_MESSAGE = "log_message"


class EventBus:
    """事件总线，用于模块间通信"""
    
    def __init__(self):
        self._listeners: Dict[Events, List[Callable]] = {}
        self._lock = threading.RLock()
    
    def subscribe(self, event_type: Events, callback: Callable):
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: Events, callback: Callable):
        """
        取消订阅
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        with self._lock:
            if event_type in self._listeners:
                try:
                    self._listeners[event_type].remove(callback)
                except ValueError:
                    pass
    
    def publish(self, event_type: Events, data: Any = None):
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        with self._lock:
            listeners = self._listeners.get(event_type, []).copy()
        
        for callback in listeners:
            try:
                if data is not None:
                    callback(data)
                else:
                    callback()
            except Exception as e:
                print(f"Event callback error: {e}")
    
    def clear_all(self):
        """清空所有监听器"""
        with self._lock:
            self._listeners.clear()


# 全局事件总线实例
event_bus = EventBus()


class EventData:
    """事件数据基类"""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class ProgressEventData(EventData):
    """进度事件数据"""
    
    def __init__(self, current: int, total: int, message: str = "", **kwargs):
        super().__init__(**kwargs)
        self.current = current
        self.total = total
        self.message = message
        self.percentage = (current / total * 100) if total > 0 else 0


class LogEventData(EventData):
    """日志事件数据"""
    
    def __init__(self, message: str, level: str = "INFO", **kwargs):
        super().__init__(**kwargs)
        self.message = message
        self.level = level


class UploadEventData(EventData):
    """上传事件数据"""
    
    def __init__(self, file_path: str, data_index: int, success: bool, 
                 error_msg: str = None, **kwargs):
        super().__init__(**kwargs)
        self.file_path = file_path
        self.data_index = data_index
        self.success = success
        self.error_msg = error_msg