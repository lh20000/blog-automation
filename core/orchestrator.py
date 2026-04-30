# =============================================
# 오호픽 블로그 자동화 — Orchestrator
# 전체 에이전트 파이프라인 관리
# =============================================
#
# 파이프라인:
#   Scheduler → Writer → Reviewer → SEO → Publisher
#
# 실행 방법:
#   python orchestrator.py              → 1개 글 발행
#   python orchestrator.py --count 3   → 3개 글 순차 발행
#   python orchestrator.py --keyword AI → 키워드 지정
#   python orchestrator.py --force     → 간격 체크 무시 (즉시 실행)
#   python orchestrator.py --draft     → 발행 없이 draft_preview.json 저장

import sys
import os
import argparse
import importlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ──────────────────────────────────────────────────────────────
# Dynamic config loading — BLOG_TARGET 환경변수로 블로그 선택
#   BLOG_TARGET=ohopick  → configs/config_ohopick.py
#   BLOG_TARGET=ahapick  → configs/config_ahapick.py
#   미설정               → ohopick 기본
# ──────────────────────────────────────────────────────────────
BLOG_TARGET = os.environ.get("BLOG_TARGET", "ohopick").lower()

try:
    cfg = importlib.import_module(f"configs.config_{BLOG_TARGET}")
    print(f"[Orchestrator] Config: configs/config_{BLOG_TARGET}.py (BLOG_TARGET={BLOG_TARGET})")
except ModuleNotFoundError:
    try:
        import config as cfg  # 개별 레포 레거시 fallback
        print("[Orchestrator] Config: config.py (legacy fallback)")
    except ModuleNotFoundError:
        cfg = None
        print("[Orchestrator] ⚠️  No config module found — env vars only")

# STATES_DIR: 블로그별 상태 파일 디렉토리
STATES_DIR = getattr(cfg, "STATES_DIR", f"states/{BLOG_TARGET}")
os.makedirs(STATES_DIR, exist_ok=True)

from writer_agent    import run_writer,    DRAFT_FILE
from reviewer_agent  import run_reviewer,  REVIEWED_FILE
from seo_agent       import run_seo,       SEO_FILE
from publisher_agent import run_publisher
from scheduler_agent import (
    run_scheduler, record_published,
    check_keyword_duplicate, check_shared_keyword, record_shared_keyword,
    check_title_duplicate,
)

TEMP_FILES = (DRAFT_FILE, REVIEWED_FILE, SEO_FILE)


def _cleanup():
    """중간 파일 삭제."""
    for path in TEMP_FILES:
        if os.path.exists(path):
            os.remove(path)


def _banner(text: str):
    print("\n" + "=" * 52)
    print(f"  {text}")
    print("=" * 52)


def _detect_category(keyword: str, title: str = "") -> str:
    """발행 기록용 카테고리를 키워드/제목에서 판별합니다."""
    combined = (keyword or "") + " " + (title or "")
    lang = getattr(cfg, "BLOG_LANGUAGE", "ko") if cfg else "ko"

    if lang == "en":
        # 우선순위: Tech를 먼저 검사 (AI/automation 키워드가 Finance와 충돌하지 않도록)
        mapping = [
            ("Technology & AI",           {"ai", "tech", "software", "app", "cloud", "robot", "data", "digital",
                                           "chip", "gadget", "git", "github", "api", "vector", "database",
                                           "diffusion", "midjourney", "gpt", "llm", "chatgpt", "automation",
                                           "machine learning", "neural", "algorithm", "code", "coding",
                                           "developer", "programming", "python", "javascript",
                                           "productivity tool", "no-code", "saas", "stable diffusion"}),
            ("Health & Wellness",         {"health", "diet", "fitness", "nutrition", "sleep", "stress",
                                           "vitamin", "immune", "workout", "mental", "medicine",
                                           "medication", "doctor", "hospital", "wellness"}),
            ("Travel & Culture",          {"travel", "trip", "destination", "tourism", "adventure",
                                           "flight", "hotel", "visa", "passport"}),
            ("Lifestyle & Productivity",  {"productivity", "habit", "routine", "lifestyle",
                                           "self-improvement", "career", "skill", "minimalism",
                                           "remote work", "side hustle", "work life"}),
            ("Finance & Investing",       {"finance", "invest", "stock", "saving", "fund", "etf",
                                           "crypto", "budget", "loan", "tax", "retirement", "rent",
                                           "credit card", "mortgage", "interest rate", "deposit"}),
        ]
        default_cat = "Lifestyle & Productivity"
    else:
        # 우선순위: IT/건강을 먼저 검사 (default가 재테크라서 매칭 실패 시 잘못 분류되는 문제 방지)
        mapping = [
            ("IT/테크",             {"ai", "인공지능", "반도체", "스마트폰", "앱", "소프트웨어", "클라우드",
                                     "로봇", "데이터", "api", "git", "github", "코딩", "프로그래밍",
                                     "개발자", "개발", "벡터", "데이터베이스", "디퓨전", "미드저니",
                                     "gpt", "llm", "챗gpt", "머신러닝", "딥러닝", "알고리즘",
                                     "파이썬", "자바스크립트", "it"}),
            ("건강/wellness",       {"건강", "다이어트", "운동", "식단", "영양", "수면", "스트레스",
                                     "비타민", "면역", "약", "복용", "처방", "병원", "의사", "치료",
                                     "의료", "혈압", "당뇨", "근육"}),
            ("라이프스타일/생산성",  {"자기계발", "생산성", "독서", "습관", "루틴", "여행", "관광",
                                     "문화", "취업", "부업", "취미", "강의", "목표", "시간관리"}),
            ("생활정보/절약",       {"절약", "생활비", "요금", "할인", "가계부", "통신비", "공과금",
                                     "보험", "카드혜택", "쿠폰", "전기요금", "가스비"}),
            ("재테크/투자",         {"금리", "주식", "재테크", "투자", "대출", "펀드", "etf", "청약",
                                     "저축", "연금", "부동산", "월세", "전세", "세금", "isa",
                                     "예금", "적금"}),
        ]
        default_cat = "라이프스타일/생산성"

    combined_lower = combined.lower()
    for cat, keywords in mapping:
        if any(kw.lower() in combined_lower for kw in keywords):
            return cat
    return default_cat


