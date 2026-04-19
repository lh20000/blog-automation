# =============================================
# Agent 4 — SEO Editor
# reviewed_output.json → SEO 최적화
# 결과: seo_output.json
# =============================================
#
# 검사/보정 항목:
#   1. 제목 길이 30~50자 (짧으면 키워드 보강, 길면 축약)
#   2. 제목에 핵심 키워드 포함 여부
#   3. 메타 디스크립션 자동 생성 (첫 문단 60자 이내)
#   4. 태그 5개 이상 (부족 시 제목/본문에서 자동 추가)
#
# 단독 실행: python seo_agent.py

import sys
import re
import json
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import config as _cfg
LANGUAGE = getattr(_cfg, "LANGUAGE", "ko")

REVIEWED_FILE = "reviewed_output.json"
SEO_FILE      = "seo_output.json"

# 제목 길이 기준 (영어는 자연스럽게 더 길어짐)
TITLE_MIN = 30
TITLE_MAX = 70 if LANGUAGE == "en" else 50

# 태그 최소 개수
TAG_MIN = 5


# ──────────────────────────────────────────
# 내부 유틸
# ──────────────────────────────────────────

def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _extract_first_paragraph(content: str) -> str:
    """첫 번째 <p> 태그 텍스트를 반환합니다."""
    m = re.search(r"<p[^>]*>(.*?)</p>", content, re.IGNORECASE | re.DOTALL)
    if m:
        return _strip_html(m.group(1)).strip()
    return _strip_html(content)[:120]


def _korean_len(text: str) -> int:
    """한글/영문 혼합 문자열의 실질 길이(한글 1자 = 2byte 기준)를 반환합니다."""
    return sum(2 if ord(c) > 0x7F else 1 for c in text)


def _truncate_title(title: str, max_len: int = TITLE_MAX) -> str:
    """제목을 max_len자 이내로 줄입니다. 의미 단위(공백·조사)에서 자름."""
    if len(title) <= max_len:
        return title
    cut = title[:max_len]
    # 마지막 공백 이전까지만 사용
    last_space = cut.rfind(" ")
    if last_space > max_len - 8:
        cut = cut[:last_space]
    return cut.rstrip(",.?!。？！")


# ──────────────────────────────────────────
# SEO 검사/보정 함수
# ──────────────────────────────────────────

def _check_title_length(title: str) -> tuple[str, list[str]]:
    """제목 길이 검사. 범위 밖이면 보정 시도."""
    logs: list[str] = []
    length = len(title)

    if length < TITLE_MIN:
        logs.append(f"제목 {length}자 — {TITLE_MIN}자 미만 (짧음, 키워드 보강 시도)")
        # 보강: 연도 + '완전정리' 추가
        if "2026" not in title:
            title = f"2026년 {title}"
        if len(title) < TITLE_MIN:
            title = f"{title} 완전정리"
        logs.append(f"  → 보강 후: {title} ({len(title)}자)")

    elif length > TITLE_MAX:
        original = title
        title = _truncate_title(title)
        logs.append(f"제목 {length}자 — {TITLE_MAX}자 초과 (축약)")
        logs.append(f"  → 축약 후: {title} ({len(title)}자)")

    else:
        logs.append(f"제목 길이 {length}자 — ✅ 적정 범위 ({TITLE_MIN}~{TITLE_MAX}자)")

    return title, logs


def _check_keyword_in_title(title: str, keyword: str) -> list[str]:
    """핵심 키워드가 제목에 포함됐는지 확인."""
    if not keyword:
        return []
    if keyword in title:
        return [f"핵심 키워드 '{keyword}' — ✅ 제목에 포함됨"]
    return [f"핵심 키워드 '{keyword}' — ⚠️  제목에 미포함 (수동 확인 권장)"]


