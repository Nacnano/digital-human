"""
Streamlit Frontend for Digital Human Communication Coach
"""
import os
import time
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment
load_dotenv()

# API Configuration
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(
    page_title="Digital Human Coach",
    page_icon="🎤",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎤 Digital Human Communication Coach</div>', unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Settings")
mode = st.sidebar.radio("Mode", ["🗣️ Conversation", "📊 Evaluation"])

if mode == "🗣️ Conversation":
    st.header("Real-Time Conversation Mode")
    st.write("Practice your communication skills with an AI coach")
    
    # Initialize session
    if "conv_session_id" not in st.session_state:
        try:
            response = requests.post(f"{API_BASE}/api/conversation/start", json={"type": "conversation"})
            if response.status_code == 200:
                st.session_state.conv_session_id = response.json()["id"]
                st.session_state.messages = []
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")
            st.stop()
    
    # Display conversation history
    st.subheader("Conversation")
    
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("audio_url"):
                st.audio(f"{API_BASE}{msg['audio_url']}")
    
    # Input methods
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.chat_input("Type your message or upload audio...")
    
    with col2:
        audio_file = st.file_uploader("🎤 Upload Audio", type=["wav", "mp3", "m4a"], label_visibility="collapsed")
    
    # Process input
    if user_input or audio_file:
        session_id = st.session_state.conv_session_id
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input if user_input else "[Audio input]")
        
        st.session_state.messages.append({"role": "user", "content": user_input or "[Audio]"})
        
        # Send to API
        try:
            with st.spinner("Thinking..."):
                if audio_file:
                    files = {"audio": audio_file}
                    data = {}
                else:
                    files = None
                    data = {"text": user_input}
                
                response = requests.post(
                    f"{API_BASE}/api/conversation/{session_id}/speak",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assistant_msg = result["message"]["content"]
                    audio_url = result.get("audio_url")
                    
                    # Display assistant response
                    with st.chat_message("assistant"):
                        st.write(assistant_msg)
                        if audio_url:
                            st.audio(f"{API_BASE}{audio_url}")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_msg,
                        "audio_url": audio_url
                    })
                    
                    st.rerun()
                else:
                    st.error(f"API Error: {response.text}")
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Clear conversation
    if st.sidebar.button("🗑️ Clear Conversation"):
        if "conv_session_id" in st.session_state:
            requests.delete(f"{API_BASE}/api/conversation/{st.session_state.conv_session_id}")
            del st.session_state.conv_session_id
            st.session_state.messages = []
        st.rerun()

