# =============================================
# 할루시네이션 검증 모듈
# 발행 전 콘텐츠 품질 자동 점검
# =============================================

import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 허용 도메인 (검사에서 제외) ──────────────────────
_ALLOWED_DOMAINS = {
    "cloudinary.com", "unsplash.com", "pixabay.com",
    "naver.com", "kakao.com", "google.com",
    "blogspot.com", "blogger.com",
}


def _strip_html(html: str) -> str:
    """HTML 태그를 제거하고 순수 텍스트만 반환합니다."""
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _check_gachig(text: str) -> str | None:
    """
    검사 1: '(가칭)' 표현 감지
    미확정·가상 명칭이 본문에 그대로 노출되는 경우 → 발행 중단
    """
    matches = re.findall(r"\(가칭\)", text)
    if matches:
        return f"'(가칭)' 표현 {len(matches)}회 발견 — 미확정 정보가 본문에 포함됨"
    return None


def _check_fake_phone(text: str) -> str | None:
    """
    검사 2: 가상 전화번호 패턴 감지
    뒷자리가 0000인 전화번호 (예: 1577-0000, 1588-0000, 02-0000-0000)
    → 발행 중단
    """
    # 대표번호 형식: 15xx-0000 / 16xx-0000
    pattern_hot = re.compile(r"\b1[5-9]\d{2}[-\s]0{4}\b")
    # 일반 번호 형식: xx(x)-xxxx-0000 또는 xx(x)-000-0000
    pattern_reg = re.compile(r"\b\d{2,3}[-\s]\d{3,4}[-\s]0{4}\b")

    found = set(pattern_hot.findall(text)) | set(pattern_reg.findall(text))
    if found:
        samples = ", ".join(sorted(found)[:3])
        return f"가상 전화번호 패턴 발견: {samples}"
    return None


# ── 카테고리별 불확실 표현 임계값 ─────────────────
_UNCERTAINTY_CATEGORIES = [
    (
        "금리/주식/재테크",
        {"금리", "주식", "재테크", "투자", "대출", "펀드", "ETF"},
        20,
    ),
    (
        "정부지원/정책",
        {"지원금", "복지", "정책", "보조금", "청약"},
        10,
    ),
]
_UNCERTAINTY_DEFAULT = 15


def _get_uncertainty_threshold(title: str, tags: list[str]) -> tuple[int, str]:
    """제목·태그 기준으로 카테고리를 판별하고 임계값을 반환합니다."""
    combined = title + " " + " ".join(tags or [])
    for cat_name, keywords, threshold in _UNCERTAINTY_CATEGORIES:
        if any(kw in combined for kw in keywords):
            return threshold, cat_name
    return _UNCERTAINTY_DEFAULT, "일반"


def _check_uncertainty(text: str, title: str = "", tags: list[str] = None) -> str | None:
    """
    검사 3: 불확실 표현 과다 → 경고(임시저장)
    카테고리별 임계값 적용:
      금리/주식/재테크 → 20회
      정부지원/정책   → 10회
      일반            →  8회
    """
    patterns = [
        "추정", "예상",
        "것으로 보입니다", "것으로 보인다",
        "것으로 예상", "것으로 추정",
        "것으로 전망", "될 것으로 전망",
        "로 추정됩니다", "로 예상됩니다",
        "알려졌습니다", "알려져 있습니다",
    ]
    total = sum(text.count(p) for p in patterns)
    threshold, cat_name = _get_uncertainty_threshold(title, tags or [])
    if total >= threshold:
        return (
            f"불확실 표현 {total}회 (임계값 {threshold}회/{cat_name}) "
            f"— 사실 검토 필요 (추정/예상/~것으로 보입니다 등)"
        )
    return None


def _check_suspicious_urls(html: str) -> str | None:
    """
    검사 4: 공식 도메인(go.kr / or.kr) 외 URL → 경고
    이미지 src, Cloudinary 등 허용 도메인은 제외하고 검사
    """
    # img src 제거 후 href / 텍스트 URL만 추출
    no_img = re.sub(r'<img[^>]+>', '', html)
    urls = re.findall(r'https?://[^\s<>"\')\]]+', no_img)

    suspicious = []
    for url in urls:
        # 허용 도메인 확인
        domain_match = re.search(r'https?://([^/\s]+)', url)
        if not domain_match:
            continue
        domain = domain_match.group(1).lower()

        if "go.kr" in domain or "or.kr" in domain:
            continue
        if any(allowed in domain for allowed in _ALLOWED_DOMAINS):
            continue
        suspicious.append(url)

    if suspicious:
        samples = "\n    ".join(suspicious[:4])
        return (
            f"공식 도메인(go.kr/or.kr) 외 URL {len(suspicious)}개 발견:\n"
            f"    {samples}"
        )
    return None


