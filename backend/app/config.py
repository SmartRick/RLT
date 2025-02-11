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
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(DATA_DIR, 'app.db'))
    
    # 应用固定配置
    APP_CONFIG = {
        'max_concurrent_tasks': 2,
        'max_file_size': 10 * 1024 * 1024  # 10MB
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
    
    # 上传文件配置
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}  # 允许的文件类型
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 最大文件大小 (500MB)
    
    # 确保上传目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # 静态文件访问配置
    STATIC_URL_PATH = '/uploads'
    STATIC_FOLDER = UPLOAD_DIR

config = Config() 