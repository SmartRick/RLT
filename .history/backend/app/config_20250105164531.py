import os
from typing import Dict

class Config:
    # 基础配置
    PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
    LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
    UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')
    
    # 确保必要的目录存在
    for dir_path in [DATA_DIR, LOGS_DIR, UPLOAD_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    
    # 文件路径
    CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
    TASKS_FILE = os.path.join(DATA_DIR, 'tasks.json')
    ASSETS_FILE = os.path.join(DATA_DIR, 'assets.json')
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(DATA_DIR, 'app.db'))
    
    # 默认配置
    DEFAULT_CONFIG: Dict = {
        'source_dir': '/path/to/source',
        'lora_output_path': '/path/to/output',
        'scheduling_minute': 5,
        'mark_pan_dir': '/loraFile/mark',
        'lora_pan_upload_dir': '/loraFile/lora',
        'max_concurrent_tasks': 2,
        'allowed_file_types': ['.png', '.jpg', '.jpeg', '.webp'],
        'max_file_size': 10 * 1024 * 1024,  # 10MB
        'ssh_host': 'your-server-host',
        'ssh_port': 22,
        'ssh_username': 'root',
        'ssh_key_path': '~/.ssh/id_rsa'
    }
    
    # API配置
    API_V1_PREFIX = '/api/v1'
    
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # 安全配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 训练配置
    TRAINING_TIMEOUT = 60 * 60 * 24  # 24 hours
    MAX_RETRY_COUNT = 3

config = Config() 