# ==================== 项目根目录 __init__.py ====================
# __init__.py (项目根目录)
"""
文件内容提取与上传工具 - 模块化版本
"""

__version__ = "2.0.0"
__author__ = "Developer"
__description__ = "文件内容提取与上传工具 - 增强版模块化架构"

from config import Config
from utils import event_bus, Events
from core import DataManager, FileScanner, ContentAnalyzer, DataUploader, CryptoUtils
from ui import MainApplication

__all__ = [
    'Config', 'event_bus', 'Events',
    'DataManager', 'FileScanner', 'ContentAnalyzer', 'DataUploader', 'CryptoUtils',
    'MainApplication'
]