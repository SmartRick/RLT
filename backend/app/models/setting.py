from sqlalchemy import Column, String, Integer, JSON
from ..database import Base

class Setting(Base):
    __tablename__ = 'settings'
    
    key = Column(String(50), primary_key=True)
    value = Column(String(500), nullable=False)
    type = Column(String(20), nullable=False)  # string, integer, json
    description = Column(String(200))

    # 添加默认配置
    @staticmethod
    def get_defaults():
        return {
            'mark_workflow_api': {
                'type': 'json',
                'value': '{}',  # 从文件加载的默认工作流
                'description': 'ComfyUI标记工作流配置'
            },
            'comfyui_prompt_url': {
                'type': 'string',
                'value': 'http://127.0.0.1:8188/prompt',
                'description': 'ComfyUI执行API地址'
            },
            'comfyui_history_url': {
                'type': 'string',
                'value': 'http://127.0.0.1:8188/history/',
                'description': 'ComfyUI历史查询API地址'
            },
            'mark_poll_interval': {
                'type': 'integer',
                'value': '5',
                'description': '标记任务轮询间隔(秒)'
            }
        } 