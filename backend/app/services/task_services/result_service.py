from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ...models.task import Task, TaskStatus, TaskExecutionHistory, TaskImage
from ...database import get_db
from ...utils.logger import setup_logger
from ...config import config, Config
from ...utils.train_handler import TrainRequestHandler
import os
import json
import re

logger = setup_logger('result_service')

class ResultService:
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
            from ...services.config_service import ConfigService
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
            handler = TrainRequestHandler(task.training_asset)
            
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
            "success": True,
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