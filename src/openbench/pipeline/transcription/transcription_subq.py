from pathlib import Path
from typing import Callable

from deepgram import PrerecordedOptions
from pydantic import Field

from ...engine import SubqApi
from ...engine.deepgram_engine import DeepgramApiResponse
from ...pipeline import Pipeline, register_pipeline
from ...pipeline_prediction import Transcript
from ...types import PipelineType
from .common import TranscriptionConfig, TranscriptionOutput


TEMP_AUDIO_DIR = Path("temp_audio_dir")


class SubqTranscriptionPipelineConfig(TranscriptionConfig):
    model_version: str = Field(
        default="nova-3",
        description="The model version to use for SubQ transcription",
    )


@register_pipeline
class SubqTranscriptionPipeline(Pipeline):
    _config_class = SubqTranscriptionPipelineConfig
    pipeline_type = PipelineType.TRANSCRIPTION

    def build_pipeline(self) -> Callable[[Path], DeepgramApiResponse]:
        base_api = SubqApi(
            options=PrerecordedOptions(
                model=self.config.model_version, smart_format=True, detect_language=not self.config.force_language
            )
        )

        def transcribe(audio_path: Path) -> DeepgramApiResponse:
            if self.current_language:
                base_api.set_language(self.current_language)

            response = base_api.transcribe(audio_path, keyterm=self.current_keywords)
            audio_path.unlink(missing_ok=True)
            return response

        return transcribe

    def parse_input(self, input_sample) -> Path:
        self.current_keywords = None
        if self.config.use_keywords:
            keywords = input_sample.extra_info.get("dictionary", [])
            if keywords:
                self.current_keywords = "+".join(keywords)

        self.current_language = None
        if self.config.force_language:
            self.current_language = input_sample.language

        return input_sample.save_audio(TEMP_AUDIO_DIR)

    def parse_output(self, output: DeepgramApiResponse) -> TranscriptionOutput:
        return TranscriptionOutput(
            prediction=Transcript.from_words_info(
                words=output.words,
                speaker=output.speakers,
                start=output.start,
                end=output.end,
            )
        )
