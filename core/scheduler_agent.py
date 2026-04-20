# =============================================
# Scheduler Agent
# orchestrator.py 실행 전 하루 한도/간격 체크
# =============================================
#
# 규칙:
#   - 하루 최대 4개 발행 초과 시 중단
#   - 같은 카테고리 하루 2개 이상 시 다른 키워드 강제 선택
#   - 마지막 실행 후 3시간 이내 재실행 방지
#
# 단독 실행: python scheduler_agent.py

import sys
import json
import os
import re
from datetime import datetime, date, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── STATES_DIR 기반 LOG_FILE 경로 동적 설정 ──────────────
try:
    from config import STATES_DIR as _SD, LANGUAGE as _LANG
except Exception:
    _SD   = "."
    _LANG = "ko"

_BLOG_TARGET   = os.environ.get("BLOG_TARGET", "unknown").lower()
LOG_FILE       = os.path.join(_SD, "published_log.json")
SHARED_KW_FILE = os.path.join("states", "shared_used_keywords.json")

MAX_DAILY         = 4   # 하루 최대 발행 수
MIN_HOURS         = 3   # 최소 실행 간격 (시간)
MAX_SAME_CATEGORY = 1   # 같은 카테고리 하루 최대 (초과 시 다른 카테고리 강제)

# ── 유사도 체크용 불용어 ─────────────────────────────────
_KO_STOP = {
    "방법", "방식", "정보", "내용", "종류", "이유", "원인", "효과",
    "비교", "추천", "설명", "정리", "가이드", "팁", "완전", "완벽",
    "최신", "2026", "2025", "2024", "한국", "국내", "기본", "총정리",
}
_EN_STOP = {
    "the", "how", "why", "what", "best", "top", "guide", "tips",
    "ways", "list", "with", "for", "and", "use", "using", "your",
    "you", "get", "make", "that", "this", "from", "about",
}


# ──────────────────────────────────────────
# 로그 관리
# ──────────────────────────────────────────

