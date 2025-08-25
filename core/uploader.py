# -*- coding: utf-8 -*-
"""
上传模块
负责数据上传、重传等功能
"""

import json
import requests
import threading
import random
from typing import List, Tuple, Callable, Optional, Dict
from config.settings import Config
from utils.event_bus import event_bus, Events, ProgressEventData, LogEventData, UploadEventData


class MockResponse:
    """模拟响应类，用于测试"""
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text


class DataUploader:
    """数据上传器，负责上传数据到服务器"""
    
    def __init__(self):
        self.config = Config
        self.upload_url = self.config.UPLOAD_URL
        self.timeout = self.config.UPLOAD_TIMEOUT
        self._lock = threading.RLock()
        self._is_uploading = False
        self._stop_flag = False
        self.debug_mode = True  # 使用模拟上传进行测试
    
    def _clean_data_for_upload(self, data: str) -> str:
        """
        清理上传数据，去除首尾特殊字符
        
        Args:
            data: 原始数据
            
        Returns:
            清理后的数据
        """
        if not data:
            return data
        
        special_chars = ' \t\n\r\f\v\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x7f'
        cleaned_data = data.strip(special_chars)
        
        if self.debug_mode and cleaned_data != data:
            event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                message=f"数据清理: 原长度={len(data)}, 清理后长度={len(cleaned_data)}",
                level="DEBUG"
            ))
        
        return cleaned_data
    
    def upload_single(self, data: str, index: int = 0) -> Tuple[bool, Optional[str]]:
        """
        上传单条数据
        
        Args:
            data: 要上传的数据
            index: 数据索引（用于日志）
            
        Returns:
            (成功标志, 错误信息)
        """
        try:
            # 清理数据
            cleaned_data = self._clean_data_for_upload(data)
            payload = {"param": cleaned_data}
            
            if self.debug_mode:
                event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                    message=f"上传数据 #{index}: 长度={len(cleaned_data)}, 前20字符='{cleaned_data[:20]}...'",
                    level="DEBUG"
                ))
            
            # 执行上传请求
            if self.debug_mode:
                # 模拟上传响应
                response = self._simulate_upload_response()
            else:
                # 实际上传
                # response = requests.post(self.upload_url, json=payload, timeout=self.timeout)
                pass
            
            # 处理响应
            return self._handle_upload_response(response, index)
            
        except requests.exceptions.Timeout:
            error_msg = "请求超时"
        except requests.exceptions.RequestException as e:
            error_msg = f"网络错误: {str(e)[:30]}..."
        except Exception as e:
            error_msg = f"未知错误: {str(e)[:30]}..."
        
        # 记录失败
        event_bus.publish(Events.LOG_MESSAGE, LogEventData(
            message=f"#{index:04d} 失败: {error_msg}",
            level="ERROR"
        ))
        
        return False, error_msg
    
    def _simulate_upload_response(self) -> MockResponse:
        """模拟上传响应，用于测试"""
        if random.random() > 0.1:  # 90% 成功率
            response_body = {"success": "1", "message": "上传成功 (Simulated)"}
        else:  # 10% 失败率
            response_body = {"success": "0", "message": "写入数据库失败，解码失败 (Simulated)"}
        
        return MockResponse(200, json.dumps(response_body))
    
    def _handle_upload_response(self, response, index: int) -> Tuple[bool, Optional[str]]:
        """
        处理上传响应
        
        Args:
            response: HTTP响应对象
            index: 数据索引
            
        Returns:
            (成功标志, 错误信息)
        """
        if response.status_code == 200:
            try:
                data = json.loads(response.text)
                # 检查业务成功标志，兼容 "1" 和 1
                if str(data.get("success")) == "1":
                    message = data.get("message", "成功")
                    event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                        message=f"#{index:04d} 成功: {message}",
                        level="SUCCESS"
                    ))
                    return True, None
                else:
                    # 业务失败
                    error_msg = data.get("message", "未知业务错误")
            except json.JSONDecodeError:
                error_msg = f"无效JSON响应: {response.text[:50]}..."
        else:
            # HTTP层面失败
            error_msg = f"状态码{response.status_code}: {response.text[:50]}..."
        
        event_bus.publish(Events.LOG_MESSAGE, LogEventData(
            message=f"#{index:04d} 失败: {error_msg}",
            level="ERROR"
        ))
        
        return False, error_msg
    
    def upload_batch(self, data_items: List[Tuple[str, int, str]], 
                    skip_uploaded: bool = False,
                    upload_status: Dict = None,
                    progress_callback: Callable = None) -> Dict[str, int]:
        """
        批量上传数据
        
        Args:
            data_items: [(file_path, data_index, data), ...]
            skip_uploaded: 是否跳过已上传的数据
            upload_status: 当前上传状态 {file_path: {data_index: status}}
            progress_callback: 进度回调函数
            
        Returns:
            统计信息字典
        """
        with self._lock:
            self._is_uploading = True
            self._stop_flag = False
        
        try:
            return self._do_batch_upload(data_items, skip_uploaded, upload_status, progress_callback)
        finally:
            with self._lock:
                self._is_uploading = False
    
    def _do_batch_upload(self, data_items: List[Tuple[str, int, str]], 
                        skip_uploaded: bool, upload_status: Dict,
                        progress_callback: Callable) -> Dict[str, int]:
        """执行批量上传"""
        event_bus.publish(Events.UPLOAD_STARTED, LogEventData(
            message="开始批量上传数据...",
            level="INFO"
        ))
        
        stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        total_items = len(data_items)
        
        for i, (file_path, data_index, data) in enumerate(data_items):
            if self._stop_flag:
                break
            
            current_index = i + 1
            
            # 发布进度
            event_bus.publish(Events.UPLOAD_PROGRESS, ProgressEventData(
                current=current_index,
                total=total_items,
                message=f"上传第 {current_index}/{total_items} 项"
            ))
            
            # 检查是否跳过已上传数据
            if (skip_uploaded and upload_status and 
                upload_status.get(file_path, {}).get(data_index) == 'success'):
                stats['skipped'] += 1
                event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                    message=f"跳过第 {current_index}/{total_items} 项（已上传）",
                    level="INFO"
                ))
                continue
            
            # 执行上传
            success, error_msg = self.upload_single(data, current_index)
            
            if success:
                stats['success'] += 1
                event_bus.publish(Events.UPLOAD_SUCCESS, UploadEventData(
                    file_path=file_path,
                    data_index=data_index,
                    success=True
                ))
            else:
                stats['failed'] += 1
                event_bus.publish(Events.UPLOAD_FAILED, UploadEventData(
                    file_path=file_path,
                    data_index=data_index,
                    success=False,
                    error_msg=error_msg
                ))
            
            # 调用进度回调
            if progress_callback:
                progress_callback(file_path, data_index, success, error_msg)
        
        # 发布完成事件
        event_bus.publish(Events.UPLOAD_COMPLETED, stats)
        
        status_msg = f"成功: {stats['success']}"
        if stats['skipped'] > 0:
            status_msg += f", 跳过: {stats['skipped']}"
        if stats['failed'] > 0:
            status_msg += f", 失败: {stats['failed']}"
        
        event_bus.publish(Events.LOG_MESSAGE, LogEventData(
            message=f"批量上传完成！{status_msg}",
            level="SUCCESS"
        ))
        
        return stats
    
    def retry_failed_uploads(self, failed_items: List[Tuple[str, int, str]],
                           progress_callback: Callable = None) -> Dict[str, int]:
        """
        重试失败的上传
        
        Args:
            failed_items: 失败的数据项 [(file_path, data_index, data), ...]
            progress_callback: 进度回调函数
            
        Returns:
            统计信息字典
        """
        event_bus.publish(Events.LOG_MESSAGE, LogEventData(
            message="开始重传失败数据...",
            level="INFO"
        ))
        
        return self.upload_batch(failed_items, skip_uploaded=False, 
                               progress_callback=progress_callback)
    
    def stop_upload(self):
        """停止当前上传"""
        with self._lock:
            self._stop_flag = True
    
    def is_uploading(self) -> bool:
        """检查是否正在上传"""
        with self._lock:
            return self._is_uploading
    
    def set_debug_mode(self, enabled: bool):
        """设置调试模式（启用/禁用模拟上传）"""
        self.debug_mode = enabled


