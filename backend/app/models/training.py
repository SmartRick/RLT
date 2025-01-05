from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from ..database import Base

class TrainingMaterial(Base):
    __tablename__ = "training_materials"
    
    id = Column(Integer, primary_key=True, index=True)
    folder_name = Column(String, unique=True, index=True)
    source_path = Column(String)
    status = Column(String)  # UPLOADED, PROCESSING, COMPLETED, FAILED
    metadata = Column(JSON)  # 存储额外的训练参数
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class TrainingTask(Base):
    __tablename__ = "training_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("training_materials.id"))
    node_id = Column(Integer, ForeignKey("assets.id"))
    status = Column(String)
    lora_path = Column(String)
    error = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime) 