@echo off
chcp 65001 >nul
echo 同步媒体列表到部署目录...
copy /Y "%~dp0..\各国主流媒体网站.xlsx" "%~dp0data\media_sources.xlsx"
if errorlevel 1 (
  echo 复制失败，请确认 Excel 文件存在
  pause
  exit /b 1
)
echo 已更新 risk_insight\data\media_sources.xlsx
pause