# ──────────────────────────────────────────
# 구조 검증 함수
# ──────────────────────────────────────────

def _check_step_continuity(title: str, content: str) -> str | None:
    """
    구조 검사 1: 제목에서 선언한 단계/가지 수와 실제 h3 개수 일치 확인.
    예: "3단계로 정리한 신청법" → h3이 3개여야 함.
    """
    # 제목에서 숫자 + 단계|가지 패턴 추출 (첫 번째만)
    m = re.search(r"(\d+)\s*[단가][계지]", title)
    if not m:
        return None
    declared = int(m.group(1))

    # h3 개수 카운트 (소제목 전용, h2 제외)
    h3_count = len(re.findall(r"<h3[\s>]", content, re.IGNORECASE))

    # h3이 아예 없으면 검사 생략 (h3 미사용 글일 수 있음)
    if h3_count == 0:
        return None

    if h3_count != declared:
        return (
            f"단계 수 불일치 — 제목 선언: {declared}개, "
            f"실제 <h3> 소제목: {h3_count}개"
        )
    return None


def _check_tip_continuity(content: str) -> str | None:
    """
    구조 검사 2: '팁 N' 번호가 1부터 순서대로 이어지는지 확인.
    예: 팁 2가 나왔는데 팁 1이 없음 → 발행 중단.
    """
    text = _strip_html(content)
    # "팁 1", "팁1", "TIP 1" 등 다양한 형태 탐지
    nums = [int(n) for n in re.findall(r"팁\s*(\d+)", text)]
    if len(nums) < 2:
        return None  # 팁이 1개 이하면 연속성 검사 불필요

    unique_sorted = sorted(set(nums))
    expected = list(range(unique_sorted[0], unique_sorted[-1] + 1))

    if unique_sorted[0] != 1:
        return f"팁 번호가 {unique_sorted[0]}부터 시작 — '팁 1'이 없음"

    missing = sorted(set(expected) - set(unique_sorted))
    if missing:
        return f"팁 번호 누락 — 없는 번호: {missing}"

    return None


def _check_procedure_content(content: str) -> str | None:
    """
    구조 검사 3: '절차는 다음과 같습니다' 선언 후 실제 목록이 있는지 확인.
    선언만 있고 ol/li/번호 목록이 없으면 → 경고.
    """
    # 선언 문장 위치 찾기
    decl_pos = content.find("절차는 다음과 같습니다")
    if decl_pos == -1:
        return None

    # 선언 이후 1,500자 내에 ol/li 또는 숫자 목록이 있는지 확인
    after = content[decl_pos: decl_pos + 1500]
    has_list = bool(
        re.search(r"<ol[\s>]|<li[\s>]", after, re.IGNORECASE)
        or re.search(r"^\s*\d+[.。)]\s+", after, re.MULTILINE)
    )

    if not has_list:
        return "'절차는 다음과 같습니다' 선언 후 ol/li 목록 없음 — 절차 내용 누락 의심"
    return None


def _check_empty_headings(content: str) -> str | None:
    """
    구조 검사 4: 내용 없는 h2/h3 태그 감지 → 발행 중단
    <h2></h2>, <h2> </h2>, <h3>  </h3> 등
    """
    empty = re.findall(r"<(h[23])[^>]*>\s*<\/\1>", content, re.IGNORECASE)
    if empty:
        return f"빈 소제목 태그 {len(empty)}개 발견 ({', '.join(f'<{t}>' for t in empty[:3])})"
    return None


