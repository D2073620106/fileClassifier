import os
import logging
from logging.handlers import RotatingFileHandler
import datetime

from constants import ENABLE_LOGGING, LOG_LEVEL, LOG_FILE

# 开发时日志文件存储在项目目录下的log文件夹中
# 在打包后，日志文件在C:\Users\用户名\AppData\Local\Temp\_MEI422402\log\file_classifier.log
class Logger:
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._setup_logger()
        return cls._instance
    
    @classmethod
    def _setup_logger(cls):
        """设置日志记录器"""
        # 创建日志记录器
        cls._logger = logging.getLogger('file_classifier')
        
        # 设置日志级别
        log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        cls._logger.setLevel(log_level)
        
        # 清除已有的处理器
        if cls._logger.handlers:
            cls._logger.handlers.clear()
        
        if ENABLE_LOGGING:
            # 获取应用程序所在目录
            app_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 创建log目录
            log_dir = os.path.join(app_dir, 'log')
            os.makedirs(log_dir, exist_ok=True)
            
            # 日志文件完整路径
            log_file_path = os.path.join(log_dir, LOG_FILE)
            
            # 创建文件处理器（使用 RotatingFileHandler 限制日志文件大小）
            file_handler = RotatingFileHandler(
                log_file_path, 
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3,  # 保留3个备份文件
                encoding='utf-8'
            )
            
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            
            # 设置日志格式
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 添加处理器到日志记录器
            cls._logger.addHandler(file_handler)
            cls._logger.addHandler(console_handler)
            
            cls._logger.info("日志系统初始化完成")
    
    @classmethod
    def debug(cls, message):
        """记录调试信息"""
        if cls._logger is None:
            cls._setup_logger()
        if ENABLE_LOGGING:
            cls._logger.debug(message)
    
    @classmethod
    def info(cls, message):
        """记录一般信息"""
        if cls._logger is None:
            cls._setup_logger()
        if ENABLE_LOGGING:
            cls._logger.info(message)
    
    @classmethod
    def warning(cls, message):
        """记录警告信息"""
        if cls._logger is None:
            cls._setup_logger()
        if ENABLE_LOGGING:
            cls._logger.warning(message)
    
    @classmethod
    def error(cls, message):
        """记录错误信息"""
        if cls._logger is None:
            cls._setup_logger()
        if ENABLE_LOGGING:
            cls._logger.error(message)
    
    @classmethod
    def critical(cls, message):
        """记录严重错误信息"""
        if cls._logger is None:
            cls._setup_logger()
        if ENABLE_LOGGING:
            cls._logger.critical(message)

# 创建全局日志实例
logger = Logger()