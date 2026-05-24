# -*- coding: utf-8 -*-
"""启动 Web 服务；本地可选 SSH 隧道，云端（Render）仅用公网域名。"""
import os
import subprocess
import sys
from pathlib import Path

import uvicorn

from app import app
from config import ENABLE_TUNNEL, HOST, PORT

BASE = Path(__file__).resolve().parent
_tunnel_proc = None


def start_tunnel_manager():
    global _tunnel_proc
    if not ENABLE_TUNNEL:
        return
    # 优先 Cloudflare Quick Tunnel（网络可用时更稳定；不可用则回退 serveo）
    cf_lock = BASE / "cloudflared_manager.lock"
    cf_bin = BASE / "cloudflared.exe"
    use_cf = os.getenv("USE_CLOUDFLARED", "auto").lower()
    cf_enabled = use_cf in ("true", "1", "yes") or (use_cf == "auto" and cf_bin.exists())
    if cf_enabled and cf_bin.exists():
        if cf_lock.exists():
            try:
                pid = int(cf_lock.read_text(encoding="utf-8").strip())
                import ctypes
                k = ctypes.windll.kernel32
                h = k.OpenProcess(0x1000, False, pid)
                if h:
                    k.CloseHandle(h)
                    print(f"Cloudflare 隧道已在运行 PID={pid}")
                    return
            except Exception:
                pass
        _tunnel_proc = subprocess.Popen(
            [sys.executable, str(BASE / "cloudflared_manager.py")],
            cwd=str(BASE),
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        print(f"已启动 Cloudflare 隧道 PID={_tunnel_proc.pid}")
        return
    lock = BASE / "tunnel_manager.lock"
    if sys.platform != "win32":
        return
    if lock.exists():
        try:
            pid = int(lock.read_text(encoding="utf-8").strip())
            import ctypes
            k = ctypes.windll.kernel32
            h = k.OpenProcess(0x1000, False, pid)
            if h:
                k.CloseHandle(h)
                print(f"隧道管理器已在运行 PID={pid}")
                return
        except Exception:
            pass
    if _tunnel_proc and _tunnel_proc.poll() is None:
        return
    _tunnel_proc = subprocess.Popen(
        [sys.executable, str(BASE / "tunnel_manager.py")],
        cwd=str(BASE),
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    print(f"已启动隧道管理器 PID={_tunnel_proc.pid}")


if __name__ == "__main__":
    start_tunnel_manager()
    port = int(os.getenv("PORT", str(PORT)))
    if os.getenv("RENDER"):
        print(f"Render 模式：公网地址见 RENDER_EXTERNAL_URL，端口 {port}")
    uvicorn.run(app, host=HOST, port=port, log_level="info")
