import json
import requests
import os
import uuid
from typing import Tuple, Dict, Optional, Any, List
from ..utils.logger import setup_logger
from dataclasses import dataclass, field

logger = setup_logger('train_handler')

@dataclass
class TrainConfig:
    """训练配置参数类"""
    # 基础配置
    model_train_type: str = "flux-lora"
    train_data_dir: str = ""
    output_name: str = ""
    output_dir: str = ""
    
    # 模型路径
    pretrained_model_name_or_path: str = ""
    ae: str = ""
    clip_l: str = ""
    t5xxl: str = ""
    
    # 训练参数
    resolution: str = "768,768"
    enable_bucket: bool = True
    min_bucket_reso: int = 256
    max_bucket_reso: int = 2048
    bucket_reso_steps: int = 64
    bucket_no_upscale: bool = True
    
    # 保存配置
    save_model_as: str = "safetensors"
    save_precision: str = "bf16"
    save_every_n_epochs: int = 2
    
    # 训练超参数
    max_train_epochs: int = 10
    train_batch_size: int = 2
    gradient_checkpointing: bool = True
    gradient_accumulation_steps: int = 1
    network_train_unet_only: bool = True
    network_train_text_encoder_only: bool = False
    
    # 学习率相关
    learning_rate: float = 0.0001
    unet_lr: float = 0.0001
    text_encoder_lr: float = 0.00001
    lr_scheduler: str = "cosine_with_restarts"
    lr_warmup_steps: int = 0
    lr_scheduler_num_cycles: int = 1
    
    # 网络配置
    optimizer_type: str = "AdamW8bit"
    network_module: str = "networks.lora_flux"
    network_dim: int = 32
    network_alpha: int = 32
    
    # 日志配置
    log_with: str = "tensorboard"
    logging_dir: str = "./logs"
    
    # 其他配置
    caption_extension: str = ".txt"
    shuffle_caption: bool = False
    keep_tokens: int = 0
    seed: int = 1337
    clip_skip: int = 2
    mixed_precision: str = "bf16"
    fp8_base: bool = True
    sdpa: bool = True
    lowram: bool = False
    cache_latents: bool = True
    cache_latents_to_disk: bool = True
    cache_text_encoder_outputs: bool = True
    cache_text_encoder_outputs_to_disk: bool = True
    persistent_data_loader_workers: bool = True
    
    # 高级参数
    timestep_sampling: str = "sigmoid"
    sigmoid_scale: int = 1
    model_prediction_type: str = "raw"
    discrete_flow_shift: int = 1
    loss_type: str = "l2"
    guidance_scale: int = 1
    prior_loss_weight: int = 1
    
    # 额外字段，用于存储任意其他参数
    extra_params: Dict[str, Any] = field(default_factory=dict)

