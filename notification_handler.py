import os
import subprocess
from PyQt5.QtCore import QObject

# 导入软件名称常量
from constants import APP_NAME
from logger import logger  # 导入日志模块

class NotificationHandler(QObject):
    """
    处理通知相关的功能，包括点击通知打开目标文件所在文件夹并选中文件
    """
    def __init__(self):
        super().__init__()
        self.last_classified_file = None
        self.last_target_folder = None
        logger.debug("通知处理器初始化完成")
    
    def store_classified_file_info(self, file_path, target_folder):
        """
        存储最近一次分类的文件信息
        
        Args:
            file_path: 原始文件路径
            target_folder: 目标文件夹路径
        """
        self.last_classified_file = file_path
        self.last_target_folder = target_folder
        logger.debug(f"存储分类文件信息: {file_path} -> {target_folder}")
    
    def open_folder_and_select_file(self):
        """
        打开目标文件夹并选中文件
        """
        if not self.last_classified_file or not self.last_target_folder:
            logger.warning("没有最近分类的文件信息，无法打开文件夹")
            return False
        
        # 确保路径使用正确的分隔符
        target_folder = self.last_target_folder.replace('/', '\\')
        target_file_path = self.last_classified_file.replace('/', '\\')
        
        logger.info(f"尝试打开文件: {target_file_path}")
        
        # 如果找到了文件，打开文件夹并选中文件
        if os.path.exists(target_file_path):
            try:
                # 在Windows上使用explorer选中文件
                # 修复explorer命令参数格式，确保路径格式正确
                # 当路径中包含空格时，需要使用shell=True并将整个命令作为一个字符串传递
                command = f'explorer /select,"{target_file_path}"'
                logger.debug(f"执行命令: {command}")
                subprocess.run(command, shell=True)
                logger.info("成功打开文件夹并选中文件")
                return True
            except Exception as e:
                logger.error(f"打开文件夹时出错: {str(e)}")
                return False
        else:
            logger.warning(f"文件不存在，无法打开: {target_file_path}")
            return False
    
    def show_notification(self, title, message):
        """
        显示系统通知
        
        Args:
            title: 通知标题
            message: 通知内容
        """
        logger.debug(f"显示通知: {title} - {message}")
        # 这里可以根据需要实现系统通知功能
        # 目前通知功能由系统托盘图标实现，此方法保留为扩展接口