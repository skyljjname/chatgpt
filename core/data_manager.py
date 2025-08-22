# -*- coding: utf-8 -*-
"""
数据管理模块
负责管理文件数据、上传状态、选择状态等
"""

import os
import threading
from typing import Dict, Set, List, Tuple, Optional
from utils.event_bus import event_bus, Events, EventData


class DataManager:
    """数据管理器，负责管理所有数据状态"""
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # 核心数据
        self.scanned_files: Set[str] = set()                    # 已扫描文件（规范化路径）
        self.file_match_data: Dict[str, List[str]] = {}         # 文件匹配数据
        self.upload_status: Dict[str, Dict[int, str]] = {}      # 上传状态 {file_path: {data_index: status}}
        self.failed_data: Dict[str, Dict[int, str]] = {}        # 失败数据 {file_path: {data_index: error_msg}}
        
        # 选择状态
        self.selected_files: Set[str] = set()                   # 选中的文件
        self.selected_data: Dict[str, Set[int]] = {}            # 选中的数据 {file_path: {data_indices}}
        
        # 映射关系
        self.item_to_path: Dict[str, str] = {}                  # UI项目ID到路径的映射
        self.path_to_item: Dict[str, str] = {}                  # 路径到UI项目ID的映射
    
    def _canon_path(self, path: str) -> str:
        """规范化路径"""
        return os.path.normcase(os.path.abspath(path))
    
    def add_scanned_files(self, files: List[str]) -> List[str]:
        """
        添加扫描到的文件
        
        Args:
            files: 文件路径列表
            
        Returns:
            新增的文件列表
        """
        with self._lock:
            new_files = []
            for file_path in files:
                canon_path = self._canon_path(file_path)
                if canon_path not in self.scanned_files:
                    self.scanned_files.add(canon_path)
                    new_files.append(canon_path)
            
            if new_files:
                event_bus.publish(Events.DATA_UPDATED, EventData(
                    type="files_added",
                    files=new_files
                ))
            
            return new_files
    
    def remove_scanned_files(self, files: List[str]) -> List[str]:
        """
        移除扫描文件（文件已删除）
        
        Args:
            files: 要移除的文件路径列表
            
        Returns:
            实际移除的文件列表
        """
        with self._lock:
            removed_files = []
            for file_path in files:
                canon_path = self._canon_path(file_path)
                if canon_path in self.scanned_files:
                    self.scanned_files.discard(canon_path)
                    
                    # 清理相关数据
                    self.file_match_data.pop(canon_path, None)
                    self.upload_status.pop(canon_path, None)
                    self.failed_data.pop(canon_path, None)
                    self.selected_files.discard(canon_path)
                    self.selected_data.pop(canon_path, None)
                    
                    removed_files.append(canon_path)
            
            if removed_files:
                event_bus.publish(Events.DATA_UPDATED, EventData(
                    type="files_removed",
                    files=removed_files
                ))
            
            return removed_files
    
    def set_file_matches(self, file_path: str, matches: List[str]):
        """
        设置文件匹配数据
        
        Args:
            file_path: 文件路径
            matches: 匹配内容列表
        """
        with self._lock:
            canon_path = self._canon_path(file_path)
            self.file_match_data[canon_path] = matches
            
            event_bus.publish(Events.DATA_UPDATED, EventData(
                type="matches_updated",
                file_path=canon_path,
                matches_count=len(matches)
            ))
    
    def get_file_matches(self, file_path: str) -> List[str]:
        """获取文件匹配数据"""
        canon_path = self._canon_path(file_path)
        return self.file_match_data.get(canon_path, [])
    
    def get_all_matches(self) -> List[Tuple[str, int, str]]:
        """
        获取所有匹配数据
        
        Returns:
            [(file_path, data_index, match_data), ...]
        """
        with self._lock:
            all_matches = []
            for file_path, matches in self.file_match_data.items():
                for i, match in enumerate(matches):
                    all_matches.append((file_path, i, match))
            return all_matches
    
    def mark_upload_status(self, file_path: str, data_index: int, 
                          status: str, error_msg: Optional[str] = None):
        """
        标记上传状态
        
        Args:
            file_path: 文件路径
            data_index: 数据索引
            status: 状态 ('success', 'failed')
            error_msg: 错误信息（失败时）
        """
        with self._lock:
            canon_path = self._canon_path(file_path)
            
            if canon_path not in self.upload_status:
                self.upload_status[canon_path] = {}
            if canon_path not in self.failed_data:
                self.failed_data[canon_path] = {}
            
            self.upload_status[canon_path][data_index] = status
            
            if status == 'success':
                # 成功时清除失败记录
                self.failed_data[canon_path].pop(data_index, None)
                if not self.failed_data[canon_path]:
                    self.failed_data.pop(canon_path, None)
            elif status == 'failed' and error_msg:
                # 失败时记录错误信息
                self.failed_data[canon_path][data_index] = error_msg
            
            event_bus.publish(Events.DATA_UPDATED, EventData(
                type="upload_status_updated",
                file_path=canon_path,
                data_index=data_index,
                status=status
            ))
    
    def get_upload_stats(self) -> Dict[str, int]:
        """
        获取上传统计
        
        Returns:
            统计信息字典
        """
        with self._lock:
            stats = {
                'total_files': len(self.scanned_files),
                'files_with_matches': len(self.file_match_data),
                'total_matches': sum(len(matches) for matches in self.file_match_data.values()),
                'uploaded_success': 0,
                'uploaded_failed': 0
            }
            
            for file_status in self.upload_status.values():
                for status in file_status.values():
                    if status == 'success':
                        stats['uploaded_success'] += 1
                    elif status == 'failed':
                        stats['uploaded_failed'] += 1
            
            return stats
    
    def get_failed_data(self) -> List[Tuple[str, int, str]]:
        """
        获取所有失败数据
        
        Returns:
            [(file_path, data_index, match_data), ...]
        """
        with self._lock:
            failed_items = []
            for file_path, failed_indices in self.failed_data.items():
                matches = self.file_match_data.get(file_path, [])
                for data_index in failed_indices:
                    if data_index < len(matches):
                        failed_items.append((file_path, data_index, matches[data_index]))
            return failed_items
    
    def toggle_file_selection(self, file_path: str) -> bool:
        """
        切换文件选择状态
        
        Args:
            file_path: 文件路径
            
        Returns:
            选择后的状态
        """
        with self._lock:
            canon_path = self._canon_path(file_path)
            
            if canon_path in self.selected_files:
                # 取消选择
                self.selected_files.discard(canon_path)
                self.selected_data.pop(canon_path, None)
                selected = False
            else:
                # 选择文件及其所有数据
                self.selected_files.add(canon_path)
                matches = self.file_match_data.get(canon_path, [])
                if matches:
                    self.selected_data[canon_path] = set(range(len(matches)))
                selected = True
            
            event_bus.publish(Events.SELECTION_CHANGED, EventData(
                type="file_selection",
                file_path=canon_path,
                selected=selected
            ))
            
            return selected
    
    def toggle_data_selection(self, file_path: str, data_index: int) -> bool:
        """
        切换数据选择状态
        
        Args:
            file_path: 文件路径
            data_index: 数据索引
            
        Returns:
            选择后的状态
        """
        with self._lock:
            canon_path = self._canon_path(file_path)
            
            if canon_path not in self.selected_data:
                self.selected_data[canon_path] = set()
            
            if data_index in self.selected_data[canon_path]:
                # 取消选择
                self.selected_data[canon_path].discard(data_index)
                if not self.selected_data[canon_path]:
                    self.selected_data.pop(canon_path, None)
                    self.selected_files.discard(canon_path)
                selected = False
            else:
                # 选择数据
                self.selected_data[canon_path].add(data_index)
                self.selected_files.add(canon_path)
                selected = True
            
            event_bus.publish(Events.SELECTION_CHANGED, EventData(
                type="data_selection",
                file_path=canon_path,
                data_index=data_index,
                selected=selected
            ))
            
            return selected
    
    def get_selected_data(self) -> List[Tuple[str, int, str]]:
        """
        获取所有选中的数据
        
        Returns:
            [(file_path, data_index, match_data), ...]
        """
        with self._lock:
            selected_items = []
            for file_path, data_indices in self.selected_data.items():
                matches = self.file_match_data.get(file_path, [])
                for data_index in data_indices:
                    if data_index < len(matches):
                        selected_items.append((file_path, data_index, matches[data_index]))
            return selected_items
    
    def select_all_files(self):
        """选择所有文件"""
        with self._lock:
            self.selected_files = self.scanned_files.copy()
            self.selected_data = {}
            
            for file_path, matches in self.file_match_data.items():
                if matches:
                    self.selected_data[file_path] = set(range(len(matches)))
            
            event_bus.publish(Events.SELECTION_CHANGED, EventData(
                type="select_all"
            ))
    
    def clear_all_selections(self):
        """清空所有选择"""
        with self._lock:
            self.selected_files.clear()
            self.selected_data.clear()
            
            event_bus.publish(Events.SELECTION_CHANGED, EventData(
                type="clear_all"
            ))
    
    def select_failed_data(self):
        """选择所有失败的数据"""
        with self._lock:
            self.selected_files.clear()
            self.selected_data.clear()
            
            for file_path, failed_indices in self.failed_data.items():
                if failed_indices:
                    self.selected_files.add(file_path)
                    self.selected_data[file_path] = set(failed_indices.keys())
            
            event_bus.publish(Events.SELECTION_CHANGED, EventData(
                type="select_failed"
            ))
    
    def clear_all_data(self):
        """清空所有数据"""
        with self._lock:
            self.scanned_files.clear()
            self.file_match_data.clear()
            self.upload_status.clear()
            self.failed_data.clear()
            self.selected_files.clear()
            self.selected_data.clear()
            self.item_to_path.clear()
            self.path_to_item.clear()
            
            event_bus.publish(Events.DATA_UPDATED, EventData(
                type="all_cleared"
            ))