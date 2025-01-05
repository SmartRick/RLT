from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
from datetime import datetime

class LoraTrainingConfig(BaseModel):
    enabled: bool = False
    url: Optional[HttpUrl] = None
    port: Optional[int] = None
    config_path: Optional[str] = None
    params: Optional[Dict] = None

class AIEngineConfig(BaseModel):
    enabled: bool = False
    url: Optional[HttpUrl] = None
    port: Optional[int] = None

class AssetBase(BaseModel):
    name: str
    ip: str
    ssh_port: int = 22
    ssh_username: str
    ssh_key_path: Optional[str] = None
    lora_training: Optional[LoraTrainingConfig] = LoraTrainingConfig()
    ai_engine: Optional[AIEngineConfig] = AIEngineConfig()

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    ssh_port: Optional[int] = None
    ssh_username: Optional[str] = None
    ssh_key_path: Optional[str] = None
    status: Optional[str] = None
    lora_training: Optional[LoraTrainingConfig] = None
    ai_engine: Optional[AIEngineConfig] = None

class Asset(AssetBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 