def _check_fake_institution(text: str) -> str | None:
    """
    구조 검사 5: 가상 기관명 패턴 감지 → 경고(임시저장)
    'A증권사', 'B은행', 'C카드' 등 단일 대문자 + 기관명 조합
    """
    pattern = re.compile(
        r"\b[A-Za-z가-힣]\s*(?:증권사|증권|은행|카드사|카드|보험사|보험|캐피탈|저축은행)\b"
    )
    found = pattern.findall(text)
    # 실제 존재하는 기관명 앞글자 예외 처리 (단일 영문자만 가상으로 판단)
    fake = [f for f in found if re.match(r"^[A-Z]\s*(?:증권|은행|카드|보험|캐피탈)", f)]
    if fake:
        samples = ", ".join(dict.fromkeys(fake[:4]))  # 중복 제거
        return f"가상 기관명 패턴 발견: {samples} — 실제 기관명으로 교체 필요"
    return None


def check_structure(title: str, content: str) -> dict:
    """
    구조 일관성 검증 (팩트체크와 별도).
    실패 항목은 재생성 1회 후 그래도 실패하면 임시저장으로 강등.

    Returns: check_content()와 동일한 형태
    """
    text = _strip_html(content)

    fails: list[str] = []
    warns: list[str] = []

    r1 = _check_step_continuity(title, content)
    if r1:
        fails.append(r1)

    r2 = _check_tip_continuity(content)
    if r2:
        fails.append(r2)

    r3 = _check_procedure_content(content)
    if r3:
        warns.append(r3)

    r4 = _check_empty_headings(content)
    if r4:
        fails.append(r4)

    r5 = _check_fake_institution(text)
    if r5:
        warns.append(r5)

    abort       = len(fails) > 0
    force_draft = abort or len(warns) > 0

    if abort:
        status = "fail"
    elif warns:
        status = "warn"
    else:
        status = "pass"

    return {
        "status":      status,
        "force_draft": force_draft,
        "abort":       abort,
        "fails":       fails,
        "warns":       warns,
    }


def print_structure_result(result: dict) -> None:
    """구조 검증 결과를 터미널에 출력합니다."""
    print("\n=== 구조 검증 결과 ===")

    if result["fails"]:
        for msg in result["fails"]:
            print(f"❌ 실패: {msg}")

    if result["warns"]:
        for msg in result["warns"]:
            print(f"⚠️  경고: {msg}")

    status = result["status"]
    if status == "pass":
        print("✅ 구조 통과")
    elif status == "warn":
        print("→ 경고 (임시저장 전환)")
    else:
        print("→ 재생성 시도")


# ──────────────────────────────────────────
# 메인 검증 함수
# ──────────────────────────────────────────

def check_content(title: str, content: str, tags: list[str] = None) -> dict:
    """
    발행 전 콘텐츠 할루시네이션 검증

    Returns:
        {
            "status": "pass" | "warn" | "fail",
            "force_draft": bool,   # True → 강제 임시저장
            "abort": bool,         # True → 발행 완전 중단
            "fails": list[str],    # ❌ 항목
            "warns": list[str],    # ⚠️ 항목
        }
    """
    text = _strip_html(content)

    fails: list[str] = []
    warns: list[str] = []

    # ❌ 발행 중단 항목
    r1 = _check_gachig(text)
    if r1:
        fails.append(r1)

    r2 = _check_fake_phone(text)
    if r2:
        fails.append(r2)

    # ⚠️ 경고 → 임시저장 항목
    r3 = _check_uncertainty(text, title=title, tags=tags)
    if r3:
        warns.append(r3)

    r4 = _check_suspicious_urls(content)
    if r4:
        warns.append(r4)

    abort       = len(fails) > 0
    force_draft = abort or len(warns) > 0

    if abort:
        status = "fail"
    elif warns:
        status = "warn"
    else:
        status = "pass"

    return {
        "status":      status,
        "force_draft": force_draft,
        "abort":       abort,
        "fails":       fails,
        "warns":       warns,
    }


def print_check_result(result: dict) -> None:
    """검증 결과를 터미널에 출력합니다."""
    print("\n=== 팩트체크 결과 ===")

    if result["fails"]:
        for msg in result["fails"]:
            print(f"❌ 실패: {msg}")

    if result["warns"]:
        for msg in result["warns"]:
            print(f"⚠️  경고: {msg}")

    status = result["status"]
    if status == "pass":
        print("✅ 통과 → 정상 발행 진행")
    elif status == "warn":
        print("→ 임시저장으로 전환")
    else:
        print("→ 발행 중단")
