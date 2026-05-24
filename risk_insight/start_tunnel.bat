@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist cloudflared.exe (
  echo 正在下载 cloudflared...
  python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe','cloudflared.exe')"
)
echo 启动公网隧道（Cloudflare Quick Tunnel）...
echo 请将下方 trycloudflare.com 链接保存到手机浏览器
cloudflared.exe tunnel --url http://127.0.0.1:8765
