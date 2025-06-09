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
    

def generate_unique_folder_path(base_dir: str, task_id: int, path_type: str) -> str:
    """
    生成唯一的文件夹路径，格式为 base_dir/task_id_序号
    
    Args:
        base_dir: 基础目录
        task_id: 任务ID
        path_type: 路径类型，mark或train
        
    Returns:
        唯一的文件夹路径
    """
    # 确保基础目录存在
    os.makedirs(base_dir, exist_ok=True)
    
    # 查找已存在的当前任务的文件夹
    existing_folders = []
    prefix = f"{task_id}_"
    
    if os.path.exists(base_dir):
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path) and item.startswith(prefix):
                try:
                    # 提取序号部分
                    sequence = int(item.split('_')[1])
                    existing_folders.append(sequence)
                except (IndexError, ValueError):
                    # 如果格式不符，忽略
                    pass
    
    # 确定新的序号
    sequence_num = 1
    if existing_folders:
        sequence_num = max(existing_folders) + 1
    
    # 生成新的文件夹路径
    folder_name = f"{task_id}_{sequence_num}"
    if path_type == 'mark':
        folder_name += "_mark"
    elif path_type == 'train':
        folder_name += "_train"
    
    new_folder_path = os.path.join(base_dir, folder_name)
    
    # 创建目录
    os.makedirs(new_folder_path, exist_ok=True)
    
    return new_folder_path