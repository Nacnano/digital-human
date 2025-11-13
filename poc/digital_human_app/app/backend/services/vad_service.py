"""
Voice Activity Detection Service for detecting speech segments
"""
import io
import numpy as np
import torch
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from loguru import logger


class VADService(ABC):
    """Abstract base class for VAD services"""
    
    @abstractmethod
    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        """
        Detect if audio chunk contains speech
        
        Args:
            audio_chunk: Raw audio bytes
            sample_rate: Sample rate in Hz
            
        Returns:
            True if speech detected, False otherwise
        """
        pass
    
    @abstractmethod
    def reset(self):
        """Reset VAD state"""
        pass


class SileroVAD(VADService):
    """
    Silero VAD implementation
    High-quality pre-trained VAD model
    """
    
    def __init__(self, threshold: float = 0.5):
        """
        Initialize Silero VAD
        
        Args:
            threshold: Speech probability threshold (0-1)
        """
        self.threshold = threshold
        self._model = None
        self._utils = None
        logger.info(f"SileroVAD initialized (threshold={threshold})")
    
    def _load_model(self):
        """Lazy load the Silero VAD model"""
        if self._model is None:
            try:
                logger.info("Loading Silero VAD model...")
                self._model, self._utils = torch.hub.load(
                    repo_or_dir='snakers4/silero-vad',
                    model='silero_vad',
                    force_reload=False,
                    onnx=False
                )
                logger.info("Silero VAD model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Silero VAD model: {e}")
                raise
    
    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        """Detect speech in audio chunk"""
        self._load_model()
        
        try:
            # Convert bytes to numpy array
            audio_int16 = np.frombuffer(audio_chunk, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_float32)
            
            # Get speech probability
            speech_prob = self._model(audio_tensor, sample_rate).item()
            
            return speech_prob > self.threshold
            
        except Exception as e:
            logger.error(f"VAD detection error: {e}")
            return False
    
    def reset(self):
        """Reset VAD state"""
        if self._model is not None:
            self._model.reset_states()


class WebRTCVAD(VADService):
    """
    WebRTC VAD implementation
    Lightweight and fast VAD
    """
    
    def __init__(self, aggressiveness: int = 3):
        """
        Initialize WebRTC VAD
        
        Args:
            aggressiveness: VAD aggressiveness level (0-3)
                           0: Least aggressive
                           3: Most aggressive
        """
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad(aggressiveness)
            self.aggressiveness = aggressiveness
            logger.info(f"WebRTCVAD initialized (aggressiveness={aggressiveness})")
        except ImportError:
            raise ImportError("webrtcvad not installed. Install with: pip install webrtcvad")
    
    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        """
        Detect speech in audio chunk
        
        Note: WebRTC VAD requires specific sample rates (8000, 16000, 32000, 48000 Hz)
        and frame sizes (10, 20, 30 ms)
        """
        try:
            # WebRTC VAD expects specific frame sizes
            # For 16kHz: 160 bytes (10ms), 320 bytes (20ms), 480 bytes (30ms)
            if sample_rate not in [8000, 16000, 32000, 48000]:
                logger.warning(f"Unsupported sample rate for WebRTC VAD: {sample_rate}")
                return False
            
            # Ensure frame size is valid
            frame_duration_ms = len(audio_chunk) * 1000 // (sample_rate * 2)  # *2 for int16
            if frame_duration_ms not in [10, 20, 30]:
                # Pad or truncate to valid size
                target_samples = (sample_rate * 20) // 1000  # 20ms frame
                target_bytes = target_samples * 2
                
                if len(audio_chunk) < target_bytes:
                    audio_chunk = audio_chunk + b'\x00' * (target_bytes - len(audio_chunk))
                else:
                    audio_chunk = audio_chunk[:target_bytes]
            
            return self.vad.is_speech(audio_chunk, sample_rate)
            
        except Exception as e:
            logger.error(f"WebRTC VAD detection error: {e}")
            return False
    
    def reset(self):
        """Reset VAD state (no-op for WebRTC VAD)"""
        pass


