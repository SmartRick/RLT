from flask import Blueprint, request
from ...services.training_service import TrainingService
from ...utils.logger import setup_logger
from ...utils.response import success_json, error_json, exception_handler, response_template

logger = setup_logger('training_api')
training_bp = Blueprint('training', __name__)

@training_bp.route('/start', methods=['POST'])
@exception_handler
def start_training():
    """开始训练"""
    task_id = request.json.get('task_id')
    if not task_id:
        return response_template("bad_request", msg="缺少任务ID")
        
    result = TrainingService.start_training(task_id)
    if result:
        return success_json(None, "训练已启动")
    return error_json(5001, "启动训练失败")

@training_bp.route('/stop/<task_id>', methods=['POST'])
@exception_handler
def stop_training(task_id):
    """停止训练"""
    if TrainingService.stop_training(task_id):
        return success_json(None, "训练已停止")
    return error_json(5002, "停止训练失败")

@training_bp.route('/status/<task_id>', methods=['GET'])
@exception_handler
def get_training_status(task_id):
    """获取训练状态"""
    status = TrainingService.get_training_status(task_id)
    if status:
        return success_json(status)
    return response_template("not_found", code=5003, msg="获取训练状态失败") 