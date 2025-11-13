"""
verify_setup.py - moved from `quick_test.py`
Run this before running tests to ensure environment is ready.
"""
import importlib.util
from pathlib import Path

REQUIRED_PACKAGES = [
    'fastapi', 'uvicorn', 'requests', 'loguru', 'streamlit', 'pydantic'
]

REQUIRED_FILES = [
    "app/backend/main.py",
    "app/backend/api/conversation.py",
    "app/backend/api/evaluation.py",
    "app/backend/models/schemas.py",
    "app/backend/services/stt_service.py",
    "app/backend/services/llm_service.py",
    "app/backend/services/tts_service.py",
    "app/backend/services/pose_service.py",
    "app/backend/services/metrics_service.py",
    "app/utils/storage.py",
    "app/frontend/main.py"
]


def check_dependencies():
    print("Checking Python package availability...")
    missing = []
    for pkg in REQUIRED_PACKAGES:
        spec = importlib.util.find_spec(pkg)
        if spec is None:
            missing.append(pkg)
            print(f"  MISSING: {pkg}")
        else:
            print(f"  OK: {pkg}")
    return missing


def check_files():
    print("Checking required project files...")
    missing = []
    for p in REQUIRED_FILES:
        if not Path(p).exists():
            missing.append(p)
            print(f"  MISSING: {p}")
        else:
            print(f"  OK: {p}")
    return missing


def check_backend_running():
    try:
        import requests
        r = requests.get("http://localhost:8000/health", timeout=2)
        if r.status_code == 200:
            print("Backend is running and healthy")
            return True
    except Exception:
        print("Backend is not reachable at http://localhost:8000")
    return False


if __name__ == "__main__":
    print("VERIFY SETUP")
    print("==========")
    miss_pkgs = check_dependencies()
    miss_files = check_files()
    backend_ok = check_backend_running()

    if miss_pkgs or miss_files:
        print("\nPlease install missing packages and/or restore missing files before running tests.")
    else:
        print("\nEnvironment looks good.")

    if not backend_ok:
        print("Start the backend: python -m app.backend.main or use docker-compose up")
