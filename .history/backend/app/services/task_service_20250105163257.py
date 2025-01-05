from typing import List, Dict, Optional
from datetime import datetime
from ..config import config
from ..utils.file_handler import load_json, save_json
from ..utils.logger import setup_logger

logger = setup_logger('task_service')

class TaskService:
    @staticmethod
    def list_tasks(
        status: Optional[str] = None,
        search: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """获取任务列表"""
        tasks = load_json(config.TASKS_FILE, [])
        
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
        
        return tasks

    @staticmethod
    def create_task(task_data: Dict) -> Optional[Dict]:
        """创建新任务"""
        tasks = load_json(config.TASKS_FILE, [])
        
        task = {
            **task_data,
            'id': str(len(tasks) + 1),
            'created_at': datetime.now().isoformat(),
            'status': 'PENDING'
        }
        
        tasks.append(task)
        if save_json(config.TASKS_FILE, tasks):
            return task
        return None

    @staticmethod
    def update_task(task_id: str, update_data: Dict) -> Optional[Dict]:
        """更新任务"""
        tasks = load_json(config.TASKS_FILE, [])
        
        for task in tasks:
            if task['id'] == task_id:
                task.update(update_data)
                task['updated_at'] = datetime.now().isoformat()
                
                if save_json(config.TASKS_FILE, tasks):
                    return task
                return None
        
        return None

    @staticmethod
    def delete_task(task_id: str) -> bool:
        """删除任务"""
        tasks = load_json(config.TASKS_FILE, [])
        tasks = [t for t in tasks if t['id'] != task_id]
        return save_json(config.TASKS_FILE, tasks)

    @staticmethod
    def get_task_log(task_id: str) -> Optional[str]:
        """获取任务日志"""
        log_file = os.path.join(config.LOGS_DIR, f'task_{task_id}.log')
        if not os.path.exists(log_file):
            return None
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取日志失败: {e}")
            return None

    @staticmethod
    def get_stats() -> Dict:
        """获取任务统计"""
        tasks = load_json(config.TASKS_FILE, [])
        return {
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