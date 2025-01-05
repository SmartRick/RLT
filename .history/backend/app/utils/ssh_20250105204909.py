import paramiko
import os
from typing import Tuple
from ..config import config
from .logger import setup_logger

logger = setup_logger('ssh')

def create_ssh_client() -> paramiko.SSHClient:
    """创建 SSH 客户端"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 从配置获取 SSH 连接信息
        ssh.connect(
            hostname=config.DEFAULT_CONFIG['ssh_host'],
            port=config.DEFAULT_CONFIG['ssh_port'],
            username=config.DEFAULT_CONFIG['ssh_username'],
            key_filename=os.path.expanduser(config.DEFAULT_CONFIG['ssh_key_path'])
        )
        return ssh
    except Exception as e:
        logger.error(f"Failed to create SSH client: {str(e)}")
        raise

def test_ssh_connection() -> Tuple[bool, str]:
    """测试 SSH 连接"""
    try:
        ssh = create_ssh_client()
        ssh.close()
        return True, "SSH connection successful"
    except Exception as e:
        return False, f"SSH connection failed: {str(e)}"

def execute_command(command: str) -> Tuple[bool, str]:
    """执行远程命令"""
    try:
        ssh = create_ssh_client()
        stdin, stdout, stderr = ssh.exec_command(command)
        
        # 获取命令输出
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        # 检查执行状态
        exit_status = stdout.channel.recv_exit_status()
        
        ssh.close()
        
        if exit_status == 0:
            return True, output
        return False, error
        
    except Exception as e:
        logger.error(f"Command execution failed: {str(e)}")
        return False, str(e) 