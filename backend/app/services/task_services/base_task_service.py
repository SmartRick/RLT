from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ...models.task import Task, TaskStatus, TaskStatusHistory, TaskStatusLog
from ...database import get_db
from ...utils.logger import setup_logger
import os
import shutil
from ...models.task import TaskImage
from ...config import config
from ...services.common_service import CommonService
from ...utils.train_handler import TrainRequestHandler
from ...utils.mark_handler import MarkRequestHandler
logger = setup_logger('base_task_service')

class BaseTaskService:
    @staticmethod
    def list_tasks(
        db: Session,
        status: Optional[str] = None,
        search: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """获取任务列表"""
        query = db.query(Task)
        
        if status:
            query = query.filter(Task.status == TaskStatus(status))
        if search:
            query = query.filter(Task.name.ilike(f'%{search}%'))
        if start_date:
            start = datetime.fromisoformat(start_date)
            query = query.filter(Task.created_at >= start)
        if end_date:
            end = datetime.fromisoformat(end_date)
            query = query.filter(Task.created_at <= end)
        
        tasks = query.order_by(Task.created_at.desc()).all()
        return [task.to_dict() for task in tasks]

    @staticmethod
    def create_task(db: Session, task_data: Dict) -> Optional[Dict]:
        """创建新任务"""
        # 只保留模型中定义的字段
        valid_fields = ['name', 'description', 'auto_training']
        filtered_data = {k: v for k, v in task_data.items() if k in valid_fields}
        task = Task(**filtered_data)
        try:
            # 将任务名称翻译为英文作为触发词
            if 'name' in filtered_data and filtered_data['name']:
                task_name = filtered_data['name']
                # 调用翻译服务，将中文名称翻译为英文
                translate_result = CommonService.translate_text(task_name, to_lang='en')
                
                if translate_result and translate_result['success'] and translate_result['result']:
                    # 获取翻译结果
                    english_name = translate_result['result'].strip()
                    logger.info(f"翻译任务名称: {task_name} -> {english_name}")
                    task.mark_config = {'trigger_words': english_name}
                
            # 设置自动训练标志，如果未提供则默认为True
            if 'auto_training' not in filtered_data:
                task.auto_training = True
            
            db.add(task)
            # 初始化状态为NEW并添加日志记录
            db.commit()
            db.refresh(task)
            task.update_status('NEW', '任务已创建', db=db)  # 不自动提交
            return task.to_dict()
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            db.rollback()
            return None

    @staticmethod
    def update_task(db: Session, task_id: int, update_data: Dict) -> Optional[Dict]:
        """更新任务"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
            
        try:
            # 只允许更新特定字段
            valid_fields = ['name', 'description', 'mark_config', 'training_config', 
                           'use_global_mark_config', 'use_global_training_config', 'auto_training']
            filtered_data = {k: v for k, v in update_data.items() if k in valid_fields}
            
            for key, value in filtered_data.items():
                setattr(task, key, value)
            db.commit()
            db.refresh(task)
            return task.to_dict()
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            db.rollback()
            return None

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """删除任务"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
            
        try:
            images = db.query(TaskImage).filter(TaskImage.task_id == task_id).all()
            for image in images:
                # 删除单个图片文件
                if image.file_path and os.path.exists(image.file_path):
                    os.remove(image.file_path)
                    logger.info(f"已删除图片文件: {image.file_path}")
                
            # 2. 删除任务目录
            task_upload_dir = os.path.join(config.UPLOAD_DIR, str(task_id))
            if os.path.exists(task_upload_dir):
                shutil.rmtree(task_upload_dir)
                logger.info(f"已删除任务目录: {task_upload_dir}")
            
            # 3. 删除数据库中的任务记录（会级联删除关联的图片记录）
            db.delete(task)
            db.commit()
            logger.info(f"已删除任务记录: {task_id}")
            return True
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            db.rollback()
            return False

    @staticmethod
    def get_task_log(task_id: int) -> Optional[str]:
        """获取任务日志"""
        log_file = f'logs/task_{task_id}.log'
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取日志失败: {e}")
            return None

    @staticmethod
    def get_stats(db: Session) -> Dict:
        """获取任务统计"""
        stats = {
            'total': db.query(Task).count(),
            'new': db.query(Task).filter(Task.status == TaskStatus.NEW).count(),
            'marking': db.query(Task).filter(Task.status == TaskStatus.MARKING).count(),
            'marked': db.query(Task).filter(Task.status == TaskStatus.MARKED).count(),
            'training': db.query(Task).filter(Task.status == TaskStatus.TRAINING).count(),
            'completed': db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count(),
            'error': db.query(Task).filter(Task.status == TaskStatus.ERROR).count()
        }
        return stats 

    @staticmethod
    def get_task_by_id(db: Session, task_id: int) -> Optional[Dict]:
        """获取任务详情"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                return task.to_dict()
            return None
        except Exception as e:
            logger.error(f"获取任务详情失败: {e}")
            return None
            
    @staticmethod
    def get_task_status(db: Session, task_id: int) -> Optional[Dict]:
        """
        获取任务状态
        返回任务的当前状态、进度、错误信息等
        """
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return None
                    # 将状态历史转换为与之前 JSON 字段格式兼容的字典
            status_history_dict = {}
            for history in task.status_history:
                status_history_dict[history.status] = {
                    'start_time': history.start_time.isoformat(),
                    'end_time': history.end_time.isoformat() if history.end_time else None,
                    'logs': [log.to_dict() for log in history.logs]
                }
            # 整理返回数据
            return {
                'id': task.id,
                'name': task.name,
                'status': task.status.value if task.status else None,
                'progress': task.progress,
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'status_history': status_history_dict,
                'marking_asset_id': task.marking_asset_id,
                'training_asset_id': task.training_asset_id
            }
        except Exception as e:
            logger.error(f"获取任务状态失败: {str(e)}", exc_info=True)
            return None
            
    @staticmethod
    def stop_task(db: Session, task_id: int) -> Dict:
        """
        终止任务并回滚到前一个状态
        
        根据任务类型使用不同的终止逻辑：
        - 对于训练中的任务，使用TrainHandler的cancel_training方法，回滚到MARKED状态
        - 对于打标中的任务，使用ComfyUIAPI工具中的中断方法，回滚到NEW状态
        
        Returns:
            包含操作结果的字典
        """
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"success": False, "message": "任务不存在"}
                
            if task.status not in [TaskStatus.MARKING, TaskStatus.TRAINING]:
                return {"success": False, "message": f"任务状态为 {task.status}，不能终止"}

            cancel_success = False
            cancel_message = "任务已终止"
            # 确定目标回滚状态
            target_status = TaskStatus.NEW if task.status == TaskStatus.MARKING else TaskStatus.MARKED

            # 根据任务类型执行不同的终止逻辑
            if task.status == TaskStatus.TRAINING and task.training_asset and task.prompt_id:
                # 训练任务终止
                logger.info(f"开始终止训练任务: {task_id}")
                
                # 创建训练处理器，直接传入资产对象
                
                handler = TrainRequestHandler(task.training_asset)
                
                # 调用训练处理器的取消任务方法
                cancel_success = handler.cancel_training(task.prompt_id)
                
                if cancel_success:
                    logger.info(f"成功终止训练任务 {task_id}")
                    cancel_message = "训练任务已成功终止并回滚到MARKED状态"
                else:
                    logger.warning(f"终止训练任务 {task_id} 失败，但将继续回滚任务状态")
                    cancel_message = "无法通过API终止训练任务，但已回滚任务状态"
                
            elif task.status == TaskStatus.MARKING and task.marking_asset and task.prompt_id:
                # 打标任务终止
                logger.info(f"开始终止打标任务: {task_id}")
                
                # 使用asset对象初始化一个MarkRequestHandler，以便获取正确的连接信息
                
                mark_handler = MarkRequestHandler(task.marking_asset)
                
                # 直接使用mark_handler的interrupt方法
                cancel_success = mark_handler.interrupt()
                
                if cancel_success:
                    logger.info(f"成功终止打标任务 {task_id}")
                    cancel_message = "打标任务已成功终止并回滚到NEW状态"
                else:
                    logger.warning(f"终止打标任务 {task_id} 失败")
                    cancel_message = "无法通过API终止打标任务，但已回滚任务状态"
            
            # 回滚任务状态
            rollback_success = BaseTaskService._rollback_task_state(
                db=db,
                task=task,
                target_status=target_status,
                delete_history=True,
                clear_assets=True
            )
            
            if not rollback_success:
                logger.warning(f"回滚任务 {task_id} 状态失败")
                cancel_message += "，但回滚状态失败"
            
            return {
                "success": True,
                "message": cancel_message,
                "api_cancel_success": cancel_success,
                "rollback_success": rollback_success,
                "target_status": target_status.value,
                "task": task.to_dict()
            }
            
        except Exception as e:
            logger.error(f"终止任务失败: {str(e)}", exc_info=True)
            db.rollback()
            return {
                "success": False,
                "message": f"终止任务失败: {str(e)}",
                "error": str(e)
            }
            
    @staticmethod
    def restart_task(db: Session, task_id: int) -> Optional[Dict]:
        """重启任务"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task or task.status not in [TaskStatus.ERROR, TaskStatus.COMPLETED]:
                raise ValueError("只有错误状态或完成状态的任务可以重启")

            # 根据上一次执行的阶段决定重启到哪个状态
            target_status = None
            if task.status == TaskStatus.COMPLETED or (task.marking_asset_id and not task.training_asset_id):
                # 完成状态的任务或者只有标记资产的任务（在标记阶段失败的），恢复到新建状态
                target_status = TaskStatus.NEW
            elif task.training_asset_id:
                # 如果有训练资产，说明是在训练阶段失败的
                target_status = TaskStatus.MARKED
            else:
                # 默认回到新建状态
                target_status = TaskStatus.NEW
            
            # 使用公共回滚方法
            rollback_success = BaseTaskService._rollback_task_state(
                db=db,
                task=task,
                target_status=target_status,
                delete_history=True,
                clear_assets=True
            )
            
            if rollback_success:
                return {
                    'success': True,
                    'message': f'任务已成功重启并回滚到{target_status.value}状态',
                    'task': task.to_dict()
                }
            else:
                return {
                    'success': False,
                    'error': '回滚任务状态失败',
                    'error_type': 'SYSTEM_ERROR'
                }

        except ValueError as e:
            logger.warning(f"重启任务失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'VALIDATION_ERROR'
            }
        except Exception as e:
            logger.error(f"重启任务失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f"系统错误: {str(e)}",
                'error_type': 'SYSTEM_ERROR'
            }
            
    @staticmethod
    def _rollback_task_state(db: Session, task: Task, target_status: TaskStatus, 
                             delete_history: bool = True, clear_assets: bool = True,
                             keep_marked_files: bool = False) -> bool:
        """
        将任务回滚到指定状态
        
        Args:
            db: 数据库会话
            task: 任务对象
            target_status: 目标状态
            delete_history: 是否删除历史记录
            clear_assets: 是否清除资产关联
            keep_marked_files: 如果为False且回滚到NEW状态，则删除标记文件
            
        Returns:
            操作是否成功
        """
        try:
            # 如果需要删除历史记录
            if delete_history:
                # 确定需要删除的状态历史记录
                status_to_delete = []
                if target_status == TaskStatus.NEW:
                    # 回滚到新建状态，删除所有除NEW外的历史
                    status_to_delete = [s.value for s in TaskStatus if s != TaskStatus.NEW]
                elif target_status == TaskStatus.MARKED:
                    # 回滚到已标记状态，删除ERROR和TRAINING状态
                    status_to_delete = ['ERROR', 'TRAINING']

                # 获取需要删除的历史记录
                histories = db.query(TaskStatusHistory).filter(
                    TaskStatusHistory.task_id == task.id,
                    TaskStatusHistory.status.in_(status_to_delete)
                ).all()
                
                # 获取需要删除的历史记录ID
                history_ids = [h.id for h in histories]
                
                # 删除这些历史记录相关的日志
                if history_ids:
                    db.query(TaskStatusLog).filter(TaskStatusLog.history_id.in_(history_ids)).delete(synchronize_session=False)
                
                # 删除历史记录
                for history in histories:
                    db.delete(history)
                    
                db.commit()
                
            # 如果回滚到NEW状态且需要删除标记文件
            if target_status == TaskStatus.NEW and not keep_marked_files and task.marked_images_path and os.path.exists(task.marked_images_path):
                try:
                    # 只删除目录下的文件，保留目录本身
                    for filename in os.listdir(task.marked_images_path):
                        file_path = os.path.join(task.marked_images_path, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            logger.info(f"已删除标记文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除标记文件失败: {str(e)}")
                
                # 清除执行历史ID，但保留执行历史记录
                task.execution_history_id = None
                
            # 更新任务状态和重置进度
            task.update_status(target_status, f'任务已回滚到{target_status.value}状态', db=db)
            task.progress = 0
            
            # 清除当前阶段的prompt_id
            if (target_status == TaskStatus.NEW and task.status == TaskStatus.MARKING) or \
               (target_status == TaskStatus.MARKED and task.status == TaskStatus.TRAINING):
                task.prompt_id = None
                
                # 清除资产关联
            if clear_assets:
                if target_status == TaskStatus.NEW and task.marking_asset:
                    task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                task.marking_asset_id = None
                
                if task.training_asset:
                    task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                task.training_asset_id = None
                
            db.commit()
            return True
        
        except Exception as e:
            logger.error(f"回滚任务状态失败: {str(e)}", exc_info=True)
            db.rollback()
            return False 