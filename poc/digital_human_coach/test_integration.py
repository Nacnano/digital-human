"""
Integration tests for Digital Human Coach API
Tests both conversation and evaluation endpoints
"""
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

def test_health_check():
    """Test health check endpoint"""
    print("\n=== Test 1: Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            runner.log_success("Health check endpoint responded")
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)}")
            if data.get('status') == 'healthy':
                runner.log_success("System status is healthy")
            else:
                runner.log_warning(f"System status: {data.get('status')}")
        else:
            runner.log_failure(f"Health check failed with status {response.status_code}")
    except Exception as e:
        runner.log_failure(f"Health check error: {str(e)}")

def test_root_endpoint():
    """Test root endpoint"""
    print("\n=== Test 2: Root Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            runner.log_success("Root endpoint responded")
            data = response.json()
            print(f"  Version: {data.get('version')}")
            print(f"  Status: {data.get('status')}")
        else:
            runner.log_failure(f"Root endpoint failed with status {response.status_code}")
    except Exception as e:
        runner.log_failure(f"Root endpoint error: {str(e)}")

def test_api_docs():
    """Test API documentation"""
    print("\n=== Test 3: API Documentation ===")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            runner.log_success("API docs are accessible at /docs")
        else:
            runner.log_warning("API docs endpoint returned non-200 status")
    except Exception as e:
        runner.log_warning(f"API docs check: {str(e)}")

def test_conversation_session():
    """Test conversation session creation"""
    print("\n=== Test 4: Conversation Session ===")
    try:
        response = requests.post(
            f"{BASE_URL}/api/conversation/session",
            json={"user_id": "test_user_001"},
            timeout=10
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            runner.log_success("Session created successfully")
            data = response.json()
            session_id = data.get("session_id")
            print(f"  Session ID: {session_id}")
            return session_id
        else:
            runner.log_failure(f"Session creation failed: {response.text[:200]}")
            return None
    except Exception as e:
        runner.log_failure(f"Session creation error: {str(e)}")
        return None

def test_send_message(session_id):
    """Test sending a message in conversation"""
    print("\n=== Test 5: Send Message ===")
    if not session_id:
        runner.log_warning("Skipping - no session ID available")
        return
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/conversation/send-audio",
            json={
                "session_id": session_id,
                "text": "Hello! I want to improve my communication skills."
            },
            timeout=30
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            runner.log_success("Message sent successfully")
            data = response.json()
            print(f"  AI Response: {data.get('text', '')[:100]}...")
            if data.get('audio_url'):
                runner.log_success("Audio response generated")
        else:
            runner.log_failure(f"Message send failed: {response.text[:200]}")
    except Exception as e:
        runner.log_failure(f"Message send error: {str(e)}")

def test_conversation_history(session_id):
    """Test retrieving conversation history"""
    print("\n=== Test 6: Conversation History ===")
    if not session_id:
        runner.log_warning("Skipping - no session ID available")
        return
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/conversation/history/{session_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            runner.log_success("History retrieved successfully")
            data = response.json()
            print(f"  Messages: {len(data.get('messages', []))}")
        else:
            runner.log_failure(f"History retrieval failed: {response.text[:200]}")
    except Exception as e:
        runner.log_failure(f"History retrieval error: {str(e)}")

def test_video_upload():
    """Test video upload for evaluation"""
    print("\n=== Test 7: Video Upload ===")
    
    # Create a dummy video file
    dummy_content = b"dummy video content for testing"
    
    try:
        files = {
            'file': ('test_video.mp4', io.BytesIO(dummy_content), 'video/mp4')
        }
        data = {'user_id': 'test_user_001'}
        
        response = requests.post(
            f"{BASE_URL}/api/evaluation/upload-video",
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            runner.log_success("Video upload initiated")
            result = response.json()
            session_id = result.get("session_id")
            print(f"  Evaluation Session ID: {session_id}")
            return session_id
        elif response.status_code == 422:
            runner.log_warning("Upload endpoint exists but validation failed (expected for dummy file)")
            print(f"  Response: {response.text[:200]}")
            return None
        else:
            runner.log_failure(f"Video upload failed: {response.text[:200]}")
            return None
    except Exception as e:
        runner.log_failure(f"Video upload error: {str(e)}")
        return None

def test_evaluation_status(session_id):
    """Test evaluation status check"""
    print("\n=== Test 8: Evaluation Status ===")
    if not session_id:
        runner.log_warning("Skipping - no evaluation session ID available")
        return
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/evaluation/status/{session_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            runner.log_success("Status check successful")
            data = response.json()
            print(f"  Status: {data.get('status')}")
        else:
            runner.log_warning(f"Status check returned {response.status_code}")
    except Exception as e:
        runner.log_failure(f"Status check error: {str(e)}")

def test_evaluation_results(session_id):
    """Test getting evaluation results"""
    print("\n=== Test 9: Evaluation Results ===")
    if not session_id:
        runner.log_warning("Skipping - no evaluation session ID available")
        return
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/evaluation/results/{session_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            runner.log_success("Results retrieved successfully")
            data = response.json()
            if 'speech_metrics' in data:
                runner.log_success("Speech metrics present")
            if 'pose_metrics' in data:
                runner.log_success("Pose metrics present")
        else:
            runner.log_warning(f"Results retrieval returned {response.status_code}")
    except Exception as e:
        runner.log_failure(f"Results retrieval error: {str(e)}")

def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("DIGITAL HUMAN COACH - INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        # Basic connectivity tests
        test_health_check()
        test_root_endpoint()
        test_api_docs()
        
        # Conversation mode tests
        session_id = test_conversation_session()
        test_send_message(session_id)
        test_conversation_history(session_id)
        
        # Evaluation mode tests
        eval_session_id = test_video_upload()
        test_evaluation_status(eval_session_id)
        test_evaluation_results(eval_session_id)
        
        # Print summary
        runner.print_summary()
        
        if runner.failed == 0:
            print("\n🎉 All critical tests passed!")
        elif runner.passed > runner.failed:
            print("\n✅ Most tests passed - some features may need attention")
        else:
            print("\n⚠️ Multiple tests failed - check backend implementation")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server!")
        print("Please ensure the backend is running on http://localhost:8000")
        print("Start it with: python -m app.backend.main")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    runner = TestRunner()
    run_all_tests()
