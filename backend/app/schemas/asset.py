from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

class LoraTrainingConfig(BaseModel):
    enabled: bool = False
    port: Optional[int] = None
    config_path: Optional[str] = ''
    params: Optional[str] = '{}'
    verified: bool = False

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
    port: Optional[int] = None
    verified: bool = False

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
    ssh_auth_type: str = Field(default='KEY')
    ssh_password: Optional[str] = None
    ssh_key_path: Optional[str] = None
    lora_training: LoraTrainingConfig
    ai_engine: AIEngineConfig
    is_local: bool = Field(default=False, description="是否为本地系统资产")

    @validator('ssh_auth_type')
    def validate_auth_type(cls, v):
        if v not in ['PASSWORD', 'KEY']:
            raise ValueError('认证类型必须是 PASSWORD 或 KEY')
        return v

    @validator('ssh_password')
    def validate_password(cls, v, values):
        # 打印values以便调试
        print(f"Password validator values: {values}")
        
        # 安全检查is_local值，即使它不在values中
        # 检查名称是否为本地系统
        if values.get('name') == '本地系统' or values.get('is_local', False):
            return v
            
        if 'ssh_auth_type' in values and values['ssh_auth_type'] == 'PASSWORD':
            if not v:
                raise ValueError('密码认证方式下必须提供密码')
        return v

    @validator('ssh_key_path')
    def validate_key_path(cls, v, values):
        # 打印values以便调试
        print(f"Key path validator values: {values}")
        
        # 安全检查is_local值，即使它不在values中
        # 检查名称是否为本地系统
        if values.get('name') == '本地系统' or values.get('is_local', False):
            return v
            
        if 'ssh_auth_type' in values and values['ssh_auth_type'] == 'KEY':
            if not v:
                raise ValueError('密钥认证方式下必须提供密钥路径')
        return v

class Asset(BaseModel):
    id: int
    name: str
    ip: str
    ssh_port: int
    ssh_username: str
    ssh_auth_type: str = 'KEY'
    ssh_password: Optional[str] = None
    ssh_key_path: Optional[str] = None
    status: str = 'PENDING'
    lora_training: LoraTrainingConfig
    ai_engine: AIEngineConfig
    created_at: datetime
    updated_at: datetime
    is_local: bool = False  # 添加本地系统标识

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

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    ip: Optional[str] = Field(None, regex=r'^(\d{1,3}\.){3}\d{1,3}$')
    ssh_port: Optional[int] = Field(None, gt=0, lt=65536)
    ssh_username: Optional[str] = None
    ssh_auth_type: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_key_path: Optional[str] = None
    lora_training: Optional[LoraTrainingConfig] = None
    ai_engine: Optional[AIEngineConfig] = None
    is_local: Optional[bool] = None

    @validator('ssh_password')
    def validate_update_password(cls, v, values):
        # 打印values以便调试
        print(f"Update password validator values: {values}")
        
        # 如果是本地系统或is_local为true，跳过验证
        if values.get('name') == '本地系统' or values.get('is_local', False):
            return v
            
        # 如果密码未提供(None)，允许通过，因为是部分更新
        if v is None:
            return v
            
        # 只有当auth_type明确是PASSWORD时才验证
        if values.get('ssh_auth_type') == 'PASSWORD' and not v:
            raise ValueError('密码认证方式下必须提供密码')
        return v

    @validator('ssh_key_path')
    def validate_update_key_path(cls, v, values):
        # 打印values以便调试  
        print(f"Update key path validator values: {values}")
        
        # 如果是本地系统或is_local为true，跳过验证
        if values.get('name') == '本地系统' or values.get('is_local', False):
            return v
            
        # 如果密钥路径未提供(None)，允许通过，因为是部分更新
        if v is None:
            return v
            
        # 只有当auth_type明确是KEY时才验证
        if values.get('ssh_auth_type') == 'KEY' and not v:
            raise ValueError('密钥认证方式下必须提供密钥路径')
        return v

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