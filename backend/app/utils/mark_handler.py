import json
import requests
import os
from ..utils.logger import setup_logger
from ..services.config_service import ConfigService
from ..config import Config

logger = setup_logger('mark_handler')

class MarkRequestHandler:
    def __init__(self, asset_config: dict):
        """
        初始化标记处理器
        :param asset_config: 资产配置信息，包含AI引擎URL等
        """
        self.asset_config = asset_config
        self.config = ConfigService.get_config()
        self.workflow_api = self.load_workflow_api()

    def load_workflow_api(self):
        """加载标记工作流配置"""
        try:
            workflow_file = os.path.join(Config.DATA_DIR, 'workflow', 'mark_workflow_api.json')
            with open(workflow_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载工作流配置失败: {str(e)}")
            return {}

    def mark_request(self, input_folder: str, output_folder: str, resolution: int, ratio: float) -> str:
        """
        发送标记请求
        :return: prompt_id
        """
        try:
            # 更新工作流配置
            workflow = self.workflow_api.copy()
            workflow["35"]["inputs"]["aspect_ratio"] = ratio
            workflow["35"]["inputs"]["scale_to_length"] = resolution
            workflow["57"]["inputs"]["string"] = input_folder
            workflow["155"]["inputs"]["string"] = output_folder
            workflow["64"]["inputs"]["max_new_tokens"] = 300

            # 构建请求
            url = f"http://{self.asset_config['url']}:{self.asset_config['port']}/prompt"
            payload = {
                "prompt": workflow,
                "client_id": "lora_tool"
            }

            # 发送请求
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            prompt_id = data.get("prompt_id")
            
            if not prompt_id:
                raise ValueError("未获取到prompt_id")
                
            return prompt_id

        except Exception as e:
            logger.error(f"发送标记请求失败: {str(e)}")
            raise

    def check_status(self, prompt_id: str) -> tuple[bool, bool, dict]:
        """
        检查标记任务状态
        :return: (is_completed, is_success, task_info)
        """
        try:
            url = f"http://{self.asset_config['url']}:{self.asset_config['port']}/history/{prompt_id}"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"任务 {prompt_id} 状态详情: {json.dumps(data, indent=2)}")
            
            # 检查响应是否为空
            if not data or data == {}:
                logger.debug(f"任务 {prompt_id} 执行中...")
                return False, False, {}

            # 获取任务状态
            task_info = data.get(prompt_id, {}).get("status", {})
            status = task_info.get("status_str")

            # 提取错误信息
            error_info = {}
            if status == "error":
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
                logger.debug(f"任务 {prompt_id} 状态: {status}")
                return False, False, result_info

        except Exception as e:
            logger.error(f"检查任务状态失败: {str(e)}")
            return False, False, {"error_info": {"error_message": str(e)}} 