"""
Conversation API endpoints
"""
import asyncio
import base64
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from loguru import logger

from app.backend.models.schemas import (
    ConversationHistory,
    ConversationMessage,
    ConversationResponse,
    MessageRole,
    SessionCreate,
    SessionResponse,
    SessionType,
    StreamEventType,
    StreamMessage,
    AudioChunkMessage,
    TranscriptionMessage,
    ResponseTextMessage,
    ResponseAudioMessage,
    StreamError,
)
from app.backend.services.llm_service import CONVERSATION_SYSTEM_PROMPT, create_llm_service
from app.backend.services.stt_service import create_stt_service
from app.backend.services.tts_service import create_tts_service
from app.backend.services.vad_service import create_vad_service, VADSegmenter
from app.utils.storage import StorageService

router = APIRouter()
storage = StorageService()

# Service instances - lazy initialized
_stt_service = None
_llm_service = None
_tts_service = None

def get_services():
    """Lazy initialization of services"""
    global _stt_service, _llm_service, _tts_service
    
    if _stt_service is None or _llm_service is None or _tts_service is None:
        stt_provider = os.getenv("STT_PROVIDER", "whisper")
        llm_provider = os.getenv("LLM_PROVIDER", "openai")
        tts_provider = os.getenv("TTS_PROVIDER", "edge")
        
        try:
            _stt_service = create_stt_service(
                provider=stt_provider,
                api_key=os.getenv(f"{stt_provider.upper()}_API_KEY")
            )
            
            # Get the appropriate API key for LLM provider
            if llm_provider in ["google", "gemini"]:
                llm_api_key = os.getenv("GOOGLE_API_KEY")
            elif llm_provider == "typhoon":
                llm_api_key = os.getenv("TYPHOON_API_KEY")
            elif llm_provider == "nvidia":
                llm_api_key = os.getenv("NVIDIA_API_KEY")
            else:
                llm_api_key = os.getenv(f"{llm_provider.upper()}_API_KEY")
            
            _llm_service = create_llm_service(
                provider=llm_provider,
                api_key=llm_api_key,
                model=os.getenv("LLM_MODEL")
            )
            _tts_service = create_tts_service(
                provider=tts_provider,
                api_key=os.getenv(f"{tts_provider.upper()}_API_KEY")
            )
            logger.info(f"Services initialized: STT={stt_provider}, LLM={llm_provider}, TTS={tts_provider}")
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            raise
    
    return _stt_service, _llm_service, _tts_service


@router.post("/start", response_model=SessionResponse)
async def start_conversation(session: SessionCreate):
    """Start a new conversation session"""
    session_id = storage.create_session("conversation", session.metadata)
    
    return SessionResponse(
        id=session_id,
        type=SessionType.CONVERSATION,
        status="active",
        created_at=datetime.now()
    )


