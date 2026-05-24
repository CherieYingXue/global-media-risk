# -*- coding: utf-8 -*-
"""公网隧道守护：自动建立 localhost.run 隧道，断线重连，写入 deploy_url.txt。"""
from __future__ import annotations

import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
URL_FILE = BASE_DIR / "deploy_url.txt"
LOG_FILE = BASE_DIR / "tunnel.log"
LOCAL_HEALTH = "http://127.0.0.1:8765/health"
SSH_CMD = [
    "ssh",
    "-o", "StrictHostKeyChecking=no",
    "-o", "ServerAliveInterval=30",
    "-o", "ServerAliveCountMax=6",
    "-o", "ExitOnForwardFailure=yes",
    "-o", "TCPKeepAlive=yes",
    "-R", "80:127.0.0.1:8765",
    "nokey@localhost.run",
]
URL_PATTERN = re.compile(r"https://[\w-]+\.lhr\.life")


def log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def wait_local_server(timeout: int = 60) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(LOCAL_HEALTH, timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def check_public_url(url: str) -> bool:
    try:
        r = requests.get(f"{url.rstrip('/')}/health", timeout=12)
        if r.status_code == 200 and '"status":"ok"' in r.text.replace(" ", ""):
            return True
        if "no tunnel here" in r.text.lower():
            return False
    except Exception:
        return False
    return False


def save_url(url: str) -> None:
    URL_FILE.write_text(url.strip() + "\n", encoding="utf-8")
    log(f"公网链接已更新: {url}")


def _read_stdout(proc: subprocess.Popen, found: list[str]) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        log(f"ssh> {line}")
        m = URL_PATTERN.search(line)
        if m:
            found.append(m.group(0))
            save_url(m.group(0))


def run_tunnel_once() -> str | None:
    log("正在建立 SSH 隧道 (localhost.run)…")
    proc = subprocess.Popen(
        SSH_CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    found: list[str] = []
    reader = threading.Thread(target=_read_stdout, args=(proc, found), daemon=True)
    reader.start()

    deadline = time.time() + 45
    while time.time() < deadline and not found:
        if proc.poll() is not None:
            break
        time.sleep(0.5)

    if not found:
        log("未在 45 秒内获取公网链接")
        proc.kill()
        proc.wait(timeout=5)
        return None

    public_url = found[0]
    log(f"隧道就绪: {public_url}")

    while proc.poll() is None:
        time.sleep(25)
        if proc.poll() is not None:
            log("SSH 连接断开")
            break
        if not check_public_url(public_url):
            log("公网健康检查失败，主动重连")
            proc.kill()
            break

    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()

    return public_url


def main() -> None:
    log("=== 隧道守护启动 ===")
    if not wait_local_server():
        log("错误: 本地 Web 服务 (8765) 未运行，请先执行 start_server.bat")
        sys.exit(1)

    while True:
        try:
            run_tunnel_once()
        except Exception as e:
            log(f"隧道异常: {e}")
        log("5 秒后重连…")
        time.sleep(5)


if __name__ == "__main__":
    main()
