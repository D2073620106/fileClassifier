import os
import sys
import winreg

def get_app_path():
    """获取应用程序路径"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        return os.path.abspath(sys.executable)
    else:
        # 如果是源代码运行
        script_path = os.path.abspath(sys.argv[0])
        return script_path

def add_to_startup():
    """添加程序到开机启动项"""
    try:
        app_path = get_app_path()
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "FileClassifier", 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"添加到开机启动项失败: {str(e)}")
        return False

def remove_from_startup():
    """从开机启动项中移除程序"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, "FileClassifier")
        except FileNotFoundError:
            # 如果键不存在，忽略错误
            pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"从开机启动项移除失败: {str(e)}")
        return False

def is_in_startup():
    """检查程序是否在开机启动项中"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, "FileClassifier")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception as e:
        print(f"检查开机启动项失败: {str(e)}")
        return False

def update_startup_status(auto_start):
    """根据配置更新开机启动状态"""
    if auto_start:
        return add_to_startup()
    else:
        return remove_from_startup()