@router.post("/{session_id}/speak", response_model=ConversationResponse)
async def speak(
    session_id: str,
    audio: UploadFile = File(None),
    text: str = Form(None)
):
    """Process user speech or text input"""
    if not audio and not text:
        raise HTTPException(status_code=400, detail="Either audio or text must be provided")
    
    # Get services
    stt_service, llm_service, tts_service = get_services()
    
    start_time = datetime.now()
    
    # Get or create conversation history
    metadata = storage.get_metadata(session_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Session not found")
    
    conversation_history = metadata.get("conversation", [])
    
    # Transcribe audio if provided
    if audio:
        audio_data = await audio.read()
        audio_path = storage.save_file(session_id, audio_data, f"input_{len(conversation_history)}.wav", "audio")
        
        try:
            transcript = await stt_service.transcribe(audio_path)
            text = transcript
        except Exception as e:
            logger.error(f"STT error: {e}")
            raise HTTPException(status_code=500, detail=f"Speech transcription failed: {str(e)}")
    
    # Add user message to history
    user_message = {
        "role": "user",
        "content": text,
        "timestamp": datetime.now().isoformat()
    }
    conversation_history.append(user_message)
    
    # Generate LLM response
    try:
        response_text = await llm_service.generate_conversation(
            messages=[{"role": msg["role"], "content": msg["content"]} for msg in conversation_history],
            system_prompt=CONVERSATION_SYSTEM_PROMPT
        )
    except Exception as e:
        logger.error(f"LLM error: {e}")
        raise HTTPException(status_code=500, detail=f"AI response generation failed: {str(e)}")
    
    # Add assistant message to history
    assistant_message = {
        "role": "assistant",
        "content": response_text,
        "timestamp": datetime.now().isoformat()
    }
    conversation_history.append(assistant_message)
    
    # Generate TTS audio
    audio_url = None
    audio_file_path = None
    try:
        audio_filename = f"response_{len(conversation_history)}.mp3"
        audio_file_path = str(Path(storage.get_session_path(session_id)) / "audio" / audio_filename)
        await tts_service.generate_to_file(response_text, audio_file_path)
        audio_url = f"/temp/sessions/{session_id}/audio/{audio_filename}"
    except Exception as e:
        logger.warning(f"TTS error: {e}")
        # Continue without audio
    
    # Generate facial animation if enabled and audio was generated
    animation_url = None
    if os.getenv("ENABLE_AUDIO2FACE", "false").lower() == "true" and audio_file_path and os.path.exists(audio_file_path):
        try:
            from app.backend.api.audio2face import get_audio2face_service
            
            logger.info("Generating facial animation for response...")
            audio2face = get_audio2face_service()
            
            animation_result = await audio2face.generate_facial_animation(
                audio_path=audio_file_path
            )
            
            # Save animation video
            if animation_result.get("video_path"):
                source_video_path = animation_result["video_path"]
                
                # Check if the video file actually exists
                if os.path.exists(source_video_path):
                    video_filename = f"animation_{len(conversation_history)}.mp4"
                    video_dir = Path(storage.get_session_path(session_id)) / "video"
                    video_dir.mkdir(parents=True, exist_ok=True)
                    video_path = str(video_dir / video_filename)
                    
                    shutil.copy(source_video_path, video_path)
                    animation_url = f"/temp/sessions/{session_id}/video/{video_filename}"
                    logger.info(f"Generated facial animation: {animation_url}")
                    
                    # Clean up temporary file if it was created in temp dir
                    if source_video_path.startswith(tempfile.gettempdir()):
                        try:
                            os.remove(source_video_path)
                        except:
                            pass
                else:
                    logger.warning(f"Video file not found at: {source_video_path}")
        except Exception as e:
            logger.warning(f"Audio2Face error: {e}")
            # Continue without animation
    
    # Update session metadata
    storage.update_metadata(session_id, {"conversation": conversation_history})
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    response_data = ConversationResponse(
        message=ConversationMessage(
            role=MessageRole.ASSISTANT,
            content=response_text,
            timestamp=datetime.now()
        ),
        audio_url=audio_url,
        animation_url=animation_url,  # Include animation URL in response
        processing_time=processing_time,
        user_transcription=text  # Include user transcription for continuous mode
    )
    
    return response_data


@router.get("/{session_id}/history", response_model=ConversationHistory)
async def get_history(session_id: str):
    """Get conversation history"""
    metadata = storage.get_metadata(session_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Session not found")
    
    conversation = metadata.get("conversation", [])
    messages = [
        ConversationMessage(
            role=msg["role"],
            content=msg["content"],
            timestamp=datetime.fromisoformat(msg["timestamp"])
        )
        for msg in conversation
    ]
    
    return ConversationHistory(
        session_id=session_id,
        messages=messages,
        total_messages=len(messages)
    )


@router.delete("/{session_id}")
async def end_conversation(session_id: str):
    """End conversation and cleanup"""
    storage.delete_session(session_id)
    return {"message": "Conversation ended", "session_id": session_id}


# ============================================================================
# WebSocket Streaming Endpoint for Continuous Conversation
# ============================================================================

@router.websocket("/{session_id}/stream")
async def stream_conversation(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for continuous streaming conversation
    
    This enables real-time bidirectional communication:
    - Client sends audio chunks
    - Server detects speech using VAD
    - Server transcribes speech in real-time
    - LLM decides when to respond
    - Server streams back text and audio responses
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established for session: {session_id}")
    
    # Initialize services
    try:
        stt_service, llm_service, tts_service = get_services()
        
        # Initialize VAD
        vad_provider = os.getenv("VAD_PROVIDER", "silero")  # silero, webrtc, energy
        vad_service = create_vad_service(provider=vad_provider)
        vad_segmenter = VADSegmenter(
            vad_service=vad_service,
            sample_rate=16000,
            frame_duration_ms=30,
            padding_duration_ms=300,
            min_speech_duration_ms=250
        )
        
        # Get or create conversation history
        metadata = storage.get_metadata(session_id)
        if not metadata:
            logger.warning(f"Session {session_id} not found, creating new one")
            storage.create_session("conversation", {})
            metadata = storage.get_metadata(session_id)
        
        conversation_history = metadata.get("conversation", [])
        
        # State management
        current_transcription = ""
        is_processing_response = False
        audio_buffer = []
        
        async def send_event(event: StreamEventType, data: dict):
            """Send event to client"""
            message = StreamMessage(
                event=event,
                session_id=session_id,
                data=data
            )
            await websocket.send_json(message.model_dump(mode='json'))
        
        async def process_speech_segment(audio_segment: bytes):
            """Process complete speech segment"""
            nonlocal current_transcription, is_processing_response, conversation_history
            
            if is_processing_response:
                logger.debug("Already processing response, ignoring speech")
                return
            
            try:
                # Save audio temporarily
                temp_audio_path = storage.get_temp_path(f"stream_{session_id}_{datetime.now().timestamp()}.wav")
                
                # Write WAV file
                import wave
                with wave.open(temp_audio_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(16000)
                    wav_file.writeframes(audio_segment)
                
                # Transcribe
                logger.info("Transcribing speech segment...")
                transcript = await stt_service.transcribe(temp_audio_path)
                logger.info(f"Transcription: {transcript}")
                
                # Clean up temp file
                try:
                    os.remove(temp_audio_path)
                except:
                    pass
                
                if not transcript or len(transcript.strip()) < 3:
                    logger.debug("Transcription too short, ignoring")
                    return
                
                # Send final transcription
                await send_event(StreamEventType.TRANSCRIPTION_FINAL, {
                    "text": transcript,
                    "is_final": True
                })
                
                # Add to conversation history
                user_message = {
                    "role": "user",
                    "content": transcript,
                    "timestamp": datetime.now().isoformat()
                }
                conversation_history.append(user_message)
                
                # Determine if LLM should respond
                should_respond = await should_llm_respond(transcript, conversation_history)
                
                if should_respond:
                    is_processing_response = True
                    await send_event(StreamEventType.RESPONSE_START, {})
                    
                    # Generate LLM response
                    logger.info("Generating LLM response...")
                    try:
                        # Check if streaming is supported
                        if hasattr(llm_service, 'generate_conversation_stream'):
                            # Stream response
                            full_response = ""
                            async for text_chunk in llm_service.generate_conversation_stream(
                                messages=[{"role": msg["role"], "content": msg["content"]} for msg in conversation_history],
                                system_prompt=CONVERSATION_SYSTEM_PROMPT
                            ):
                                full_response += text_chunk
                                await send_event(StreamEventType.RESPONSE_TEXT, {
                                    "text": text_chunk,
                                    "is_final": False
                                })
                            
                            response_text = full_response
                        else:
                            # Non-streaming response
                            response_text = await llm_service.generate_conversation(
                                messages=[{"role": msg["role"], "content": msg["content"]} for msg in conversation_history],
                                system_prompt=CONVERSATION_SYSTEM_PROMPT
                            )
                            await send_event(StreamEventType.RESPONSE_TEXT, {
                                "text": response_text,
                                "is_final": True
                            })
                        
                        # Add assistant message to history
                        assistant_message = {
                            "role": "assistant",
                            "content": response_text,
                            "timestamp": datetime.now().isoformat()
                        }
                        conversation_history.append(assistant_message)
                        
                        # Generate TTS audio
                        logger.info("Generating TTS audio...")
                        audio_filename = f"stream_response_{len(conversation_history)}.mp3"
                        audio_file_path = str(Path(storage.get_session_path(session_id)) / "audio" / audio_filename)
                        await tts_service.generate_to_file(response_text, audio_file_path)
                        
                        # Read audio and send as base64
                        with open(audio_file_path, 'rb') as f:
                            audio_data = f.read()
                            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                        
                        await send_event(StreamEventType.RESPONSE_AUDIO, {
                            "audio_data": audio_base64,
                            "format": "mp3"
                        })
                        
                        await send_event(StreamEventType.RESPONSE_END, {})
                        
                        # Update session metadata
                        storage.update_metadata(session_id, {"conversation": conversation_history})
                        
                    except Exception as e:
                        logger.error(f"Error generating response: {e}")
                        await send_event(StreamEventType.ERROR, {
                            "error": "Response generation failed",
                            "detail": str(e),
                            "recoverable": True
                        })
                    finally:
                        is_processing_response = False
                
            except Exception as e:
                logger.error(f"Error processing speech segment: {e}")
                await send_event(StreamEventType.ERROR, {
                    "error": "Speech processing failed",
                    "detail": str(e),
                    "recoverable": True
                })
        
        # Main message loop
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                if "audio_data" in data:
                    # Audio chunk received
                    audio_base64 = data["audio_data"]
                    audio_bytes = base64.b64decode(audio_base64)
                    
                    # Process with VAD
                    is_speaking, speech_segment = vad_segmenter.process_frame(audio_bytes)
                    
                    if speech_segment is not None:
                        # Complete speech segment detected
                        logger.info("Complete speech segment detected")
                        await send_event(StreamEventType.SPEECH_END, {})
                        
                        # Process the speech segment
                        await process_speech_segment(speech_segment)
                    elif is_speaking:
                        # Still speaking
                        await send_event(StreamEventType.SPEECH_START, {})
                
                elif data.get("action") == "reset":
                    # Reset conversation
                    conversation_history = []
                    vad_segmenter.reset()
                    current_transcription = ""
                    is_processing_response = False
                    storage.update_metadata(session_id, {"conversation": []})
                    await send_event(StreamEventType.STATUS, {"message": "Conversation reset"})
                
                elif data.get("action") == "ping":
                    # Keepalive
                    await send_event(StreamEventType.STATUS, {"message": "pong"})
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session: {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            try:
                await send_event(StreamEventType.ERROR, {
                    "error": "Connection error",
                    "detail": str(e),
                    "recoverable": False
                })
            except:
                pass
        finally:
            logger.info(f"Closing WebSocket for session: {session_id}")
            # Update final state
            storage.update_metadata(session_id, {"conversation": conversation_history})
    
    except Exception as e:
        logger.error(f"Failed to initialize streaming services: {e}")
        await websocket.close(code=1011, reason=f"Service initialization failed: {str(e)}")


async def should_llm_respond(transcript: str, conversation_history: list) -> bool:
    """
    Determine if LLM should respond based on the transcript and conversation context
    
    Simple heuristics:
    - Always respond if it's a question (ends with ?)
    - Respond if user is clearly waiting (short statement)
    - Don't respond to very short utterances (< 5 words)
    
    This can be enhanced with more sophisticated logic or a separate classifier model
    """
    transcript = transcript.strip()
    
    # Very short utterances - probably noise or incomplete
    words = transcript.split()
    if len(words) < 3:
        return False
    
    # Questions always get a response
    if transcript.endswith('?'):
        return True
    
    # Check for conversation starters or greetings
    starters = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
    if any(starter in transcript.lower() for starter in starters):
        return True
    
    # Check for explicit prompts
    prompts = ['what do you think', 'can you', 'could you', 'would you', 'tell me', 'help me']
    if any(prompt in transcript.lower() for prompt in prompts):
        return True
    
    # If user said something substantial (> 5 words), respond
    if len(words) >= 5:
        return True
    
    # Default: don't respond to very short statements
    return False
