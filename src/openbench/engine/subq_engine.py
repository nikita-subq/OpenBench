import os
from pathlib import Path

from argmaxtools.utils import get_logger
from deepgram import DeepgramClient, DeepgramClientOptions, FileSource, PrerecordedOptions, PrerecordedResponse
from httpx import Timeout

from .deepgram_engine import DeepgramApiResponse


logger = get_logger(__name__)


class SubqApi:
    def __init__(self, options: PrerecordedOptions, timeout: Timeout = Timeout(600)):
        self.options = options
        self.timeout = timeout

        if not os.getenv("SUBQ_API_KEY"):
            raise ValueError("`SUBQ_API_KEY` is not set")

        host = os.getenv("SUBQ_HOST_URL")
        if not host:
            raise ValueError("`SUBQ_HOST_URL` is not set")
        self.host = host

        print(f"[SubqApi] SUBQ_HOST_URL={self.host}", flush=True)
        logger.info("SubqApi initialized with SUBQ_HOST_URL=%s", self.host)

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

        response: PrerecordedResponse = self.client.listen.rest.v("1").transcribe_file(
            payload, self.options, timeout=self.timeout
        )

        return DeepgramApiResponse(
            words=[w.punctuated_word for w in response.results.channels[0].alternatives[0].words],
            speakers=[str(w.speaker) for w in response.results.channels[0].alternatives[0].words],
            start=[float(w.start) for w in response.results.channels[0].alternatives[0].words],
            end=[float(w.end) for w in response.results.channels[0].alternatives[0].words],
        )
