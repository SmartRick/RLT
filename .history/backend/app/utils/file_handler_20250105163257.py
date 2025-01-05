import json
import os
from typing import Dict, List, Any
from ..utils.logger import setup_logger

logger = setup_logger('file_handler')

def load_json(file_path: str, default: Any = None) -> Any:
    """加载JSON文件"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    except Exception as e:
        logger.error(f"加载文件失败 {file_path}: {e}")
        return default

def save_json(file_path: str, data: Any) -> bool:
    """保存JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存文件失败 {file_path}: {e}")
        return False 