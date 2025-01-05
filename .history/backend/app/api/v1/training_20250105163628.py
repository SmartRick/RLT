from flask import Blueprint, request, jsonify
from ...services.training_service import TrainingService
from ...utils.logger import setup_logger

logger = setup_logger('training_api')
training_bp = Blueprint('training', __name__)

@training_bp.route('/start', methods=['POST'])
def start_training():
    """开始训练"""
    task_id = request.json.get('task_id')
    if not task_id:
        return jsonify({'error': '缺少任务ID'}), 400
        
    result = TrainingService.start_training(task_id)
    if result:
        return jsonify({'message': '训练已启动'})
    return jsonify({'error': '启动训练失败'}), 500

@training_bp.route('/stop/<task_id>', methods=['POST'])
def stop_training(task_id):
    """停止训练"""
    if TrainingService.stop_training(task_id):
        return jsonify({'message': '训练已停止'})
    return jsonify({'error': '停止训练失败'}), 500

@training_bp.route('/status/<task_id>', methods=['GET'])
def get_training_status(task_id):
    """获取训练状态"""
    status = TrainingService.get_training_status(task_id)
    if status:
        return jsonify(status)
    return jsonify({'error': '获取训练状态失败'}), 404 