class TrainRequestHandler:
    def __init__(self, asset=None, asset_ip=None, training_port=None):
        """
        初始化训练处理器
        :param asset: 资产对象，如果提供则从资产获取连接信息
        :param asset_ip: 资产IP地址，如果同时提供asset和asset_ip，优先使用asset_ip
        :param training_port: 训练端口，如果同时提供asset和training_port，优先使用training_port
        """
        self.training_port = training_port or 28000  # 默认端口
        self.asset_ip = asset_ip or '127.0.0.1'  # 默认IP
        
        if asset and not asset_ip:
            # 根据资产的访问模式选择连接方式
            self.training_port = asset.lora_training.get('port', 28000)
            
            if asset.is_local:
                # 本地资产使用127.0.0.1
                self.asset_ip = '127.0.0.1'
            elif asset.port_access_mode == 'DOMAIN':
                # 域名访问模式
                from ..utils.common import generate_domain_url
                domain_url = generate_domain_url(asset.ip, self.training_port)
                if domain_url:
                    # 使用域名格式访问，端口设置为80
                    self.asset_ip = domain_url.replace('https://', '').replace('http://', '')
                    self.training_port = 80
                else:
                    # 如果无法生成域名URL，使用IP
                    self.asset_ip = asset.ip
            else:
                # 直连模式
                self.asset_ip = asset.ip
        
        # 构建API基础URL
        if self.training_port == 80:
            # HTTP标准端口无需在URL中指定
            self.api_base_url = f"http://{self.asset_ip}/api"
        else:
            self.api_base_url = f"http://{self.asset_ip}:{self.training_port}/api"

    def train_request(self, train_config: TrainConfig) -> str:
        """
        发送训练请求
        :param train_config: 训练配置参数
        :return: 训练任务ID
        """
        # 构建请求
        url = f"{self.api_base_url}/run"
        
        # 将TrainConfig对象转换为字典
        payload = {}
        for key, value in train_config.__dict__.items():
            if key != 'extra_params':
                payload[key] = value
        
        # 添加额外参数
        if hasattr(train_config, 'extra_params'):
            for key, value in train_config.extra_params.items():
                payload[key] = value
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        
        # 如果有自定义请求头，添加到headers
        if hasattr(train_config, 'headers') and isinstance(train_config.headers, dict):
            headers.update(train_config.headers)
        
        logger.debug(f"发送训练请求到 {url}")
        
        # 发送请求
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # 检查响应
        if data.get('status') != 'success':
            error_msg = data.get('message', '未知错误')
            raise ValueError(f"训练请求失败: {error_msg}")
        
        # 提取训练任务ID
        message = data.get('message', '')
        task_id = None
        
        # 尝试从消息中提取ID
        if 'ID:' in message:
            task_id = message.split('ID:')[-1].strip()
        
        if not task_id:
            # 如果没有找到ID，使用UUID作为备用
            task_id = str(uuid.uuid4())
            logger.warning(f"未能从响应中提取训练ID，使用生成的UUID: {task_id}")
            
        logger.info(f"训练请求发送成功，task_id: {task_id}")
        return task_id

    def check_status(self, task_id: str, train_config: Optional[TrainConfig] = None) -> str:
        """
        检查训练任务状态
        :param task_id: 任务ID
        :param train_config: 可选的训练配置参数
        :return: (is_completed, is_success, status_message)
        """
        url = f"{self.api_base_url}/tasks"
        logger.debug(f"检查训练任务状态: {url}")
        
        headers = {}
        # 如果有自定义请求头，添加到headers
        if train_config and hasattr(train_config, 'headers') and isinstance(train_config.headers, dict):
            headers.update(train_config.headers)
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # 检查响应是否有效
        if data.get('status') != 'success' or 'data' not in data or 'tasks' not in data['data']:
            logger.warning(f"任务状态响应格式无效: {data}")
            raise ValueError("任务状态响应格式无效")
        
        # 查找指定ID的任务
        task_info = None
        for task in data['data']['tasks']:
            if task.get('id') == task_id:
                task_info = task
                break
        
        # 如果没有找到任务
        if not task_info:
            logger.warning(f"未找到任务 {task_id} 的状态信息")
            return "NOT_FOUND"

        return task_info.get("status", "RUNNING")
        
    def cancel_training(self, task_id: str, train_config: Optional[TrainConfig] = None) -> bool:
        """
        取消训练任务
        :param task_id: 任务ID
        :param train_config: 可选的训练配置参数
        :return: 是否成功取消
        """
        url = f"{self.api_base_url}/tasks/terminate/{task_id}"
        logger.debug(f"取消训练任务: {url}")
        
        headers = {}
        # 如果有自定义请求头，添加到headers
        if train_config and hasattr(train_config, 'headers') and isinstance(train_config.headers, dict):
            headers.update(train_config.headers)
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'success':
            logger.info(f"成功取消训练任务: {task_id}")
            return True
        else:
            logger.warning(f"取消训练任务失败: {data.get('message', '未知错误')}")
            return False
        
    def get_all_training_logs(self) -> List[str]:
        """
        获取所有训练日志key
        :return: 所有训练日志key的列表
        """
        url = f"http://{self.asset_ip}:{self.training_port}/proxy/tensorboard/data/runs"
        logger.debug(f"获取所有训练日志key: {url}")
        
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'X-TensorBoard-Feature-Flags': '{"enabledColorGroup":true,"enabledColorGroupByRegex":true,"enabledExperimentalPlugins":[],"enabledLinkedTime":false,"enabledCardWidthSetting":true,"enabledScalarDataTable":false,"forceSvg":false,"enableDarkModeOverride":null,"defaultEnableDarkMode":false,"isAutoDarkModeAllowed":true,"inColab":false,"metricsImageSupportEnabled":true,"enableTimeSeriesPromotion":false}'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"获取到所有训练日志key: {data}")
        
        return data
        
    def get_training_loss_data(self, task_id: str) -> Dict:
        """
        获取训练loss曲线数据
        :param task_id: 训练任务ID
        :return: loss曲线数据
        """
        # 先获取所有训练日志key
        all_logs = self.get_all_training_logs()
        if not all_logs:
            raise ValueError("无法获取训练日志列表")
            
        # 匹配当前任务ID对应的key
        matched_key = None
        for key in all_logs:
            # 检查key是否包含任务ID
            if task_id in key:
                matched_key = key
                logger.info(f"找到匹配的训练日志key: {matched_key}")
                break
                
        if not matched_key:
            raise ValueError(f"未找到与任务ID {task_id} 匹配的训练日志key")
            
        # 使用匹配到的key获取loss数据
        url = f"http://{self.asset_ip}:{self.training_port}/proxy/tensorboard/experiment/defaultExperimentId/data/plugin/timeseries/timeSeries"
        logger.debug(f"获取训练loss曲线数据: {url}")
        
        # 构建正确的multipart/form-data请求
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'X-XSRF-Protected': '1'
        }
        
        # 使用正确的请求参数格式，使用匹配到的key
        files = {
            'requests': (None, json.dumps([{"plugin":"scalars","tag":"loss/average","run":matched_key}]))
        }
        
        response = requests.post(url, files=files, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"获取到训练loss曲线数据: {data}")
        
        return data 