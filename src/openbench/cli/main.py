# For licensing see accompanying LICENSE.md file.
# Copyright (C) 2025 Argmax, Inc. All Rights Reserved.

"""Main CLI entry point for openbench-cli."""

import typer
from dotenv import find_dotenv, load_dotenv

# Load environment variables from a .env file (searches cwd and parents) before
# importing any modules that may read env vars at import time.
load_dotenv(find_dotenv(usecwd=True), override=False)

from openbench.cli.commands import dataset, evaluate, inference, summary  # noqa: E402


app = typer.Typer(
    name="openbench-cli",
    help="OpenBench CLI for benchmarking, currently supports transcription, diarization, diarized-transcripts (aka orchestration) and realtime-transcription",
    add_completion=False,
)

# Add commands to the app
app.add_typer(dataset.app, name="dataset")
app.command()(evaluate)
app.command()(inference)
app.command()(summary)


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
