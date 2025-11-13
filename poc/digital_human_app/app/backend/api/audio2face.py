"""
Audio2Face API endpoints for facial animation generation
"""
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel

from app.backend.services.audio2face_service import create_audio2face_service
from app.utils.storage import StorageService

router = APIRouter()
storage = StorageService()

# Service instance - lazy initialized
_audio2face_service = None


def get_audio2face_service():
    """Lazy initialization of Audio2Face service"""
    global _audio2face_service
    
    if _audio2face_service is None:
        provider = os.getenv("AUDIO2FACE_PROVIDER", "mock")
        
        try:
            if provider == "nvidia":
                api_key = os.getenv("NVIDIA_API_KEY")
                if not api_key:
                    raise ValueError("NVIDIA_API_KEY environment variable required for NVIDIA provider")
                model = os.getenv("AUDIO2FACE_MODEL", "nvidia/audio2face-3d")
                _audio2face_service = create_audio2face_service(
                    provider="nvidia",
                    api_key=api_key,
                    model=model
                )
            elif provider == "huggingface":
                api_key = os.getenv("HUGGINGFACE_API_KEY")
                model = os.getenv("AUDIO2FACE_MODEL", "nvidia/Audio2Face-3D-v3.0")
                _audio2face_service = create_audio2face_service(
                    provider="huggingface",
                    api_key=api_key,
                    model=model
                )
            elif provider == "onnx":
                model_path = os.getenv("AUDIO2FACE_MODEL_PATH", "./models/audio2face.onnx")
                device = os.getenv("AUDIO2FACE_DEVICE", "cuda")
                _audio2face_service = create_audio2face_service(
                    provider="onnx",
                    model_path=model_path,
                    device=device
                )
            else:  # mock
                _audio2face_service = create_audio2face_service(provider="mock")
            
            logger.info(f"Audio2Face service initialized: {provider}")
        except Exception as e:
            logger.error(f"Failed to initialize Audio2Face service: {e}")
            # Fallback to mock
            _audio2face_service = create_audio2face_service(provider="mock")
            logger.warning("Using mock Audio2Face service as fallback")
    
    return _audio2face_service


class AnimationRequest(BaseModel):
    """Request to generate facial animation"""
    audio_url: str


class AnimationResponse(BaseModel):
    """Response with facial animation"""
    video_url: Optional[str] = None
    blendshapes_url: Optional[str] = None
    fps: int
    duration: float
    model: str


@router.post("/generate", response_model=AnimationResponse)
async def generate_animation(
    audio: UploadFile = File(...)
):
    """
    Generate facial animation from uploaded audio
    
    The audio file is processed to generate lip-sync and facial animation.
    Returns video URL and blendshape data.
    """
    try:
        audio2face = get_audio2face_service()
        
        # Save uploaded audio temporarily
        temp_audio_path = storage.get_temp_path(f"audio2face_input_{audio.filename}")
        with open(temp_audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        logger.info(f"Generating facial animation from audio: {audio.filename}")
        
        # Generate animation
        result = await audio2face.generate_facial_animation(
            audio_path=temp_audio_path
        )
        
        # Save outputs
        video_path = result.get("video_path")
        video_url = None
        blendshapes_url = None
        
        if video_path and os.path.exists(video_path):
            # Copy to storage
            video_filename = f"animation_{Path(audio.filename).stem}.mp4"
            saved_video_path = storage.save_temp_file(video_path, video_filename)
            video_url = f"/api/audio2face/video/{video_filename}"
        
        # Save blendshapes as JSON
        if result.get("blendshapes"):
            import json
            blendshapes_filename = f"blendshapes_{Path(audio.filename).stem}.json"
            blendshapes_path = storage.get_temp_path(blendshapes_filename)
            with open(blendshapes_path, 'w') as f:
                json.dump({
                    "blendshapes": result["blendshapes"],
                    "fps": result["fps"],
                    "duration": result["duration"]
                }, f)
            blendshapes_url = f"/api/audio2face/blendshapes/{blendshapes_filename}"
        
        # Cleanup temp audio
        try:
            os.remove(temp_audio_path)
        except:
            pass
        
        return AnimationResponse(
            video_url=video_url,
            blendshapes_url=blendshapes_url,
            fps=result["fps"],
            duration=result["duration"],
            model=result["model"]
        )
        
    except Exception as e:
        logger.error(f"Error generating facial animation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate animation: {str(e)}")


@router.get("/video/{filename}")
async def get_animation_video(filename: str):
    """Serve generated animation video"""
    try:
        video_path = storage.get_temp_path(filename)
        
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video not found")
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blendshapes/{filename}")
async def get_blendshapes(filename: str):
    """Serve blendshapes JSON data"""
    try:
        blendshapes_path = storage.get_temp_path(filename)
        
        if not os.path.exists(blendshapes_path):
            raise HTTPException(status_code=404, detail="Blendshapes not found")
        
        return FileResponse(
            blendshapes_path,
            media_type="application/json",
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving blendshapes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-url", response_model=AnimationResponse)
async def generate_animation_from_url(request: AnimationRequest):
    """
    Generate facial animation from audio URL
    
    Downloads audio from URL and generates animation.
    """
    try:
        import requests
        
        audio2face = get_audio2face_service()
        
        # Download audio
        logger.info(f"Downloading audio from: {request.audio_url}")
        response = requests.get(request.audio_url, timeout=30)
        response.raise_for_status()
        
        # Save temporarily
        temp_audio_path = storage.get_temp_path("audio2face_input.wav")
        with open(temp_audio_path, "wb") as f:
            f.write(response.content)
        
        # Generate animation
        result = await audio2face.generate_facial_animation(
            audio_path=temp_audio_path
        )
        
        # Save outputs (similar to generate_animation)
        video_url = None
        blendshapes_url = None
        
        if result.get("video_path") and os.path.exists(result["video_path"]):
            video_filename = "animation_from_url.mp4"
            saved_video_path = storage.save_temp_file(result["video_path"], video_filename)
            video_url = f"/api/audio2face/video/{video_filename}"
        
        if result.get("blendshapes"):
            import json
            blendshapes_filename = "blendshapes_from_url.json"
            blendshapes_path = storage.get_temp_path(blendshapes_filename)
            with open(blendshapes_path, 'w') as f:
                json.dump({
                    "blendshapes": result["blendshapes"],
                    "fps": result["fps"],
                    "duration": result["duration"]
                }, f)
            blendshapes_url = f"/api/audio2face/blendshapes/{blendshapes_filename}"
        
        # Cleanup
        try:
            os.remove(temp_audio_path)
        except:
            pass
        
        return AnimationResponse(
            video_url=video_url,
            blendshapes_url=blendshapes_url,
            fps=result["fps"],
            duration=result["duration"],
            model=result["model"]
        )
        
    except Exception as e:
        logger.error(f"Error generating animation from URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate animation: {str(e)}")
