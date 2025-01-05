from flask import Blueprint, current_app
from flask_sock import Sock
import paramiko
import json
from ...services.asset_service import AssetService
from ...utils.logger import setup_logger

logger = setup_logger('terminal')
terminal_bp = Blueprint('terminal', __name__)
sock = Sock()

@sock.route('/<int:asset_id>')  # 简化路由路径
def terminal(ws, asset_id):
    """WebSocket终端处理器"""
    ssh = None
    channel = None
    
    try:
        logger.info(f"开始建立终端连接，资产ID: {asset_id}")
        
        # 获取资产信息
        asset = AssetService.get_asset(asset_id)
        if not asset:
            error_msg = f'Asset not found: {asset_id}'
            logger.error(error_msg)
            ws.send(json.dumps({
                'type': 'error',
                'data': error_msg
            }))
            return
        
        logger.info(f"获取到资产信息: {asset.ip}:{asset.ssh_port}")
        
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 根据认证类型连接
        try:
            connect_params = {
                'hostname': asset.ip,
                'port': asset.ssh_port,
                'username': asset.ssh_username,
                'timeout': 10
            }
            
            if asset.ssh_auth_type == 'PASSWORD':
                if not asset.ssh_password:
                    raise ValueError("密码认证方式下密码不能为空")
                connect_params['password'] = asset.ssh_password
            else:
                if not asset.ssh_key_path:
                    raise ValueError("密钥认证方式下密钥路径不能为空")
                connect_params['key_filename'] = asset.ssh_key_path
            
            logger.info(f"尝试SSH连接: {asset.ip}:{asset.ssh_port}")
            ssh.connect(**connect_params)
            logger.info(f"SSH连接成功: {asset.ip}:{asset.ssh_port}")
            
        except Exception as e:
            error_msg = f'SSH连接失败: {str(e)}'
            logger.error(f"SSH连接错误: {error_msg}")
            ws.send(json.dumps({
                'type': 'error',
                'data': error_msg
            }))
            return
            
        # 获取交互式shell
        channel = ssh.invoke_shell(term='xterm')
        channel.setblocking(0)  # 设置非阻塞模式
        
        logger.info("终端会话已建立")
        ws.send(json.dumps({
            'type': 'output',
            'data': f'Connected to {asset.ip}\r\n'
        }))
        
        # 双向转发数据
        try:
            while True:
                # 处理从客户端接收的数据
                try:
                    message = ws.receive()
                    if message:
                        data = json.loads(message)
                        if data['type'] == 'input':
                            channel.send(data['data'])
                        elif data['type'] == 'resize':
                            channel.resize_pty(
                                width=data.get('cols', 80),
                                height=data.get('rows', 24)
                            )
                except Exception as e:
                    logger.error(f"Error processing client message: {str(e)}")
                    break
                
                # 处理从服务器接收的数据
                if channel.recv_ready():
                    data = channel.recv(1024).decode('utf-8', errors='ignore')
                    ws.send(json.dumps({
                        'type': 'output',
                        'data': data
                    }))
                    
        except Exception as e:
            logger.error(f"Terminal session error: {str(e)}")
            
    except Exception as e:
        error_msg = f'Terminal error: {str(e)}'
        logger.error(error_msg)
        try:
            ws.send(json.dumps({
                'type': 'error',
                'data': error_msg
            }))
        except:
            pass
        
    finally:
        try:
            if channel:
                channel.close()
            if ssh:
                ssh.close()
        except:
            pass 