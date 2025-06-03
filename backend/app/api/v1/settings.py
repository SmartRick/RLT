from flask import Blueprint, request
from ...services.config_service import ConfigService
from ...utils.logger import setup_logger
from ...utils.response import success_json, error_json, exception_handler, response_template

logger = setup_logger('settings_api')
settings_bp = Blueprint('settings', __name__)

@settings_bp.route('', methods=['GET'])
@exception_handler
def get_settings():
    """获取系统配置"""
    return success_json(ConfigService.get_config())

@settings_bp.route('', methods=['PUT'])
@exception_handler
def update_settings():
    """更新系统配置"""
    if ConfigService.update_config(request.json):
        return response_template("updated")
    return error_json(4001, "更新配置失败") 