# -*- coding: utf-8 -*-
"""
配置管理模块
集中管理所有配置参数
"""


class Config:
    """应用程序配置类"""
    
    # 正则表达式模式
    PATTERNS = [
        r'【日志内容】：源码：\s*\^(.*?)\^',
        r'【日志内容】：源码：\s*\^([^"^"]*?)\^',
        r'【日志内容】：源码：[\s]*\^(.*?)\^',
        r'【日志内容】：源码：\s*\^(.+?)\^',
    ]
    
    # 上传配置
    UPLOAD_URL = "http://xbmonitor1.xingbangtech.com:800/XB/DataUpload"
    UPLOAD_TIMEOUT = 30
    
    # 3DES配置
    DES3_KEY = b"jadl12345678912345678912"  # 24字节密钥
    
    # UI配置
    WINDOW_SIZE = "1000x700"
    WINDOW_TITLE = "文件内容提取与上传工具 - 增强版"
    
    # 文件处理配置
    SUPPORTED_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'latin1', 'cp1252']
    DEBUG_FILE_PREFIX = "debug"
    
    # 性能配置
    CHUNK_SIZE = 4096
    MAX_WORKERS = 4
    PROGRESS_UPDATE_INTERVAL = 100  # ms
    
    # 日志配置
    LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%H:%M:%S"
    
    # UI图标配置
    ICONS = {
        'scan': '🔍',
        'analyze': '📊',
        'upload': '⬆️',
        'confirm': '✅',
        'retry': '🔄',
        'clear': '🗑️',
        'export': '💾',
        'debug': '🔧',
        'file': '📁',
        'match': '🎯',
        'success': '✅',
        'failed': '❌',
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '❌'
    }
    
    @classmethod
    def get_pattern_compiled(cls):
        """获取编译后的正则表达式"""
        import re
        return [re.compile(pattern, re.DOTALL | re.MULTILINE) for pattern in cls.PATTERNS]