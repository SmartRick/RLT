import json
import os
import random
from typing import Tuple, Dict, Optional, Any
from ..utils.logger import setup_logger
from ..config import Config
from dataclasses import dataclass
from task_scheduler.comfyui_api import ComfyUIAPI, ComfyUIConfig

logger = setup_logger('mark_handler')

@dataclass
class MarkConfig:
    """标记配置参数类"""
    input_folder: str
    output_folder: str
    auto_crop: bool = True
    resolution: int = 1024
    default_crop_ratio: str = '1:1'
    max_tokens: int = 300
    min_confidence: float = 0.6
    trigger_words: str = ''

class MarkRequestHandler:
    def __init__(self, asset=None):
        """
        初始化标记处理器
        :param asset: 资产对象，如果不提供则使用本地地址127.0.0.1:8188
        """
        self.asset_ip = f'http://{asset.ip}'
        self.mark_port = asset.ai_engine.get('port', 8188)
        
        if asset.port_access_mode == 'DOMAIN':
            # 域名访问模式
            from ..utils.common import generate_domain_url
            domain_url,port = generate_domain_url(asset.ip, self.mark_port)
            # 使用域名格式访问，端口设置为80
            self.asset_ip = domain_url
            self.mark_port = port
            
        # 创建ComfyUIConfig和ComfyUIAPI实例
        self.comfy_config = ComfyUIConfig(
            host=self.asset_ip,
            port=self.mark_port,
            client_id="lora_tool"
        )
        self.api = ComfyUIAPI(self.comfy_config)

    def load_workflow_api(self) -> Dict:
        """加载标记工作流配置"""
        try:
            #TODO: 从数据库中获取工作流配置
            workflow_file = os.path.join(Config.DATA_DIR, 'workflow', 'mark_workflow_api_list.json')
            with open(workflow_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载工作流配置失败: {str(e)}")
            return {}
            
    def mark_request(self, mark_config: MarkConfig) -> str:
        """
        发送标记请求
        :param mark_config: 标记配置参数
        :return: prompt_id
        :raises: ValueError 如果请求失败或返回无效数据
        """
        try:
            # 更新工作流配置
            workflow = self.load_workflow_api()
            workflow["209"]["inputs"]["boolean"] = mark_config.auto_crop
            workflow["35"]["inputs"]["aspect_ratio"] = mark_config.default_crop_ratio
            workflow["35"]["inputs"]["scale_to_length"] = mark_config.resolution
            workflow["208"]["inputs"]["string"] = mark_config.input_folder
            workflow["155"]["inputs"]["string"] = mark_config.output_folder
            
            # workflow["207"]["inputs"]["seed"] = random.randint(1, 1000000)
            # workflow["64"]["inputs"]["max_new_tokens"] = mark_config.max_tokens
            workflow["220"]["inputs"]["threshold"] = mark_config.min_confidence
            workflow["210"]["inputs"]["string"] = mark_config.trigger_words
            # 保存修改后的工作流配置到项目路径的workflow文件夹下
            workflow_new_file = os.path.join(Config.DATA_DIR, 'workflow', 'mark_workflow_api_new.json')
            with open(workflow_new_file, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, ensure_ascii=False, indent=4)

            logger.debug(f"发送标记请求到 http://{self.asset_ip}:{self.mark_port}")
            
            # 使用ComfyUIAPI提交任务
            response = self.api.submit_prompt(workflow)
            
            prompt_id = response.get("prompt_id")
            
            if not prompt_id:
                raise ValueError("API返回成功但未获取到prompt_id")
                
            logger.info(f"标记请求发送成功，prompt_id: {prompt_id}")
            return prompt_id

        except Exception as e:
            logger.error(f"发送标记请求失败: {str(e)}", exc_info=True)
            
            # 构建结构化错误信息
            error_info = {
                "message": str(e),
                "type": type(e).__name__
            }
            
            raise ValueError(json.dumps(error_info))
            
    def check_status(self, prompt_id: str, mark_config: MarkConfig) -> Tuple[bool, bool, Dict[str, Any]]:
        """
        检查标记任务状态
        :param prompt_id: 任务ID
        :param mark_config: 标记配置参数
        :return: (is_completed, is_success, task_info)
        """
        try:
            # 使用ComfyUIAPI获取任务历史
            history_data = self.api.get_history_by_id(prompt_id)
            
            # 检查响应是否为空
            if not history_data or not isinstance(history_data, dict) or prompt_id not in history_data:
                logger.debug(f"任务 {prompt_id} 执行中...")
                return False, False, {"status": "processing", "progress": 0}
    
            # 获取任务状态
            task_info = history_data.get(prompt_id, {}).get("status", {})
            status = task_info.get("status_str")
    
            # 提取错误信息
            error_info = self._extract_error_info(task_info)
    
            result_info = {
                "status": status,
                "progress": task_info.get("progress", 0),
                "execution_time": task_info.get("exec_time", 0),
                "error_info": error_info
            }
    
            if status == "success":
                logger.info(f"任务 {prompt_id} 完成")
                return True, True, result_info
            elif status == "error":
                error_msg = error_info.get("error_message", "未知错误")
                logger.error(f"任务 {prompt_id} 失败: {error_msg}")
                return True, False, result_info
            else:
                logger.debug(f"任务 {prompt_id} 状态: {status}, 进度: {result_info['progress']}%")
                return False, False, result_info
                
        except Exception as e:
            logger.error(f"检查任务状态出错: {str(e)}", exc_info=True)
            # 返回处理中状态，允许后续重试
            return False, False, {"status": "error_checking", "error": str(e), "progress": 0}
            
    def _extract_error_info(self, task_info: Dict) -> Dict:
        """从任务状态中提取错误信息"""
        error_info = {}
        
        if task_info.get("status_str") == "error":
            messages = task_info.get("messages", [])
            for msg in messages:
                if msg[0] == "execution_error":
                    error_data = msg[1]
                    error_info = {
                        "node_id": error_data.get("node_id"),
                        "node_type": error_data.get("node_type"),
                        "error_type": error_data.get("exception_type"),
                        "error_message": error_data.get("exception_message"),
                        "traceback": error_data.get("traceback"),
                        "inputs": error_data.get("current_inputs")
                    }
                    break
                    
        return error_info
        
    def interrupt(self) -> bool:
        """
        中断正在进行的标记任务
        
        Returns:
            操作是否成功
        """
        try:
            result = self.api.interrupt()
            return result.get("success", False)
        except Exception as e:
            logger.error(f"中断任务失败: {str(e)}")
            return False