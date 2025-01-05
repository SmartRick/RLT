from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from ...schemas.training import (
    TrainingMaterialCreate, 
    TrainingMaterialUpdate,
    TrainingMaterial,
    TrainingTaskCreate,
    TrainingTaskUpdate,
    TrainingTask
)
from ...services import training_service
from ...database import get_db

router = APIRouter()

# 训练素材相关路由
@router.post("/materials/", response_model=TrainingMaterial)
async def create_material(
    material: TrainingMaterialCreate, 
    db: Session = Depends(get_db)
):
    return training_service.create_material(db, material)

@router.get("/materials/", response_model=List[TrainingMaterial])
def list_materials(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    return training_service.get_materials(db, skip=skip, limit=limit)

@router.get("/materials/{material_id}", response_model=TrainingMaterial)
def get_material(material_id: int, db: Session = Depends(get_db)):
    material = training_service.get_material(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

@router.put("/materials/{material_id}", response_model=TrainingMaterial)
def update_material(
    material_id: int, 
    material: TrainingMaterialUpdate, 
    db: Session = Depends(get_db)
):
    return training_service.update_material(db, material_id, material)

# 训练任务相关路由
@router.post("/tasks/", response_model=TrainingTask)
def create_task(task: TrainingTaskCreate, db: Session = Depends(get_db)):
    return training_service.create_task(db, task)

@router.get("/tasks/", response_model=List[TrainingTask])
def list_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return training_service.get_tasks(db, skip=skip, limit=limit)

@router.get("/tasks/{task_id}", response_model=TrainingTask)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = training_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/tasks/{task_id}", response_model=TrainingTask)
def update_task(
    task_id: int, 
    task: TrainingTaskUpdate, 
    db: Session = Depends(get_db)
):
    return training_service.update_task(db, task_id, task)

# 文件上传路由
@router.post("/materials/{material_id}/upload")
async def upload_material_files(
    material_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    return await training_service.upload_material_files(db, material_id, files) 