DRAFT_PREVIEW_FILE = os.path.join(STATES_DIR, "draft_preview.json")


def run_pipeline(keyword: str = None, force: bool = False, draft: bool = False) -> dict | None:
    """
    Scheduler 체크 후 Writer → Reviewer → SEO → Publisher 순서로 실행.
    draft=True 이면 Publisher를 건너뛰고 draft_preview.json 저장 후 반환.
    실패/중단 시 중간 파일 정리 후 None 반환.
    """
    try:
        # ── Scheduler 체크 (draft 모드에서는 한도/간격 무시) ──
        if draft:
            print("[Scheduler] Draft 모드 — 발행 한도/간격 체크 생략")
        else:
            sched = run_scheduler(force=force)
            if not sched["ok"]:
                print(f"\n[Orchestrator] 실행 중단: {sched['reason']}")
                return None

            # 카테고리 균형으로 키워드 강제 변경
            if sched["force_keyword"] and not keyword:
                keyword = sched["force_keyword"]
                print(f"[Orchestrator] 키워드 → '{keyword}' (카테고리 균형)")

        # ── 키워드 중복/유사 체크 ─────────────────
        if keyword:
            dup, dup_reason = check_keyword_duplicate(keyword)
            if dup:
                print(f"[Orchestrator] ⏭️  키워드 스킵: '{keyword}' — {dup_reason}")
                return None
            shared_dup, shared_reason = check_shared_keyword(keyword)
            if shared_dup:
                print(f"[Orchestrator] ⏭️  키워드 스킵: '{keyword}' — {shared_reason}")
                return None

        # ── Agent 1: Writer ───────────────────────
        _banner("Agent 1 — Writer  (콘텐츠 생성)")
        draft_data = run_writer(keyword)
        if not draft_data:
            _cleanup()
            return None

        # ── Writer 선택 키워드·제목 중복 체크 ────
        # keyword=None 인 경우 writer가 내부에서 키워드를 선택하므로
        # draft_data에서 실제 사용 키워드를 꺼내 30일 중복 체크 수행
        _used_kw    = draft_data.get("keyword", keyword or "")
        _used_title = draft_data.get("title", "")

        if _used_kw and not keyword:  # writer가 자동 선택한 키워드만 재검사
            kw_dup, kw_reason = check_keyword_duplicate(_used_kw)
            if kw_dup:
                print(f"[Orchestrator] ⏭️  키워드 중복 스킵: '{_used_kw}' — {kw_reason}")
                _cleanup()
                return None
            shared_dup, shared_reason = check_shared_keyword(_used_kw)
            if shared_dup:
                print(f"[Orchestrator] ⏭️  공유 키워드 스킵: '{_used_kw}' — {shared_reason}")
                _cleanup()
                return None

        if _used_title:
            title_dup, title_reason = check_title_duplicate(_used_title)
            if title_dup:
                print(f"[Orchestrator] ⏭️  제목 유사 스킵: '{_used_title[:40]}' — {title_reason}")
                _cleanup()
                return None

        # ── Agent 2: Reviewer ─────────────────────
        _banner("Agent 2 — Reviewer  (팩트체크 + 구조검증)")
        reviewed = run_reviewer()
        if not reviewed:
            _cleanup()
            return None

        # ── Agent 3: SEO Editor ───────────────────
        _banner("Agent 3 — SEO Editor  (제목/메타/태그 최적화)")
        seo = run_seo()
        if not seo:
            _cleanup()
            return None

        # ── Draft 모드: 발행 없이 파일 저장 후 종료 ──
        if draft:
            import json
            preview = {
                "keyword":     keyword or "",
                "title":       seo.get("title", ""),
                "description": seo.get("description", ""),
                "tags":        seo.get("tags", []),
                "content":     seo.get("content", ""),
            }
            with open(DRAFT_PREVIEW_FILE, "w", encoding="utf-8") as f:
                json.dump(preview, f, ensure_ascii=False, indent=2)
            print(f"\n[Draft] 발행 생략 — 결과 저장: {DRAFT_PREVIEW_FILE}")
            print(f"  제목: {preview['title']}")
            return {"draft": True, "file": DRAFT_PREVIEW_FILE, "title": preview["title"]}

        # ── Agent 4: Publisher ────────────────────
        _banner("Agent 4 — Publisher  (Blogger 발행)")
        result = run_publisher()

        # ── 발행 성공 시 스케줄러 로그 기록 ─────────
        if result:
            # writer가 자동 선택한 키워드도 저장해야 30일 중복 체크가 작동함
            actual_keyword = keyword or _used_kw or ""
            category = _detect_category(actual_keyword, seo.get("title", ""))
            record_published(
                title=seo.get("title", ""),
                url=result["url"],
                category=category,
                keyword=actual_keyword,
            )
            record_shared_keyword(actual_keyword)
            from trend_collector import save_rotation_state
            save_rotation_state(category)
            print(f"[Orchestrator] 로테이션 상태 저장: '{category}'")

        return result

    finally:
        _cleanup()


