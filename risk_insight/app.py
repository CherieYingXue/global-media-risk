# -*- coding: utf-8 -*-
"""FastAPI 应用：手机端风险洞察界面。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from access_info import get_access_info
from config import (
    IS_CLOUD,
    REPORTS_DIR,
    SCHEDULE_HOUR,
    SCHEDULE_MINUTE,
    STATIC_DIR,
    TEMPLATES_DIR,
    TIMEZONE,
)
from report_generator import load_latest_report
from report_job import get_job_status, start_report_job

app = FastAPI(title="全球媒体风险洞察", version="1.0.0")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

scheduler = BackgroundScheduler(timezone=TIMEZONE)


def _scheduled_job():
    try:
        print(f"[定时任务] {datetime.now(ZoneInfo(TIMEZONE))} 开始生成报告…")
        from report_job import run_report_job_sync
        run_report_job_sync()
    except Exception as e:
        print(f"[定时任务] 失败: {e}")


@app.on_event("startup")
def startup():
    if not scheduler.running:
        scheduler.add_job(
            _scheduled_job,
            CronTrigger(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE, timezone=TIMEZONE),
            id="daily_report",
            replace_existing=True,
        )
        scheduler.add_job(
            _scheduled_job,
            CronTrigger(minute=0, timezone=TIMEZONE),
            id="hourly_report",
            replace_existing=True,
        )
        scheduler.start()
        print(
            f"已启动定时任务：每小时整点 + 每日 {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} ({TIMEZONE})"
        )

    if IS_CLOUD and not load_latest_report():
        print("[启动] 云端首次运行，后台生成首份报告…")
        start_report_job()


@app.on_event("shutdown")
def shutdown():
    if scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    report = load_latest_report()
    access = get_access_info()
    return templates.TemplateResponse(
        request,
        "index.html",
        {"report": report, "access": access},
    )


@app.get("/link", response_class=HTMLResponse)
async def link_page(request: Request):
    access = get_access_info()
    return templates.TemplateResponse(
        request,
        "link.html",
        {"access": access},
    )


@app.get("/api/access-info")
async def api_access_info():
    return get_access_info()


@app.get("/api/report/latest")
async def api_latest():
    report = load_latest_report()
    if not report:
        return JSONResponse({"error": "暂无报告，请先生成"}, status_code=404)
    return report


def _no_cache_json(data: dict) -> JSONResponse:
    return JSONResponse(
        data,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@app.get("/api/report/status")
async def api_report_status():
    return _no_cache_json(get_job_status())


@app.get("/api/report/refresh")
async def api_refresh():
    """GET 触发刷新（公网隧道对 POST 常返回 502）。"""
    return _no_cache_json(start_report_job())


@app.post("/api/report/generate")
async def api_generate():
    """兼容旧版 POST 调用。"""
    return _no_cache_json(start_report_job())


@app.get("/api/report/{date}")
async def api_by_date(date: str):
    path = REPORTS_DIR / f"report_{date}.json"
    if not path.exists():
        return JSONResponse({"error": "未找到该日报告"}, status_code=404)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@app.get("/health")
async def health():
    report = load_latest_report()
    return {
        "status": "ok",
        "has_report": report is not None,
        "generated_at": report.get("generated_at") if report else None,
    }
