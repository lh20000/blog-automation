# =============================================
# 블로그 글 + 이미지 자동 생성 모듈
# 실용 정보 중심 | 모델: config.py TEXT_MODEL
# =============================================

import sys
import io
import os
import re
import json
import random
import requests
from PIL import Image
from google import genai
import cloudinary
import cloudinary.uploader

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import (GEMINI_API_KEY, UNSPLASH_ACCESS_KEY, PIXABAY_API_KEY,
                    CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET,
                    TEXT_MODEL)
import config as _cfg_cg
FALLBACK_MODELS = getattr(_cfg_cg, "FALLBACK_MODELS", [TEXT_MODEL])
LLM_PROVIDER   = getattr(_cfg_cg, "LLM_PROVIDER",   "gemini")
OPENAI_API_KEY = getattr(_cfg_cg, "OPENAI_API_KEY",  "")
import config as _cfg
LANGUAGE  = getattr(_cfg, "LANGUAGE",  "ko")
BLOG_NAME = getattr(_cfg, "BLOG_NAME", "")

# Gemini 클라이언트 (OpenAI 사용 시 None으로 두어 불필요한 초기화 방지)
client = genai.Client(api_key=GEMINI_API_KEY) if LLM_PROVIDER != "openai" and GEMINI_API_KEY else None

# Cloudinary SDK 초기화 (키가 설정된 경우에만)
if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )


# ──────────────────────────────────────────
# 1. 텍스트 생성
# ──────────────────────────────────────────

def _build_prompt(keyword: str) -> str:
    """LANGUAGE 설정에 따라 한국어 또는 영어 프롬프트를 반환합니다."""
    if LANGUAGE == "en":
        return _build_prompt_en(keyword)
    return _build_prompt_ko(keyword)


def _build_prompt_ko(keyword: str) -> str:
    return f"""
당신은 대한민국 독자를 위한 실용 정보 블로그 전문 작가입니다.
아래 키워드 주제로 독자가 읽고 즉시 행동할 수 있는 정보성 글을 작성하세요.

[키워드] {keyword}
[작성 기준 연도] 2026년 (현재 시점 기준으로 작성)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
절대 지켜야 할 핵심 원칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 구체적 수치 필수 (반드시 "2026년 기준" 명시)
   - 금액: "2026년 기준 월 70만원", "최대 500만원 지원"
   - 기간: "2026년 신청 기간 1월 2일~12월 31일"
   - 비율: "소득 상위 30% 이하", "전년 대비 23% 증가"
   - 수량: "3가지 방법", "5단계 절차"
   - 만약 2026년 기준 정확한 수치를 모른다면:
     추정 수치를 작성하되 "약", "추정", "예상" 등의 단어로 불확실성을 표현할 것

2. 단계별 행동 지침 필수 — 반드시 HTML ol/li 태그 사용
   - 신청 방법, 절차, 순서, 단계는 반드시 아래 형식 사용:
     <ol style="line-height:2; padding-left:20px;">
       <li>복지로(bokjiro.go.kr) 접속</li>
       <li>회원가입 후 로그인</li>
       <li>급여/서비스 신청 클릭</li>
     </ol>
   - ① ② ③ 또는 1. 2. 3. 을 문단 텍스트 안에 넣는 것 절대 금지
   - "→" 화살표로 단계를 한 문장에 연결하는 것 절대 금지

3. 비교표 항상 필수 — 예외 없음
   - 주제와 관계없이 ##TABLE_DATA## 비교표를 반드시 포함할 것
   - 상품/방법/옵션을 최소 3개 이상 수치로 비교
   - 반드시 실제 존재하는 기관명을 사용할 것
     (예: 미래에셋증권, 삼성증권, 키움증권, 국민은행, 카카오뱅크, 삼성카드)
   - "A증권사", "B은행", "C카드" 등 가상 기관명 절대 금지
   - 주제가 자연스럽게 비교 불가능한 경우에도 시기별·방법별·시나리오별 비교표 생성
   - 예: "미래에셋증권 수수료 0.015% vs 키움증권 0.015%, 국내 ETF 거래 기준"

4. 감성 문장·뜬구름 표현 완전 금지
   금지 예시: "많은 분들이 고민합니다", "함께 극복해봐요", "현명하게 대처하세요"
             "중요합니다", "도움이 될 것입니다", "쉽지 않죠", "응원합니다"

5. 이모지 절대 금지 (본문 전체, 소제목 포함)
   - 단, 전문가 팁 박스 헤더에 💡, 주의 박스 헤더에 ⚠️ 각 1회만 허용

6. "오호픽" 블로그명 완전 금지 (제목, 본문, 태그 어디에도 포함 금지)

7. 도입부 규칙
   - 인사말("안녕하세요") 금지
   - 반드시 충격적인 수치나 핵심 팩트로 시작
   - 예: "청년도약계좌 가입자 중 42%가 납입 한도를 채우지 못해 연간 평균 18만원의 정부지원금을 놓치고 있습니다."

8. 최소 총 3,500자 이상 (이미지 제외 순수 텍스트) — SEO 권장 기준

9. 문단 나누기 규칙 — 모바일 가독성 최우선
   - 단락은 최대 2~3문장. <p> 태그 안에 3문장 초과 절대 금지
   - <p>&nbsp;</p> 절대 금지 — 공백 단락 삽입 금지
   - 단독 <br> 태그 절대 금지 — 모든 간격은 CSS margin으로만 처리
   - 문단이 길어지면 반드시 새 <p> 태그로 나눌 것
   - 긴 설명이 필요한 경우 소제목(h2/h3)으로 나눠서 작성
   - 긴 문장 하나로 이어지지 않도록 반드시 끊어 쓸 것 (쉼표 5개 이상 한 문장 금지)

   [나쁜 예 — 절대 금지]
   <p>문장1. 문장2. 문장3. 문장4.</p>
   <p>&nbsp;</p>
   문장5.<br>문장6.

   [좋은 예 — 반드시 이렇게]
   <p>문장1. 문장2. 문장3.</p>
   <p>문장4. 문장5. 문장6.</p>

10. 단계별 서술 구분 — 순서 있는 내용은 반드시 <h3> 소제목으로 구분
   - "첫 번째", "두 번째", "셋째", "1단계", "2단계" 등 순서 표현이 있으면
     각 단계마다 <h3> 태그를 사용할 것
   - 예:
     <h3>첫 번째 단계: 자격 조건 확인</h3>
     <p>만 19~34세 청년이면서 중위소득 180% 이하인 경우 신청 가능합니다.</p>
     <h3>두 번째 단계: 서류 준비</h3>
     <p>주민등록등본, 건강보험료 납부확인서, 소득확인서류를 준비합니다.</p>

11. <h3> 태그 다음 본문은 반드시 <p> 태그로 감쌀 것
   - <h3> 바로 뒤에 오는 텍스트는 반드시 <p>...</p>로 감싸야 함
   - 절대 금지: <h3>소제목</h3>본문 텍스트가 태그 없이 바로 나오는 것
   - 반드시 이렇게:
     <h3>소제목</h3>
     <p>본문 텍스트...</p>

12. H2/H3 스타일 필수 적용
   - 모든 <h2> 태그에 style="margin-top:32px;" 반드시 포함
   - 모든 <h3> 태그에 style="margin-top:24px;" 반드시 포함
   - 예:
     <h2 style="margin-top:32px;">소제목</h2>
     <h3 style="margin-top:24px;">세부 소제목</h3>

13. Featured Snippet — 첫 번째 H2 바로 다음에 핵심 요약 배치
   - 첫 번째 <h2> 태그 직후에 반드시 2~3문장 핵심 요약 <p>를 배치할 것
   - 독자가 스크롤 없이 핵심 정보를 파악할 수 있도록 수치 중심으로 작성
   - 예:
     <h2 style="margin-top:32px;">청년도약계좌 자격 조건</h2>
     <p>2026년 기준 만 19~34세 청년 중 개인소득 연 7,500만원 이하면 신청 가능합니다. 월 최대 70만원 납입 시 정부기여금 포함 5년 후 약 5,000만원을 달성할 수 있습니다.</p>

14. 전문가 팁 박스(💡)와 주의 박스(⚠️) 각 1회 필수 포함
   - 각 박스는 ##TIPBOX## 와 ##WARNBOX## 마커로 출력 — 이 마커들은 독립 출력 섹션임
   - ❌ 절대 금지: SECTION1_BODY 또는 SECTION2_BODY 본문 텍스트 안에
     "💡 **전문가 팁**" 또는 "⚠️ **주의**" 내용을 직접 쓰는 것 금지.
     본문과 마커 섹션 양쪽에 모두 쓰면 중복 출력이 발생함 — 엄격히 금지.
   - ✅ 올바른 방법: 팁/주의 내용은 반드시 ##TIPBOX## / ##WARNBOX## 마커 아래에만 작성

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
나쁜 글 vs 좋은 글 예시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[나쁜 예 — 절대 이렇게 쓰지 말 것]
"절약은 누구에게나 필요합니다. 작은 실천부터 시작해봐요.
 생활비를 줄이는 방법에 대해 알아보겠습니다."

[좋은 예 — 이렇게 써야 함]
"월급 300만원 직장인이 공과금 자동이체 항목 3개만 바꿔도
 연간 최대 84,000원을 절약할 수 있습니다. 한국전력 에너지캐시백(3~5만원),
 가스공사 절약 프로그램(최대 2만원), 통신사 결합할인(월 1,000~3,000원 추가)을
 합산하면 월 7,000원 이상 고정 지출이 줄어듭니다."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
출력 형식 — 아래 마커를 반드시 그대로 사용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

##TITLE##
(클릭 유도 제목, 30자 이내, 키워드+수치 포함, 이모지 없이, "오호픽" 금지)
예: "청년도약계좌 월 70만원 납입하면 5년 후 얼마?"

##SUMMARY##
(핵심 요약 3줄, 각 줄 앞에 ✅ 붙이기, 반드시 수치 포함, 줄바꿈으로 구분)

##INTRO##
(수치/팩트로 시작, 2~3문장, <p> 태그 사용, 인사말/감성 표현 금지)

##SECTION1_TITLE##
(소제목 텍스트만, 이모지 없이, 수치 포함 권장)

##SECTION1_BODY##
(본문 2~3단락, 구체적 수치 포함)
(각 <p> 태그 안에 최대 2~3문장 — 3문장 초과 절대 금지, <p>&nbsp;</p>·단독<br> 사용 금지)
(절차/단계가 있으면 반드시 <ol style="line-height:2; padding-left:20px;"><li>...</li></ol> 사용)
(⚠️ 주의: 모든 ##MARKER## 는 HTML 태그 밖에서 단독 줄로 배치할 것. </ol></ul> 닫힘 완료 후에만 다음 마커 시작)

##TABLE_DATA##
아래 JSON 형식만 출력. 다른 텍스트, HTML 태그, 마크다운, 코드블록 절대 금지.
최소 3행 4열 이상의 비교 데이터를 담을 것.

{{
  "headers": ["구분", "항목1", "항목2", "항목3"],
  "rows": [
    ["행1", "값1", "값2", "값3"],
    ["행2", "값4", "값5", "값6"],
    ["행3", "값7", "값8", "값9"]
  ]
}}

올바른 출력 예시:
{{"headers": ["구분", "소상공인 정책자금", "시중은행 대출", "비고"], "rows": [["한도", "7,000만원", "5,000만원", "정책자금 유리"], ["금리", "연 2.5%", "연 5.8%", "정책자금 유리"], ["조건", "사업자등록 후 7년 이내", "신용등급 4등급 이상", "조건 상이"]]}}

절대 금지:
- | 파이프 | 형식 금지
- <table> HTML 태그 금지
- ```json 코드블록 금지
- JSON 바깥에 설명 텍스트 금지

##SECTION2_TITLE##
(소제목 텍스트만, 이모지 없이)

##SECTION2_BODY##
(본문 2~3단락, 실용 팁 3개 이상)
(각 <p> 태그 안에 최대 2~3문장 — 3문장 초과 절대 금지, <p>&nbsp;</p>·단독<br> 사용 금지)
(절차/단계가 있으면 반드시 <ol style="line-height:2; padding-left:20px;"><li>...</li></ol> 사용)
(⚠️ 절대 금지: 이 섹션 본문 안에 💡 또는 ⚠️ 팁/주의 내용을 직접 넣지 마세요.
##TIPBOX##와 ##WARNBOX## 마커는 이 섹션이 끝난 뒤 별도로 출력하는 독립 섹션입니다.
본문에 팁 내용을 쓰면 중복 출력이 발생합니다 — 금지.)

##TIPBOX##
(💡 전문가 팁 박스 — 구체적 수치와 즉시 실행 가능한 행동 지침 포함, 2~3줄)

##WARNBOX##
(⚠️ 주의 박스 — 독자가 놓치기 쉬운 함정·조건·주의사항, 구체적 수치 포함, 2~3줄)

##FAQ_Q1##
(실제 독자가 궁금해할 구체적인 질문)
##FAQ_A1##
(답변 2~3문장, 수치/날짜/금액 포함)
##FAQ_Q2##
##FAQ_A2##
##FAQ_Q3##
##FAQ_A3##

##OUTRO##
(마무리 1~2문장, <p> 태그 사용, 이모지 없이, 독자가 바로 취할 행동 한 가지 제시)

##TAGS##
(태그 5개, 쉼표 구분, "{BLOG_NAME}" 제외)
"""


