from typing import Dict, Any
from ..database import get_db
from ..models.setting import Setting
from ..schemas.setting import SettingUpdate
from ..utils.logger import setup_logger
import json

logger = setup_logger('config_service')

class ConfigService:
    DEFAULT_SETTINGS = {
        'source_dir': {
            'value': '/path/to/source',
            'type': 'string',
            'description': '源文件目录'
        },
        'lora_output_path': {
            'value': '/path/to/output',
            'type': 'string',
            'description': 'Lora输出目录'
        },
        'scheduling_minute': {
            'value': '5',
            'type': 'integer',
            'description': '调度间隔(分钟)'
        },
        'mark_pan_dir': {
            'value': '/loraFile/mark',
            'type': 'string',
            'description': '标记文件目录'
        },
        'lora_pan_upload_dir': {
            'value': '/loraFile/lora',
            'type': 'string',
            'description': 'Lora上传目录'
        },
        'mark_poll_interval': {
            'value': '5',
            'type': 'integer',
            'description': '标记任务轮询间隔(秒)'
        },
        'mark_workflow_api': {
            'value': '{}',
            'type': 'json',
            'description': 'ComfyUI标记工作流配置'
        }
    }

    @staticmethod
    def init_settings():
        """初始化系统设置"""
        try:
            with get_db() as db:
                # 检查是否需要初始化
                if db.query(Setting).count() == 0:
                    # 插入默认设置
                    for key, config in ConfigService.DEFAULT_SETTINGS.items():
                        setting = Setting(
                            key=key,
                            value=str(config['value']),
                            type=config['type'],
                            description=config['description']
                        )
                        db.add(setting)
                    db.commit()
                    logger.info("系统设置初始化完成")
        except Exception as e:
            logger.error(f"初始化系统设置失败: {str(e)}")
            raise

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """获取所有配置"""
        try:
            with get_db() as db:
                settings = db.query(Setting).all()
                config = {}
                for setting in settings:
                    if setting.type == 'integer':
                        config[setting.key] = int(setting.value)
                    elif setting.type == 'json':
                        config[setting.key] = json.loads(setting.value)
                    else:
                        config[setting.key] = setting.value
                return config
        except Exception as e:
            logger.error(f"获取配置失败: {str(e)}")
            # 返回默认值
            return {k: v['value'] for k, v in ConfigService.DEFAULT_SETTINGS.items()}

    @staticmethod
    def update_config(config_data: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            with get_db() as db:
                for key, value in config_data.items():
                    setting = db.query(Setting).filter(Setting.key == key).first()
                    if setting:
                        setting.value = str(value)
                db.commit()
                logger.info("配置更新成功")
                return True
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False 

    @staticmethod
    def get_value(key: str, default: Any = None) -> Any:
        """
        获取指定配置值
        :param key: 配置键
        :param default: 默认值
        :return: 配置值
        """
        try:
            with get_db() as db:
                setting = db.query(Setting).filter(Setting.key == key).first()
                if not setting:
                    # 如果数据库中没有，返回默认配置或传入的默认值
                    default_setting = ConfigService.DEFAULT_SETTINGS.get(key, {})
                    return default_setting.get('value', default)

                if setting.type == 'integer':
                    return int(setting.value)
                elif setting.type == 'json':
                    return json.loads(setting.value)
                return setting.value

        except Exception as e:
            logger.error(f"获取配置值失败 [{key}]: {str(e)}")
            # 如果出错，返回默认配置或传入的默认值
            default_setting = ConfigService.DEFAULT_SETTINGS.get(key, {})
            return default_setting.get('value', default) 