from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from ..models.asset import Asset
from ..schemas.asset import AssetCreate, AssetUpdate
from ..utils.ssh import test_ssh_connection

def create_asset(db: Session, asset: AssetCreate) -> Asset:
    db_asset = Asset(
        name=asset.name,
        type=asset.type,
        ip=asset.ip,
        ssh_port=asset.ssh_port,
        ssh_username=asset.ssh_username,
        ssh_key_path=asset.ssh_key_path,
        status="OFFLINE",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # 测试SSH连接
    if test_ssh_connection(db_asset):
        db_asset.status = "ONLINE"
    
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def get_assets(db: Session, skip: int = 0, limit: int = 100) -> List[Asset]:
    return db.query(Asset).offset(skip).limit(limit).all()

def get_asset(db: Session, asset_id: int) -> Optional[Asset]:
    return db.query(Asset).filter(Asset.id == asset_id).first()

def update_asset(db: Session, asset_id: int, asset_update: AssetUpdate) -> Optional[Asset]:
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
        
    update_data = asset_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_asset, field, value)
    
    db_asset.updated_at = datetime.utcnow()
    
    # 如果更新了连接相关信息，重新测试连接
    if any(field in update_data for field in ['ip', 'ssh_port', 'ssh_username', 'ssh_key_path']):
        db_asset.status = "ONLINE" if test_ssh_connection(db_asset) else "OFFLINE"
    
    db.commit()
    db.refresh(db_asset)
    return db_asset 