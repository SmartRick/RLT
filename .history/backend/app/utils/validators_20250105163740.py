from typing import Dict, Any, List
from ..middleware.error_handler import ValidationError
from ..config import config

def validate_task_create(data: Dict[str, Any]) -> None:
    """验证创建任务的数据"""
    required_fields = ['folder_name', 'asset_id']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
            
    if not isinstance(data['folder_name'], str):
        raise ValidationError("folder_name must be a string")
        
    if not isinstance(data['asset_id'], str):
        raise ValidationError("asset_id must be a string")

def validate_asset_create(data: Dict[str, Any]) -> None:
    """验证创建资产的数据"""
    required_fields = ['name', 'folder_name']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")

def validate_file_upload(files: List[Any]) -> None:
    """验证文件上传"""
    if not files:
        raise ValidationError("No files were uploaded")
        
    allowed_extensions = config.DEFAULT_CONFIG['allowed_file_types']
    max_size = config.DEFAULT_CONFIG['max_file_size']
    
    for file in files:
        # 检查文件扩展名
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError(f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}")
            
        # 检查文件大小
        if file.content_length > max_size:
            raise ValidationError(f"File too large. Maximum size: {max_size/1024/1024}MB") 