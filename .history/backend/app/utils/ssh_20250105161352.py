import paramiko
from typing import Optional
from ..models.asset import Asset
from ..config import settings
import os

def get_ssh_client(asset: Asset) -> Optional[paramiko.SSHClient]:
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        key_path = asset.ssh_key_path or settings.SSH_KEY_PATH
        key_path = os.path.expanduser(key_path)
        
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"SSH key not found: {key_path}")
            
        private_key = paramiko.RSAKey.from_private_key_file(key_path)
        
        client.connect(
            hostname=asset.ip,
            port=asset.ssh_port,
            username=asset.ssh_username,
            pkey=private_key,
            timeout=5
        )
        
        return client
    except Exception as e:
        print(f"SSH connection failed: {str(e)}")
        return None

def test_ssh_connection(asset: Asset) -> bool:
    client = get_ssh_client(asset)
    if client:
        client.close()
        return True
    return False

def execute_command(asset: Asset, command: str) -> tuple[Optional[str], Optional[str]]:
    client = get_ssh_client(asset)
    if not client:
        return None, "Failed to establish SSH connection"
        
    try:
        stdin, stdout, stderr = client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()
    except Exception as e:
        return None, str(e)
    finally:
        client.close() 