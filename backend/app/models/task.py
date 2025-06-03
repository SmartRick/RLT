from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import Base
from ..utils.common import logger
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

    # 状态历史记录字段 - 简化结构
    status_history = Column(
        JSON,
        nullable=False,
        default=dict,
        comment='任务状态历史'
    )
    
    # 添加开始时间和结束时间
    started_at = Column(DateTime, comment='任务开始时间')
    completed_at = Column(DateTime, comment='任务完成时间')

    # 日志类型枚举，用于前端展示不同样式
    LOG_TYPE_INFO = "INFO"         # 普通信息
    LOG_TYPE_SUCCESS = "SUCCESS"   # 成功信息
    LOG_TYPE_WARNING = "WARNING"   # 警告信息
    LOG_TYPE_ERROR = "ERROR"       # 错误信息
    LOG_TYPE_PROGRESS = "PROGRESS" # 进度信息
    LOG_TYPE_SYSTEM = "SYSTEM"     # 系统信息

    def update_status(self, new_status: str, message: str = None):
        """
        更新任务状态并记录历史
        
        Args:
            new_status: 新状态
            message: 状态变更消息
            db: 数据库会话对象，如果提供则自动提交更改
        """
        now = datetime.now()
        old_status = self.status
        
        # 初始化状态历史
        if not self.status_history:
            self.status_history = {}
            
        # 如果是新状态，创建新的状态记录
        if new_status not in self.status_history:
            self.status_history[new_status] = {
                'start_time': now.isoformat(),
                'end_time': None,
                'duration': None,
                'logs': []
            }
            
        # 更新旧状态的结束时间和持续时间
        if old_status and old_status in self.status_history:
            self.status_history[old_status]['end_time'] = now.isoformat()
            # 计算状态持续时间（秒）
            try:
                start_time = datetime.fromisoformat(self.status_history[old_status]['start_time'])
                self.status_history[old_status]['duration'] = (now - start_time).total_seconds()
            except Exception:
                self.status_history[old_status]['duration'] = None
        
        # 更新任务状态
        self.status = new_status
        
        if message:
            # 根据状态选择日志类型
            log_type = self.LOG_TYPE_INFO
            if new_status == 'ERROR':
                log_type = self.LOG_TYPE_ERROR
            elif new_status == 'COMPLETED':
                log_type = self.LOG_TYPE_SUCCESS
            elif new_status in ['MARKED', 'TRAINING']:
                log_type = self.LOG_TYPE_SUCCESS
                
            # 添加自定义消息
            self.add_log(message, log_type=log_type)
        else:
            # 生成默认的状态变更消息
            default_message = f"任务状态从 {old_status or 'None'} 变更为 {new_status}"
            # 添加状态变更日志
            self.add_log(default_message, log_type=self.LOG_TYPE_SYSTEM)
        
        # 更新开始和结束时间
        if new_status in ['MARKING', 'TRAINING'] and not self.started_at:
            self.started_at = now
        elif new_status in ['MARKED', 'COMPLETED', 'ERROR']:
            self.completed_at = now

        logger.info(f"任务 {self.id} 状态更新为 {new_status}")

    def add_log(self, message: str, log_type: str = None, db: object = None):
        """
        添加日志到当前状态
        
        Args:
            message: 日志消息
            log_type: 日志类型
            db: 数据库会话对象，如果提供则自动提交更改
        """
        # 当前状态
        status = self.status
        
        # 如果没有指定日志类型，根据消息内容和状态猜测
        if log_type is None:
            if "错误" in message or "失败" in message:
                log_type = self.LOG_TYPE_ERROR
            elif "成功" in message or "完成" in message:
                log_type = self.LOG_TYPE_SUCCESS
            elif "%" in message or "进度" in message:
                log_type = self.LOG_TYPE_PROGRESS
            elif "警告" in message:
                log_type = self.LOG_TYPE_WARNING
            else:
                log_type = self.LOG_TYPE_INFO
        
        current_time = datetime.now()
        timestamp = current_time.isoformat()
        
        # 确保status_history是字典类型
        if not self.status_history:
            self.status_history = {}
        
        # 创建日志条目
        log_entry = {
            'time': timestamp,
            'message': message,
            'type': log_type
        }
            
        # 添加到对应状态的日志中
        if status not in self.status_history:
            self.status_history[status] = {
                'start_time': timestamp,
                'end_time': None,
                'duration': None,
                'logs': []
            }
            
        # 添加到状态特定日志
        self.status_history[status]['logs'].append(log_entry)
        logger.info(f"任务 {self.id} 日志更新为 {log_entry}")

    def add_progress_log(self, progress: int):
        """
        添加进度日志
        
        Args:
            progress: 进度百分比
            db: 数据库会话对象，如果提供则自动提交更改
        """
        message = f"当前进度: {progress}%"
        self.add_log(message, log_type=self.LOG_TYPE_PROGRESS)
        self.progress = progress
    
    def add_error_log(self, error_message: str, db: object = None):
        """
        添加错误日志
        
        Args:
            error_message: 错误消息
            db: 数据库会话对象，如果提供则自动提交更改
        """
        self.add_log(error_message, log_type=self.LOG_TYPE_ERROR)
        self.error_message = error_message
            
    def get_all_logs(self, limit: int = 100):
        """获取所有日志列表（按时间倒序排列）"""
        if not self.status_history:
            return []
            
        # 从所有状态中收集日志
        all_logs = []
        for status, data in self.status_history.items():
            logs = data.get('logs', [])
            for log in logs:
                # 添加状态信息以便前端区分
                log_with_status = log.copy()
                log_with_status['status'] = status
                all_logs.append(log_with_status)
        
        # 按时间排序（倒序）
        all_logs.sort(key=lambda x: x.get('time', ''), reverse=True)
        
        # 应用限制
        return all_logs[:limit]

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