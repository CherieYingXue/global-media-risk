# -*- coding: utf-8 -*-
"""标题翻译：外文标题下附中文译文。"""
from __future__ import annotations

import re
import time
from functools import lru_cache

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_LATIN_RE = re.compile(r"[A-Za-z\u00c0-\u024f\u1e00-\u1eff]")


def is_primarily_chinese(text: str) -> bool:
    if not text:
        return True
    cjk = len(_CJK_RE.findall(text))
    latin = len(_LATIN_RE.findall(text))
    total = cjk + latin
    if total == 0:
        return True
    return cjk / total >= 0.4


@lru_cache(maxsize=512)
def _translate_cached(text: str, src: str) -> str:
    if not text or is_primarily_chinese(text):
        return text
    if GoogleTranslator is None:
        return text
    try:
        return GoogleTranslator(source=src, target="zh-CN").translate(text[:500]) or text
    except Exception:
        try:
            time.sleep(0.3)
            return GoogleTranslator(source="auto", target="zh-CN").translate(text[:500]) or text
        except Exception:
            return text


def translate_title(title: str) -> dict[str, str | bool]:
    title = (title or "").strip()
    if not title:
        return {"title": "", "title_zh": "", "is_foreign": False}

    if is_primarily_chinese(title):
        return {"title": title, "title_zh": title, "is_foreign": False}

    zh = _translate_cached(title, "auto")
    if zh == title or not zh:
        zh = _translate_cached(title, "en")

    return {
        "title": title,
        "title_zh": zh,
        "is_foreign": True,
    }


def enrich_items_with_translation(items: list[dict]) -> list[dict]:
    for item in items:
        t = translate_title(item.get("title", ""))
        item["title"] = t["title"]
        item["title_zh"] = t["title_zh"]
        item["is_foreign_title"] = t["is_foreign"]
    return items
