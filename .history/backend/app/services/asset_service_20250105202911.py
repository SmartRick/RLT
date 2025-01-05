import os
from typing import Dict, List, Optional
from datetime import datetime
from ..config import config
from ..utils.logger import setup_logger
from ..utils.file_handler import load_json, save_json
from ..utils.ssh import execute_command
from ..middleware.error_handler import ServiceError
from ..schemas.asset import AssetCreate, AssetUpdate

logger = setup_logger('asset_service')

class AssetService:
    @staticmethod
    def list_assets() -> List[Dict]:
        """获取资产列表"""
        assets = load_json(config.ASSETS_FILE, [])
        # 确保每个资产都有能力配置字段
        for asset in assets:
            if 'lora_training' not in asset:
                asset['lora_training'] = {'enabled': False}
            if 'ai_engine' not in asset:
                asset['ai_engine'] = {'enabled': False}
        return assets

    @staticmethod
    def create_asset(asset_data: AssetCreate) -> Optional[Dict]:
        """创建新资产"""
        assets = load_json(config.ASSETS_FILE, [])
        
        # 生成新资产数据
        new_asset = {
            'id': len(assets) + 1,
            'status': 'PENDING',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            **asset_data.dict()
        }
        
        # 验证SSH连接
        try:
            if AssetService._verify_ssh_connection(new_asset):
                new_asset['status'] = 'CONNECTED'
            else:
                new_asset['status'] = 'CONNECTION_ERROR'
        except Exception as e:
            logger.error(f"SSH connection verification failed: {str(e)}")
            new_asset['status'] = 'CONNECTION_ERROR'
        
        assets.append(new_asset)
        if save_json(config.ASSETS_FILE, assets):
            return new_asset
        return None

    @staticmethod
    def update_asset(asset_id: int, update_data: AssetUpdate) -> Optional[Dict]:
        """更新资产"""
        assets = load_json(config.ASSETS_FILE, [])
        
        for asset in assets:
            if asset['id'] == asset_id:
                # 更新基本信息
                update_dict = update_data.dict(exclude_unset=True)
                asset.update(update_dict)
                asset['updated_at'] = datetime.now().isoformat()
                
                # 如果更新了连接信息，重新验证SSH连接
                if any(key in update_dict for key in ['ip', 'ssh_port', 'ssh_username', 'ssh_key_path']):
                    try:
                        if AssetService._verify_ssh_connection(asset):
                            asset['status'] = 'CONNECTED'
                        else:
                            asset['status'] = 'CONNECTION_ERROR'
                    except Exception as e:
                        logger.error(f"SSH connection verification failed: {str(e)}")
                        asset['status'] = 'CONNECTION_ERROR'
                
                if save_json(config.ASSETS_FILE, assets):
                    return asset
                return None
        
        return None

    @staticmethod
    def delete_asset(asset_id: int) -> bool:
        """删除资产"""
        assets = load_json(config.ASSETS_FILE, [])
        assets = [a for a in assets if a['id'] != asset_id]
        return save_json(config.ASSETS_FILE, assets)

    @staticmethod
    def _verify_ssh_connection(asset: Dict) -> bool:
        """验证SSH连接"""
        try:
            # 执行简单的命令来测试连接
            result = execute_command(
                host=asset['ip'],
                port=asset['ssh_port'],
                username=asset['ssh_username'],
                key_path=asset.get('ssh_key_path'),
                command='echo "Connection test"'
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"SSH connection test failed: {str(e)}")
            return False

    @staticmethod
    def verify_capabilities(asset_id: int) -> Dict[str, bool]:
        """验证资产的能力配置"""
        assets = load_json(config.ASSETS_FILE, [])
        asset = next((a for a in assets if a['id'] == asset_id), None)
        if not asset:
            raise ServiceError("Asset not found")

        results = {
            'lora_training': False,
            'ai_engine': False
        }

        # 验证Lora训练能力
        if asset.get('lora_training', {}).get('enabled'):
            try:
                # TODO: 实现具体的验证逻辑
                results['lora_training'] = True
            except Exception as e:
                logger.error(f"Lora training capability verification failed: {str(e)}")

        # 验证AI引擎能力
        if asset.get('ai_engine', {}).get('enabled'):
            try:
                # TODO: 实现具体的验证逻辑
                results['ai_engine'] = True
            except Exception as e:
                logger.error(f"AI engine capability verification failed: {str(e)}")

        return results 