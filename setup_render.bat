@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================
echo   代码已推送到 GitHub，请在 Render 完成部署
echo ============================================
echo.
echo 仓库: https://github.com/CherieYingXue/global-media-risk
echo.
echo 正在打开 Render 一键部署页面...
start "https://render.com/deploy?repo=https://github.com/CherieYingXue/global-media-risk"
echo.
echo 请按以下步骤操作:
echo   1. 点击 New Blueprint Instance
echo   2. 连接 GitHub 账号（若未连接）
echo   3. 选择仓库 CherieYingXue / global-media-risk
echo   4. 点击 Apply 并等待 5-10 分钟
echo.
echo 部署完成后手机访问:
echo   https://global-media-risk.onrender.com
echo.
pause
