# =============================================
# 픽스IT연구소 블로그 자동화 설정
# Blog: 픽스IT연구소 (Korean, Google Blogger)
# 역할: 한국 IT 사용자 대상 실제 오류·문제 해결 전문 블로그
# =============================================

import os

# ──────────────────────────────────────────
# [1] Blog Identity
# ──────────────────────────────────────────
BLOG_NAME     = "픽스IT연구소"
BLOG_LANGUAGE = "ko"
LANGUAGE      = "ko"
BLOG_ID       = os.environ.get("FIXITLAB_KO_BLOG_ID") or os.environ.get("BLOG_ID")

# ──────────────────────────────────────────
# [2] Gemini API Key
# ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ──────────────────────────────────────────
# [3] 네이버 API 키 (한국 트렌드 수집용)
# ──────────────────────────────────────────
NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

# ──────────────────────────────────────────
# [4] 이미지 API 키
# ──────────────────────────────────────────
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
PIXABAY_API_KEY     = os.environ.get("PIXABAY_API_KEY")

# ──────────────────────────────────────────
# [5] Cloudinary (이미지 영구 호스팅)
# ──────────────────────────────────────────
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY    = os.environ.get("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")

# ──────────────────────────────────────────
# [6] 파일 경로
# ──────────────────────────────────────────
STATES_DIR       = "states/fixitlab_ko"
CREDENTIALS_FILE = "states/fixitlab_ko/credentials.json"
TOKEN_FILE       = "states/fixitlab_ko/token.json"

# ──────────────────────────────────────────
# [7] 글 생성 설정
# ──────────────────────────────────────────
TREND_COUNT = 5

# ──────────────────────────────────────────
# [8] Gemini 모델 설정
# ──────────────────────────────────────────
LLM_PROVIDER   = "openai"
TEXT_MODEL     = "gpt-5-mini"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ──────────────────────────────────────────
# [9] 카테고리 (지침서 v2.2 기준)
# Primary Keyword Labels: Windows/PC, 모바일/앱, AI/웹 툴, 브라우저 해결, 디지털 생활
# ──────────────────────────────────────────
CATEGORIES = [
    "Windows/PC",
    "모바일/앱",
    "AI/웹 툴",
    "브라우저 해결",
    "디지털 생활",
]

# ──────────────────────────────────────────
# [10] 트렌드 수집 소스 (지침서 v2.2 기준)
# 실시간: 네이버 지식인, 뽐뿌, 클리앙, 세티즌, 루리웹IT, 네이버NOW,
#          Reddit r/windows, r/techsupport, MS·Samsung·LG·애플 코리아 패치노트
# 수익형: 네이버·Google 검색 트렌드(한국), Semrush IT 키워드,
#          제조사·OS 공식 지원 포럼 미해결 스레드
# ──────────────────────────────────────────
RSS_SOURCES = {
    "Windows/PC": [
        "https://www.reddit.com/r/windows/.rss",
        "https://www.reddit.com/r/techsupport/.rss",
    ],
    "모바일/앱": [
        "https://www.reddit.com/r/android/.rss",
        "https://www.reddit.com/r/apple/.rss",
    ],
    "AI/웹 툴": [
        "https://www.reddit.com/r/ChatGPT/.rss",
        "https://techcrunch.com/feed/",
    ],
    "브라우저 해결": [
        "https://www.reddit.com/r/chrome/.rss",
        "https://www.reddit.com/r/firefox/.rss",
    ],
    "디지털 생활": [
        "https://www.reddit.com/r/gadgets/.rss",
        "https://www.reddit.com/r/tech/.rss",
    ],
}
