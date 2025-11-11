"""
Developer example: conversation usage (moved from `examples/test_api.py`).
"""
import requests

API_BASE = "http://localhost:8000"


def run_conversation_example():
    response = requests.post(f"{API_BASE}/api/conversation/start", json={"type": "conversation"})
    response.raise_for_status()
    session_id = response.json().get('id')
    print(f"Session created: {session_id}")

    messages = [
        "Hello! I want to practice my pitch.",
        "I'm building an AI-powered education platform.",
        "What feedback do you have for me?"
    ]

    for msg in messages:
        resp = requests.post(f"{API_BASE}/api/conversation/{session_id}/speak", data={"text": msg})
        if resp.status_code == 200:
            print("Assistant:", resp.json().get('message', {}).get('content'))
        else:
            print("Error sending message:", resp.text)

    # Get history
    resp = requests.get(f"{API_BASE}/api/conversation/{session_id}/history")
    if resp.status_code == 200:
        print('Total messages:', resp.json().get('total_messages'))

    # End session
    requests.delete(f"{API_BASE}/api/conversation/{session_id}")


if __name__ == '__main__':
    try:
        run_conversation_example()
    except requests.exceptions.ConnectionError:
        print('Cannot connect to API. Ensure backend is running.')
