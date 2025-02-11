from flask import Flask, send_from_directory
from flask_cors import CORS
from .config import config
from .api.v1 import api_v1
from .utils.logger import setup_logger
from .middleware.error_handler import ErrorHandler
from .database import init_db
from .api.v1.terminal import sock  # 确保导入 sock
from .services.config_service import ConfigService  # 添加这行
from .services.scheduler_service import scheduler
import os

logger = setup_logger('main')

def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__)
    
    # 基础配置
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    
    # 初始化数据库
    init_db()
    
    # 初始化系统设置
    ConfigService.init_settings()
    
    # 启用CORS
    CORS(app)
    
    # 注册错误处理
    ErrorHandler.init_app(app)
    
    # 注册 API 路由
    app.register_blueprint(api_v1)
    
    # 注册请求前处理器
    @app.before_request
    def before_request():
        # TODO: 添加认证和请求日志
        pass
    
    # 注册请求后处理器
    @app.after_request
    def after_request(response):
        # TODO: 添加响应日志
        return response
    
    # 注册 WebSocket 扩展
    sock.init_app(app)
    
    # 注册静态文件路由
    @app.route(f'{config.STATIC_URL_PATH}/<path:filename>')
    def serve_uploads(filename):
        """处理上传文件的访问"""
        logger.info(f"Accessing file: {filename}")
        
        # 从完整路径中提取任务ID和文件名
        parts = filename.split('/')
        if len(parts) != 2:
            logger.error(f"Invalid path format: {filename}")
            return "Invalid path", 400
        
        task_id, file_name = parts
        file_path = os.path.join(config.UPLOAD_DIR, task_id)
        logger.info(f"Looking for file in: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"Directory not found: {file_path}")
            return "Directory not found", 404
        
        return send_from_directory(file_path, file_name)
    
    # 启动任务调度器
    scheduler.start()
    
    return app

app = create_app() 