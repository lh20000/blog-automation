# =============================================
# Agent 2 — Reviewer
# draft_output.json → 팩트체크 + 구조 검증
# 결과: reviewed_output.json (통과 시)
# =============================================
#
# 검증 순서:
#   1) 팩트체크 (가칭/가상전화/불확실표현/URL)
#      ❌ 발행 중단 | ⚠️ 임시저장 전환
#   2) 구조 검증 (단계수/팁연속성/절차선언)
#      ❌ 재생성 1회 시도 → 재실패 시 임시저장 강등
#      ⚠️ 임시저장 전환
#
# 단독 실행: python reviewer_agent.py

import sys
import json
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DRAFT_FILE    = "draft_output.json"
REVIEWED_FILE = "reviewed_output.json"


def _load_draft() -> dict | None:
    if not os.path.exists(DRAFT_FILE):
        print(f"[Reviewer] ❌ {DRAFT_FILE} 없음 — Writer를 먼저 실행하세요")
        return None
    with open(DRAFT_FILE, encoding="utf-8") as f:
        return json.load(f)


def _regenerate(keyword: str) -> dict | None:
    """keyword로 콘텐츠를 재생성하고 draft를 덮어씁니다."""
    print(f"\n[Reviewer] 재생성 시도: '{keyword}'")
    from content_generator import generate_blog_post
    post = generate_blog_post(keyword)
    if not post:
        print("[Reviewer] ❌ 재생성 실패")
        return None

    draft = {
        "keyword":     keyword,
        "title":       post["title"],
        "content":     post["content"],
        "tags":        post.get("tags", []),
        "description": post.get("description", ""),
    }
    with open(DRAFT_FILE, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)

    print(f"[Reviewer] 재생성 완료: {draft['title']}")
    return draft


def run_reviewer() -> dict | None:
    """
    draft_output.json을 읽어 팩트체크 + 구조 검증 후 reviewed_output.json 저장.

    반환:
      None     → 발행 완전 중단 (팩트체크 ❌)
      dict     → 정상 진행 (force_draft=True/False 포함)
    """
    from fact_checker import (
        check_content, print_check_result,
        check_structure, print_structure_result,
    )

    draft = _load_draft()
    if not draft:
        return None

    title   = draft["title"]
    content = draft["content"]
    keyword = draft.get("keyword", title)

    # ════════════════════════════════════════
    # STEP 1 — 팩트체크
    # ════════════════════════════════════════
    print(f"\n[Reviewer] ── STEP 1: 팩트체크 ──────────────")
    print(f"  대상: {title}")

    fact = check_content(title, content, tags=draft.get("tags", []))
    print_check_result(fact)

    if fact["abort"]:
        print("[Reviewer] ❌ 팩트체크 실패 — 발행 중단")
        return None

    force_draft = fact["force_draft"]   # 경고가 있으면 이미 True

    # ════════════════════════════════════════
    # STEP 2 — 구조 검증
    # ════════════════════════════════════════
    print(f"\n[Reviewer] ── STEP 2: 구조 검증 ──────────────")

    struct = check_structure(title, content)
    print_structure_result(struct)

    if struct["abort"]:
        # ── 구조 실패 → 재생성 1회 시도 ──────
        print("\n[Reviewer] 구조 불일치 감지 → 재생성 1회 시도")
        new_draft = _regenerate(keyword)

        if new_draft:
            new_struct = check_structure(new_draft["title"], new_draft["content"])
            print("\n[Reviewer] ── 재생성 후 구조 재검증 ──")
            print_structure_result(new_struct)

            if not new_struct["abort"]:
                # 재생성 성공: 새 draft로 교체
                title   = new_draft["title"]
                content = new_draft["content"]
                draft   = new_draft
                struct  = new_struct
                print("[Reviewer] ✅ 재생성 후 구조 통과")
            else:
                # 재생성도 실패 → 임시저장으로 강등
                print("[Reviewer] ⚠️  재생성 후에도 구조 불일치 → 임시저장으로 강등")
                force_draft = True
                struct["abort"] = False   # 중단 대신 임시저장
        else:
            # 재생성 자체 실패 → 임시저장으로 강등
            print("[Reviewer] ⚠️  재생성 실패 → 임시저장으로 강등")
            force_draft = True
            struct["abort"] = False

    if struct["force_draft"]:
        force_draft = True

    # ════════════════════════════════════════
    # 최종 저장
    # ════════════════════════════════════════
    reviewed = {
        **draft,
        "title":        title,
        "content":      content,
        "fact_check":   fact,
        "struct_check": struct,
        "force_draft":  force_draft,
    }
    with open(REVIEWED_FILE, "w", encoding="utf-8") as f:
        json.dump(reviewed, f, ensure_ascii=False, indent=2)

    if force_draft:
        status_msg = "⚠️  경고/불일치 — 임시저장으로 전환"
    else:
        status_msg = "✅ 모든 검증 통과 — 정상 발행"

    print(f"\n[Reviewer] {status_msg}")
    print(f"  저장: {REVIEWED_FILE}")
    return reviewed


if __name__ == "__main__":
    result = run_reviewer()
    if not result:
        sys.exit(1)
