from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile, HTTPException
import os
import shutil

from ..models.training import TrainingMaterial, TrainingTask
from ..models.asset import Asset
from ..schemas.training import (
    TrainingMaterialCreate,
    TrainingMaterialUpdate,
    TrainingTaskCreate,
    TrainingTaskUpdate
)
from ..config import settings
from ..utils.ssh import execute_command

# 训练素材相关服务
async def create_material(db: Session, material: TrainingMaterialCreate) -> TrainingMaterial:
    db_material = TrainingMaterial(
        folder_name=material.folder_name,
        source_path=material.source_path,
        status="UPLOADED",
        metadata=material.metadata,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

def get_materials(db: Session, skip: int = 0, limit: int = 100) -> List[TrainingMaterial]:
    return db.query(TrainingMaterial).offset(skip).limit(limit).all()

def get_material(db: Session, material_id: int) -> Optional[TrainingMaterial]:
    return db.query(TrainingMaterial).filter(TrainingMaterial.id == material_id).first()

def update_material(
    db: Session, 
    material_id: int, 
    material: TrainingMaterialUpdate
) -> Optional[TrainingMaterial]:
    db_material = get_material(db, material_id)
    if not db_material:
        return None
        
    update_data = material.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_material, field, value)
    
    db_material.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_material)
    return db_material

# 训练任务相关服务
def create_task(db: Session, task: TrainingTaskCreate) -> TrainingTask:
    # 验证素材和节点是否存在
    material = get_material(db, task.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Training material not found")
        
    node = db.query(Asset).filter(Asset.id == task.node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Training node not found")
    
    db_task = TrainingTask(
        material_id=task.material_id,
        node_id=task.node_id,
        status="PENDING",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 异步启动训练任务
    # TODO: 实现异步任务处理
    
    return db_task

def get_tasks(db: Session, skip: int = 0, limit: int = 100) -> List[TrainingTask]:
    return db.query(TrainingTask).offset(skip).limit(limit).all()

def get_task(db: Session, task_id: int) -> Optional[TrainingTask]:
    return db.query(TrainingTask).filter(TrainingTask.id == task_id).first()

def update_task(
    db: Session, 
    task_id: int, 
    task: TrainingTaskUpdate
) -> Optional[TrainingTask]:
    db_task = get_task(db, task_id)
    if not db_task:
        return None
        
    update_data = task.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task

# 文件上传服务
async def upload_material_files(
    db: Session, 
    material_id: int, 
    files: List[UploadFile]
) -> dict:
    material = get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # 确保目标目录存在
    upload_dir = os.path.join(settings.SOURCE_DIR, material.folder_name)
    os.makedirs(upload_dir, exist_ok=True)
    
    uploaded_files = []
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(file.filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload {file.filename}: {str(e)}")
    
    return {
        "message": "Files uploaded successfully",
        "material_id": material_id,
        "uploaded_files": uploaded_files
    } 