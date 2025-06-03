from flask import Blueprint, request, current_app
from werkzeug.utils import secure_filename
import os
from ...database import get_db
from ...services.task_service import TaskService
from ...utils.logger import setup_logger
from ...utils.validators import validate_task_create, validate_file_upload
from ...utils.response import success_json, error_json, exception_handler, response_template

logger = setup_logger('tasks_api')
tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('', methods=['GET'])
@exception_handler
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
        return success_json(tasks)

@tasks_bp.route('', methods=['POST'])
@exception_handler
def create_task():
    """创建任务"""
    data = request.get_json()
    
    if not validate_task_create(data):
        return response_template("bad_request", msg="无效的任务数据，任务名称不能为空")
        
    with get_db() as db:
        task = TaskService.create_task(db, data)
        if task:
            return response_template("created", data=task)
        return error_json(1003, "创建任务失败")

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@exception_handler
def update_task(task_id):
    """更新任务"""
    data = request.get_json()
    
    with get_db() as db:
        task = TaskService.update_task(db, task_id, data)
        if task:
            return response_template("updated", data=task)
        return error_json(1004, "更新任务失败")

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@exception_handler
def delete_task(task_id):
    """删除任务"""
    with get_db() as db:
        if TaskService.delete_task(db, task_id):
            return response_template("deleted")
        return error_json(1005, "删除任务失败")

@tasks_bp.route('/<int:task_id>/log', methods=['GET'])
@exception_handler
def get_task_log(task_id):
    """获取任务日志"""
    content = TaskService.get_task_log(task_id)
    if content is not None:
        return success_json({"content": content})
    return response_template("not_found", msg="获取日志失败", code=404)

@tasks_bp.route('/stats', methods=['GET'])
@exception_handler
def get_stats():
    """获取任务统计"""
    with get_db() as db:
        return success_json(TaskService.get_stats(db))

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@exception_handler
def get_task(task_id):
    """获取任务详情"""
    with get_db() as db:
        task = TaskService.get_task_by_id(db, task_id)
        if task:
            return success_json(task)
        return response_template("not_found", code=1001, msg=f"未找到ID为 {task_id} 的任务")

@tasks_bp.route('/<int:task_id>/images', methods=['POST'])
@exception_handler
def upload_images(task_id):
    """上传任务图片"""
    if 'files' not in request.files:
        return response_template("bad_request", msg="没有上传文件")
        
    files = request.files.getlist('files')
    try:
        validate_file_upload(files)
    except Exception as e:
        return response_template("bad_request", msg=str(e))
        
    with get_db() as db:
        result = TaskService.upload_images(db, task_id, files)
        if result:
            return success_json(result)
        return error_json(3001, "上传图片失败")

@tasks_bp.route('/<int:task_id>/images/<int:image_id>', methods=['DELETE'])
@exception_handler
def delete_image(task_id, image_id):
    """删除任务图片"""
    with get_db() as db:
        if TaskService.delete_image(db, task_id, image_id):
            return response_template("deleted", msg="删除成功")
        return error_json(3002, "删除图片失败")

@tasks_bp.route('/<int:task_id>/mark', methods=['POST'])
@exception_handler
def start_marking(task_id):
    """开始标记"""
    with get_db() as db:
        result = TaskService.start_marking(db, task_id)
        if result:
            if 'error' in result:
                error_code = 2003 if result.get('error_type') == 'SYSTEM_ERROR' else 1002
                return error_json(error_code, result['error'], result.get('task'))
            return success_json(result)
        return error_json(2003, "开始标记失败")

@tasks_bp.route('/<int:task_id>/train', methods=['POST'])
@exception_handler
def start_training(task_id):
    """开始训练"""
    with get_db() as db:
        result = TaskService.start_training(db, task_id)
        if result:
            if 'error' in result:
                error_code = 2002 if result.get('error_type') == 'SYSTEM_ERROR' else 1002
                return error_json(error_code, result['error'], result.get('task'))
            return success_json(result)
        return error_json(2002, "开始训练失败")

@tasks_bp.route('/<int:task_id>/stop', methods=['POST'])
@exception_handler
def stop_task(task_id):
    """终止任务"""
    with get_db() as db:
        if TaskService.stop_task(db, task_id):
            return success_json(None, "任务已终止")
        return error_json(1002, "终止任务失败")

@tasks_bp.route('/<int:task_id>/restart', methods=['POST'])
@exception_handler
def restart_task(task_id):
    """重启任务"""
    with get_db() as db:
        result = TaskService.restart_task(db, task_id)
        if result:
            if not result.get('success', False):
                error_code = 500 if result.get('error_type') == 'SYSTEM_ERROR' else 1002
                return error_json(error_code, result.get('error', "重启任务失败"))
            return success_json(result.get('task'))
        return error_json(500, "重启任务失败")

@tasks_bp.route('/<int:task_id>/cancel', methods=['POST'])
@exception_handler
def cancel_task(task_id):
    """取消任务"""
    with get_db() as db:
        result = TaskService.cancel_task(db, task_id)
        if result:
            if not result.get('success', False):
                error_code = 500 if result.get('error_type') == 'SYSTEM_ERROR' else 1002
                return error_json(error_code, result.get('error', "取消任务失败"))
            return success_json(result.get('task'))
        return error_json(500, "取消任务失败")

@tasks_bp.route('/<int:task_id>/status', methods=['GET'])
@exception_handler
def get_task_status(task_id):
    """获取任务状态"""
    with get_db() as db:
        task_status = TaskService.get_task_status(db, task_id)
        if task_status:
            return success_json(task_status)
        return response_template("not_found", code=1001, msg=f"未找到ID为 {task_id} 的任务") 