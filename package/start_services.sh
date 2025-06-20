# 创建日志目录
mkdir -p /var/log/custom_scripts

# 添加日志记录函数
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> /var/log/custom_scripts/startup.log
}

log "开始执行服务启动脚本"

# 启动nginx
log "正在启动nginx服务"
nginx
if [ $? -eq 0 ]; then
  log "nginx启动成功"
else
  log "nginx启动失败，错误码: $?"
fi

# 在screen会话中启动ComfyUI (comfyui环境)
log "正在启动ComfyUI服务"
screen -d -m -D -L -Logfile /tmp/comfyui.log -S comfyui \
bash -l -c 'source $(conda info --base)/etc/profile.d/conda.sh; \
conda activate comfyui; \
cd /root/comfy/ComfyUI && python main.py'
if [ $? -eq 0 ]; then
  log "ComfyUI启动成功"
else
  log "ComfyUI启动失败，错误码: $?"
fi

# 在screen会话中启动另一个Python脚本 (base环境)
log "正在启动base环境的Python脚本"
screen -d -m -D -L -Logfile /tmp/base_app.log -S base_app \
bash -l -c 'source $(conda info --base)/etc/profile.d/conda.sh; \
conda activate base; \
cd /home/rlt && python run.py'
if [ $? -eq 0 ]; then
  log "base环境Python脚本启动成功"
else
  log "base环境Python脚本启动失败，错误码: $?"
fi

log "所有服务启动完成"

echo "所有服务已启动"
echo "使用 'screen -r comfyui' 查看ComfyUI日志"
echo "使用 'screen -r base_app' 查看base应用日志"
echo "启动日志位于 /var/log/custom_scripts/startup.log" 