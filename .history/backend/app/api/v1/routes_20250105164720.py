"""
API 路由定义
GET /api/v1/tasks - 获取任务列表
POST /api/v1/tasks - 创建新任务
PUT /api/v1/tasks/{task_id} - 更新任务
DELETE /api/v1/tasks/{task_id} - 删除任务
GET /api/v1/tasks/{task_id}/log - 获取任务日志
GET /api/v1/tasks/stats - 获取任务统计

GET /api/v1/assets - 获取资产列表
POST /api/v1/assets - 创建新资产
PUT /api/v1/assets/{asset_id} - 更新资产
DELETE /api/v1/assets/{asset_id} - 删除资产
POST /api/v1/assets/{asset_id}/upload - 上传资产文件

GET /api/v1/settings - 获取系统配置
PUT /api/v1/settings - 更新系统配置

POST /api/v1/training/start - 开始训练
POST /api/v1/training/stop/{task_id} - 停止训练
GET /api/v1/training/status/{task_id} - 获取训练状态
""" 