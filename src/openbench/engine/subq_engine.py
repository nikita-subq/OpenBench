import os
from pathlib import Path

from deepgram import DeepgramClient, DeepgramClientOptions, FileSource, PrerecordedOptions, PrerecordedResponse
from httpx import Timeout

from .deepgram_engine import DeepgramApiResponse


SUBQ_DEFAULT_HOST = "https://api.aldea.ai"

_CONTENT_TYPES = {
    ".wav": "audio/wav",
    ".flac": "audio/flac",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    ".webm": "audio/webm",
}


class SubqApi:
    def __init__(self, options: PrerecordedOptions, timeout: Timeout = Timeout(600)):
        self.options = options
        self.timeout = timeout

        if not os.getenv("SUBQ_API_KEY"):
            raise ValueError("`SUBQ_API_KEY` is not set")

        self.host = os.getenv("SUBQ_HOST_URL", SUBQ_DEFAULT_HOST)
        config = DeepgramClientOptions(url=self.host)
        self.client = DeepgramClient(os.getenv("SUBQ_API_KEY"), config)

    def set_language(self, language: str) -> None:
        self.options.language = language

    def transcribe(self, audio_path: Path | str, keyterm: str | None = None) -> DeepgramApiResponse:
        if keyterm:
            base_url = f"{self.host}/v1/listen?model={self.options.model}"
            base_url += f"&keyterm={keyterm}"
            self.client._config.url = base_url
        else:
            self.client._config.url = self.host

        if isinstance(audio_path, str):
            audio_path = Path(audio_path)

        with audio_path.open("rb") as file:
            buffer_data = file.read()
        payload: FileSource = {"buffer": buffer_data}

        content_type = _CONTENT_TYPES.get(audio_path.suffix.lower(), "audio/wav")
        extra_headers = {"Content-Type": content_type}

        response: PrerecordedResponse = self.client.listen.rest.v("1").transcribe_file(
            payload, self.options, headers=extra_headers, timeout=self.timeout
        )

        words = response.results.channels[0].alternatives[0].words
        return DeepgramApiResponse(
            words=[getattr(w, "punctuated_word", None) or w.word for w in words],
            speakers=[str(w.speaker) if w.speaker is not None else "0" for w in words],
            start=[float(w.start) for w in words],
            end=[float(w.end) for w in words],
        )
