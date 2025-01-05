from datetime import datetime
from typing import Dict, List, Optional
import os
import subprocess
import paramiko
from ..models.training import TrainingMaterial, TrainingTask
from ..config import config  # 只导入 config
from ..utils.logger import setup_logger
from ..utils.file_handler import load_json, save_json
from ..middleware.error_handler import ServiceError

logger = setup_logger('training_service')

class TrainingService:
    @staticmethod
    def start_training(task_id: str) -> bool:
        """启动训练任务"""
        try:
            # 获取任务信息
            tasks = load_json(config.TASKS_FILE, [])
            task = next((t for t in tasks if t['id'] == task_id), None)
            if not task:
                raise ServiceError(f"Task {task_id} not found")
            
            # 检查任务状态
            if task['status'] not in ['PENDING', 'FAILED']:
                raise ServiceError(f"Task {task_id} cannot be started in {task['status']} status")
            
            # 更新任务状态
            task['status'] = 'DOWNLOADING'
            task['updated_at'] = datetime.now().isoformat()
            save_json(config.TASKS_FILE, tasks)
            
            # 下载训练素材
            TrainingService._download_materials(task)
            
            # 开始训练
            TrainingService._start_training_process(task)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start training for task {task_id}: {str(e)}")
            task['status'] = 'FAILED'
            task['error'] = str(e)
            task['updated_at'] = datetime.now().isoformat()
            save_json(config.TASKS_FILE, tasks)
            return False

    @staticmethod
    def stop_training(task_id: str) -> bool:
        """停止训练任务"""
        try:
            tasks = load_json(config.TASKS_FILE, [])
            task = next((t for t in tasks if t['id'] == task_id), None)
            if not task:
                raise ServiceError(f"Task {task_id} not found")
            
            if task['status'] not in ['TRAINING', 'DOWNLOADING']:
                raise ServiceError(f"Task {task_id} cannot be stopped in {task['status']} status")
            
            # 停止训练进程
            TrainingService._stop_training_process(task)
            
            # 更新任务状态
            task['status'] = 'STOPPED'
            task['updated_at'] = datetime.now().isoformat()
            save_json(config.TASKS_FILE, tasks)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop training for task {task_id}: {str(e)}")
            return False

    @staticmethod
    def get_training_status(task_id: str) -> Optional[Dict]:
        """获取训练状态"""
        try:
            tasks = load_json(config.TASKS_FILE, [])
            task = next((t for t in tasks if t['id'] == task_id), None)
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

    @staticmethod
    def upload_material_files(material_id: str, files: List) -> bool:
        """上传训练素材文件"""
        try:
            # 获取素材信息
            materials = load_json(config.ASSETS_FILE, [])
            material = next((m for m in materials if m['id'] == material_id), None)
            if not material:
                raise ServiceError("Material not found")
            
            # 创建上传目录
            upload_dir = os.path.join(config.UPLOAD_DIR, material['folder_name'])
            os.makedirs(upload_dir, exist_ok=True)
            
            # 保存文件
            for file in files:
                file_path = os.path.join(upload_dir, file.filename)
                file.save(file_path)
            
            # 更新素材信息
            material['status'] = 'UPLOADED'
            material['file_count'] = len(files)
            material['updated_at'] = datetime.now().isoformat()
            save_json(config.ASSETS_FILE, materials)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload files: {str(e)}")
            return False 