class AsyncDataUploader:
    """异步数据上传器，在后台线程中执行上传"""
    
    def __init__(self, uploader: DataUploader):
        self.uploader = uploader
        self._upload_thread: Optional[threading.Thread] = None
    
    def start_upload(self, data_items: List[Tuple[str, int, str]], 
                    skip_uploaded: bool = False,
                    upload_status: Dict = None,
                    callback: Callable = None,
                    progress_callback: Callable = None):
        """
        启动异步上传
        
        Args:
            data_items: 要上传的数据项
            skip_uploaded: 是否跳过已上传数据
            upload_status: 当前上传状态
            callback: 完成回调函数 callback(stats)
            progress_callback: 进度回调函数
        """
        if self._upload_thread and self._upload_thread.is_alive():
            self.uploader.stop_upload()
            self._upload_thread.join(timeout=2.0)
        
        def upload_worker():
            try:
                stats = self.uploader.upload_batch(
                    data_items, skip_uploaded, upload_status, progress_callback
                )
                if callback:
                    callback(stats)
            except Exception as e:
                event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                    message=f"异步上传失败: {str(e)}",
                    level="ERROR"
                ))
        
        self._upload_thread = threading.Thread(target=upload_worker, daemon=True)
        self._upload_thread.start()
    
    def start_retry(self, failed_items: List[Tuple[str, int, str]],
                   callback: Callable = None,
                   progress_callback: Callable = None):
        """
        启动异步重传
        
        Args:
            failed_items: 失败的数据项
            callback: 完成回调函数
            progress_callback: 进度回调函数
        """
        if self._upload_thread and self._upload_thread.is_alive():
            self.uploader.stop_upload()
            self._upload_thread.join(timeout=2.0)
        
        def retry_worker():
            try:
                stats = self.uploader.retry_failed_uploads(failed_items, progress_callback)
                if callback:
                    callback(stats)
            except Exception as e:
                event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                    message=f"异步重传失败: {str(e)}",
                    level="ERROR"
                ))
        
        self._upload_thread = threading.Thread(target=retry_worker, daemon=True)
        self._upload_thread.start()
    
    def stop_upload(self):
        """停止异步上传"""
        self.uploader.stop_upload()
        if self._upload_thread and self._upload_thread.is_alive():
            self._upload_thread.join(timeout=3.0)
    
    def is_uploading(self) -> bool:
        """检查是否正在上传"""
        return self.uploader.is_uploading()