# CLAUDE.md — blog-automation (통합 레포)

## 1. 레포 개요
- 레포: lh20000/blog-automation
- 포함 블로그: 오호픽(ko) / ahapick(en) / 픽스IT연구소(ko) / Fix IT Lab(en) / Fix AI Lab(en)
- 공통 파이프라인: core/
- 블로그별 설정: configs/
- 블로그별 상세 지침: docs/

## 2. 폴더 구조
```
blog-automation/
├── core/
│   ├── orchestrator.py
│   ├── writer_agent.py
│   ├── reviewer_agent.py
│   ├── seo_agent.py
│   ├── publisher_agent.py
│   ├── scheduler_agent.py
│   ├── trend_collector.py
│   ├── content_generator.py
│   ├── blogger_poster.py
│   ├── fact_checker.py
│   ├── repair_posts.py
│   └── validate_config.py
├── configs/
│   ├── config_ohopick.py
│   ├── config_ahapick.py
│   ├── config_fixitkr.py
│   ├── config_fixiten.py
│   └── config_fixai.py
├── docs/
│   ├── blog_ohopick.md
│   ├── blog_ahapick.md
│   ├── blog_fixitkr.md
│   ├── blog_fixiten.md
│   └── blog_fixai.md
├── states/
│   ├── ohopick/
│   ├── ahapick/
│   ├── fixitkr/
│   ├── fixiten/
│   └── fixai/
├── .github/workflows/
│   ├── ohopick_schedule.yml
│   ├── ahapick_schedule.yml
│   ├── fixailab_schedule.yml
│   ├── fixitlab_schedule.yml
│   └── fixitlab_ko_schedule.yml
├── CLAUDE.md
├── requirements.txt
└── .gitignore
```

## 3. 블로그별 docs 참조 규칙 (필수)
특정 블로그 작업 전 반드시 해당 docs 파일을 먼저 읽을 것.

| 블로그 | config 파일 | docs 파일 |
|--------|------------|-----------|
| 오호픽 | config_ohopick.py | docs/blog_ohopick.md |
| ahapick | config_ahapick.py | docs/blog_ahapick.md |
| 픽스IT연구소 | config_fixitkr.py | docs/blog_fixitkr.md |
| Fix IT Lab | config_fixiten.py | docs/blog_fixiten.md |
| Fix AI Lab | config_fixai.py | docs/blog_fixai.md |

## 4. 공통 파이프라인 흐름
BLOG_TARGET 환경변수로 블로그 선택
→ 해당 config 로드
→ 해당 docs 파일 로드
→ trend_collector → writer_agent → reviewer_agent
→ seo_agent → publisher_agent

## 5. GitHub Secrets
- GEMINI_API_KEY
- OPENAI_API_KEY
- OHOPICK_BLOG_ID / AHAPICK_BLOG_ID
- FIXITKR_BLOG_ID / FIXITEN_BLOG_ID / FIXAI_BLOG_ID
- OAuth2 credentials/token (블로그별)
- UNSPLASH_ACCESS_KEY / PIXABAY_API_KEY
- CLOUDINARY_CLOUD_NAME / API_KEY / API_SECRET

## 6. 개발 규칙
- 모든 API 키는 os.environ.get()으로만 읽기 (하드코딩 금지)
- 새 블로그 추가 시 config + docs + workflow + states 폴더 함께 생성
- 작업 전 반드시 해당 블로그 docs 파일 확인

## 7. Claude Code Hook
- Syntax check: python -m py_compile
- Config validate: core/validate_config.py
