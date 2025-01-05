from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

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
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        
        @staticmethod
        def json_dumps(v, *, default):
            from json import dumps
            return dumps({
                **v.dict(),
                'created_at': v.created_at.isoformat() if v.created_at else None,
                'updated_at': v.updated_at.isoformat() if v.updated_at else None
            }) 

class SshVerifyRequest(BaseModel):
    """SSH连接验证请求模型"""
    ip: str = Field(..., description="SSH服务器IP地址")
    ssh_port: int = Field(default=22, ge=1, le=65535, description="SSH端口")
    ssh_username: str = Field(..., description="SSH用户名")
    ssh_auth_type: str = Field(..., description="认证类型: PASSWORD/KEY")
    ssh_password: Optional[str] = Field(None, description="SSH密码")
    ssh_key_path: Optional[str] = Field(None, description="SSH密钥路径")

    @validator('ssh_auth_type')
    def validate_auth_type(cls, v):
        if v not in ['PASSWORD', 'KEY']:
            raise ValueError('认证类型必须是 PASSWORD 或 KEY')
        return v

    @validator('ssh_password')
    def validate_password(cls, v, values):
        if values.get('ssh_auth_type') == 'PASSWORD' and not v:
            raise ValueError('密码认证方式下必须提供密码')
        return v

    @validator('ssh_key_path')
    def validate_key_path(cls, v, values):
        if values.get('ssh_auth_type') == 'KEY' and not v:
            raise ValueError('密钥认证方式下必须提供密钥路径')
        return v 