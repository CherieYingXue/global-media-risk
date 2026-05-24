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
    if not ENABLE_TUNNEL or sys.platform != "win32":
        return
    lock = BASE / "tunnel_manager.lock"
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
