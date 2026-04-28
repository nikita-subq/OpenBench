import asyncio
import json
import os

import numpy as np
import websockets
from argmaxtools.utils import get_logger
from pydantic import Field

from openbench.dataset import StreamingSample

from ...pipeline import Pipeline, register_pipeline
from ...pipeline_prediction import StreamingTranscript
from ...types import PipelineType
from .common import StreamingTranscriptionConfig, StreamingTranscriptionOutput


logger = get_logger(__name__)

SUBQ_DEFAULT_WS_HOST = "wss://api.aldea.ai"


class SubqStreamingApi:
    def __init__(self, cfg) -> None:
        self.realtime_resolution = 0.020
        self.model_version = cfg.model_version
        self.api_key = os.getenv("SUBQ_API_KEY")
        assert self.api_key is not None, "Please set `SUBQ_API_KEY` in environment"
        self.channels = cfg.channels
        self.sample_width = cfg.sample_width
        self.sample_rate = cfg.sample_rate
        self.host_url = os.getenv("SUBQ_HOST_URL", SUBQ_DEFAULT_WS_HOST)

    async def run(self, data, key, channels, sample_width, sample_rate):
        byte_rate = sample_width * sample_rate * channels
        global audio_cursor_l
        global interim_transcripts
        global confirmed_audio_cursor_l
        global confirmed_interim_transcripts
        global model_timestamps_hypothesis
        global model_timestamps_confirmed
        audio_cursor = 0.0
        audio_cursor_l = []
        interim_transcripts = []
        confirmed_audio_cursor_l = []
        confirmed_interim_transcripts = []
        model_timestamps_hypothesis = []
        model_timestamps_confirmed = []

        async with websockets.connect(
            f"{self.host_url}/v1/listen?model={self.model_version}&channels={channels}&sample_rate={sample_rate}&encoding=linear16&interim_results=true",
            additional_headers={
                "Authorization": "Token {}".format(key),
            },
        ) as ws:

            async def sender(ws):
                nonlocal data, audio_cursor
                while len(data):
                    i = int(byte_rate * self.realtime_resolution)
                    chunk, data = data[:i], data[i:]
                    await ws.send(chunk)
                    audio_cursor += self.realtime_resolution
                    await asyncio.sleep(self.realtime_resolution)

                await ws.send(json.dumps({"type": "CloseStream"}))

            async def receiver(ws):
                nonlocal audio_cursor
                global transcript
                global interim_transcripts
                global audio_cursor_l
                global confirmed_interim_transcripts
                global confirmed_audio_cursor_l
                global model_timestamps_hypothesis
                global model_timestamps_confirmed
                transcript = ""

                async for msg in ws:
                    msg = json.loads(msg)
                    if "request_id" in msg:
                        continue
                    if msg["channel"]["alternatives"][0]["transcript"] != "":
                        if not msg["is_final"]:
                            audio_cursor_l.append(audio_cursor)
                            model_timestamps_hypothesis.append(msg["channel"]["alternatives"][0]["words"])
                            interim_transcripts.append(
                                transcript + " " + msg["channel"]["alternatives"][0]["transcript"]
                            )
                            logger.debug(
                                "\n" + "Transcription: " + transcript + msg["channel"]["alternatives"][0]["transcript"]
                            )

                        elif msg["is_final"]:
                            confirmed_audio_cursor_l.append(audio_cursor)
                            transcript = transcript + " " + msg["channel"]["alternatives"][0]["transcript"]
                            confirmed_interim_transcripts.append(transcript)
                            model_timestamps_confirmed.append(msg["channel"]["alternatives"][0]["words"])

            await asyncio.gather(sender(ws), receiver(ws))
            return (
                transcript,
                interim_transcripts,
                audio_cursor_l,
                confirmed_interim_transcripts,
                confirmed_audio_cursor_l,
                model_timestamps_hypothesis,
                model_timestamps_confirmed,
            )

    def __call__(self, sample):
        (
            transcript,
            interim_transcripts,
            audio_cursor_l,
            confirmed_interim_transcripts,
            confirmed_audio_cursor_l,
            model_timestamps_hypothesis,
            model_timestamps_confirmed,
        ) = asyncio.get_event_loop().run_until_complete(
            self.run(sample, self.api_key, self.channels, self.sample_width, self.sample_rate)
        )
        return {
            "transcript": transcript,
            "interim_transcripts": interim_transcripts,
            "audio_cursor": audio_cursor_l,
            "confirmed_interim_transcripts": confirmed_interim_transcripts,
            "confirmed_audio_cursor": confirmed_audio_cursor_l,
            "model_timestamps_hypothesis": model_timestamps_hypothesis,
            "model_timestamps_confirmed": model_timestamps_confirmed,
        }


class SubqStreamingPipelineConfig(StreamingTranscriptionConfig):
    sample_rate: int
    channels: int
    sample_width: int
    realtime_resolution: float
    model_version: str = Field(..., description="The model to use for real-time transcription")


@register_pipeline
class SubqStreamingPipeline(Pipeline):
    _config_class = SubqStreamingPipelineConfig
    pipeline_type = PipelineType.STREAMING_TRANSCRIPTION

    def parse_input(self, input_sample: StreamingSample):
        y = input_sample.waveform
        y_int16 = (y * 32767).astype(np.int16)
        audio_data_byte = y_int16.T.tobytes()
        return audio_data_byte

    def parse_output(self, output) -> StreamingTranscriptionOutput:
        model_timestamps_hypothesis = output["model_timestamps_hypothesis"]
        model_timestamps_confirmed = output["model_timestamps_confirmed"]

        if model_timestamps_hypothesis is not None:
            model_timestamps_hypothesis = [
                [{"start": word["start"], "end": word["end"]} for word in interim_result_words]
                for interim_result_words in model_timestamps_hypothesis
                if len(interim_result_words) > 0
            ]

        if model_timestamps_confirmed is not None:
            model_timestamps_confirmed = [
                [{"start": word["start"], "end": word["end"]} for word in interim_result_words]
                for interim_result_words in model_timestamps_confirmed
                if len(interim_result_words) > 0
            ]

        prediction = StreamingTranscript(
            transcript=output["transcript"],
            audio_cursor=[a for a, m in zip(output["audio_cursor"], model_timestamps_hypothesis) if len(m) > 0],
            interim_results=[
                t for t, m in zip(output["interim_transcripts"], model_timestamps_hypothesis) if len(m) > 0
            ],
            confirmed_audio_cursor=[
                a for a, m in zip(output["confirmed_audio_cursor"], model_timestamps_confirmed) if len(m) > 0
            ],
            confirmed_interim_results=[
                t for t, m in zip(output["confirmed_interim_transcripts"], model_timestamps_confirmed) if len(m) > 0
            ],
            model_timestamps_hypothesis=model_timestamps_hypothesis,
            model_timestamps_confirmed=model_timestamps_confirmed,
        )

        return StreamingTranscriptionOutput(prediction=prediction)

    def build_pipeline(self):
        pipeline = SubqStreamingApi(self.config)
        return pipeline
