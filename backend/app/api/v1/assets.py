from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...schemas.asset import AssetCreate, AssetUpdate, Asset
from ...services import asset_service
from ...database import get_db

router = APIRouter()

@router.post("/assets/", response_model=Asset)
def create_asset(asset: AssetCreate, db: Session = Depends(get_db)):
    return asset_service.create_asset(db, asset)

@router.get("/assets/", response_model=List[Asset])
def list_assets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return asset_service.get_assets(db, skip=skip, limit=limit)

@router.get("/assets/{asset_id}", response_model=Asset)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = asset_service.get_asset(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.put("/assets/{asset_id}", response_model=Asset)
def update_asset(asset_id: int, asset: AssetUpdate, db: Session = Depends(get_db)):
    return asset_service.update_asset(db, asset_id, asset) 