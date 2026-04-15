# =============================================
# 트렌드 키워드 수집 모듈
# 카테고리별 RSS + 네이버 API 멀티소스
# =============================================

import sys
import time
import json
import re
import requests
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, TREND_COUNT

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 카테고리별 RSS 소스 ─────────────────────────────
RSS_SOURCES: dict[str, list[tuple[str, str]]] = {
    "재테크/투자": [
        ("연합뉴스 경제", "https://www.yna.co.kr/rss/economy.xml"),
        ("매일경제",     "https://www.mk.co.kr/rss/30200030/"),
    ],
    "건강/wellness": [
        ("코메디닷컴",   "https://www.kormedi.com/feed/"),
        ("헬스조선",     "https://health.chosun.com/rss/index.html"),
    ],
    "IT/테크": [
        ("전자신문 IT",  "https://rss.etnews.com/Section901.xml"),
        ("전자신문 SW",  "https://rss.etnews.com/Section903.xml"),
    ],
    "라이프스타일/생산성": [
        ("연합뉴스 문화","https://www.yna.co.kr/rss/culture.xml"),
        ("여행신문",     "https://www.traveltimes.co.kr/rss/allArticle.xml"),
    ],
    "생활정보/절약": [
        ("연합뉴스 생활","https://www.yna.co.kr/rss/life.xml"),
        ("머니투데이",   "https://news.mt.co.kr/rss/rss_one.jsp?pCodeType=1&pCode=MTE0"),
    ],
}

# ── 균등 하루 쿼터 (카테고리당 1개) ───────────────
DAILY_QUOTA: dict[str, int] = {
    "재테크/투자":        1,
    "건강/wellness":      1,
    "IT/테크":            1,
    "라이프스타일/생산성": 1,
    "생활정보/절약":      1,
    "기타":               99,
}

_QUOTA_FILE   = "daily_quota.json"
ROTATION_FILE = "rotation_state.json"


# ── 불용어 / 차단어 ────────────────────────────────
STOP_WORDS = {
    "이", "그", "저", "것", "수", "등", "및", "를", "을", "가", "의",
    "에", "은", "는", "로", "으로", "하다", "있다", "없다", "되다", "한다",
    "오늘", "내일", "올해", "지난", "최근", "현재", "대한", "관련", "위해",
    "통해", "따라", "대해", "위한", "하는", "있는", "없는", "된다", "했다",
    "한국", "서울", "뉴스", "기자", "제공", "사진", "영상", "단독",
    "어떻게", "무엇", "그러나", "하지만", "그리고", "또한", "따라서",
    "가장", "매우", "정말", "아주", "너무", "더욱", "계속", "모두", "이미",
    "아닌", "없이", "처럼", "만큼", "보다", "부터", "까지", "라고",
    "이후", "이전", "내년", "지난해", "하반기", "상반기", "분기",
    "둘째", "첫째", "셋째", "마지막", "이번", "다음", "해당", "이같은",
    "개최", "진행", "실시", "발표", "공개", "확인", "소개", "시작",
    "운세", "띠별", "오늘의", "사주", "별자리", "타로",
    "고백", "충격", "경악", "논란", "의혹", "혐의",
    "종합", "속보", "긴급", "어제", "오후", "오전", "올봄", "올겨울",
    "모델", "버전", "신제품", "출시", "발매", "예정", "업데이트",
    "지원", "보조", "혜택", "신청", "접수",
    "스님", "셰프", "교수", "감독", "배우", "가수",
}

BLOCKED_KEYWORDS = {
    "대통령", "국회", "탄핵", "선거", "정당", "여당", "야당", "의원", "대선",
    "총선", "국정", "청와대", "정부", "장관", "총리", "여론", "정치",
    "민주당", "국민의힘", "공화당", "트럼프", "바이든", "해리스",
    "푸틴", "시진핑", "이재명", "윤석열", "한동훈",
    "전쟁", "폭격", "공습", "미사일", "전투", "침공", "분쟁", "휴전",
    "이란", "이스라엘", "우크라이나", "러시아", "가자",
    "사망", "살인", "사고", "재난", "피해", "부상", "충돌", "추락",
    "화재", "폭발", "붕괴", "실종", "구조", "검거", "범인", "피의자",
    "체포", "구속", "수사", "기소", "판결", "형량", "재판", "수감",
    "암", "자살", "우울증", "마약", "중독", "자해",
    "추경", "금리인상", "환율폭락", "주가폭락", "코인폭락", "파산",
    "파업", "시위", "집회", "노조", "갈등",
    "성인", "도박", "음란", "성범죄",
    "이슬람", "극우", "혐오", "차별",
    "북한", "핵", "ICBM",
    "김정은", "김여정", "김정일", "김일성",
    "기시다", "아베", "마크롱", "숄츠", "스나크",
    "삼성전자", "삼성", "애플", "구글", "마이크로소프트",
    "현대차", "기아차", "엘지", "에스케이",
}

