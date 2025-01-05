import os
from typing import Dict

class Config:
    # 基础配置
    PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
    LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
    
    # 确保必要的目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # 文件路径
    CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
    TASKS_FILE = os.path.join(DATA_DIR, 'tasks.json')
    
    # 默认配置
    DEFAULT_CONFIG: Dict = {
        'source_dir': '/path/to/source',
        'lora_output_path': '/path/to/output',
        'scheduling_minute': 5,
        'mark_pan_dir': '/loraFile/mark',
        'lora_pan_upload_dir': '/loraFile/lora'
    }
    
    # API配置
    API_V1_PREFIX = '/api/v1'
    
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True

config = Config() 