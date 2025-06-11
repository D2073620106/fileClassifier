import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QCheckBox, QFileDialog, QMessageBox, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QDialogButtonBox, QGroupBox, QFormLayout, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# 导入软件名称常量
from constants import APP_NAME

# 导入开机自启动管理模块
from startup_manager import update_startup_status, is_in_startup

# 导入监听管理器
from monitoring_manager import MonitoringManager

class SettingsDialog(QDialog):
    def __init__(self, config_manager, monitoring_manager=None):
        super().__init__()
        # 移除问号按钮
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.config_manager = config_manager
        self.config = self.config_manager.get_config()
        
        # 使用传入的监听管理器或创建新的实例
        if monitoring_manager is None:
            raise ValueError("MonitoringManager instance is required.")
        
        self.monitoring_manager = monitoring_manager
       
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f'{APP_NAME} - 文件夹设置')
        self.setMinimumWidth(500)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 源文件夹设置
        source_group = QGroupBox('监听文件夹设置')
        source_layout = QHBoxLayout()
        
        self.source_folder_edit = QLineEdit(self.config.get('source_folder', ''))
        self.source_folder_edit.setReadOnly(True)
        
        browse_source_btn = QPushButton('浏览...')
        browse_source_btn.clicked.connect(self.browse_source_folder)
        
        source_layout.addWidget(self.source_folder_edit)
        source_layout.addWidget(browse_source_btn)
        source_group.setLayout(source_layout)
        
        # 目标文件夹设置
        target_group = QGroupBox('默认分类文件夹设置')
        target_layout = QHBoxLayout()
        
        self.target_folder_edit = QLineEdit(self.config.get('default_target_folder', ''))
        self.target_folder_edit.setReadOnly(True)
        
        browse_target_btn = QPushButton('浏览...')
        browse_target_btn.clicked.connect(self.browse_target_folder)
        
        target_layout.addWidget(self.target_folder_edit)
        target_layout.addWidget(browse_target_btn)
        target_group.setLayout(target_layout)
        
        # 其他设置
        options_group = QGroupBox('其他设置')
        options_layout = QVBoxLayout()
        
        # 检查实际的开机自启动状态
        actual_auto_start = is_in_startup()
        # 如果配置和实际状态不一致，以实际状态为准
        if self.config.get('auto_start', False) != actual_auto_start:
            self.config['auto_start'] = actual_auto_start
            self.config_manager.save_config(self.config)
        
        self.auto_start_checkbox = QCheckBox('开机自动启动')
        self.auto_start_checkbox.setChecked(self.config.get('auto_start', False))
        
        self.show_notifications_checkbox = QCheckBox('显示通知')
        self.show_notifications_checkbox.setChecked(self.config.get('show_notifications', True))
        
        options_layout.addWidget(self.auto_start_checkbox)
        options_layout.addWidget(self.show_notifications_checkbox)
        options_group.setLayout(options_layout)
        
        # 开启监听按钮
        self.start_monitoring_btn = QPushButton('开启监听')
        # 根据当前监听状态设置按钮文本
        is_monitoring = self.config.get('is_monitoring', False)
        if is_monitoring:
            self.start_monitoring_btn.setText('关闭监听')
        else:
            self.start_monitoring_btn.setText('开启监听')
        self.start_monitoring_btn.clicked.connect(self.toggle_monitoring)
        
        # 创建底部按钮布局
        bottom_layout = QHBoxLayout()
        
        # 添加开启监听按钮到左侧
        bottom_layout.addWidget(self.start_monitoring_btn)
        
        # 添加弹簧，将确定取消按钮推到右侧
        bottom_layout.addStretch()
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 获取按钮并修改文本
        ok_button = button_box.button(QDialogButtonBox.Ok)
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        ok_button.setText('确定')
        cancel_button.setText('取消')
        
        # 添加确定取消按钮到右侧
        bottom_layout.addWidget(button_box)
        
        # 添加所有组件到主布局
        main_layout.addWidget(source_group)
        main_layout.addWidget(target_group)
        main_layout.addWidget(options_group)
        main_layout.addLayout(bottom_layout)
        
        self.setLayout(main_layout)
    
    def browse_source_folder(self):
        folder = QFileDialog.getExistingDirectory(self, f'{APP_NAME} - 选择监听文件夹', self.source_folder_edit.text())
        if folder:
            self.source_folder_edit.setText(folder)
    
    def browse_target_folder(self):
        folder = QFileDialog.getExistingDirectory(self, f'{APP_NAME} - 选择默认分类文件夹', self.target_folder_edit.text())
        if folder:
            self.target_folder_edit.setText(folder)
    
    def accept(self):
        # 验证设置
        source_folder = self.source_folder_edit.text()
        target_folder = self.target_folder_edit.text()
        
        if not source_folder:
            QMessageBox.warning(self, f'{APP_NAME} - 警告', '请选择要监听的源文件夹！')
            return
        
        # 获取开机自启动设置
        auto_start = self.auto_start_checkbox.isChecked()
        
        # 更新配置
        self.config['source_folder'] = source_folder
        self.config['default_target_folder'] = target_folder
        self.config['auto_start'] = auto_start
        self.config['show_notifications'] = self.show_notifications_checkbox.isChecked()
        
        # 更新开机自启动状态
        update_result = update_startup_status(auto_start)
        if not update_result:
            QMessageBox.warning(self, f'{APP_NAME} - 警告', '更新开机自启动设置失败，可能需要管理员权限。')
            # 将配置中的auto_start设置为实际状态
            self.config['auto_start'] = is_in_startup()
        
        # 保存配置
        if self.config_manager.save_config(self.config):
            super().accept()
        else:
            QMessageBox.critical(self, f'{APP_NAME} - 错误', '保存配置失败！')
    
    def toggle_monitoring(self):
        """切换监听状态
        
        使用监听管理器切换监听状态，并更新按钮文本
        """
        # 使用监听管理器切换监听状态
        result = self.monitoring_manager.toggle_monitoring(self)
        
        # 如果操作成功，更新按钮文本
        if result:
            # 获取最新的监听状态
            is_monitoring = self.monitoring_manager.get_monitoring_status()
            
            # 更新按钮文本
            if is_monitoring:
                self.start_monitoring_btn.setText('关闭监听')
            else:
                self.start_monitoring_btn.setText('开启监听')
            
            # 更新配置
            self.config = self.config_manager.get_config()


