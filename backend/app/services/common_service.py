from typing import Dict, Any, List, Optional
import requests
import random
import hashlib
import json
import time
from ..utils.logger import setup_logger
from ..services.config_service import ConfigService

logger = setup_logger('common_service')

class CommonService:
    """
    系统通用接口服务
    提供各种常用功能接口
    """
    
    @staticmethod
    def translate_text(text: str, to_lang: str = None, from_lang: str = None) -> Dict[str, Any]:
        """
        调用百度翻译API翻译文本
        
        Args:
            text: 要翻译的文本
            to_lang: 目标语言，默认为系统配置的默认目标语言
            from_lang: 源语言，默认为auto（自动检测）
            
        Returns:
            包含翻译结果的字典
            {
                'success': True/False,
                'result': '翻译结果',
                'from': '源语言',
                'to': '目标语言',
                'error': '错误信息（如果失败）'
            }
        """
        try:
            # 获取百度翻译API配置
            config = ConfigService.get_value('baidu_translate_config', {})
            
            if not config or not isinstance(config, dict):
                return {
                    'success': False,
                    'error': '系统未配置百度翻译API'
                }
            
            app_id = config.get('app_id')
            secret_key = config.get('secret_key')
            api_url = config.get('api_url', 'https://fanyi-api.baidu.com/api/trans/vip/translate')
            
            if not app_id or not secret_key:
                return {
                    'success': False,
                    'error': '百度翻译API配置不完整'
                }
            
            # 设置默认值
            if not from_lang:
                from_lang = config.get('default_from', 'auto')
            if not to_lang:
                to_lang = config.get('default_to', 'zh')
            
            # 处理过长的文本
            if len(text) > 2000:
                text = text[:2000]
                logger.warning('翻译文本过长，已截断至2000字符')
            
            # 准备请求参数
            salt = str(random.randint(32768, 65536))
            sign = app_id + text + salt + secret_key
            sign = hashlib.md5(sign.encode()).hexdigest()
            
            params = {
                'q': text,
                'from': from_lang,
                'to': to_lang,
                'appid': app_id,
                'salt': salt,
                'sign': sign
            }
            
            # 发送请求
            response = requests.get(api_url, params=params, timeout=10)
            result = response.json()
            
            if 'error_code' in result:
                return {
                    'success': False,
                    'error': f"百度翻译API错误: {result.get('error_code')} - {result.get('error_msg', '未知错误')}"
                }
            
            # 处理翻译结果
            translated_text = ""
            src_lang = from_lang
            
            if 'trans_result' in result:
                translated_text = ' '.join([item['dst'] for item in result['trans_result']])
                src_lang = result.get('from', from_lang)
            
            return {
                'success': True,
                'result': translated_text,
                'from': src_lang,
                'to': to_lang
            }
            
        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            return {
                'success': False,
                'error': f"翻译失败: {str(e)}"
            }
    
    @staticmethod
    def batch_translate(texts: List[str], to_lang: str = None, from_lang: str = None) -> Dict[str, Any]:
        """
        批量翻译多个文本
        
        Args:
            texts: 要翻译的文本列表
            to_lang: 目标语言，默认为系统配置的默认目标语言
            from_lang: 源语言，默认为auto（自动检测）
            
        Returns:
            包含所有翻译结果的字典
        """
        results = []
        success_count = 0
        
        for text in texts:
            # 为避免API调用过于频繁，添加短暂延迟
            time.sleep(0.2)
            result = CommonService.translate_text(text, to_lang, from_lang)
            results.append(result)
            if result['success']:
                success_count += 1
        
        return {
            'success': success_count == len(texts),
            'results': results,
            'total': len(texts),
            'success_count': success_count,
            'failed_count': len(texts) - success_count
        } 