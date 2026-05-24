@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 启动 Web 服务 + 隧道管理器...
python run.py
