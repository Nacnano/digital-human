"""
Evaluation API endpoints
"""
import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from loguru import logger

from app.backend.models.schemas import (
    AIFeedback,
    EvaluationResult,
    EvaluationStatus,
    SessionStatus,
    VideoUploadResponse,
)
from app.backend.services.llm_service import EVALUATION_SYSTEM_PROMPT, create_llm_service
from app.backend.services.metrics_service import MetricsService
from app.backend.services.pose_service import PoseService
from app.backend.services.stt_service import create_stt_service
from app.backend.services.tts_service import create_tts_service
from app.utils.storage import StorageService
from app.utils.video_utils import extract_audio_from_video, get_video_duration

router = APIRouter()
storage = StorageService()

# Service instances - lazy initialized
_llm_service = None
_stt_service = None
_tts_service = None
_pose_service = None
_metrics_service = None

def get_services():
    """Lazy initialization of services"""
    global _llm_service, _stt_service, _tts_service, _pose_service, _metrics_service
    
    if _llm_service is None:
        llm_provider = os.getenv("LLM_PROVIDER", "openai")
        # Get the appropriate API key based on provider
        if llm_provider in ["google", "gemini"]:
            api_key = os.getenv("GOOGLE_API_KEY")
        elif llm_provider == "typhoon":
            api_key = os.getenv("TYPHOON_API_KEY")
        elif llm_provider == "nvidia":
            api_key = os.getenv("NVIDIA_API_KEY")
        elif llm_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
        else:
            api_key = os.getenv("OPENAI_API_KEY")
        
        _llm_service = create_llm_service(
            provider=llm_provider,
            api_key=api_key,
            model=os.getenv("LLM_MODEL")
        )
    if _stt_service is None:
        _stt_service = create_stt_service(
            provider=os.getenv("STT_PROVIDER", "whisper")
        )
    if _tts_service is None:
        _tts_service = create_tts_service(
            provider=os.getenv("TTS_PROVIDER", "edge")
        )
    if _pose_service is None:
        _pose_service = PoseService()
    if _metrics_service is None:
        _metrics_service = MetricsService()
    
    return _llm_service, _stt_service, _tts_service, _pose_service, _metrics_service


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """Upload video for evaluation"""
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Create session
    session_id = storage.create_session("evaluation")
    
    # Save video
    video_data = await file.read()
    video_filename = f"input.{file.filename.split('.')[-1]}"
    video_path = storage.save_file(session_id, video_data, video_filename, "video")
    
    # Get video info
    try:
        duration = get_video_duration(video_path)
    except Exception:
        duration = None
    
    file_size = len(video_data)
    
    storage.update_metadata(session_id, {
        "video_path": video_path,
        "video_filename": file.filename,
        "file_size": file_size,
        "duration": duration
    })
    
    logger.info(f"Video uploaded for session {session_id}: {file.filename}")
    
    return VideoUploadResponse(
        session_id=session_id,
        video_url=f"/temp/sessions/{session_id}/video/{video_filename}",
        file_size=file_size,
        duration_seconds=duration,
        status="uploaded"
    )


