# CLAUDE.md — blog-automation (통합 레포)

> 오호픽(한국어) + ahapick(영어) 블로그 자동화 공통 레포.
> 새 세션에서도 이 파일 하나로 전체 구조를 파악할 수 있도록 작성됨.

---

## 1. 레포 개요

| 항목 | 값 |
|------|-----|
| 레포 | lh20000/blog-automation |
| 포함 블로그 | 오호픽 (ko) + ahapick (en) |
| 공통 core | `core/` — 에이전트·유틸 공통 모듈 |
| 블로그별 설정 | `configs/config_ohopick.py` / `configs/config_ahapick.py` |
| 블로그별 상태 | `states/ohopick/` / `states/ahapick/` |

---

## 2. 폴더 구조

```
blog-automation/
├── core/                      # 공통 파이프라인 모듈
│   ├── orchestrator.py        # 전체 파이프라인 관리
│   ├── writer_agent.py        # RSS 트렌드 수집 + Gemini 초안 생성
│   ├── reviewer_agent.py      # 팩트체크 + 구조 검증
│   ├── seo_agent.py           # SEO 최적화
│   ├── publisher_agent.py     # Blogger API 발행
│   ├── scheduler_agent.py     # 일일 한도·간격·카테고리 균형 체크
│   ├── trend_collector.py     # RSS 키워드 수집
│   ├── content_generator.py   # Gemini 텍스트 생성 + Cloudinary 이미지 업로드
│   ├── blogger_poster.py      # Google Blogger OAuth2 + API
│   ├── fact_checker.py        # 팩트체크·구조검증 규칙
│   ├── repair_posts.py        # 초안 글 HTML 수정 후 재발행
│   └── validate_config.py     # configs/ 유효성 검사 (hook용)
│
├── configs/
│   ├── config_ohopick.py      # 오호픽 전용 설정
│   └── config_ahapick.py      # ahapick 전용 설정
│
├── states/
│   ├── ohopick/               # 오호픽 상태 파일들 (published_log.json 등)
│   └── ahapick/               # ahapick 상태 파일들
│
├── .github/workflows/
│   ├── ohopick_schedule.yml   # 오호픽 자동 발행 (하루 N회)
│   └── ahapick_schedule.yml   # ahapick 자동 발행 (하루 4회)
│
├── .claude/
│   └── settings.json          # Claude Code hook 설정
│
├── CLAUDE.md                  # 이 파일
├── requirements.txt           # 공통 Python 패키지
└── .gitignore
```

---

## 3. config 파일 구조

각 블로그의 config는 `configs/` 하위에 분리됨.  
core 모듈들은 실행 시 환경변수 `BLOG_TARGET=ohopick|ahapick`을 읽어  
해당 config를 동적으로 임포트:

```python
# 예시 (orchestrator.py 상단)
import os, importlib
target = os.environ.get("BLOG_TARGET", "ohopick")
cfg = importlib.import_module(f"configs.config_{target}")
```

### config_ohopick.py 주요 변수

| 변수 | 설명 |
|------|------|
| `BLOG_NAME` | `"ohopick"` |
| `BLOG_LANGUAGE` | `"ko"` |
| `BLOG_ID` | `OHOPICK_BLOG_ID` env (또는 `BLOG_ID` fallback) |
| `NAVER_CLIENT_ID/SECRET` | 네이버 트렌드 수집용 |
| `STATES_DIR` | `"states/ohopick"` |

### config_ahapick.py 주요 변수

| 변수 | 설명 |
|------|------|
| `BLOG_NAME` | `"ahapick"` |
| `BLOG_LANGUAGE` | `"en"` |
| `BLOG_ID` | `AHAPICK_BLOG_ID` env (또는 `BLOG_ID` fallback) |
| `STATES_DIR` | `"states/ahapick"` |

---

## 4. GitHub Secrets 구조

두 블로그를 같은 레포에서 운영하므로 Secret 이름에 블로그 접두어 사용:

| Secret | 용도 |
|--------|------|
| `GEMINI_API_KEY` | 공통 (두 블로그 동일 키 사용 가능) |
| `OHOPICK_BLOG_ID` | 오호픽 Blogger ID |
| `AHAPICK_BLOG_ID` | ahapick Blogger ID |
| `OHOPICK_CREDENTIALS_JSON` | 오호픽 OAuth2 credentials |
| `OHOPICK_TOKEN_JSON` | 오호픽 OAuth2 token |
| `AHAPICK_CREDENTIALS_JSON` | ahapick OAuth2 credentials |
| `AHAPICK_TOKEN_JSON` | ahapick OAuth2 token |
| `NAVER_CLIENT_ID` | 오호픽 트렌드 수집 |
| `NAVER_CLIENT_SECRET` | 오호픽 트렌드 수집 |
| `UNSPLASH_ACCESS_KEY` | 공통 이미지 검색 |
| `PIXABAY_API_KEY` | 공통 이미지 검색 |
| `CLOUDINARY_CLOUD_NAME` | 공통 이미지 호스팅 |
| `CLOUDINARY_API_KEY` | 공통 이미지 호스팅 |
| `CLOUDINARY_API_SECRET` | 공통 이미지 호스팅 |

---

## 5. Claude Code Hook 설정

`.claude/settings.json` — Edit/Write 시 자동 실행:

1. **Syntax check**: `python -m py_compile` — 문법 오류 즉시 감지
2. **Config validate**: `core/validate_config.py` — 필수 키 누락 확인

---

## 6. 개발 로드맵

- [ ] core 모듈을 `BLOG_TARGET` 환경변수로 동적 config 로드하도록 리팩터링
- [ ] ohopick_schedule.yml / ahapick_schedule.yml 워크플로우 작성
- [ ] states/ 하위 초기화 스크립트 작성
- [ ] 두 블로그 동시 발행 테스트
