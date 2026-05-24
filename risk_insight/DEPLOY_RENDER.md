# 部署到 Render（稳定公网，无需 SSH 隧道）

Render 提供固定 HTTPS 地址（如 `https://global-media-risk.onrender.com`），手机随时可访问，不会像 serveo 隧道那样频繁断开。

## 一、准备工作

1. 注册 [Render](https://render.com)（可用 GitHub 登录）
2. 注册 [GitHub](https://github.com) 并安装 Git
3. 本目录已包含：
   - 根目录 `render.yaml`（一键部署配置）
   - `risk_insight/data/media_sources.xlsx`（媒体列表，已打包）

## 二、把代码推到 GitHub

在项目根目录 `全球信源cursor整理` 打开终端，执行：

```bash
git init
git add .
git commit -m "全球媒体风险洞察 - Render 部署"
```

在 GitHub 新建空仓库（例如 `global-media-risk`），然后：

```bash
git remote add origin https://github.com/你的用户名/global-media-risk.git
git branch -M main
git push -u origin main
```

## 三、在 Render 创建服务

### 方式 A：Blueprint（推荐）

1. 登录 Render → **Blueprints** → **New Blueprint Instance**
2. 连接刚创建的 GitHub 仓库
3. Render 会读取根目录 `render.yaml`，自动创建 **Web 服务**
4. 点击 **Apply**，等待约 5–10 分钟部署完成

### 方式 B：手动创建 Web 服务

1. **New** → **Web Service** → 连接 GitHub 仓库
2. 设置：
   - **Root Directory**：`risk_insight`
   - **Runtime**：Python 3
   - **Build Command**：`pip install -r requirements.txt`
   - **Start Command**：`python run.py`
   - **Health Check Path**：`/health`
3. 环境变量（Environment）：

   | Key | Value |
   |-----|-------|
   | `RENDER` | `true` |
   | `ENABLE_TUNNEL` | `false` |
   | `TZ` | `Asia/Shanghai` |

4. **Create Web Service**

## 四、获取手机链接

部署成功后，Render 会显示：

```text
https://global-media-risk.onxxxx.onrender.com
```

将此链接存到手机书签即可。页面底部也会显示同一地址。

## 五、使用说明

| 功能 | 说明 |
|------|------|
| 手动刷新 | 点击页面底部按钮，约 1–2 分钟完成 |
| 自动更新 | 服务运行中每小时整点自动刷新 |
| 免费版限制 | 15 分钟无人访问会休眠，首次打开约需等待 30–60 秒唤醒 |
| 更新媒体列表 | 修改 `risk_insight/data/media_sources.xlsx` 后 `git push`，Render 自动重新部署 |

## 六、可选：减少休眠 + 定时刷新

免费实例空闲会休眠。可任选：

- [UptimeRobot](https://uptimerobot.com) 每 10 分钟访问 `https://你的域名.onrender.com/health`（保持唤醒）
- 每 60 分钟访问 `https://你的域名.onrender.com/api/report/refresh`（定时生成报告）
- 或升级 Render 付费计划（实例常开）

## 七、更新 Excel 媒体表

1. 编辑上级目录 `各国主流媒体网站.xlsx`
2. 复制到部署目录：
   ```bash
   copy "各国主流媒体网站.xlsx" "risk_insight\data\media_sources.xlsx"
   ```
3. `git add` → `git commit` → `git push`

## 八、本地运行（仍可用）

```bash
cd risk_insight
pip install -r requirements.txt
python run.py
```

本地仍可用 `deploy.bat` + 隧道；云端部署后一般不再需要隧道。