class SimpleEnergyVAD(VADService):
    """
    Simple energy-based VAD
    Fallback option when other VADs are unavailable
    """
    
    def __init__(self, threshold: float = 0.01):
        """
        Initialize energy-based VAD
        
        Args:
            threshold: Energy threshold for speech detection
        """
        self.threshold = threshold
        logger.info(f"SimpleEnergyVAD initialized (threshold={threshold})")
    
    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        """Detect speech based on audio energy"""
        try:
            # Convert bytes to numpy array
            audio_int16 = np.frombuffer(audio_chunk, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            
            # Calculate RMS energy
            energy = np.sqrt(np.mean(audio_float32 ** 2))
            
            return energy > self.threshold
            
        except Exception as e:
            logger.error(f"Energy VAD detection error: {e}")
            return False
    
    def reset(self):
        """Reset VAD state (no-op for energy VAD)"""
        pass


def create_vad_service(
    provider: str = "silero",
    **kwargs
) -> VADService:
    """
    Create VAD service instance
    
    Args:
        provider: VAD provider ('silero', 'webrtc', 'energy')
        **kwargs: Provider-specific arguments
        
    Returns:
        VADService instance
    """
    if provider == "silero":
        return SileroVAD(**kwargs)
    elif provider == "webrtc":
        return WebRTCVAD(**kwargs)
    elif provider == "energy":
        return SimpleEnergyVAD(**kwargs)
    else:
        raise ValueError(f"Unknown VAD provider: {provider}")


class VADSegmenter:
    """
    Helper class to segment audio stream into speech chunks using VAD
    """
    
    def __init__(
        self,
        vad_service: VADService,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,
        padding_duration_ms: int = 300,
        min_speech_duration_ms: int = 250
    ):
        """
        Initialize VAD segmenter
        
        Args:
            vad_service: VAD service to use
            sample_rate: Audio sample rate in Hz
            frame_duration_ms: Frame duration for VAD checks
            padding_duration_ms: Padding duration before/after speech
            min_speech_duration_ms: Minimum speech duration to consider valid
        """
        self.vad = vad_service
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.padding_duration_ms = padding_duration_ms
        self.min_speech_duration_ms = min_speech_duration_ms
        
        # Calculate frame sizes
        self.frame_size = (sample_rate * frame_duration_ms) // 1000
        self.frame_bytes = self.frame_size * 2  # 16-bit audio
        
        # State
        self.is_speaking = False
        self.speech_frames = []
        self.silence_frames = 0
        self.padding_frames = padding_duration_ms // frame_duration_ms
        
        logger.info(f"VADSegmenter initialized (sample_rate={sample_rate}, frame_duration={frame_duration_ms}ms)")
    
    def process_frame(self, frame: bytes) -> Tuple[bool, Optional[bytes]]:
        """
        Process audio frame and return speech segment when complete
        
        Args:
            frame: Audio frame bytes
            
        Returns:
            Tuple of (is_speaking, speech_segment)
            - is_speaking: True if currently in speech segment
            - speech_segment: Complete speech audio bytes (None if not complete)
        """
        is_speech = self.vad.is_speech(frame, self.sample_rate)
        
        if is_speech:
            self.speech_frames.append(frame)
            self.silence_frames = 0
            
            if not self.is_speaking:
                self.is_speaking = True
                logger.debug("Speech started")
        else:
            if self.is_speaking:
                self.silence_frames += 1
                self.speech_frames.append(frame)  # Add silence frame
                
                # Check if speech segment ended
                if self.silence_frames >= self.padding_frames:
                    # Calculate speech duration
                    speech_duration_ms = len(self.speech_frames) * self.frame_duration_ms
                    
                    if speech_duration_ms >= self.min_speech_duration_ms:
                        # Return complete speech segment
                        speech_segment = b''.join(self.speech_frames)
                        logger.debug(f"Speech ended (duration={speech_duration_ms}ms)")
                        
                        # Reset state
                        self.speech_frames = []
                        self.silence_frames = 0
                        self.is_speaking = False
                        
                        return False, speech_segment
                    else:
                        # Too short, discard
                        logger.debug(f"Speech too short, discarding (duration={speech_duration_ms}ms)")
                        self.speech_frames = []
                        self.silence_frames = 0
                        self.is_speaking = False
        
        return self.is_speaking, None
    
    def reset(self):
        """Reset segmenter state"""
        self.is_speaking = False
        self.speech_frames = []
        self.silence_frames = 0
        self.vad.reset()
