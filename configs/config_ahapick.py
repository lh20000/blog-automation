# =============================================
# ahapick Blog Automation — Configuration
# Blog: ahapick (English, Google Blogger)
# =============================================
# Local dev: fill in values directly below
# GitHub Actions: all values injected from GitHub Secrets
# =============================================

import os

# ──────────────────────────────────────────
# [1] Blog Identity
# ──────────────────────────────────────────
BLOG_NAME     = "ahapick"
BLOG_LANGUAGE = "en"   # English
BLOG_ID       = os.environ.get("AHAPICK_BLOG_ID") or os.environ.get("BLOG_ID")

# ──────────────────────────────────────────
# [2] Gemini API Key
# ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ──────────────────────────────────────────
# [3] Image API Keys
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
# [5] File Paths (under states/ahapick/)
# ──────────────────────────────────────────
STATES_DIR       = "states/ahapick"
CREDENTIALS_FILE = "states/ahapick/credentials.json"
TOKEN_FILE       = "states/ahapick/token.json"

# ──────────────────────────────────────────
# [6] Post Generation Settings
# ──────────────────────────────────────────
TREND_COUNT = 5    # Number of trending keywords to collect
LANGUAGE    = "en" # Language: English

# ──────────────────────────────────────────
# [7] Gemini Model Settings
# ──────────────────────────────────────────
LLM_PROVIDER   = "openai"
TEXT_MODEL     = "gpt-4.1-mini"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ──────────────────────────────────────────
# [8] Categories (English)
# ──────────────────────────────────────────
CATEGORIES = [
    "Finance & Investing",
    "Technology & AI",
    "Health & Wellness",
    "Lifestyle & Productivity",
    "Travel & Culture",
]
