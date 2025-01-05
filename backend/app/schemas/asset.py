from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AssetBase(BaseModel):
    name: str
    type: str
    ip: str
    ssh_port: int = 22
    ssh_username: str
    ssh_key_path: Optional[str] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    ssh_port: Optional[int] = None
    ssh_username: Optional[str] = None
    ssh_key_path: Optional[str] = None
    status: Optional[str] = None

class Asset(AssetBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 