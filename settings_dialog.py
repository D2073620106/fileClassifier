import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QCheckBox, QFileDialog, QMessageBox, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QDialogButtonBox, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# 导入软件名称常量
from constants import APP_NAME

# 导入开机自启动管理模块
from startup_manager import update_startup_status, is_in_startup

class SettingsDialog(QDialog):
    def __init__(self, config_manager):
        super().__init__()
        # 移除问号按钮
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.config_manager = config_manager
        self.config = self.config_manager.get_config()
        
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
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 添加所有组件到主布局
        main_layout.addWidget(source_group)
        main_layout.addWidget(target_group)
        main_layout.addWidget(options_group)
        main_layout.addWidget(button_box)
        
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
        
        layout = QFormLayout()
        
        # 分类名称
        self.category_edit = QLineEdit(self.rule.get('category', ''))
        layout.addRow('分类名称:', self.category_edit)
        
        # 文件扩展名
        self.extensions_edit = QLineEdit(', '.join([ext for ext in self.rule.get('extensions', [])]))
        layout.addRow('文件扩展名 (用逗号分隔):', self.extensions_edit)
        
        # 目标文件夹
        target_layout = QHBoxLayout()
        self.target_folder_edit = QLineEdit(self.rule.get('target_folder', ''))
        self.target_folder_edit.setReadOnly(True)
        
        browse_btn = QPushButton('浏览...')
        browse_btn.clicked.connect(self.browse_target_folder)
        
        target_layout.addWidget(self.target_folder_edit)
        target_layout.addWidget(browse_btn)
        
        layout.addRow('目标文件夹:', target_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        self.setLayout(layout)
    
    def browse_target_folder(self):
        folder = QFileDialog.getExistingDirectory(self, f'{APP_NAME} - 选择目标文件夹', self.target_folder_edit.text())
        if folder:
            self.target_folder_edit.setText(folder)
    
    def accept(self):
        # 验证输入
        category = self.category_edit.text().strip()
        extensions_text = self.extensions_edit.text().strip()
        target_folder = self.target_folder_edit.text().strip()
        
        if not category:
            QMessageBox.warning(self, f'{APP_NAME} - 警告', '请输入分类名称！')
            return
        
        if not extensions_text:
            QMessageBox.warning(self, f'{APP_NAME} - 警告', '请输入至少一个文件扩展名！')
            return
        
        if not target_folder:
            QMessageBox.warning(self, f'{APP_NAME} - 警告', '请选择目标文件夹！')
            return
        
        # 处理扩展名
        extensions = [ext.strip() for ext in extensions_text.split(',')]
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
        
        # 更新规则
        self.rule['category'] = category
        self.rule['extensions'] = extensions
        self.rule['target_folder'] = target_folder
        
        super().accept()
    
    def get_rule(self):
        return self.rule

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
        self.load_rules()
    
    def init_ui(self):
        self.setWindowTitle(f'{APP_NAME} - 分类规则设置')
        self.setMinimumSize(700, 400)
        
        layout = QVBoxLayout()
        
        # 规则表格
        self.rules_table = QTableWidget(0, 3)
        self.rules_table.setHorizontalHeaderLabels(['分类', '文件类型', '目标文件夹'])
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.rules_table)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton('添加规则')
        self.add_btn.clicked.connect(self.add_rule)
        
        self.edit_btn = QPushButton('编辑规则')
        self.edit_btn.clicked.connect(self.edit_rule)
        
        self.delete_btn = QPushButton('删除规则')
        self.delete_btn.clicked.connect(self.delete_rule)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        layout.addLayout(button_layout)
        
        # 对话框按钮
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Close)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)
        
        self.setLayout(layout)
    
    def load_rules(self):
        self.rules_table.setRowCount(0)
        
        for i, rule in enumerate(self.rules):
            self.rules_table.insertRow(i)
            
            category_item = QTableWidgetItem(rule.get('category', ''))
            extensions_item = QTableWidgetItem(', '.join(rule.get('extensions', [])))
            target_folder_item = QTableWidgetItem(rule.get('target_folder', ''))
            
            self.rules_table.setItem(i, 0, category_item)
            self.rules_table.setItem(i, 1, extensions_item)
            self.rules_table.setItem(i, 2, target_folder_item)
    
    def add_rule(self):
        dialog = RuleEditDialog(parent=self)
        if dialog.exec_():
            new_rule = dialog.get_rule()
            self.rules.append(new_rule)
            self.config['rules'] = self.rules
            self.config_manager.save_config(self.config)
            self.load_rules()
    
    def edit_rule(self):
        selected_rows = self.rules_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, f'{APP_NAME} - 警告', '请先选择一个规则！')
            return
        
        row = selected_rows[0].row()
        dialog = RuleEditDialog(rule=self.rules[row].copy(), parent=self)
        
        if dialog.exec_():
            self.rules[row] = dialog.get_rule()
            self.config['rules'] = self.rules
            self.config_manager.save_config(self.config)
            self.load_rules()
    
    def delete_rule(self):
        selected_rows = self.rules_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, f'{APP_NAME} - 警告', '请先选择一个规则！')
            return
        
        row = selected_rows[0].row()
        
        reply = QMessageBox.question(self, f'{APP_NAME} - 确认删除', 
                                    f'确定要删除规则 "{self.rules[row].get("category", "")}" 吗？',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            del self.rules[row]
            self.config['rules'] = self.rules
            self.config_manager.save_config(self.config)
            self.load_rules()