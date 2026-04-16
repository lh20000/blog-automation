# =============================================
# Blogger 자동 포스팅 모듈
# 2단계 API: 영문 슬러그로 생성 → 한국어 제목 업데이트
# =============================================

import os
import re
import sys
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import BLOG_ID, CREDENTIALS_FILE, TOKEN_FILE
from fact_checker import check_content, print_check_result

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCOPES = ["https://www.googleapis.com/auth/blogger"]

# 슬러그 생성 시 제거할 영어 불용어
_SLUG_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "of", "in", "on", "for", "with", "and", "or", "to", "at", "by",
    "how", "what", "why", "when", "where", "who", "which",
    "guide", "guides", "method", "methods", "way", "ways",
    "tip", "tips", "information", "info", "about", "using", "use",
    "best", "top", "great", "good", "new", "latest", "based",
    "year", "criteria", "standard", "complete", "full", "all",
    "get", "know", "find", "learn", "check", "see",
}


# ──────────────────────────────────────────
# OAuth 인증
# ──────────────────────────────────────────

def get_credentials():
    """저장된 token.json 사용, 없으면 브라우저 로그인."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("\n브라우저가 열립니다. 구글 계정으로 로그인해주세요.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print("인증 완료! token.json 저장됨.")

    return creds


# ──────────────────────────────────────────
# 퍼머링크 생성
# ──────────────────────────────────────────

# 번역 전 한국어 제목에서 제거할 숫자·금액·단위 패턴
_KO_NUM_PATTERN = re.compile(
    r'\d[\d,\.]*\s*[만억천백원%개월년일회]+'  # 금액·날짜·수량 (70만원, 2026년 등)
    r'|\d[\d,\.]*'                            # 남은 단독 숫자
    r'|[!?!？]',                              # 특수 구두점
    re.IGNORECASE,
)

# 번역 후 슬러그에서 제거할 숫자·금액 관련 영단어
_SLUG_NUM_STOPWORDS = {
    "000", "100", "200", "300", "400", "500", "600", "700", "800", "900",
    "million", "billion", "trillion", "won", "krw", "usd",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
}


def generate_permalink(title: str) -> str:
    """
    한국어 제목 → 영문 슬러그 변환
    - 숫자·금액 단위(만원, 억, 000 등) 제거 후 의미 있는 키워드만 사용
    - 예: "월 70만원 청년지원금" → "youth-support-fund-2026"

    1단계: 한국어 숫자·금액 패턴 제거
    2단계: deep-translator로 한→영 번역
    3단계: 숫자·금액 영단어 + 불용어 제거 + 하이픈 연결
    4단계: 앞 5단어 + 연도 추가
    폴백: MD5 해시
    """
    year = datetime.now().year
    try:
        from deep_translator import GoogleTranslator

        # 번역 전: 숫자·금액·단위 제거
        clean_title = _KO_NUM_PATTERN.sub(" ", title)
        clean_title = re.sub(r"\s+", " ", clean_title).strip()

        translated = GoogleTranslator(source="ko", target="en").translate(clean_title or title)

        # 소문자, 영문자+공백만 남기기 (숫자 포함 제거)
        slug = re.sub(r"[^a-z\s]", " ", translated.lower())

        # 불용어 + 숫자 관련 영단어 제거
        all_stop = _SLUG_STOPWORDS | _SLUG_NUM_STOPWORDS
        words = [w for w in slug.split() if w and w not in all_stop and len(w) > 1]

        # 앞 5단어로 제한
        slug = "-".join(words[:5])
        slug = re.sub(r"-+", "-", slug).strip("-")

        if slug:
            print(f"  [퍼머링크] {title} → {slug}-{year}")
            return f"{slug}-{year}"

    except Exception as e:
        print(f"  [퍼머링크] 번역 오류: {e}")

    # 폴백: MD5 해시
    import hashlib
    h = hashlib.md5(title.encode("utf-8")).hexdigest()[:8]
    return f"post-{year}-{h}"


# ──────────────────────────────────────────
# 퍼머링크 중복 확인
# ──────────────────────────────────────────

def _permalink_exists(service, blog_id: str, slug: str) -> bool:
    """
    slug가 블로그 발행(LIVE) 글 URL에 이미 존재하는지 확인합니다.
    DRAFT는 제외합니다 — 이전 실행 중단으로 남은 임시 초안이
    중복으로 잘못 감지되어 2개 발행되는 버그를 방지합니다.
    """
    try:
        result = service.posts().list(
            blogId=blog_id,
            maxResults=500,
            status="LIVE",
            fields="items/url",
        ).execute()
        for item in result.get("items", []):
            if slug in item.get("url", ""):
                return True
    except Exception as e:
        print(f"  [중복확인] 조회 오류: {e}")
    return False


# ──────────────────────────────────────────
# 포스팅 메인 함수
# ──────────────────────────────────────────

def post_to_blogger(title: str, content: str,
                    tags: list = None, description: str = "",
                    is_draft: bool = False,
                    skip_fact_check: bool = False) -> dict | None:
    """
    4단계 퍼머링크 확정 방식:
      1) 영문 슬러그를 title로 초안 생성
      2) 발행(publish) → Blogger가 영문 slug로 URL을 영구 확정
      3) 한국어 제목으로 patch → 발행된 URL은 변경되지 않음
      4) is_draft=True인 경우 revert()로 다시 임시저장 복원

    Blogger는 발행 후 title이 바뀌어도 URL을 재생성하지 않습니다.
    draft 상태에서는 URL이 미확정이므로 반드시 publish 후 patch해야 합니다.
    """
    # BLOG_ID 검증 (빈 값이면 API 호출 전에 조기 실패)
    if not BLOG_ID:
        print(f"[blogger_poster] ❌ BLOG_ID가 비어 있습니다. 환경변수 BLOG_ID(=GitHub Secret BLOGGER_BLOG_ID)를 확인하세요.")
        return None

    print("\nBlogger API 연결 중...")
    creds   = get_credentials()
    service = build("blogger", "v3", credentials=creds)

    permalink = generate_permalink(title)

    # 중복 슬러그 확인 → 중복이면 -MMDD 추가
    if _permalink_exists(service, BLOG_ID, permalink):
        mmdd = datetime.now().strftime("%m%d")
        permalink = f"{permalink}-{mmdd}"
        print(f"  [중복방지] 슬러그 중복 → 변경: {permalink}")
    else:
        print(f"  슬러그: {permalink}")

    if description:
        print(f"  검색설명: {description}")

    # ── 팩트체크 (할루시네이션 검증) ─────────────────────
    # skip_fact_check=True: orchestrator의 Reviewer가 이미 검증한 경우 생략
    if not skip_fact_check:
        check = check_content(title, content, tags=tags)
        print_check_result(check)

        if check["abort"]:
            return None                    # ❌ 발행 완전 중단

        if check["force_draft"]:
            is_draft = True                # ⚠️ 경고 시 강제 임시저장

    # 포스트 본문 앞에 테이블 스타일 태그 삽입
    # .post-body 선택자 없이 element 선택자 + !important 로 테마 CSS 완전 덮어쓰기
    TABLE_STYLE = """\
