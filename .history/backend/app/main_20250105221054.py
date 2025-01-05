from flask import Flask
from flask_cors import CORS
from .config import config
from .api.v1 import api_v1
from .utils.logger import setup_logger
from .middleware.error_handler import ErrorHandler
from .database import init_db
from .api.v1.terminal import sock  # 确保导入 sock

logger = setup_logger('main')

def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__)
    
    # 基础配置
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.DEFAULT_CONFIG['max_file_size']
    
    # 初始化数据库
    init_db()
    
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
    
    return app

app = create_app() 