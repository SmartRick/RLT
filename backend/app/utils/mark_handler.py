import json
import requests
import os
from typing import Tuple, Dict, Optional, Any
from ..utils.logger import setup_logger
from ..services.config_service import ConfigService
from ..config import Config

logger = setup_logger('mark_handler')

class MarkRequestHandler:
    def __init__(self, asset_config: dict, asset_ip: str = None):
        """
        初始化标记处理器
        :param asset_config: 资产配置信息，包含AI引擎端口等
        :param asset_ip: 资产IP地址，如果不提供则使用127.0.0.1
        """
        self.asset_config = asset_config
        self.asset_ip = asset_ip or '127.0.0.1'
        self.config = ConfigService.get_config()
        self.workflow_api = self.load_workflow_api()
        self.api_base_url = f"http://{self.asset_ip}:{self.asset_config.get('port', 8188)}"

    def load_workflow_api(self) -> Dict:
        """加载标记工作流配置"""
        try:
            workflow_file = os.path.join(Config.DATA_DIR, 'workflow', 'mark_workflow_api.json')
            with open(workflow_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载工作流配置失败: {str(e)}")
            return {}
            
    def mark_request(self, input_folder: str, output_folder: str, resolution: int, ratio: str) -> str:
        """
        发送标记请求
        :return: prompt_id
        :raises: ValueError 如果请求失败或返回无效数据
        """
        try:
            # 更新工作流配置
            workflow = self.workflow_api.copy()
            workflow["35"]["inputs"]["aspect_ratio"] = ratio
            workflow["35"]["inputs"]["scale_to_length"] = resolution
            workflow["57"]["inputs"]["string"] = input_folder
            workflow["155"]["inputs"]["string"] = output_folder
            workflow["64"]["inputs"]["max_new_tokens"] = 300
            # 保存修改后的工作流配置到项目路径的workflow文件夹下
            workflow_new = os.path.join(Config.DATA_DIR, 'workflow', 'mark_workflow_api_new.json')
            with open(workflow_new, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, ensure_ascii=False, indent=4)

            # 构建请求
            url = f"{self.api_base_url}/prompt"
            payload = {
                "prompt": workflow,
                "client_id": "lora_tool"
            }

            logger.debug(f"发送标记请求到 {url}")
            
            # 发送请求
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            prompt_id = data.get("prompt_id")
            
            if not prompt_id:
                raise ValueError("API返回成功但未获取到prompt_id")
                
            logger.info(f"标记请求发送成功，prompt_id: {prompt_id}")
            return prompt_id

        except requests.exceptions.RequestException as e:
            error_msg, error_detail = self._parse_request_error(e)
            logger.error(f"发送标记请求失败: {error_msg}", exc_info=True)
            
            # 构建结构化错误信息
            error_info = {
                "message": error_msg,
                "detail": error_detail,
                "type": "REQUEST_ERROR"
            }
            
            raise ValueError(json.dumps(error_info))
            
        except Exception as e:
            logger.error(f"发送标记请求时发生未知错误: {str(e)}", exc_info=True)
            
            # 构建结构化错误信息
            error_info = {
                "message": str(e),
                "type": "UNKNOWN_ERROR"
            }
            
            raise ValueError(json.dumps(error_info))
            
    def _parse_request_error(self, exception: requests.exceptions.RequestException) -> Tuple[str, str]:
        """解析请求异常，提取有用的错误信息"""
        error_msg = str(exception)
        error_detail = ""
        
        try:
            if hasattr(exception, 'response') and exception.response is not None:
                status_code = exception.response.status_code
                error_msg = f"HTTP {status_code}"
                
                # 尝试解析JSON响应
                try:
                    error_data = exception.response.json()
                    if isinstance(error_data, dict):
                        api_error = error_data.get('error', '')
                        api_detail = error_data.get('detail', '')
                        
                        if api_error:
                            error_msg = api_error
                        if api_detail:
                            error_detail = api_detail
                except ValueError:
                    # 响应不是有效的JSON
                    error_detail = exception.response.text[:200]  # 只取前200个字符
        except Exception:
            # 解析过程中出现异常，返回原始错误
            pass
            
        return error_msg, error_detail

    def check_status(self, prompt_id: str) -> Tuple[bool, bool, Dict[str, Any]]:
        """
        检查标记任务状态
        :param prompt_id: 任务ID
        :return: (is_completed, is_success, task_info)
        """
        try:
            url = f"{self.api_base_url}/history/{prompt_id}"
            logger.debug(f"检查任务状态: {url}")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查响应是否为空
            if not data or data == {}:
                logger.debug(f"任务 {prompt_id} 执行中...")
                return False, False, {"status": "processing", "progress": 0}

            # 获取任务状态
            task_info = data.get(prompt_id, {}).get("status", {})
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

        except requests.exceptions.RequestException as e:
            error_msg, error_detail = self._parse_request_error(e)
            logger.error(f"检查任务状态失败: {error_msg}")
            
            error_info = {
                "error_message": error_msg,
                "error_detail": error_detail,
                "error_type": "REQUEST_ERROR"
            }
            
            return False, False, {"error_info": error_info}
            
        except Exception as e:
            logger.error(f"检查任务状态时发生未知错误: {str(e)}", exc_info=True)
            
            error_info = {
                "error_message": str(e),
                "error_type": "UNKNOWN_ERROR"
            }
            
            return False, False, {"error_info": error_info}
            
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
        
    def get_status(self, prompt_id: str) -> Optional[Dict]:
        """
        获取任务状态信息（简化版）
        :param prompt_id: 任务ID
        :return: 状态信息字典或None（如果获取失败）
        """
        completed, success, info = self.check_status(prompt_id)
        if not info:
            return None
            
        return {
            "completed": completed,
            "success": success,
            "progress": info.get("progress", 0),
            "status": info.get("status"),
            "error_info": info.get("error_info", {})
        } 