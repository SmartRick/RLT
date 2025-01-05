from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile, HTTPException
import os
import shutil
import subprocess
import paramiko

from ..models.training import TrainingMaterial, TrainingTask
from ..models.asset import Asset
from ..schemas.training import (
    TrainingMaterialCreate,
    TrainingMaterialUpdate,
    TrainingTaskCreate,
    TrainingTaskUpdate
)
from ..config import settings, config
from ..utils.ssh import execute_command
from ..utils.logger import setup_logger
from ..middleware.error_handler import ServiceError
from .task_service import TaskService

logger = setup_logger('training_service')

# 训练素材相关服务
async def create_material(db: Session, material: TrainingMaterialCreate) -> TrainingMaterial:
    db_material = TrainingMaterial(
        folder_name=material.folder_name,
        source_path=material.source_path,
        status="UPLOADED",
        metadata=material.metadata,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

def get_materials(db: Session, skip: int = 0, limit: int = 100) -> List[TrainingMaterial]:
    return db.query(TrainingMaterial).offset(skip).limit(limit).all()

def get_material(db: Session, material_id: int) -> Optional[TrainingMaterial]:
    return db.query(TrainingMaterial).filter(TrainingMaterial.id == material_id).first()

def update_material(
    db: Session, 
    material_id: int, 
    material: TrainingMaterialUpdate
) -> Optional[TrainingMaterial]:
    db_material = get_material(db, material_id)
    if not db_material:
        return None
        
    update_data = material.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_material, field, value)
    
    db_material.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_material)
    return db_material

