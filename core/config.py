# =============================================
# core/config.py — 동적 config 브릿지
# =============================================
# 에이전트 파일들이 "from config import ..."로 직접 임포트할 때
# BLOG_TARGET 환경변수에 따라 올바른 config를 자동 선택합니다.
#
#   BLOG_TARGET=ohopick  →  configs/config_ohopick.py
#   BLOG_TARGET=ahapick  →  configs/config_ahapick.py
#   미설정               →  ohopick 기본
# =============================================

import os
import sys
import importlib

BLOG_TARGET = os.environ.get("BLOG_TARGET", "ohopick").lower()

# configs/ 패키지를 찾기 위해 레포 루트(core의 부모)를 sys.path에 추가
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

try:
    _cfg = importlib.import_module(f"configs.config_{BLOG_TARGET}")
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        f"[config] configs/config_{BLOG_TARGET}.py 를 찾을 수 없습니다. "
        f"BLOG_TARGET='{BLOG_TARGET}' 값을 확인하세요."
    )

# 모든 공개 변수를 이 모듈 네임스페이스로 노출
for _k, _v in vars(_cfg).items():
    if not _k.startswith("_"):
        globals()[_k] = _v

# LANGUAGE 별칭 (일부 에이전트가 BLOG_LANGUAGE 대신 LANGUAGE 사용)
if "LANGUAGE" not in globals() and "BLOG_LANGUAGE" in globals():
    LANGUAGE = globals()["BLOG_LANGUAGE"]
