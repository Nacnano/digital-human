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

def get_session_animation_url(session_id: str) -> str:
    """Get last animation URL from session metadata"""
    try:
        response = requests.get(f"{API_BASE}/api/conversation/{session_id}/history")
        if response.status_code == 200:
            # Try to get metadata with animation URL
            # This would require adding an endpoint or modifying the history endpoint
            # For now, return None
            pass
    except:
        pass
    return None

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

# Audio2Face settings (global for conversation mode)
if mode == "🗣️ Conversation":
    st.sidebar.subheader("Display Options")
    show_animation = st.sidebar.checkbox(
        "Show Animated Face",
        value=False,
        help="Display AI's facial animation (requires Audio2Face enabled on backend)"
    )

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
    
    # Input method selector
    st.sidebar.subheader("Input Method")
    input_method = st.sidebar.radio(
        "Choose input method:",
        ["💬 Text", "🎤 Upload Audio", "🔴 Live Recording", "🔄 Continuous Talking"],
        help="Select how you want to communicate with the AI coach"
    )
    
    # Display conversation history
    st.subheader("Conversation")
    
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
            # Display audio if available
            if msg.get("audio_url"):
                st.audio(f"{API_BASE}{msg['audio_url']}")
            
            # Display animated face if available and enabled
            if show_animation and msg.get("animation_url") and msg["role"] == "assistant":
                st.video(f"{API_BASE}{msg['animation_url']}")
                st.caption("🎭 Animated Face")
    
    # Input based on selected method
    session_id = st.session_state.conv_session_id
    
    if input_method == "💬 Text":
        # Text input
        user_input = st.chat_input("Type your message...")
        
        if user_input:
            # Display user message
            with st.chat_message("user"):
                st.write(user_input)
            
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Send to API
            try:
                with st.spinner("AI is thinking..."):
                    response = requests.post(
                        f"{API_BASE}/api/conversation/{session_id}/speak",
                        data={"text": user_input}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        assistant_msg = result["message"]["content"]
                        audio_url = result.get("audio_url")
                        animation_url = result.get("animation_url")
                        
                        # Display assistant response
                        with st.chat_message("assistant"):
                            st.write(assistant_msg)
                            if audio_url:
                                st.audio(f"{API_BASE}{audio_url}")
                            if show_animation and animation_url:
                                st.video(f"{API_BASE}{animation_url}")
                                st.caption("🎭 Animated Face")
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": assistant_msg,
                            "audio_url": audio_url,
                            "animation_url": animation_url
                        })
                        
                        st.rerun()
                    else:
                        st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")
    
    elif input_method == "🎤 Upload Audio":
        # Audio file upload
        audio_file = st.file_uploader(
            "Upload an audio file",
            type=["wav", "mp3", "m4a", "ogg", "webm"],
            help="Upload a pre-recorded audio file"
        )
        
        if audio_file:
            st.audio(audio_file)
            
            if st.button("📤 Send Audio", type="primary"):
                # Display user message
                with st.chat_message("user"):
                    st.write("[Audio message]")
                    st.audio(audio_file)
                
                st.session_state.messages.append({"role": "user", "content": "[Audio message]"})
                
                # Send to API
                try:
                    with st.spinner("Processing audio and generating response..."):
                        # Reset file pointer
                        audio_file.seek(0)
                        files = {"audio": audio_file}
                        
                        response = requests.post(
                            f"{API_BASE}/api/conversation/{session_id}/speak",
                            files=files
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            assistant_msg = result["message"]["content"]
                            audio_url = result.get("audio_url")
                            animation_url = result.get("animation_url")
                            
                            # Display assistant response
                            with st.chat_message("assistant"):
                                st.write(assistant_msg)
                                if audio_url:
                                    st.audio(f"{API_BASE}{audio_url}")
                                if show_animation and animation_url:
                                    st.video(f"{API_BASE}{animation_url}")
                                    st.caption("🎭 Animated Face")
                            
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": assistant_msg,
                                "audio_url": audio_url,
                                "animation_url": animation_url
                            })
                            
                            st.rerun()
                        else:
                            st.error(f"API Error: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    elif input_method == "🔴 Live Recording":
        st.info("🎙️ **Live Audio Recording**")
        st.write("Click the button below to record your voice in real-time.")
        
        # Use streamlit-audio-recorder or st.audio_input if available
        try:
            # Try using st.audio_input (available in Streamlit 1.28+)
            audio_value = st.audio_input("Record your message")
            
            if audio_value:
                st.audio(audio_value)
                
                if st.button("📤 Send Recording", type="primary"):
                    # Display user message
                    with st.chat_message("user"):
                        st.write("[Voice message]")
                        st.audio(audio_value)
                    
                    st.session_state.messages.append({"role": "user", "content": "[Voice message]"})
                    
                    # Send to API
                    try:
                        with st.spinner("Processing audio and generating response..."):
                            files = {"audio": ("recording.wav", audio_value, "audio/wav")}
                            
                            response = requests.post(
                                f"{API_BASE}/api/conversation/{session_id}/speak",
                                files=files
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                assistant_msg = result["message"]["content"]
                                audio_url = result.get("audio_url")
                                animation_url = result.get("animation_url")
                                
                                # Display assistant response
                                with st.chat_message("assistant"):
                                    st.write(assistant_msg)
                                    if audio_url:
                                        st.audio(f"{API_BASE}{audio_url}")
                                    if show_animation and animation_url:
                                        st.video(f"{API_BASE}{animation_url}")
                                        st.caption("🎭 Animated Face")
                                
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": assistant_msg,
                                    "audio_url": audio_url,
                                    "animation_url": animation_url
                                })
                                
                                st.rerun()
                            else:
                                st.error(f"API Error: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        except AttributeError:
            # Fallback if st.audio_input is not available
            st.warning("⚠️ Live recording requires Streamlit 1.28 or higher.")
            st.info("""
            **To enable live recording:**
            1. Upgrade Streamlit: `pip install --upgrade streamlit`
            2. Or use the "Upload Audio" option to upload pre-recorded files
            
            **Alternative: Use external recording**
            - Record audio using your device's voice recorder
            - Save the file
            - Switch to "Upload Audio" mode and upload the file
            """)
            
            st.markdown("---")
            st.subheader("Quick Recording Tips")
            st.write("""
            - **Windows**: Use Voice Recorder app (Win + H for dictation)
            - **Mac**: Use QuickTime Player or Voice Memos
            - **Linux**: Use GNOME Sound Recorder or Audacity
            """)
    
    elif input_method == "🔄 Continuous Talking":
        # Continuous conversation mode - IMPROVED VERSION
        st.info("🔄 **Continuous Talking Mode**")
        st.write("""
        **Manual Continuous Conversation:**
        1. Start continuous mode below
        2. Click the record button to capture your speech
        3. Click again to stop when you finish speaking
        4. The system automatically processes and responds
        5. Repeat for natural conversation flow
        
        **Note:** This provides better control than auto-recording.
        """)
        
        # Settings for continuous mode
        with st.expander("⚙️ Settings"):
            auto_play_response = st.checkbox(
                "Auto-play AI responses",
                value=True,
                help="Automatically play AI voice responses"
            )
            
            show_transcription = st.checkbox(
                "Show transcriptions",
                value=True,
                help="Display text transcriptions of speech"
            )
        
        # Initialize continuous mode state
        if "continuous_mode_active" not in st.session_state:
            st.session_state.continuous_mode_active = False
        if "processing_audio" not in st.session_state:
            st.session_state.processing_audio = False
        
        # Control buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if not st.session_state.continuous_mode_active:
                if st.button("🎙️ Start Continuous Mode", type="primary", use_container_width=True):
                    st.session_state.continuous_mode_active = True
                    st.session_state.processing_audio = False
                    st.rerun()
        
        with col2:
            if st.session_state.continuous_mode_active:
                if st.button("⏹️ Stop Continuous Mode", type="secondary", use_container_width=True):
                    st.session_state.continuous_mode_active = False
                    st.session_state.processing_audio = False
                    st.rerun()
        
        # Continuous mode active
        if st.session_state.continuous_mode_active:
            st.success("✅ **Continuous Mode Active** - Click record to speak!")
            
            # Status indicator
            if st.session_state.processing_audio:
                st.warning("⏳ Processing your speech... Please wait before recording again.")
            
            # Check if we can use audio_input
            try:
                # Only show recording interface if not currently processing
                if not st.session_state.processing_audio:
                    st.markdown("**🎤 Record your message:**")
                    audio_value = st.audio_input("Click to start/stop recording", key=f"continuous_audio_{len(st.session_state.messages)}")
                    
                    if audio_value:
                        # Check audio duration to avoid processing very short clips
                        audio_bytes = audio_value.read()
                        audio_value.seek(0)  # Reset for later use
                        
                        # Rough duration estimate (WAV format: file_size / sample_rate / channels / bytes_per_sample)
                        # For typical WAV: 44100 Hz, stereo, 16-bit = ~176400 bytes/sec
                        estimated_duration = len(audio_bytes) / 176400.0
                        
                        if estimated_duration < 0.5:
                            st.warning(f"⚠️ Recording too short ({estimated_duration:.1f}s). Please speak longer.")
                        else:
                            # Set processing flag to prevent new recordings
                            st.session_state.processing_audio = True
                            
                            # Automatically process when audio is captured
                            with st.spinner("🎯 Processing your speech..."):
                                # Send to API
                                try:
                                    files = {"audio": ("recording.wav", audio_value, "audio/wav")}
                                    
                                    response = requests.post(
                                        f"{API_BASE}/api/conversation/{session_id}/speak",
                                        files=files,
                                        timeout=60  # Increased timeout for better reliability
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        assistant_msg = result["message"]["content"]
                                        audio_url = result.get("audio_url")
                                        animation_url = result.get("animation_url")
                                        
                                        # Get transcription from response if available
                                        user_transcription = result.get("user_transcription", "[Voice message]")
                                        
                                        # Display user message with transcription
                                        with st.chat_message("user"):
                                            if show_transcription:
                                                st.write(f"**You said:** {user_transcription}")
                                            else:
                                                st.write("🎤 [Voice message]")
                                        
                                        st.session_state.messages.append({
                                            "role": "user",
                                            "content": user_transcription
                                        })
                                        
                                        # Display and play assistant response
                                        with st.chat_message("assistant"):
                                            if show_transcription:
                                                st.write(assistant_msg)
                                            if audio_url and auto_play_response:
                                                # Auto-play the response
                                                st.audio(f"{API_BASE}{audio_url}", autoplay=True)
                                            elif audio_url:
                                                st.audio(f"{API_BASE}{audio_url}")
                                            if show_animation and animation_url:
                                                st.video(f"{API_BASE}{animation_url}")
                                                st.caption("🎭 Animated Face")
                                        
                                        st.session_state.messages.append({
                                            "role": "assistant",
                                            "content": assistant_msg,
                                            "audio_url": audio_url,
                                            "animation_url": animation_url
                                        })
                                        
                                        # Clear processing flag and rerun
                                        st.session_state.processing_audio = False
                                        st.rerun()
                                    else:
                                        st.error(f"API Error: {response.text}")
                                        st.session_state.processing_audio = False
                                        st.session_state.continuous_mode_active = False
                                
                                except Exception as e:
                                    st.error(f"Error: {e}")
                                    st.session_state.processing_audio = False
                                    st.session_state.continuous_mode_active = False
                else:
                    # Show placeholder while processing
                    st.info("⏳ Please wait for the AI to finish responding before recording again...")
            
            except AttributeError:
                # Fallback for older Streamlit versions
                st.error("❌ Continuous mode requires Streamlit 1.28 or higher.")
                st.info("""
                **To enable continuous mode:**
                ```bash
                pip install --upgrade streamlit>=1.28.0
                ```
                
                **Alternative:** Use "Live Recording" mode for manual record/send workflow.
                """)
                st.session_state.continuous_mode_active = False
        
        else:
            st.info("👆 Click 'Start Continuous Mode' above to begin")
            st.write("""
            **How it works:**
            1. Start continuous mode
            2. Click the record button and speak your message
            3. Click again to stop recording when you finish
            4. AI automatically processes and responds with voice
            5. Repeat for natural conversation flow
            
            **Benefits:**
            - Better speech detection than auto-recording
            - No interruptions while you're speaking
            - Natural conversation rhythm
            - Clear start/stop control
            """)
    
    # Clear conversation
    if st.sidebar.button("️ Clear Conversation", help="Start a new conversation"):
        if "conv_session_id" in st.session_state:
            try:
                requests.delete(f"{API_BASE}/api/conversation/{st.session_state.conv_session_id}")
            except:
                pass
            del st.session_state.conv_session_id
            st.session_state.messages = []
            if "continuous_mode_active" in st.session_state:
                st.session_state.continuous_mode_active = False
            if "processing_audio" in st.session_state:
                st.session_state.processing_audio = False
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
