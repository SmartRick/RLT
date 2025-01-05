from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from ..database import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    ip = Column(String)
    ssh_port = Column(Integer, default=22)
    ssh_username = Column(String)
    ssh_key_path = Column(String, nullable=True)
    status = Column(String, default='PENDING')
    lora_training = Column(JSON, default=lambda: {"enabled": False, "verified": False})
    ai_engine = Column(JSON, default=lambda: {"enabled": False, "verified": False})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) 