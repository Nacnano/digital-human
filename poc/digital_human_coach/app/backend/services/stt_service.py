"""
Speech-to-Text Service with multiple provider support
"""
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from loguru import logger


class STTService(ABC):
    """Abstract base class for STT services"""
    
    @abstractmethod
    async def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file to text"""
        pass
    
    @abstractmethod
    async def transcribe_stream(self, audio_data: bytes) -> str:
        """Transcribe audio data stream to text"""
        pass


class WhisperSTT(STTService):
    """OpenAI Whisper STT implementation with lazy loading"""
    
    def __init__(self, model: str = "base", language: Optional[str] = None):
        self.model_name = model
        self.language = language
        self._model = None
        logger.info(f"WhisperSTT initialized (model will load on first use): {model}")
    
    def _load_model(self):
        """Lazy load the Whisper model"""
        if self._model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model: {self.model_name}...")
                self._model = whisper.load_model(self.model_name)
                logger.info(f"Whisper model loaded successfully")
            except ImportError:
                raise ImportError("whisper not installed. Install with: pip install openai-whisper")
    
    async def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file using Whisper"""
        self._load_model()
        try:
            result = self._model.transcribe(
                audio_path,
                language=self.language,
                fp16=False
            )
            return result["text"].strip()
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            raise
    
    async def transcribe_stream(self, audio_data: bytes) -> str:
        """Transcribe audio data (save temporarily then process)"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            result = await self.transcribe(temp_path)
            return result
        finally:
            Path(temp_path).unlink(missing_ok=True)


class DeepgramSTT(STTService):
    """Deepgram STT implementation"""
    
    def __init__(self, api_key: str, model: str = "nova-2"):
        try:
            from deepgram import DeepgramClient
            self.client = DeepgramClient(api_key)
            self.model = model
            logger.info("Initialized Deepgram STT client")
        except ImportError:
            raise ImportError("deepgram-sdk not installed. Install with: pip install deepgram-sdk")
    
    async def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file using Deepgram"""
        try:
            from deepgram import FileSource, PrerecordedOptions
            
            with open(audio_path, "rb") as audio_file:
                buffer_data = audio_file.read()
            
            payload: FileSource = {"buffer": buffer_data}
            options = PrerecordedOptions(
                model=self.model,
                smart_format=True,
            )
            
            response = self.client.listen.rest.v("1").transcribe_file(
                payload, options
            )
            
            if (
                response
                and response.results
                and response.results.channels
                and response.results.channels[0].alternatives
            ):
                transcript = response.results.channels[0].alternatives[0].transcript
                return transcript.strip() if transcript else ""
            
            return ""
        except Exception as e:
            logger.error(f"Deepgram transcription error: {e}")
            raise
    
    async def transcribe_stream(self, audio_data: bytes) -> str:
        """Transcribe audio data stream"""
        try:
            from deepgram import FileSource, PrerecordedOptions
            
            payload: FileSource = {"buffer": audio_data}
            options = PrerecordedOptions(
                model=self.model,
                smart_format=True,
            )
            
            response = self.client.listen.rest.v("1").transcribe_file(
                payload, options
            )
            
            if (
                response
                and response.results
                and response.results.channels
                and response.results.channels[0].alternatives
            ):
                transcript = response.results.channels[0].alternatives[0].transcript
                return transcript.strip() if transcript else ""
            
            return ""
        except Exception as e:
            logger.error(f"Deepgram stream transcription error: {e}")
            raise


class GoogleSTT(STTService):
    """Google Cloud Speech-to-Text implementation"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        try:
            from google.cloud import speech
            if credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            self.client = speech.SpeechClient()
            logger.info("Initialized Google Cloud STT client")
        except ImportError:
            raise ImportError("google-cloud-speech not installed. Install with: pip install google-cloud-speech")
    
    async def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file using Google Cloud STT"""
        try:
            from google.cloud import speech
            
            with open(audio_path, "rb") as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                language_code="en-US",
                enable_automatic_punctuation=True,
            )
            
            response = self.client.recognize(config=config, audio=audio)
            
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript
            
            return transcript.strip()
        except Exception as e:
            logger.error(f"Google STT transcription error: {e}")
            raise
    
    async def transcribe_stream(self, audio_data: bytes) -> str:
        """Transcribe audio data stream"""
        try:
            from google.cloud import speech
            
            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                language_code="en-US",
                enable_automatic_punctuation=True,
            )
            
            response = self.client.recognize(config=config, audio=audio)
            
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript
            
            return transcript.strip()
        except Exception as e:
            logger.error(f"Google STT stream transcription error: {e}")
            raise


class STTServiceFactory:
    """Factory for creating STT service instances"""
    
    @staticmethod
    def create(provider: str, **kwargs) -> STTService:
        """Create STT service based on provider name"""
        providers = {
            "whisper": WhisperSTT,
            "deepgram": DeepgramSTT,
            "google": GoogleSTT,
        }
        
        if provider not in providers:
            raise ValueError(f"Unknown STT provider: {provider}. Available: {list(providers.keys())}")
        
        return providers[provider](**kwargs)


# Convenience function
def create_stt_service(
    provider: str = "whisper",
    api_key: Optional[str] = None,
    **kwargs
) -> STTService:
    """
    Create STT service with automatic configuration
    
    Args:
        provider: STT provider name (whisper, deepgram, google)
        api_key: API key for cloud providers
        **kwargs: Additional provider-specific arguments
    
    Returns:
        Configured STT service instance
    """
    if provider == "whisper":
        return WhisperSTT(**kwargs)
    elif provider == "deepgram":
        if not api_key:
            api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            raise ValueError("Deepgram requires API key")
        return DeepgramSTT(api_key=api_key, **kwargs)
    elif provider == "google":
        return GoogleSTT(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")
