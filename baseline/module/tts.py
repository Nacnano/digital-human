from typing import Iterator

from elevenlabs import ElevenLabs


class TTS:
    def __init__(self, api_key: str, voice_id: str, model_id: str):
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.model_id = model_id

    def generate(self, text: str) -> Iterator[bytes]:
        audio_stream = self.client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
            model_id=self.model_id,
            output_format="mp3_44100_128",
        )
        return audio_stream


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv
    from elevenlabs import play

    load_dotenv()
    tts = TTS(
        api_key=os.getenv("ELEVEN_LABS_API_KEY", ""),
        voice_id="TX3LPaxmHKxFdv7VOQHJ",
        model_id="eleven_multilingual_v2",
    )
    audio_stream = tts.generate("Hello Everyone, How are you doing today?")
    play(audio_stream)
