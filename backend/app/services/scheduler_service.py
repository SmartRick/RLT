import threading
import time
from typing import List, Dict
from ..database import get_db
from ..models.task import Task
from ..utils.logger import setup_logger
from .task_service import TaskService
from .config_service import ConfigService
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

logger = setup_logger('scheduler')

class TaskScheduler:
    def __init__(self):
        self._running = False
        self._mark_thread = None
        self._train_thread = None
        self._mark_lock = threading.Lock()
        self._train_lock = threading.Lock()
        self._mark_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="MarkWorker")
        self._monitor_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix="MonitorWorker")
        self._train_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="TrainWorker")

    def start(self):
        """启动调度器"""
        if self._running:
            return
            
        self._running = True
        
        # 恢复处理中的任务状态监控
        self._recover_task_monitors()
        
        # 启动调度线程
        self._mark_thread = threading.Thread(
            target=self._run_marking_scheduler,
            daemon=True,
            name="MarkScheduler"
        )
        self._mark_thread.start()
        
        self._train_thread = threading.Thread(
            target=self._run_training_scheduler,
            daemon=True,
            name="TrainScheduler"
        )
        self._train_thread.start()
        
        logger.info("任务调度器已启动")

    def _recover_task_monitors(self):
        """恢复任务状态监控"""
        try:
            with get_db() as db:
                # 恢复标记中的任务监控
                marking_tasks = db.query(Task).filter(
                    Task.status == 'MARKING',
                    Task.prompt_id.isnot(None)  # 已有prompt_id的任务
                ).all()
                
                for task in marking_tasks:
                    if task.marking_asset_id and task.prompt_id:
                        logger.info(f"恢复标记任务 {task.id} 的状态监控")
                        self._monitor_pool.submit(
                            TaskService._monitor_mark_status,
                            task.id,
                            task.marking_asset_id,
                            task.prompt_id
                        )

                # TODO: 恢复训练中的任务监控
                # ...

        except Exception as e:
            logger.error(f"恢复任务监控失败: {str(e)}", exc_info=True)

    def stop(self):
        """停止调度器"""
        self._running = False
        if self._mark_thread:
            self._mark_thread.join()
        if self._train_thread:
            self._train_thread.join()
            
        # 关闭线程池
        self._mark_pool.shutdown(wait=True)
        self._train_pool.shutdown(wait=True)
        
        logger.info("任务调度器已停止")

    def _run_marking_scheduler(self):
        """标记任务调度循环"""
        while self._running:
            try:
                with get_db() as db:
                    count = self._process_marking_tasks(db)
                    if count:
                        logger.info(f"本次调度处理了 {count} 个标记任务")
                    else:
                        logger.debug("当前没有需要处理的标记任务")
            except Exception as e:
                logger.error(f"标记任务调度出错: {str(e)}", exc_info=True)
            
            interval = ConfigService.get_value('mark_scheduler_interval', 10)
            logger.debug(f"标记调度器休眠 {interval} 秒")
            time.sleep(interval)

    def _run_training_scheduler(self):
        """训练任务调度循环"""
        while self._running:
            try:
                with self._train_lock:  # 使用锁保护数据库操作
                    with get_db() as db:
                        count = self._process_training_tasks(db)
                        if count:
                            logger.info(f"本次调度处理了 {count} 个训练任务")
                        else:
                            logger.debug("当前没有需要处理的训练任务")
            except Exception as e:
                logger.error(f"训练任务调度出错: {str(e)}", exc_info=True)
            
            interval = ConfigService.get_value('train_scheduler_interval', 15)
            logger.debug(f"训练调度器休眠 {interval} 秒")
            time.sleep(interval)

    def _process_marking_tasks(self, db) -> int:
        """处理待标记任务"""
        # 查询可用任务和资产
        tasks = db.query(Task).filter(
            Task.status == 'SUBMITTED',
            Task.images.any()
        ).all()

        if not tasks:
            return 0

        logger.info(f"发现 {len(tasks)} 个待标记任务: {[t.id for t in tasks]}")
        available_assets = TaskService.get_available_marking_assets(db)
        
        if not available_assets:
            logger.warning("没有可用的标记资产")
            return 0

        logger.info(f"找到 {len(available_assets)} 个可用标记资产: {[a.id for a in available_assets]}")
        processed_count = 0

        for task in tasks:
            try:
                asset = min(available_assets, key=lambda x: x.marking_tasks_count)
                if asset.marking_tasks_count >= asset.max_concurrent_tasks:
                    logger.warning(f"资产 {asset.id} 已达到最大任务数: {asset.max_concurrent_tasks}")
                    continue

                logger.info(f"准备分配任务 {task.id} 给资产 {asset.id}")

                # 使用锁保护状态更新
                acquired = self._mark_lock.acquire(timeout=5)  # 添加超时
                if not acquired:
                    logger.warning(f"获取任务锁超时，跳过任务 {task.id}")
                    continue

                try:
                    # 重新检查任务状态（可能在等待锁期间被其他进程修改）
                    task = db.query(Task).filter(Task.id == task.id).first()
                    if not task or task.status != 'SUBMITTED':
                        logger.warning(f"任务 {task.id} 状态已改变，跳过处理")
                        continue

                    # 更新任务状态和资产计数
                    task.status = 'MARKING'
                    task.progress = 0
                    task.marking_asset_id = asset.id
                    task.error_message = None
                    asset.marking_tasks_count += 1
                    db.commit()
                    logger.info(f"已更新任务 {task.id} 状态为 MARKING")

                    # 提交标记任务并获取prompt_id
                    future = self._mark_pool.submit(
                        TaskService._process_marking,
                        task.id,
                        asset.id
                    )
                    logger.info(f"已提交任务 {task.id} 到标记线程池")

                    ## 在提交任务成功后，启动该标记任务的监控线程
                    def start_monitor(f):
                        try:
                            prompt_id = f.result()
                            logger.info(f"任务 {task.id} 获取到 prompt_id: {prompt_id}")
                            if prompt_id:
                                self._monitor_pool.submit(
                                    TaskService._monitor_mark_status,
                                    task.id,
                                    asset.id,
                                    prompt_id
                                )
                                logger.info(f"已启动任务 {task.id} 的状态监控")
                        except Exception as e:
                            logger.error(f"启动任务 {task.id} 监控失败: {str(e)}", exc_info=True)

                    future.add_done_callback(start_monitor)
                    processed_count += 1

                finally:
                    self._mark_lock.release()

            except Exception as e:
                logger.error(f"处理标记任务 {task.id} 失败: {str(e)}", exc_info=True)
                continue

        return processed_count

    def _process_training_tasks(self, db) -> int:
        """处理待训练任务"""
        tasks = db.query(Task).filter(Task.status == 'MARKED').all()

        if not tasks:
            return 0

        logger.info(f"发现 {len(tasks)} 个待训练任务")
        available_assets = TaskService.get_available_training_assets(db)
        
        if not available_assets:
            logger.warning("没有可用的训练资产")
            return 0

        logger.info(f"找到 {len(available_assets)} 个可用训练资产")
        processed_count = 0

        for task in tasks:
            try:
                asset = min(available_assets, key=lambda x: x.training_tasks_count)
                if asset.training_tasks_count >= asset.max_concurrent_tasks:
                    continue

                # 更新任务状态和资产计数
                with self._train_lock:
                    task.status = 'TRAINING'
                    task.progress = 0
                    task.training_asset_id = asset.id
                    asset.training_tasks_count += 1
                    db.commit()

                # TODO: 提交到训练线程池
                # self._train_pool.submit(
                #     TaskService._process_training,
                #     task.id,
                #     asset.id
                # )

                processed_count += 1
                logger.info(f"任务 {task.id} 提交到训练线程池")

            except Exception as e:
                logger.error(f"处理训练任务 {task.id} 失败: {str(e)}")
                continue

        return processed_count

# 创建全局调度器实例
scheduler = TaskScheduler() 