def _build_prompt_en(keyword: str) -> str:
    return f"""
You are a professional blog writer for US and global English-speaking readers.
Write a practical, actionable information article on the topic below.

[KEYWORD] {keyword}
[REFERENCE YEAR] 2026 (write from current perspective)

==============================
CORE RULES — MUST FOLLOW
==============================

1. Specific numbers are mandatory (always state "as of 2026" where relevant)
   - Amounts: "up to $500/month", "maximum $6,000 per year"
   - Dates: "application window: January 2 – December 31, 2026"
   - Rates: "top 30% income bracket", "23% increase year-over-year"
   - Counts: "3 methods", "5-step process"
   - If exact 2026 figures are unknown, use "approximately", "estimated", "projected"

2. Step-by-step action guides are mandatory — use HTML ol/li tags
   - Any numbered procedure must use this format:
     <ol style="line-height:2; padding-left:20px;">
       <li>Go to the official website</li>
       <li>Create an account and log in</li>
       <li>Click "Apply" and fill out the form</li>
     </ol>
   - NEVER write steps inline as ① ② ③ or 1. 2. 3. inside paragraph text
   - NEVER chain steps with "→" arrows in a single sentence

3. Comparison table is ALWAYS mandatory — no exceptions
   - A ##TABLE_DATA## comparison table is REQUIRED for every article
   - Compare at least 3 products/options/methods with real numbers
   - Use REAL institution or brand names only
     (e.g., Fidelity, Vanguard, Chase, Bank of America, Robinhood, Schwab, Betterment)
   - NEVER use placeholder names like "Bank A", "Company B", "XYZ Fund"

4. No emotional filler or vague language
   Banned phrases: "many people wonder", "it's not easy", "we're all in this together",
                   "important to note", "this will help you", "don't miss out"

5. No emojis in body text (except 💡 once in the expert tip box and ⚠️ once in the warning box)

6. Do NOT mention "{BLOG_NAME}" anywhere in the article (title, body, or tags)

7. Opening rule — NO greeting; start with a shocking statistic or key fact

8. Minimum 2,000 words of pure text (excluding images)

9. Paragraph formatting — mobile readability first
   - Max 2–3 sentences per <p> tag
   - NEVER use <p>&nbsp;</p> — no blank paragraph spacers
   - NEVER use standalone <br> tags — use CSS margin only

10. Step-by-step sections — use <h3> subheadings for each step
    - Each step must have its own <h3 style="margin-top:24px;">

11. Every <h3> must be followed immediately by a <p> tag

12. H2/H3 style attributes are mandatory
    - All <h2> tags: style="margin-top:32px;"
    - All <h3> tags: style="margin-top:24px;"

13. Featured Snippet — place a key summary right after the first H2
    - Immediately after the first <h2>, add a 2–3 sentence summary <p>

14. Expert tip box (💡) and warning box (⚠️) — each required once
    - Use ##TIPBOX## and ##WARNBOX## markers — STANDALONE output sections
    - ❌ FORBIDDEN: Do NOT write tip/warning content inside SECTION1_BODY or SECTION2_BODY
    - ✅ CORRECT: Write tip/warning content ONLY under ##TIPBOX## / ##WARNBOX## markers

==============================
OUTPUT FORMAT — use these markers exactly
==============================

##TITLE##
(Click-worthy title, under 70 characters, keyword + number, no emoji, no "{BLOG_NAME}")

##SUMMARY##
(3-line key summary, each line starts with ✅, must include numbers, separated by newlines)

##INTRO##
(Start with a statistic/fact, 2–3 sentences, use <p> tags, no greeting or emotional language)

##SECTION1_TITLE##
(Subheading text only, no emoji, include a number where possible)

##SECTION1_BODY##
(2–3 paragraphs, specific numbers required)
(Max 2–3 sentences per <p> tag; no <p>&nbsp;</p> or standalone <br>)
(Use <ol style="line-height:2; padding-left:20px;"><li>...</li></ol> for any procedure)

##TABLE_DATA##
Output ONLY the JSON below. No other text, HTML tags, markdown, or code blocks.
Minimum 3 rows × 4 columns of comparison data.

{{
  "headers": ["Category", "Option 1", "Option 2", "Option 3"],
  "rows": [
    ["Row 1", "Value 1", "Value 2", "Value 3"],
    ["Row 2", "Value 4", "Value 5", "Value 6"],
    ["Row 3", "Value 7", "Value 8", "Value 9"]
  ]
}}

##SECTION2_TITLE##
(Subheading text only, no emoji)

##SECTION2_BODY##
(2–3 paragraphs, at least 3 practical tips)
(Max 2–3 sentences per <p> tag; no <p>&nbsp;</p> or standalone <br>)
(⚠️ Do NOT write 💡 or ⚠️ tip/warning content here — use ##TIPBOX## / ##WARNBOX## markers only)

##TIPBOX##
(💡 Expert Tip — specific numbers + immediately actionable advice, 2–3 lines)

##WARNBOX##
(⚠️ Warning — common pitfalls readers miss, specific numbers/conditions, 2–3 lines)

##FAQ_Q1##
(A specific question a real reader would ask)
##FAQ_A1##
(Answer in 2–3 sentences, include numbers/dates/amounts)
##FAQ_Q2##
##FAQ_A2##
##FAQ_Q3##
##FAQ_A3##

##OUTRO##
(Closing 1–2 sentences, use <p> tags, no emoji, give reader one specific action to take)

##TAGS##
(5 tags, comma-separated, no "{BLOG_NAME}")
"""


