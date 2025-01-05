import paramiko
import os
from typing import Tuple, Optional, NamedTuple
from ..config import config
from .logger import setup_logger

logger = setup_logger('ssh')

class CommandResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str

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

def execute_command(
    hostname: str,
    port: int,
    username: str,
    command: str,
    key_path: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 10
) -> CommandResult:
    """
    执行SSH命令
    
    Args:
        hostname: 主机地址
        port: SSH端口
        username: SSH用户名
        command: 要执行的命令
        key_path: SSH密钥路径（可选）
        password: SSH密码（可选）
        timeout: 超时时间（秒）
    
    Returns:
        CommandResult: 包含返回码、标准输出和标准错误的元组
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if key_path:
            ssh.connect(
                hostname=hostname,
                port=port,
                username=username,
                key_filename=key_path,
                timeout=timeout
            )
        elif password:
            ssh.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                timeout=timeout
            )
        else:
            raise ValueError("必须提供密钥路径或密码")

        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        
        return CommandResult(
            returncode=exit_status,
            stdout=stdout.read().decode('utf-8').strip(),
            stderr=stderr.read().decode('utf-8').strip()
        )
        
    except Exception as e:
        return CommandResult(
            returncode=1,
            stdout='',
            stderr=str(e)
        )
    finally:
        ssh.close() 