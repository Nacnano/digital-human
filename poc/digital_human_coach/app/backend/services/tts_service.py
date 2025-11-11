"""
Text-to-Speech Service with multiple provider support
"""
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Optional, Union

from loguru import logger


class TTSService(ABC):
    """Abstract base class for TTS services"""
    
    @abstractmethod
    async def generate(self, text: str) -> Union[bytes, Iterator[bytes]]:
        """Generate speech from text"""
        pass
    
    @abstractmethod
    async def generate_to_file(self, text: str, output_path: str) -> str:
        """Generate speech and save to file"""
        pass


class ElevenLabsTTS(TTSService):
    """ElevenLabs TTS implementation"""
    
    def __init__(
        self,
        api_key: str,
        voice_id: str = "TX3LPaxmHKxFdv7VOQHJ",
        model_id: str = "eleven_multilingual_v2"
    ):
        try:
            from elevenlabs import ElevenLabs
            self.client = ElevenLabs(api_key=api_key)
            self.voice_id = voice_id
            self.model_id = model_id
            logger.info(f"Initialized ElevenLabs TTS with voice: {voice_id}")
        except ImportError:
            raise ImportError("elevenlabs not installed. Install with: pip install elevenlabs")
    
    async def generate(self, text: str) -> Iterator[bytes]:
        """Generate speech audio stream"""
        try:
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                output_format="mp3_44100_128",
            )
            return audio_stream
        except Exception as e:
            logger.error(f"ElevenLabs TTS generation error: {e}")
            raise
    
    async def generate_to_file(self, text: str, output_path: str) -> str:
        """Generate speech and save to file"""
        audio_stream = await self.generate(text)
        
        with open(output_path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
        
        logger.info(f"Saved TTS audio to: {output_path}")
        return output_path


class EdgeTTS(TTSService):
    """Microsoft Edge TTS implementation (free)"""
    
    def __init__(self, voice: str = "en-US-AriaNeural", rate: str = "+0%", volume: str = "+0%"):
        try:
            import edge_tts
            self.voice = voice
            self.rate = rate
            self.volume = volume
            logger.info(f"Initialized Edge TTS with voice: {voice}")
        except ImportError:
            raise ImportError("edge-tts not installed. Install with: pip install edge-tts")
    
    async def generate(self, text: str) -> bytes:
        """Generate speech audio"""
        import edge_tts
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume
            )
            await communicate.save(temp_path)
            
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            return audio_data
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    async def generate_to_file(self, text: str, output_path: str) -> str:
        """Generate speech and save to file"""
        import edge_tts
        
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume
        )
        await communicate.save(output_path)
        
        logger.info(f"Saved TTS audio to: {output_path}")
        return output_path


class gTTSService(TTSService):
    """Google TTS implementation (simple, free)"""
    
    def __init__(self, language: str = "en", slow: bool = False):
        try:
            from gtts import gTTS
            self.language = language
            self.slow = slow
            logger.info(f"Initialized gTTS with language: {language}")
        except ImportError:
            raise ImportError("gTTS not installed. Install with: pip install gtts")
    
    async def generate(self, text: str) -> bytes:
        """Generate speech audio"""
        from gtts import gTTS
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            tts = gTTS(text=text, lang=self.language, slow=self.slow)
            tts.save(temp_path)
            
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            return audio_data
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    async def generate_to_file(self, text: str, output_path: str) -> str:
        """Generate speech and save to file"""
        from gtts import gTTS
        
        tts = gTTS(text=text, lang=self.language, slow=self.slow)
        tts.save(output_path)
        
        logger.info(f"Saved TTS audio to: {output_path}")
        return output_path


class CoquiTTS(TTSService):
    """Coqui TTS implementation (open-source, local)"""
    
    def __init__(self, model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"):
        try:
            from TTS.api import TTS as CoquiAPI
            self.tts = CoquiAPI(model_name=model_name)
            logger.info(f"Initialized Coqui TTS with model: {model_name}")
        except ImportError:
            raise ImportError("TTS not installed. Install with: pip install TTS")
    
    async def generate(self, text: str) -> bytes:
        """Generate speech audio"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            self.tts.tts_to_file(text=text, file_path=temp_path)
            
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            return audio_data
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    async def generate_to_file(self, text: str, output_path: str) -> str:
        """Generate speech and save to file"""
        self.tts.tts_to_file(text=text, file_path=output_path)
        
        logger.info(f"Saved TTS audio to: {output_path}")
        return output_path


class TTSServiceFactory:
    """Factory for creating TTS service instances"""
    
    @staticmethod
    def create(provider: str, **kwargs) -> TTSService:
        """Create TTS service based on provider name"""
        providers = {
            "elevenlabs": ElevenLabsTTS,
            "edge": EdgeTTS,
            "gtts": gTTSService,
            "coqui": CoquiTTS,
        }
        
        if provider not in providers:
            raise ValueError(f"Unknown TTS provider: {provider}. Available: {list(providers.keys())}")
        
        return providers[provider](**kwargs)


# Convenience function
def create_tts_service(
    provider: str = "edge",
    api_key: Optional[str] = None,
    **kwargs
) -> TTSService:
    """
    Create TTS service with automatic configuration
    
    Args:
        provider: TTS provider name (elevenlabs, edge, gtts, coqui)
        api_key: API key for cloud providers
        **kwargs: Additional provider-specific arguments
    
    Returns:
        Configured TTS service instance
    """
    if provider == "elevenlabs":
        if not api_key:
            api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ElevenLabs requires API key")
        return ElevenLabsTTS(api_key=api_key, **kwargs)
    elif provider == "edge":
        return EdgeTTS(**kwargs)
    elif provider == "gtts":
        return gTTSService(**kwargs)
    elif provider == "coqui":
        return CoquiTTS(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")