# ── 카테고리별 힌트 키워드 ─────────────────────────
_CATEGORY_HINTS: dict[str, set[str]] = {
    "재테크/투자": {
        "투자", "재테크", "금리", "적금", "예금", "펀드", "ETF", "주식",
        "청약", "대출", "절약", "저축", "연금", "부동산", "월세", "전세",
        "세금", "환급", "카드",
    },
    "건강/wellness": {
        "건강", "다이어트", "운동", "식단", "영양", "질병", "치료",
        "약", "병원", "의료", "체중", "근육", "수면", "스트레스",
        "면역", "비타민", "혈압", "당뇨",
    },
    "IT/테크": {
        "반도체", "AI", "인공지능", "스마트폰", "앱", "소프트웨어",
        "클라우드", "데이터", "보안", "통신", "5G", "전기차", "배터리",
        "칩", "메모리", "GPU", "CPU", "로봇", "드론",
    },
    "라이프스타일/생산성": {
        "자기계발", "생산성", "독서", "습관", "루틴", "시간관리",
        "여행", "관광", "문화", "예술", "공연", "전시", "취미",
        "직장", "취업", "부업", "강의", "목표",
    },
    "생활정보/절약": {
        "절약", "생활비", "요금", "할인", "가계부", "공과금",
        "생활정보", "생필품", "마트", "쿠폰", "적립", "청구",
        "전기요금", "가스비", "통신비", "보험", "카드혜택",
    },
}

# 네이버 API 보조 쿼리
_NAVER_QUERIES = [
    "재테크", "절약방법", "청약",
    "건강관리", "다이어트", "운동방법",
    "스마트폰", "인공지능",
    "자기계발", "취업준비", "부업",
    "생활비절약", "통신비줄이기",
]


# ── 로테이션 상태 ────────────────────────────────────

def _load_last_category() -> str | None:
    """마지막 발행 카테고리를 로드합니다."""
    try:
        with open(ROTATION_FILE, encoding="utf-8") as f:
            return json.load(f).get("last_category")
    except Exception:
        return None