<style>
table {border-left:none !important; outline:none !important; border-collapse:collapse !important; width:100% !important; margin:20px 0 !important;}
th {background:#1565C0 !important; color:white !important; padding:10px !important; border:1px solid #ddd !important; border-left:none !important;}
td {padding:10px !important; border:1px solid #ddd !important; border-left:none !important;}
tr:nth-child(even) {background:#f9f9f9 !important;}
</style>
"""
    base_body: dict = {"content": TABLE_STYLE + content}
    if tags:
        base_body["labels"] = tags
    if description:
        # Blogger API v3는 customMetaData 필드를 통해 검색 설명 저장 시도
        # (API 플랫폼 제한으로 무시될 수 있음 — 실패해도 발행은 정상 진행)
        base_body["customMetaData"] = json.dumps({"itemprop:description": description}, ensure_ascii=False)

    try:
        # ── STEP 1: 영문 슬러그 title로 초안 생성 ──────────
        created = service.posts().insert(
            blogId=BLOG_ID,
            body={**base_body, "title": permalink},
            isDraft=True,
        ).execute()
        post_id = created["id"]
        print(f"  [1단계] 초안 생성 완료 (id: {post_id[:8]}...)")

        # ── STEP 2: 발행 → URL 영구 확정 ────────────────────
        published = service.posts().publish(
            blogId=BLOG_ID,
            postId=post_id,
        ).execute()
        post_url = published.get("url", "")
        print(f"  [2단계] URL 확정: {post_url}")

        # ── STEP 3: 한국어 제목으로 업데이트 (URL 불변) ─────
        service.posts().patch(
            blogId=BLOG_ID,
            postId=post_id,
            body={"title": title},
        ).execute()
        print(f"  [3단계] 제목 업데이트: {title}")

        # ── STEP 4: is_draft 요청이면 임시저장으로 복원 ─────
        if is_draft:
            service.posts().revert(
                blogId=BLOG_ID,
                postId=post_id,
            ).execute()
            status = "임시저장"
            print(f"  [4단계] 임시저장으로 복원 완료")
        else:
            status = "발행"

        print(f"\n포스팅 {status} 완료!")
        print(f"  제목: {title}")
        print(f"  URL:  {post_url}")

        return {"status": status, "url": post_url, "id": post_id, "permalink": permalink}

    except Exception as e:
        print(f"\n포스팅 오류: {e}")
        return None


# ──────────────────────────────────────────
# 직접 실행 시 전체 파이프라인 테스트
# ──────────────────────────────────────────

if __name__ == "__main__":
    from trend_collector import get_trending_keywords
    from content_generator import generate_blog_post

    print("=" * 50)
    print("오호픽 블로그 자동 포스팅")
    print("※ 1회 실행 시 정확히 1개만 발행됩니다.")
    print("=" * 50)

    # ── 이중 발행 방지 플래그 ──────────────────────
    _posting_done = False

    print("\n[1단계] 트렌드 키워드 수집")
    keywords = get_trending_keywords(count=5)
    if not keywords:
        print("키워드 수집 실패.")
        exit()
    target = keywords[0]
    print(f"선택 키워드: {target}")

    print(f"\n[2단계] '{target}' 블로그 글 생성")
    post = generate_blog_post(target)
    if not post:
        print("글 생성 실패.")
        exit()

    # ── 포스팅은 단 1회만 실행 ────────────────────
    if _posting_done:
        print("오류: 포스팅이 이미 실행됐습니다. 중단합니다.")
        exit()

    print(f"\n[3단계] 블로그 포스팅 (1개)")
    result = post_to_blogger(
        title=post["title"],
        content=post["content"],
        tags=post["tags"],
        description=post.get("description", ""),
        is_draft=True,
    )
    _posting_done = True

    if result:
        print("\n" + "=" * 50)
        print(f"완료! 발행된 글: 1개")
        print("=" * 50)
