# =============================================
# Fix IT Lab Blog Automation — Configuration
# Blog: Fix IT Lab (English, Google Blogger)
# Role: Global IT troubleshooting expert blog for real device & software problems
# =============================================

import os

# ──────────────────────────────────────────
# [1] Blog Identity
# ──────────────────────────────────────────
BLOG_NAME     = "Fix IT Lab"
BLOG_LANGUAGE = "en"
LANGUAGE      = "en"
BLOG_ID       = os.environ.get("FIXITLAB_BLOG_ID") or os.environ.get("BLOG_ID")

# ──────────────────────────────────────────
# [2] Gemini API Key
# ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ──────────────────────────────────────────
# [3] Naver API (영어 블로그 미사용 — None 유지)
# trend_collector.py 임포트 호환성을 위해 선언 필요
# ──────────────────────────────────────────
NAVER_CLIENT_ID     = None
NAVER_CLIENT_SECRET = None

# ──────────────────────────────────────────
# [4] Image API Keys
# ──────────────────────────────────────────
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
PIXABAY_API_KEY     = os.environ.get("PIXABAY_API_KEY")

# ──────────────────────────────────────────
# [4] Cloudinary (permanent image hosting)
# ──────────────────────────────────────────
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY    = os.environ.get("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")

# ──────────────────────────────────────────
# [5] File Paths
# ──────────────────────────────────────────
STATES_DIR       = "states/fixitlab"
CREDENTIALS_FILE = "states/fixitlab/credentials.json"
TOKEN_FILE       = "states/fixitlab/token.json"

# ──────────────────────────────────────────
# [6] Post Generation Settings
# ──────────────────────────────────────────
TREND_COUNT = 5

# ──────────────────────────────────────────
# [7] Gemini Model Settings
# ──────────────────────────────────────────
LLM_PROVIDER   = "gemini"
TEXT_MODEL     = "gemini-3.1-flash-lite-preview"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ──────────────────────────────────────────
# [8] Categories (Fix IT Lab PROMPT v2.2)
# Primary Keyword Labels:
#   Windows/PC, Mobile/App, AI/Web Tools, Browser Fix, Digital Life
# ──────────────────────────────────────────
CATEGORIES = [
    "Windows/PC",
    "Mobile/App",
    "AI/Web Tools",
    "Browser Fix",
    "Digital Life",
]

# ──────────────────────────────────────────
# [9] Trend Sources (Fix IT Lab PROMPT v2.2)
# Real-Time: Reddit r/tech, r/gadgets, r/windows, r/android, r/apple, r/techsupport,
#             Quora, X Tech Curators, MS/Apple/Google/Samsung official patch notes
# Steady:    Google Trends (global), Semrush IT keywords,
#             manufacturer support forums — last 6 months
# ──────────────────────────────────────────
RSS_SOURCES = {
    "Windows/PC": [
        "https://www.reddit.com/r/windows/.rss",
        "https://www.reddit.com/r/techsupport/.rss",
    ],
    "Mobile/App": [
        "https://www.reddit.com/r/android/.rss",
        "https://www.reddit.com/r/apple/.rss",
    ],
    "AI/Web Tools": [
        "https://www.reddit.com/r/ChatGPT/.rss",
        "https://techcrunch.com/feed/",
    ],
    "Browser Fix": [
        "https://www.reddit.com/r/chrome/.rss",
        "https://www.reddit.com/r/firefox/.rss",
    ],
    "Digital Life": [
        "https://www.reddit.com/r/gadgets/.rss",
        "https://www.reddit.com/r/tech/.rss",
    ],
}
