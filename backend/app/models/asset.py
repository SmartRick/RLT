from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from ..database import Base

class Asset(Base):
    __tablename__ = 'assets'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    ip = Column(String(15), nullable=False)
    ssh_port = Column(Integer, default=22)
    ssh_username = Column(String(50), nullable=False)
    ssh_password = Column(String(255))
    ssh_key_path = Column(String(255))
    ssh_auth_type = Column(String(20), default='KEY')
    status = Column(String(20), default='PENDING')
    
    # 存储为JSON字段
    lora_training = Column(JSON, default={
        'enabled': False,
        'url': '',
        'port': None,
        'config_path': '',
        'params': '{}',
        'verified': False
    })
    
    ai_engine = Column(JSON, default={
        'enabled': False,
        'url': '',
        'port': None,
        'verified': False
    })
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 添加任务计数字段
    marking_tasks_count = Column(Integer, default=0, comment='当前标记任务数')
    training_tasks_count = Column(Integer, default=0, comment='当前训练任务数')
    max_concurrent_tasks = Column(Integer, default=2, comment='最大并发任务数')
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ip': self.ip,
            'ssh_port': self.ssh_port,
            'ssh_username': self.ssh_username,
            'ssh_auth_type': self.ssh_auth_type,
            'status': self.status,
            'lora_training': self.lora_training,
            'ai_engine': self.ai_engine,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'marking_tasks_count': self.marking_tasks_count,
            'training_tasks_count': self.training_tasks_count,
            'max_concurrent_tasks': self.max_concurrent_tasks
        }