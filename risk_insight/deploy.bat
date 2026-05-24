@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 检查 Web 服务...
python -c "import requests; requests.get('http://127.0.0.1:8765/health',timeout=3).raise_for_status()" 2>nul
if errorlevel 1 (
  echo 启动 Web 服务 + 隧道...
  start "RiskInsight" /MIN python run.py
  timeout /t 8 /nobreak >nul
) else (
  echo Web 服务已运行，启动隧道...
  start "RiskInsight-Tunnel" /MIN python tunnel_manager.py
  timeout /t 5 /nobreak >nul
)

echo 等待公网链接...
timeout /t 40 /nobreak >nul

echo.
echo ===== 手机访问链接 =====
if exist deploy_url.txt (
  type deploy_url.txt
) else (
  echo 公网链接生成中，请稍候再运行本脚本
)
echo.
python -c "from access_info import get_access_info; i=get_access_info(); print('局域网:', i['lan_url'])"
echo ========================
pause
