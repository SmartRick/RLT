from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from ...database import get_db
from ...services.task_service import TaskService
from ...utils.logger import setup_logger
from ...utils.validators import validate_task_create, validate_file_upload

logger = setup_logger('tasks_api')
tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('', methods=['GET'])
def list_tasks():
    """获取任务列表"""
    status = request.args.get('status')
    search = request.args.get('search')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    with get_db() as db:
        tasks = TaskService.list_tasks(
            db,
            status=status,
            search=search,
            start_date=start_date,
            end_date=end_date
        )
        return jsonify(tasks)

@tasks_bp.route('', methods=['POST'])
def create_task():
    """创建任务"""
    data = request.get_json()
    
    if not validate_task_create(data):
        return jsonify({
            'error': '无效的任务数据',
            'message': '任务名称不能为空'
        }), 400
        
    with get_db() as db:
        task = TaskService.create_task(db, data)
        if task:
            return jsonify(task)
        return jsonify({
            'error': '创建任务失败',
            'message': '服务器内部错误'
        }), 500

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    data = request.get_json()
    
    with get_db() as db:
        task = TaskService.update_task(db, task_id, data)
        if task:
            return jsonify(task)
        return jsonify({'error': '更新任务失败'}), 500

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    with get_db() as db:
        if TaskService.delete_task(db, task_id):
            return jsonify({'message': '任务已删除'})
        return jsonify({'error': '删除任务失败'}), 500

@tasks_bp.route('/<int:task_id>/log', methods=['GET'])
def get_task_log(task_id):
    """获取任务日志"""
    content = TaskService.get_task_log(task_id)
    if content is not None:
        return jsonify({'content': content})
    return jsonify({'error': '获取日志失败'}), 404

@tasks_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取任务统计"""
    with get_db() as db:
        return jsonify(TaskService.get_stats(db)) 

@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    with get_db() as db:
        task = TaskService.get_task_by_id(db, task_id)
        if task:
            return jsonify(task)
        return jsonify({
            'error': '任务不存在',
            'message': f'未找到ID为 {task_id} 的任务'
        }), 404 

@tasks_bp.route('/<int:task_id>/images', methods=['POST'])
def upload_images(task_id):
    """上传任务图片"""
    if 'files[]' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
        
    files = request.files.getlist('files[]')
    try:
        validate_file_upload(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
        
    with get_db() as db:
        result = TaskService.upload_images(db, task_id, files)
        if result:
            return jsonify(result)
        return jsonify({'error': '上传失败'}), 500

@tasks_bp.route('/<int:task_id>/images/<int:image_id>', methods=['DELETE'])
def delete_image(task_id, image_id):
    """删除任务图片"""
    with get_db() as db:
        if TaskService.delete_image(db, task_id, image_id):
            return jsonify({'message': '删除成功'})
        return jsonify({'error': '删除失败'}), 500

@tasks_bp.route('/<int:task_id>/mark', methods=['POST'])
def start_marking(task_id):
    """开始标记"""
    with get_db() as db:
        result = TaskService.start_marking(db, task_id)
        if result:
            return jsonify(result)
        return jsonify({'error': '开始标记失败'}), 500

@tasks_bp.route('/<int:task_id>/train', methods=['POST'])
def start_training(task_id):
    """开始训练"""
    with get_db() as db:
        result = TaskService.start_training(db, task_id)
        if result:
            return jsonify(result)
        return jsonify({'error': '开始训练失败'}), 500

@tasks_bp.route('/<int:task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """终止任务"""
    with get_db() as db:
        if TaskService.stop_task(db, task_id):
            return jsonify({'message': '任务已终止'})
        return jsonify({'error': '终止任务失败'}), 500 

@tasks_bp.route('/<int:task_id>/restart', methods=['POST'])
def restart_task(task_id):
    """重启任务"""
    with get_db() as db:
        result = TaskService.restart_task(db, task_id)
        if result:
            if 'error' in result:
                return jsonify(result), 400
            return jsonify(result)
        return jsonify({'error': '重启任务失败'}), 500 

@tasks_bp.route('/<int:task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    with get_db() as db:
        result = TaskService.cancel_task(db, task_id)
        if result:
            if 'error' in result:
                return jsonify(result), 400
            return jsonify(result)
        return jsonify({'error': '取消任务失败'}), 500 