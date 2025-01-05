from flask import Blueprint
from .tasks import tasks_bp
from .assets import assets_bp
from .settings import settings_bp
from .training import training_bp

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# 注册路由
api_v1.register_blueprint(tasks_bp, url_prefix='/tasks')
api_v1.register_blueprint(assets_bp, url_prefix='/assets')
api_v1.register_blueprint(settings_bp, url_prefix='/settings')
api_v1.register_blueprint(training_bp, url_prefix='/training') 