"""
Example: Test the conversation API programmatically
"""
import asyncio
import os

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

API_BASE = "http://localhost:8000"


def test_conversation():
    """Test conversation mode"""
    print("🚀 Testing Conversation Mode")
    print("=" * 50)
    
    # Start session
    response = requests.post(f"{API_BASE}/api/conversation/start", json={"type": "conversation"})
    session_id = response.json()["id"]
    print(f"✅ Session created: {session_id}")
    
    # Send messages
    messages = [
        "Hello! I want to practice my pitch.",
        "I'm building an AI-powered education platform.",
        "What feedback do you have for me?"
    ]
    
    for msg in messages:
        print(f"\n👤 You: {msg}")
        
        response = requests.post(
            f"{API_BASE}/api/conversation/{session_id}/speak",
            data={"text": msg}
        )
        
        if response.status_code == 200:
            result = response.json()
            assistant_msg = result["message"]["content"]
            print(f"🤖 Coach: {assistant_msg}")
            print(f"⏱️  Response time: {result['processing_time']:.2f}s")
        else:
            print(f"❌ Error: {response.text}")
    
    # Get history
    response = requests.get(f"{API_BASE}/api/conversation/{session_id}/history")
    history = response.json()
    print(f"\n📊 Total messages: {history['total_messages']}")
    
    # Cleanup
    requests.delete(f"{API_BASE}/api/conversation/{session_id}")
    print("\n✅ Session ended")


def test_health():
    """Test API health"""
    print("\n🏥 Testing API Health")
    print("=" * 50)
    
    response = requests.get(f"{API_BASE}/health")
    if response.status_code == 200:
        print("✅ API is healthy")
        print(response.json())
    else:
        print("❌ API is not responding")


if __name__ == "__main__":
    print("Digital Human Coach - API Test\n")
    
    try:
        test_health()
        print()
        test_conversation()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the backend is running:")
        print("   python -m app.backend.main")
    except Exception as e:
        print(f"❌ Error: {e}")
