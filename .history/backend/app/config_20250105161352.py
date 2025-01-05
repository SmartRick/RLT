from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Lora Training Manager"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # 文件路径配置
    SOURCE_DIR: str = "./source"
    LORA_OUTPUT_PATH: str = "./output"
    MARK_PAN_DIR: str = "/loraFile/mark"
    LORA_PAN_UPLOAD_DIR: str = "/loraFile/lora"
    
    # SSH配置
    SSH_KEY_PATH: str = "~/.ssh/id_rsa"
    SSH_KNOWN_HOSTS: str = "~/.ssh/known_hosts"
    
    class Config:
        env_file = ".env"

settings = Settings() 