def generate_text_content(keyword: str) -> dict | None:
    """LLM_PROVIDER 설정에 따라 OpenAI 또는 Gemini로 텍스트를 생성합니다."""
    if LLM_PROVIDER == "openai":
        return _generate_openai(keyword)
    return _generate_gemini(keyword)


def _generate_openai(keyword: str) -> dict | None:
    """OpenAI gpt-5-mini로 블로그 콘텐츠를 생성합니다."""
    if not OPENAI_API_KEY:
        print("  [OpenAI] ❌ OPENAI_API_KEY 미설정")
        return None
    lang_label = "EN" if LANGUAGE == "en" else "KO"
    print(f"  텍스트 생성 중 [{lang_label}|OpenAI {TEXT_MODEL}]: '{keyword}'")
    try:
        from openai import OpenAI
        oai = OpenAI(api_key=OPENAI_API_KEY)
        response = oai.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": _build_prompt(keyword)}],
            max_completion_tokens=16384,
        )
        text  = response.choices[0].message.content
        usage = response.usage
        finish = response.choices[0].finish_reason
        print(
            f"  [OpenAI] 완료 — "
            f"입력 {usage.prompt_tokens:,} / 출력 {usage.completion_tokens:,} tokens"
            f" / finish_reason={finish}"
        )
        # 디버그: 원시 응답 앞 300자 출력 (파싱 문제 진단용)
        print(f"  [OpenAI DEBUG] 응답 앞 300자: {repr(text[:300])}")
        result = parse_text_response(text)
        # 파싱 결과 요약 출력
        empty_keys = [k for k, v in result.items() if not v.strip()]
        if empty_keys:
            print(f"  [OpenAI DEBUG] 비어있는 마커: {empty_keys}")
        return result
    except Exception as e:
        print(f"  [OpenAI] 오류: {e}")
        return None


def _generate_gemini(keyword: str) -> dict | None:
    """Gemini로 실용 정보 중심의 블로그 텍스트를 생성합니다."""
    lang_label = "EN" if LANGUAGE == "en" else "KO"
    print(f"  텍스트 생성 중 [{lang_label}|Gemini]: '{keyword}'")

    prompt = _build_prompt(keyword)

    import time
    models_to_try = list(dict.fromkeys(FALLBACK_MODELS))
    for attempt, model in enumerate(models_to_try, 1):
        try:
            if attempt > 1:
                wait = 20 * (attempt - 1)
                print(f"  재시도 {attempt}회 (모델: {model}, {wait}초 대기 중...)")
                time.sleep(wait)
            response = client.models.generate_content(model=model, contents=prompt)
            if attempt > 1:
                print(f"  모델 '{model}'으로 생성 성공")
            return parse_text_response(response.text)
        except Exception as e:
            print(f"  텍스트 생성 오류 (모델: {model}): {e}")
    return None


def strip_html(text: str) -> str:
    """HTML 태그를 제거해 순수 텍스트를 반환합니다."""
    return re.sub(r"<[^>]+>", "", text).strip()


def markdown_to_html_table(text: str) -> str:
    """
    마크다운 파이프 표를 HTML <table>로 변환합니다.

    입력 예:
      | 구분 | A은행 | B은행 |
      |------|-------|-------|
      | 금리 | 4.5%  | 5.1%  |

    출력: <table><thead>...</thead><tbody>...</tbody></table>
    """
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    # 파이프 행만 추출
    pipe_lines = [l for l in lines if l.startswith("|") and l.endswith("|")]
    if not pipe_lines:
        return text  # 마크다운 표 없으면 원본 반환

    # 구분선(|---|) 제외
    def is_separator(line: str) -> bool:
        return bool(re.match(r"^\|[\s\-:|]+\|$", line))

    data_lines = [l for l in pipe_lines if not is_separator(l)]
    if not data_lines:
        return text

    def parse_row(line: str) -> list[str]:
        # 앞뒤 | 제거 후 셀 분리
        return [cell.strip() for cell in line.strip("|").split("|")]

    rows = [parse_row(l) for l in data_lines]
    if not rows:
        return text

    header = rows[0]
    body   = rows[1:]

    th_cells = "".join(f"<th>{c}</th>" for c in header)
    thead = f"<thead><tr>{th_cells}</tr></thead>"

    tbody_rows = ""
    for row in body:
        td_cells = "".join(f"<td>{c}</td>" for c in row)
        tbody_rows += f"<tr>{td_cells}</tr>"
    tbody = f"<tbody>{tbody_rows}</tbody>"

    return f"<table>{thead}{tbody}</table>"


