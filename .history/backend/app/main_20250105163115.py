from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
import logging
from typing import Dict, List

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_FILE = 'config.json'
TASKS_FILE = 'tasks.json'

# 默认配置
DEFAULT_CONFIG = {
    'source_dir': '/path/to/source',
    'lora_output_path': '/path/to/output',
    'scheduling_minute': 5,
    'mark_pan_dir': '/loraFile/mark',
    'lora_pan_upload_dir': '/loraFile/lora'
}

def load_config() -> Dict:
    """加载配置文件"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return DEFAULT_CONFIG
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return DEFAULT_CONFIG

def save_config(config: Dict) -> bool:
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return False

def load_tasks() -> List[Dict]:
    """加载任务列表"""
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"加载任务失败: {e}")
        return []

def save_tasks(tasks: List[Dict]) -> bool:
    """保存任务列表"""
    try:
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存任务失败: {e}")
        return False

# 配置相关接口
@app.route('/api/v1/settings/', methods=['GET'])
def get_settings():
    """获取系统配置"""
    return jsonify(load_config())

@app.route('/api/v1/settings/', methods=['PUT'])
def update_settings():
    """更新系统配置"""
    config = request.json
    if save_config(config):
        return jsonify({'message': '配置已更新'})
    return jsonify({'error': '保存配置失败'}), 500

# 任务相关接口
@app.route('/api/v1/tasks/', methods=['GET'])
def list_tasks():
    """获取任务列表"""
    tasks = load_tasks()
    
    # 处理过滤参数
    status = request.args.get('status')
    search = request.args.get('search')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if status:
        tasks = [t for t in tasks if t['status'] == status]
    if search:
        tasks = [t for t in tasks if search.lower() in t['folder_name'].lower()]
    if start_date:
        start = datetime.fromisoformat(start_date)
        tasks = [t for t in tasks if datetime.fromisoformat(t['created_at']) >= start]
    if end_date:
        end = datetime.fromisoformat(end_date)
        tasks = [t for t in tasks if datetime.fromisoformat(t['created_at']) <= end]
    
    return jsonify(tasks)

@app.route('/api/v1/tasks/', methods=['POST'])
def create_task():
    """创建新任务"""
    task = request.json
    task['id'] = str(len(load_tasks()) + 1)  # 简单的ID生成
    task['created_at'] = datetime.now().isoformat()
    task['status'] = 'PENDING'
    
    tasks = load_tasks()
    tasks.append(task)
    
    if save_tasks(tasks):
        return jsonify(task)
    return jsonify({'error': '创建任务失败'}), 500

@app.route('/api/v1/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务状态"""
    update_data = request.json
    tasks = load_tasks()
    
    for task in tasks:
        if task['id'] == task_id:
            task.update(update_data)
            task['updated_at'] = datetime.now().isoformat()
            
            if save_tasks(tasks):
                return jsonify(task)
            return jsonify({'error': '更新任务失败'}), 500
            
    return jsonify({'error': '任务不存在'}), 404

@app.route('/api/v1/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    tasks = load_tasks()
    tasks = [t for t in tasks if t['id'] != task_id]
    
    if save_tasks(tasks):
        return jsonify({'message': '任务已删除'})
    return jsonify({'error': '删除任务失败'}), 500

@app.route('/api/v1/tasks/<task_id>/log', methods=['GET'])
def get_task_log(task_id):
    """获取任务日志"""
    tasks = load_tasks()
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if not task:
        return jsonify({'error': '任务不存在'}), 404
        
    log_file = f"logs/task_{task_id}.log"
    if not os.path.exists(log_file):
        return jsonify({'content': '暂无日志'})
        
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        logger.error(f"读取日志失败: {e}")
        return jsonify({'error': '读取日志失败'}), 500

@app.route('/api/v1/stats/', methods=['GET'])
def get_stats():
    """获取任务统计信息"""
    tasks = load_tasks()
    stats = {
        'total': len(tasks),
        'downloading': sum(1 for t in tasks if t['status'] == 'DOWNLOADING'),
        'pending': sum(1 for t in tasks if t['status'] == 'PENDING'),
        'training': sum(1 for t in tasks if t['status'] == 'TRAINING'),
        'pending_upload': sum(1 for t in tasks if t['status'] == 'PENDING_UPLOAD'),
        'uploading': sum(1 for t in tasks if t['status'] == 'UPLOADING'),
        'completed': sum(1 for t in tasks if t['status'] == 'COMPLETED'),
        'failed': {
            'download': sum(1 for t in tasks if t['status'] == 'DOWNLOAD_FAILED'),
            'training': sum(1 for t in tasks if t['status'] == 'TRAINING_FAILED'),
            'upload': sum(1 for t in tasks if t['status'] == 'UPLOAD_FAILED')
        }
    }
    return jsonify(stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 