else:  # Evaluation Mode
    st.header("Video Evaluation Mode")
    st.write("Upload a video of yourself speaking to receive detailed feedback")
    
    # File upload
    video_file = st.file_uploader("📹 Upload Video", type=["mp4", "avi", "mov", "mkv"])
    
    if video_file:
        # Show video preview
        st.video(video_file)
        
        if st.button("🔍 Analyze Video", type="primary"):
            # Upload video
            with st.spinner("Uploading video..."):
                try:
                    files = {"file": video_file}
                    response = requests.post(f"{API_BASE}/api/evaluation/upload", files=files)
                    
                    if response.status_code == 200:
                        upload_result = response.json()
                        session_id = upload_result["session_id"]
                        st.session_state.eval_session_id = session_id
                        
                        st.success(f"✅ Video uploaded! Session ID: {session_id}")
                        
                        # Start analysis
                        response = requests.post(f"{API_BASE}/api/evaluation/{session_id}/analyze")
                        
                        if response.status_code == 200:
                            st.info("🔄 Analysis started...")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error(f"Upload failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Show progress if analyzing
    if "eval_session_id" in st.session_state:
        session_id = st.session_state.eval_session_id
        
        # Poll status
        try:
            response = requests.get(f"{API_BASE}/api/evaluation/{session_id}/status")
            if response.status_code == 200:
                status = response.json()
                
                if status["status"] == "processing":
                    st.progress(status["progress"] / 100)
                    st.info(f"⏳ {status['message']}")
                    time.sleep(2)
                    st.rerun()
                
                elif status["status"] == "completed":
                    st.success("✅ Analysis complete!")
                    
                    # Fetch results
                    response = requests.get(f"{API_BASE}/api/evaluation/{session_id}/report")
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display results
                        st.subheader("📊 Evaluation Results")
                        
                        # Overall score
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Overall Score", f"{result['feedback']['overall_score']}/10")
                        with col2:
                            st.metric("Words/Minute", f"{result['speech_metrics']['words_per_minute']}")
                        with col3:
                            st.metric("Filler Words", result['speech_metrics']['filler_words_count'])
                        
                        # Detailed metrics
                        tab1, tab2, tab3 = st.tabs(["💬 Speech", "🧍 Body Language", "💡 Feedback"])
                        
                        with tab1:
                            st.write("### Speech Metrics")
                            metrics = result['speech_metrics']
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Clarity Score", f"{metrics['clarity_score']}/10")
                                st.metric("Total Words", metrics['total_words'])
                                st.metric("Speaking Time", f"{metrics['speaking_time_seconds']}s")
                            with col2:
                                st.metric("Pauses", metrics['pause_count'])
                                st.metric("Avg Pause", f"{metrics['average_pause_duration']}s")
                                st.metric("Filler Words", ", ".join(metrics['filler_words'][:5]))
                        
                        with tab2:
                            st.write("### Body Language Metrics")
                            pose = result['pose_metrics']
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Posture Score", f"{pose['posture_score']}/10")
                                st.metric("Gestures", pose['gesture_count'])
                                st.metric("Movement Smoothness", f"{pose['movement_smoothness']}/10")
                            with col2:
                                st.metric("Eye Contact", f"{pose['eye_contact_score']}/10")
                                st.metric("Body Openness", f"{pose['body_openness_score']}/10")
                                st.metric("Tracking Quality", f"{pose['tracking_quality']*100:.0f}%")
                        
                        with tab3:
                            st.write("### AI Feedback")
                            feedback = result['feedback']
                            
                            st.write("#### ✅ Strengths")
                            for strength in feedback['strengths']:
                                st.write(f"- {strength}")
                            
                            st.write("#### 📈 Areas for Improvement")
                            for area in feedback['areas_for_improvement']:
                                st.write(f"- {area}")
                            
                            st.write("#### 💡 Recommendations")
                            for rec in feedback['specific_recommendations']:
                                st.write(f"- {rec}")
                            
                            st.write("#### 📝 Detailed Feedback")
                            st.write(feedback['detailed_feedback'])
                            
                            # Audio feedback
                            if feedback.get('audio_feedback_url'):
                                st.write("#### 🔊 Listen to Feedback")
                                st.audio(f"{API_BASE}{feedback['audio_feedback_url']}")
                        
                        # Transcript
                        with st.expander("📄 View Transcript"):
                            st.write(result['transcript'])
                        
                        # Download report
                        if st.button("📥 Download Report (JSON)"):
                            st.download_button(
                                label="Download",
                                data=response.text,
                                file_name=f"report_{session_id}.json",
                                mime="application/json"
                            )
                    
                    # Clear session
                    if st.button("🔄 Analyze Another Video"):
                        del st.session_state.eval_session_id
                        st.rerun()
                
                elif status["status"] == "failed":
                    st.error(f"❌ {status['message']}")
                    if st.button("🔄 Try Again"):
                        del st.session_state.eval_session_id
                        st.rerun()
        
        except Exception as e:
            st.error(f"Error fetching status: {e}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**Digital Human Coach v0.1.0**

🔧 Powered by:
- STT: Whisper/Deepgram
- LLM: GPT-4/Claude/Gemini
- TTS: ElevenLabs/Edge TTS
- Pose: MediaPipe
""")
