import os
import json
from logger import logger  # 导入日志模块

class ConfigManager:
    def __init__(self, config_file='config.json'):
        # 使用绝对路径来指定配置文件位置
        # 如果传入的是相对路径，则转换为绝对路径
        if not os.path.isabs(config_file):
            # 获取应用程序所在目录
            app_dir = os.path.dirname(os.path.abspath(__file__))
            # 拼接绝对路径
            self.config_file = os.path.join(app_dir, config_file)
        else:
            self.config_file = config_file
        logger.debug(f"配置文件路径: {self.config_file}")
        self.config = self.load_config()
        logger.info("配置管理器初始化完成")
    
    default_config = {
        "source_folder": "",
        "default_target_folder": "",
        "rules": [
            {
                "extensions": [
                    ".pdf",
                    ".doc",
                    ".docx",
                    ".txt",
                    ".xls",
                    ".xlsx",
                    ".ppt",
                    ".pptx",
                    ".csv",
                    ".md"
                ],
                "target_folder": "",
                "category": "Documents"
            },
            {
                "extensions": [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".gif",
                    ".bmp",
                    ".svg",
                    ".webp",
                    ".tiff",
                    ".jfif"
                ],
                "target_folder": "",
                "category": "Images"
            },
            {
                "extensions": [
                    ".zip",
                    ".rar",
                    ".7z",
                    ".tar",
                    ".gz"
                ],
                "target_folder": "",
                "category": "Zip"
            },
            {
                "extensions": [
                    ".mp4",
                    ".avi",
                    ".mov",
                    ".wmv",
                    ".flv",
                    ".mkv"
                ],
                "target_folder": "",
                "category": "Videos"
            },
            {
                "extensions": [
                    ".mp3",
                    ".wav",
                    ".flac",
                    ".aac",
                    ".ogg"
                ],
                "target_folder": "",
                "category": "Audio"
            },
            {
                "extensions": [
                    ".ipa",
                    ".apk",
                    ".dmg",
                    ".pkg",
                    ".deb",
                    ".rpm",
                    ".exe",
                    ".msi"
                ],
                "target_folder": "",
                "category": "Exe"
            },
            {
                "extensions": [
                    ".py",
                    ".json",
                    ".js",
                    ".html",
                    ".css",
                    ".java",
                    ".c",
                    ".cpp",
                    ".h",
                    ".php",
                    ".sh",
                    ".bat",
                    ".xml",
                    ".jsx",
                    ".ts",
                    ".tsx",
                    ".scss",
                    ".less",
                    ".kt",
                    ".cs",
                    ".rb",
                    ".go",
                    ".swift",
                    ".m",
                    ".mm",
                    ".bash",
                    ".zsh",
                    ".cmd",
                    ".ps1",
                    ".yml",
                    ".yaml",
                    ".ini",
                    ".cfg",
                    ".conf",
                    ".sql",
                    ".lua",
                    ".pl",
                    ".r",
                    ".dart",
                    ".rs",
                    ".vue",
                    ".svelte",
                    ".gradle",
                    ".properties",
                    ".toml",
                    ".lock",
                    ".gitignore",
                    ".dockerfile",
                    ".makefile",
                    ".htm",
                    ".keystore",
                    ".json5",
                    ".plist",
                    ".sketch"
                ],
                "target_folder": "",
                "category": "Code"
            }
        ],
        "auto_start": False,
        "show_notifications": True,
        "is_monitoring": False
    }

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                logger.debug(f"正在加载配置文件: {self.config_file}")
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("配置文件加载成功")
                return config
            else:
                logger.warning(f"配置文件不存在: {self.config_file}，将创建默认配置")
                self.save_config(self.default_config)
                return self.default_config
        except Exception as e:
            logger.error(f"加载配置文件时出错: {str(e)}，将使用默认配置")
            return self.default_config
    
    def save_config(self, config=None):
        if config is None:
            config = self.config
        
        try:
            logger.debug(f"正在保存配置到文件: {self.config_file}")
            # 确保配置文件目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            self.config = config
            logger.info("配置保存成功")
            return True
        except Exception as e:
            logger.error(f"保存配置文件时出错: {str(e)}")
            return False
    
    def get_config(self):
        logger.debug("获取当前配置")
        return self.config
    
    def update_config(self, key, value):
        logger.debug(f"更新配置: {key} = {value}")
        self.config[key] = value
        return self.save_config()
    
    def update_rule(self, index, extensions=None, target_folder=None, category=None):
        logger.debug(f"更新规则 #{index}: 扩展名={extensions}, 目标文件夹={target_folder}, 分类={category}")
        if 'rules' not in self.config or index >= len(self.config['rules']):
            logger.warning(f"规则 #{index} 不存在，无法更新")
            return False
        
        if extensions is not None:
            self.config['rules'][index]['extensions'] = extensions
        
        if target_folder is not None:
            self.config['rules'][index]['target_folder'] = target_folder
        
        if category is not None:
            self.config['rules'][index]['category'] = category
        
        return self.save_config()
    
    def add_rule(self, extensions, target_folder, category):
        logger.debug(f"添加规则: 扩展名={extensions}, 目标文件夹={target_folder}, 分类={category}")
        new_rule = {
            "extensions": extensions,
            "target_folder": target_folder,
            "category": category
        }
        
        self.config.setdefault('rules', []).append(new_rule)
        return self.save_config()
    
    def delete_rule(self, index):
        logger.debug(f"删除规则 #{index}")
        if 'rules' not in self.config or index >= len(self.config['rules']):
            logger.warning(f"规则 #{index} 不存在，无法删除")
            return False
        
        del self.config['rules'][index]
        return self.save_config()
        return False
