@echo off
chcp 65001 > nul
title 项目服务启动器

echo ========================================
echo   正在启动项目服务...
echo ========================================

REM 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
echo 项目根目录: %SCRIPT_DIR%

REM 启动Python后端服务（新窗口）
echo 启动Python后端服务...
start "Python后端API服务" cmd /k "conda activate web && cd /d "%SCRIPT_DIR%code-annotation-backend-master" && echo [后端] 正在启动... && python run.py && echo [后端] 服务已停止 && pause"

REM 等待2秒确保后端服务初始化
timeout /t 2 /nobreak > nul

REM 启动前端开发服务器（新窗口）
echo 启动前端开发服务器...
start "前端开发服务器" cmd /k "cd /d "%SCRIPT_DIR%code-annotation-master" && echo [前端] 正在启动... && npm run serve && echo [前端] 服务已停止 && pause"

echo ========================================
echo   所有服务启动命令已执行！
echo   请检查打开的两个命令窗口
echo ========================================
echo 后端服务: http://localhost:5000 (或其他配置端口)
echo 前端服务: http://localhost:3000 (或其他配置端口)
echo ========================================

pause
