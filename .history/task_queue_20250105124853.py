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
        
        # 确保队列文件所在目录存在
        os.makedirs(os.path.dirname(os.path.abspath(queue_file)), exist_ok=True)
        
        # 如果队列文件不存在，创建空队列文件
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