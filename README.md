# AI Lora Training Platform

一个用于管理和自动化 AI 绘图 Lora 模型训练的平台系统。支持训练资产管理、任务调度、进度监控等功能。

## 功能特性

### 1. 资产管理
- 支持多训练节点管理
- SSH 远程连接配置
- 节点状态监控
- 并发任务数控制

### 2. 训练流程自动化
- 素材自动下载 (支持百度网盘)
- 数据标注处理
- Lora 模型训练
- 成品模型上传

### 3. 任务管理
- 可视化任务状态追踪
- 实时训练进度展示
- 训练日志实时查看
- 失败任务自动重试

### 4. 系统配置
- 灵活的训练参数配置
- 节点资源分配策略
- 调度间隔设置
- 并发限制控制

## 技术架构

### 后端
- Flask + SQLAlchemy
- WebSocket 实时通信
- 多线程任务调度
- 分布式任务处理

### 前端
- Vue 3 
- Vue Router
- 响应式界面设计
- 实时数据更新

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 14+
- SQLite/MySQL
- Redis (可选,用于任务队列)

### 安装部署

1. 克隆项目
bash```
git clone <repository_url>
cd ai-lora-training
```
2. 安装后端依赖
bash```
cd backend
pip install -r requirements.txt
```
3. 安装前端依赖
bash```
cd frontend
npm install
```
5. 启动服务
启动后端
python run.py
启动前端
npm run dev

## 系统架构

### 核心模块
- TaskQueue: 任务队列管理
- TaskScheduler: 调度器
- AssetManager: 资产管理
- TrainingService: 训练服务
- ConfigService: 配置管理

### 数据流
```
素材下载 -> 数据标注 -> 模型训练 -> 结果上传
```

### 状态流转
NEW -> SUBMITTED -> MARKING -> MARKED -> TRAINING -> COMPLETED


## 开发指南

### 添加新训练节点
1. 在资产管理中添加新节点
2. 配置SSH连接信息
3. 设置并发限制
4. 验证节点连接

### 自定义训练流程
1. 实现自定义TrainingHandler
2. 注册到TrainingService
3. 更新配置文件
4. 重启调度服务

## 常见问题

1. **任务卡在PENDING状态**
   - 检查节点连接状态
   - 确认并发限制设置
   - 查看错误日志

2. **训练失败自动重试**
   - 系统会自动重试失败任务
   - 最大重试次数可配置
   - 查看任务历史记录

## 维护说明

1. **日志管理**
   - 日志位于 logs/ 目录
   - 按日期自动轮转
   - 支持日志级别配置

2. **数据备份**
   - 定期备份数据库
   - 配置文件备份
   - 训练成果备份

## License

MIT License
