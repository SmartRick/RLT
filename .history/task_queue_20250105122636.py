"""
@description Lora训练任务队列管理器
"""
import json
import logging
import os
from collections import deque
from threading import Lock

class TaskQueue:
    def __init__(self, queue_file="task_queue.json"):
        """
        @description 初始化任务队列
        @param {str} queue_file - 队列持久化文件路径
        """
        self.queue_file = queue_file
        self.queue = deque()
        self.lock = Lock()
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