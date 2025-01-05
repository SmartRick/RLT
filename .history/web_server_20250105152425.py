from flask import Flask, jsonify, send_from_directory, request
from task_queue import TaskQueue, TaskStatus
import logging
import os
import json
import glob
from datetime import datetime

app = Flask(__name__)
task_queue = TaskQueue()

@app.route('/')
def index():
    """返回静态HTML页面"""
    return send_from_directory('static', 'index.html')

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

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取系统配置"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify({"success": True, "data": config})
    except Exception as e:
        logging.error(f"读取配置文件失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/config', methods=['POST'])
def update_config():
    """更新系统配置"""
    try:
        new_config = request.json
        # 备份原配置
        if os.path.exists('config.json'):
            os.rename('config.json', 'config.json.bak')
        
        # 写入新配置
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)
        
        return jsonify({"success": True})
    except Exception as e:
        # 恢复备份
        if os.path.exists('config.json.bak'):
            os.rename('config.json.bak', 'config.json')
        logging.error(f"更新配置文件失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

# 添加错误处理
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"success": False, "error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500

# 添加日志配置
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('web_server.log')
        ]
    )

@app.route('/api/logs')
def get_logs():
    """获取日志文件列表"""
    try:
        log_files = glob.glob('logs/*.log')
        logs = []
        for file in log_files:
            filename = os.path.basename(file)
            # 获取文件修改时间
            mtime = os.path.getmtime(file)
            # 获取文件大小
            size = os.path.getsize(file)
            logs.append({
                "filename": filename,
                "modified": datetime.fromtimestamp(mtime).isoformat(),
                "size": size
            })
        # 按修改时间倒序排序
        logs.sort(key=lambda x: x["modified"], reverse=True)
        return jsonify({"success": True, "data": logs})
    except Exception as e:
        logging.error(f"获取日志列表失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/logs/<filename>')
def get_log_content(filename):
    """获取日志文件内容"""
    try:
        file_path = os.path.join('logs', filename)
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "文件不存在"}), 404
        
        # 获取查询参数
        lines = request.args.get('lines', default=100, type=int)  # 默认返回最后100行
        
        # 读取文件最后N行
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
            total_lines = len(content)
            start = max(0, total_lines - lines)
            content = content[start:]
            
        return jsonify({
            "success": True, 
            "data": {
                "content": content,
                "total_lines": total_lines,
                "showing_lines": len(content)
            }
        })
    except Exception as e:
        logging.error(f"读取日志文件失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    setup_logging()
    logging.info("Web服务器启动...")
    app.run(debug=True, port=5000) 