class RuleEditDialog(QDialog):
    def __init__(self, rule=None, parent=None):
        super().__init__(parent)
        # 移除问号按钮
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.rule = rule or {"extensions": [], "target_folder": "", "category": ""}
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f'{APP_NAME} - 编辑规则')
        self.setMinimumWidth(400)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 分类名称
        self.category_edit = QLineEdit(self.rule.get('category', ''))
        form_layout.addRow('分类名称:', self.category_edit)
        
        # 目标文件夹
        target_layout = QHBoxLayout()
        self.target_folder_edit = QLineEdit(self.rule.get('target_folder', ''))
        self.target_folder_edit.setReadOnly(True)
        
        browse_target_btn = QPushButton('浏览...')
        browse_target_btn.clicked.connect(self.browse_target_folder)
        
        target_layout.addWidget(self.target_folder_edit)
        target_layout.addWidget(browse_target_btn)
        form_layout.addRow('目标文件夹:', target_layout)
        
        # 文件扩展名
        extensions_layout = QVBoxLayout()
        extensions_label = QLabel('文件扩展名 (使用逗号分隔多个扩展名，例如 .pdf,.doc):')
        
        # 创建水平布局来放置输入框和添加按钮
        extensions_input_layout = QHBoxLayout()
        
        self.extensions_edit = QLineEdit()
        self.extensions_edit.setPlaceholderText('输入扩展名，使用逗号分隔 (例如 .pdf,.doc)')
        # 移除回车事件
        # self.extensions_edit.returnPressed.connect(self.add_extension)
        
        # 添加按钮
        add_ext_btn = QPushButton('添加')
        add_ext_btn.clicked.connect(self.add_extension)
        
        extensions_input_layout.addWidget(self.extensions_edit)
        extensions_input_layout.addWidget(add_ext_btn)
        
        self.extensions_table = QTableWidget(0, 2)  # 2列：扩展名和删除按钮
        self.extensions_table.setHorizontalHeaderLabels(['扩展名', '操作'])
        self.extensions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.extensions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.extensions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.extensions_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 设置表格样式，添加表头和内容之间的分割线
        self.extensions_table.setStyleSheet("""
            QHeaderView::section { 
                background-color: #FFFFFF; 
                border: 1px solid #D0D0D0;
            }
        """)
        
        # 添加现有的扩展名
        for ext in self.rule.get('extensions', []):
            self.add_extension_to_table(ext)
        
        extensions_layout.addWidget(extensions_label)
        extensions_layout.addLayout(extensions_input_layout)
        extensions_layout.addWidget(self.extensions_table)
        
        # 添加表单和扩展名部分到主布局
        main_layout.addLayout(form_layout)
        main_layout.addLayout(extensions_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 获取按钮并修改文本
        ok_button = button_box.button(QDialogButtonBox.Ok)
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        ok_button.setText('确定')
        cancel_button.setText('取消')
        
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
    
    def browse_target_folder(self):
        folder = QFileDialog.getExistingDirectory(self, f'{APP_NAME} - 选择目标文件夹', self.target_folder_edit.text())
        if folder:
            self.target_folder_edit.setText(folder)
    
    def add_extension(self):
        input_text = self.extensions_edit.text().strip().lower()
        if not input_text:
            return
        
        # 分割逗号分隔的扩展名
        extensions = [ext.strip() for ext in input_text.split(',') if ext.strip()]
        
        if not extensions:
            return
        
        added_count = 0
        for ext in extensions:
            # 确保扩展名以点开头
            if not ext.startswith('.'):
                ext = '.' + ext
            
            # 检查是否已存在
            exists = False
            for row in range(self.extensions_table.rowCount()):
                if self.extensions_table.item(row, 0).text() == ext:
                    exists = True
                    break
            
            if exists:
                continue  # 跳过已存在的扩展名
            
            # 添加到表格
            self.add_extension_to_table(ext)
            added_count += 1
        
        # 清空输入框
        self.extensions_edit.clear()
        
        # 如果有添加成功的扩展名，显示成功消息
        if added_count <= 0:
            QMessageBox.warning(self, f'{APP_NAME} - 警告', '没有添加任何新的扩展名，可能是扩展名已存在！')
    
    def add_extension_to_table(self, ext):
        row = self.extensions_table.rowCount()
        self.extensions_table.insertRow(row)
        
        # 添加扩展名
        self.extensions_table.setItem(row, 0, QTableWidgetItem(ext))
        
        # 添加删除按钮
        delete_btn = QPushButton('删除')
        delete_btn.clicked.connect(lambda: self.delete_extension(row))
        self.extensions_table.setCellWidget(row, 1, delete_btn)
    
    def delete_extension(self, row):
        self.extensions_table.removeRow(row)
    
    def accept(self):
        # 验证输入
        category = self.category_edit.text().strip()
        if not category:
            QMessageBox.warning(self, f'{APP_NAME} - 警告', '请输入分类名称！')
            return
        
        # 收集扩展名
        extensions = []
        for row in range(self.extensions_table.rowCount()):
            ext = self.extensions_table.item(row, 0).text()
            extensions.append(ext)
        
        if not extensions:
            QMessageBox.warning(self, f'{APP_NAME} - 警告', '请至少添加一个文件扩展名！')
            return
        
        # 更新规则
        self.rule['category'] = category
        self.rule['target_folder'] = self.target_folder_edit.text()
        self.rule['extensions'] = extensions
        
        super().accept()


class RuleSettingsDialog(QDialog):
    def __init__(self, config_manager):
        super().__init__()
        # 移除问号按钮
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.config_manager = config_manager
        self.config = self.config_manager.get_config()
        self.rules = self.config.get('rules', [])
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f'{APP_NAME} - 规则设置')
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 规则表格
        self.rules_table = QTableWidget(0, 4)  # 4列：分类名称、目标文件夹、扩展名、操作
        self.rules_table.setHorizontalHeaderLabels(['分类名称', '目标文件夹', '扩展名', '操作'])
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.rules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.rules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rules_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 设置表格样式，添加表头和内容之间的分割线
        self.rules_table.setStyleSheet("""
           QHeaderView::section { 
                background-color: #FFFFFF; 
                border: 1px solid #D0D0D0;
            }
        """)
        
        # 添加现有的规则
        self.update_rules_table()
        
        # 添加规则按钮
        add_rule_btn = QPushButton('添加规则')
        add_rule_btn.clicked.connect(self.add_rule)
        
        # 创建底部按钮布局
        bottom_layout = QHBoxLayout()
        
        # 添加规则按钮放到左侧
        bottom_layout.addWidget(add_rule_btn)
        
        # 添加弹簧，将确定取消按钮推到右侧
        bottom_layout.addStretch()
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 获取按钮并修改文本
        ok_button = button_box.button(QDialogButtonBox.Ok)
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        ok_button.setText('确定')
        cancel_button.setText('取消')
        
        # 添加确定取消按钮到右侧
        bottom_layout.addWidget(button_box)
        
        # 添加组件到主布局
        main_layout.addWidget(self.rules_table)
        main_layout.addLayout(bottom_layout)
        
        self.setLayout(main_layout)
    
    def update_rules_table(self):
        # 清空表格
        self.rules_table.setRowCount(0)
        
        # 添加规则
        for i, rule in enumerate(self.rules):
            row = self.rules_table.rowCount()
            self.rules_table.insertRow(row)
            
            # 分类名称
            self.rules_table.setItem(row, 0, QTableWidgetItem(rule.get('category', '')))
            
            # 目标文件夹
            target_folder = rule.get('target_folder', '')
            if not target_folder and self.config.get('default_target_folder', ''):
                target_folder = os.path.join(self.config.get('default_target_folder', ''), rule.get('category', ''))
            self.rules_table.setItem(row, 1, QTableWidgetItem(target_folder))
            
            # 扩展名
            extensions = ', '.join(rule.get('extensions', []))
            self.rules_table.setItem(row, 2, QTableWidgetItem(extensions))
            
            # 操作按钮
            operations_layout = QHBoxLayout()
            operations_layout.setContentsMargins(0, 0, 0, 0)
            operations_layout.setSpacing(2)
            
            edit_btn = QPushButton('编辑')
            edit_btn.clicked.connect(lambda checked, idx=i: self.edit_rule(idx))
            
            delete_btn = QPushButton('删除')
            delete_btn.clicked.connect(lambda checked, idx=i: self.delete_rule(idx))
            
            operations_layout.addWidget(edit_btn)
            operations_layout.addWidget(delete_btn)
            
            operations_widget = QWidget()
            operations_widget.setLayout(operations_layout)
            self.rules_table.setCellWidget(row, 3, operations_widget)
    
    def add_rule(self):
        dialog = RuleEditDialog(parent=self)
        if dialog.exec_():
            self.rules.append(dialog.rule)
            self.update_rules_table()
    
    def edit_rule(self, index):
        dialog = RuleEditDialog(self.rules[index], parent=self)
        if dialog.exec_():
            self.rules[index] = dialog.rule
            self.update_rules_table()
    
    def delete_rule(self, index):
        reply = QMessageBox.question(self, f'{APP_NAME} - 确认', '确定要删除这条规则吗？', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.rules[index]
            self.update_rules_table()
    
    def accept(self):
        # 保存规则
        self.config['rules'] = self.rules
        if self.config_manager.save_config(self.config):
            super().accept()
        else:
            QMessageBox.critical(self, f'{APP_NAME} - 错误', '保存配置失败！')
