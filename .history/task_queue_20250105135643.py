"""
@description Lora训练任务队列管理器
"""
import json
import logging
import os
from collections import deque
from threading import Lock
from datetime import datetime

class TaskStatus:
    """任务状态定义"""
    DOWNLOADING = "downloading"    # 下载中
    DOWNLOAD_FAILED = "download_failed"  # 下载失败
    PENDING = "pending"           # 下载完成，等待训练
    TRAINING = "training"         # 训练中
    TRAINING_FAILED = "training_failed"  # 训练失败
    COMPLETED = "completed"       # 训练完成

class TaskQueue:
    def __init__(self, queue_file="task_queue.json"):
        """
        @description 初始化任务队列
        @param {str} queue_file - 队列持久化文件路径
        """
        self.queue_file = queue_file
        self.queue = deque()
        self.lock = Lock()
        
        # 确保队列文件所在目录存在
        os.makedirs(os.path.dirname(os.path.abspath(queue_file)), exist_ok=True)
        
        # 初始化队列文件
        if not os.path.exists(queue_file):
            self.save_queue()
            logging.info(f"创建新的任务队列文件: {queue_file}")
        else:
            self.load_queue()

    def load_queue(self):
        """
        @description 从文件加载任务队列
        """
        try:
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.queue = deque(data)
                logging.info(f"已加载任务队列，当前队列长度: {len(self.queue)}")
        except json.JSONDecodeError:
            logging.warning(f"队列文件格式错误，创建新队列: {self.queue_file}")
            self.queue = deque()
            self.save_queue()
        except Exception as e:
            logging.error(f"加载任务队列失败: {e}")
            self.queue = deque()

    def save_queue(self):
        """
        @description 将任务队列保存到文件
        """
        try:
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.queue), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存任务队列失败: {e}")

    def add_task(self, task_info):
        """
        @description 添加任务到队列
        @param {dict} task_info - 任务信息
        @return {bool} 是否添加成功
        """
        try:
            with self.lock:
                # 检查任务是否已在队列中
                folder_name = task_info.get('folder_name')
                if any(task['folder_name'] == folder_name for task in self.queue):
                    logging.warning(f"任务已在队列中 - {folder_name}")
                    return False
                    
                self.queue.append(task_info)
                self.save_queue()
                logging.info(f"新任务已添加到队列 - {folder_name}")
                return True
        except Exception as e:
            logging.error(f"添加任务失败: {e}")
            return False

    def get_next_task(self):
        """
        @description 获取下一个待处理任务
        @return {dict|None} 任务信息或None
        """
        with self.lock:
            if self.queue:
                task = self.queue.popleft()
                self.save_queue()
                logging.info(f"获取任务 - {task.get('folder_name')}")
                return task
            return None

    def peek_next_task(self):
        """
        @description 查看下一个待处理任务（不移除）
        @return {dict|None} 任务信息或None
        """
        with self.lock:
            if self.queue:
                return self.queue[0]
            return None

    def get_queue_length(self):
        """
        @description 获取当前队列长度
        @return {int} 队列长度
        """
        return len(self.queue)

    def update_task_status(self, folder_name, status, **extra_info):
        """
        @description 更新任务状态
        @param {str} folder_name - 文件夹名称
        @param {str} status - 新状态
        @param {dict} extra_info - 额外信息
        """
        with self.lock:
            for task in self.queue:
                if task["folder_name"] == folder_name:
                    task["status"] = status
                    task["updated_at"] = datetime.now().isoformat()
                    if "error" in extra_info:  # 记录错误信息
                        task["last_error"] = {
                            "message": extra_info["error"],
                            "timestamp": datetime.now().isoformat()
                        }
                    task.update(extra_info)
                    logging.info(f"任务状态更新 - {folder_name}: {status}")
                    if "error" in extra_info:
                        logging.error(f"任务错误 - {folder_name}: {extra_info['error']}")
                    self.save_queue()
                    break

    def get_task_by_folder(self, folder_name):
        """
        @description 根据文件夹名称获取任务
        @param {str} folder_name - 文件夹名称
        @return {dict|None} 任务信息或None
        """
        with self.lock:
            for task in self.queue:
                if task["folder_name"] == folder_name:
                    return task
            return None 

    def add_download_task(self, folder_name, src_path):
        """
        @description 添加下载任务
        @param {str} folder_name - 文件夹名称
        @param {str} src_path - 源文件路径
        @return {bool} 是否添加成功
        """
        task_info = {
            "folder_name": folder_name,
            "src_path": src_path,
            "folder_path": None,  # 初始为None，下载完成后更新
            "status": TaskStatus.DOWNLOADING,
            "created_at": datetime.now().isoformat()
        }
        return self.add_task(task_info)

    def get_tasks_by_status(self, status):
        """
        @description 获取指定状态的所有任务
        @param {str} status - 任务状态
        @return {list} 任务列表
        """
        with self.lock:
            return [task for task in self.queue if task["status"] == status]

    def mark_download_complete(self, folder_name, local_path):
        """
        @description 标记下载完成
        @param {str} folder_name - 文件夹名称
        @param {str} local_path - 本地路径
        """
        self.update_task_status(folder_name, TaskStatus.PENDING, 
                              local_path=local_path,
                              folder_path=local_path)  # 更新folder_path

    def mark_download_failed(self, folder_name, error_msg):
        """
        @description 标记下载失败
        @param {str} folder_name - 文件夹名称
        @param {str} error_msg - 错误信息
        """
        self.update_task_status(folder_name, TaskStatus.DOWNLOAD_FAILED, 
                              error=error_msg)

    def mark_training_start(self, folder_name, task_id):
        """
        @description 标记开始训练
        @param {str} folder_name - 文件夹名称
        @param {str} task_id - 训练任务ID
        """
        self.update_task_status(folder_name, TaskStatus.TRAINING, 
                              task_id=task_id)

    def mark_training_complete(self, folder_name, lora_path):
        """
        @description 标记训练完成
        @param {str} folder_name - 文件夹名称
        @param {str} lora_path - Lora模型路径
        """
        self.update_task_status(folder_name, TaskStatus.COMPLETED, 
                              lora_path=lora_path)

    def mark_training_failed(self, folder_name, error_msg):
        """
        @description 标记训练失败
        @param {str} folder_name - 文件夹名称
        @param {str} error_msg - 错误信息
        """
        self.update_task_status(folder_name, TaskStatus.TRAINING_FAILED, 
                              error=error_msg)

    def get_next_pending_task(self):
        """
        @description 获取下一个待训练任务
        @return {dict|None} 任务信息
        """
        with self.lock:
            for task in self.queue:
                if task["status"] == TaskStatus.PENDING:
                    return task
            return None

    def get_next_download_task(self):
        """
        @description 获取下一个待下载任务
        @return {dict|None} 任务信息
        """
        with self.lock:
            for task in self.queue:
                if task["status"] == TaskStatus.DOWNLOADING:
                    return task
            return None 

    def get_task_error(self, folder_name):
        """
        @description 获取任务的最后一次错误信息
        @param {str} folder_name - 文件夹名称
        @return {dict|None} 错误信息或None
        """
        task = self.get_task_by_folder(folder_name)
        return task.get("last_error") if task else None 

    def has_task(self, folder_name):
        """
        @description 检查任务是否存在于队列中
        @param {str} folder_name - 文件夹名称
        @return {bool} 是否存在
        """
        with self.lock:
            return any(task["folder_name"] == folder_name for task in self.queue) 