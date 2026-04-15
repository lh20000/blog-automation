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

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from writer_agent    import run_writer,    DRAFT_FILE
from reviewer_agent  import run_reviewer,  REVIEWED_FILE
from seo_agent       import run_seo,       SEO_FILE
from publisher_agent import run_publisher
from scheduler_agent import run_scheduler, record_published

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
    mapping = [
        ("재테크/투자",         {"금리", "주식", "재테크", "투자", "대출", "펀드", "ETF", "청약", "저축", "연금", "부동산"}),
        ("IT/테크",             {"AI", "인공지능", "반도체", "스마트폰", "앱", "소프트웨어", "클라우드", "로봇", "데이터"}),
        ("건강/wellness",       {"건강", "다이어트", "운동", "식단", "영양", "수면", "스트레스", "비타민", "면역"}),
        ("라이프스타일/생산성",  {"자기계발", "생산성", "독서", "습관", "루틴", "여행", "관광", "문화", "취업", "부업"}),
        ("생활정보/절약",       {"절약", "생활비", "요금", "할인", "가계부", "통신비", "공과금", "보험", "카드혜택"}),
    ]
    for cat, keywords in mapping:
        if any(kw in combined for kw in keywords):
            return cat
    return "재테크/투자"  # 기본 fallback


DRAFT_PREVIEW_FILE = "draft_preview.json"


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

        # ── Agent 1: Writer ───────────────────────
        _banner("Agent 1 — Writer  (콘텐츠 생성)")
        draft_data = run_writer(keyword)
        if not draft_data:
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
            category = _detect_category(keyword or "", seo.get("title", ""))
            record_published(
                title=seo.get("title", ""),
                url=result["url"],
                category=category,
            )
            from trend_collector import save_rotation_state
            save_rotation_state(category)
            print(f"[Orchestrator] 로테이션 상태 저장: '{category}'")

        return result

    finally:
        _cleanup()


def main():
    parser = argparse.ArgumentParser(
        description="오호픽 블로그 자동 포스팅 오케스트레이터",
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
    print("  오호픽 블로그 자동화 — Orchestrator")
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
