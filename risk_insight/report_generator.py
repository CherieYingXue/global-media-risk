# -*- coding: utf-8 -*-
"""生成并保存每日风险报告。"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer import analyze_batch, build_report_meta
from collector import collect_all
from config import REPORTS_DIR, TIMEZONE
from media_loader import load_media_sources
from translator import enrich_items_with_translation


async def generate_report_async() -> dict:
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)
    sources = load_media_sources()

    print(f"[{now.isoformat()}] 开始采集 {len(sources)} 家媒体…")
    articles = await collect_all(sources, hours=24)
    print(f"  采集到 {len(articles)} 条近24小时报道")

    items = analyze_batch(articles)
    print(f"  识别对中国构成风险的信号 {len(items)} 条")

    items = enrich_items_with_translation(items)
    print(f"  已完成标题中文翻译")

    meta = build_report_meta(items)

    report = {
        "generated_at": now.isoformat(),
        "generated_at_display": now.strftime("%Y年%m月%d日 %H:%M"),
        "period": "过去24小时",
        "timezone": TIMEZONE,
        "media_scanned": len(sources),
        "articles_collected": len(articles),
        "summary": meta,
        "items": items,
    }

    date_key = now.strftime("%Y-%m-%d")
    report_path = REPORTS_DIR / f"report_{date_key}.json"
    latest_path = REPORTS_DIR / "latest.json"

    # 序列化时去掉 datetime 对象
    for item in report["items"]:
        item.pop("published_dt", None)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"  报告已保存: {report_path}")
    return report


def generate_report() -> dict:
    return asyncio.run(generate_report_async())


def load_latest_report() -> dict | None:
    latest = REPORTS_DIR / "latest.json"
    if not latest.exists():
        return None
    with open(latest, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    generate_report()
