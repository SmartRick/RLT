import socket
import platform
import os
from ..utils.logger import setup_logger

logger = setup_logger('common')

def get_local_ip():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 使用谷歌DNS服务器地址，不需要真的连接
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"获取本地IP地址失败: {str(e)}")
        return "127.0.0.1"

def get_system_info():
    """获取系统信息"""
    system = platform.system()
    if system == "Windows":
        username = os.environ.get("USERNAME", "Administrator")
        return {
            "is_windows": True,
            "username": username
        }
    else:  # Linux/Darwin
        username = os.environ.get("USER", "root")
        return {
            "is_windows": False,
            "username": username
        }