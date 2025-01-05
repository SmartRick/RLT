from flask import Flask, jsonify, render_template
from task_queue import TaskQueue, TaskStatus
import logging

app = Flask(__name__)
task_queue = TaskQueue()

@app.route('/')
def index():
    """返回主页"""
    return render_template('index.html')

@app.route('/api/tasks')
def get_tasks():
    """获取所有任务"""
    try:
        tasks = []
        for task in task_queue.queue:
            task_info = {
                "folder_name": task.get("folder_name", ""),
                "status": task.get("status", ""),
                "created_at": task.get("created_at", ""),
                "updated_at": task.get("updated_at", ""),
                "error": task.get("error", ""),
                "lora_path": task.get("lora_path", ""),
                "task_id": task.get("task_id", "")
            }
            tasks.append(task_info)
        return jsonify({"success": True, "data": tasks})
    except Exception as e:
        logging.error(f"获取任务列表失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/stats')
def get_stats():
    """获取任务统计信息"""
    try:
        stats = {
            "total": len(task_queue.queue),
            "downloading": len(task_queue.get_tasks_by_status(TaskStatus.DOWNLOADING)),
            "pending": len(task_queue.get_tasks_by_status(TaskStatus.PENDING)),
            "training": len(task_queue.get_tasks_by_status(TaskStatus.TRAINING)),
            "training_completed": len(task_queue.get_tasks_by_status(TaskStatus.TRAINING_COMPLETED)),
            "pending_upload": len(task_queue.get_tasks_by_status(TaskStatus.PENDING_UPLOAD)),
            "uploading": len(task_queue.get_tasks_by_status(TaskStatus.UPLOADING)),
            "completed": len(task_queue.get_tasks_by_status(TaskStatus.COMPLETED)),
            "failed": {
                "download": len(task_queue.get_tasks_by_status(TaskStatus.DOWNLOAD_FAILED)),
                "training": len(task_queue.get_tasks_by_status(TaskStatus.TRAINING_FAILED)),
                "upload": len(task_queue.get_tasks_by_status(TaskStatus.UPLOAD_FAILED))
            }
        }
        return jsonify({"success": True, "data": stats})
    except Exception as e:
        logging.error(f"获取统计信息失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 