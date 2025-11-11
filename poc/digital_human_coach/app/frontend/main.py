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
    page_title="Digital Human App",
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
                        
                        feedback = result['feedback']
                        
                        # Overall Feedback at the top
                        st.info(f"**Overall Assessment:** {feedback['OverallFeedback']}")
                        
                        # Main metrics in columns
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Words/Minute", f"{result['speech_metrics']['words_per_minute']:.0f}")
                        with col2:
                            st.metric("Speaking Time", f"{result['speech_metrics']['speaking_time_seconds']:.1f}s")
                        with col3:
                            st.metric("Filler Words", result['speech_metrics']['filler_words_count'])
                        
                        # Detailed evaluation tabs
                        tab1, tab2, tab3 = st.tabs(["💬 Speech Evaluation", "🧍 Pose Evaluation", "� Detailed Metrics"])
                        
                        with tab1:
                            st.write("### Speech Evaluation")
                            
                            speech = feedback['Speech']
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Speed", f"{speech['Speed']['score']}/3", help="1=Slow, 2=Moderate, 3=Fast")
                                st.caption(speech['Speed']['comment'])
                                
                                st.metric("Naturalness", f"{speech['Naturalness']['score']}/3", help="1=Unnatural, 2=Somewhat natural, 3=Very natural")
                                st.caption(speech['Naturalness']['comment'])
                            
                            with col2:
                                st.metric("Continuity", f"{speech['Continuity']['score']}/3", help="1=Smooth, 2=Somewhat smooth, 3=Disjointed")
                                st.caption(speech['Continuity']['comment'])
                                
                                st.metric("Listening Effort", f"{speech['ListeningEffort']['score']}/5", help="1=Unclear, 5=Effortless")
                                st.caption(speech['ListeningEffort']['comment'])
                        
                        with tab2:
                            st.write("### Pose Evaluation")
                            
                            pose_eval = feedback['Pose']
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Eye Contact", f"{pose_eval['EyeContact']['score']}/3", help="1=Needs improvement, 2=Good, 3=Excellent")
                                st.caption(pose_eval['EyeContact']['comment'])
                            
                            with col2:
                                st.metric("Posture", f"{pose_eval['Posture']['score']}/3", help="1=Needs improvement, 2=Good, 3=Excellent")
                                st.caption(pose_eval['Posture']['comment'])
                            
                            with col3:
                                st.metric("Hand Gestures", f"{pose_eval['HandGestures']['score']}/3", help="0=None, 1=Needs improvement, 2=Good, 3=Excellent")
                                st.caption(pose_eval['HandGestures']['comment'])
                        
                        with tab3:
                            st.write("### Detailed Speech Metrics")
                            metrics = result['speech_metrics']
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Clarity Score", f"{metrics['clarity_score']:.1f}/10")
                                st.metric("Total Words", metrics['total_words'])
                                st.metric("Pauses", metrics['pause_count'])
                                st.metric("Volume Variation", f"{metrics['volume_variation']:.2f}")
                            with col2:
                                st.metric("Avg Pause Duration", f"{metrics['average_pause_duration']:.2f}s")
                                st.metric("Pitch Variation", f"{metrics['pitch_variation']:.2f}")
                                if metrics['filler_words']:
                                    st.metric("Common Fillers", ", ".join(metrics['filler_words'][:5]))
                            
                            st.write("### Body Language Metrics")
                            pose = result['pose_metrics']
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Posture Score", f"{pose['posture_score']:.1f}/10")
                                st.metric("Gestures", pose['gesture_count'])
                                st.metric("Movement Smoothness", f"{pose['movement_smoothness']:.1f}/10")
                            with col2:
                                st.metric("Eye Contact Score", f"{pose['eye_contact_score']:.1f}/10")
                                st.metric("Body Openness", f"{pose['body_openness_score']:.1f}/10")
                                st.metric("Tracking Quality", f"{pose['tracking_quality']*100:.0f}%")
                        
                        # Audio feedback
                        if feedback.get('audio_feedback_url'):
                            st.write("### 🔊 Audio Feedback")
                            st.audio(f"{API_BASE}{feedback['audio_feedback_url']}")
                        
                        # Transcript
                        with st.expander("📄 View Full Transcript"):
                            st.write(result['transcript'])
                        
                        # Download report
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("📥 Download Report (JSON)"):
                                import json
                                st.download_button(
                                    label="Download JSON",
                                    data=json.dumps(result, indent=2),
                                    file_name=f"evaluation_report_{session_id}.json",
                                    mime="application/json"
                                )
                        
                        with col2:
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
**Digital Human App v0.1.0**

🔧 Powered by:
- STT: Whisper/Deepgram
- LLM: GPT-4/Claude/Gemini
- TTS: ElevenLabs/Edge TTS
- Pose: MediaPipe
""")
