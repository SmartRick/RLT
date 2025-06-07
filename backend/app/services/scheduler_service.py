import threading
import time
from typing import List, Dict
from sqlalchemy import func
from ..database import get_db
from ..models.task import Task, TaskStatus
from ..utils.logger import setup_logger
from .task_service import TaskService
from .config_service import ConfigService
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from ..models.asset import Asset

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
                    Task.status == TaskStatus.MARKING,
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

                # 恢复训练中的任务监控
                training_tasks = db.query(Task).filter(
                    Task.status == TaskStatus.TRAINING,
                    Task.prompt_id.isnot(None),  # 已有训练任务ID的任务
                    Task.training_asset_id.isnot(None)  # 已分配训练资产的任务
                ).all()
                
                for task in training_tasks:
                    if task.training_asset_id and task.prompt_id:
                        logger.info(f"恢复训练任务 {task.id} 的状态监控")
                        self._monitor_pool.submit(
                            TaskService._monitor_training_status,
                            task.id,
                            task.training_asset_id,
                            task.prompt_id
                        )
                        
                # 更新任务计数
                self._update_asset_task_counts(db)

        except Exception as e:
            logger.error(f"恢复任务监控失败: {str(e)}", exc_info=True)
            
    def _update_asset_task_counts(self, db):
        """更新资产的任务计数"""
        try:
            # 重置所有资产的任务计数
            db.query(Asset).update({
                Asset.marking_tasks_count: 0,
                Asset.training_tasks_count: 0
            })
            
            # 更新标记任务计数
            marking_assets = db.query(Asset.id, func.count(Task.id)).join(
                Task, Asset.id == Task.marking_asset_id
            ).filter(
                Task.status == TaskStatus.MARKING
            ).group_by(Asset.id).all()
            
            for asset_id, count in marking_assets:
                db.query(Asset).filter(Asset.id == asset_id).update({
                    Asset.marking_tasks_count: count
                })
                
            # 更新训练任务计数
            training_assets = db.query(Asset.id, func.count(Task.id)).join(
                Task, Asset.id == Task.training_asset_id
            ).filter(
                Task.status == TaskStatus.TRAINING
            ).group_by(Asset.id).all()
            
            for asset_id, count in training_assets:
                db.query(Asset).filter(Asset.id == asset_id).update({
                    Asset.training_tasks_count: count
                })
                
            db.commit()
            logger.info("已更新资产任务计数")
            
        except Exception as e:
            logger.error(f"更新资产任务计数失败: {str(e)}", exc_info=True)

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
                logger.info("训练任务调度器开始调度")
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
            Task.status == TaskStatus.SUBMITTED,
            Task.images.any()
        ).all()

        if not tasks:
            return 0

        logger.info(f"发现 {len(tasks)} 个待标记任务: {[t.id for t in tasks]}")
        available_assets = TaskService.get_available_marking_assets()
        
        if not available_assets:
            logger.warning("没有可用的标记资产")
            
            # 为每个待标记任务更新日志
            for task in tasks:
                try:
                    # 查找是否已有类似日志
                    retry_count = 1
                    existing_log_id = None
                    
                    # 获取任务的最近日志
                    recent_logs = task.get_all_logs(10)
                    
                    # 如果有日志，检查是否存在"暂无可用标记资产"的日志
                    if recent_logs:
                        for log in recent_logs:
                            if "暂无可用标记资产" in log.get('message', ''):
                                # 从日志消息中提取尝试次数
                                try:
                                    log_msg = log.get('message', '')
                                    retry_count = int(log_msg.split('第')[1].split('次')[0]) + 1
                                    existing_log_id = log.get('id')
                                except:
                                    retry_count = 1
                                break
                    
                    # 更新日志消息
                    log_message = f"暂无可用标记资产，等待分配资产中（第{retry_count}次尝试）"
                    
                    # 如果找到现有日志，则更新它
                    if existing_log_id:
                        # 直接在数据库中更新日志消息
                        from app.models.task import TaskStatusLog
                        db.query(TaskStatusLog).filter(TaskStatusLog.id == existing_log_id).update(
                            {"message": log_message}
                        )
                        db.commit()
                        logger.info(f"已更新任务 {task.id} 的现有日志")
                    else:
                        # 如果没有找到现有日志，则添加新的
                        task.add_log(log_message, db=db)
                        logger.info(f"已为任务 {task.id} 添加第一条日志")
                    
                except Exception as e:
                    logger.error(f"为任务 {task.id} 更新日志失败: {str(e)}")
            
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
                    if not task or task.status != TaskStatus.SUBMITTED:
                        logger.warning(f"任务 {task.id} 状态已改变，跳过处理")
                        continue

                    # 更新任务状态和资产计数
                    task.progress = 0
                    task.marking_asset_id = asset.id
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
        tasks = db.query(Task).filter(Task.status == TaskStatus.MARKED).all()

        if not tasks:
            return 0

        logger.info(f"发现 {len(tasks)} 个待训练任务")
        available_assets = TaskService.get_available_training_assets()
        
        if not available_assets:
            logger.warning("没有可用的训练资产")
            
            # 为每个待训练任务更新日志
            for task in tasks:
                try:
                    # 查找是否已有类似日志
                    retry_count = 1
                    existing_log_id = None
                    
                    # 获取任务的最近日志
                    recent_logs = task.get_all_logs(10)
                    
                    # 如果有日志，检查是否存在"暂无可用训练资产"的日志
                    if recent_logs:
                        for log in recent_logs:
                            if "暂无可用训练资产" in log.get('message', ''):
                                # 从日志消息中提取尝试次数
                                try:
                                    log_msg = log.get('message', '')
                                    retry_count = int(log_msg.split('第')[1].split('次')[0]) + 1
                                    existing_log_id = log.get('id')
                                except:
                                    retry_count = 1
                                break
                    
                    # 更新日志消息
                    log_message = f"暂无可用训练资产，等待分配资产中（第{retry_count}次尝试）"
                    
                    # 如果找到现有日志，则更新它
                    if existing_log_id:
                        # 直接在数据库中更新日志消息
                        from app.models.task import TaskStatusLog
                        db.query(TaskStatusLog).filter(TaskStatusLog.id == existing_log_id).update(
                            {"message": log_message}
                        )
                        db.commit()
                        logger.info(f"已更新任务 {task.id} 的现有日志")
                    else:
                        # 如果没有找到现有日志，则添加新的
                        task.add_log(log_message, db=db)
                        logger.info(f"已为任务 {task.id} 添加第一条日志")
                    
                except Exception as e:
                    logger.error(f"为任务 {task.id} 更新日志失败: {str(e)}")
            
            return 0

        logger.info(f"找到 {len(available_assets)} 个可用训练资产: {[a.id for a in available_assets]}")
        processed_count = 0

        for task in tasks:
            try:
                asset = min(available_assets, key=lambda x: x.training_tasks_count)
                if asset.training_tasks_count >= asset.max_concurrent_tasks:
                    logger.warning(f"资产 {asset.id} 已达到最大任务数: {asset.max_concurrent_tasks}")
                    continue

                logger.info(f"准备分配任务 {task.id} 给资产 {asset.id}")

                # 使用锁保护状态更新
                acquired = self._train_lock.acquire(timeout=5)  # 添加超时
                if not acquired:
                    logger.warning(f"获取训练任务锁超时，跳过任务 {task.id}")
                    continue

                try:
                    # 重新检查任务状态（可能在等待锁期间被其他进程修改）
                    task = db.query(Task).filter(Task.id == task.id).first()
                    if not task or task.status != TaskStatus.MARKED:
                        logger.warning(f"任务 {task.id} 状态已改变，跳过处理")
                        continue

                    # 更新任务状态和资产计数
                    task.progress = 0
                    task.training_asset_id = asset.id
                    asset.training_tasks_count += 1
                    db.commit()
                    logger.info(f"已更新任务 {task.id} 状态和资产计数")

                    # 提交训练任务并获取训练任务ID
                    future = self._train_pool.submit(
                        TaskService._process_training,
                        task.id,
                        asset.id
                    )
                    logger.info(f"已提交任务 {task.id} 到训练线程池")

                    # 在提交任务成功后，启动该训练任务的监控线程
                    def start_monitor(f):
                        try:
                            training_task_id = f.result()
                            logger.info(f"任务 {task.id} 获取到训练任务ID: {training_task_id}")
                            if training_task_id:
                                self._monitor_pool.submit(
                                    TaskService._monitor_training_status,
                                    task.id,
                                    asset.id,
                                    training_task_id
                                )
                                logger.info(f"已启动任务 {task.id} 的训练状态监控")
                        except Exception as e:
                            logger.error(f"启动任务 {task.id} 训练监控失败: {str(e)}", exc_info=True)

                    future.add_done_callback(start_monitor)
                    processed_count += 1

                finally:
                    self._train_lock.release()

            except Exception as e:
                logger.error(f"处理训练任务 {task.id} 失败: {str(e)}", exc_info=True)
                try:
                    with get_db() as err_db:
                        task = err_db.query(Task).filter(Task.id == task.id).first()
                        if task:
                            task.update_status(TaskStatus.ERROR, f"训练失败: {str(e)}", db=err_db)
                            task.add_log(f"训练失败: {str(e)}", db=err_db)
                            if hasattr(task, 'training_asset') and task.training_asset:
                                task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                                err_db.commit()
                except Exception as inner_e:
                    logger.error(f"更新任务 {task.id} 错误状态失败: {str(inner_e)}", exc_info=True)
                continue

        return processed_count

# 创建全局调度器实例
scheduler = TaskScheduler() 