async def process_evaluation(session_id: str):
    """Background task to process video evaluation"""
    try:
        # Get services
        llm_service, stt_service, tts_service, pose_service, metrics_service = get_services()
        
        storage.update_metadata(session_id, {"status": "processing", "progress": 0})
        
        metadata = storage.get_metadata(session_id)
        video_path = metadata["video_path"]
        
        # Step 1: Extract audio (10%)
        logger.info(f"[{session_id}] Extracting audio...")
        audio_path = str(Path(video_path).parent / "audio.wav")
        extract_audio_from_video(video_path, audio_path)
        storage.update_metadata(session_id, {"progress": 10})
        
        # Step 2: Transcribe audio (30%)
        logger.info(f"[{session_id}] Transcribing audio...")
        transcript = await stt_service.transcribe(audio_path)
        storage.update_metadata(session_id, {"progress": 30, "transcript": transcript})
        
        # Step 3: Analyze speech metrics (50%)
        logger.info(f"[{session_id}] Analyzing speech metrics...")
        speech_metrics = metrics_service.analyze_speech(
            audio_path,
            transcript,
            metadata.get("duration")
        )
        storage.update_metadata(session_id, {"progress": 50})
        
        # Step 4: Analyze pose (70%)
        logger.info(f"[{session_id}] Analyzing body language...")
        pose_metrics = pose_service.analyze_video(video_path)
        storage.update_metadata(session_id, {"progress": 70})
        
        # Step 5: Generate AI feedback (85%)
        logger.info(f"[{session_id}] Generating AI feedback...")
        feedback_prompt = metrics_service.generate_feedback_prompt(
            transcript, speech_metrics, pose_metrics
        )
        
        feedback_text = await llm_service.generate_text(
            feedback_prompt,
            system_prompt=EVALUATION_SYSTEM_PROMPT
        )
        
        # Parse feedback (expect JSON format)
        try:
            feedback_data = json.loads(feedback_text)
        except json.JSONDecodeError:
            # Fallback if not JSON
            feedback_data = {
                "overall_score": 7.0,
                "strengths": ["Good content"],
                "areas_for_improvement": ["Practice more"],
                "specific_recommendations": ["Keep practicing"],
                "detailed_feedback": feedback_text
            }
        
        storage.update_metadata(session_id, {"progress": 85})
        
        # Step 6: Generate audio feedback (95%)
        logger.info(f"[{session_id}] Generating audio feedback...")
        audio_feedback_path = str(Path(storage.get_session_path(session_id)) / "feedback.mp3")
        await tts_service.generate_to_file(
            feedback_data["detailed_feedback"],
            audio_feedback_path
        )
        audio_feedback_url = f"/temp/sessions/{session_id}/feedback.mp3"
        storage.update_metadata(session_id, {"progress": 95})
        
        # Create result
        result = EvaluationResult(
            session_id=session_id,
            video_url=f"/temp/sessions/{session_id}/video/input.mp4",
            transcript=transcript,
            duration_seconds=metadata.get("duration", 0),
            speech_metrics=speech_metrics,
            pose_metrics=pose_metrics,
            feedback=AIFeedback(
                overall_score=feedback_data.get("overall_score", 7.0),
                strengths=feedback_data.get("strengths", []),
                areas_for_improvement=feedback_data.get("areas_for_improvement", []),
                specific_recommendations=feedback_data.get("specific_recommendations", []),
                detailed_feedback=feedback_data.get("detailed_feedback", ""),
                audio_feedback_url=audio_feedback_url
            ),
            created_at=datetime.now()
        )
        
        # Save results
        storage.save_results(session_id, result.model_dump(mode="json"))
        storage.update_metadata(session_id, {"status": "completed", "progress": 100})
        
        logger.info(f"[{session_id}] Evaluation complete!")
        
    except Exception as e:
        logger.error(f"[{session_id}] Evaluation failed: {e}")
        storage.update_metadata(session_id, {
            "status": "failed",
            "error": str(e)
        })


@router.post("/{session_id}/analyze")
async def analyze_video(session_id: str, background_tasks: BackgroundTasks):
    """Start video analysis"""
    metadata = storage.get_metadata(session_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add background task
    background_tasks.add_task(process_evaluation, session_id)
    
    return {"message": "Analysis started", "session_id": session_id}


@router.get("/{session_id}/status", response_model=EvaluationStatus)
async def get_status(session_id: str):
    """Get evaluation status"""
    metadata = storage.get_metadata(session_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Session not found")
    
    status = metadata.get("status", "active")
    progress = metadata.get("progress", 0)
    
    if status == "processing":
        message = f"Processing... {progress}%"
    elif status == "completed":
        message = "Analysis complete"
    elif status == "failed":
        message = f"Analysis failed: {metadata.get('error', 'Unknown error')}"
    else:
        message = "Waiting to start"
    
    return EvaluationStatus(
        session_id=session_id,
        status=SessionStatus(status),
        progress=progress,
        message=message
    )


@router.get("/{session_id}/report", response_model=EvaluationResult)
async def get_report(session_id: str):
    """Get evaluation report"""
    results = storage.get_results(session_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    return EvaluationResult(**results)
