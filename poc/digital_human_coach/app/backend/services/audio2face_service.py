"""
Audio2Face Service for generating facial animations from audio
Supports multiple backends: HuggingFace API, Local ONNX, Mock
"""
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
from loguru import logger


class Audio2FaceService(ABC):
    """Abstract base class for Audio2Face services"""
    
    @abstractmethod
    async def generate_facial_animation(
        self,
        audio_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate facial animation from audio file
        
        Args:
            audio_path: Path to audio file
            output_path: Optional path to save animation video
            
        Returns:
            Dictionary with animation data:
            - video_path: Path to generated video
            - blendshapes: Array of blendshape weights per frame
            - fps: Frames per second
            - duration: Animation duration in seconds
        """
        pass


class NVIDIAAudio2Face(Audio2FaceService):
    """Audio2Face using NVIDIA NIM API (build.nvidia.com)"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "nvidia/audio2face-3d"
    ):
        self.api_key = api_key
        self.model = model
        # NVIDIA NIM API endpoint for Audio2Face-3D
        self.api_url = "https://integrate.api.nvidia.com/v1/audio2face"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"Initialized NVIDIA Audio2Face with model: {model}")
    
    async def generate_facial_animation(
        self,
        audio_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate facial animation using NVIDIA NIM API"""
        try:
            import requests
            import base64
            import json
            
            # Read and encode audio file
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # Encode audio to base64 for API
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Prepare request payload
            payload = {
                "audio": audio_base64,
                "model": self.model,
                "output_format": "blendshapes",  # ARKit blendshapes
                "fps": 60
            }
            
            # Call NVIDIA API
            logger.info(f"Calling NVIDIA API for Audio2Face: {self.model}")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"NVIDIA API error: {response.status_code} - {response.text}")
            
            # Parse response
            result = response.json()
            
            # Generate video from blendshapes if available
            if output_path is None:
                output_path = tempfile.mktemp(suffix=".mp4")
            
            # Extract blendshapes data
            blendshapes = result.get("blendshapes", [])
            fps = result.get("fps", 60)
            duration = len(blendshapes) / fps if blendshapes else 0
            
            # Note: Actual video rendering would be done here
            # For now, save blendshapes data
            blendshapes_path = output_path.replace(".mp4", "_blendshapes.json")
            with open(blendshapes_path, 'w') as f:
                json.dump({"blendshapes": blendshapes, "fps": fps}, f)
            
            logger.info(f"Generated animation: {len(blendshapes)} frames at {fps} FPS")
            
            return {
                "video_path": output_path,
                "blendshapes": blendshapes,
                "blendshapes_path": blendshapes_path,
                "fps": fps,
                "duration": duration,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Error generating facial animation with NVIDIA API: {e}")
            raise


class HuggingFaceAudio2Face(Audio2FaceService):
    """Audio2Face using Hugging Face Inference API"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "nvidia/Audio2Face-3D-v3.0"
    ):
        self.api_key = api_key
        self.model = model
        self.api_url = f"https://api-inference.huggingface.co/models/{model}"
        logger.info(f"Initialized HuggingFace Audio2Face with model: {model}")
    
    async def generate_facial_animation(
        self,
        audio_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate facial animation using HuggingFace API"""
        try:
            import requests
            import json
            
            # Read audio file
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Call HuggingFace API
            logger.info(f"Calling HuggingFace API for Audio2Face: {self.model}")
            response = requests.post(
                self.api_url,
                headers=headers,
                data=audio_data,
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"HuggingFace API error: {response.status_code} - {response.text}")
            
            # Parse response
            result = response.json()
            
            # Generate video from blendshapes if available
            if output_path is None:
                output_path = tempfile.mktemp(suffix=".mp4")
            
            # Note: Actual implementation would render blendshapes to video
            # For now, return the data structure
            return {
                "video_path": output_path,
                "blendshapes": result.get("blendshapes", []),
                "fps": result.get("fps", 60),
                "duration": result.get("duration", 0),
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Error generating facial animation with HuggingFace: {e}")
            raise


class LocalONNXAudio2Face(Audio2FaceService):
    """Audio2Face using local ONNX model"""
    
    def __init__(
        self,
        model_path: str,
        device: str = "cuda"
    ):
        self.model_path = model_path
        self.device = device
        self.session = None
        logger.info(f"Initializing Local ONNX Audio2Face from: {model_path}")
        
        try:
            import onnxruntime as ort
            
            # Set providers based on device
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if device == 'cuda' else ['CPUExecutionProvider']
            
            # Load ONNX model
            self.session = ort.InferenceSession(model_path, providers=providers)
            logger.info(f"Loaded ONNX model successfully on {device}")
            
        except ImportError:
            logger.warning("onnxruntime not installed. Install with: pip install onnxruntime-gpu")
            raise
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")
            raise
    
    async def generate_facial_animation(
        self,
        audio_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate facial animation using local ONNX model"""
        try:
            import librosa
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            duration = len(audio) / sr
            
            # Prepare input (adjust based on actual model requirements)
            audio_input = audio.astype(np.float32).reshape(1, -1)
            
            # Run inference
            logger.info(f"Running ONNX inference on audio ({duration:.2f}s)")
            outputs = self.session.run(None, {"input": audio_input})
            
            # Extract blendshapes
            blendshapes = outputs[0]  # Adjust index based on model
            
            # Generate video
            if output_path is None:
                output_path = tempfile.mktemp(suffix=".mp4")
            
            # Render blendshapes to video
            fps = 60
            await self._render_to_video(blendshapes, audio_path, output_path, fps)
            
            return {
                "video_path": output_path,
                "blendshapes": blendshapes.tolist(),
                "fps": fps,
                "duration": duration,
                "model": "local-onnx"
            }
            
        except Exception as e:
            logger.error(f"Error generating facial animation with ONNX: {e}")
            raise
    
    async def _render_to_video(
        self,
        blendshapes: np.ndarray,
        audio_path: str,
        output_path: str,
        fps: int = 60
    ):
        """Render blendshapes to video with audio"""
        # This is a placeholder - actual rendering would use OpenGL/pyrender
        # or export to format that can be rendered in frontend
        logger.info(f"Rendering {len(blendshapes)} frames to video at {fps} FPS")
        
        # For now, create a simple placeholder video
        # In production, this would:
        # 1. Load 3D face mesh
        # 2. Apply blendshapes per frame
        # 3. Render each frame
        # 4. Combine frames with audio into MP4
        pass


class MockAudio2Face(Audio2FaceService):
    """Mock Audio2Face service for testing without model"""
    
    def __init__(self):
        logger.info("Initialized Mock Audio2Face service")
    
    async def generate_facial_animation(
        self,
        audio_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate mock facial animation"""
        try:
            import librosa
            
            # Get audio duration
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            duration = len(audio) / sr
            
            # Generate fake blendshapes (sinusoidal patterns)
            fps = 60
            num_frames = int(duration * fps)
            num_blendshapes = 52  # ARKit standard blendshape count
            
            # Create fake animation
            t = np.linspace(0, duration, num_frames)
            blendshapes = []
            
            for i in range(num_frames):
                frame_blendshapes = np.zeros(num_blendshapes)
                # Animate mouth (blendshapes 0-15 typically mouth-related)
                frame_blendshapes[0] = 0.5 * (1 + np.sin(t[i] * 10))  # Jaw open
                frame_blendshapes[1] = 0.3 * (1 + np.sin(t[i] * 15))  # Mouth smile
                # Add some blink animation
                frame_blendshapes[25] = 0.2 * (1 + np.sin(t[i] * 2))  # Eye blink
                blendshapes.append(frame_blendshapes)
            
            blendshapes = np.array(blendshapes)
            
            if output_path is None:
                output_path = tempfile.mktemp(suffix=".mp4")
            
            logger.info(f"Generated mock animation: {num_frames} frames at {fps} FPS")
            
            return {
                "video_path": output_path,
                "blendshapes": blendshapes.tolist(),
                "fps": fps,
                "duration": duration,
                "model": "mock"
            }
            
        except Exception as e:
            logger.error(f"Error generating mock facial animation: {e}")
            raise


def create_audio2face_service(
    provider: str = "mock",
    **kwargs
) -> Audio2FaceService:
    """
    Factory function to create Audio2Face service
    
    Args:
        provider: Service provider ('nvidia', 'huggingface', 'onnx', 'mock')
        **kwargs: Provider-specific arguments
            - For nvidia: api_key, model
            - For huggingface: api_key, model
            - For onnx: model_path, device
    
    Returns:
        Audio2FaceService instance
    """
    provider = provider.lower()
    
    if provider == "nvidia":
        api_key = kwargs.get("api_key")
        if not api_key:
            raise ValueError("api_key required for NVIDIA provider")
        model = kwargs.get("model", "nvidia/audio2face-3d")
        return NVIDIAAudio2Face(api_key=api_key, model=model)
    
    elif provider == "huggingface":
        api_key = kwargs.get("api_key")
        if not api_key:
            raise ValueError("api_key required for HuggingFace provider")
        model = kwargs.get("model", "nvidia/Audio2Face-3D-v3.0")
        return HuggingFaceAudio2Face(api_key=api_key, model=model)
    
    elif provider == "onnx":
        model_path = kwargs.get("model_path")
        if not model_path:
            raise ValueError("model_path required for ONNX provider")
        device = kwargs.get("device", "cuda")
        return LocalONNXAudio2Face(model_path=model_path, device=device)
    
    elif provider == "mock":
        return MockAudio2Face()
    
    else:
        raise ValueError(f"Unknown Audio2Face provider: {provider}")
