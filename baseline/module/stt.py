from typing import cast

from deepgram import DeepgramClient, FileSource, PrerecordedOptions
from deepgram.clients.listen.v1.rest.client import ListenRESTClient
from deepgram.clients.listen.v1.rest.response import PrerecordedResponse


class STT:
    def __init__(self, api_key: str):
        self._client = DeepgramClient(api_key)
        self.listen_client = cast(ListenRESTClient, self._client.listen.rest.v("1"))

    def transcribe(self, audio_file_path: str) -> str:
        with open(audio_file_path, "rb") as audio_file:
            buffered_data = audio_file.read()
            payload: FileSource = {
                "buffer": buffered_data,
            }

        options = PrerecordedOptions(
            model="nova-3",
            smart_format=True,
        )

        response = cast(
            PrerecordedResponse,
            self.listen_client.transcribe_file(
                source=payload,
                options=options,
            ),
        )
        if (
            response
            and response.results
            and response.results.channels
            and response.results.channels[0].alternatives
            and (transcript := response.results.channels[0].alternatives[0].transcript)
        ):
            return transcript
        return ""


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    stt = STT(os.getenv("DEEPGRAM_API_KEY", ""))
    print(stt.transcribe("../example/test.mp3"))