def apply_table_styles(html: str) -> str:
    """
    테이블에 Blogger에서도 유지되는 완전한 인라인 스타일을 적용합니다.
    - Gemini가 마크다운 코드블록(```html ... ```)으로 감싸는 경우 제거
    - HTML 속성(border, cellpadding)과 인라인 스타일을 함께 적용
    - 가독성을 위한 홀짝 행 처리는 CSS 클래스 대신 직접 <tr> 스타일 사용
    """
    # ── [디버그] 원본 TABLE 내용 출력 ─────────────
    preview = repr(html[:200]) if html else "(비어 있음)"
    print(f"\n  [표 디버그] apply_table_styles() 호출됨")
    print(f"  [표 디버그] 원본 길이: {len(html)}자")
    print(f"  [표 디버그] 원본 미리보기: {preview}")
    has_html_table  = "<table" in html.lower()
    has_pipe        = "|" in html
    print(f"  [표 디버그] <table> 태그 포함: {has_html_table} / 파이프(|) 포함: {has_pipe}")

    # ── 마크다운 코드블록 제거 ────────────────────
    html = re.sub(r"```(?:html)?\s*", "", html, flags=re.IGNORECASE)
    html = html.strip()

    # ── 마크다운 파이프 표 감지 → HTML 자동 변환 ──
    # "<table" 태그가 없고 파이프(|) 행이 있으면 마크다운 표로 판단
    if "<table" not in html.lower() and "|" in html:
        print(f"  [표 디버그] → markdown_to_html_table() 호출 (content_generator.py:235)")
        html = markdown_to_html_table(html)
        if "<table" in html.lower():
            print("    [표] 마크다운 → HTML 자동 변환 완료")
        else:
            print("    [표 디버그] 마크다운 변환 실패 — <table> 태그 생성 안 됨")
    elif has_html_table:
        print(f"  [표 디버그] → HTML <table> 감지됨, markdown_to_html_table() 건너뜀, 스타일 직접 적용")
    else:
        print(f"  [표 디버그] → 표 없음: markdown_to_html_table() 호출 안 됨")

    if not html or "<table" not in html.lower():
        print(f"  [표 디버그] → apply_table_styles() 반환: 빈 문자열 (표 없음 또는 변환 실패)")
        return ""
    print(f"  [표 디버그] → 인라인 스타일 적용 시작")

    # ── <table> 스타일 ────────────────────────────
    # border-left:none !important — Blogger 테마 기본 CSS가 왼쪽 파란 border를 강제 적용하는 것을 차단
    html = re.sub(
        r"<table[^>]*>",
        (
            '<table border="0" cellpadding="0" cellspacing="0" '
            'style="width:100%; border-collapse:collapse; '
            'border-left:none !important; border-right:none !important; '
            'border-top:1px solid #d0d0d0; border-bottom:1px solid #d0d0d0; '
            'outline:none !important; margin:24px 0; font-size:0.93em; '
            'table-layout:auto;">'
        ),
        html, flags=re.IGNORECASE,
    )

    # ── <thead> / <th> 스타일 ─────────────────────
    html = re.sub(
        r"<thead[^>]*>",
        '<thead style="background-color:#1565C0; color:#ffffff;">',
        html, flags=re.IGNORECASE,
    )
    html = re.sub(
        r"<th[^>]*>",
        (
            '<th style="padding:11px 14px; '
            'border-top:1px solid #d0d0d0; border-bottom:1px solid #d0d0d0; '
            'border-right:1px solid #b0c4de; border-left:none !important; '
            'text-align:left; font-weight:bold; '
            'background-color:#1565C0; color:#ffffff; '
            'white-space:nowrap;">'
        ),
        html, flags=re.IGNORECASE,
    )

    # ── <tbody> ───────────────────────────────────
    html = re.sub(r"<tbody[^>]*>", "<tbody>", html, flags=re.IGNORECASE)

    # ── <tr> 홀짝 행 배경색 ───────────────────────
    row_count = [0]
    def style_tr(m):
        row_count[0] += 1
        bg = "#f5f8ff" if row_count[0] % 2 == 0 else "#ffffff"
        return f'<tr style="background-color:{bg};">'
    html = re.sub(r"<tr[^>]*>", style_tr, html, flags=re.IGNORECASE)

    # ── <td> 스타일 ───────────────────────────────
    html = re.sub(
        r"<td[^>]*>",
        (
            '<td style="padding:10px 14px; '
            'border-top:1px solid #e8e8e8; border-bottom:1px solid #e8e8e8; '
            'border-right:1px solid #e8e8e8; border-left:none !important; '
            'vertical-align:top; line-height:1.65; color:#333333;">'
        ),
        html, flags=re.IGNORECASE,
    )

    # ── 스크롤 가능한 컨테이너로 감싸기 (모바일 대응) ──
    wrapped = (
        '<div style="overflow-x:auto; -webkit-overflow-scrolling:touch; '
        'margin:24px 0; border-radius:6px; '
        'box-shadow:0 2px 8px rgba(0,0,0,0.08);">'
        + html
        + '</div>'
    )
    print(f"  [표 디버그] → apply_table_styles() 완료, 결과 길이: {len(wrapped)}자")
    return wrapped


def parse_text_response(raw: str) -> dict:
    """##MARKER## 형식으로 응답을 파싱합니다."""
    markers = [
        "TITLE", "SUMMARY", "INTRO",
        "SECTION1_TITLE", "SECTION1_BODY",
        "TABLE_DATA",
        "SECTION2_TITLE", "SECTION2_BODY",
        "TIPBOX", "WARNBOX",
        "FAQ_Q1", "FAQ_A1", "FAQ_Q2", "FAQ_A2", "FAQ_Q3", "FAQ_A3",
        "OUTRO", "TAGS",
    ]
    data = {m: "" for m in markers}

    current = None
    buf = []

    for line in raw.splitlines():
        stripped = line.strip()
        found = False
        for m in markers:
            if stripped == f"##{m}##":
                if current:
                    data[current] = "\n".join(buf).strip()
                current, buf, found = m, [], True
                break
        if not found and current:
            buf.append(line)

    if current:
        data[current] = "\n".join(buf).strip()

    # 소제목에 Gemini가 <h2> 태그를 넣는 경우 제거 + 첫 줄만 사용 (본문 오버플로우 방지)
    for key in ("SECTION1_TITLE", "SECTION2_TITLE"):
        cleaned = re.sub(r"</?h[1-6][^>]*>", "", data[key]).strip()
        data[key] = cleaned.split("\n")[0].strip()

    # ── INTRO 오버플로우 감지 ────────────────────────────────────
    # Gemini가 SECTION1_BODY 내용을 INTRO에 몰아 넣는 경우:
    # INTRO 안에 <h2>/<h3> 태그가 있으면 첫 태그 이전을 진짜 INTRO로 유지하고
    # 나머지를 SECTION1_BODY로 이동합니다.
    intro = data["INTRO"]
    if intro and re.search(r'<h[23]', intro, re.IGNORECASE):
        first_h = re.search(r'<h[23]', intro, re.IGNORECASE)
        overflow = intro[first_h.start():].strip()
        data["INTRO"] = intro[:first_h.start()].strip()
        if overflow:
            if not data["SECTION1_BODY"].strip():
                data["SECTION1_BODY"] = overflow
            else:
                data["SECTION1_BODY"] = overflow + "\n" + data["SECTION1_BODY"]
        print(f"  [INTRO 오버플로우] <h2>/<h3> 감지 → SECTION1_BODY로 이동 ({len(overflow)}자)")

    # <p> 안에 <ol>/<ul>이 들어간 무효 HTML 수정 (LLM이 <ol>을 <p>로 감싸는 패턴)
    # 케이스1: <p>...</ol></p>  → </ol>
    # 케이스2: <p>...</ol> 뒤 </p> 없이 블록 요소 시작 → <p> 태그만 제거
    for body_key in ("INTRO", "SECTION1_BODY", "SECTION2_BODY"):
        if data[body_key]:
            # </p> 로 닫힌 경우
            data[body_key] = re.sub(
                r'<p>\s*\n?\s*(<(?:ol|ul)\b[^>]*>.*?</(?:ol|ul)>)\s*\n?\s*</p>',
                r'\1',
                data[body_key],
                flags=re.DOTALL | re.IGNORECASE,
            )
            # </p> 없이 끝나는 경우 (문자열 끝 또는 다음 블록 요소 직전)
            data[body_key] = re.sub(
                r'<p>\s*\n?\s*(<(?:ol|ul)\b[^>]*>.*?</(?:ol|ul)>)',
                r'\1',
                data[body_key],
                flags=re.DOTALL | re.IGNORECASE,
            )

    # SECTION_BODY 안 <ol>/<ul>이 ##TIPBOX## 앞에서 잘린 경우 닫힘 태그 보완
    # + TIPBOX/WARNBOX 앞에 잔여 리스트 태그 제거
    for body_key in ("SECTION1_BODY", "SECTION2_BODY"):
        body = data[body_key]
        open_ol = len(re.findall(r'<ol[\s>]', body, re.I)) - len(re.findall(r'</ol>', body, re.I))
        open_ul = len(re.findall(r'<ul[\s>]', body, re.I)) - len(re.findall(r'</ul>', body, re.I))
        if open_ol > 0:
            data[body_key] += '</ol>' * open_ol
        if open_ul > 0:
            data[body_key] += '</ul>' * open_ul

    for box_key in ("TIPBOX", "WARNBOX"):
        content = data[box_key]
        # <ol>/<ul> 안에서 마커가 분리될 때 흘러들어온 <li>, </li>, </ol>, </ul> 제거
        content = re.sub(r'^(\s*(</?li[^>]*>|</ol>|</ul>|<ol[^>]*>|<ul[^>]*>)\s*)+', '', content, flags=re.I)
        # HTML <strong>...</strong> 볼드 제거 (Gemini가 HTML 태그로 볼드 출력하는 경우)
        content = re.sub(r'<strong>([^<]*)</strong>', r'\1', content, flags=re.IGNORECASE)
        # **마크다운 볼드** 제거
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        # 중복 팁/주의 헤더 제거 — 한국어(전문가 팁, 주의/주의사항) + 영어(Expert Tip, Warning) 모두 처리
        content = re.sub(
            r'^[💡⚠️\s]*(?:전문가\s*팁|주의(?:사항?)?|Expert\s*Tip|Warning)[:\s\n]*',
            '', content.strip(), flags=re.IGNORECASE,
        )
        # 위 패턴에 걸리지 않은 나머지 선행 이모지 제거 (박스 헤더에 이미 표시됨)
        content = re.sub(r'^[💡⚠️]+\s*', '', content.strip())
        data[box_key] = content.strip()

    # 모든 본문 섹션에서 <b>/<strong> HTML 볼드 태그 제거 (CSS로 처리)
    for key in ("SUMMARY", "INTRO", "SECTION1_BODY", "SECTION2_BODY", "OUTRO"):
        if data[key]:
            data[key] = re.sub(r'</?(?:b|strong)(?:\s[^>]*)?>', '', data[key])

    # SECTION_BODY에 중복 삽입된 팁/주의 박스 마크다운 텍스트 제거
    # Gemini가 "💡 **전문가 팁**..." 를 SECTION_BODY 안에 직접 쓰고
    # 동시에 ##TIPBOX## 아래에도 출력하는 경우를 방어적으로 제거
    for key in ("SECTION1_BODY", "SECTION2_BODY"):
        if data[key]:
            # **마크다운 볼드** 제거 (SECTION_BODY는 별도 처리 없어 여기서 수행)
            data[key] = re.sub(r'\*\*([^*]+)\*\*', r'\1', data[key])
            # <p> 태그로 감싸진 팁/주의 헤더 줄 제거
            data[key] = re.sub(
                r'<p[^>]*>\s*[💡⚠️][^\n<]*</p>\s*',
                '', data[key], flags=re.IGNORECASE,
            )
            # 태그 없이 단독 줄로 나온 💡/⚠️ 헤더 제거
            data[key] = re.sub(r'(?m)^[💡⚠️][^\n]*\n?', '', data[key])

    # 본문 섹션 문단 후처리 (4문장 이상 → 2~3문장씩 새 <p> 분리)
    for key in ("INTRO", "SECTION1_BODY", "SECTION2_BODY"):
        if data[key]:
            data[key] = _split_long_paragraphs(data[key])

    # <h3> 뒤 나오는 태그 없는 텍스트를 <p>로 감싸기
    for key in ("SECTION1_BODY", "SECTION2_BODY"):
        if data[key]:
            data[key] = _wrap_text_after_h3(data[key])

    # <p>&nbsp;</p> 및 단독 <br> 태그 제거
    for key in ("INTRO", "SECTION1_BODY", "SECTION2_BODY", "OUTRO"):
        if data[key]:
            data[key] = _remove_forbidden_tags(data[key])

    # OUTRO 문장 분리 (각 문장을 개별 <p> 태그로)
    if data["OUTRO"]:
        data["OUTRO"] = _split_outro_sentences(data["OUTRO"])

    return data