# 训练任务相关服务
def create_task(db: Session, task: TrainingTaskCreate) -> TrainingTask:
    # 验证素材和节点是否存在
    material = get_material(db, task.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Training material not found")
        
    node = db.query(Asset).filter(Asset.id == task.node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Training node not found")
    
    db_task = TrainingTask(
        material_id=task.material_id,
        node_id=task.node_id,
        status="PENDING",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 异步启动训练任务
    # TODO: 实现异步任务处理
    
    return db_task

def get_tasks(db: Session, skip: int = 0, limit: int = 100) -> List[TrainingTask]:
    return db.query(TrainingTask).offset(skip).limit(limit).all()

def get_task(db: Session, task_id: int) -> Optional[TrainingTask]:
    return db.query(TrainingTask).filter(TrainingTask.id == task_id).first()

def update_task(
    db: Session, 
    task_id: int, 
    task: TrainingTaskUpdate
) -> Optional[TrainingTask]:
    db_task = get_task(db, task_id)
    if not db_task:
        return None
        
    update_data = task.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task

# 文件上传服务
async def upload_material_files(
    db: Session, 
    material_id: int, 
    files: List[UploadFile]
) -> dict:
    material = get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # 确保目标目录存在
    upload_dir = os.path.join(settings.SOURCE_DIR, material.folder_name)
    os.makedirs(upload_dir, exist_ok=True)
    
    uploaded_files = []
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(file.filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload {file.filename}: {str(e)}")
    
    return {
        "message": "Files uploaded successfully",
        "material_id": material_id,
        "uploaded_files": uploaded_files
    } 

class TrainingService:
    @staticmethod
    def start_training(task_id: str) -> bool:
        """启动训练任务"""
        try:
            # 获取任务信息
            task = TaskService.get_task(task_id)
            if not task:
                raise ServiceError(f"Task {task_id} not found")
            
            # 检查任务状态
            if task['status'] not in ['PENDING', 'FAILED']:
                raise ServiceError(f"Task {task_id} cannot be started in {task['status']} status")
            
            # 更新任务状态
            TaskService.update_task(task_id, {'status': 'DOWNLOADING'})
            
            # 下载训练素材
            TrainingService._download_materials(task)
            
            # 开始训练
            TrainingService._start_training_process(task)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start training for task {task_id}: {str(e)}")
            TaskService.update_task(task_id, {
                'status': 'FAILED',
                'error': str(e)
            })
            return False

    @staticmethod
    def stop_training(task_id: str) -> bool:
        """停止训练任务"""
        try:
            task = TaskService.get_task(task_id)
            if not task:
                raise ServiceError(f"Task {task_id} not found")
            
            if task['status'] not in ['TRAINING', 'DOWNLOADING']:
                raise ServiceError(f"Task {task_id} cannot be stopped in {task['status']} status")
            
            # 停止训练进程
            TrainingService._stop_training_process(task)
            
            # 更新任务状态
            TaskService.update_task(task_id, {
                'status': 'STOPPED',
                'updated_at': datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop training for task {task_id}: {str(e)}")
            return False

    @staticmethod
    def get_training_status(task_id: str) -> Optional[Dict]:
        """获取训练状态"""
        try:
            task = TaskService.get_task(task_id)
            if not task:
                return None
            
            # 如果任务正在训练，获取实时进度
            if task['status'] == 'TRAINING':
                progress = TrainingService._get_training_progress(task)
                task.update(progress)
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to get training status for task {task_id}: {str(e)}")
            return None

    @staticmethod
    def _download_materials(task: Dict) -> None:
        """下载训练素材"""
        try:
            # 创建SSH客户端
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接远程服务器
            ssh.connect(
                hostname=config.DEFAULT_CONFIG['ssh_host'],
                port=config.DEFAULT_CONFIG['ssh_port'],
                username=config.DEFAULT_CONFIG['ssh_username'],
                key_filename=os.path.expanduser(config.DEFAULT_CONFIG['ssh_key_path'])
            )
            
            # 执行下载命令
            source_path = f"{config.DEFAULT_CONFIG['mark_pan_dir']}/{task['folder_name']}"
            dest_path = f"{config.DEFAULT_CONFIG['source_dir']}/{task['folder_name']}"
            
            command = f"rsync -av {source_path}/ {dest_path}/"
            stdin, stdout, stderr = ssh.exec_command(command)
            
            # 检查执行结果
            if stderr.channel.recv_exit_status() != 0:
                error = stderr.read().decode()
                raise ServiceError(f"Download failed: {error}")
            
            ssh.close()
            
        except Exception as e:
            raise ServiceError(f"Failed to download materials: {str(e)}")

    @staticmethod
    def _start_training_process(task: Dict) -> None:
        """启动训练进程"""
        try:
            # 准备训练命令
            train_script = os.path.join(config.PROJECT_ROOT, 'scripts', 'train.py')
            output_dir = os.path.join(config.DEFAULT_CONFIG['lora_output_path'], task['folder_name'])
            
            command = [
                'python',
                train_script,
                '--pretrained_model_name_or_path=runwayml/stable-diffusion-v1-5',
                f'--train_data_dir={config.DEFAULT_CONFIG["source_dir"]}/{task["folder_name"]}',
                f'--output_dir={output_dir}',
                '--learning_rate=1e-4',
                '--max_train_steps=1000',
                '--save_steps=100'
            ]
            
            # 启动训练进程
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # 更新任务状态
            TaskService.update_task(task['id'], {
                'status': 'TRAINING',
                'process_id': process.pid,
                'started_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            raise ServiceError(f"Failed to start training process: {str(e)}")

    @staticmethod
    def _stop_training_process(task: Dict) -> None:
        """停止训练进程"""
        try:
            if task.get('process_id'):
                os.kill(task['process_id'], 9)
                
        except Exception as e:
            raise ServiceError(f"Failed to stop training process: {str(e)}")

    @staticmethod
    def _get_training_progress(task: Dict) -> Dict:
        """获取训练进度"""
        try:
            # 读取训练日志获取进度
            log_file = os.path.join(config.LOGS_DIR, f'task_{task["id"]}.log')
            if not os.path.exists(log_file):
                return {'progress': 0}
                
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            # 解析最后一行获取进度
            if lines:
                last_line = lines[-1]
                if 'Step' in last_line:
                    current_step = int(last_line.split('Step')[1].split('/')[0])
                    total_steps = 1000  # 从配置获取
                    return {
                        'progress': round(current_step / total_steps * 100, 2),
                        'current_step': current_step,
                        'total_steps': total_steps
                    }
                    
            return {'progress': 0}
            
        except Exception as e:
            logger.error(f"Failed to get training progress: {str(e)}")
            return {'progress': 0} 