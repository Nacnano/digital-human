"""
Conversation API endpoints
"""
import base64
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from loguru import logger

from app.backend.models.schemas import (
    ConversationHistory,
    ConversationMessage,
    ConversationResponse,
    MessageRole,
    SessionCreate,
    SessionResponse,
    SessionType,
)
from app.backend.services.llm_service import CONVERSATION_SYSTEM_PROMPT, create_llm_service
from app.backend.services.stt_service import create_stt_service
from app.backend.services.tts_service import create_tts_service
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
    try:
        audio_filename = f"response_{len(conversation_history)}.mp3"
        audio_path = str(Path(storage.get_session_path(session_id)) / "audio" / audio_filename)
        await tts_service.generate_to_file(response_text, audio_path)
        audio_url = f"/temp/sessions/{session_id}/audio/{audio_filename}"
    except Exception as e:
        logger.warning(f"TTS error: {e}")
        # Continue without audio
    
    # Update session metadata
    storage.update_metadata(session_id, {"conversation": conversation_history})
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return ConversationResponse(
        message=ConversationMessage(
            role=MessageRole.ASSISTANT,
            content=response_text,
            timestamp=datetime.now()
        ),
        audio_url=audio_url,
        processing_time=processing_time
    )


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
