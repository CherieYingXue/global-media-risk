@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo.
echo ============================================
echo   部署到 Render（需 GitHub 账号，一次性）
echo ============================================
echo.
echo 1. 在浏览器打开 GitHub 创建仓库:
start https://github.com/new?name=global-media-risk
echo    仓库名: global-media-risk （保持空仓库，不要勾选 README）
echo.
echo 2. 创建后在本窗口执行（把 YOUR_NAME 换成你的 GitHub 用户名）:
echo.
echo    git remote add origin https://github.com/YOUR_NAME/global-media-risk.git
echo    git push -u origin main
echo.
echo 3. 推送完成后，在 Render 一键部署:
start https://dashboard.render.com/blueprints
echo    选择 New Blueprint Instance ^> 连接仓库 ^> Apply
echo.
echo 部署完成后会得到固定链接，例如:
echo    https://global-media-risk.onrender.com
echo.
pause
