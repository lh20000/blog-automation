# =============================================
# 오호픽 블로그 자동화 설정
# Blog: 오호픽 (Korean, Google Blogger)
# =============================================
# 로컬 개발: 아래 값을 직접 입력
# GitHub Actions: 모든 값을 GitHub Secrets에서 자동 주입
# =============================================

import os

# ──────────────────────────────────────────
# [1] Blog Identity
# ──────────────────────────────────────────
BLOG_NAME     = "ohopick"
BLOG_LANGUAGE = "ko"   # 한국어
BLOG_ID       = os.environ.get("OHOPICK_BLOG_ID") or os.environ.get("BLOG_ID")

# ──────────────────────────────────────────
# [2] Gemini API Key
# ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ──────────────────────────────────────────
# [3] 네이버 API 키 (트렌드 키워드 수집용)
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
# [6] 파일 경로 (states/ohopick/ 하위)
# ──────────────────────────────────────────
STATES_DIR       = "states/ohopick"
CREDENTIALS_FILE = "states/ohopick/credentials.json"
TOKEN_FILE       = "states/ohopick/token.json"

# ──────────────────────────────────────────
# [7] 글 생성 설정
# ──────────────────────────────────────────
TREND_COUNT = 5    # 수집할 트렌드 키워드 수
LANGUAGE    = "ko" # 언어

# ──────────────────────────────────────────
# [8] Gemini 모델 설정
# ──────────────────────────────────────────
LLM_PROVIDER   = "gemini"
TEXT_MODEL     = "gemini-3.1-flash-lite-preview"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ──────────────────────────────────────────
# [9] 카테고리 (한국어)
# ──────────────────────────────────────────
CATEGORIES = [
    "재테크 & 투자",
    "기술 & AI",
    "건강 & 웰빙",
    "라이프스타일 & 생산성",
    "여행 & 문화",
]
