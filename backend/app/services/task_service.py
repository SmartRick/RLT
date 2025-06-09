from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..services.config_service import ConfigService
from ..models.task import Task, TaskImage, TaskStatus, TaskStatusHistory, TaskStatusLog, TaskExecutionHistory
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
import re
from ..services.asset_service import AssetService
from ..utils.mark_handler import MarkConfig
from ..utils.file_handler import *
from ..services.common_service import CommonService
# 导入ComfyUIAPI
from task_scheduler.comfyui_api import ComfyUIAPI, ComfyUIConfig


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
            
            # 获取标记配置
            mark_config = ConfigService.get_task_mark_config(task_id)
            training_data_path = f"{mark_config.get('repeat_num',10)}_rick"
            # 生成唯一的打标路径
            marked_images_path = os.path.join(generate_unique_folder_path(Config.MARKED_DIR, task_id, 'mark'),training_data_path)
            task.marked_images_path = marked_images_path

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
                output_dir = task.marked_images_path
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
    def _generate_sample_prompts(task_id: int, training_config: Dict) -> str:
        """
        根据任务配置生成sample_prompts
        
        Args:
            task_id: 任务ID
            training_config: 训练配置
            
        Returns:
            生成的sample_prompts字符串
        """
        try:
            # 获取配置参数
            use_image_tags = training_config.get('use_image_tags', False)
            max_image_tags = int(training_config.get('max_image_tags', 5))
            positive_prompt = training_config.get('positive_prompt', '')
            negative_prompt = training_config.get('negative_prompt', 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts,signature, watermark, username, blurry')
            preview_width = training_config.get('preview_width', 512)
            preview_height = training_config.get('preview_height', 768)
            cfg_scale = training_config.get('cfg_scale', 7)
            steps = training_config.get('steps', 24)
            seed = training_config.get('seed', 1337)
            
            # 构建基本的负面提示词部分
            negative_part = f"--n {negative_prompt}"
            
            # 构建预览图参数部分
            params_part = f" --w {preview_width} --h {preview_height} --l {cfg_scale} --s {steps} --d {seed}"
            
            # 如果使用图片标签
            if use_image_tags:
                with get_db() as db:
                    # 获取任务的打标文本
                    marked_texts = TaskService.get_marked_texts(db, task_id)
                    
                    if not marked_texts:
                        # 如果没有打标文本，使用默认提示词
                        return f"(masterpiece, best quality:1.2), 1girl, solo, {negative_part}{params_part}"
                    
                    # 构建多行提示词
                    prompts = []
                    count = 0
                    
                    for _, text in marked_texts.items():
                        if count >= max_image_tags:
                            break
                        
                        # 提取文本的第一行作为提示词
                        first_line = text.strip().split('\n')[0] if text else ""
                        if first_line:
                            # 添加基本质量词
                            prompt = f"(masterpiece, best quality:1.2), {first_line}, {negative_part}{params_part}"
                            prompts.append(prompt)
                            count += 1
                    
                    # 如果没有有效的提示词，使用默认提示词
                    if not prompts:
                        return f"(masterpiece, best quality:1.2), 1girl, solo, {negative_part}{params_part}"
                    
                    # 返回多行提示词
                    return "\n".join(prompts)
            else:
                # 使用配置中的正向提示词
                return f"(masterpiece, best quality:1.2), {positive_prompt}, {negative_part}{params_part}"
        
        except Exception as e:
            logger.error(f"生成sample_prompts失败: {str(e)}", exc_info=True)
            # 返回一个默认值
            return "(masterpiece, best quality:1.2), 1girl, solo, --n lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts,signature, watermark, username, blurry --w 512 --h 768 --l 7 --s 24 --d 1337"

    @staticmethod
    def _prepare_training_execution_history(task_id: int, db: Session):
        """
        准备训练执行历史记录和相关配置
        
        Args:
            task_id: 任务ID
            db: 数据库会话
            
        Returns:
            Dictionary containing training configuration and output path
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")

        # 获取训练配置
        mark_config = ConfigService.get_task_mark_config(task_id)
        training_config = ConfigService.get_task_training_config(task_id)
        
        # 生成sample_prompts并更新到训练配置中
        training_config['sample_prompts'] = TaskService._generate_sample_prompts(task_id, training_config)
        
        # 移除业务参数，避免传递给训练服务
        business_params = ['use_image_tags', 'max_image_tags', 'positive_prompt', 
                            'negative_prompt', 'preview_width', 'preview_height', 
                            'cfg_scale', 'steps', 'seed']
        for param in business_params:
            if param in training_config:
                training_config.pop(param)
        
        # 生成唯一的训练输出路径
        training_output_path = generate_unique_folder_path(Config.OUTPUT_DIR, task_id, 'train')
        task.training_output_path = training_output_path
        
        # 创建执行历史记录
        execution_history = TaskExecutionHistory(
            task_id=task_id,
            status='RUNNING',
            mark_config=mark_config,
            training_config=training_config,
            marked_images_path=task.marked_images_path,
            training_output_path=training_output_path,
            description=f"训练开始于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        db.add(execution_history)
        db.commit()
        db.refresh(execution_history)
        
        # 记录历史ID到任务的prompt_id字段，方便后续更新
        task.execution_history_id = execution_history.id
        db.commit()
    
        return {
            "training_config": training_config,
            "training_output_path": training_output_path,
            "execution_history_id": execution_history.id
        }

    @staticmethod
    def start_training(db: Session, task_id: int) -> Optional[Dict]:
        """启动训练流程"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError("任务不存在")
            
            if task.status != TaskStatus.MARKED:
                raise ValueError(f"任务状态 {task.status} 不允许开始训练")

            # 只更新任务状态，不创建历史记录，历史记录将在_process_training中创建
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
                handler = TrainRequestHandler(
                    asset_ip=task.training_asset.ip,
                    training_port=task.training_asset.lora_training.get('port', 28000)
                )
                
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
                
                # 配置ComfyUI API客户端
                comfy_config = ComfyUIConfig(
                    host=f"http://{task.marking_asset.ip}",
                    port=task.marking_asset.ai_engine.get('port', 8188),
                    client_id="TASK_TERMINATOR"
                )
                api = ComfyUIAPI(comfy_config)
                
                # 首先获取队列信息，检查任务是否在运行状态
                try:
                    queue_info = api.get_queue()
                    
                    # 检查任务是否在运行队列中
                    task_running = False
                    if "queue_running" in queue_info and queue_info["queue_running"]:
                        for item in queue_info["queue_running"]:
                            if len(item) > 1 and item[1] == task.prompt_id:
                                task_running = True
                                break
                    
                    # 检查任务是否在等待队列中
                    task_pending = False
                    if "queue_pending" in queue_info and queue_info["queue_pending"]:
                        for item in queue_info["queue_pending"]:
                            if len(item) > 1 and item[1] == task.prompt_id:
                                task_pending = True
                                break
                    
                    # 只有当任务确实在运行或等待时才尝试终止
                    if task_running or task_pending:
                        interrupt_result = api.interrupt()
                        cancel_success = interrupt_result.get("success", False)
                        
                        if cancel_success:
                            logger.info(f"成功终止打标任务 {task_id}")
                            cancel_message = "打标任务已成功终止并回滚到NEW状态"
                        else:
                            logger.warning(f"终止打标任务 {task_id} 失败: {interrupt_result}")
                            cancel_message = "无法通过API终止打标任务，但已回滚任务状态"
                    else:
                        logger.info(f"打标任务 {task_id} 不在队列中，可能已经完成或被终止")
                        cancel_success = True
                        cancel_message = "打标任务不在执行队列中，已回滚任务状态"
                except Exception as e:
                    logger.error(f"获取队列信息或终止打标任务时出错: {str(e)}")
                    cancel_message = f"终止打标任务时出错: {str(e)}，但已回滚任务状态"
            
            # 回滚任务状态
            rollback_success = TaskService._rollback_task_state(
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
            rollback_success = TaskService._rollback_task_state(
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

                # 准备训练执行历史记录和配置
                execution_result = TaskService._prepare_training_execution_history(task_id, db)
                training_config = execution_result["training_config"]
                output_dir = execution_result["training_output_path"]
                
                # 记录执行历史ID
                task.execution_history_id = execution_result["execution_history_id"]
                db.commit()
                
                # 去掉最后一个路径部分
                input_dir = os.path.dirname(task.marked_images_path)
                # 检查输入目录是否存在
                if not os.path.exists(input_dir):
                    raise ValueError(f"标记图片目录不存在: {input_dir}")
                
                # 确保输出目录存在
                os.makedirs(output_dir, exist_ok=True)

                # 记录目录信息
                task.add_log(f'输入目录: {input_dir}', db=db)
                task.add_log(f'输出目录: {output_dir}', db=db)

                # 记录训练配置
                task.add_log(f'训练配置: {json.dumps(training_config, indent=2, ensure_ascii=False)}', db=db)
                
                # 更新训练配置中的输入输出路径
                training_config['train_data_dir'] = input_dir
                training_config['output_dir'] = output_dir
                
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
                max_error_retries = 10  # 最大错误重试次数
                
                while True:
                    try:
                        # 获取训练状态
                        status = handler.check_status(training_task_id)
                        logger.info(f"检查训练任务状态: {status}")
                        
                        # 判断任务状态
                        is_completed = False
                        is_success = False
                        
                        if status == "FINISHED":
                            is_completed = True
                            is_success = True
                        elif status in ["FAILED", "TERMINATED"]:
                            is_completed = True
                            is_success = False
                        
                        with get_db() as complete_db:
                            task = complete_db.query(Task).filter(Task.id == task_id).first()
                            # 可能在训练过程中取消了任务，不再继续监听
                            if task and task.status != TaskStatus.TRAINING:
                                logger.info("监听训练过程中任务被取消")
                                
                                # 更新执行历史记录状态为ERROR
                                if task.execution_history_id:
                                    execution_history = complete_db.query(TaskExecutionHistory).filter(
                                        TaskExecutionHistory.id == task.execution_history_id
                                    ).first()
                                    if execution_history:
                                        execution_history.status = 'ERROR'
                                        execution_history.end_time = datetime.now()
                                        execution_history.description += f"\n任务被取消于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                        complete_db.commit()
                                
                                break
                                
                            # 更新进度

                            
                            # 任务完成处理
                            if is_completed and task:
                                # 获取执行历史记录
                                execution_history = None
                                if task.execution_history_id:
                                    execution_history = complete_db.query(TaskExecutionHistory).filter(
                                        TaskExecutionHistory.id == task.execution_history_id
                                    ).first()
                                
                                if is_success:
                                    task.update_status(TaskStatus.COMPLETED, '训练完成', db=complete_db)
                                    task.progress = 100
                                    task.add_log('训练任务成功完成', db=complete_db)
                                    
                                    # 记录输出文件路径
                                    output_dir = task.training_output_path
                                    task.add_log(f'训练输出目录: {output_dir}', db=complete_db)
                                    
                                    # 获取训练结果
                                    training_results = TaskService.get_training_results(task_id)
                                    
                                    # 获取训练loss数据
                                    try:
                                        loss_result = TaskService.get_training_loss_data(task_id)
                                        if loss_result and loss_result.get('success') and loss_result.get('series'):
                                            loss_data = {'series': loss_result.get('series')}
                                        else:
                                            loss_data = None
                                    except Exception as loss_err:
                                        logger.error(f"获取训练loss数据失败: {str(loss_err)}")
                                        loss_data = None
                                    
                                    # 如果有执行历史记录，更新其状态和结果
                                    if execution_history:
                                        execution_history.status = 'COMPLETED'
                                        execution_history.end_time = datetime.now()
                                        execution_history.training_results = training_results
                                        # 保存loss数据
                                        if loss_data:
                                            execution_history.loss_data = loss_data
                                        execution_history.description += f"\n训练成功完成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                        complete_db.commit()
                                    
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
                                    
                                    task.update_status(
                                        TaskStatus.ERROR,
                                        f'训练失败，任务状态为: {status}',
                                        db=complete_db
                                    )
                                    
                                    # 如果有执行历史记录，更新其状态为ERROR
                                    if execution_history:
                                        execution_history.status = 'ERROR'
                                        execution_history.end_time = datetime.now()
                                        execution_history.description += f"\n训练失败于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {message}"
                                        complete_db.commit()
                                
                                # 更新资产任务计数
                                if task.training_asset:
                                    task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                                    complete_db.commit()
                                break
                        
                        # 重置错误计数
                        if error_count > 0:
                            logger.info(f"从错误状态恢复，重置错误计数器。之前错误次数: {error_count}")
                        error_count = 0
                        
                    except Exception as check_err:
                        # 捕获检查状态时的错误
                        error_count += 1
                        
                        # 根据错误次数决定等待时间
                        if error_count <= max_error_retries // 2:  # 前一半错误使用较短的等待
                            wait_time = 5  # 短等待时间
                            logger.error(f"检查训练状态时出错 ({error_count}/{max_error_retries}): {str(check_err)}, 将在{wait_time}秒后重试")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"检查训练状态时出错 ({error_count}/{max_error_retries}): {str(check_err)}, 将继续使用正常轮询间隔")
                        
                        with get_db() as err_db:
                            task = err_db.query(Task).filter(Task.id == task_id).first()
                            if task:
                                task.add_log(f'检查任务状态出错 ({error_count}/{max_error_retries}): {str(check_err)}', db=err_db)
                            
                            # 如果累计出错达到最大重试次数，停止监控并更新任务状态
                            if error_count >= max_error_retries:
                                task = err_db.query(Task).filter(Task.id == task_id).first()
                                if task:
                                    task.update_status(
                                        TaskStatus.ERROR, 
                                        f'连续{max_error_retries}次检查状态失败，停止监控: {str(check_err)}', 
                                        db=err_db
                                    )
                                    if task.training_asset:
                                        task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                                        err_db.commit()
                                break
                    
                        # 如果错误次数未达到阈值，继续正常轮询
                        if error_count < max_error_retries:
                            continue
                    
                    # 正常情况下等待轮询间隔
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

    @staticmethod
    def get_training_results(task_id: int) -> Dict:
        """
        获取训练结果，包括模型文件和预览图的相对路径
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含训练结果的字典
        """
        with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    return {"success": False, "message": f"任务 {task_id} 不存在"}
                
                # 使用任务指定的训练输出目录
                if not task.training_output_path or not os.path.exists(task.training_output_path):
                    return {"success": False, "message": f"训练输出目录不存在: {task.training_output_path}"}
                    
                output_dir = task.training_output_path
                    
                # 获取相对路径前缀（从/data开始）
                output_data_path = output_dir.replace(config.PROJECT_ROOT, "")
                output_data_path = output_data_path.replace("\\", "/")
                if not output_data_path.startswith("/data"):
                    output_data_path = f"/data{output_data_path}"
                if not output_data_path.endswith("/"):
                    output_data_path += "/"
                    
                # 预先加载sample目录中的所有预览图及其修改时间
                sample_dir = os.path.join(output_dir, "sample")
                preview_images = {}
                latest_preview = None
                latest_time = 0
                
                if os.path.exists(sample_dir) and os.path.isdir(sample_dir):
                    # 使用一次循环处理所有预览图
                    for img_file in os.listdir(sample_dir):
                        if img_file.endswith('.png'):
                            img_path = os.path.join(sample_dir, img_file)
                            mod_time = os.path.getmtime(img_path)
                            
                            # 记录最新的预览图
                            if mod_time > latest_time:
                                latest_time = mod_time
                                latest_preview = img_file
                            
                            # 尝试从文件名中提取epoch数字
                            
                            epoch_match = re.search(r'_e(\d{6})_', img_file)
                            if epoch_match:
                                epoch_num = epoch_match.group(1)
                                preview_images[epoch_num] = img_file
                
                # 查找所有模型文件
                models = []
                for filename in os.listdir(output_dir):
                    file_path = os.path.join(output_dir, filename)
                    if os.path.isfile(file_path) and (filename.endswith('.safetensors') or filename.endswith('.pt')):
                        # 获取模型名称（不含扩展名）
                        model_name_base = os.path.splitext(filename)[0]
                        
                        # 初始化预览图为空
                        preview_image = ''
                        
                        # 尝试从模型名称中提取轮次编号
                        epoch_match = re.search(r'-(\d{6})', model_name_base)
                        
                        if epoch_match:
                            # 如果是有轮次的模型，查找对应的预览图
                            epoch_num = epoch_match.group(1)
                            if epoch_num in preview_images:
                                preview_image = f"{output_data_path}sample/{preview_images[epoch_num]}"
                        else:
                            # 如果是最后一轮模型（没有轮次数字），使用最新的预览图
                            if latest_preview:
                                preview_image = f"{output_data_path}sample/{latest_preview}"
                        
                        # 构建模型信息
                        model_info = {
                            "name": filename,
                            "path": f"{output_data_path}{filename}",
                            "preview_image": preview_image,
                            "size": os.path.getsize(file_path),
                            "modified_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        }
                        models.append(model_info)
                
                return {
                    "task_id": task_id,
                    "task_name": task.name,
                    "output_dir": output_data_path,
                    "models": models,
                    "total_models": len(models)
                }
            
    @staticmethod
    def get_training_loss_data(task_id: int, history_id: int = None) -> Dict:
        """
        获取训练loss曲线数据并计算训练进度
        
        Args:
            task_id: 任务ID
            history_id: 历史记录ID（可选）
            
        Returns:
            包含loss曲线数据和训练进度的字典
        """
        with get_db() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"任务 {task_id} 不存在")
            
            # 检查任务状态
            if task.status not in [TaskStatus.TRAINING, TaskStatus.COMPLETED]:
                raise ValueError(f"任务状态 {task.status} 不支持获取训练数据")
            
            # 检查是否有训练资产和prompt_id
            if not task.training_asset or not task.prompt_id:
                raise ValueError("任务没有关联的训练资产或训练ID")
        
            # 获取训练配置（从执行历史记录中获取）
            training_config = None
            
            # 先确定要使用的历史记录ID
            history_id_to_use = history_id if history_id else task.execution_history_id
            
            execution_history = db.query(TaskExecutionHistory).filter(
                TaskExecutionHistory.id == history_id_to_use
            ).first()
            
            if execution_history and execution_history.training_config:
                training_config = execution_history.training_config
                logger.info(f"从执行历史记录中获取训练配置: {execution_history.id}")
            
            # 如果从执行历史记录中没有获取到配置，则回退到使用ConfigService
            if not training_config:
                training_config = ConfigService.get_task_training_config(task_id)
                logger.info("从ConfigService获取训练配置")
            
            if not training_config:
                raise ValueError("无法获取训练配置")
            
            # 计算总步数
            image_count = db.query(TaskImage).filter(TaskImage.task_id == task_id).count()
            repeat_num = training_config.get('repeat_num', 10)  # 默认重复次数为10
            max_epochs = training_config.get('max_train_epochs', 10)  # 默认训练轮次为10
            train_batch_size = training_config.get('train_batch_size', 1)  # 默认训练batch size为1
            total_steps = image_count * repeat_num * max_epochs / train_batch_size
            
            # 创建训练处理器并获取loss数据
            handler = TrainRequestHandler(
                asset_ip=task.training_asset.ip,
                training_port=task.training_asset.lora_training.get('port', 28000)
            )
            
            loss_data = handler.get_training_loss_data(task.prompt_id)
            
            # 如果获取失败，抛出异常
            if not loss_data:
                raise RuntimeError("获取训练loss数据失败")
            
            # 计算当前步数和进度
            current_step = 0
            series_data = None
            
            if loss_data and isinstance(loss_data, list) and len(loss_data) > 0:
                run_to_series = loss_data[0].get('runToSeries', {})
                
                # 由于我们已经在TrainRequestHandler中匹配了正确的key
                # 所以这里run_to_series应该只有一个元素，直接获取其值
                if run_to_series:
                    # 获取第一个(唯一的)key对应的数据
                    first_key = next(iter(run_to_series))
                    series_data = run_to_series[first_key]
                    
                    # 如果找到了数据系列，获取最后一个数据点的步数
                    if series_data and len(series_data) > 0:
                        current_step = series_data[-1].get('step', 0)
                    else:
                        logger.warning(f"训练数据系列为空")
                else:
                    logger.warning(f"未找到任何训练数据系列")
                    raise ValueError("未找到任何训练数据系列")
            
            # 计算进度百分比
            progress = min(100, int((current_step / total_steps) * 100)) if total_steps > 0 else 0
            
            result = {
                "series": series_data,  # 返回匹配到的数据系列
                "training_progress": {
                    "current_step": current_step,
                    "total_steps": total_steps,
                    "progress_percent": progress,
                    "image_count": image_count,
                    "repeat_num": repeat_num,
                    "max_epochs": max_epochs
                },
                "source": "live"
            }
            
            # 如果任务有执行历史记录ID，保存loss数据到历史记录
            if task.execution_history_id:
                execution_history = db.query(TaskExecutionHistory).filter(
                    TaskExecutionHistory.id == task.execution_history_id
                ).first()
                
                if execution_history:
                    execution_history.loss_data = {"series": series_data}
                    db.commit()
            
            return result

    @staticmethod
    def get_execution_history(db: Session, task_id: int) -> List[Dict]:
        """
        获取任务的执行历史记录列表
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            
        Returns:
            执行历史记录列表
        """
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return []
            
            # 获取所有执行历史记录
            history_records = db.query(TaskExecutionHistory).filter(
                TaskExecutionHistory.task_id == task_id
            ).order_by(TaskExecutionHistory.start_time.desc()).all()
            
            return [record.to_dict() for record in history_records]
            
        except Exception as e:
            logger.error(f"获取执行历史记录失败: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def update_execution_history_result(db: Session, execution_history_id: int, results: Dict, loss_data: Dict = None, status: str = 'COMPLETED') -> bool:
        """
        更新执行历史记录的结果
        
        Args:
            db: 数据库会话
            execution_history_id: 执行历史记录ID
            results: 结果数据
            loss_data: loss数据
            status: 状态（COMPLETED或ERROR）
            
        Returns:
            是否更新成功
        """
        try:
            execution_history = db.query(TaskExecutionHistory).filter(TaskExecutionHistory.id == execution_history_id).first()
            if not execution_history:
                return False
            
            execution_history.training_results = results
            
            # 如果提供了loss数据，更新loss_data字段
            if loss_data:
                execution_history.loss_data = loss_data
            
            execution_history.status = status
            execution_history.end_time = datetime.now()
            
            if status == 'COMPLETED':
                execution_history.description += f"\n结果更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                execution_history.description += f"\n失败状态更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新执行历史记录结果失败: {str(e)}", exc_info=True)
            db.rollback()
            return False