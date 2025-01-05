from sqlalchemy import Column, Integer, String, DateTime, Enum
from ..database import Base

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(Enum("TRAINING_NODE", "AI_NODE", name="asset_type"))
    ip = Column(String)
    ssh_port = Column(Integer)
    ssh_username = Column(String)
    ssh_key_path = Column(String)
    status = Column(Enum("ONLINE", "OFFLINE", name="asset_status"))
    created_at = Column(DateTime)
    updated_at = Column(DateTime) 