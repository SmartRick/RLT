from flask import Flask
from flask_cors import CORS
from .config import config
from .api.v1 import api_v1
from .utils.logger import setup_logger

logger = setup_logger('main')

def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__)
    CORS(app)
    
    # 注册 API 路由
    app.register_blueprint(api_v1)
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not Found'}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"Server Error: {error}")
        return {'error': 'Internal Server Error'}, 500
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    ) 