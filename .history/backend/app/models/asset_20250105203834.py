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
    ssh_key_path = Column(String(255))
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