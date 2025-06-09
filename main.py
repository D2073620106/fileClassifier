import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox, QStyle
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import subprocess

from file_watcher import FileWatcher
from config_manager import ConfigManager
from settings_dialog import SettingsDialog, RuleSettingsDialog
from notification_handler import NotificationHandler
from logger import logger  # 导入日志模块

# 导入软件名称常量
from constants import APP_NAME

# 导入开机自启动管理模块
from startup_manager import update_startup_status, is_in_startup


class FileClassifierApp(QObject):
    file_classified_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        logger.info(f"{APP_NAME} 应用程序启动")
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        logger.info("配置管理器初始化完成")
        
        # 检查并同步开机自启动状态
        self.check_and_sync_auto_start()
        
        # 初始化通知处理器
        self.notification_handler = NotificationHandler()
        logger.info("通知处理器初始化完成")
        
        # 初始化系统托盘图标
        self.setup_tray_icon()
        logger.info("系统托盘图标初始化完成")
        
        # 初始化文件监视器
        self.file_watcher = None
        self.watcher_thread = None
        self.setup_file_watcher()
        logger.info("文件监视器初始化完成")
        
        # 连接信号
        self.file_classified_signal.connect(self.on_file_classified)
        
        # 恢复上次的监听状态
        self.restore_monitoring_state()
        logger.info("应用程序初始化完成")
    
    def check_and_sync_auto_start(self):
        """检查并同步开机自启动状态"""
        logger.info("检查并同步开机自启动状态")
        config = self.config_manager.get_config()
        auto_start_config = config.get('auto_start', False)
        auto_start_actual = is_in_startup()
        
        logger.debug(f"配置中的自启动状态: {auto_start_config}, 实际自启动状态: {auto_start_actual}")
        
        # 如果配置和实际状态不一致
        if auto_start_config != auto_start_actual:
            logger.info("配置和实际自启动状态不一致，进行同步")
            # 如果是配置中设置了自启动但实际没有，尝试添加
            if auto_start_config:
                logger.info("尝试添加到开机自启动")
                update_result = update_startup_status(True)
                # 如果添加失败，更新配置
                if not update_result:
                    logger.warning("添加到开机自启动失败，更新配置")
                    config['auto_start'] = False
                    self.config_manager.save_config(config)
                else:
                    logger.info("成功添加到开机自启动")
            else:
                # 如果配置中没有设置自启动但实际有，更新配置
                logger.info("配置中未设置自启动但实际已添加，更新配置")
                config['auto_start'] = auto_start_actual
                self.config_manager.save_config(config)
        else:
            logger.debug("配置和实际自启动状态一致，无需同步")
    
    def setup_tray_icon(self):
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self.app)
        self.tray_icon.setToolTip(APP_NAME)
        
        # 设置图标（使用自定义图标icon.png）
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # 如果图标文件不存在，使用默认图标
            self.tray_icon.setIcon(self.app.style().standardIcon(QStyle.SP_FileIcon))
        
        # 连接托盘图标的点击事件
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # 连接通知点击事件
        self.tray_icon.messageClicked.connect(self.on_notification_clicked)
        
        # 创建托盘菜单
        self.tray_menu = QMenu()
        
        # 监听控制动作
        self.toggle_monitoring_action = QAction('开启监听')
        self.toggle_monitoring_action.triggered.connect(self.toggle_monitoring)
        self.tray_menu.addAction(self.toggle_monitoring_action)
        
        # 添加分隔线
        self.tray_menu.addSeparator()
        
        # 设置动作
        self.folder_settings_action = QAction('设置')
        self.folder_settings_action.triggered.connect(self.open_folder_settings)
        self.tray_menu.addAction(self.folder_settings_action)
        
        self.rule_settings_action = QAction('规则设置')
        self.rule_settings_action.triggered.connect(self.open_rule_settings)
        self.tray_menu.addAction(self.rule_settings_action)
        
        # 添加查看日志选项
        self.view_log_action = QAction('查看日志')
        self.view_log_action.triggered.connect(self.open_log_file)
        self.tray_menu.addAction(self.view_log_action)
        
        # 分隔线 - 分类文件夹菜单项将在这里添加
        self.category_separator = self.tray_menu.addSeparator()
        
        # 更新分类文件夹菜单项
        self.update_category_folders()
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # 显示托盘图标
        self.tray_icon.show()
        
        # 更新菜单状态
        self.update_menu_state()
    
    def update_category_folders(self):
        """更新分类文件夹菜单项"""
        config = self.config_manager.get_config()
        rules = config.get('rules', [])
        print(f"规则: {rules}")
        default_target_folder = config.get('default_target_folder', '')
        
        # 移除旧的分类文件夹菜单项
        # 找到查看日志菜单项的位置
        view_log_index = -1
        for i, action in enumerate(self.tray_menu.actions()):
            if action == self.view_log_action:
                view_log_index = i
                break
        
        if view_log_index == -1:
            logger.warning("未找到查看日志菜单项，无法更新分类文件夹菜单")
            return
        
        # 移除旧的分类文件夹菜单项
        # 从查看日志后面一个位置开始，到分隔线之前
        actions_to_remove = []
        for i in range(view_log_index + 1, len(self.tray_menu.actions())):
            action = self.tray_menu.actions()[i]
            if action.isSeparator():
                break
            actions_to_remove.append(action)
        
        for action in actions_to_remove:
            self.tray_menu.removeAction(action)
        
        # 清空文件夹菜单项数组
        self.folder_actions = []
        
        # 添加新的分类文件夹菜单项
        added_folders = set()
        for rule in rules:
            target_folder = rule.get('target_folder', '')
            category = rule.get('category', '')
            
            # 如果目标文件夹为空，使用默认目标文件夹
            if not target_folder and default_target_folder:
                target_folder = os.path.join(default_target_folder, category)
            
            # 如果目标文件夹已经添加过，跳过
            if not target_folder or target_folder in added_folders:
                continue
            
            # 确保目标文件夹存在
            if not os.path.exists(target_folder):
                try:
                    os.makedirs(target_folder, exist_ok=True)
                except Exception as e:
                    print(f"创建目标文件夹失败: {str(e)}")
                    continue
            
            # 添加菜单项 - 使用self的属性而不是局部变量
            action_name = f'folder_action_{len(self.folder_actions)}'
            setattr(self, action_name, QAction(f'{category}文件夹'))
            folder_action = getattr(self, action_name)
            folder_action.triggered.connect(lambda checked, folder=target_folder: self.open_folder(folder))
            
            # 将菜单项添加到数组中
            self.folder_actions.append(folder_action)
            
            # 在规则设置后面插入，使用addAction而不是insertAction
            self.tray_menu.addAction(folder_action)
            added_folders.add(target_folder)
            print(f"添加菜单项: {folder_action.text()}")
        
        # 添加一个分隔线，分隔分类文件夹菜单项和退出菜单项
        self.tray_menu.addSeparator()
        
        # 添加退出动作
        self.exit_action = QAction('退出')
        self.exit_action.triggered.connect(self.exit_app)
        self.tray_menu.addAction(self.exit_action)
    
    def open_log_file(self):
        """打开日志文件"""
        from constants import LOG_FILE
        
        # 获取应用程序所在目录
        app_dir = os.path.dirname(os.path.abspath(__file__))
        # 日志目录路径
        log_dir = os.path.join(app_dir, 'log')
        # 日志文件完整路径
        log_file_path = os.path.join(log_dir, LOG_FILE)
        
        logger.info(f"尝试打开日志文件: {log_file_path}")
        
        if not os.path.exists(log_file_path):
            logger.warning(f"日志文件不存在: {log_file_path}")
            QMessageBox.information(None, f'{APP_NAME} - 提示', '日志文件尚未创建。')
            return
        
        try:
            # 根据操作系统打开日志文件
            if os.name == 'nt':  # Windows
                os.startfile(log_file_path)
            elif os.name == 'posix':  # macOS 和 Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', log_file_path])
                else:  # Linux
                    subprocess.run(['xdg-open', log_file_path])
            logger.debug(f"成功打开日志文件: {log_file_path}")
        except Exception as e:
            logger.error(f"打开日志文件失败: {str(e)}")
            QMessageBox.warning(None, f'{APP_NAME} - 警告', f'打开日志文件失败: {str(e)}')

    def open_folder(self, folder_path):
        """打开指定的文件夹"""
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
            except Exception as e:
                print(f"创建文件夹失败: {str(e)}")
                QMessageBox.warning(None, f'{APP_NAME} - 警告', f'文件夹不存在且无法创建: {folder_path}')
                return
        
        try:
            # 根据操作系统打开文件夹
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS 和 Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', folder_path])
                else:  # Linux
                    subprocess.run(['xdg-open', folder_path])
        except Exception as e:
            print(f"打开文件夹失败: {str(e)}")
            QMessageBox.warning(None, f'{APP_NAME} - 警告', f'打开文件夹失败: {str(e)}')
    
    def setup_file_watcher(self):
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
        else:
            if not source_folder:
                logger.warning("未设置源文件夹，无法启动监视器")
            elif not os.path.isdir(source_folder):
                logger.warning(f"源文件夹不存在: {source_folder}，无法启动监视器")
            elif not is_monitoring:
                logger.debug("监听状态为关闭，不启动监视器")
    
    def toggle_monitoring(self):
        logger.info("切换监听状态")
        config = self.config_manager.get_config()
        source_folder = config.get('source_folder', '')
        
        # 检查是否设置了源文件夹
        if not source_folder or not os.path.isdir(source_folder):
            logger.warning("未设置有效的源文件夹，无法切换监听状态")
            QMessageBox.warning(None, f'{APP_NAME} - 警告', '请先设置要监听的源文件夹！')
            self.open_folder_settings()
            return
        
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
            
            # 更新菜单状态
            self.toggle_monitoring_action.setText('开启监听')
            self.tray_icon.setToolTip(f'{APP_NAME} (监听已停止)')
            
            # 显示通知
            if config.get('show_notifications', True):
                self.tray_icon.showMessage(APP_NAME, '文件监听已停止', QSystemTrayIcon.Information, 2000)
                logger.debug("显示通知：文件监听已停止")
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
            
            # 更新菜单状态
            self.toggle_monitoring_action.setText('关闭监听')
            self.tray_icon.setToolTip(f'{APP_NAME} (监听中)')
            
            # 显示通知
            if config.get('show_notifications', True):
                self.tray_icon.showMessage(APP_NAME, f'开始监听文件夹: {source_folder}', QSystemTrayIcon.Information, 2000)
                logger.debug(f"显示通知：开始监听文件夹 {source_folder}")
        
        # 更新菜单状态
        self.update_menu_state()
    
    def restore_monitoring_state(self):
        """恢复上次的监听状态"""
        logger.info("恢复上次的监听状态")
        config = self.config_manager.get_config()
        is_monitoring = config.get('is_monitoring', False)
        source_folder = config.get('source_folder', '')
        default_target_folder = config.get('default_target_folder', '')
        
        logger.debug(f"配置信息 - 监听状态: {is_monitoring}, 源文件夹: {source_folder}, 默认目标文件夹: {default_target_folder}")
        
        # 检查是否设置了源文件夹
        if not source_folder or not os.path.isdir(source_folder):
            logger.warning("未设置有效的源文件夹，无法恢复监听状态")
            return
        
        # 更新分类文件夹菜单项，确保使用最新的 default_target_folder 设置
        self.update_category_folders()
        logger.debug("更新分类文件夹菜单项")
        
        # 如果上次是开启监听状态，则启动监视器
        if is_monitoring:
            logger.info(f"恢复监听状态：开启监听文件夹 {source_folder}")
            # 重新设置文件监视器，确保使用最新的配置
            self.setup_file_watcher()
            # 启动监视器线程
            if self.watcher_thread and not self.watcher_thread.isRunning():
                logger.debug("启动监视器线程")
                self.watcher_thread.start()
            
            # 更新菜单状态
            self.toggle_monitoring_action.setText('关闭监听')
            self.tray_icon.setToolTip(f'{APP_NAME} (监听中)')
        else:
            logger.info("恢复监听状态：保持停止监听")
            # 更新菜单状态
            self.toggle_monitoring_action.setText('开启监听')
            self.tray_icon.setToolTip(f'{APP_NAME} (监听已停止)')
        
        # 更新菜单状态
        self.update_menu_state()
    
    def update_menu_state(self):
        config = self.config_manager.get_config()
        is_monitoring = config.get('is_monitoring', False)
        
        if is_monitoring:
            self.toggle_monitoring_action.setText('关闭监听')
            self.tray_icon.setToolTip(f'{APP_NAME} (监听中)')
        else:
            self.toggle_monitoring_action.setText('开启监听')
            self.tray_icon.setToolTip(f'{APP_NAME} (监听已停止)')
        
        # 更新分类文件夹菜单项
        self.update_category_folders()
    
    def open_folder_settings(self):
        dialog = SettingsDialog(self.config_manager)
        if dialog.exec_():
            # 如果设置已更改，重新设置文件监视器
            self.setup_file_watcher()
            self.update_menu_state()
    
    def open_rule_settings(self):
        dialog = RuleSettingsDialog(self.config_manager)
        if dialog.exec_():
            # 如果规则设置已更改，更新分类文件夹菜单
            self.update_category_folders()
    
    def on_file_classified(self, file_path, target_folder):
        config = self.config_manager.get_config()
        if config.get('show_notifications', True):
            file_name = os.path.basename(file_path)
            # 存储分类文件信息，用于通知点击事件
            self.notification_handler.store_classified_file_info(file_path, target_folder)
            
            self.tray_icon.showMessage(
                f'{APP_NAME} - 文件已分类',
                f'文件 {file_name} 已移动到 {target_folder}',
                QSystemTrayIcon.Information,
                2000
            )
    
    def on_notification_clicked(self):
        """处理通知点击事件，打开目标文件所在文件夹并选中文件"""
        self.notification_handler.open_folder_and_select_file()
    
    def on_tray_icon_activated(self, reason):
        # 当用户点击托盘图标时打开规则设置面板
        # QSystemTrayIcon.Trigger表示单击，QSystemTrayIcon.DoubleClick表示双击
        from PyQt5.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.Trigger or reason == QSystemTrayIcon.DoubleClick:
            self.open_rule_settings()
    
    def exit_app(self):
        # 停止文件监视器
        if self.file_watcher and self.watcher_thread and self.watcher_thread.isRunning():
            self.file_watcher.stop()
            self.watcher_thread.quit()
            self.watcher_thread.wait()
        
        # 退出应用
        self.tray_icon.hide()
        self.app.quit()
    
    def run(self):
        # 运行应用程序
        return self.app.exec_()

if __name__ == '__main__':
    app = FileClassifierApp()
    sys.exit(app.run())