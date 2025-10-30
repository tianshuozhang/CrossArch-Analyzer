#!/bin/bash

# 同时启动Python后端和前端服务的Shell脚本

echo "正在启动服务..."

# 启动Python后端服务（第一个终端）
gnome-terminal --title="Python后端" -- bash -c "cd /code-annotation-backend-master && echo '启动Python后端服务...' && python run.py; exec bash"

# 等待2秒确保第一个终端完全启动
sleep 2

# 启动前端服务（第二个终端）
gnome-terminal --title="前端服务" -- bash -c "cd /code-annotation-master && echo '启动前端开发服务器...' && npm run serve; exec bash"

echo "服务启动命令已执行，请检查打开的终端窗口"