def save_rotation_state(category: str) -> None:
    """발행 후 orchestrator에서 호출 — 마지막 카테고리 저장."""
    with open(ROTATION_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_category": category}, f, ensure_ascii=False)


# ── 쿼터 관리 ────────────────────────────────────────

def _load_quota() -> dict:
    today = str(date.today())
    try:
        with open(_QUOTA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("date") != today:
            return {"date": today, "counts": {}}
        return data
    except FileNotFoundError:
        return {"date": today, "counts": {}}


def _quota_available(category: str, quota_data: dict) -> bool:
    used = quota_data["counts"].get(category, 0)
    limit = DAILY_QUOTA.get(category, 1)
    return used < limit


def record_posted_category(category: str) -> None:
    data = _load_quota()
    data["counts"][category] = data["counts"].get(category, 0) + 1
    with open(_QUOTA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# ── RSS 수집 ─────────────────────────────────────────

def fetch_rss_titles(url: str, display: int = 20) -> list[str]:
    r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    root = ET.fromstring(r.content)
    titles = [el.text for el in root.findall(".//item/title") if el.text]
    return titles[:display]


def extract_keywords_from_titles(titles: list[str], top_n: int = 5) -> list[str]:
    all_words: list[str] = []
    for title in titles:
        clean = re.sub(r"<[^>]+>", "", title)
        words = re.findall(r"[가-힣]{2,}", clean)
        all_words.extend(w for w in words if w not in STOP_WORDS)

    counter = Counter(all_words)
    safe, skipped = [], []
    for word, _ in counter.most_common(top_n * 15):
        if _is_safe_keyword(word):
            safe.append(word)
        else:
            skipped.append(word)

    if skipped:
        print(f"    [필터] 제외: {', '.join(skipped[:6])}")

    result: list[str] = []
    for kw in safe:
        if not any(kw in other and kw != other for other in safe):
            result.append(kw)
        if len(result) >= top_n:
            break
    return result


def _is_safe_keyword(keyword: str) -> bool:
    for blocked in BLOCKED_KEYWORDS:
        if blocked in keyword:
            return False
    if keyword in STOP_WORDS:
        return False
    if len(keyword) < 2:
        return False
    return True


# ── 네이버 API 수집 ──────────────────────────────────

def _search_naver_news(query: str, display: int = 10) -> list[str]:
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id":     NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": query, "display": display, "sort": "date"}
    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    return [item["title"] for item in r.json().get("items", [])]


# ── 카테고리별 RSS 수집 ──────────────────────────────

def _collect_rss_category(category: str, per_source: int = 2) -> list[str]:
    sources = RSS_SOURCES.get(category, [])
    hints   = list(_CATEGORY_HINTS.get(category, set()))
    all_titles: list[str] = []

    for name, url in sources:
        try:
            titles = fetch_rss_titles(url, display=30)
            all_titles.extend(titles)
            print(f"    [{name}] {len(titles)}개 수집")
        except Exception as e:
            print(f"    [{name}] 오류: {e}")
        time.sleep(0.3)

    if not all_titles or not hints:
        return []

    combined = " ".join(all_titles)
    hint_counts = [(h, combined.count(h)) for h in hints if combined.count(h) > 0]
    hint_counts.sort(key=lambda x: -x[1])

    result = [h for h, _ in hint_counts[:per_source]]
    if hint_counts:
        top = ", ".join(f"'{h}'({c}회)" for h, c in hint_counts[:4])
        print(f"    [힌트 등장] {top}")
    return result


def _collect_naver_category(per_query: int = 3) -> list[str]:
    all_titles: list[str] = []
    for query in _NAVER_QUERIES:
        try:
            titles = _search_naver_news(query, display=5)
            all_titles.extend(titles)
        except Exception as e:
            print(f"    [네이버:{query}] 오류: {e}")
        time.sleep(0.15)
    return extract_keywords_from_titles(all_titles, top_n=per_query * 3)


# ── 메인: 균등 로테이션 키워드 수집 ─────────────────

def get_trending_keywords(count: int = None) -> list[str]:
    """
    5개 카테고리 균등 로테이션으로 키워드 수집.
    - 직전 발행 카테고리는 이번 수집에서 후순위로 밀림
    - 카테고리당 하루 1개 쿼터
    """
    if count is None:
        count = TREND_COUNT

    print("=" * 48)
    print("트렌드 키워드 수집 (5-카테고리 균등 로테이션)")
    print("=" * 48)

    last_cat = _load_last_category()
    if last_cat:
        print(f"  [로테이션] 직전 발행 카테고리: '{last_cat}' → 후순위 처리")

    quota_data = _load_quota()

    # 직전 카테고리를 후순위로 배치
    all_cats     = list(RSS_SOURCES.keys())
    priority_cats = [c for c in all_cats if c != last_cat]
    fallback_cats = [c for c in all_cats if c == last_cat]
    ordered_cats  = priority_cats + fallback_cats

    pool: list[tuple[str, str]] = []

    for category in ordered_cats:
        if not _quota_available(category, quota_data):
            print(f"\n  [{category}] 오늘 쿼터 초과 → 건너뜀")
            continue

        print(f"\n  [{category}] RSS 수집 중...")
        kws = _collect_rss_category(category, per_source=2)
        for kw in kws:
            pool.append((category, kw))
            print(f"    → '{kw}'")

    # 네이버 보조
    print("\n  [기타/보조] 네이버 API 수집 중...")
    naver_kws = _collect_naver_category(per_query=2)
    for kw in naver_kws:
        pool.append(("기타", kw))

    if not pool:
        print("\n키워드 수집 실패.")
        return []

    # 최종 선택 (카테고리 쿼터 적용)
    result: list[str] = []
    category_used_count: dict[str, int] = {}

    for category, kw in pool:
        if kw in result:
            continue
        limit = DAILY_QUOTA.get(category, 99)
        if category_used_count.get(category, 0) >= limit:
            continue
        result.append(kw)
        category_used_count[category] = category_used_count.get(category, 0) + 1
        if len(result) >= count:
            break

    # 부족하면 나머지로 채우기
    if len(result) < count:
        for category, kw in pool:
            if kw not in result:
                result.append(kw)
            if len(result) >= count:
                break

    print(f"\n수집된 키워드 TOP {len(result)}:")
    for i, kw in enumerate(result, 1):
        cat = next((c for c, k in pool if k == kw), "?")
        print(f"  {i}위: {kw}  [{cat}]")

    print("\n수집 완료!")
    return result


if __name__ == "__main__":
    kws = get_trending_keywords(count=5)
    if kws:
        print("\n테스트 성공!")
    else:
        print("\n키워드 수집 실패.")
