"""
validate_config.py - configs/ 설정 파일 유효성 검사

Claude Code hook에서 자동 호출:
  python core/validate_config.py

수동 실행:
  python core/validate_config.py              # 두 파일 모두 검사
  python core/validate_config.py ohopick      # 특정 블로그만 검사
"""

import sys
import os
import importlib.util

# ──────────────────────────────────────────────────────────────
# 필수 키 정의
# ──────────────────────────────────────────────────────────────

# 반드시 존재해야 하는 키 (None이어도 존재는 해야 함)
REQUIRED_KEYS = [
    "BLOG_ID",        # Blogger Blog ID (런타임에 env에서 주입)
    "LANGUAGE",       # "ko" or "en"
    "CATEGORIES",     # 카테고리 목록 (list)
    "TEXT_MODEL",     # Gemini 모델명
]

# 추가 권장 키 (없으면 경고만, 실패 처리 안 함)
RECOMMENDED_KEYS = [
    "BLOG_NAME",
    "STATES_DIR",
    "CREDENTIALS_FILE",
    "TOKEN_FILE",
]

CONFIG_FILES = {
    "ohopick": "configs/config_ohopick.py",
    "ahapick": "configs/config_ahapick.py",
}


def validate(target: str, config_path: str) -> bool:
    print(f"\n[validate_config] ── {target} ({config_path}) ──")

    if not os.path.exists(config_path):
        print(f"  SKIP - 파일 없음: {config_path}")
        return True

    spec = importlib.util.spec_from_file_location("cfg_check", config_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"  ERROR - 로드 실패: {e}")
        return False

    ok = True

    # ── 필수 키 검사 ──────────────────────────────────────────
    missing = [k for k in REQUIRED_KEYS if not hasattr(mod, k)]
    if missing:
        print(f"  ERROR - 필수 키 누락: {missing}")
        ok = False
    else:
        print(f"  OK    - 필수 키 ({', '.join(REQUIRED_KEYS)}) 모두 존재")

    # ── 값 타입 검사 ──────────────────────────────────────────
    if hasattr(mod, "CATEGORIES"):
        cats = getattr(mod, "CATEGORIES")
        if not isinstance(cats, list) or len(cats) == 0:
            print(f"  ERROR - CATEGORIES는 비어있지 않은 list여야 합니다. 현재: {cats!r}")
            ok = False
        else:
            print(f"  OK    - CATEGORIES: {len(cats)}개 항목")

    if hasattr(mod, "LANGUAGE"):
        lang = getattr(mod, "LANGUAGE")
        if lang not in ("ko", "en"):
            print(f"  WARN  - LANGUAGE='{lang}' (예상값: 'ko' 또는 'en')")

    if hasattr(mod, "TEXT_MODEL"):
        model = getattr(mod, "TEXT_MODEL")
        if not model:
            print(f"  ERROR - TEXT_MODEL이 비어 있습니다")
            ok = False
        else:
            print(f"  OK    - TEXT_MODEL: {model}")

    if hasattr(mod, "BLOG_ID"):
        blog_id = getattr(mod, "BLOG_ID")
        if blog_id is None:
            print(f"  WARN  - BLOG_ID=None (런타임 env 주입 필요: OHOPICK_BLOG_ID / AHAPICK_BLOG_ID)")

    # ── 권장 키 검사 ─────────────────────────────────────────
    missing_rec = [k for k in RECOMMENDED_KEYS if not hasattr(mod, k)]
    if missing_rec:
        print(f"  WARN  - 권장 키 누락: {missing_rec}")

    status = "OK" if ok else "FAIL"
    print(f"  결과  - [{status}]")
    return ok


if __name__ == "__main__":
    # 인자로 특정 블로그 지정 가능: python core/validate_config.py ohopick
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(CONFIG_FILES.keys())
    invalid = [t for t in targets if t not in CONFIG_FILES]
    if invalid:
        print(f"[validate_config] 알 수 없는 대상: {invalid}")
        print(f"  사용 가능: {list(CONFIG_FILES.keys())}")
        sys.exit(1)

    results = [validate(t, CONFIG_FILES[t]) for t in targets]
    all_ok = all(results)

    print(f"\n[validate_config] 최종 결과: {'✅ 모두 통과' if all_ok else '❌ 실패 있음'}")
    sys.exit(0 if all_ok else 1)
