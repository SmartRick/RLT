from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import assets, training, tasks
from .config import settings
from .database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(assets.router, prefix=settings.API_V1_STR)
app.include_router(training.router, prefix=settings.API_V1_STR)
app.include_router(tasks.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to Lora Training Manager"} 