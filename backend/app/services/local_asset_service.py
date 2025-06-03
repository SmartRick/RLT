import os
import platform
import socket
from typing import Optional
from ..models.asset import Asset
from ..database import get_db
from ..utils.logger import setup_logger
from ..utils.ssh import execute_command
from ..utils import common
logger = setup_logger('local_asset_service')

class LocalAssetService:
    """本地资产服务，用于管理本地资产"""
    
    LOCAL_ASSET_NAME = "本地系统"
    
    @staticmethod
    def init_local_asset():
        """初始化本地资产"""
        try:
            with get_db() as db:
                # 检查是否已存在本地资产
                existing = db.query(Asset).filter(Asset.name == LocalAssetService.LOCAL_ASSET_NAME).first()
                if existing:
                    logger.info(f"本地资产已存在: {existing.id}")
                    return existing
                
                # 获取系统信息
                # ip = LocalAssetService.get_local_ip()
                system_info = common.get_system_info()
                
                # 创建新的本地资产
                local_asset = Asset(
                    name=LocalAssetService.LOCAL_ASSET_NAME,
                    ip='127.0.0.1',
                    ssh_port=22,  # 默认值，Windows不会使用
                    ssh_username=system_info["username"],
                    ssh_auth_type="KEY",  # 默认值，不重要
                    status="CONNECTED",  # 本地资产默认为已连接状态
                    is_local=True  # 标记为本地资产
                )
                
                # 设置本地资产的能力
                local_asset.lora_training = {
                    'enabled': True,
                    'port': 8188,  # 假设ComfyUI默认端口
                    'config_path': '',
                    'params': '{}',
                    'verified': True  # 默认验证通过
                }
                
                local_asset.ai_engine = {
                    'enabled': True,
                    'port': 8188,  # 假设使用相同端口
                    'verified': True  # 默认验证通过
                }
                
                # 保存到数据库
                db.add(local_asset)
                db.commit()
                db.refresh(local_asset)
                
                logger.info(f"本地资产创建成功: ID={local_asset.id}, 系统类型={'Windows' if system_info['is_windows'] else 'Linux/Unix'}")
                return local_asset
                
        except Exception as e:
            logger.error(f"初始化本地资产失败: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def is_local_asset(asset_id: int) -> bool:
        """判断是否为本地资产"""
        try:
            with get_db() as db:
                asset = db.query(Asset).filter(Asset.id == asset_id).first()
                if not asset:
                    return False
                return asset.name == LocalAssetService.LOCAL_ASSET_NAME
        except Exception as e:
            logger.error(f"检查本地资产失败: {str(e)}")
            return False 