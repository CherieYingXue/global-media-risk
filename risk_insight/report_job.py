# -*- coding: utf-8 -*-
"""后台报告生成任务（避免公网隧道长连接超时）。"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from config import TIMEZONE
from report_generator import generate_report

_lock = threading.Lock()
_state: dict[str, Any] = {
    "status": "idle",
    "message": "",
    "items": 0,
    "generated_at": None,
    "error": None,
    "started_at": None,
    "finished_at": None,
}


def _snapshot() -> dict[str, Any]:
    with _lock:
        return dict(_state)


def get_job_status() -> dict[str, Any]:
    return _snapshot()


def start_report_job() -> dict[str, Any]:
    with _lock:
        if _state["status"] == "running":
            return {
                "ok": True,
                "status": "running",
                "message": "报告正在生成中，请稍候…",
            }
        _state.update(
            status="running",
            message="正在采集全球媒体…",
            items=0,
            generated_at=None,
            error=None,
            started_at=datetime.now(ZoneInfo(TIMEZONE)).isoformat(),
            finished_at=None,
        )

    def worker() -> None:
        try:
            with _lock:
                _state["message"] = "正在分析风险信号并翻译标题…"
            report = generate_report()
            with _lock:
                _state.update(
                    status="done",
                    message="报告生成完成",
                    items=len(report["items"]),
                    generated_at=report["generated_at"],
                    finished_at=datetime.now(ZoneInfo(TIMEZONE)).isoformat(),
                    error=None,
                )
        except Exception as e:
            with _lock:
                _state.update(
                    status="error",
                    message="生成失败",
                    error=str(e),
                    finished_at=datetime.now(ZoneInfo(TIMEZONE)).isoformat(),
                )

    threading.Thread(target=worker, daemon=True, name="report-job").start()
    return {
        "ok": True,
        "status": "running",
        "message": "已开始生成，预计需要 1–2 分钟…",
    }


def run_report_job_sync() -> None:
    """供定时任务调用：启动并等待后台任务完成。"""
    start_report_job()
    for _ in range(180):
        st = get_job_status()
        if st["status"] == "done":
            return
        if st["status"] == "error":
            raise RuntimeError(st.get("error") or "report job failed")
        threading.Event().wait(2)
