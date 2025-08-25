# -*- coding: utf-8 -*-
"""
内容分析模块
负责分析文件内容，提取匹配数据
"""

import os
import re
import threading
from typing import List, Callable, Optional, Dict
from config.settings import Config
from utils.event_bus import event_bus, Events, ProgressEventData, LogEventData


class ContentAnalyzer:
    """内容分析器，负责从文件中提取匹配内容"""
    
    def __init__(self):
        self.config = Config
        self.patterns = self.config.get_pattern_compiled()
        self._lock = threading.RLock()
        self._is_analyzing = False
        self._stop_flag = False
        self.debug_mode = True
    
    def analyze_file(self, file_path: str) -> List[str]:
        """
        分析单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            匹配内容列表
        """
        matches = []
        
        try:
            # 读取文件内容
            content = self._read_file_with_encoding(file_path)
            if content is None:
                if self.debug_mode:
                    event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                        message=f"无法读取文件 (编码问题): {os.path.basename(file_path)}",
                        level="WARNING"
                    ))
                return matches
            
            # 使用多个正则表达式模式进行匹配
            for i, pattern in enumerate(self.patterns):
                try:
                    pattern_matches = pattern.findall(content)
                    if pattern_matches:
                        matches.extend(pattern_matches)
                        if self.debug_mode:
                            event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                                message=f"模式 {i+1} 在文件 {os.path.basename(file_path)} 中找到 {len(pattern_matches)} 个匹配",
                                level="DEBUG"
                            ))
                        break  # 找到匹配就停止尝试其他模式
                except re.error as regex_error:
                    if self.debug_mode:
                        event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                            message=f"正则表达式错误 (模式 {i+1}): {str(regex_error)}",
                            level="ERROR"
                        ))
                    continue
            
            # 调试信息
            if not matches and self.debug_mode:
                self._debug_file_content(file_path, content)
            
            # 清理匹配结果
            matches = [match.strip() for match in matches if match.strip()]
            
        except Exception as e:
            event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                message=f"处理文件时出错 {os.path.basename(file_path)}: {str(e)}",
                level="ERROR"
            ))
        
        return matches
    
    def analyze_files(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        批量分析文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            {file_path: matches} 字典
        """
        with self._lock:
            self._is_analyzing = True
            self._stop_flag = False
        
        try:
            return self._do_analyze_files(file_paths)
        finally:
            with self._lock:
                self._is_analyzing = False
    
    def _do_analyze_files(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """执行批量文件分析"""
        event_bus.publish(Events.ANALYSIS_STARTED, LogEventData(
            message="开始分析文件内容...",
            level="INFO"
        ))
        
        results = {}
        total_files = len(file_paths)
        total_matches = 0
        
        for i, file_path in enumerate(file_paths):
            if self._stop_flag:
                break
            
            # 发布进度
            event_bus.publish(Events.ANALYSIS_PROGRESS, ProgressEventData(
                current=i + 1,
                total=total_files,
                message=f"分析文件: {os.path.relpath(file_path, os.getcwd())}"
            ))
            
            matches = self.analyze_file(file_path)
            if matches:
                results[file_path] = matches
                total_matches += len(matches)
                
                event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                    message=f"文件 {os.path.basename(file_path)} 找到 {len(matches)} 个匹配项",
                    level="INFO"
                ))
        
        # 发布完成事件
        event_bus.publish(Events.ANALYSIS_COMPLETED, {
            'analyzed_files': len(file_paths),
            'files_with_matches': len(results),
            'total_matches': total_matches
        })
        
        event_bus.publish(Events.LOG_MESSAGE, LogEventData(
            message=f"分析完成！共找到 {total_matches} 个匹配项",
            level="SUCCESS"
        ))
        
        return results
    
    def _read_file_with_encoding(self, file_path: str) -> Optional[str]:
        """
        尝试不同编码读取文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容或None
        """
        for encoding in self.config.SUPPORTED_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                if self.debug_mode:
                    event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                        message=f"使用编码 {encoding} 读取文件: {os.path.basename(file_path)}",
                        level="DEBUG"
                    ))
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                    message=f"读取文件失败 {file_path}: {str(e)}",
                    level="ERROR"
                ))
                break
        return None
    
    def _debug_file_content(self, file_path: str, content: str):
        """调试文件内容，帮助诊断为什么没有匹配"""
        filename = os.path.basename(file_path)
        
        if '【日志内容】' in content:
            event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                message=f"文件 {filename} 包含'【日志内容】'关键字",
                level="DEBUG"
            ))
            
            if '源码：' in content:
                event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                    message=f"文件 {filename} 包含'源码：'关键字",
                    level="DEBUG"
                ))
                
                # 统计^字符数量
                caret_positions = [i for i, char in enumerate(content) if char == '^']
                if len(caret_positions) >= 2:
                    event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                        message=f"文件 {filename} 找到 {len(caret_positions)} 个'^'字符",
                        level="DEBUG"
                    ))
                    
                    # 显示示例内容
                    start_pos = caret_positions[0]
                    end_pos = caret_positions[1] if len(caret_positions) > 1 else len(content)
                    sample_content = content[max(0, start_pos-20):min(len(content), end_pos+20)]
                    event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                        message=f"示例内容: ...{sample_content}...",
                        level="DEBUG"
                    ))
                else:
                    event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                        message=f"文件 {filename} 未找到足够的'^'字符",
                        level="DEBUG"
                    ))
            else:
                event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                    message=f"文件 {filename} 不包含'源码：'关键字",
                    level="DEBUG"
                ))
        else:
            event_bus.publish(Events.LOG_MESSAGE, LogEventData(
                message=f"文件 {filename} 不包含'【日志内容】'关键字",
                level="DEBUG"
            ))
    
    def stop_analysis(self):
        """停止当前分析"""
        with self._lock:
            self._stop_flag = True
    
    def is_analyzing(self) -> bool:
        """检查是否正在分析"""
        with self._lock:
            return self._is_analyzing
    
    def set_debug_mode(self, enabled: bool):
        """设置调试模式"""
        self.debug_mode = enabled


class AsyncContentAnalyzer:
    """异步内容分析器，在后台线程中执行分析"""
    
    def __init__(self, analyzer: ContentAnalyzer):
        self.analyzer = analyzer
        self._analysis_thread: Optional[threading.Thread] = None
    
    def start_analysis(self, file_paths: List[str], callback=None):
        """
        启动异步分析
        
        Args:
            file_paths: 文件路径列表
            callback: 完成回调函数 callback(results)
        """
        if self._analysis_thread and self._analysis_thread.is_alive():
            self.analyzer.stop_analysis()
            self._analysis_thread.join(timeout=1.0)
        
        def analysis_worker():
            try:
                results = self.analyzer.analyze_files(file_paths)
                if callback:
                    callback(results)
            except Exception as e:
                event_bus.publish(Events.ANALYSIS_ERROR, LogEventData(
                    message=f"异步分析失败: {str(e)}",
                    level="ERROR"
                ))
        
        self._analysis_thread = threading.Thread(target=analysis_worker, daemon=True)
        self._analysis_thread.start()
    
    def stop_analysis(self):
        """停止异步分析"""
        self.analyzer.stop_analysis()
        if self._analysis_thread and self._analysis_thread.is_alive():
            self._analysis_thread.join(timeout=2.0)
    
    def is_analyzing(self) -> bool:
        """检查是否正在分析"""
        return self.analyzer.is_analyzing()