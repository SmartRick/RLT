from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..services.config_service import ConfigService
from ..models.task import Task, TaskImage
from ..database import get_db
from ..utils.logger import setup_logger
import os
from werkzeug.utils import secure_filename
from ..config import config
from ..models.asset import Asset
from sqlalchemy import Boolean
from ..utils.mark_handler import MarkRequestHandler
from concurrent.futures import ThreadPoolExecutor
import time
import json
from ..config import Config

logger = setup_logger('task_service')

class TaskService:
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
            query = query.filter(Task.status == status)
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
        valid_fields = ['name', 'description']
        filtered_data = {k: v for k, v in task_data.items() if k in valid_fields}
        
        task = Task(**filtered_data)
        try:
            db.add(task)
            db.commit()
            db.refresh(task)
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
            for key, value in update_data.items():
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
            db.delete(task)
            db.commit()
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
            'new': db.query(Task).filter(Task.status == 'NEW').count(),
            'marking': db.query(Task).filter(Task.status == 'MARKING').count(),
            'marked': db.query(Task).filter(Task.status == 'MARKED').count(),
            'training': db.query(Task).filter(Task.status == 'TRAINING').count(),
            'completed': db.query(Task).filter(Task.status == 'COMPLETED').count(),
            'error': db.query(Task).filter(Task.status == 'ERROR').count()
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
    def upload_images(db: Session, task_id: int, files: List) -> Optional[Dict]:
        """上传任务图片"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task or task.status != 'NEW':
                return None

            results = []
            # 创建任务专属的上传目录
            task_upload_dir = os.path.join(config.UPLOAD_DIR, str(task_id))
            os.makedirs(task_upload_dir, exist_ok=True)

            for file in files:
                filename = secure_filename(file.filename)
                file_path = os.path.join(task_upload_dir, filename)
                
                # 保存文件
                file.save(file_path)
                
                # 创建图片记录
                image = TaskImage(
                    task_id=task_id,
                    filename=filename,
                    file_path=file_path,
                    preview_url=f'{config.STATIC_URL_PATH}/{task_id}/{filename}',
                    size=os.path.getsize(file_path)
                )
                db.add(image)
                results.append(image.to_dict())

            db.commit()
            return results
        except Exception as e:
            logger.error(f"上传图片失败: {e}")
            db.rollback()
            return None

    @staticmethod
    def delete_image(db: Session, task_id: int, image_id: int) -> bool:
        """删除任务图片"""
        try:
            image = db.query(TaskImage).filter(
                TaskImage.id == image_id,
                TaskImage.task_id == task_id
            ).first()

            if image and os.path.exists(image.file_path):
                os.remove(image.file_path)
                db.delete(image)
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"删除图片失败: {e}")
            db.rollback()
            return False

    @staticmethod
    def get_available_marking_assets(db: Session) -> List[Asset]:
        """获取可用的标记资产"""
        try:
            # 查询所有已连接且未达到最大任务数的资产
            available_assets = db.query(Asset).filter(
                # Asset.status == 'CONNECTED',  # 已连接
                Asset.marking_tasks_count < Asset.max_concurrent_tasks,  # 未达到最大任务数
            ).all()

            # 过滤出AI引擎能力已验证的资产
            verified_assets = [
                asset for asset in available_assets
                if (asset.ai_engine.get('enabled') and 
                    asset.ai_engine.get('verified', False))
            ]

            if not verified_assets:
                logger.warning("没有找到已验证的可用标记资产")
                return []

            return verified_assets

        except Exception as e:
            logger.error(f"获取可用标记资产失败: {str(e)}")
            return []

    @staticmethod
    def get_available_training_assets(db: Session) -> List[Asset]:
        """获取可用的训练资产"""
        return db.query(Asset).filter(
            Asset.status == 'ONLINE',
            Asset.lora_training.op('->>')('enabled') == 'true',
            Asset.lora_training.op('->>')('verified') == 'true',
            Asset.training_tasks_count < Asset.max_concurrent_tasks
        ).order_by(
            Asset.training_tasks_count  # 按任务数排序
        ).all()

    @staticmethod
    def start_marking(db: Session, task_id: int) -> Optional[Dict]:
        """提交标记任务"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            
            # 检查任务是否存在
            if not task:
                raise ValueError("任务不存在")
            
            # 检查任务状态
            if task.status != 'NEW':
                raise ValueError(f"任务状态 {task.status} 不允许提交标记")
            
            # 检查是否有图片
            if not task.images:
                raise ValueError("任务没有上传任何图片")

            # 更新任务状态为已提交
            task.update_status('SUBMITTED', '任务已提交')
            db.commit()

            return task.to_dict()
            
        except ValueError as e:
            logger.warning(f"提交标记任务失败: {str(e)}")
            if task:
                task.update_status('ERROR', str(e))
                db.commit()
            return {
                'error': str(e),
                'error_type': 'VALIDATION_ERROR',
                'task': task.to_dict() if task else None
            }
            
        except Exception as e:
            logger.error(f"开始标记失败: {str(e)}", exc_info=True)
            if task:
                task.update_status('ERROR', f"系统错误: {str(e)}")
                db.commit()
            return {
                'error': f"系统错误: {str(e)}",
                'error_type': 'SYSTEM_ERROR',
                'task': task.to_dict() if task else None
            }

    @staticmethod
    def _process_marking(task_id: int, asset_id: int):
        """处理标记任务"""
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                asset = db.query(Asset).filter(Asset.id == asset_id).first()

                if not task or not asset:
                    raise ValueError("任务或资产不存在")

                logger.info(f"开始处理标记任务 {task_id}")

                # 准备输入输出目录
                input_dir = os.path.join(Config.DATA_DIR, 'uploads', str(task_id))
                output_dir = os.path.join(Config.DATA_DIR, 'uploads', str(task_id), 'marked')
                os.makedirs(output_dir, exist_ok=True)

                # 创建标记处理器
                handler = MarkRequestHandler(asset.ai_engine)
                
                # 发送标记请求
                logger.info(f"发送标记请求: task_id={task_id}, asset_id={asset_id}")
                logger.info(f"输入目录: {input_dir}")
                logger.info(f"输出目录: {output_dir}")
                prompt_id = handler.mark_request(
                    input_folder=input_dir,
                    output_folder=output_dir,
                    resolution=1024,
                    ratio=1.0
                )

                if not prompt_id:
                    raise ValueError("创建标记任务失败")

                logger.info(f"标记任务 {task_id} 创建成功, prompt_id={prompt_id}")

                # 更新任务状态和prompt_id
                task.prompt_id = prompt_id
                db.commit()
                logger.info(f"已更新任务 {task_id} 的 prompt_id")

                return prompt_id

        except Exception as e:
            logger.error(f"标记任务 {task_id} 处理失败: {str(e)}", exc_info=True)
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.update_status('ERROR', str(e))
                    if task.marking_asset:
                        task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                    db.commit()
            raise

    @staticmethod
    def _monitor_mark_status(task_id: int, asset_id: int, prompt_id: str):
        """监控标记任务状态"""
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                asset = db.query(Asset).filter(Asset.id == asset_id).first()

                if not task or not asset:
                    raise ValueError("任务或资产不存在")

                handler = MarkRequestHandler(asset.ai_engine)
                poll_interval = ConfigService.get_value('mark_poll_interval', 5)
                last_progress = 0

                while True:
                    completed, success, task_info = handler.check_status(prompt_id)
                    current_progress = task_info.get("progress", 0)
                    
                    # 只在进度变化时更新数据库
                    if current_progress != last_progress:
                        with get_db() as db:
                            task = db.query(Task).filter(Task.id == task_id).first()
                            if task:
                                task.progress = current_progress
                                # 记录进度变更
                                task.update_status(
                                    'MARKING',
                                    f'标记进度: {current_progress}%'
                                )
                                db.commit()
                    last_progress = current_progress
                    
                    if completed:
                        with get_db() as db:
                            task = db.query(Task).filter(Task.id == task_id).first()
                            if task:
                                if success:
                                    task.update_status('MARKED', '标记完成')
                                    task.progress = 100
                                else:
                                    error_info = task_info.get("error_info", {})
                                    error_message = {
                                        "message": error_info.get("error_message"),
                                        "type": error_info.get("error_type"),
                                        "node": error_info.get("node_type"),
                                        "details": {
                                            "inputs": error_info.get("inputs"),
                                            "traceback": error_info.get("traceback")
                                        }
                                    }
                                    error_json = json.dumps(error_message, indent=2)
                                    task.update_status(
                                        'ERROR',
                                        error_json
                                    )
                                    task.error_message = error_json
                                
                                # 更新资产任务计数
                                if task.marking_asset:
                                    task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                                db.commit()
                        break
                    
                    time.sleep(poll_interval)

        except Exception as e:
            logger.error(f"监控标记任务状态失败: {str(e)}")
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    error_message = json.dumps({
                        "message": str(e),
                        "type": "MONITOR_ERROR"
                    })
                    task.update_status(
                        'ERROR',
                        error_message
                    )
                    task.error_message = error_message
                    if task.marking_asset:
                        task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                    db.commit()

    @staticmethod
    def start_training(db: Session, task_id: int) -> Optional[Dict]:
        """开始训练"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError("任务不存在")
            
            if task.status != 'MARKED':
                raise ValueError(f"任务状态 {task.status} 不允许开始训练")

            # 更新任务状态
            task.update_status('MARKED', '准备开始训练')
            db.commit()
            
            return task.to_dict()
            
        except ValueError as e:
            logger.warning(f"开始训练失败: {str(e)}")
            return {
                'error': str(e),
                'error_type': 'VALIDATION_ERROR'
            }
        except Exception as e:
            logger.error(f"开始训练失败: {str(e)}")
            return {
                'error': f"系统错误: {str(e)}",
                'error_type': 'SYSTEM_ERROR'
            }

    @staticmethod
    def stop_task(db: Session, task_id: int) -> bool:
        """终止任务"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task or task.status not in ['MARKING', 'TRAINING']:
                return False

            # 更新资产任务计数
            if task.status == 'MARKING' and task.marking_asset:
                task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
            elif task.status == 'TRAINING' and task.training_asset:
                task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)

            task.update_status('ERROR', '任务被手动终止')
            db.commit()
            return True
        except Exception as e:
            logger.error(f"终止任务失败: {e}")
            db.rollback()
            return False 

    @staticmethod
    def restart_task(db: Session, task_id: int) -> Optional[Dict]:
        """重启任务"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task or task.status != 'ERROR':
                raise ValueError("只有错误状态的任务可以重启")

            # 根据上一次执行的阶段决定重启到哪个状态
            if task.marking_asset_id and not task.training_asset_id:
                # 如果只有标记资产，说明是在标记阶段失败的
                task.update_status('NEW', '任务已重启')
                task.progress = 0
                task.prompt_id = None
                
                # 清除资产关联
                if task.marking_asset:
                    task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                task.marking_asset_id = None
                
            elif task.training_asset_id:
                # 如果有训练资产，说明是在训练阶段失败的
                task.update_status('MARKED', '任务已重启')
                task.progress = 0
                
                # 清除训练资产关联
                if task.training_asset:
                    task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                task.training_asset_id = None

            db.commit()
            return {
                'success': True,
                'task': task.to_dict()
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
    def cancel_task(db: Session, task_id: int) -> Optional[Dict]:
        """取消任务"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError("任务不存在")
            
            # 只允许取消已提交和已标记状态的任务
            if task.status not in ['SUBMITTED', 'MARKED']:
                raise ValueError(f"任务状态 {task.status} 不允许取消")

            # 更新任务状态
            task.update_status('NEW', '任务已取消')
            task.error_message = None
            task.progress = 0
            
            # 清除资产关联但保留历史记录
            if task.marking_asset:
                task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                task.marking_asset_id = None
                
            if task.training_asset:
                task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                task.training_asset_id = None

            db.commit()
            return {
                'success': True,
                'task': task.to_dict()
            }

        except ValueError as e:
            logger.warning(f"取消任务失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'VALIDATION_ERROR'
            }
        except Exception as e:
            logger.error(f"取消任务失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f"系统错误: {str(e)}",
                'error_type': 'SYSTEM_ERROR'
            } 

    @staticmethod
    def monitor_marking_status(task_id: int):
        """监控标记任务状态"""
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    logger.error(f"任务 {task_id} 不存在")
                    return

                handler = MarkRequestHandler(task.marking_asset.ai_engine)
                
                while True:
                    task_info = handler.get_status(task.prompt_id)
                    if not task_info:
                        logger.error(f"获取任务 {task_id} 状态失败")
                        break

                    # 更新进度
                    progress = task_info.get('progress', 0)
                    if progress != task.progress:
                        task.progress = progress
                        task.add_log(f"标记进度: {progress}%", 'MARKING')
                        db.commit()

                    # 检查是否完成
                    completed = task_info.get('completed', False)
                    if completed:
                        success = task_info.get('success', False)
                        if success:
                            task.update_status('MARKED', '标记完成')
                        else:
                            error_info = task_info.get('error_info', {})
                            task.update_status('ERROR', f"标记失败: {error_info.get('error_message')}")
                        db.commit()
                        break

                    time.sleep(2)  # 每2秒检查一次

        except Exception as e:
            logger.error(f"监控标记任务状态失败: {str(e)}")
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.update_status('ERROR', f"监控失败: {str(e)}")
                    db.commit() 