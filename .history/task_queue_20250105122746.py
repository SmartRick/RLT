"""
@description Lora训练任务队列管理器
"""
import json
import logging
import os
from collections import deque
from threading import Lock

class TaskQueue:
    def __init__(self, queue_file="queue/task_queue.json"):
        """
        @description 初始化任务队列
        @param {str} queue_file - 队列持久化文件路径
        """
        self.queue_file = queue_file
        self.queue = deque()
        self.lock = Lock()
        
        # 确保队列文件所在目录存在
        os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
        
        # 如果队列文件不存在，创建空队列文件
        if not os.path.exists(self.queue_file):
            self.save_queue()
            logging.info("创建新的任务队列文件")
        else:
            self.load_queue()

    def load_queue(self):
        """
        @description 从文件加载任务队列
        """
        try:
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.queue = deque(data)
                    logging.info(f"已加载任务队列，当前队列长度: {len(self.queue)}")
        except Exception as e:
            logging.error(f"加载任务队列失败: {e}")

    def save_queue(self):
        """
        @description 将任务队列保存到文件
        """
        try:
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.queue), f)
        except Exception as e:
            logging.error(f"保存任务队列失败: {e}")

    def add_task(self, task_info):
        """
        @description 添加任务到队列
        @param {dict} task_info - 任务信息
        """
        with self.lock:
            self.queue.append(task_info)
            logging.info(f"新任务已添加到队列 - {task_info.get('folder_name')}")
            self.save_queue()

    def get_next_task(self):
        """
        @description 获取下一个待处理任务
        @return {dict|None} 任务信息或None
        """
        with self.lock:
            if self.queue:
                task = self.queue.popleft()
                self.save_queue()
                return task
            return None

    def peek_next_task(self):
        """
        @description 查看下一个待处理任务（不移除）
        @return {dict|None} 任务信息或None
        """
        with self.lock:
            return self.queue[0] if self.queue else None

    def get_queue_length(self):
        """
        @description 获取当前队列长度
        @return {int} 队列长度
        """
        return len(self.queue)

    def update_task_status(self, folder_name, status):
        """
        @description 更新任务状态
        @param {str} folder_name - 文件夹名称
        @param {str} status - 任务状态
        """
        with self.lock:
            for task in self.queue:
                if task["folder_name"] == folder_name:
                    task["status"] = status
                    logging.info(f"任务状态更新 - {folder_name}: {status}")
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

    def check_queue_status(self):
        """
        @description 检查队列状态
        @return {dict} 队列状态信息
        """
        status = {
            "total": len(self.queue),
            "pending": 0,
            "running": 0,
            "failed": 0
        }
        
        for task in self.queue:
            task_status = task.get("status", "unknown")
            if task_status in status:
                status[task_status] += 1
                
        return status

    def log_queue_status(self):
        """
        @description 记录当前队列状态
        """
        status = self.check_queue_status()
        logging.info(f"当前队列状态:")
        logging.info(f"- 总任务数: {status['total']}")
        logging.info(f"- 待处理: {status['pending']}")
        logging.info(f"- 执行中: {status['running']}")
        logging.info(f"- 失败: {status['failed']}") 