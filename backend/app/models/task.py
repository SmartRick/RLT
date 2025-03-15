from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import Base

class TaskImage(Base):
    """任务图片模型"""
    __tablename__ = 'task_images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    preview_url = Column(String(500))
    size = Column(Integer)  # 文件大小(字节)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'preview_url': self.preview_url,
            'size': self.size,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(Base):
    """训练任务模型"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='任务名称')
    description = Column(Text, nullable=True, comment='任务描述')
    status = Column(Enum(
        'NEW',         # 新建
        'SUBMITTED',   # 已提交
        'MARKING',     # 标记中
        'MARKED',      # 已标记
        'TRAINING',    # 训练中
        'COMPLETED',   # 已完成
        'ERROR'        # 错误
    ), nullable=False, default='NEW', comment='任务状态')
    progress = Column(Integer, default=0, comment='进度百分比')
    log_file = Column(String(500), comment='日志文件路径')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    prompt_id = Column(String(50))  # 存储ComfyUI的prompt_id

    # 资产关联
    marking_asset_id = Column(Integer, ForeignKey('assets.id'), comment='标记资产ID')
    training_asset_id = Column(Integer, ForeignKey('assets.id'), comment='训练资产ID')
    
    # 关联关系
    marking_asset = relationship('Asset', foreign_keys=[marking_asset_id])
    training_asset = relationship('Asset', foreign_keys=[training_asset_id])

    # 关联图片
    images = relationship('TaskImage', cascade='all, delete-orphan')

    # 添加状态历史记录字段
    status_history = Column(
        JSON,
        nullable=False,
        default=dict,
        comment='任务状态历史'
    )
    
    # 添加开始时间和结束时间
    started_at = Column(DateTime, comment='任务开始时间')
    completed_at = Column(DateTime, comment='任务完成时间')

    def update_status(self, new_status: str, message: str = None):
        """更新任务状态并记录历史"""
        now = datetime.now()
        old_status = self.status
        
        # 初始化状态历史
        if not self.status_history:
            self.status_history = []
            
        # 如果是新状态，创建新的状态记录
        if new_status not in self.status_history:
            self.status_history[new_status] = {
                'start_time': now.isoformat(),
                'end_time': None,
                'logs': []
            }
            
        # 更新旧状态的结束时间
        if old_status and old_status in self.status_history:
            self.status_history[old_status]['end_time'] = now.isoformat()
        
        # 更新任务状态
        self.status = new_status
        
        # 如果有消息，添加到新状态的日志中
        if message:
            self.add_log(message, new_status)
        
        # 更新开始和结束时间
        if new_status in ['MARKING', 'TRAINING'] and not self.started_at:
            self.started_at = now
        elif new_status in ['MARKED', 'COMPLETED', 'ERROR']:
            self.completed_at = now

    def add_log(self, message: str, status: str = None):
        """添加日志到当前状态"""
        # 如果没有指定状态，使用当前状态
        target_status = status or self.status
        
        if target_status and target_status in self.status_history:
            current_time = datetime.now().isoformat()
            self.status_history[target_status]['logs'].append({
                'time': current_time,
                'message': message
            })
        else:
            # 如果状态不存在，创建新的状态记录
            self.status_history[target_status] = {
                'start_time': current_time,
                'end_time': None,
                'logs': [{
                    'time': current_time,
                    'message': message
                }]
            }

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status_history': self.status_history,
            'images': [img.to_dict() for img in self.images],
            'marking_asset': self.marking_asset.to_dict() if self.marking_asset else None,
            'training_asset': self.training_asset.to_dict() if self.training_asset else None
        } 