"""
Simple WebSocket client example for testing continuous conversation

Requirements:
    pip install websockets asyncio

Usage:
    python examples/websocket_client_example.py
"""

import asyncio
import base64
import json
import wave
from pathlib import Path

import websockets


API_BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"


async def create_session():
    """Create a new conversation session"""
    import requests
    
    response = requests.post(f"{API_BASE}/api/conversation/start", json={
        "metadata": {}
    })
    
    if response.status_code == 200:
        session_data = response.json()
        return session_data["id"]
    else:
        raise Exception(f"Failed to create session: {response.text}")


async def stream_audio_file(websocket, audio_file_path: str, chunk_size: int = 4096):
    """
    Stream audio file to WebSocket in chunks
    
    Args:
        websocket: WebSocket connection
        audio_file_path: Path to WAV file (16kHz, 16-bit, mono)
        chunk_size: Size of each chunk to send
    """
    print(f"Streaming audio from: {audio_file_path}")
    
    with wave.open(audio_file_path, 'rb') as wav_file:
        # Verify format
        assert wav_file.getnchannels() == 1, "Audio must be mono"
        assert wav_file.getsampwidth() == 2, "Audio must be 16-bit"
        assert wav_file.getframerate() == 16000, "Audio must be 16kHz"
        
        # Read and send in chunks
        while True:
            frames = wav_file.readframes(chunk_size // 2)  # chunk_size is in bytes
            if not frames:
                break
            
            # Encode as base64
            audio_base64 = base64.b64encode(frames).decode('utf-8')
            
            # Send to server
            await websocket.send(json.dumps({
                "audio_data": audio_base64,
                "sample_rate": 16000,
                "format": "pcm16"
            }))
            
            # Simulate real-time streaming (optional)
            await asyncio.sleep(chunk_size / (16000 * 2))  # Sleep for chunk duration
    
    print("Audio streaming complete")


async def receive_messages(websocket):
    """
    Receive and handle messages from server
    """
    try:
        while True:
            message_str = await websocket.recv()
            message = json.loads(message_str)
            
            event = message.get("event")
            data = message.get("data", {})
            
            if event == "speech_start":
                print("🎤 User started speaking")
            
            elif event == "speech_end":
                print("🎤 User stopped speaking")
            
            elif event == "transcription_partial":
                print(f"📝 Partial: {data.get('text')}")
            
            elif event == "transcription_final":
                print(f"📝 Transcription: {data.get('text')}")
            
            elif event == "response_start":
                print("🤖 Assistant is responding...")
            
            elif event == "response_text":
                text = data.get('text', '')
                is_final = data.get('is_final', False)
                if is_final:
                    print(f"🤖 Assistant: {text}")
                else:
                    print(text, end='', flush=True)
            
            elif event == "response_audio":
                print("🔊 Received audio response")
                # Optionally save audio
                audio_base64 = data.get('audio_data')
                if audio_base64:
                    audio_bytes = base64.b64decode(audio_base64)
                    output_path = Path("temp") / f"response_{message['timestamp']}.mp3"
                    output_path.parent.mkdir(exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(audio_bytes)
                    print(f"   Saved to: {output_path}")
            
            elif event == "response_end":
                print("✅ Assistant finished")
            
            elif event == "error":
                error = data.get('error')
                detail = data.get('detail')
                print(f"❌ Error: {error}")
                if detail:
                    print(f"   Detail: {detail}")
            
            elif event == "status":
                status_msg = data.get('message')
                print(f"ℹ️  Status: {status_msg}")
            
            else:
                print(f"Unknown event: {event}")
    
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")


async def continuous_conversation_demo(audio_file: str = None):
    """
    Demo of continuous conversation with WebSocket streaming
    
    Args:
        audio_file: Path to test audio file (optional)
    """
    print("=== Continuous Conversation Demo ===\n")
    
    # Create session
    print("Creating conversation session...")
    session_id = await create_session()
    print(f"Session ID: {session_id}\n")
    
    # Connect to WebSocket
    ws_url = f"{WS_BASE}/api/conversation/{session_id}/stream"
    print(f"Connecting to: {ws_url}")
    
    async with websockets.connect(ws_url) as websocket:
        print("Connected!\n")
        
        # Start receiving messages
        receive_task = asyncio.create_task(receive_messages(websocket))
        
        try:
            if audio_file:
                # Stream audio file
                await stream_audio_file(websocket, audio_file)
            else:
                # Interactive mode - wait for user input
                print("WebSocket connected. Send audio or type commands:")
                print("  Commands: 'reset', 'ping', 'quit'\n")
                
                while True:
                    command = input("> ")
                    
                    if command.lower() == "quit":
                        break
                    elif command.lower() == "reset":
                        await websocket.send(json.dumps({"action": "reset"}))
                    elif command.lower() == "ping":
                        await websocket.send(json.dumps({"action": "ping"}))
                    else:
                        print("Unknown command. Use: reset, ping, quit")
                        print("To stream audio, run with --audio <file.wav>")
        
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            receive_task.cancel()
            print("\nClosing connection...")


async def test_multiple_utterances():
    """
    Test with multiple audio files simulating a conversation
    """
    print("=== Testing Multiple Utterances ===\n")
    
    # List of test audio files (you'll need to create these)
    test_files = [
        "test_audio/hello.wav",
        "test_audio/how_are_you.wav",
        "test_audio/tell_me_about_yourself.wav",
    ]
    
    session_id = await create_session()
    print(f"Session ID: {session_id}\n")
    
    ws_url = f"{WS_BASE}/api/conversation/{session_id}/stream"
    
    async with websockets.connect(ws_url) as websocket:
        receive_task = asyncio.create_task(receive_messages(websocket))
        
        for audio_file in test_files:
            if not Path(audio_file).exists():
                print(f"Skipping {audio_file} (not found)")
                continue
            
            print(f"\n--- Sending: {audio_file} ---")
            await stream_audio_file(websocket, audio_file)
            
            # Wait a bit between utterances
            await asyncio.sleep(5)
        
        receive_task.cancel()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 2 and sys.argv[1] == "--audio":
        # Test with audio file
        audio_file = sys.argv[2]
        if not Path(audio_file).exists():
            print(f"Error: Audio file not found: {audio_file}")
            sys.exit(1)
        
        asyncio.run(continuous_conversation_demo(audio_file))
    
    elif len(sys.argv) > 1 and sys.argv[1] == "--multi":
        # Test with multiple utterances
        asyncio.run(test_multiple_utterances())
    
    else:
        # Interactive mode
        print("Usage:")
        print("  python examples/websocket_client_example.py --audio <file.wav>")
        print("  python examples/websocket_client_example.py --multi")
        print("  python examples/websocket_client_example.py  (interactive mode)")
        print()
        
        asyncio.run(continuous_conversation_demo())
