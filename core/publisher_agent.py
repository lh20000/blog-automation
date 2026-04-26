# =============================================
# Agent 5 — Publisher
# seo_output.json → Blogger 발행
# =============================================
#
# 단독 실행: python publisher_agent.py

import sys
import json
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SEO_FILE      = "seo_output.json"
REVIEWED_FILE = "reviewed_output.json"   # SEO 없이 단독 실행 시 폴백


def submit_indexnow(url: str):
    import requests
    key = os.environ.get("INDEXNOW_KEY", "")
    if not key:
        print("[IndexNow] ⚠️ INDEXNOW_KEY 없음, 스킵")
        return
    try:
        host = url.split("/")[2]
        payload = {"host": host, "key": key, "urlList": [url]}
        r = requests.post(
            "https://api.indexnow.org/indexnow",
            json=payload,
            timeout=10
        )
        print(f"[IndexNow] ✅ 제출 완료: {url} ({r.status_code})")
    except Exception as e:
        print(f"[IndexNow] ❌ 실패: {e}")


def run_publisher() -> dict | None:
    """
    seo_output.json (없으면 reviewed_output.json) 을 읽어 Blogger 발행.
    Reviewer/SEO 에이전트가 이미 검증 완료 → 내부 팩트체크 생략.
    """
    from blogger_poster import post_to_blogger

    # ── BLOG_ID 디버그 로그 ───────────────────
    blog_id_env = os.environ.get("BLOG_ID", "")
    print(f"[Publisher] DEBUG BLOG_ID='{blog_id_env}' (len={len(blog_id_env)})")
    if not blog_id_env:
        print("[Publisher] ⚠️  BLOG_ID 환경변수가 비어 있습니다! GitHub Secret BLOGGER_BLOG_ID를 확인하세요.")

    # ── 입력 파일 결정 ────────────────────────
    if os.path.exists(SEO_FILE):
        src = SEO_FILE
    elif os.path.exists(REVIEWED_FILE):
        src = REVIEWED_FILE
        print(f"[Publisher] ⚠️  {SEO_FILE} 없음 — {REVIEWED_FILE} 사용")
    else:
        print(f"[Publisher] ❌ 입력 파일 없음 — SEO 또는 Reviewer를 먼저 실행하세요")
        return None

    with open(src, encoding="utf-8") as f:
        data = json.load(f)

    is_draft = data.get("force_draft", False)
    mode_msg = "임시저장" if is_draft else "발행"
    print(f"\n[Publisher] Blogger {mode_msg} 시작: {data['title']}")

    result = post_to_blogger(
        title=data["title"],
        content=data["content"],
        tags=data.get("tags", []),
        description=data.get("description", ""),
        is_draft=is_draft,
        skip_fact_check=True,
    )

    if result:
        print(f"\n[Publisher] ✅ 완료")
        print(f"  URL: {result['url']}")
        if not is_draft:
            submit_indexnow(result["url"])
    else:
        print("[Publisher] ❌ 발행 실패")

    return result


if __name__ == "__main__":
    result = run_publisher()
    if not result:
        sys.exit(1)
