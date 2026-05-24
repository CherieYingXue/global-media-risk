# -*- coding: utf-8 -*-
"""一键部署：Web 服务 + 隧道。"""
import subprocess
import sys
import time
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent


def wait_server(timeout=20) -> bool:
    for _ in range(timeout):
        try:
            if requests.get("http://127.0.0.1:8765/health", timeout=2).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def wait_tunnel(timeout=60) -> str | None:
    status_file = BASE / "tunnel_status.json"
    for _ in range(timeout):
        if status_file.exists():
            import json
            st = json.loads(status_file.read_text(encoding="utf-8"))
            if st.get("connected") and st.get("url"):
                return st["url"]
        time.sleep(1)
    url_file = BASE / "deploy_url.txt"
    if url_file.exists():
        return url_file.read_text(encoding="utf-8").strip()
    return None


def main():
    print("=" * 44)
    print("  全球媒体风险洞察 - 部署")
    print("=" * 44)

    if not wait_server():
        print("[..] 启动服务...")
        subprocess.Popen(
            [sys.executable, str(BASE / "run.py")],
            cwd=str(BASE),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        if not wait_server(25):
            print("[错误] Web 服务启动失败")
            input("按回车退出...")
            return

    print("[OK] Web 服务运行中")
    print("[..] 等待公网隧道...")

    url = wait_tunnel(60)
    from access_info import get_access_info
    info = get_access_info()

    print()
    print("=" * 44)
    print("  手机访问链接")
    print("=" * 44)
    if url:
        print(f"  公网: {url}")
    else:
        print("  公网: 仍在建立，请查看 deploy_url.txt")
    print(f"  局域网: {info['lan_url']}")
    print("=" * 44)
    input("\n按回车关闭...")


if __name__ == "__main__":
    main()