def _build_description(content: str, existing: str = "") -> tuple[str, list[str]]:
    """메타 디스크립션 생성 (60자 이내). 기존 값이 적절하면 유지."""
    logs: list[str] = []

    if existing and 20 <= len(existing) <= 160:
        logs.append(f"메타 디스크립션 — ✅ 기존 유지 ({len(existing)}자)")
        return existing, logs

    # 언어별 디스크립션 한계치: 한국어 120자, 영어 100자
    DESC_LIMIT = 100 if LANGUAGE == "en" else 120

    raw = _extract_first_paragraph(content)
    desc = raw[:DESC_LIMIT * 2].rstrip(".,?!。？！")

    # 마지막 완결 문장까지만 (최소 40자 이상인 경우에만 자름)
    if LANGUAGE == "en":
        last_period = desc.rfind(".")
    else:
        last_period = max(desc.rfind("."), desc.rfind("다"), desc.rfind("요"))
    if last_period > 40:
        desc = desc[: last_period + 1]

    desc = desc[:DESC_LIMIT]
    logs.append(f"메타 디스크립션 — 자동 생성 ({len(desc)}자, 한계 {DESC_LIMIT}자)")
    return desc, logs


def _check_tags(tags: list[str], title: str, content: str, keyword: str) -> tuple[list[str], list[str]]:
    """태그가 TAG_MIN개 미만이면 제목/키워드/본문에서 자동 추가."""
    logs: list[str] = []
    tags = list(dict.fromkeys(t.strip() for t in tags if t.strip()))  # 중복 제거

    if len(tags) >= TAG_MIN:
        logs.append(f"태그 {len(tags)}개 — ✅ 충분")
        return tags, logs

    logs.append(f"태그 {len(tags)}개 — {TAG_MIN}개 미만, 자동 보충")
    added: list[str] = []

    # 1) 핵심 키워드 추가
    if keyword and keyword not in tags:
        tags.append(keyword)
        added.append(keyword)

    # 2) 제목에서 2음절 이상 한글 단어 추출
    title_words = re.findall(r"[가-힣]{2,}", title)
    for w in title_words:
        if w not in tags and len(tags) < TAG_MIN + 3:
            tags.append(w)
            added.append(w)

    # 3) 본문에서 빈도 높은 단어 추출
    if len(tags) < TAG_MIN:
        text = _strip_html(content)
        words = re.findall(r"[가-힣]{2,4}", text)
        from collections import Counter
        common = [w for w, _ in Counter(words).most_common(30)]
        stop = {"있습니다", "합니다", "됩니다", "이후", "경우", "통해", "위해", "대해", "그리고", "하지만"}
        for w in common:
            if w not in tags and w not in stop and len(tags) < TAG_MIN + 2:
                tags.append(w)
                added.append(w)

    if added:
        logs.append(f"  → 추가된 태그: {', '.join(added)}")
    logs.append(f"  → 최종 태그 수: {len(tags)}개")
    return tags, logs


# ──────────────────────────────────────────
# 메인
# ──────────────────────────────────────────

def run_seo() -> dict | None:
    """
    reviewed_output.json을 읽어 SEO 최적화 후 seo_output.json 저장.
    """
    if not os.path.exists(REVIEWED_FILE):
        print(f"[SEO] ❌ {REVIEWED_FILE} 없음 — Reviewer를 먼저 실행하세요")
        return None

    with open(REVIEWED_FILE, encoding="utf-8") as f:
        data = json.load(f)

    title       = data["title"]
    content     = data["content"]
    tags        = data.get("tags", [])
    description = data.get("description", "")
    keyword     = data.get("keyword", "")

    print(f"\n[SEO] 최적화 시작: {title}")
    print("-" * 52)

    all_logs: list[str] = []

    # 1. 제목 길이
    title, logs1 = _check_title_length(title)
    all_logs += logs1

    # 2. 키워드 포함
    logs2 = _check_keyword_in_title(title, keyword)
    all_logs += logs2

    # 3. 메타 디스크립션
    description, logs3 = _build_description(content, description)
    all_logs += logs3

    # 4. 태그
    tags, logs4 = _check_tags(tags, title, content, keyword)
    all_logs += logs4

    for log in all_logs:
        print(f"  {log}")

    # ── seo_output.json 저장 ─────────────────
    seo_data = {
        **data,
        "title":       title,
        "description": description,
        "tags":        tags,
    }
    with open(SEO_FILE, "w", encoding="utf-8") as f:
        json.dump(seo_data, f, ensure_ascii=False, indent=2)

    print(f"\n[SEO] ✅ 완료 → {SEO_FILE}")
    return seo_data


if __name__ == "__main__":
    result = run_seo()
    if not result:
        sys.exit(1)
