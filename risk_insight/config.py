# -*- coding: utf-8 -*-
"""配置项。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# 云端部署使用打包的媒体表；本地仍可读上级目录 Excel
_BUNDLED_MEDIA = BASE_DIR / "data" / "media_sources.xlsx"
_PARENT_MEDIA = PROJECT_ROOT / "各国主流媒体网站.xlsx"
_env_media = os.getenv("MEDIA_EXCEL", "").strip()
if _env_media:
    MEDIA_EXCEL = Path(_env_media)
elif _BUNDLED_MEDIA.exists():
    MEDIA_EXCEL = _BUNDLED_MEDIA
elif _PARENT_MEDIA.exists():
    MEDIA_EXCEL = _PARENT_MEDIA
else:
    MEDIA_EXCEL = _BUNDLED_MEDIA
REPORTS_DIR = BASE_DIR / "data" / "reports"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 每日 6:00（北京时间）生成报告
SCHEDULE_HOUR = 6
SCHEDULE_MINUTE = 0
TIMEZONE = "Asia/Shanghai"

# 单次采集最多处理的媒体数量（控制耗时）
MAX_MEDIA_PER_RUN = int(os.getenv("MAX_MEDIA_PER_RUN", "80"))
# 并发请求数
FETCH_CONCURRENCY = int(os.getenv("FETCH_CONCURRENCY", "8"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "12"))

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8765"))

# Render / 云端：RENDER=true 或 ENABLE_TUNNEL=false 时不启本地 SSH 隧道
IS_CLOUD = os.getenv("RENDER", "").lower() in ("true", "1", "yes")
ENABLE_TUNNEL = os.getenv("ENABLE_TUNNEL", "false" if IS_CLOUD else "true").lower() == "true"
PUBLIC_BASE_URL = os.getenv("RENDER_EXTERNAL_URL", os.getenv("PUBLIC_URL", "")).rstrip("/")

# 风险分类
RISK_CATEGORIES = {
    "friction": "摩擦冲突",
    "negative": "负面评价",
    "measure": "不利措施",
    "geopolitical": "地缘风险",
}

# 中国及相关关键词（多语言）
CHINA_KEYWORDS = [
    "china", "chinese", "beijing", "xi jinping", "prc", "mainland china",
    "中国", "中方", "北京", "习近平", "中资", "华人", "台海", "南海", "香港", "新疆", "西藏",
    "hong kong", "taiwan strait", "south china sea", "xinjiang", "tibet",
]

# 对中国构成风险的方向性表述（涉华 + 以下之一，才视为对中国有风险）
RISK_TO_CHINA_PATTERNS = [
    "against china", "on china", "toward china", "towards china", "vs china", "versus china",
    "target china", "targeting china", "china threat", "threat from china", "threat of china",
    "contain china", "containing china", "containment of china", "curb china", "counter china",
    "pressure on china", "pressure china", "crack down on china", "crackdown on china",
    "sanctions on china", "sanctions against china", "sanction china", "ban chinese", "ban china",
    "restrict china", "restrict chinese", "blacklist chinese", "tariffs on china", "tariff on china",
    "decouple from china", "decoupling from china", "de-risk from china", "de-risking from china",
    "criticize china", "criticise china", "criticism of china", "condemn china", "accuse china",
    "blame china", "warn china", "attack china", "denounce china", "slam china", "blast china",
    "human rights in china", "china's human rights", "china human rights",
    "tension with china", "tensions with china", "dispute with china", "clash with china",
    "confrontation with china", "standoff with china", "conflict with china",
    "对华", "针对中国", "针对中方", "涉华", "制裁中国", "制裁中方", "打压中国", "遏制中国",
    "围堵中国", "抹黑中国", "攻击中国", "指责中国", "批评中国", "警告中国", "威胁中国",
    "限制中国", "限制中资", "禁止中国", "加征关税", "实体清单", "出口管制", "脱钩",
    "与中国冲突", "与中国摩擦", "与中国争端", "对华关系紧张", "中美关系", "中日关系",
    "中台", "台海局势", "南海争端", "香港问题", "新疆问题", "西藏问题",
]

# 排除：体育竞赛与竞技类报道
SPORTS_EXCLUDE_KEYWORDS = [
    "sport", "sports", "athletic", "football", "soccer", "basketball", "tennis",
    "cricket", "rugby", "golf", "olympic", "olympics", "hurdles", "marathon",
    "nba", "nfl", "fifa", "uefa", "premier league", "world cup", "championship",
    "medal", "athlete", "match result", "edges out", "defeats", "beat ", " vs ",
    "400m", "100m", "swimming", "boxing", "wrestling", "volleyball", "badminton",
    "体育", "足球", "篮球", "奥运", "世锦赛", "联赛", "决赛", "夺冠", "田径",
]

# 排除：股市行情/评级类（非对华风险议题）
FINANCE_NOISE_KEYWORDS = [
    "buy rating", "sell rating", "reaffirms", "price target", "stock price",
    "shares rose", "shares fell", "earnings report", "quarterly results",
    "买入评级", "卖出评级", "股价", "财报",
]

# 排除：对中国明显中性/正面报道
POSITIVE_EXCLUDE_KEYWORDS = [
    "cooperation with china", "cooperate with china", "partnership with china", "trade deal with china",
    "invest in china", "investment in china", "visit china", "welcome chinese", "praise china",
    "china growth", "china's growth", "china economy grows", "china opens", "china wins",
    "与中国合作", "对华合作", "友好访问", "深化合作", "互利共赢", "投资中国", "看好中国",
]

# 排除：仅报道中国自身动态、未体现外部对华压力的中性信息
NEUTRAL_CHINA_ACTION_PATTERNS = [
    "china builds", "china building", "china launches", "china unveils", "china opens",
    "china announces", "china's new", "china to launch", "china set to", "china aims to",
    "中国发布", "中国推出", "中国举行", "中国在建", "中国建成", "中国开通",
]

# 各国/地区风险关键词
RISK_KEYWORDS = {
    "friction": [
        "conflict", "clash", "dispute", "tension", "confrontation", "standoff", "war", "military",
        "冲突", "摩擦", "争端", "对峙", "紧张", "军事", "交火", "挑衅", "碰撞",
        "escalat", "incursion", "provoc", "skirmish",
    ],
    "negative": [
        "critic", "condemn", "attack", "accus", "blame", "denounc", "warn", "threat",
        "批评", "谴责", "指责", "攻击", "抹黑", "威胁", "警告", "负面", "人权",
        "human rights", "authoritarian", "aggressive",
    ],
    "measure": [
        "sanction", "ban", "tariff", "restrict", "embargo", "blacklist", "prohibit", "block",
        "制裁", "禁令", "限制", "加征关税", "出口管制", "实体清单", "脱钩", "禁运", "审查",
        "decoupling", "curb", "crackdown", "investigation into",
    ],
    "geopolitical": [
        "alliance", "nato", "trade war", "chip war", "tech war", "supply chain", "indo-pacific",
        "地缘", "联盟", "贸易战", "芯片", "供应链", "印太", "遏制", "围堵", "战略",
        "containment", " deterrence", "arms sale",
    ],
}

USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
