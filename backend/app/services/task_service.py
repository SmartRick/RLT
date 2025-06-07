from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..services.config_service import ConfigService
from ..models.task import Task, TaskImage, TaskStatus, TaskStatusHistory, TaskStatusLog
from ..utils.train_handler import TrainRequestHandler, TrainConfig
from ..database import get_db
from ..utils.logger import setup_logger
from ..utils.common import copy_attributes
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
from ..services.asset_service import AssetService
from ..utils.mark_handler import MarkConfig

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
        valid_fields = ['name', 'description']
        filtered_data = {k: v for k, v in task_data.items() if k in valid_fields}
        task = Task(**filtered_data)
        try:
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
    def upload_images(db: Session, task_id: int, files: List) -> Optional[Dict]:
        """上传任务图片"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task or task.status != TaskStatus.NEW:
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
                    preview_url=f'/data/uploads/{task_id}/{filename}',
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

            if not image:
                logger.warning(f"未找到图片: task_id={task_id}, image_id={image_id}")
                return False
                
            # 1. 删除原始图片文件
            if image.file_path and os.path.exists(image.file_path):
                os.remove(image.file_path)
                logger.info(f"已删除图片文件: {image.file_path}")
            
            # 2. 删除对应的打标文本文件（如果存在）
            name_without_ext = os.path.splitext(image.filename)[0]
            marked_dir = os.path.join(Config.MARKED_DIR, str(task_id))
            text_file_path = os.path.join(marked_dir, f"{name_without_ext}.txt")
            
            if os.path.exists(text_file_path):
                os.remove(text_file_path)
                logger.info(f"已删除打标文本文件: {text_file_path}")
            
            # 3. 从数据库中删除图片记录
            db.delete(image)
            
            # 4. 记录操作日志
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.add_log(f"删除了图片: {image.filename}", db=db)
            else:
                db.commit()
                
            return True
        except Exception as e:
            logger.error(f"删除图片失败: {e}")
            db.rollback()
            return False

    @staticmethod
    def batch_delete_images(db: Session, task_id: int, image_ids: List[int]) -> Dict:
        """批量删除任务图片
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            image_ids: 要删除的图片ID列表
            
        Returns:
            包含操作结果的字典，包括成功删除的图片和失败的图片
        """
        # 检查任务是否存在
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {
                "success": False,
                "message": f"任务 {task_id} 不存在",
                "deleted": [],
                "failed": [{"id": image_id, "reason": "任务不存在"} for image_id in image_ids]
            }
            
        # 检查任务状态，只有NEW状态的任务可以删除图片
        if task.status != TaskStatus.NEW:
            return {
                "success": False,
                "message": f"任务状态为 {task.status}，不允许删除图片",
                "deleted": [],
                "failed": [{"id": image_id, "reason": f"任务状态为 {task.status}，不允许删除图片"} for image_id in image_ids]
            }
            
        results = {
            "success": True,
            "message": "批量删除图片完成",
            "deleted": [],
            "failed": []
        }
        
        for image_id in image_ids:
            try:
                # 查询图片
                image = db.query(TaskImage).filter(
                    TaskImage.id == image_id,
                    TaskImage.task_id == task_id
                ).first()
                
                if not image:
                    results["failed"].append({
                        "id": image_id,
                        "reason": f"图片不存在或不属于任务 {task_id}"
                    })
                    continue
                    
                image_info = image.to_dict()
                
                # 1. 删除原始图片文件
                if image.file_path and os.path.exists(image.file_path):
                    os.remove(image.file_path)
                
                # 2. 删除对应的打标文本文件（如果存在）
                name_without_ext = os.path.splitext(image.filename)[0]
                marked_dir = os.path.join(Config.MARKED_DIR, str(task_id))
                text_file_path = os.path.join(marked_dir, f"{name_without_ext}.txt")
                
                if os.path.exists(text_file_path):
                    os.remove(text_file_path)
                
                # 3. 从数据库中删除图片记录
                db.delete(image)
                
                # 添加到成功列表
                results["deleted"].append(image_info)
                
            except Exception as e:
                logger.error(f"删除图片 {image_id} 失败: {str(e)}")
                results["failed"].append({
                    "id": image_id,
                    "reason": str(e)
                })
        
        # 记录操作日志
        if results["deleted"]:
            deleted_filenames = [img.get("filename", f"ID:{img.get('id')}") for img in results["deleted"]]
            task.add_log(f"批量删除了 {len(results['deleted'])} 个图片: {', '.join(deleted_filenames)}", db=db)
        
        # 如果全部失败，则整体标记为失败
        if not results["deleted"] and results["failed"]:
            results["success"] = False
            results["message"] = "所有图片删除都失败了"
        
        return results

    @staticmethod
    def get_available_marking_assets() -> List[Asset]:
        """获取可用于标记的资产"""
        try:
            assets = AssetService.verify_all_assets('ai_engine')
            # 过滤出任务数量未达到上限的资产
            return [asset for asset in assets if asset.marking_tasks_count < asset.max_concurrent_tasks]
        except Exception as e:
            logger.error(f"获取可用标记资产失败: {str(e)}")
            return []

    @staticmethod
    def get_available_training_assets() -> List[Asset]:
        """获取可用于训练的资产"""
        try:
            assets = AssetService.verify_all_assets('lora_training')
            # 过滤出任务数量未达到上限的资产
            return [asset for asset in assets if asset.training_tasks_count < asset.max_concurrent_tasks]
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
            if task.status != TaskStatus.NEW:
                raise ValueError(f"任务状态 {task.status} 不允许提交标记")
            
            # 检查是否有图片
            if not task.images:
                raise ValueError("任务没有上传任何图片")

            # 更新任务状态为已提交，并传递数据库会话
            task.update_status(TaskStatus.SUBMITTED, '任务已提交', db=db)

            return task.to_dict()
            
        except ValueError as e:
            logger.warning(f"提交标记任务失败: {str(e)}")
            if task:
                task.update_status(TaskStatus.ERROR, str(e), db=db)
            return {
                'error': str(e),
                'error_type': 'VALIDATION_ERROR',
                'task': task.to_dict() if task else None
            }
            
        except Exception as e:
            logger.error(f"开始标记失败: {str(e)}", exc_info=True)
            if task:
                task.update_status(TaskStatus.ERROR, f"系统错误: {str(e)}", db=db)
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
                task.update_status(TaskStatus.MARKING, f'开始处理标记任务，使用资产: {asset.name}')

                mark_config = ConfigService.get_task_mark_config(task.id)
                training_config = ConfigService.get_task_training_config(task.id)
                # 准备输入输出目录
                input_dir = os.path.join(Config.UPLOAD_DIR, str(task_id))
                output_dir = os.path.join(Config.MARKED_DIR, str(task_id),f"{training_config.get('repeat_num',10)}_rick")
                task.marked_images_path = output_dir

                # 记录目录信息
                task.add_log(f'输入目录: {input_dir}')
                task.add_log(f'输出目录: {output_dir}')

                # 创建标记处理器
                # 记录请求准备信息
                task.add_log(f'准备发送标记请求: task_id={task_id}, asset_id={asset_id}, asset_ip={asset.ip}')
                db.commit()
                
                try:
                    handler = MarkRequestHandler(asset.ip,asset.ai_engine.get('port',8188))
                    # 发送标记请求
                    logger.info(f"发送标记请求: task_id={task_id}, asset_id={asset_id}")
                    logger.info(f"输入目录: {input_dir}")
                    logger.info(f"输出目录: {output_dir}")
                    
                    # 创建MarkConfig对象
                    config = MarkConfig(
                        input_folder=input_dir,
                        output_folder=output_dir
                    )        
                    copy_attributes(mark_config, config)
                    logger.info("打标配置mark_config",mark_config)
                    prompt_id = handler.mark_request(config)
                except Exception as req_error:
                    # 捕获请求异常，记录详细错误信息
                    error_detail = {
                        "message": str(req_error),
                        "type": type(req_error).__name__,
                        "traceback": str(traceback.format_exc())
                    }
                    error_json = json.dumps(error_detail, indent=2)
                    task.update_status(TaskStatus.ERROR, f'标记请求失败: {str(req_error)}', db=db)
                    task.add_log(error_json, db=db)
                    if task.marking_asset:
                        task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                        db.commit()
                    # 重新抛出异常，让上层处理
                    raise ValueError(f"标记请求失败: {str(req_error)}")

                if not prompt_id:
                    task.add_log('没有获取到有效的prompt_id', db=db)
                    raise ValueError("创建标记任务失败，未获取到prompt_id")

                # 记录成功获取prompt_id
                task.add_log(f'标记任务创建成功，prompt_id={prompt_id}', db=db)
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
                    task.update_status(TaskStatus.ERROR, f'标记处理失败: {str(e)}', db=db)
                    task.add_log(error_json, db=db)
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
                task.add_log(f'开始监控标记任务状态, prompt_id={prompt_id}', db=db)
                handler = MarkRequestHandler(asset.ip,asset.ai_engine.get('port',8188))
                poll_interval = ConfigService.get_value('mark_poll_interval', 5)
                mark_config = ConfigService.get_task_mark_config(task.id)
                last_progress = 0
                error_count = 0
                while True:
                    try:
                        completed, success, task_info = handler.check_status(prompt_id,mark_config)
                        logger.info(f"检查标记任务状态: {completed}, {success}, {task_info}")
                        with get_db() as complete_db:
                            task = complete_db.query(Task).filter(Task.id == task_id).first()
                            # 可能在打标过程中取消了任务，不再继续监听
                            if task and task.status == TaskStatus.NEW:
                                logger.info("监听打标过程中任务被取消")
                                break
                            if completed and task:
                                if success:
                                    task.update_status(TaskStatus.MARKED, '标记完成', db=complete_db)
                                    task.progress = 100
                                    task.add_log('标记任务成功完成', db=complete_db)
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
                                        TaskStatus.ERROR,
                                        f'标记失败: {error_info.get("error_message")}',
                                        db=complete_db
                                    )
                                    task.add_log(error_json, db=complete_db)
                                
                                # 更新资产任务计数
                                if task.marking_asset:
                                    task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                                    complete_db.commit()
                            break
                        # 重置错误计数
                        error_count = 0
                        
                        
                    except Exception as check_err:
                        # 捕获检查状态时的错误
                        error_count += 1
                        logger.error(f"检查任务状态时出错 ({error_count}/3): {str(check_err)}")
                        
                        with get_db() as err_db:
                            task = err_db.query(Task).filter(Task.id == task_id).first()
                            if task:
                                task.add_log(f'检查任务状态出错 ({error_count}/3): {str(check_err)}', db=err_db)
                            # 如果累计出错3次，停止监控并更新任务状态
                            if error_count >= 3:
                                task = err_db.query(Task).filter(Task.id == task_id).first()
                                if task:
                                    task.update_status(TaskStatus.ERROR, f'连续3次检查状态失败，停止监控: {str(check_err)}', db=err_db)
                                    if task.marking_asset:
                                        task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                                        err_db.commit()
                                break
                    
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
                    task.update_status(TaskStatus.ERROR, f'监控失败: {str(e)}', db=db)
                    task.add_log(error_json, db=db)
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
            
            if task.status != TaskStatus.MARKED:
                raise ValueError(f"任务状态 {task.status} 不允许开始训练")

            # 更新任务状态
            task.update_status(TaskStatus.TRAINING, '准备开始训练', db=db)
            
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
            if not task or task.status not in [TaskStatus.MARKING, TaskStatus.TRAINING]:
                return False

            # 更新资产任务计数
            if task.status == TaskStatus.MARKING and task.marking_asset:
                task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
            elif task.status == TaskStatus.TRAINING and task.training_asset:
                task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)

            task.update_status(TaskStatus.ERROR, '任务被手动终止', db=db)
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
            if not task or task.status != TaskStatus.ERROR:
                raise ValueError("只有错误状态的任务可以重启")

            # 根据上一次执行的阶段决定重启到哪个状态
            if task.marking_asset_id and not task.training_asset_id:
                # 如果只有标记资产，说明是在标记阶段失败的
                # 清除任务历史状态和日志
                # 首先获取所有与该任务相关的历史记录ID
                history_ids = [h.id for h in db.query(TaskStatusHistory).filter(TaskStatusHistory.task_id == task_id).all()]
                # 删除这些历史记录相关的日志
                if history_ids:
                    db.query(TaskStatusLog).filter(TaskStatusLog.history_id.in_(history_ids)).delete(synchronize_session=False)
                # 删除历史记录
                db.query(TaskStatusHistory).filter(TaskStatusHistory.task_id == task_id).delete()
                db.commit()
                
                task.update_status(TaskStatus.NEW, '任务已重启', db=db)
                task.progress = 0
                task.prompt_id = None
                
                # 清除资产关联
                if task.marking_asset:
                    task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                task.marking_asset_id = None
                
            elif task.training_asset_id:
                # 如果有训练资产，说明是在训练阶段失败的
                # 只清除ERROR和TRAINING状态的历史记录和日志
                error_training_histories = db.query(TaskStatusHistory).filter(
                    TaskStatusHistory.task_id == task_id,
                    TaskStatusHistory.status.in_(['ERROR', 'TRAINING'])
                ).all()
                
                # 获取需要删除的历史记录ID
                history_ids = [h.id for h in error_training_histories]
                
                # 删除这些历史记录相关的日志
                if history_ids:
                    db.query(TaskStatusLog).filter(TaskStatusLog.history_id.in_(history_ids)).delete(synchronize_session=False)
                
                # 删除历史记录
                for history in error_training_histories:
                    db.delete(history)
                
                db.commit()
                
                task.update_status(TaskStatus.MARKED, '任务已重启', db=db)
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
            if task.status not in [TaskStatus.SUBMITTED, TaskStatus.MARKED]:
                raise ValueError(f"任务状态 {task.status} 不允许取消")

            # 首先获取所有与该任务相关的历史记录ID
            history_ids = [h.id for h in db.query(TaskStatusHistory).filter(TaskStatusHistory.task_id == task_id).all()]
            # 删除这些历史记录相关的日志
            if history_ids:
                db.query(TaskStatusLog).filter(TaskStatusLog.history_id.in_(history_ids)).delete(synchronize_session=False)
            # 删除历史记录
            db.query(TaskStatusHistory).filter(TaskStatusHistory.task_id == task_id).delete()
            # 删除任务
            db.commit()
            
            task.update_status(TaskStatus.NEW, '任务已取消', db=db)
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
    def get_marked_texts(db: Session, task_id: int) -> Optional[Dict]:
        """
        获取打标后的文本内容
        返回文件名称和打标文本内容的映射
        """
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.warning(f"任务 {task_id} 不存在")
                return None
            
            if task.status not in [TaskStatus.MARKED, TaskStatus.TRAINING, TaskStatus.COMPLETED]:
                logger.warning(f"任务 {task_id} 状态为 {task.status}，未完成打标")
                return None
            
            # 打标后的文本存储目录
            if not os.path.exists(task.marked_images_path):
                logger.warning(f"打标目录不存在: {task.marked_images_path}")
                return None
            
            # 构建图片文件名到原始文件名的映射
            image_name_map = {}
            for image in task.images:
                # 获取不带扩展名的文件名作为key
                name_without_ext = os.path.splitext(image.filename)[0]
                image_name_map[name_without_ext] = image.filename
            
            # 获取marked_images_path的相对路径（从/data开始）
            if task.marked_images_path:
                # 从完整路径中提取相对路径
                relative_path = task.marked_images_path.replace(config.PROJECT_ROOT, "")
                # 确保路径以/data开头
                relative_path = relative_path.replace("\\", "/")
            else:
                # 如果没有marked_images_path，使用上传路径
                relative_path = f"/data/{config.UPLOAD_DIR}/{task_id}"
            
            # 确保路径使用正斜杠并以斜杠结尾

            if not relative_path.endswith("/"):
                relative_path += "/"
            
            result = {}
            # 遍历目录中的所有txt文件
            for filename in os.listdir(task.marked_images_path):
                if filename.endswith('.txt'):
                    file_path = os.path.join(task.marked_images_path, filename)
                    try:
                        # 获取不带扩展名的文件名
                        name_without_ext = os.path.splitext(filename)[0]
                        # 查找原始图片文件名
                        original_filename = image_name_map.get(name_without_ext)
                        
                        if original_filename:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # 使用相对路径作为键的前缀
                                result_key = f"{relative_path}{original_filename}"
                                result[result_key] = content
                        else:
                            logger.warning(f"找不到与打标文本 {filename} 对应的原始图片")
                    except Exception as e:
                        logger.error(f"读取文件 {file_path} 失败: {str(e)}")
                        if original_filename:
                            result_key = f"{relative_path}{original_filename}"
                            result[result_key] = f"读取失败: {str(e)}"
            
            return result
        except Exception as e:
            logger.error(f"获取打标文本失败: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def update_marked_text(db: Session, task_id: int, image_filename: str, content: str) -> Dict:
        """
        更新某张图片的打标文本
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            image_filename: 图片文件名或从/data开始的相对路径+文件名
            content: 新的打标文本内容
            
        Returns:
            包含操作结果的字典
        """
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"success": False, "message": f"任务 {task_id} 不存在"}
            
            if task.status not in [TaskStatus.MARKED, TaskStatus.TRAINING, TaskStatus.COMPLETED]:
                return {"success": False, "message": f"任务状态为 {task.status}，不允许编辑打标文本"}
            
            # 检查marked_images_path是否存在
            if not task.marked_images_path or not os.path.exists(task.marked_images_path):
                return {"success": False, "message": f"打标目录不存在: {task.marked_images_path}"}
            
            # 使用任务的marked_images_path作为打标目录
            marked_dir = task.marked_images_path
            
            # 处理可能是从/data开始的相对路径的情况
            original_filename = None
            
            # 如果是相对路径（以/data开头），需要提取实际的文件名
            if image_filename.startswith('/data/'):
                original_filename = os.path.basename(image_filename)
            else:
                # 直接使用传入的文件名
                image = next((img for img in task.images if img.filename == image_filename), None)
                if image:
                    original_filename = image_filename
            
            # 如果无法找到对应的原始文件名，返回错误
            if not original_filename:
                return {"success": False, "message": f"图片 {image_filename} 不属于该任务或路径无法识别"}
            
            # 获取不带扩展名的文件名
            name_without_ext = os.path.splitext(original_filename)[0]
            # 打标文本文件路径
            text_file_path = os.path.join(marked_dir, f"{name_without_ext}.txt")
            
            # 写入新的打标文本内容
            with open(text_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 记录日志
            task.add_log(f"更新了图片 {original_filename} 的打标文本", db=db)
            
            return {
                "success": True, 
                "message": "打标文本更新成功",
                "filename": original_filename,
                "original_path": image_filename,
                "text_path": text_file_path
            }
            
        except Exception as e:
            logger.error(f"更新打标文本失败: {str(e)}", exc_info=True)
            return {"success": False, "message": f"更新打标文本失败: {str(e)}"}
            
    @staticmethod
    def batch_update_marked_texts(db: Session, task_id: int, texts_map: Dict[str, str]) -> Dict:
        """
        批量更新多个图片的打标文本
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            texts_map: 从/data开始的相对路径+文件名到文本内容的映射字典
            
        Returns:
            包含操作结果的字典
        """
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"success": False, "message": f"任务 {task_id} 不存在"}
            
            if task.status not in [TaskStatus.MARKED, TaskStatus.TRAINING, TaskStatus.COMPLETED]:
                return {"success": False, "message": f"任务状态为 {task.status}，不允许编辑打标文本"}
            
            # 检查marked_images_path是否存在
            if not task.marked_images_path or not os.path.exists(task.marked_images_path):
                return {"success": False, "message": f"打标目录不存在: {task.marked_images_path}"}
            
            # 使用任务的marked_images_path作为打标目录
            marked_dir = task.marked_images_path
            
            results = {
                "success": True,
                "message": "批量更新打标文本完成",
                "updated": [],
                "failed": []
            }
            
            # 获取任务中所有图片的文件名和/data路径的映射
            image_name_map = {}
            marked_data_path = task.marked_images_path.replace(config.PROJECT_ROOT, "")
            # 确保路径使用正斜杠
            marked_data_path = marked_data_path.replace("\\", "/")
            if not marked_data_path.endswith("/"):
                marked_data_path += "/"
                
            for image in task.images:
                marked_path = f"{marked_data_path}{image.filename}"
                image_name_map[marked_path] = image.filename
            
            for path_filename, content in texts_map.items():
                try:
                    # 从路径中提取原始文件名
                    original_filename = None
                    
                    # 直接在映射中查找
                    if path_filename in image_name_map:
                        original_filename = image_name_map[path_filename]
                    
                    if not original_filename:
                        results["failed"].append({
                            "filename": path_filename,
                            "reason": f"无法匹配路径 {path_filename} 到任务中的图片"
                        })
                        continue
                    
                    # 获取不带扩展名的文件名
                    name_without_ext = os.path.splitext(original_filename)[0]
                    # 打标文本文件路径
                    text_file_path = os.path.join(marked_dir, f"{name_without_ext}.txt")
                    
                    # 写入新的打标文本内容
                    with open(text_file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    results["updated"].append({
                        "filename": original_filename,
                        "path": path_filename,
                        "text_path": text_file_path
                    })
                    
                except Exception as e:
                    logger.error(f"更新图片 {path_filename} 的打标文本失败: {str(e)}")
                    results["failed"].append({
                        "filename": path_filename,
                        "reason": str(e)
                    })
            
            # 记录日志
            if results["updated"]:
                updated_files = [item["filename"] for item in results["updated"]]
                task.add_log(f"批量更新了 {len(updated_files)} 个图片的打标文本: {', '.join(updated_files)}", db=db)
            
            # 如果全部失败，则整体标记为失败
            if not results["updated"] and results["failed"]:
                results["success"] = False
                results["message"] = "所有打标文本更新都失败了"
            
            return results
            
        except Exception as e:
            logger.error(f"批量更新打标文本失败: {str(e)}", exc_info=True)
            return {"success": False, "message": f"批量更新打标文本失败: {str(e)}"}

    @staticmethod
    def _process_training(task_id: int, asset_id: int):
        """处理训练任务"""
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                asset = db.query(Asset).filter(Asset.id == asset_id).first()

                if not task or not asset:
                    raise ValueError("任务或资产不存在")

                logger.info(f"开始处理训练任务 {task_id}")
                
                # 更新任务状态，记录开始处理训练
                task.update_status(TaskStatus.TRAINING, f'开始处理训练任务，使用资产: {asset.name}', db=db)

                # 去掉最后一个路径部分
                input_dir = os.path.dirname(task.marked_images_path)
                # 检查输入目录是否存在
                if not os.path.exists(input_dir):
                    raise ValueError(f"标记图片目录不存在: {input_dir}")
                output_dir = os.path.join(Config.OUTPUT_DIR, str(task_id))
                
                # 确保输出目录存在
                os.makedirs(output_dir, exist_ok=True)

                # 记录目录信息
                task.add_log(f'输入目录: {input_dir}', db=db)
                task.add_log(f'输出目录: {output_dir}', db=db)

                # 获取训练配置
                training_config = ConfigService.get_task_training_config(task.id)
                
                # 记录训练配置
                task.add_log(f'训练配置: {json.dumps(training_config, indent=2, ensure_ascii=False)}', db=db)
                
                handler = TrainRequestHandler(asset.ip,asset.lora_training.get('port',28000))
                
                # 记录请求准备信息
                task.add_log(f'准备发送训练请求: task_id={task_id}, asset_id={asset_id}, asset_ip={asset.ip}', db=db)
                
                try:
                    # 创建基础TrainConfig对象
                    train_config = TrainConfig(
                        train_data_dir=input_dir,
                        output_dir=output_dir,
                        output_name=task.name
                    )
                    
                    # 从训练配置中拷贝参数到train_config对象
                    if training_config and isinstance(training_config, dict):
                        copy_attributes(training_config, train_config)
                    
                    # 发送训练请求
                    logger.info(f"发送训练请求: task_id={task_id}, asset_id={asset_id}")
                    task_id_str = handler.train_request(train_config)
                    
                    if not task_id_str:
                        task.add_log('没有获取到有效的训练任务ID', db=db)
                        raise ValueError("创建训练任务失败，未获取到任务ID")
                    
                    # 记录成功获取task_id
                    task.add_log(f'训练任务创建成功，task_id={task_id_str}', db=db)
                    logger.info(f"训练任务 {task_id} 创建成功, task_id={task_id_str}")
                    
                    # 更新任务的prompt_id字段存储训练任务ID
                    task.prompt_id = task_id_str
                    db.commit()
                    logger.info(f"已更新任务 {task_id} 的 prompt_id 为训练任务ID")
                    
                    # 启动监控线程
                    return task_id_str
                    
                except Exception as req_error:
                    # 捕获请求异常，记录详细错误信息
                    error_detail = {
                        "message": str(req_error),
                        "type": type(req_error).__name__,
                        "traceback": str(traceback.format_exc())
                    }
                    error_json = json.dumps(error_detail, indent=2)
                    task.update_status(TaskStatus.ERROR, f'训练请求失败: {str(req_error)}', db=db)
                    task.add_log(error_json, db=db)
                    if task.training_asset:
                        task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                        db.commit()
                    # 重新抛出异常，让上层处理
                    raise ValueError(f"训练请求失败: {str(req_error)}")
                    
        except Exception as e:
            logger.error(f"训练任务 {task_id} 处理失败: {str(e)}", exc_info=True)
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
                    task.update_status(TaskStatus.ERROR, f'训练处理失败: {str(e)}', db=db)
                    task.add_log(error_json, db=db)
                    if task.training_asset:
                        task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                        db.commit()
            raise
            
    @staticmethod
    def _monitor_training_status(task_id: int, asset_id: int, training_task_id: str):
        """监控训练任务状态"""
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                asset = db.query(Asset).filter(Asset.id == asset_id).first()

                if not task or not asset:
                    raise ValueError("任务或资产不存在")
                
                # 记录开始监控
                task.add_log(f'开始监控训练任务状态, training_task_id={training_task_id}', db=db)

                handler = TrainRequestHandler(asset.ip,asset.lora_training.get('port',28000))
                
                poll_interval = ConfigService.get_value('train_poll_interval', 30)
                last_progress = 0
                error_count = 0
                
                while True:
                    try:
                        completed, success, task_info = handler.check_status(training_task_id)
                        logger.info(f"检查训练任务状态: {completed}, {success}, {task_info}")
                        
                        # 获取进度信息
                        current_progress = task_info.get("progress", 0)
                        status_message = task_info.get("message", "")
                        
                        with get_db() as complete_db:
                            task = complete_db.query(Task).filter(Task.id == task_id).first()
                            
                            # 可能在训练过程中取消了任务，不再继续监听
                            if task and task.status != TaskStatus.TRAINING:
                                logger.info("监听训练过程中任务被取消")
                                break
                                
                            # 更新进度
                            if task and current_progress != last_progress:
                                task.progress = current_progress
                                task.add_log(f'训练进度: {current_progress}%, {status_message}', db=complete_db)
                                last_progress = current_progress
                            
                            # 任务完成处理
                            if completed and task:
                                if success:
                                    task.update_status(TaskStatus.COMPLETED, '训练完成', db=complete_db)
                                    task.progress = 100
                                    task.add_log('训练任务成功完成', db=complete_db)
                                    
                                    # 记录输出文件路径
                                    output_dir = os.path.join(Config.OUTPUT_DIR, str(task_id))
                                    task.add_log(f'训练输出目录: {output_dir}', db=complete_db)
                                    
                                    # 尝试找到生成的Lora文件
                                    try:
                                        lora_files = []
                                        if os.path.exists(output_dir):
                                            for file in os.listdir(output_dir):
                                                if file.endswith('.safetensors') or file.endswith('.pt'):
                                                    lora_files.append(os.path.join(output_dir, file))
                                        
                                        if lora_files:
                                            task.add_log(f'生成的Lora文件: {", ".join(lora_files)}', db=complete_db)
                                    except Exception as e:
                                        logger.error(f"查找Lora文件失败: {str(e)}")
                                else:
                                    # 训练失败
                                    error_message = {
                                        "message": status_message,
                                        "details": task_info.get("details", {})
                                    }
                                    error_json = json.dumps(error_message, indent=2)
                                    task.update_status(
                                        TaskStatus.ERROR,
                                        f'训练失败: {status_message}',
                                        db=complete_db
                                    )
                                    task.add_log(error_json, db=complete_db)
                                
                                # 更新资产任务计数
                                if task.training_asset:
                                    task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                                    complete_db.commit()
                                break
                        
                        # 重置错误计数
                        error_count = 0
                        
                    except Exception as check_err:
                        # 捕获检查状态时的错误
                        error_count += 1
                        logger.error(f"检查训练状态时出错 ({error_count}/3): {str(check_err)}")
                        
                        with get_db() as err_db:
                            task = err_db.query(Task).filter(Task.id == task_id).first()
                            if task:
                                task.add_log(f'检查训练状态出错 ({error_count}/3): {str(check_err)}', db=err_db)
                            # 如果累计出错3次，停止监控并更新任务状态
                            if error_count >= 3:
                                task = err_db.query(Task).filter(Task.id == task_id).first()
                                if task:
                                    task.update_status(TaskStatus.ERROR, f'连续3次检查状态失败，停止监控: {str(check_err)}', db=err_db)
                                    if task.training_asset:
                                        task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                                        err_db.commit()
                                break
                    
                    time.sleep(poll_interval)

        except Exception as e:
            logger.error(f"监控训练任务状态失败: {str(e)}")
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
                    task.update_status(TaskStatus.ERROR, f'监控失败: {str(e)}', db=db)
                    task.add_log(error_json, db=db)
                    if task.training_asset:
                        task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                        db.commit() 