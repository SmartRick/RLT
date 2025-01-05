# 空文件，标记这是一个 Python 包 

from flask import Flask
from flask_cors import CORS
from .api.v1 import assets_bp

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # 注册蓝图
    app.register_blueprint(assets_bp, url_prefix='/api/v1/assets')
    
    return app 