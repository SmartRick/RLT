from flask import Blueprint, request, jsonify
from ...services.config_service import ConfigService
from ...utils.logger import setup_logger

logger = setup_logger('settings_api')
settings_bp = Blueprint('settings', __name__)

@settings_bp.route('', methods=['GET'])
def get_settings():
    """获取系统配置"""
    return jsonify(ConfigService.get_config())

@settings_bp.route('', methods=['PUT'])
def update_settings():
    """更新系统配置"""
    if ConfigService.update_config(request.json):
        return jsonify({'message': '配置已更新'})
    return jsonify({'error': '更新配置失败'}), 500 