def _wrap_text_after_h3(html: str) -> str:
    """
    <h3> 태그 직후에 <p> 태그 없이 나오는 텍스트를 <p>...</p>로 자동 감쌉니다.

    처리 대상:
      <h3>소제목</h3>
      텍스트가 바로 나오는 경우  →  <p>텍스트</p>로 변환

    처리 제외:
      <h3> 뒤에 <p>, <ol>, <ul>, <div>, <h2>, <h3> 등 블록 태그가 오는 경우
    """
    # <h3...>...</h3> 뒤에 공백/개행을 건너뛰고 블록 태그가 아닌 텍스트가 오는 패턴
    # 블록 태그: p, ol, ul, div, h1~h6, table, br
    BLOCK_TAGS = re.compile(r'^\s*<(?:p|ol|ul|div|h[1-6]|table|br)[\s>]', re.IGNORECASE)

    result = []
    pos = 0

    for m in re.finditer(r'(</h3>)([\s\n]*)', html, flags=re.IGNORECASE):
        result.append(html[pos:m.end()])
        pos = m.end()

        # h3 닫힘 이후 남은 텍스트 확인
        rest = html[pos:]
        if rest and not BLOCK_TAGS.match(rest):
            # 다음 블록 태그 또는 문자열 끝까지를 텍스트로 간주
            next_block = re.search(r'<(?:p|ol|ul|div|h[1-6]|table|br)[\s>]', rest, re.IGNORECASE)
            if next_block:
                raw_text = rest[:next_block.start()].strip()
                if raw_text:
                    result.append(f"<p>{raw_text}</p>\n")
                    pos += next_block.start()
            else:
                # 남은 전체가 텍스트인 경우는 건드리지 않음 (OUTRO 등 다른 처리와 충돌 방지)
                pass

    result.append(html[pos:])
    return "".join(result)


