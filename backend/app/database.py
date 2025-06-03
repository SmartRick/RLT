from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .config import config
from .utils.logger import setup_logger
import sqlalchemy as sa

# 设置日志记录器
logger = setup_logger('database')

# 创建数据库引擎
engine = create_engine(config.DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

@contextmanager
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库"""
    # 导入所有模型以确保它们被注册
    from .models import task  # noqa
    from .models import training  # noqa
    from .models import asset  # noqa
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 检查并添加缺失的列
    inspector = sa.inspect(engine)
    try:
        # 检查tasks表是否存在
        if 'tasks' in inspector.get_table_names():
            # 获取tasks表的列
            columns = [col['name'] for col in inspector.get_columns('tasks')]
            
            # 如果status_history列不存在，添加它
            if 'status_history' not in columns:
                logger.info("添加 status_history 列到 tasks 表")
                with engine.begin() as conn:
                    conn.execute(sa.text(
                        "ALTER TABLE tasks ADD COLUMN status_history JSON DEFAULT '{}'"
                    ))
            
            # 如果started_at列不存在，添加它
            if 'started_at' not in columns:
                logger.info("添加 started_at 列到 tasks 表")
                with engine.begin() as conn:
                    conn.execute(sa.text(
                        "ALTER TABLE tasks ADD COLUMN started_at DATETIME"
                    ))
            
            # 如果completed_at列不存在，添加它
            if 'completed_at' not in columns:
                logger.info("添加 completed_at 列到 tasks 表")
                with engine.begin() as conn:
                    conn.execute(sa.text(
                        "ALTER TABLE tasks ADD COLUMN completed_at DATETIME"
                    ))
        
        # 检查assets表是否存在
        if 'assets' in inspector.get_table_names():
            # 获取assets表的列
            columns = [col['name'] for col in inspector.get_columns('assets')]
            
            # 如果is_local列不存在，添加它
            if 'is_local' not in columns:
                logger.info("添加 is_local 列到 assets 表")
                with engine.begin() as conn:
                    conn.execute(sa.text(
                        "ALTER TABLE assets ADD COLUMN is_local BOOLEAN DEFAULT 0"
                    ))
                    
                # 更新本地资产的is_local标志
                with engine.begin() as conn:
                    conn.execute(sa.text(
                        "UPDATE assets SET is_local = 1 WHERE name = '本地系统'"
                    ))
    except Exception as e:
        logger.error(f"检查和添加表列时出错: {str(e)}")
    
    # 初始化本地资产
    try:
        from .services.local_asset_service import LocalAssetService
        logger.info("正在初始化本地资产...")
        local_asset = LocalAssetService.init_local_asset()
        if local_asset:
            logger.info(f"本地资产初始化成功: ID={local_asset.id}, 名称={local_asset.name}")
        else:
            logger.warning("本地资产初始化失败")
    except Exception as e:
        logger.error(f"初始化本地资产时出错: {str(e)}", exc_info=True) 