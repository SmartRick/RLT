from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ...models.task import Task, TaskStatus, TaskExecutionHistory
from ...models.asset import Asset
from ...database import get_db
from ...utils.logger import setup_logger
from ...services.config_service import ConfigService
from ...utils.file_handler import generate_unique_folder_path
from ...utils.train_handler import TrainRequestHandler, TrainConfig
from ...utils.common import copy_attributes
from ...utils.ssh import upload_directory, download_directory
from ...services.asset_service import AssetService
from ...config import Config
import json
import traceback
import os
import time
import re

logger = setup_logger('training_service')

class TrainingService:
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
    def start_training(db: Session, task_id: int) -> Optional[Dict]:
        """启动训练流程"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError("任务不存在")
            
            # 检查当前状态
            if task.status == TaskStatus.TRAINING:
                # 如果任务已经是训练状态，检查是否已分配资产
                if task.training_asset_id:
                    # 已经分配了资产，说明训练已经开始，不需要重复处理
                    return {
                        'warning': "任务已经在训练中",
                        'task': task.to_dict()
                    }
                # 如果是TRAINING状态但没有分配资产，说明任务在队列中等待处理，不需要操作
                return {
                    'info': "任务正在等待分配训练资产",
                    'task': task.to_dict()
                }
            elif task.status != TaskStatus.MARKED:
                # 非法状态转换
                raise ValueError(f"任务状态 {task.status} 不允许开始训练")
            
            # 更新任务状态为TRAINING，但不分配资产，由调度器处理
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
                    from ...services.task_services.result_service import ResultService
                    # 获取任务的打标文本
                    marked_texts = ResultService.get_marked_texts(db, task_id)
                    
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
        training_config['sample_prompts'] = TrainingService._generate_sample_prompts(task_id, training_config)
        
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
                execution_result = TrainingService._prepare_training_execution_history(task_id, db)
                training_config = execution_result["training_config"]
                output_dir = execution_result["training_output_path"]
                
                # 记录执行历史ID
                task.execution_history_id = execution_result["execution_history_id"]
                db.commit()
                
                # 准备输入输出目录
                input_dir = task.marked_images_path
                output_dir = execution_result["training_output_path"]
                
                # 检查输入目录是否存在
                if not os.path.exists(input_dir):
                    raise ValueError(f"标记图片目录不存在: {input_dir}")
                
                # 确保输出目录存在
                os.makedirs(output_dir, exist_ok=True)

                # 记录目录信息
                task.add_log(f'输入目录: {input_dir}', db=db)
                task.add_log(f'输出目录: {output_dir}', db=db)

                # 定义远程目录路径
                # 如果任务有打标资产，并且mark_config中有remote_output_dir，则使用该路径作为远程输入目录
                remote_input_dir = None
                if task.marking_asset and task.mark_config and task.mark_config.get('remote_output_dir'):
                    remote_input_dir = task.mark_config['remote_output_dir']
                    task.add_log(f'使用打标任务的远程输出路径作为训练输入: {remote_input_dir}', db=db)
                else:
                    # 如果没有打标资产或没有保存remote_output_dir，使用默认路径
                    output_suffix = task.marked_images_path.replace(Config.MARKED_DIR, '').lstrip('/')
                    remote_input_dir = f"{Config.REMOTE_MARKED_DIR}/{output_suffix}"
                    task.add_log(f'使用默认远程输入路径: {remote_input_dir}', db=db)
                
                # 定义训练输出目录
                output_suffix = output_dir.replace(Config.OUTPUT_DIR, '').lstrip('/')
                remote_output_dir = f"{Config.REMOTE_OUTPUT_DIR}/{output_suffix}"
                
                # 将远程输出路径保存到任务的training_config配置中
                if not task.training_config:
                    task.training_config = {}
                task.training_config['remote_output_dir'] = remote_output_dir
                db.commit()
                
                # 如果不是本地资产，需要同步文件
                if not asset.is_local:
                    task.add_log('资产不是本地资产，需要同步文件...', db=db)
                    
                    # 检查是否需要同步标记结果（如果训练和打标资产不同）
                    if not task.marking_asset or task.marking_asset_id != asset_id:
                        task.add_log('训练和打标资产不同，需要同步打标结果到训练资产...', db=db)
                        
                        # 上传打标结果到训练资产
                        success, message = upload_directory(asset, input_dir, remote_input_dir)
                        if not success:
                            raise ValueError(f"上传打标结果失败: {message}")
                        
                        task.add_log('打标结果上传成功', db=db)
                    else:
                        task.add_log('训练和打标使用相同资产，无需同步打标结果', db=db)
                    
                    # 更新输入目录为远程目录
                    input_dir = remote_input_dir
                
                # 更新训练配置中的输入输出路径
                training_config['train_data_dir'] = input_dir
                training_config['output_dir'] = remote_output_dir if not asset.is_local else output_dir
                
                # 记录训练配置
                task.add_log(f'训练配置: {json.dumps(training_config, indent=2, ensure_ascii=False)}', db=db)
                
                # 创建训练处理器，直接传入资产对象
                handler = TrainRequestHandler(asset)
                
                # 记录请求准备信息
                task.add_log(f'准备发送训练请求: task_id={task_id}, asset_id={asset_id}, asset_ip={asset.ip}', db=db)
                
                try:
                    # 创建基础TrainConfig对象
                    train_config = TrainConfig(
                        train_data_dir=input_dir,
                        output_dir=training_config['output_dir'],
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
                    
                    # 更新任务的prompt_id字段存储训练任务ID
                    task.prompt_id = task_id_str
                    db.commit()
                    
                    # 返回训练任务ID
                    return task_id_str
                    
                except Exception as req_error:
                    # 处理请求异常
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
                    raise ValueError(f"训练请求失败: {str(req_error)}")
                    
        except Exception as e:
            logger.error(f"训练任务 {task_id} 处理失败: {str(e)}", exc_info=True)
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.update_status(TaskStatus.ERROR, f'训练处理失败: {str(e)}', db=db)
                    task.add_log(json.dumps({
                        "message": str(e),
                        "type": type(e).__name__,
                        "traceback": str(traceback.format_exc())
                    }, indent=2), db=db)
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
                
                # 创建训练处理器，直接传入资产对象
                handler = TrainRequestHandler(asset)
                
                poll_interval = ConfigService.get_value('train_poll_interval', 30)
                error_count = 0
                max_error_retries = 10
                
                while True:
                    try:
                        # 获取训练状态
                        training_config = ConfigService.get_task_training_config(task_id)
                        status = handler.check_status(training_task_id, training_config)
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
                            # 检查任务是否被取消
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
                            
                            # 任务完成处理
                            if is_completed and task:
                                # 获取执行历史记录
                                execution_history = None
                                if task.execution_history_id:
                                    execution_history = complete_db.query(TaskExecutionHistory).filter(
                                        TaskExecutionHistory.id == task.execution_history_id
                                    ).first()
                                
                                if is_success:
                                    # 如果是非本地资产，需要下载训练结果
                                    if not asset.is_local and task.training_config and task.training_config.get('remote_output_dir'):
                                        task.add_log('训练完成，开始从远程服务器下载结果...', db=complete_db)
                                        
                                        # 下载远程输出目录到本地
                                        success, message = download_directory(
                                            asset, 
                                            task.training_config['remote_output_dir'], 
                                            task.training_output_path
                                        )
                                        
                                        if not success:
                                            task.add_log(f'下载结果失败: {message}', db=complete_db)
                                            task.update_status(TaskStatus.ERROR, f'下载训练结果失败: {message}', db=complete_db)
                                            break
                                        
                                        task.add_log('训练结果下载成功', db=complete_db)
                                    
                                    # 更新任务状态为完成
                                    task.update_status(TaskStatus.COMPLETED, '训练完成', db=complete_db)
                                    task.progress = 100
                                    task.add_log('训练任务成功完成', db=complete_db)
                                    
                                    # 记录输出文件路径
                                    output_dir = task.training_output_path
                                    task.add_log(f'训练输出目录: {output_dir}', db=complete_db)
                                    
                                    # 获取训练结果
                                    from ...services.task_services.result_service import ResultService
                                    training_results = ResultService.get_training_results(task_id)
                                    
                                    # 获取训练loss数据
                                    try:
                                        loss_result = ResultService.get_training_loss_data(task_id)
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
                                else:
                                    # 处理训练失败情况
                                    task.update_status(
                                        TaskStatus.ERROR,
                                        f'训练失败，任务状态为: {status}',
                                        db=complete_db
                                    )
                                    
                                    # 更新执行历史记录状态
                                    if execution_history:
                                        execution_history.status = 'ERROR'
                                        execution_history.end_time = datetime.now()
                                        execution_history.description += f"\n训练失败于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {status}"
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
                        # 处理检查状态时的错误
                        error_count += 1
                        
                        # 根据错误次数决定等待时间
                        wait_time = 5 if error_count <= max_error_retries // 2 else poll_interval
                        logger.error(f"检查训练状态时出错 ({error_count}/{max_error_retries}): {str(check_err)}, 将在{wait_time}秒后重试")
                        
                        with get_db() as err_db:
                            task = err_db.query(Task).filter(Task.id == task_id).first()
                            if task:
                                task.add_log(f'检查任务状态出错 ({error_count}/{max_error_retries}): {str(check_err)}', db=err_db)
                            
                            # 如果错误次数达到上限，停止监控
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
                        
                        # 等待一段时间后重试
                        time.sleep(wait_time)
                        continue
                
                    # 正常轮询间隔
                    time.sleep(poll_interval)

        except Exception as e:
            # 处理整体监控异常
            logger.error(f"监控训练任务状态失败: {str(e)}")
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.update_status(TaskStatus.ERROR, f'监控失败: {str(e)}', db=db)
                    task.add_log(json.dumps({
                        "message": str(e),
                        "type": type(e).__name__,
                        "traceback": str(traceback.format_exc())
                    }, indent=2), db=db)
                    if task.training_asset:
                        task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                        db.commit() 