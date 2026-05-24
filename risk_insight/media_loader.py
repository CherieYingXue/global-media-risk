# -*- coding: utf-8 -*-
"""从 Excel 加载媒体列表。"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import pandas as pd

from config import MEDIA_EXCEL, MAX_MEDIA_PER_RUN


@dataclass
class MediaSource:
    url: str
    name: str
    language: str
    country: str

    @property
    def domain(self) -> str:
        return urlparse(self.url).netloc.replace("www.", "")


def load_media_sources(limit: int | None = MAX_MEDIA_PER_RUN) -> list[MediaSource]:
    if not MEDIA_EXCEL.exists():
        raise FileNotFoundError(f"未找到媒体列表: {MEDIA_EXCEL}")

    df = pd.read_excel(MEDIA_EXCEL, sheet_name="主流媒体列表")
    sources: list[MediaSource] = []
    seen_domains: set[str] = set()

    for _, row in df.iterrows():
        url = str(row["网站"]).strip()
        domain = urlparse(url).netloc.replace("www.", "")
        if domain in seen_domains:
            continue
        seen_domains.add(domain)
        sources.append(
            MediaSource(
                url=url,
                name=str(row["媒体"]).strip(),
                language=str(row["文种"]).strip(),
                country=str(row["国家"]).strip(),
            )
        )

    # 优先非中国媒体（外部视角对中国风险更相关），再补充中国媒体
    foreign = [s for s in sources if s.country != "中国"]
    domestic = [s for s in sources if s.country == "中国"]
    ordered = foreign + domestic

    if limit:
        return ordered[:limit]
    return ordered
