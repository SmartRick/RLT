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
from ..services.local_asset_service import LocalAssetService
import traceback

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
            # 初始化状态为NEW并添加日志记录
            task.update_status('NEW', '任务已创建', db=None)  # 不自动提交
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
            # 1. 获取并删除关联的图片文件
            images = db.query(TaskImage).filter(TaskImage.task_id == task_id).all()
            for image in images:
                # 删除单个图片文件
                if image.file_path and os.path.exists(image.file_path):
                    os.remove(image.file_path)
                    logger.info(f"已删除图片文件: {image.file_path}")
                
            # 2. 删除任务目录
            task_upload_dir = os.path.join(config.UPLOAD_DIR, str(task_id))
            if os.path.exists(task_upload_dir):
                import shutil
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
        """获取可用于标记的资产"""
        try:
            # 查询具有标记能力且当前连接状态的资产
            assets = db.query(Asset).filter(
                Asset.status == 'CONNECTED',
                Asset.ai_engine.op('->')('enabled').in_(['true', 'True', '1']),
                Asset.marking_tasks_count < Asset.max_concurrent_tasks
            ).all()
        
            return assets
        except Exception as e:
            logger.error(f"获取可用标记资产失败: {str(e)}")
            return []

    @staticmethod
    def get_available_training_assets(db: Session) -> List[Asset]:
        """获取可用于训练的资产"""
        try:
            # 查询具有训练能力且当前连接状态的资产
            assets = db.query(Asset).filter(
                Asset.status == 'CONNECTED',
                Asset.lora_training.op('->')('enabled').in_(['true', 'True', '1']),
                Asset.training_tasks_count < Asset.max_concurrent_tasks
            ).all()
            
                
            return assets
        except Exception as e:
            logger.error(f"获取可用训练资产失败: {str(e)}")
            return []

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

            # 更新任务状态为已提交，并传递数据库会话
            task.update_status('SUBMITTED', '任务已提交', db=db)

            return task.to_dict()
            
        except ValueError as e:
            logger.warning(f"提交标记任务失败: {str(e)}")
            if task:
                task.update_status('ERROR', str(e), db=db)
            return {
                'error': str(e),
                'error_type': 'VALIDATION_ERROR',
                'task': task.to_dict() if task else None
            }
            
        except Exception as e:
            logger.error(f"开始标记失败: {str(e)}", exc_info=True)
            if task:
                task.update_status('ERROR', f"系统错误: {str(e)}", db=db)
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
                
                # 更新任务状态，记录开始处理标记
                task.update_status('MARKING', f'开始处理标记任务，使用资产: {asset.name}', db=db)

                # 准备输入输出目录
                input_dir = os.path.join(Config.DATA_DIR, 'uploads', str(task_id))
                output_dir = os.path.join(Config.DATA_DIR, 'marked', str(task_id))

                # 记录目录信息
                task.add_log(f'输入目录: {input_dir}', log_type=task.LOG_TYPE_INFO, db=db)
                task.add_log(f'输出目录: {output_dir}', log_type=task.LOG_TYPE_INFO, db=db)

                # 创建标记处理器
                handler = MarkRequestHandler(asset.ai_engine, asset.ip)
                
                # 记录请求准备信息
                task.add_log(f'准备发送标记请求: task_id={task_id}, asset_id={asset_id}, asset_ip={asset.ip}', log_type=task.LOG_TYPE_INFO, db=db)
                
                
                try:
                    # 发送标记请求
                    logger.info(f"发送标记请求: task_id={task_id}, asset_id={asset_id}")
                    logger.info(f"输入目录: {input_dir}")
                    logger.info(f"输出目录: {output_dir}")
                    prompt_id = handler.mark_request(
                        input_folder=input_dir,
                        output_folder=output_dir,
                        resolution=1024,
                        ratio="1:1"
                    )
                except Exception as req_error:
                    # 捕获请求异常，记录详细错误信息
                    error_detail = {
                        "message": str(req_error),
                        "type": type(req_error).__name__,
                        "traceback": str(traceback.format_exc())
                    }
                    error_json = json.dumps(error_detail, indent=2)
                    task.update_status('ERROR', f'标记请求失败: {str(req_error)}', db=db)
                    task.add_error_log(error_json, db=db)
                    if task.marking_asset:
                        task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                        db.commit()
                    # 重新抛出异常，让上层处理
                    raise ValueError(f"标记请求失败: {str(req_error)}")

                if not prompt_id:
                    task.add_log('没有获取到有效的prompt_id', log_type=task.LOG_TYPE_ERROR, db=db)
                    raise ValueError("创建标记任务失败，未获取到prompt_id")

                # 记录成功获取prompt_id
                task.add_log(f'标记任务创建成功，prompt_id={prompt_id}', log_type=task.LOG_TYPE_SUCCESS, db=db)
                logger.info(f"标记任务 {task_id} 创建成功, prompt_id={prompt_id}")

                # 更新任务状态和prompt_id
                task.prompt_id = prompt_id
                db.commit()
                logger.info(f"已更新任务 {task_id} 的 prompt_id")

                return prompt_id

        except Exception as e:
            logger.error(f"标记任务 {task_id} 处理失败: {str(e)}", exc_info=True)
            # 捕获所有异常，确保错误信息被记录
            error_detail = {
                "message": str(e),
                "type": type(e).__name__,
                "traceback": str(traceback.format_exc())
            }
            error_json = json.dumps(error_detail, indent=2)
            
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.update_status('ERROR', f'标记处理失败: {str(e)}', db=db)
                    task.add_error_log(error_json, db=db)
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
                
                # 记录开始监控
                task.add_log(f'开始监控标记任务状态, prompt_id={prompt_id}', log_type=task.LOG_TYPE_INFO, db=db)

                handler = MarkRequestHandler(asset.ai_engine, asset.ip)
                poll_interval = ConfigService.get_value('mark_poll_interval', 5)
                last_progress = 0

                while True:
                    try:
                        completed, success, task_info = handler.check_status(prompt_id)
                        
                        if completed:
                            with get_db() as complete_db:
                                task = complete_db.query(Task).filter(Task.id == task_id).first()
                                if task:
                                    if success:
                                        task.update_status('MARKED', '标记完成', db=complete_db)
                                        task.progress = 100
                                        task.add_log('标记任务成功完成', log_type=task.LOG_TYPE_SUCCESS, db=complete_db)
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
                                            f'标记失败: {error_info.get("error_message")}',
                                            db=complete_db
                                        )
                                        task.add_error_log(error_json, db=complete_db)
                                    
                                    # 更新资产任务计数
                                    if task.marking_asset:
                                        task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                                        complete_db.commit()
                            break
                    except Exception as check_err:
                        # 捕获检查状态时的错误
                        logger.error(f"检查任务状态时出错: {str(check_err)}")
                        with get_db() as err_db:
                            task = err_db.query(Task).filter(Task.id == task_id).first()
                            if task:
                                task.add_log(f'检查任务状态出错: {str(check_err)}', log_type=task.LOG_TYPE_WARNING, db=err_db)
                        # 继续尝试，不中断监控
                    
                    time.sleep(poll_interval)

        except Exception as e:
            logger.error(f"监控标记任务状态失败: {str(e)}")
            # 记录详细的错误信息
            error_detail = {
                "message": str(e),
                "type": type(e).__name__,
                "traceback": str(traceback.format_exc())
            }
            error_json = json.dumps(error_detail, indent=2)
            
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.update_status('ERROR', f'监控失败: {str(e)}', db=db)
                    task.add_error_log(error_json, db=db)
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
            task.update_status('MARKED', '准备开始训练', db=db)
            
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

            task.update_status('ERROR', '任务被手动终止', db=db)
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
                task.update_status('NEW', '任务已重启', db=db)
                task.progress = 0
                task.prompt_id = None
                
                # 清除资产关联
                if task.marking_asset:
                    task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                task.marking_asset_id = None
                
            elif task.training_asset_id:
                # 如果有训练资产，说明是在训练阶段失败的
                task.update_status('MARKED', '任务已重启', db=db)
                task.progress = 0
                
                # 清除训练资产关联
                if task.training_asset:
                    task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                task.training_asset_id = None

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
            task.update_status('NEW', '任务已取消', db=db)
            task.error_message = None
            task.progress = 0
            
            # 清除资产关联但保留历史记录
            if task.marking_asset:
                task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                task.marking_asset_id = None
                
            if task.training_asset:
                task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                task.training_asset_id = None

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

                handler = MarkRequestHandler(task.marking_asset.ai_engine, task.marking_asset.ip)
                
                while True:
                    task_info = handler.get_status(task.prompt_id)
                    if not task_info:
                        logger.error(f"获取任务 {task_id} 状态失败")
                        break

                    # 更新进度
                    progress = task_info.get('progress', 0)
                    if progress != task.progress:
                        task.add_progress_log(progress, db=db)

                    # 检查是否完成
                    completed = task_info.get('completed', False)
                    if completed:
                        success = task_info.get('success', False)
                        if success:
                            task.update_status('MARKED', '标记完成', db=db)
                        else:
                            error_info = task_info.get('error_info', {})
                            task.update_status('ERROR', f"标记失败: {error_info.get('error_message')}", db=db)
                        break

                    time.sleep(2)  # 每2秒检查一次

        except Exception as e:
            logger.error(f"监控标记任务状态失败: {str(e)}")
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.update_status('ERROR', f"监控失败: {str(e)}", db=db)

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
            
            # 整理返回数据
            return {
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'progress': task.progress,
                'error_message': task.error_message,
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'status_history': task.status_history,
                'marking_asset_id': task.marking_asset_id,
                'training_asset_id': task.training_asset_id
            }
        except Exception as e:
            logger.error(f"获取任务状态失败: {str(e)}", exc_info=True)
            return None 