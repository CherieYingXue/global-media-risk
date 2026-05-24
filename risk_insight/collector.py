# -*- coding: utf-8 -*-
"""新闻采集：RSS + Google News 站点搜索。"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import quote_plus, urlparse

import feedparser
import httpx

from config import FETCH_CONCURRENCY, REQUEST_TIMEOUT, USER_AGENT
from media_loader import MediaSource

# 已知 RSS 直链（提高命中率）
KNOWN_FEEDS: dict[str, list[str]] = {
    "bbc.com": ["https://feeds.bbci.co.uk/news/world/rss.xml"],
    "reuters.com": ["https://www.reutersagency.com/feed/"],
    "theguardian.com": ["https://www.theguardian.com/world/rss"],
    "nytimes.com": ["https://rss.nytimes.com/services/xml/rss/nyt/World.xml"],
    "cnn.com": ["http://rss.cnn.com/rss/edition_world.rss"],
    "aljazeera.com": ["https://www.aljazeera.com/xml/rss/all.xml"],
    "dw.com": ["https://rss.dw.com/xml/rss-en-world"],
    "france24.com": ["https://www.france24.com/en/rss"],
    "spiegel.de": ["https://www.spiegel.de/international/index.rss"],
    "asahi.com": ["https://www.asahi.com/rss/asahi/newsheadlines.rdf"],
    "straitstimes.com": ["https://www.straitstimes.com/news/world/rss.xml"],
    "scmp.com": ["https://www.scmp.com/rss/91/feed"],
    "timesofindia.indiatimes.com": ["https://timesofindia.indiatimes.com/rssfeedstopstories.cms"],
    "thehindu.com": ["https://www.thehindu.com/news/international/feeder/default.rss"],
    "globo.com": ["https://oglobo.globo.com/rss/"],
    "detik.com": ["https://rss.detik.com/index.php/detikcom"],
    "kompas.com": ["https://www.kompas.com/rss"],
    "abc.net.au": ["https://www.abc.net.au/news/feed/51120/rss.xml"],
    "nzherald.co.nz": ["https://www.nzherald.co.nz/arc/outboundfeeds/rss/"],
    "jpost.com": ["https://www.jpost.com/rss/rssfeedsfrontpage.aspx"],
    "haaretz.com": ["https://www.haaretz.com/srv/rss"],
    "rt.com": ["https://www.rt.com/rss/"],
    "people.com.cn": ["http://www.people.com.cn/rss/politics.xml"],
    "xinhuanet.com": ["http://www.xinhuanet.com/politics/news_politics.xml"],
}

COMMON_FEED_PATHS = ["/rss", "/feed", "/index.xml", "/rss.xml", "/feeds/rss"]


def _parse_dt(entry: dict[str, Any]) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        tp = entry.get(key)
        if tp:
            try:
                return datetime(*tp[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    for key in ("published", "updated"):
        val = entry.get(key)
        if not val:
            continue
        try:
            dt = parsedate_to_datetime(val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass
    return None


def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _entry_to_article(entry: dict[str, Any], source: MediaSource, feed_url: str) -> dict | None:
    title = _clean_html(entry.get("title", ""))
    link = entry.get("link") or entry.get("id") or ""
    if not title or not link:
        return None
    summary = _clean_html(entry.get("summary", entry.get("description", "")))
    published = _parse_dt(entry)
    return {
        "title": title,
        "summary": summary[:500],
        "url": link,
        "published": published.isoformat() if published else None,
        "published_dt": published,
        "media": source.name,
        "media_url": source.url,
        "country": source.country,
        "language": source.language,
        "source_feed": feed_url,
    }


def _google_news_feed(source: MediaSource, query: str) -> str:
    q = quote_plus(f"site:{source.domain} ({query}) when:1d")
    return (
        f"https://news.google.com/rss/search?q={q}"
        f"&hl=en-US&gl=US&ceid=US:en"
    )


def _feed_candidates(source: MediaSource) -> list[str]:
    urls: list[str] = []
    domain = source.domain
    if domain in KNOWN_FEEDS:
        urls.extend(KNOWN_FEEDS[domain])
    base = source.url.rstrip("/")
    for path in COMMON_FEED_PATHS:
        urls.append(base + path)
    # Google News 作为兜底：搜索中国相关及风险词
    urls.append(_google_news_feed(source, "China OR Chinese OR Beijing OR 中国 OR 制裁 OR conflict"))
    return urls


async def _fetch_feed(client: httpx.AsyncClient, feed_url: str) -> feedparser.FeedParserDict:
    try:
        resp = await client.get(feed_url, timeout=REQUEST_TIMEOUT)
        if resp.status_code >= 400:
            return feedparser.parse("")
        return feedparser.parse(resp.content)
    except Exception:
        return feedparser.parse("")


async def collect_from_source(
    client: httpx.AsyncClient,
    source: MediaSource,
    since: datetime,
) -> list[dict]:
    articles: list[dict] = []
    seen_urls: set[str] = set()

    for feed_url in _feed_candidates(source):
        parsed = await _fetch_feed(client, feed_url)
        if not parsed.entries:
            continue
        for entry in parsed.entries[:15]:
            item = _entry_to_article(entry, source, feed_url)
            if not item:
                continue
            pub = item.get("published_dt")
            if pub and pub < since:
                continue
            norm = urlparse(item["url"])._replace(query="", fragment="").geturl()
            if norm in seen_urls:
                continue
            seen_urls.add(norm)
            articles.append(item)
        if articles:
            break
    return articles


async def collect_all(sources: list[MediaSource], hours: int = 24) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    sem = asyncio.Semaphore(FETCH_CONCURRENCY)
    all_articles: list[dict] = []

    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        async def worker(src: MediaSource) -> list[dict]:
            async with sem:
                return await collect_from_source(client, src, since)

        results = await asyncio.gather(*[worker(s) for s in sources], return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                all_articles.extend(r)

    # 去重
    deduped: dict[str, dict] = {}
    for a in all_articles:
        key = re.sub(r"[^\w\u4e00-\u9fff]", "", a["title"].lower())[:80]
        if key not in deduped:
            deduped[key] = a
    return list(deduped.values())
