from typing import Optional
from pydantic import BaseModel, Field, validator

class LoraTrainingConfig(BaseModel):
    enabled: bool = False
    url: Optional[str] = ''
    port: Optional[int] = None
    config_path: Optional[str] = ''
    params: Optional[str] = '{}'

    @validator('url')
    def validate_url(cls, v, values):
        if values.get('enabled', False):
            if not v or len(v.strip()) == 0:
                raise ValueError('当启用Lora训练能力时，URL不能为空')
        return v

    @validator('port')
    def validate_port(cls, v, values):
        if values.get('enabled', False):
            if v is None:
                raise ValueError('当启用Lora训练能力时，端口不能为空')
            if v < 1 or v > 65535:
                raise ValueError('端口范围必须在1-65535之间')
        return v

class AIEngineConfig(BaseModel):
    enabled: bool = False
    url: Optional[str] = ''
    port: Optional[int] = None

    @validator('url')
    def validate_url(cls, v, values):
        if values.get('enabled', False):
            if not v or len(v.strip()) == 0:
                raise ValueError('当启用AI引擎能力时，URL不能为空')
        return v

    @validator('port')
    def validate_port(cls, v, values):
        if values.get('enabled', False):
            if v is None:
                raise ValueError('当启用AI引擎能力时，端口不能为空')
            if v < 1 or v > 65535:
                raise ValueError('端口范围必须在1-65535之间')
        return v

class AssetCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    ip: str = Field(..., regex=r'^(\d{1,3}\.){3}\d{1,3}$')
    ssh_port: int = Field(..., gt=0, lt=65536)
    ssh_username: str
    ssh_key_path: Optional[str] = None
    lora_training: LoraTrainingConfig
    ai_engine: AIEngineConfig

class AssetUpdate(AssetCreate):
    pass

class Asset(AssetCreate):
    id: int
    status: str = 'PENDING'

    class Config:
        orm_mode = True 