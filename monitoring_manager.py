import os
import sys
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QMessageBox

from file_watcher import FileWatcher
from logger import logger
from constants import APP_NAME

class MonitoringManager(QObject):
    """文件监听管理器，封装文件监听的核心功能，可被主程序和对话框页面调用"""
    
    # 定义信号
    monitoring_status_changed = pyqtSignal(bool)  # 监听状态变化信号，参数为是否正在监听
    file_classified_signal = pyqtSignal(str, str)  # 文件分类信号，参数为文件路径和目标文件夹
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.file_watcher = None
        self.watcher_thread = None
        logger.info("文件监听管理器初始化完成")
    
    def setup_file_watcher(self):
        """设置文件监视器"""
        # 获取最新的配置
        logger.info("设置文件监视器")
        config = self.config_manager.get_config()
        source_folder = config.get('source_folder', '')
        is_monitoring = config.get('is_monitoring', False)
        
        logger.debug(f"源文件夹: {source_folder}, 监听状态: {is_monitoring}")
        
        # 如果已经有监视器在运行，先停止它
        if self.file_watcher and self.watcher_thread and self.watcher_thread.isRunning():
            logger.info("停止现有的文件监视器")
            self.file_watcher.stop()
            self.watcher_thread.quit()
            self.watcher_thread.wait()
        
        # 创建新的文件监视器
        self.file_watcher = FileWatcher(self.config_manager)
        self.file_watcher.file_classified.connect(self.file_classified_signal)
        logger.debug("创建新的文件监视器实例")
        
        # 创建线程并移动监视器到线程中
        self.watcher_thread = QThread()
        self.file_watcher.moveToThread(self.watcher_thread)
        self.watcher_thread.started.connect(self.file_watcher.start_monitoring)
        logger.debug("创建监视器线程并设置连接")
        
        # 如果配置中设置了自动开始监听，且源文件夹有效，则启动监视器
        if is_monitoring and source_folder and os.path.isdir(source_folder):
            logger.info(f"启动文件监视器线程，监听文件夹: {source_folder}")
            self.watcher_thread.start()
            # 不在这里发送监听状态变化信号，避免重复通知
            # self.monitoring_status_changed.emit(True)
        else:
            if not source_folder:
                logger.warning("未设置源文件夹，无法启动监视器")
            elif not os.path.isdir(source_folder):
                logger.warning(f"源文件夹不存在: {source_folder}，无法启动监视器")
            elif not is_monitoring:
                logger.debug("监听状态为关闭，不启动监视器")
            # 不在这里发送监听状态变化信号，避免重复通知
            # self.monitoring_status_changed.emit(False)
    
    def toggle_monitoring(self, parent_widget=None):
        """切换监听状态
        
        Args:
            parent_widget: 父窗口部件，用于显示消息框，如果为None则使用None作为父窗口
        
        Returns:
            bool: 操作是否成功
        """
        logger.info("切换监听状态")
        config = self.config_manager.get_config()
        source_folder = config.get('source_folder', '')
        
        # 检查是否设置了源文件夹
        if not source_folder or not os.path.isdir(source_folder):
            logger.warning("未设置有效的源文件夹，无法切换监听状态")
            if parent_widget is not None:
                QMessageBox.warning(parent_widget, f'{APP_NAME} - 警告', '请先设置要监听的源文件夹！')
            else:
                QMessageBox.warning(None, f'{APP_NAME} - 警告', '请先设置要监听的源文件夹！')
            return False
        
        # 切换监听状态
        is_monitoring = config.get('is_monitoring', False)
        if is_monitoring:
            logger.info("关闭监听")
            # 停止监听
            if self.file_watcher and self.watcher_thread and self.watcher_thread.isRunning():
                logger.debug("停止文件监视器线程")
                self.file_watcher.stop()
                self.watcher_thread.quit()
                self.watcher_thread.wait()
            
            # 更新配置
            config['is_monitoring'] = False
            self.config_manager.save_config(config)
            logger.debug("更新配置：监听状态设为关闭")
            
            # 发送监听状态变化信号
            self.monitoring_status_changed.emit(False)
        else:
            logger.info(f"开启监听，源文件夹: {source_folder}")
            # 开始监听
            config['is_monitoring'] = True
            self.config_manager.save_config(config)
            logger.debug("更新配置：监听状态设为开启")
            
            # 重新设置文件监视器
            self.setup_file_watcher()
            self.watcher_thread.start()
            logger.debug("启动文件监视器线程")
            
            # 发送监听状态变化信号
            self.monitoring_status_changed.emit(True)
        
        return True
    
    def restore_monitoring_state(self):
        """恢复上次的监听状态"""
        logger.info("恢复上次的监听状态")
        config = self.config_manager.get_config()
        is_monitoring = config.get('is_monitoring', False)
        source_folder = config.get('source_folder', '')
        
        logger.debug(f"配置信息 - 监听状态: {is_monitoring}, 源文件夹: {source_folder}")
        
        # 检查是否设置了源文件夹
        if not source_folder or not os.path.isdir(source_folder):
            logger.warning("未设置有效的源文件夹，无法恢复监听状态")
            # 不在这里发送监听状态变化信号，避免重复通知
            # self.monitoring_status_changed.emit(False)
            return
        
        # 如果上次是开启监听状态，则启动监视器
        if is_monitoring:
            logger.info(f"恢复监听状态：开启监听文件夹 {source_folder}")
            # 重新设置文件监视器，确保使用最新的配置
            self.setup_file_watcher()
            # 启动监视器线程
            if self.watcher_thread and not self.watcher_thread.isRunning():
                logger.debug("启动监视器线程")
                self.watcher_thread.start()
            
            # 不在这里发送监听状态变化信号，避免重复通知
            # self.monitoring_status_changed.emit(True)
        else:
            logger.info("恢复监听状态：保持监听关闭")
            # 不在这里发送监听状态变化信号，避免重复通知
            # self.monitoring_status_changed.emit(False)
    
    def get_monitoring_status(self):
        """获取当前监听状态
        
        Returns:
            bool: 是否正在监听
        """
        config = self.config_manager.get_config()
        return config.get('is_monitoring', False)
    
    def stop_monitoring(self):
        """停止监听
        
        Returns:
            bool: 操作是否成功
        """
        logger.info("停止监听")
        config = self.config_manager.get_config()
        
        # 如果当前不是监听状态，直接返回
        if not config.get('is_monitoring', False):
            logger.debug("当前不是监听状态，无需停止")
            return True
        
        # 停止监听
        if self.file_watcher and self.watcher_thread and self.watcher_thread.isRunning():
            logger.debug("停止文件监视器线程")
            self.file_watcher.stop()
            self.watcher_thread.quit()
            self.watcher_thread.wait()
        
        # 更新配置
        config['is_monitoring'] = False
        self.config_manager.save_config(config)
        logger.debug("更新配置：监听状态设为关闭")
        
        # 发送监听状态变化信号
        self.monitoring_status_changed.emit(False)
        
        return True
    
    def start_monitoring(self):
        """开始监听
        
        Returns:
            bool: 操作是否成功
        """
        logger.info("开始监听")
        config = self.config_manager.get_config()
        source_folder = config.get('source_folder', '')
        
        # 检查是否设置了源文件夹
        if not source_folder or not os.path.isdir(source_folder):
            logger.warning("未设置有效的源文件夹，无法开始监听")
            return False
        
        # 如果当前已经是监听状态，直接返回
        if config.get('is_monitoring', False):
            logger.debug("当前已经是监听状态，无需重新开始")
            return True
        
        # 开始监听
        config['is_monitoring'] = True
        self.config_manager.save_config(config)
        logger.debug("更新配置：监听状态设为开启")
        
        # 重新设置文件监视器
        self.setup_file_watcher()
        self.watcher_thread.start()
        logger.debug("启动文件监视器线程")
        
        # 发送监听状态变化信号
        self.monitoring_status_changed.emit(True)
        
        return True