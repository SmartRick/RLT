from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime

class TrainingMaterial(Base):
    __tablename__ = "training_materials"

    id = Column(Integer, primary_key=True, index=True)
    folder_name = Column(String, unique=True, index=True)
    source_path = Column(String)
    status = Column(String)  # PENDING, UPLOADED, PROCESSING, COMPLETED, FAILED
    extra_info = Column(JSON)  # 改用 extra_info 替代 metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    tasks = relationship("TrainingTask", back_populates="material")

class TrainingTask(Base):
    __tablename__ = "training_tasks"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("training_materials.id"))
    model_name = Column(String)
    status = Column(String)  # PENDING, TRAINING, COMPLETED, FAILED
    progress = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 关联关系
    material = relationship("TrainingMaterial", back_populates="tasks") 