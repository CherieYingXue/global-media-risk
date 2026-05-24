# -*- coding: utf-8 -*-
"""读取公网/局域网访问地址。"""
from __future__ import annotations

import json
import os
import re
import socket
from datetime import datetime, timezone
from pathlib import Path

from config import ENABLE_TUNNEL, PORT, PUBLIC_BASE_URL

BASE_DIR = Path(__file__).resolve().parent
URL_FILE = BASE_DIR / "deploy_url.txt"
STATUS_FILE = BASE_DIR / "tunnel_status.json"


def _local_ip() -> str:
    candidates: list[str] = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip.startswith(("127.", "169.254.", "198.18.")):
                continue
            candidates.append(ip)
    except Exception:
        pass
    for ip in candidates:
        if ip.startswith(("192.168.", "10.")):
            return ip
    for ip in candidates:
        if ip.startswith("172.") and not ip.startswith("198.18."):
            return ip
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("114.114.114.114", 80))
        ip = s.getsockname()[0]
        s.close()
        if not ip.startswith("198.18."):
            return ip
    except Exception:
        pass
    return "127.0.0.1"


def _read_url_file() -> str | None:
    if not URL_FILE.exists():
        return None
    text = URL_FILE.read_text(encoding="utf-8").strip()
    m = re.search(r"https://[\w-]+\.(?:lhr\.life|serveousercontent\.com)", text)
    return m.group(0) if m else (text if text.startswith("http") else None)


def _read_status() -> dict:
    if not STATUS_FILE.exists():
        return {}
    try:
        return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _status_fresh(st: dict, max_age_sec: int = 300) -> bool:
    updated = st.get("updated_at")
    if not updated:
        return False
    try:
        ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        return age <= max_age_sec
    except Exception:
        return False


def get_access_info() -> dict:
    ip = _local_ip()
    deploy_mode = "cloud" if PUBLIC_BASE_URL else "local"

    if PUBLIC_BASE_URL:
        return {
            "public_url": PUBLIC_BASE_URL,
            "public_url_stored": PUBLIC_BASE_URL,
            "tunnel_alive": True,
            "tunnel_detail": "Render 云端",
            "deploy_mode": deploy_mode,
            "lan_url": f"http://{ip}:{PORT}",
            "local_url": f"http://127.0.0.1:{PORT}",
        }

    st = _read_status()
    url = st.get("url") or _read_url_file()
    connected = ENABLE_TUNNEL and bool(st.get("connected")) and _status_fresh(st)
    return {
        "public_url": url if url else None,
        "public_url_stored": url,
        "tunnel_alive": connected,
        "tunnel_detail": st.get("detail", ""),
        "deploy_mode": deploy_mode,
        "lan_url": f"http://{ip}:{PORT}",
        "local_url": f"http://127.0.0.1:{PORT}",
    }
