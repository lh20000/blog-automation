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
from datetime import datetime, date, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG_FILE   = "published_log.json"
MAX_DAILY  = 4           # 하루 최대 발행 수
MIN_HOURS  = 3           # 최소 실행 간격 (시간)
MAX_SAME_CATEGORY = 1    # 같은 카테고리 하루 최대 (초과 시 다른 카테고리 강제)


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
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def _today_entries(log: dict) -> list[dict]:
    """오늘 날짜의 발행 기록만 반환."""
    today = str(date.today())
    return [e for e in log["entries"] if e.get("date") == today]


def record_published(title: str, url: str, category: str = "기타") -> None:
    """발행 완료 후 로그에 기록합니다. orchestrator.py에서 호출."""
    log = _load_log()
    log["entries"].append({
        "date":      str(date.today()),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "title":     title,
        "url":       url,
        "category":  category,
    })
    # 30일 이상 된 기록 정리
    cutoff = str(date.today() - timedelta(days=30))
    log["entries"] = [e for e in log["entries"] if e.get("date", "") >= cutoff]
    _save_log(log)
    print(f"[Scheduler] 발행 기록 저장: {title}")


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
