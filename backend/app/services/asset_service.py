from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.asset import Asset as AssetModel
from ..schemas.asset import AssetCreate, AssetUpdate, Asset
from ..database import get_db
from ..utils.logger import setup_logger
from ..utils.ssh import execute_command
import paramiko

logger = setup_logger('asset_service')

class AssetService:
    @staticmethod
    def list_assets() -> List[Asset]:
        """获取资产列表"""
        with get_db() as db:
            assets = db.query(AssetModel).all()
            return [Asset.from_orm(asset) for asset in assets]

    @staticmethod
    def create_asset(asset_data: AssetCreate) -> Optional[Asset]:
        """创建新资产"""
        try:
            logger.debug(f"开始创建资产: {asset_data.dict()}")
            with get_db() as db:
                # 检查资产名称是否已存在
                existing = db.query(AssetModel).filter(AssetModel.name == asset_data.name).first()
                if existing:
                    logger.error(f"资产名称已存在: {asset_data.name}")
                    raise ValueError("资产名称已存在")

                asset = AssetModel(**asset_data.dict())
                
                # 设置初始状态为 PENDING
                asset.status = 'PENDING'
                
                # 验证SSH连接
                try:
                    if AssetService._verify_ssh_connection(asset_data.dict()):
                        asset.status = 'CONNECTED'
                    else:
                        asset.status = 'CONNECTION_ERROR'
                except Exception as e:
                    logger.error(f"SSH connection verification failed: {str(e)}")
                    asset.status = 'CONNECTION_ERROR'
                
                logger.debug("添加资产到数据库")
                db.add(asset)
                try:
                    db.commit()
                    logger.debug("数据库提交成功")
                    db.refresh(asset)
                    logger.info(f"资产创建成功: ID={asset.id}, 名称={asset.name}")
                    return Asset.from_orm(asset)
                except Exception as e:
                    logger.error(f"数据库操作失败: {str(e)}")
                    db.rollback()
                    raise
        except Exception as e:
            logger.error(f"创建资产失败: {str(e)}", exc_info=True)
            if isinstance(e, ValueError):
                raise
            return None

    @staticmethod
    def update_asset(asset_id: int, update_data: AssetUpdate) -> Optional[Asset]:
        """更新资产"""
        try:
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    return None
                
                # 更新资产数据
                update_dict = update_data.dict(exclude_unset=True)
                for key, value in update_dict.items():
                    setattr(asset, key, value)
                
                # 如果更新了连接信息，重新验证SSH连接
                if any(key in update_dict for key in ['ip', 'ssh_port', 'ssh_username', 'ssh_key_path']):
                    try:
                        if AssetService._verify_ssh_connection(asset.__dict__):
                            asset.status = 'CONNECTED'
                        else:
                            asset.status = 'CONNECTION_ERROR'
                    except Exception as e:
                        logger.error(f"SSH connection verification failed: {str(e)}")
                        asset.status = 'CONNECTION_ERROR'
                
                db.commit()
                db.refresh(asset)
                return Asset.from_orm(asset)
        except Exception as e:
            logger.error(f"Update asset failed: {str(e)}")
            return None

    @staticmethod
    def delete_asset(asset_id: int) -> bool:
        """删除资产"""
        try:
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if asset:
                    db.delete(asset)
                    db.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Delete asset failed: {str(e)}")
            return False

    @staticmethod
    def verify_capabilities(asset_id: int) -> dict:
        """验证资产能力"""
        try:
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    raise ValueError("资产不存在")

                results = {
                    'lora_training': False,
                    'ai_engine': False
                }

                # 验证Lora训练能力
                if asset.lora_training.get('enabled'):
                    try:
                        url = asset.lora_training.get('url', '')
                        port = asset.lora_training.get('port')
                        
                        if url and port:
                            import socket
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(5)
                            
                            try:
                                sock.connect((url, int(port)))
                                results['lora_training'] = True
                                asset.lora_training = {
                                    **asset.lora_training,
                                    'verified': True
                                }
                            except Exception as e:
                                logger.error(f"Lora训练服务连接失败: {url}:{port}, 错误: {str(e)}")
                                asset.lora_training = {
                                    **asset.lora_training,
                                    'verified': False
                                }
                            finally:
                                sock.close()
                        else:
                            asset.lora_training = {
                                **asset.lora_training,
                                'verified': False
                            }
                    except Exception as e:
                        logger.error(f"Lora训练验证失败: {str(e)}")
                        asset.lora_training = {
                            **asset.lora_training,
                            'verified': False
                        }

                # 验证AI引擎能力
                if asset.ai_engine.get('enabled'):
                    try:
                        url = asset.ai_engine.get('url', '')
                        port = asset.ai_engine.get('port')
                        
                        if url and port:
                            import socket
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(5)
                            
                            try:
                                sock.connect((url, int(port)))
                                results['ai_engine'] = True
                                asset.ai_engine = {
                                    **asset.ai_engine,
                                    'verified': True
                                }
                            except Exception as e:
                                logger.error(f"AI引擎服务连接失败: {url}:{port}, 错误: {str(e)}")
                                asset.ai_engine = {
                                    **asset.ai_engine,
                                    'verified': False
                                }
                            finally:
                                sock.close()
                        else:
                            asset.ai_engine = {
                                **asset.ai_engine,
                                'verified': False
                            }
                    except Exception as e:
                        logger.error(f"AI引擎验证失败: {str(e)}")
                        asset.ai_engine = {
                            **asset.ai_engine,
                            'verified': False
                        }

                db.commit()
                return results
        except Exception as e:
            logger.error(f"验证资产能力失败: {str(e)}")
            raise

    @staticmethod
    def _verify_ssh_connection(asset: dict) -> bool:
        """验证SSH连接"""
        try:
            logger.debug(f"开始SSH连接测试: {asset['ip']}:{asset['ssh_port']}")
            result = execute_command(
                hostname=asset['ip'],
                port=asset['ssh_port'],
                username=asset['ssh_username'],
                key_path=asset.get('ssh_key_path'),
                command='echo "Connection test"'
            )
            
            # 根据返回码更新状态
            if result.returncode == 0:
                logger.info(f"SSH连接测试成功: {asset['ip']}:{asset['ssh_port']}")
                return True
            else:
                logger.warning(f"SSH连接测试失败: {asset['ip']}:{asset['ssh_port']}, 错误信息: {result.stderr}")
                return False
            
        except Exception as e:
            error_msg = str(e)
            if "Authentication failed" in error_msg:
                logger.error(f"SSH认证失败: {asset['ip']}:{asset['ssh_port']}, 请检查用户名和密钥")
            elif "Connection refused" in error_msg:
                logger.error(f"SSH连接被拒绝: {asset['ip']}:{asset['ssh_port']}, 请检查IP地址和端口")
            elif "No such file" in error_msg:
                logger.error(f"SSH密钥文件不存在: {asset.get('ssh_key_path')}")
            else:
                logger.error(f"SSH连接测试异常: {asset['ip']}:{asset['ssh_port']}, 错误: {error_msg}", exc_info=True)
            return False 

    @staticmethod
    def verify_ssh_connection(data: Dict[str, Any]) -> bool:
        """
        验证SSH连接
        
        Args:
            data: SSH连接参数
                {
                    'ip': str,
                    'ssh_port': int,
                    'ssh_username': str,
                    'ssh_auth_type': str,
                    'ssh_password': str,
                    'ssh_key_path': str
                }
        
        Returns:
            bool: 连接是否成功
            
        Raises:
            Exception: SSH连接失败时抛出异常
        """
        try:
            # 创建SSH客户端
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 准备连接参数
            connect_params = {
                'hostname': data['ip'],
                'port': int(data['ssh_port']),
                'username': data['ssh_username'],
                'timeout': 10  # 设置超时时间
            }

            # 根据认证类型设置认证参数
            if data['ssh_auth_type'] == 'PASSWORD':
                if not data.get('ssh_password'):
                    raise ValueError('密码认证方式下必须提供密码')
                connect_params['password'] = data['ssh_password']
            else:
                if not data.get('ssh_key_path'):
                    raise ValueError('密钥认证方式下必须提供密钥路径')
                connect_params['key_filename'] = data['ssh_key_path']

            logger.debug(f"尝试SSH连接: {data['ip']}:{data['ssh_port']}")
            
            # 尝试建立连接
            ssh.connect(**connect_params)
            
            # 执行简单命令测试连接
            stdin, stdout, stderr = ssh.exec_command('echo "SSH connection test"')
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error = stderr.read().decode().strip()
                raise Exception(f"命令执行失败: {error}")

            logger.info(f"SSH连接成功: {data['ip']}:{data['ssh_port']}")

            # 更新资产状态
            try:
                with get_db() as db:
                    # 通过 IP 和端口查找资产
                    asset = db.query(AssetModel).filter(
                        AssetModel.ip == data['ip'],
                        AssetModel.ssh_port == data['ssh_port']
                    ).first()
                    
                    if asset:
                        asset.status = 'CONNECTED'
                        db.commit()
                        logger.info(f"已更新资产状态为已连接: {data['ip']}:{data['ssh_port']}")

            except Exception as e:
                logger.error(f"更新资产状态失败: {str(e)}")
                # 不影响验证结果返回
                pass

            return True

        except paramiko.AuthenticationException:
            logger.error(f"SSH认证失败: {data['ip']}:{data['ssh_port']}")
            # 更新状态为连接错误
            try:
                with get_db() as db:
                    asset = db.query(AssetModel).filter(
                        AssetModel.ip == data['ip'],
                        AssetModel.ssh_port == data['ssh_port']
                    ).first()
                    if asset:
                        asset.status = 'CONNECTION_ERROR'
                        db.commit()
            except Exception as e:
                logger.error(f"更新资产状态失败: {str(e)}")
            raise Exception("SSH认证失败，请检查用户名和密码/密钥")
            
        except paramiko.SSHException as e:
            logger.error(f"SSH连接异常: {str(e)}")
            # 更新状态为连接错误
            try:
                with get_db() as db:
                    asset = db.query(AssetModel).filter(
                        AssetModel.ip == data['ip'],
                        AssetModel.ssh_port == data['ssh_port']
                    ).first()
                    if asset:
                        asset.status = 'CONNECTION_ERROR'
                        db.commit()
            except Exception as db_error:
                logger.error(f"更新资产状态失败: {str(db_error)}")
            raise Exception(f"SSH连接异常: {str(e)}")
            
        except Exception as e:
            logger.error(f"SSH连接失败: {str(e)}")
            # 更新状态为连接错误
            try:
                with get_db() as db:
                    asset = db.query(AssetModel).filter(
                        AssetModel.ip == data['ip'],
                        AssetModel.ssh_port == data['ssh_port']
                    ).first()
                    if asset:
                        asset.status = 'CONNECTION_ERROR'
                        db.commit()
            except Exception as db_error:
                logger.error(f"更新资产状态失败: {str(db_error)}")
            raise Exception(f"SSH连接失败: {str(e)}")
            
        finally:
            try:
                ssh.close()
            except:
                pass 

    @staticmethod
    def get_asset(asset_id: int) -> Optional[Asset]:
        """获取单个资产"""
        try:
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if asset:
                    return Asset.from_orm(asset)
                return None
        except Exception as e:
            logger.error(f"获取资产失败: {str(e)}")
            return None 