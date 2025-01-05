import os
from typing import Dict, List, Optional
from ..config import config
from ..utils.logger import setup_logger
from ..utils.file_handler import load_json, save_json
from ..utils.ssh import execute_command
from ..middleware.error_handler import ServiceError

logger = setup_logger('asset_service')

class AssetService:
    @staticmethod
    def list_assets() -> List[Dict]:
        """获取资产列表"""
        return load_json(config.ASSETS_FILE, [])

    @staticmethod
    def create_asset(asset_data: Dict) -> Optional[Dict]:
        """创建新资产"""
        assets = load_json(config.ASSETS_FILE, [])
        
        asset = {
            **asset_data,
            'id': str(len(assets) + 1),
            'status': 'PENDING',
            'file_count': 0
        }
        
        assets.append(asset)
        if save_json(config.ASSETS_FILE, assets):
            return asset
        return None

    @staticmethod
    def update_asset(asset_id: str, update_data: Dict) -> Optional[Dict]:
        """更新资产"""
        assets = load_json(config.ASSETS_FILE, [])
        
        for asset in assets:
            if asset['id'] == asset_id:
                asset.update(update_data)
                if save_json(config.ASSETS_FILE, assets):
                    return asset
                return None
        
        return None

    @staticmethod
    def delete_asset(asset_id: str) -> bool:
        """删除资产"""
        assets = load_json(config.ASSETS_FILE, [])
        assets = [a for a in assets if a['id'] != asset_id]
        return save_json(config.ASSETS_FILE, assets)

    @staticmethod
    def upload_files(asset_id: str, files: List) -> bool:
        """上传资产文件"""
        try:
            asset = next((a for a in load_json(config.ASSETS_FILE, []) 
                         if a['id'] == asset_id), None)
            if not asset:
                raise ServiceError("Asset not found")
            
            # 创建上传目录
            upload_dir = os.path.join(config.UPLOAD_DIR, asset['folder_name'])
            os.makedirs(upload_dir, exist_ok=True)
            
            # 保存文件
            for file in files:
                file_path = os.path.join(upload_dir, file.filename)
                file.save(file_path)
            
            # 更新资产信息
            AssetService.update_asset(asset_id, {
                'status': 'UPLOADED',
                'file_count': len(files)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload files: {str(e)}")
            return False 