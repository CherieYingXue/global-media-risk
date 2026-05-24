# -*- coding: utf-8 -*-
"""风险分析引擎：识别对中国（中方）构成风险的媒体报道。"""
from __future__ import annotations

import re
from typing import Any

from config import (
    CHINA_KEYWORDS,
    FINANCE_NOISE_KEYWORDS,
    NEUTRAL_CHINA_ACTION_PATTERNS,
    POSITIVE_EXCLUDE_KEYWORDS,
    RISK_CATEGORIES,
    RISK_KEYWORDS,
    RISK_TO_CHINA_PATTERNS,
    SPORTS_EXCLUDE_KEYWORDS,
)

# 短英文词易误匹配人名/地名子串（如 Warholm → war）
_WORD_BOUNDARY_SHORT = frozenset(
    {"war", "ban", "block", "curb", "arms", "accus", "blame", "warn"}
)


def _keyword_in_text(text_lower: str, kw: str) -> bool:
    k = kw.strip().lower()
    if not k:
        return False
    if k in _WORD_BOUNDARY_SHORT and k.isascii():
        return re.search(rf"\b{re.escape(k)}\b", text_lower) is not None
    return k in text_lower


def _contains_any(text: str, keywords: list[str]) -> list[str]:
    text_lower = text.lower()
    hits = []
    for kw in keywords:
        if _keyword_in_text(text_lower, kw):
            hits.append(kw)
    return hits


def _is_sports_article(blob: str) -> bool:
    return bool(_contains_any(blob, SPORTS_EXCLUDE_KEYWORDS))


def _is_finance_noise(blob: str) -> bool:
    return bool(_contains_any(blob, FINANCE_NOISE_KEYWORDS))


def _is_positive_toward_china(blob: str) -> bool:
    return bool(_contains_any(blob, POSITIVE_EXCLUDE_KEYWORDS))


def _is_neutral_china_action_only(blob: str) -> bool:
    """仅描述中国自身行为、无外部对华压力信号。"""
    lower = blob.lower()
    if not _contains_any(blob, NEUTRAL_CHINA_ACTION_PATTERNS):
        return False
    external_pressure = _contains_any(
        lower,
        [
            "us ", "u.s.", "washington", "european", "eu ", "japan", "india", "australia",
            "sanction", "ban", "tariff", "critic", "condemn", "warn", "against china",
            "toward china", "对华", "制裁", "批评", "警告", "限制",
        ],
    )
    return not external_pressure


def _has_risk_to_china_signal(blob: str) -> bool:
    """是否明确指向对中国构成风险。"""
    if _contains_any(blob, RISK_TO_CHINA_PATTERNS):
        return True
    # 风险词 + 中国词同时出现，视为对中国有风险
    has_china = bool(_contains_any(blob, CHINA_KEYWORDS))
    if not has_china:
        return False
    for cat in ("measure", "negative", "friction"):
        if _contains_any(blob, RISK_KEYWORDS[cat]):
            return True
    # 地缘遏制类须与中国同现
    geo = _contains_any(blob, RISK_KEYWORDS["geopolitical"])
    if geo and has_china:
        containment = _contains_any(
            blob.lower(),
            ["contain", "containment", "curb", "deter", "遏制", "围堵", "对抗", "compete with china"],
        )
        if containment:
            return True
    return False


def analyze_article(article: dict[str, Any]) -> dict[str, Any] | None:
    title = article.get("title", "")
    summary = article.get("summary", "")
    blob = f"{title} {summary}"
    if len(blob.strip()) < 8:
        return None

    china_hits = _contains_any(blob, CHINA_KEYWORDS)
    if not china_hits:
        return None

    if _is_sports_article(blob):
        return None

    if _is_finance_noise(blob):
        return None

    if _is_positive_toward_china(blob):
        return None

    if _is_neutral_china_action_only(blob):
        return None

    if not _has_risk_to_china_signal(blob):
        return None

    categories: list[str] = []
    matched: dict[str, list[str]] = {}
    for cat, keywords in RISK_KEYWORDS.items():
        hits = _contains_any(blob, keywords)
        if hits:
            categories.append(cat)
            matched[cat] = hits

    if not categories:
        categories = ["geopolitical"]
        matched = {"geopolitical": ["对华风险信号"]}

    score = len(categories) * 2 + len(china_hits)
    if "measure" in categories:
        score += 4
    if "friction" in categories:
        score += 3
    if "negative" in categories:
        score += 2

    severity = "高" if score >= 8 else ("中" if score >= 5 else "低")

    return {
        **article,
        "risk_categories": categories,
        "risk_labels": [RISK_CATEGORIES[c] for c in categories],
        "china_keywords": china_hits[:5],
        "matched_keywords": matched,
        "risk_score": score,
        "severity": severity,
        "analysis_summary": _build_summary(article, categories),
    }


def _build_summary(article: dict, categories: list[str]) -> str:
    country = article.get("country", "")
    media = article.get("media", "")
    labels = "、".join(RISK_CATEGORIES.get(c, c) for c in categories)
    return (
        f"{country}媒体《{media}》报道指出，相关动向可能对中国构成"
        f"【{labels}】类风险，值得关注。"
    )


def analyze_batch(articles: list[dict]) -> list[dict]:
    results = []
    for art in articles:
        r = analyze_article(art)
        if r:
            results.append(r)
    results.sort(key=lambda x: (-x["risk_score"], x.get("published") or ""))
    return results


def build_report_meta(items: list[dict]) -> dict:
    by_cat: dict[str, int] = {v: 0 for v in RISK_CATEGORIES.values()}
    by_country: dict[str, int] = {}
    for item in items:
        for label in item.get("risk_labels", []):
            by_cat[label] = by_cat.get(label, 0) + 1
        c = item.get("country", "未知")
        by_country[c] = by_country.get(c, 0) + 1

    high = sum(1 for i in items if i.get("severity") == "高")
    medium = sum(1 for i in items if i.get("severity") == "中")

    return {
        "total_items": len(items),
        "high_risk_count": high,
        "medium_risk_count": medium,
        "by_category": by_cat,
        "by_country": dict(sorted(by_country.items(), key=lambda x: -x[1])[:15]),
    }
