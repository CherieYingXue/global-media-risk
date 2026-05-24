# -*- coding: utf-8 -*-
"""读取 tunnel.log 中的公网 URL。"""
import re
from pathlib import Path

log = Path(__file__).parent / "tunnel.log"
if log.exists():
    text = log.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"https://[\w.-]+\.lhr\.life", text)
    if m:
        print(m.group(0))