def _remove_forbidden_tags(html: str) -> str:
    """
    <p>&nbsp;</p> 공백 단락과 단독 <br> 태그를 제거합니다.
    <br><br>도 제거 (모든 간격은 CSS margin으로 처리).
    """
    # <p>&nbsp;</p> 또는 <p> </p> 형태 제거
    html = re.sub(r'<p[^>]*>\s*&nbsp;\s*</p>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<p[^>]*>\s*</p>', '', html, flags=re.IGNORECASE)
    # <ol>/<ul> 바깥의 단독 <br> 및 <br><br> 제거
    # (ol/ul 내부는 건드리지 않음)
    html = re.sub(r'<br\s*/?>\s*<br\s*/?>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'(?<!>)\s*<br\s*/?>\s*(?!<)', ' ', html, flags=re.IGNORECASE)
    return html.strip()


def _split_outro_sentences(html: str) -> str:
    """OUTRO 텍스트의 각 문장을 개별 <p> 태그로 분리합니다."""
    inner = re.sub(r"</?p[^>]*>", "", html).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", inner) if s.strip()]
    if len(sentences) <= 1:
        return f"<p>{inner}</p>" if inner else html
    return "\n".join(f"<p>{s}</p>" for s in sentences)


def _split_long_paragraphs(html: str) -> str:
    """
    모든 <p> 블록을 문장 수 기준으로 정규화합니다.

    규칙:
      - 1문장짜리 <p>는 다음 <p>와 합쳐서 2문장 블록으로 만듦
      - 2~3문장: 그대로 유지
      - 4문장 이상: 2~3문장씩 새 <p>로 분리
      - <ol>/<ul>/<table> 내부 포함 블록은 절대 건드리지 않음
      - 문장 경계: 한국어 마침표(.) / 물음표(?) / 느낌표(!) 뒤 공백
    """

    # ── STEP 1: 각 <p> 블록을 문장 단위로 파싱 ──────────────
    PROTECTED = re.compile(r"<(ol|ul|table|li)[\s>]", re.IGNORECASE)
    SEP       = re.compile(r'(?<=[.!?])\s+')

    Block = dict  # {"open": str, "sentences": list[str], "protected": bool}

    blocks: list[Block] = []
    last_end = 0
    prefix_parts: list[str] = []   # <p> 태그 사이의 비-<p> 텍스트(이미지 div 등)

    for m in re.finditer(r"<p(\s[^>]*)?>(.+?)</p>", html, flags=re.DOTALL | re.IGNORECASE):
        # <p> 앞 텍스트는 prefix로 보존
        if m.start() > last_end:
            prefix_parts.append(("raw", html[last_end:m.start()]))
        last_end = m.end()

        attrs    = m.group(1) or ""
        inner    = m.group(2)
        open_tag = f"<p{attrs}>" if attrs else "<p>"
        protected = bool(PROTECTED.search(inner))

        if protected:
            prefix_parts.append(("raw", m.group(0)))
        else:
            sents = [s.strip() for s in SEP.split(inner.strip()) if s.strip()]
            prefix_parts.append(("block", {"open": open_tag, "sentences": sents}))

    # 나머지 텍스트 보존
    if last_end < len(html):
        prefix_parts.append(("raw", html[last_end:]))

    # ── STEP 2: 1문장 블록을 다음 블록과 합치기 ─────────────
    merged: list = []
    i = 0
    while i < len(prefix_parts):
        kind, val = prefix_parts[i]
        if kind == "block" and len(val["sentences"]) == 1:
            # 바로 다음 block 찾기
            j = i + 1
            while j < len(prefix_parts) and prefix_parts[j][0] != "block":
                j += 1
            if j < len(prefix_parts) and prefix_parts[j][0] == "block":
                # 사이의 raw 텍스트는 삭제하고 두 블록을 합침
                merged_sents = val["sentences"] + prefix_parts[j][1]["sentences"]
                merged.append(("block", {"open": val["open"], "sentences": merged_sents}))
                i = j + 1
                continue
        merged.append((kind, val))
        i += 1

    # ── STEP 3: 4문장 이상 블록 분리 ────────────────────────
    def chunk_sentences(sents: list[str]) -> list[list[str]]:
        """4문장 이상을 2~3문장 그룹으로 나눠 새 <p>로 분리."""
        n = len(sents)
        if n <= 3:
            return [sents]
        groups = []
        idx = 0
        while idx < n:
            remaining = n - idx
            take = 3 if remaining % 2 == 1 and remaining > 2 else 2
            groups.append(sents[idx:idx + take])
            idx += take
        return groups

    # ── STEP 4: 최종 HTML 조립 ───────────────────────────────
    out_parts = []
    for kind, val in merged:
        if kind == "raw":
            out_parts.append(val)
        else:
            open_tag = val["open"]
            groups = chunk_sentences(val["sentences"])
            for g in groups:
                out_parts.append(f'{open_tag}{" ".join(g)}</p>')

    return "".join(out_parts)


# ──────────────────────────────────────────
# 2. JSON → HTML 표 변환
# ──────────────────────────────────────────

def json_to_html_table(json_str: str) -> str:
    """
    Gemini가 출력한 JSON 데이터를 인라인 스타일이 완전 적용된 HTML 표로 변환.

    입력: {"headers": ["구분", "A", "B"], "rows": [["행1", "값1", "값2"], ...]}
    출력: <div style="overflow-x:auto;..."><table ...>...</table></div>
    """
    import json as _json

    if not json_str or not json_str.strip():
        print("  [표 JSON] 빈 문자열 — TABLE_DATA 섹션 누락")
        return ""

    # 코드블록 마커 제거 (```json ... ``` 또는 ``` ... ```)
    clean = re.sub(r"```(?:json)?\s*", "", json_str, flags=re.IGNORECASE).strip()

    # JSON 파싱
    try:
        data = _json.loads(clean)
    except _json.JSONDecodeError as e:
        print(f"  [표 JSON] 파싱 실패: {e}")
        print(f"  [표 JSON] 원본: {repr(clean[:300])}")
        return ""

    headers = data.get("headers", [])
    rows    = data.get("rows", [])

    if not headers or not rows:
        print(f"  [표 JSON] headers={headers!r} / rows 개수={len(rows)} — 데이터 부족")
        return ""

    # ── <th> 셀 ───────────────────────────────
    th_style = (
        'style="padding:11px 14px; '
        'border-top:1px solid #d0d0d0; border-bottom:2px solid #1565C0; '
        'border-right:1px solid #5090d3; border-left:none !important; '
        'text-align:left; font-weight:bold; '
        'background-color:#1565C0; color:#ffffff; white-space:nowrap;"'
    )
    th_cells = "".join(f"<th {th_style}>{h}</th>" for h in headers)
    thead = (
        f'<thead>'
        f'<tr style="background-color:#1565C0;">{th_cells}</tr>'
        f'</thead>'
    )

    # ── <td> 셀 + 홀짝 행 배경 ────────────────
    td_style = (
        'style="padding:10px 14px; '
        'border-top:1px solid #e8e8e8; border-bottom:1px solid #e8e8e8; '
        'border-right:1px solid #e8e8e8; border-left:none !important; '
        'vertical-align:top; line-height:1.65; color:#333333;"'
    )
    tbody_rows = ""
    for i, row in enumerate(rows):
        bg = "#f5f8ff" if i % 2 == 1 else "#ffffff"
        td_cells = "".join(f"<td {td_style}>{cell}</td>" for cell in row)
        tbody_rows += f'<tr style="background-color:{bg};">{td_cells}</tr>'
    tbody = f"<tbody>{tbody_rows}</tbody>"

    # ── <table> ───────────────────────────────
    table = (
        '<table border="0" cellpadding="0" cellspacing="0" '
        'style="width:100%; border-collapse:collapse; '
        'border-left:none !important; border-right:none !important; '
        'border-top:1px solid #d0d0d0; border-bottom:1px solid #d0d0d0; '
        'outline:none !important; margin:24px 0; font-size:0.93em; table-layout:auto;">'
        f'{thead}{tbody}'
        '</table>'
    )

    # ── 모바일 스크롤 컨테이너 ────────────────
    wrapped = (
        '<div style="overflow-x:auto; -webkit-overflow-scrolling:touch; '
        'margin:24px 0; border-radius:6px; box-shadow:0 2px 8px rgba(0,0,0,0.08);">'
        + table + '</div>'
    )

    print(f"  [표 JSON → HTML] {len(headers)}열 × {len(rows)}행 변환 완료 ({len(wrapped)}자)")
    return wrapped


# ──────────────────────────────────────────
# 3. 이미지 키워드 추출
# ──────────────────────────────────────────

# ──────────────────────────────────────────
# 태그 기반 이미지 검색어 생성
# ──────────────────────────────────────────

# 이미지 검색에 너무 추상적이거나 짧아서 부적합한 한국어 태그
_ABSTRACT_TAGS = {
    "재테크", "절약", "정보", "팁", "가이드", "방법", "생활정보", "실용정보",
    "2026년", "2025년", "2026", "2025", "한국", "정책", "지원", "트렌드",
    "꿀팁", "추천", "비교", "분석", "총정리", "완전정복",
}


def _is_specific_tag(tag: str) -> bool:
    """이미지 검색에 충분히 구체적인 태그인지 판별합니다."""
    clean = re.sub(r"[#\s]", "", tag)
    if len(clean) < 3:                          # 3자 미만 제외
        return False
    if clean in _ABSTRACT_TAGS:                 # 추상 태그 제외
        return False
    if re.match(r"^\d{4}년?$", clean):          # 연도 단독 제외
        return False
    return True


def tags_to_image_queries(tags: list[str], keyword: str = "") -> list[str]:
    """
    블로그 태그 목록 → 이미지 검색용 영문 쿼리 3개

    1. 태그에서 추상적·짧은 것 제외, 가장 구체적인 태그 1개 선택
    2. deep-translator로 영문 번역
    3. 번역 결과로 쿼리 3개 생성:
       q1 — 번역된 전체 구문   (예: "fuel cost saving")
       q2 — 앞 2단어            (예: "fuel cost")
       q3 — 첫 단어 + "korea"  (예: "fuel korea")
    """
    fallback = "korea lifestyle daily"

    # 구체적인 태그 선택 (순서대로 첫 번째 적합한 것)
    selected = next((t for t in tags if _is_specific_tag(t)), None)

    if not selected:
        # 태그에서 못 찾으면 원본 키워드로 대체
        selected = keyword.strip() if keyword else ""
        if selected:
            print(f"  [이미지 키워드] 구체적 태그 없음 → 키워드 사용: '{selected}'")
        else:
            print(f"  [이미지 키워드] 태그·키워드 모두 없음 → 기본값 사용")
            return [fallback, fallback, fallback]

    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="ko", target="en").translate(selected)

        # 소문자 + 영문자·공백만
        clean = re.sub(r"[^a-z\s]", " ", translated.lower()).strip()
        words = [w for w in clean.split() if w and len(w) > 1]

        if not words:
            queries = [fallback] * 3
        else:
            q1 = " ".join(words[:4])
            q2 = " ".join(words[:2]) if len(words) >= 2 else words[0]
            q3 = words[0] + " korea"
            queries = [q1, q2, q3]

        print(f"  [이미지 키워드] 태그:'{selected}' → '{translated}' → {queries}")
        return queries

    except Exception as e:
        print(f"  [이미지 키워드] 번역 실패: {e}")
        return [fallback] * 3


# ──────────────────────────────────────────
# 3. 이미지 중복 방지 — used_images.json
# ──────────────────────────────────────────

_USED_IMAGES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "used_images.json")
_MAX_USED_IMAGES  = 500


