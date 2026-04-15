# =============================================
# Agent 1 — Writer
# 트렌드 키워드 수집 → Gemini 초고 작성
# 결과: draft_output.json
# =============================================
#
# 단독 실행: python writer_agent.py
#            python writer_agent.py 주식

import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DRAFT_FILE = "draft_output.json"


def run_writer(keyword: str = None) -> dict | None:
    """
    키워드 수집 + 콘텐츠 생성 후 draft_output.json 저장.
    keyword 미지정 시 RSS/네이버에서 자동 수집.
    """
    from trend_collector import get_trending_keywords
    from content_generator import generate_blog_post

    # ── 키워드 결정 ──────────────────────────
    if not keyword:
        print("\n[Writer] 트렌드 키워드 수집 중...")
        keywords = get_trending_keywords(count=5)
        if not keywords:
            print("[Writer] ❌ 키워드 수집 실패")
            return None
        keyword = keywords[0]
        print(f"[Writer] 선택 키워드: {keyword}")
    else:
        print(f"[Writer] 지정 키워드: {keyword}")

    # ── 콘텐츠 생성 ──────────────────────────
    print(f"\n[Writer] '{keyword}' 블로그 글 생성 중...")
    post = generate_blog_post(keyword)
    if not post:
        print("[Writer] ❌ 콘텐츠 생성 실패")
        return None

    # ── draft_output.json 저장 ───────────────
    draft = {
        "keyword":     keyword,
        "title":       post["title"],
        "content":     post["content"],
        "tags":        post.get("tags", []),
        "description": post.get("description", ""),
    }
    with open(DRAFT_FILE, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)

    print(f"\n[Writer] ✅ 완료")
    print(f"  제목: {draft['title']}")
    print(f"  저장: {DRAFT_FILE}")
    return draft


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_writer(keyword)
    if not result:
        sys.exit(1)
