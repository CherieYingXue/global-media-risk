# -*- coding: utf-8 -*-
"""公网隧道管理：serveo.net 优先，localhost.run 备用，单实例运行。"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
URL_FILE = BASE_DIR / "deploy_url.txt"
STATUS_FILE = BASE_DIR / "tunnel_status.json"
LOG_FILE = BASE_DIR / "tunnel.log"
LOCK_FILE = BASE_DIR / "tunnel_manager.lock"
LOCAL_HEALTH = "http://127.0.0.1:8765/health"

BACKENDS = [
    {
        "name": "serveo",
        "cmd": (
            "ssh -o StrictHostKeyChecking=no "
            "-o ServerAliveInterval=20 -o ServerAliveCountMax=3 "
            "-o ExitOnForwardFailure=yes -o TCPKeepAlive=yes "
            "-o ConnectTimeout=30 "
            "-R 80:127.0.0.1:8765 serveo.net"
        ),
        "pattern": re.compile(r"https://[\w-]+\.serveousercontent\.com"),
    },
    {
        "name": "localhost.run",
        "cmd": (
            "ssh -o StrictHostKeyChecking=no "
            "-o ServerAliveInterval=20 -o ServerAliveCountMax=3 "
            "-o ExitOnForwardFailure=yes -o TCPKeepAlive=yes "
            "-o ConnectTimeout=30 "
            "-R 80:127.0.0.1:8765 nokey@localhost.run"
        ),
        "pattern": re.compile(r"https://[\w-]+\.lhr\.life"),
    },
]


def log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def write_status(url: str | None, connected: bool, detail: str = "") -> None:
    data = {
        "url": url,
        "connected": connected,
        "detail": detail,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    STATUS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if url and connected:
        URL_FILE.write_text(url + "\n", encoding="utf-8")


def _pid_alive(pid: int) -> bool:
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)
        if h:
            k.CloseHandle(h)
            return True
    except Exception:
        pass
    return False


def acquire_singleton_lock() -> bool:
    if LOCK_FILE.exists():
        try:
            if _pid_alive(int(LOCK_FILE.read_text(encoding="utf-8").strip())):
                return False
        except Exception:
            pass
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True


def release_singleton_lock() -> None:
    try:
        if LOCK_FILE.exists() and LOCK_FILE.read_text(encoding="utf-8").strip() == str(os.getpid()):
            LOCK_FILE.unlink()
    except Exception:
        pass


def wait_local_server(timeout: int = 90) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests.get(LOCAL_HEALTH, timeout=3).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def verify_tunnel(url: str) -> bool:
    try:
        r = requests.get(f"{url.rstrip('/')}/health", timeout=20)
        if "no tunnel here" in r.text.lower():
            return False
        return r.status_code == 200
    except Exception:
        return False


def run_backend(backend: dict) -> str | None:
    name = backend["name"]
    log(f"尝试隧道后端: {name}")
    write_status(None, False, f"connecting {name}")

    proc = subprocess.Popen(
        backend["cmd"],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    found: list[str] = []
    pat = backend["pattern"]

    def reader():
        assert proc.stdout is not None
        for line in proc.stdout:
            clean = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
            if not clean:
                continue
            if "http" in clean or "Forwarding" in clean or "lhr.life" in clean:
                log(f"[{name}] {clean[:120]}")
            m = pat.search(clean)
            if m and not found:
                found.append(m.group(0))

    threading.Thread(target=reader, daemon=True).start()

    deadline = time.time() + 90
    while time.time() < deadline and not found:
        if proc.poll() is not None:
            log(f"[{name}] SSH 退出 code={proc.returncode}")
            return None
        time.sleep(0.5)

    if not found:
        proc.kill()
        log(f"[{name}] 超时未获取链接")
        return None

    public_url = found[0]
    write_status(public_url, True, f"connected via {name}")
    log(f"隧道就绪 ({name}): {public_url}")

    time.sleep(2)
    if verify_tunnel(public_url):
        write_status(public_url, True, "verified")

    while proc.poll() is None:
        time.sleep(45)
        if proc.poll() is not None:
            break
        if not verify_tunnel(public_url):
            log(f"[{name}] 隧道失效，重连")
            proc.kill()
            write_status(public_url, False, "dead")
            break
        write_status(public_url, True, "ok")

    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()

    write_status(public_url, False, "disconnected")
    return public_url


def run_tunnel_loop() -> None:
    idx = 0
    while True:
        backend = BACKENDS[idx % len(BACKENDS)]
        idx += 1
        try:
            run_backend(backend)
        except Exception as e:
            log(f"异常: {e}")
        time.sleep(3)


def main() -> None:
    if not acquire_singleton_lock():
        sys.exit(0)
    log("=== 隧道管理器启动 ===")
    if not wait_local_server():
        log("Web 服务未运行")
        release_singleton_lock()
        sys.exit(1)
    try:
        run_tunnel_loop()
    finally:
        release_singleton_lock()


if __name__ == "__main__":
    main()
