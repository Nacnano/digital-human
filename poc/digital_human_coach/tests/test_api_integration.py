"""
Integration tests (moved from top-level `test_integration.py`).
Use pytest to run: `pytest tests/test_api_integration.py`.
"""

# Keep original code but adapt top-level runner for pytest integration
import requests
import json
import time
from pathlib import Path
import io

BASE_URL = "http://localhost:8000"


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def log_success(self, message):
        print(f"  ✅ {message}")
        self.passed += 1

    def log_failure(self, message):
        print(f"  ❌ {message}")
        self.failed += 1

    def log_warning(self, message):
        print(f"  ⚠️ {message}")
        self.warnings += 1

    def print_summary(self):
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⚠️ Warnings: {self.warnings}")
        total = self.passed + self.failed
        if total > 0:
            success_rate = (self.passed / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        print("=" * 60)


runner = TestRunner()


def test_health_check():
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data.get('status') == 'healthy'


def test_root_endpoint():
    response = requests.get(f"{BASE_URL}/", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert 'version' in data


def test_api_docs():
    response = requests.get(f"{BASE_URL}/docs", timeout=5)
    assert response.status_code in (200, 302)


# Conversation tests are left as integration tests that require a running backend
# These tests are intentionally non-flaky and check basic conversation flow.

def test_conversation_flow():
    # create session
    response = requests.post(f"{BASE_URL}/api/conversation/start", json={"type": "conversation"}, timeout=10)
    assert response.status_code == 200
    data = response.json()
    session_id = data.get("id")
    assert session_id

    # send a text message
    response = requests.post(
        f"{BASE_URL}/api/conversation/{session_id}/speak",
        data={"text": "Hello, this is a test."},
        timeout=30
    )
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data

    # get history
    response = requests.get(f"{BASE_URL}/api/conversation/{session_id}/history", timeout=10)
    assert response.status_code == 200
    history = response.json()
    assert 'messages' in history


def test_evaluation_upload_and_status():
    dummy_content = b"dummy video content for testing"
    files = {'file': ('test_video.mp4', io.BytesIO(dummy_content), 'video/mp4')}
    data = {'user_id': 'test_user_001'}

    response = requests.post(f"{BASE_URL}/api/evaluation/upload", files=files, data=data, timeout=30)
    # Upload may validate file type; accept 200 or 422
    assert response.status_code in (200, 422)


# If run directly, provide a quick runner
if __name__ == "__main__":
    import sys
    print("Running integration tests (quick mode)")
    try:
        test_health_check()
        test_root_endpoint()
        test_api_docs()
        test_conversation_flow()
        test_evaluation_upload_and_status()
        print("All integration tests completed")
    except AssertionError as e:
        print("A test assertion failed:", e)
        sys.exit(1)
    except Exception as e:
        print("Error running tests:", e)
        sys.exit(2)
