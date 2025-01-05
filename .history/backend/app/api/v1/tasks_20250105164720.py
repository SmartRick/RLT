from flask import Blueprint, request, jsonify
from ...services.task_service import TaskService
from ...utils.logger import setup_logger
from ...utils.validators import validate_task_create

logger = setup_logger('tasks_api')
tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/', methods=['GET'])
def list_tasks():
    """获取任务列表"""
    status = request.args.get('status')
    search = request.args.get('search')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    tasks = TaskService.list_tasks(status, search, start_date, end_date)
    return jsonify(tasks)

@tasks_bp.route('/', methods=['POST'])
def create_task():
    """创建新任务"""
    validate_task_create(request.json)
    task = TaskService.create_task(request.json)
    if task:
        return jsonify(task)
    return jsonify({'error': '创建任务失败'}), 500

@tasks_bp.route('/<task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    task = TaskService.update_task(task_id, request.json)
    if task:
        return jsonify(task)
    return jsonify({'error': '任务不存在或更新失败'}), 404

@tasks_bp.route('/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    if TaskService.delete_task(task_id):
        return jsonify({'message': '任务已删除'})
    return jsonify({'error': '删除任务失败'}), 500

@tasks_bp.route('/<task_id>/log', methods=['GET'])
def get_task_log(task_id):
    """获取任务日志"""
    content = TaskService.get_task_log(task_id)
    if content is not None:
        return jsonify({'content': content})
    return jsonify({'error': '获取日志失败'}), 404

@tasks_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取任务统计"""
    return jsonify(TaskService.get_stats()) 