def _load_used_images() -> list[str]:
    """used_images.json에서 사용된 이미지 소스 URL 목록을 로드합니다."""
    try:
        if os.path.exists(_USED_IMAGES_FILE):
            with open(_USED_IMAGES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception:
        pass
    return []


def _save_used_images(urls: list[str]) -> None:
    """used_images.json에 URL 목록을 저장합니다. 500개 초과 시 오래된 것부터 삭제."""
    if len(urls) > _MAX_USED_IMAGES:
        removed = len(urls) - _MAX_USED_IMAGES
        urls = urls[-_MAX_USED_IMAGES:]
        print(f"    [중복방지] 오래된 항목 {removed}개 삭제 (상한 {_MAX_USED_IMAGES}개)")
    try:
        with open(_USED_IMAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(urls, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"    [중복방지] 저장 실패: {e}")


def _record_used_image(url: str) -> None:
    """이미지 소스 URL을 used_images.json에 추가합니다."""
    urls = _load_used_images()
    if url not in urls:
        urls.append(url)
        _save_used_images(urls)


# ──────────────────────────────────────────
# 4. 이미지 유틸리티
# ──────────────────────────────────────────

def to_webp_bytes(image_bytes: bytes) -> bytes:
    """이미지 바이트를 WebP로 변환합니다. 실패 시 원본 반환."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="WebP", quality=82, method=4)
        return buf.getvalue()
    except Exception as e:
        print(f"    WebP 변환 실패, 원본 사용: {str(e)[:50]}")
        return image_bytes


def _cloudinary_configured() -> bool:
    return bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)


def upload_to_cloudinary(image_bytes: bytes) -> str | None:
    """
    Cloudinary SDK로 이미지를 업로드하고 최적화 URL을 반환합니다.
    - quality="auto:good": 화질/용량 자동 균형
    - 설정 미완료 시 None 반환
    """
    if not _cloudinary_configured():
        return None
    try:
        result = cloudinary.uploader.upload(
            image_bytes,
            resource_type="image",
            quality="auto:good",
        )
        return result["secure_url"]
    except Exception as e:
        print(f"    Cloudinary 업로드 실패: {str(e)[:70]}")
    return None


# ──────────────────────────────────────────
# 3. 이미지 소스별 함수 (URL 반환, base64 없음)
# ──────────────────────────────────────────

# 차단 키워드 — alt/tags/description에 포함 시 해당 이미지 제외
_IMG_BLOCKED_TERMS = {
    "north korea", "pyongyang", "kim jong", "kim il",
    "military parade", "communist", "propaganda",
    "nuclear", "missile", "dictatorship",
}


def _is_safe_image(photo: dict) -> bool:
    """
    Unsplash 사진 객체에서 민감 키워드를 검사합니다.
    alt_description / description / tags 중 하나라도 차단어 포함 시 False 반환.
    """
    check_texts = [
        (photo.get("alt_description") or "").lower(),
        (photo.get("description") or "").lower(),
    ]
    for tag in photo.get("tags", []):
        check_texts.append((tag.get("title") or "").lower())

    for text in check_texts:
        for blocked in _IMG_BLOCKED_TERMS:
            if blocked in text:
                return False
    return True


def _is_safe_pixabay(hit: dict) -> bool:
    """
    Pixabay 이미지 객체에서 민감 키워드를 검사합니다.
    tags 필드(쉼표 구분 문자열)를 검사합니다.
    """
    tags_text = (hit.get("tags") or "").lower()
    for blocked in _IMG_BLOCKED_TERMS:
        if blocked in tags_text:
            return False
    return True


def fetch_unsplash_image(keyword: str) -> str | None:
    """
    1순위: Unsplash search/photos API
    - content_filter=high 로 민감 이미지 사전 필터
    - 민감 키워드 포함 이미지 추가 차단 (_IMG_BLOCKED_TERMS)
    - per_page=20 결과 중 미사용 이미지를 랜덤 선택
    - Cloudinary 설정 시: WebP 변환 → Cloudinary 업로드
    """
    if not UNSPLASH_ACCESS_KEY or UNSPLASH_ACCESS_KEY.startswith("여기에"):
        return None

    used = set(_load_used_images())

    try:
        r = requests.get(
            "https://api.unsplash.com/search/photos",
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            params={
                "query": keyword,
                "orientation": "landscape",
                "content_filter": "high",   # safe_search
                "per_page": 20,
            },
            timeout=8,
        )
        r.raise_for_status()
        results = r.json().get("results", [])

        if not results:
            print(f"    [1순위] Unsplash 결과 없음: '{keyword}'")
            return None

        # 민감 이미지 차단 → 미사용 필터 → 랜덤 선택
        safe    = [p for p in results if _is_safe_image(p)]
        blocked = len(results) - len(safe)
        if blocked:
            print(f"    [1순위] Unsplash 민감 이미지 {blocked}개 차단")
        if not safe:
            print(f"    [1순위] Unsplash 안전 이미지 없음: '{keyword}'")
            return None

        unused = [p for p in safe if p["urls"]["regular"] not in used]
        pool   = unused if unused else safe
        label  = f"미사용 {len(unused)}/{len(safe)}개 중 랜덤" if unused else "전부 사용됨, 재사용"

        photo   = random.choice(pool)
        img_url = photo["urls"]["regular"]

        if _cloudinary_configured():
            img_bytes = requests.get(img_url, timeout=15).content
            webp = to_webp_bytes(img_bytes)
            cdn_url = upload_to_cloudinary(webp)
            if cdn_url:
                _record_used_image(img_url)
                print(f"    [1순위] Unsplash → Cloudinary ({len(webp)//1024}KB) [{label}]")
                return cdn_url

        _record_used_image(img_url)
        print(f"    [1순위] Unsplash 직접 사용 [{label}]")
        return img_url

    except Exception as e:
        print(f"    [1순위] Unsplash 실패: {str(e)[:70]}")
    return None


def fetch_pixabay_image(keyword: str) -> str | None:
    """
    2순위: Pixabay API
    - safesearch=true + category=backgrounds 로 뉴스/정치 이미지 배제
    - 민감 키워드 포함 이미지 추가 차단 (_IMG_BLOCKED_TERMS)
    - per_page=20 결과 중 미사용 이미지를 랜덤 선택
    - Cloudinary 설정 시: WebP 변환 → Cloudinary 업로드
    """
    if not PIXABAY_API_KEY:
        return None

    used = set(_load_used_images())

    try:
        r = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": PIXABAY_API_KEY,
                "q": keyword,
                "image_type": "photo",
                "orientation": "horizontal",
                "safesearch": "true",
                "per_page": 20,
                "lang": "en",
            },
            timeout=8,
        )
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            print(f"    [2순위] Pixabay 결과 없음: '{keyword}'")
            return None

        # 민감 이미지 차단 → 미사용 필터 → 랜덤 선택
        def _src(h): return h.get("largeImageURL") or h.get("webformatURL", "")

        safe    = [h for h in hits if _src(h) and _is_safe_pixabay(h)]
        blocked = len(hits) - len(safe)
        if blocked:
            print(f"    [2순위] Pixabay 민감 이미지 {blocked}개 차단")
        if not safe:
            print(f"    [2순위] Pixabay 안전 이미지 없음: '{keyword}'")
            return None

        unused = [h for h in safe if _src(h) not in used]
        pool   = unused if unused else safe
        label  = f"미사용 {len(unused)}/{len(safe)}개 중 랜덤" if unused else "전부 사용됨, 재사용"

        hit     = random.choice(pool)
        img_url = _src(hit)

        if _cloudinary_configured():
            img_bytes = requests.get(img_url, timeout=15).content
            webp = to_webp_bytes(img_bytes)
            cdn_url = upload_to_cloudinary(webp)
            if cdn_url:
                _record_used_image(img_url)
                print(f"    [2순위] Pixabay → Cloudinary ({len(webp)//1024}KB) [{label}]")
                return cdn_url

        _record_used_image(img_url)
        print(f"    [2순위] Pixabay 직접 사용 [{label}]")
        return img_url

    except Exception as e:
        print(f"    [2순위] Pixabay 실패: {str(e)[:70]}")
    return None


def get_image(img_prompt: str, fallback_keyword: str) -> str | None:
    """
    이미지 폴백 체인 (URL 반환, base64 없음):
      1순위: Unsplash API
      2순위: Pixabay API
    Imgur Client ID 설정 시 → WebP 변환 후 Imgur 영구 호스팅 URL 사용
    """
    search_term = img_prompt if img_prompt else fallback_keyword

    src = fetch_unsplash_image(search_term)
    if src:
        return src

    src = fetch_pixabay_image(search_term)
    if src:
        return src

    print(f"    모든 이미지 소스 실패: '{search_term}'")
    return None


# ──────────────────────────────────────────
# 4. HTML 조립
# ──────────────────────────────────────────

def img_tag(src: str | None, alt: str) -> str:
    if not src:
        return ""
    return (
        f'<div style="text-align:center; margin:28px 0;">'
        f'<img src="{src}" alt="{alt}" '
        f'style="max-width:100%; height:auto; border-radius:10px; '
        f'box-shadow:0 4px 14px rgba(0,0,0,0.13);">'
        f'</div>'
    )


def summary_box(summary_text: str) -> str:
    label = "Key Takeaways" if LANGUAGE == "en" else "핵심 요약"
    lines = [l.strip() for l in summary_text.strip().splitlines() if l.strip()]
    items = "".join(f"<li style='margin:7px 0; line-height:1.7;'>{l}</li>" for l in lines)
    return (
        '<div style="background:#e8f4fd; border-left:5px solid #1976D2; '
        'padding:18px 22px; margin:26px 0; border-radius:8px;">'
        f'<p style="margin:0 0 10px 0; font-weight:bold; font-size:1.05em; '
        f'color:#1565C0;">{label}</p>'
        f'<ul style="margin:0; padding-left:22px; line-height:1.8;">{items}</ul>'
        '</div>'
    )


def tip_box(content: str) -> str:
    label = "💡 Expert Tip" if LANGUAGE == "en" else "💡 전문가 팁"
    return (
        '<div style="background:#fff8e1; border-left:5px solid #F9A825; '
        'padding:18px 22px; margin:32px 0; border-radius:8px;">'
        f'<p style="margin:0 0 10px 0; font-weight:bold; color:#E65100;">'
        f'{label}</p>'
        f'<p style="margin:0; line-height:1.8; color:#333;">{content}</p>'
        '</div>'
    )


def warn_box(content: str) -> str:
    label = "⚠️ Warning" if LANGUAGE == "en" else "⚠️ 주의사항"
    return (
        '<div style="background:#fff3e0; border-left:5px solid #e53935; '
        'padding:18px 22px; margin:32px 0; border-radius:8px;">'
        f'<p style="margin:0 0 10px 0; font-weight:bold; color:#c62828;">'
        f'{label}</p>'
        f'<p style="margin:0; line-height:1.8; color:#333;">{content}</p>'
        '</div>'
    )


def faq_section(d: dict) -> str:
    faq_title = "Frequently Asked Questions" if LANGUAGE == "en" else "자주 묻는 질문 (FAQ)"
    html = (
        f'<h2 style="margin-top:36px; margin-bottom:16px; '
        f'font-size:1.25em; color:#1a1a1a;">{faq_title}</h2>\n'
    )
    for i in range(1, 4):
        q = d.get(f"FAQ_Q{i}", "").strip()
        a = d.get(f"FAQ_A{i}", "").strip()
        if not q:
            continue
        # Gemini가 FAQ 답변에 <p> 태그를 포함하는 경우 제거 — 중첩 <p> 방지
        a_clean = re.sub(r'</?p[^>]*>', '', a).strip()
        html += (
            '<div style="background:#f9f9f9; border:1px solid #e0e0e0; '
            'padding:16px 20px; margin:14px 0; border-radius:8px;">'
            f'<p style="margin:0 0 8px 0; font-weight:bold; color:#1565C0;">'
            f'Q. {q}</p>'
            f'<p style="margin:0; line-height:1.8; color:#444;">A. {a_clean}</p>'
            '</div>\n'
        )
    return html


def _style_inline_tables(body: str) -> str:
    """
    section body 텍스트 안에 Gemini가 직접 심은 <table> 또는 마크다운 파이프 표를
    apply_table_styles()로 스타일 처리합니다.
    처리된 표가 없으면 원본 반환.
    """
    # 이미 스타일이 적용된 경우 (overflow-x:auto 포함) 건너뜀
    if 'overflow-x:auto' in body:
        return body

    def replace_table(m):
        styled = apply_table_styles(m.group(0))
        return styled if styled else m.group(0)

    # HTML <table>...</table> 블록 교체
    body = re.sub(r"<table[\s\S]*?</table>", replace_table, body, flags=re.IGNORECASE)

    # 마크다운 파이프 표 블록 교체 (연속된 | 시작 줄)
    def replace_md_table(m):
        styled = apply_table_styles(m.group(0))
        return styled if styled else m.group(0)

    body = re.sub(
        r"(?m)^(\|.+\n)+",
        replace_md_table,
        body,
    )
    return body


def assemble_html(d: dict, images: list[str | None]) -> str:
    img1, img2, img3 = images[0], images[1], images[2]

    # 빈 H2 태그 방지 — Gemini가 빈 값 반환 시 언어별 폴백 제목 사용
    section1_title = d["SECTION1_TITLE"].strip() or ("Key Information" if LANGUAGE == "en" else "핵심 정보")
    section2_title = d["SECTION2_TITLE"].strip() or ("Practical Tips & Takeaways" if LANGUAGE == "en" else "실용 팁 & 정리")

    html = ""
    html += summary_box(d["SUMMARY"])
    html += d["INTRO"] + "\n"
    # 이미지1: INTRO 다음, 첫 번째 H2 이전에 배치 (대표 이미지)
    html += img_tag(img1, section1_title)
    html += (
        f'<h2 style="margin-top:32px; margin-bottom:14px; font-size:1.3em; '
        f'color:#1a1a1a;">{section1_title}</h2>\n'
    )
    # section body 안에 표가 들어온 경우도 스타일 처리 (안전망)
    html += _style_inline_tables(d["SECTION1_BODY"]) + "\n"

    # ── TABLE_DATA JSON → HTML 표 변환 ──────────
    raw_json = d.get("TABLE_DATA", "")
    print(f"\n  [표] ##TABLE_DATA## 파싱 결과 길이: {len(raw_json)}자")
    table_html = json_to_html_table(raw_json)
    if table_html:
        html += table_html + "\n"
    else:
        print("  [표] 경고: json_to_html_table() 실패 → 표 없이 진행")
    html += (
        f'<h2 style="margin-top:32px; margin-bottom:14px; font-size:1.3em; '
        f'color:#1a1a1a;">{section2_title}</h2>\n'
    )
    html += _style_inline_tables(d["SECTION2_BODY"]) + "\n"
    html += img_tag(img2, section2_title)
    html += tip_box(d["TIPBOX"])
    if d.get("WARNBOX", "").strip():
        html += warn_box(d["WARNBOX"])
    html += faq_section(d)
    disclaimer = (
        "※ This content is based on 2026 data and may change with policy or market updates."
        if LANGUAGE == "en" else
        "※ 본 내용은 2026년 기준이며 정책 변경 시 달라질 수 있습니다."
    )
    html += (
        f'<p style="margin:24px 0 8px 0; font-size:0.85em; color:#888; '
        f'border-top:1px solid #e0e0e0; padding-top:14px;">'
        f'{disclaimer}</p>\n'
    )
    html += img_tag(img3, "마무리 이미지")
    html += d["OUTRO"] + "\n"

    return html


# ──────────────────────────────────────────
# 5. 메인 함수
# ──────────────────────────────────────────

def generate_blog_post(keyword: str) -> dict | None:
    """
    키워드 → 텍스트 생성 → 이미지 생성(WebP) → HTML 조립
    반환: {"title", "content", "tags", "keyword", "description"}
    """
    print(f"\n{'='*52}")
    print(f"블로그 글 생성 시작: [{keyword}]")
    print(f"{'='*52}")

    # 1) 텍스트
    d = generate_text_content(keyword)
    if not d:
        return None

    # 제목 확보
    clean_title = strip_html(d["TITLE"])

    # 태그를 이미지 검색 전에 먼저 추출
    tags = [t.strip().lstrip("#") for t in d["TAGS"].split(",") if t.strip()]

    # 2) 이미지 3장 — 태그 기반 영문 쿼리로 검색
    print("\n  [이미지 검색 중 — 1순위:Unsplash / 2순위:Pixabay]")
    img_queries = tags_to_image_queries(tags, keyword=keyword)
    images = []
    for i, query in enumerate(img_queries, 1):
        print(f"    [{i}/3] 검색어: {query}")
        src = get_image(query, keyword)
        images.append(src)

    # 3) HTML 조립
    content_html = assemble_html(d, images)

    print(f"\n  제목: {clean_title}")
    print(f"  태그: {', '.join(tags)}")
    print(f"  본문 길이: {len(content_html):,}자")

    return {
        "title":   clean_title,
        "content": content_html,
        "tags":    tags,
        "keyword": keyword,
    }


# ──────────────────────────────────────────
# 직접 실행 시 테스트
# ──────────────────────────────────────────

if __name__ == "__main__":
    from trend_collector import get_trending_keywords

    keywords = get_trending_keywords(count=5)
    if not keywords:
        keywords = ["청년도약계좌"]

    post = generate_blog_post(keywords[0])

    if post:
        with open("test_output.txt", "w", encoding="utf-8") as f:
            f.write(f"[제목]\n{post['title']}\n\n")
            f.write(f"[태그]\n{', '.join(post['tags'])}\n\n")
            f.write(f"[본문 길이] {len(post['content']):,}자\n\n")
            f.write(f"[본문]\n{post['content']}")
        print("\ntest_output.txt 저장 완료")
        print("=" * 52)
        print("전체 파이프라인 테스트 성공!")
