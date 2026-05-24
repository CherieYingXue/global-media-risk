# 全球媒体风险洞察

## 推荐：Render 云端部署（稳定公网）

详见 **[DEPLOY_RENDER.md](./DEPLOY_RENDER.md)** — 固定 HTTPS 地址，无需 SSH 隧道，手机随时访问。

## 本地 + 隧道（易断开，不推荐长期使用）

最新隧道链接见 `deploy_url.txt` 或页面底部。断开后双击 `deploy.bat` 重建。

## 同一 WiFi

http://192.168.1.41:8765

## 一键部署

```
deploy.bat
```

自动启动 Web 服务 + 隧道守护（serveo 优先，断线重连）

## 故障排除

出现 **no tunnel here** 时：
1. 双击 `deploy.bat`
2. 使用 `deploy_url.txt` 中的最新链接（不要用旧书签）