def _load_log() -> dict:
    """published_log.json을 읽어 반환. 없으면 빈 구조 반환."""
    if not os.path.exists(LOG_FILE):
        return {"entries": []}
    with open(LOG_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_log(log: dict) -> None:
    os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def _today_entries(log: dict) -> list[dict]:
    """오늘 날짜의 발행 기록만 반환."""
    today = str(date.today())
    return [e for e in log["entries"] if e.get("date") == today]


def record_published(title: str, url: str, category: str = "기타", keyword: str = "") -> None:
    """발행 완료 후 로그에 기록합니다. orchestrator.py에서 호출."""
    log = _load_log()
    log["entries"].append({
        "date":      str(date.today()),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "title":     title,
        "url":       url,
        "category":  category,
        "keyword":   keyword,
    })
    # 30일 이상 된 기록 정리
    cutoff = str(date.today() - timedelta(days=30))
    log["entries"] = [e for e in log["entries"] if e.get("date", "") >= cutoff]
    _save_log(log)
    print(f"[Scheduler] 발행 기록 저장: {title}")


# ──────────────────────────────────────────
# 키워드 유사도 체크
# ──────────────────────────────────────────

def _extract_nouns(keyword: str) -> set[str]:
    """키워드에서 핵심 명사 추출 (유사도 비교용)."""
    if _LANG == "en" or not re.search(r"[가-힣]", keyword):
        return {w for w in keyword.lower().split() if len(w) > 2 and w not in _EN_STOP}
    return set(re.findall(r"[가-힣]{2,}", keyword)) - _KO_STOP


def is_duplicate_keyword(new_kw: str, log: dict) -> tuple[bool, str]:
    """
    published_log의 기존 키워드와 유사도 체크.
    핵심 명사 2개 이상 겹치면 중복으로 판단.
    """
    new_nouns = _extract_nouns(new_kw)
    if len(new_nouns) < 2:
        return False, ""

    for entry in log.get("entries", []):
        prev_kw = entry.get("keyword", "")
        if not prev_kw or prev_kw.strip().lower() == new_kw.strip().lower():
            continue
        prev_nouns = _extract_nouns(prev_kw)
        overlap = new_nouns & prev_nouns
        if len(overlap) >= 2:
            return True, f"'{prev_kw}'와 유사 (공통: {', '.join(sorted(overlap))})"
    return False, ""


def check_keyword_duplicate(new_kw: str) -> tuple[bool, str]:
    """자가 블로그 published_log 기반 키워드 유사도 체크 (공개 인터페이스)."""
    if not new_kw:
        return False, ""
    return is_duplicate_keyword(new_kw, _load_log())


# ──────────────────────────────────────────
# 블로그 간 공유 키워드 (한국어 블로그 전용)
# ──────────────────────────────────────────

def _load_shared_keywords() -> dict:
    """
    shared_used_keywords.json 로드.
    구조: {"date": "YYYY-MM-DD", "keywords": [{"keyword": "...", "blog": "..."}]}
    날짜가 오늘과 다르면 자동 초기화.
    """
    today = str(date.today())
    try:
        with open(SHARED_KW_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("date") != today:
            return {"date": today, "keywords": []}
        return data
    except Exception:
        return {"date": today, "keywords": []}


def _save_shared_keywords(data: dict) -> None:
    os.makedirs("states", exist_ok=True)
    try:
        with open(SHARED_KW_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  [공유키워드] 저장 실패: {e}")


def check_shared_keyword(new_kw: str) -> tuple[bool, str]:
    """다른 한국어 블로그에서 오늘 유사 키워드 발행 여부 확인."""
    if _LANG != "ko" or not new_kw:
        return False, ""

    data      = _load_shared_keywords()
    new_nouns = _extract_nouns(new_kw)

    for entry in data.get("keywords", []):
        if entry.get("blog") == _BLOG_TARGET:
            continue
        prev_kw = entry.get("keyword", "")
        if not prev_kw:
            continue
        if prev_kw.strip().lower() == new_kw.strip().lower():
            return True, f"오늘 '{entry.get('blog')}'에서 동일 키워드 발행됨"
        if len(new_nouns) >= 2:
            prev_nouns = _extract_nouns(prev_kw)
            overlap = new_nouns & prev_nouns
            if len(overlap) >= 2:
                return True, (
                    f"오늘 '{entry.get('blog')}'에서 유사 키워드 '{prev_kw}' 발행됨 "
                    f"(공통: {', '.join(sorted(overlap))})"
                )
    return False, ""


def record_shared_keyword(keyword: str) -> None:
    """발행 후 공유 키워드 풀에 기록. 한국어 블로그만."""
    if _LANG != "ko" or not keyword:
        return

    data = _load_shared_keywords()
    data["keywords"].append({"keyword": keyword, "blog": _BLOG_TARGET})
    _save_shared_keywords(data)
    print(f"  [공유키워드] 기록 완료: '{keyword}' ({_BLOG_TARGET})")


# ──────────────────────────────────────────
# 체크 함수
# ──────────────────────────────────────────

def _check_daily_limit(today: list[dict]) -> str | None:
    """하루 최대 발행 수 초과 여부."""
    if len(today) >= MAX_DAILY:
        return f"오늘 이미 {len(today)}개 발행 완료 — 하루 최대 {MAX_DAILY}개 초과"
    return None


def _check_interval(log: dict) -> str | None:
    """마지막 실행 후 MIN_HOURS 이내 재실행 여부."""
    entries = log["entries"]
    if not entries:
        return None
    last_ts = entries[-1].get("timestamp", "")
    if not last_ts:
        return None
    try:
        last_dt = datetime.fromisoformat(last_ts)
        elapsed = datetime.now() - last_dt
        if elapsed < timedelta(hours=MIN_HOURS):
            remaining = timedelta(hours=MIN_HOURS) - elapsed
            mins = int(remaining.total_seconds() / 60)
            return (
                f"마지막 실행 후 {int(elapsed.total_seconds() / 60)}분 경과 "
                f"— {MIN_HOURS}시간 간격 필요 (남은 시간: {mins}분)"
            )
    except ValueError:
        pass
    return None


def _check_category_balance(today: list[dict]) -> dict[str, int]:
    """오늘 카테고리별 발행 횟수를 반환."""
    counts: dict[str, int] = {}
    for e in today:
        cat = e.get("category", "기타")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _suggest_keyword(cat_counts: dict[str, int]) -> str | None:
    """
    특정 카테고리가 MAX_SAME_CATEGORY 초과 시
    덜 사용된 카테고리의 대표 키워드를 제안합니다.
    """
    from trend_collector import RSS_SOURCES, _CATEGORY_HINTS

    # 오늘 한도 초과 카테고리
    saturated = {c for c, n in cat_counts.items() if n >= MAX_SAME_CATEGORY}

    # 덜 사용된 카테고리 순으로 키워드 제안
    for category in RSS_SOURCES:
        if category not in saturated:
            hints = list(_CATEGORY_HINTS.get(category, []))
            if hints:
                return hints[0]

    return None


# ──────────────────────────────────────────
# 메인 체크 함수
# ──────────────────────────────────────────

def run_scheduler(force: bool = False) -> dict:
    """
    실행 가능 여부를 판단합니다.

    Returns:
        {
            "ok":            bool,   # True → 실행 가능
            "reason":        str,    # 중단 사유 (ok=False 시)
            "today_count":   int,    # 오늘 발행 수
            "force_keyword": str|None,  # 카테고리 초과 시 강제 키워드
        }
    """
    print("\n[Scheduler] 실행 조건 점검 중...")
    log   = _load_log()
    today = _today_entries(log)

    print(f"  오늘 발행: {len(today)}/{MAX_DAILY}개")

    # 1. 하루 한도
    limit_err = _check_daily_limit(today)
    if limit_err:
        print(f"  ❌ {limit_err}")
        return {"ok": False, "reason": limit_err, "today_count": len(today), "force_keyword": None}

    # 2. 실행 간격 (force 모드 시 무시)
    if not force:
        interval_err = _check_interval(log)
        if interval_err:
            print(f"  ❌ {interval_err}")
            return {"ok": False, "reason": interval_err, "today_count": len(today), "force_keyword": None}
    else:
        print("  [강제 실행 모드] 간격 체크 건너뜀")

    # 3. 카테고리 균형
    cat_counts = _check_category_balance(today)
    force_keyword = None
    if cat_counts:
        saturated = {c: n for c, n in cat_counts.items() if n >= MAX_SAME_CATEGORY}
        if saturated:
            sat_str = ", ".join(f"{c}({n}개)" for c, n in saturated.items())
            print(f"  ⚠️  카테고리 한도 도달: {sat_str}")
            force_keyword = _suggest_keyword(cat_counts)
            if force_keyword:
                print(f"  → 다른 카테고리 키워드 강제 선택: '{force_keyword}'")

    remaining = MAX_DAILY - len(today)
    print(f"  ✅ 실행 가능 (오늘 남은 발행 횟수: {remaining}개)")

    return {
        "ok":            True,
        "reason":        "",
        "today_count":   len(today),
        "force_keyword": force_keyword,
    }


def print_today_summary() -> None:
    """오늘 발행 현황을 출력합니다."""
    log   = _load_log()
    today = _today_entries(log)
    print(f"\n[Scheduler] 오늘 발행 현황 ({date.today()})")
    if not today:
        print("  아직 발행 없음")
        return
    for e in today:
        ts = e.get("timestamp", "")[-8:]  # HH:MM:SS
        print(f"  {ts}  [{e.get('category','?')}]  {e.get('title','')}")
    print(f"  합계: {len(today)}/{MAX_DAILY}개")


if __name__ == "__main__":
    result = run_scheduler()
    print_today_summary()
    sys.exit(0 if result["ok"] else 1)
