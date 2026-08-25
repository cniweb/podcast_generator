# Repository Instructions

## Scope and Flow

- This is a Python 3.12+ CLI that creates German podcasts: trends -> Gemini script -> Freesound music -> Gemini TTS/Google Cloud TTS fallback -> `pydub` mixing -> optional FFmpeg video -> metadata.
- Main code is `podcast_generator.py`; shared helpers are in `utils.py`; tests are in `tests/`.
- Required `.env` keys are `GEMINI_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `FREESOUND_API_KEY`, `PODCAST_NAME`, `PODCAST_SLOGAN`, `SCRIPT_DEFAULT_MODEL`, `PODCAST_TEMP_DIR`, `PODCAST_OUTPUT_DIR`, and `PODCAST_ASSETS_DIR`. TTS model/voice and video generation are optional.
- Trends are DACH-focused and must retain fallback behavior. User-facing and generated content is German by default.

## Commands

- `./setup.sh` validates `.env`/FFmpeg and installs requirements.
- `./run.sh "<Thema>"`, `./run.sh ""`, `./run.sh --resume "<Thema>"`, and `./run.sh --force-restart "<Thema>"` run or resume generation.
- `./ci.sh` creates/uses `.venv`, installs dependencies and `ruff==0.6.8`, then runs Ruff, imports, compileall, pytest, coverage, pip-audit, and Markdown linting.
- Direct checks: `python -m ruff check podcast_generator.py utils.py tests/`, `python -m compileall podcast_generator.py utils.py`, `python -m pytest -q`, and `python -m pymarkdown -c .pymarkdown.toml scan .`.
- Focused examples: `python -m pytest tests/test_utils.py -k "chunk_text"` and `python -m pytest tests/test_utils.py::test_chunk_text_splits_long_paragraph`.

## Data-Safety Gotchas

- A normal run clears the configured temporary and output directories before generating. `--force-restart` also discards existing run data. Never use either against unsaved output.
- Outputs include MP3, optional MP4, transcript, metadata, and `<topic>_run.json`; checkpoints and intermediate artifacts live in `PODCAST_TEMP_DIR`.
- Do not remove or overwrite user assets in `assets/`, and never commit `.env` or `google_cloud_credentials.json`.
- The main module validates configuration and initializes dependencies at import time. Tests intentionally load it partially through `tests/conftest.py`; preserve that bootstrap.

## Change and Test Rules

- Preserve script constraints, output naming, checkpoint/resume semantics, and fallback paths unless the task explicitly changes product behavior.
- Keep external-service tests deterministic and offline; use existing stubs/fixtures. Add focused regression tests for changes to helpers, CLI, checkpoints, or output QA.
- Keep diffs targeted and read `.github/copilot-instructions.md` before changing prompts or generated output.