def main():
    blog_name = getattr(cfg, "BLOG_NAME", BLOG_TARGET) if cfg else BLOG_TARGET
    parser = argparse.ArgumentParser(
        description=f"{blog_name} 블로그 자동 포스팅 오케스트레이터",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
파이프라인: Scheduler → Writer → Reviewer → SEO → Publisher

예시:
  python orchestrator.py
  python orchestrator.py --count 3
  python orchestrator.py --keyword 금리
  python orchestrator.py --force           (간격 체크 무시)
  python orchestrator.py --count 2 --force
        """,
    )
    parser.add_argument("--count",   type=int,  default=1,     help="발행할 글 수 (기본: 1)")
    parser.add_argument("--keyword", type=str,  default=None,  help="키워드 직접 지정")
    parser.add_argument("--force",   action="store_true",      help="3시간 간격 체크 무시")
    parser.add_argument("--draft",   action="store_true",      help="발행 없이 draft_preview.json 저장")
    args = parser.parse_args()

    # --count > 1이면 키워드를 미리 수집해 다양하게 배분
    keywords: list[str] = []
    if args.keyword:
        keywords = [args.keyword] * args.count
    elif args.count > 1:
        print("\n[Orchestrator] 키워드 사전 수집 중...")
        from trend_collector import get_trending_keywords
        kw_pool = get_trending_keywords(count=args.count * 2)
        if not kw_pool:
            print("[Orchestrator] ❌ 키워드 수집 실패")
            sys.exit(1)
        seen: set[str] = set()
        for kw in kw_pool:
            if kw not in seen:
                seen.add(kw)
                keywords.append(kw)
            if len(keywords) >= args.count:
                break

    print("\n" + "█" * 52)
    print(f"  {blog_name} 블로그 자동화 — Orchestrator")
    mode_label = "[Draft 모드 — 발행 안 함]" if args.draft else f"발행 예정: {args.count}개"
    print(f"  {mode_label}  {'[강제 실행]' if args.force else ''}")
    print("█" * 52)

    success_urls: list[str] = []
    failed = 0

    for i in range(args.count):
        if args.count > 1:
            print(f"\n\n{'▶' * 52}")
            print(f"  [{i + 1} / {args.count}번째 글]")
            print(f"{'▶' * 52}")

        kw = keywords[i] if keywords else None
        result = run_pipeline(kw, force=args.force, draft=args.draft)

        if result and args.draft:
            print(f"\n✅ [{i + 1}] Draft 저장 완료: {result['file']}")
            success_urls.append(result["file"])
        elif result:
            success_urls.append(result["url"])
            print(f"\n✅ [{i + 1}] {result['url']}")
        else:
            failed += 1
            print(f"\n❌ [{i + 1}] 실패 또는 중단")

    # ── 최종 결과 요약 ──────────────────────────
    print("\n" + "█" * 52)
    label = "Draft 저장" if args.draft else "발행"
    print(f"  완료: {len(success_urls)}/{args.count}개 {label}")
    print("█" * 52)
    for url in success_urls:
        print(f"  {url}")

    if failed and not success_urls:
        sys.exit(1)


if __name__ == "__main__":
    main()
