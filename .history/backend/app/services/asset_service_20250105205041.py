from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.asset import Asset as AssetModel
from ..schemas.asset import AssetCreate, AssetUpdate, Asset
from ..database import get_db
from ..utils.logger import setup_logger
from ..utils.ssh import execute_command

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
                
                # 验证SSH连接
                try:
                    logger.debug(f"验证SSH连接: {asset_data.ip}:{asset_data.ssh_port}")
                    if AssetService._verify_ssh_connection(asset_data.dict()):
                        asset.status = 'CONNECTED'
                        logger.info(f"SSH连接验证成功: {asset_data.ip}:{asset_data.ssh_port}")
                    else:
                        asset.status = 'CONNECTION_ERROR'
                        logger.warning(f"SSH连接验证失败: {asset_data.ip}:{asset_data.ssh_port}")
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
                    raise ValueError("Asset not found")

                results = {
                    'lora_training': False,
                    'ai_engine': False
                }

                # 验证Lora训练能力
                if asset.lora_training.get('enabled'):
                    try:
                        # TODO: 实现具体的验证逻辑
                        results['lora_training'] = True
                        asset.lora_training['verified'] = True
                    except Exception as e:
                        logger.error(f"Lora training verification failed: {str(e)}")

                # 验证AI引擎能力
                if asset.ai_engine.get('enabled'):
                    try:
                        # TODO: 实现具体的验证逻辑
                        results['ai_engine'] = True
                        asset.ai_engine['verified'] = True
                    except Exception as e:
                        logger.error(f"AI engine verification failed: {str(e)}")

                db.commit()
                return results
        except Exception as e:
            logger.error(f"Verify capabilities failed: {str(e)}")
            raise

    @staticmethod
    def _verify_ssh_connection(asset: dict) -> bool:
        """验证SSH连接"""
        try:
            logger.debug(f"开始SSH连接测试: {asset['ip']}:{asset['ssh_port']}")
            result = execute_command(
                host=asset['ip'],
                port=asset['ssh_port'],
                username=asset['ssh_username'],
                key_path=asset.get('ssh_key_path'),
                command='echo "Connection test"'
            )
            logger.debug(f"SSH测试命令返回码: {result.returncode}")
            if result.returncode == 0:
                logger.info(f"SSH连接测试成功: {asset['ip']}:{asset['ssh_port']}")
            else:
                logger.warning(f"SSH连接测试失败: {asset['ip']}:{asset['ssh_port']}, 错误信息: {result.stderr}")
            return result.returncode == 0
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