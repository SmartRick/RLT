from typing import Dict, Optional
from ..config import config
from ..utils.file_handler import load_json, save_json
from ..utils.logger import setup_logger

logger = setup_logger('config_service')

class ConfigService:
    @staticmethod
    def get_config() -> Dict:
        """获取系统配置"""
        return load_json(config.CONFIG_FILE, config.DEFAULT_CONFIG)

    @staticmethod
    def update_config(new_config: Dict) -> bool:
        """更新系统配置"""
        return save_json(config.CONFIG_FILE, new_config) 