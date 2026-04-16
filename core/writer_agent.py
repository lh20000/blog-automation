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

# ══════════════════════════════════════════════════════════
# [준비 코드] OpenAI gpt-5.4-mini 연동 — 현재 비활성화
# Gemini → GPT 교체 시 아래 주석을 해제하고
# content_generator.py의 generate_text_content()를
# _generate_with_openai()로 교체하면 됩니다.
#
# 모델 정보 (2026년 3월 출시):
#   공식 모델명: gpt-5.4-mini
#   입력: $0.75 / 1M tokens
#   출력: $4.50 / 1M tokens
#   특징: 구조화 프롬프트 마커 준수율 높음
# ══════════════════════════════════════════════════════════

# import os
# from openai import OpenAI
#
# _OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
# _OPENAI_MODEL   = "gpt-5.4-mini"
#
# def _generate_with_openai(prompt: str) -> str | None:
#     """
#     OpenAI gpt-5.4-mini로 블로그 콘텐츠를 생성합니다.
#     content_generator.py의 generate_text_content() 내부에서
#     Gemini 호출 대신 이 함수를 호출하도록 교체하세요.
#
#     반환값: Gemini와 동일한 ##MARKER## 형식의 원본 텍스트
#     """
#     if not _OPENAI_API_KEY:
#         print("  [OpenAI] ❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
#         return None
#     try:
#         client = OpenAI(api_key=_OPENAI_API_KEY)
#         response = client.chat.completions.create(
#             model=_OPENAI_MODEL,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.7,
#             max_tokens=4096,
#         )
#         text = response.choices[0].message.content
#         usage = response.usage
#         print(
#             f"  [OpenAI] 생성 완료 — "
#             f"입력 {usage.prompt_tokens:,} / 출력 {usage.completion_tokens:,} tokens"
#         )
#         return text
#     except Exception as e:
#         print(f"  [OpenAI] 오류: {e}")
#         return None
#
# # GitHub Secrets에 추가 필요:
# #   OPENAI_API_KEY  — OpenAI API 키
# #
# # requirements.txt에 추가 필요:
# #   openai>=1.0.0


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
