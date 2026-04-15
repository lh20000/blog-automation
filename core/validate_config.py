"""
validate_config.py — configs/ 폴더의 설정 파일 유효성 검사
Hook에서 자동 호출됨: python core/validate_config.py
"""

import sys
import os
import importlib.util

REQUIRED_KEYS = [
    "BLOG_NAME",
    "BLOG_LANGUAGE",
    "GEMINI_API_KEY",
    "TEXT_MODEL",
    "FALLBACK_MODELS",
    "CATEGORIES",
    "STATES_DIR",
    "CREDENTIALS_FILE",
    "TOKEN_FILE",
]

CONFIG_FILES = [
    "configs/config_ohopick.py",
    "configs/config_ahapick.py",
]


def validate(config_path: str) -> bool:
    if not os.path.exists(config_path):
        print(f"[validate_config] SKIP — file not found: {config_path}")
        return True

    spec = importlib.util.spec_from_file_location("cfg", config_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"[validate_config] ERROR loading {config_path}: {e}")
        return False

    missing = [k for k in REQUIRED_KEYS if not hasattr(mod, k)]
    if missing:
        print(f"[validate_config] MISSING keys in {config_path}: {missing}")
        return False

    print(f"[validate_config] OK — {config_path}")
    return True


if __name__ == "__main__":
    results = [validate(p) for p in CONFIG_FILES]
    sys.exit(0 if all(results) else 1)
