# =============================================
# Fix AI Lab Blog Automation — Configuration
# Blog: Fix AI Lab (English, Google Blogger)
# Role: Expert blog teaching beginners to use AI tools for productivity & monetization
# =============================================

import os

# ──────────────────────────────────────────
# [1] Blog Identity
# ──────────────────────────────────────────
BLOG_NAME     = "Fix AI Lab"
BLOG_LANGUAGE = "en"
LANGUAGE      = "en"
BLOG_ID       = os.environ.get("FIXAILAB_BLOG_ID") or os.environ.get("BLOG_ID")

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
STATES_DIR       = "states/fixailab"
CREDENTIALS_FILE = "states/fixailab/credentials.json"
TOKEN_FILE       = "states/fixailab/token.json"

# ──────────────────────────────────────────
# [6] Post Generation Settings
# ──────────────────────────────────────────
TREND_COUNT = 5

ALLOWED_CATEGORIES = ["Technology & AI"]

KEYWORD_POOL = [
    "ChatGPT", "Claude AI", "Gemini", "Copilot", "Perplexity AI",
    "AI image generation", "Midjourney", "Stable Diffusion", "DALL-E",
    "prompt engineering", "AI for beginners", "AI productivity tools",
    "AI automation", "AI writing tools", "no-code AI", "AI side hustle",
    "AI monetization", "AI workflow", "LLM", "AI agent", "AI tutorial",
    "voice AI", "AI video generation", "AI summarizer", "AI coding",
]

# ──────────────────────────────────────────
# [7] Gemini Model Settings
# ──────────────────────────────────────────
LLM_PROVIDER   = "gemini"
TEXT_MODEL     = "gemini-3.1-flash-lite-preview"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ──────────────────────────────────────────
# [8] Categories (Fix AI Lab PROMPT v2.2)
# Primary Keyword Labels:
#   AI Tools, ChatGPT, AI Automation, AI Productivity,
#   AI Tutorials, AI News, AI Business, AI Prompt Engineering
# ──────────────────────────────────────────
CATEGORIES = [
    "AI Tools",
    "ChatGPT",
    "AI Automation",
    "AI Productivity",
    "AI Tutorials",
    "AI News",
    "AI Business",
    "AI Prompt Engineering",
]

# ──────────────────────────────────────────
# [9] Trend Sources (Fix AI Lab PROMPT v2.2)
# Real-Time: Reddit r/ChatGPT, r/ArtificialIntelligence, r/singularity,
#             Futurepedia, TAAFT (There's An AI For That),
#             X AI Curators & top AI influencer threads,
#             YouTube AI tutorial channels (latest 24~48h),
#             Google Trends (AI keyword spikes)
# Monetization: Google Trends (global), Semrush/Ahrefs AI keywords,
#               high-engagement AI subreddit posts
# ──────────────────────────────────────────
RSS_SOURCES = {
    "AI Tools": [
        "https://www.reddit.com/r/artificial/.rss",
        "https://feeds.feedburner.com/TechCrunch/",
    ],
    "ChatGPT": [
        "https://www.reddit.com/r/ChatGPT/.rss",
        "https://openai.com/news/rss.xml",
    ],
    "AI Automation": [
        "https://www.reddit.com/r/singularity/.rss",
        "https://zapier.com/blog/feeds/latest/",
    ],
    "AI Productivity": [
        "https://www.reddit.com/r/ArtificialIntelligence/.rss",
        "https://lifehacker.com/feed/rss",
    ],
    "AI Tutorials": [
        "https://www.reddit.com/r/learnmachinelearning/.rss",
        "https://theresanaiforthat.com/feed/",
    ],
    "AI News": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://venturebeat.com/ai/feed/",
    ],
    "AI Business": [
        "https://www.reddit.com/r/Entrepreneur/.rss",
        "https://hbr.org/topics/ai/feed",
    ],
    "AI Prompt Engineering": [
        "https://www.reddit.com/r/PromptEngineering/.rss",
        "https://www.reddit.com/r/ChatGPTPromptEngineering/.rss",
    ],
}
