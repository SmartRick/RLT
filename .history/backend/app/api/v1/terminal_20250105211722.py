from flask import Blueprint
from flask_sock import Sock
import paramiko
from ...services.asset_service import AssetService

terminal_bp = Blueprint('terminal', __name__)
sock = Sock()

@sock.route('/terminal/<int:asset_id>')
def terminal(ws, asset_id):
    """WebSocket终端处理器"""
    try:
        # 获取资产信息
        asset = AssetService.get_asset(asset_id)
        if not asset:
            ws.send('Asset not found')
            return
        
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 根据认证类型连接
        try:
            if asset.ssh_auth_type == 'PASSWORD':
                ssh.connect(
                    asset.ip,
                    port=asset.ssh_port,
                    username=asset.ssh_username,
                    password=asset.ssh_password
                )
            else:
                ssh.connect(
                    asset.ip,
                    port=asset.ssh_port,
                    username=asset.ssh_username,
                    key_filename=asset.ssh_key_path
                )
        except Exception as e:
            ws.send(f'Connection failed: {str(e)}')
            return
            
        # 获取交互式shell
        channel = ssh.invoke_shell()
        
        # 双向转发数据
        try:
            while True:
                if channel.recv_ready():
                    data = channel.recv(1024).decode('utf-8')
                    ws.send(data)
                
                message = ws.receive()
                if message:
                    channel.send(message)
        except Exception:
            pass
        finally:
            channel.close()
            ssh.close()
            
    except Exception as e:
        ws.send(f'Error: {str(e)}') 