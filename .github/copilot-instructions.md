# copilot-instructions

## Build, test, and lint commands

- Install deps: `python -m pip install -r requirements.txt`
- Lint (same target as CI): `python -m ruff check podcast_generator.py utils.py tests/`
- Compile/syntax check: `python -m compileall podcast_generator.py utils.py`
- Full test suite: `python -m pytest -q`
- Single test: `python -m pytest -q tests/test_utils.py::test_chunk_text_splits_long_paragraph`
- Markdown lint: `python -m pymarkdown scan .`
- Combined local CI flow: `./ci.sh`
- End-to-end run: `./run.sh "Dein Thema"`

## High-level architecture

- Main module: `podcast_generator.py` contains configuration loading, Gemini client setup, and the full generation pipeline.
- Helper utilities: `utils.py` provides text processing functions (chunking, formatting, validation).
- Runtime flow is orchestrated by `PodcastGenerator` in seven steps:
  1. `research_trends()` (Google Trends via `pytrends`, DACH focus with RSS fallback)
  2. `generate_script()` (Gemini text model for spoken-word script)
  3. `fetch_music()` (Freesound API for background music, fallback to silence)
  4. `generate_voice()` (Gemini TTS in chunks, Google Cloud TTS as SSML fallback)
  5. `mix_audio()` (pydub mixing of voice + music, MP3 export)
  6. `create_video()` (ffmpeg still-image video from cover + audio)
  7. `generate_metadata()` (Gemini text model to JSON metadata)
- Config is loaded from `.env` via `python-dotenv` at module level.
- Required env vars: `GEMINI_API_KEY`, `FREESOUND_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `PODCAST_NAME`, `PODCAST_SLOGAN`, `SCRIPT_DEFAULT_MODEL`, `PODCAST_TEMP_DIR`, `PODCAST_OUTPUT_DIR`, `PODCAST_ASSETS_DIR`.
- File outputs are written to `PODCAST_OUTPUT_DIR` with stable naming based on slugified topic:
  - `<topic>.mp3` (final audio)
  - `<topic>_video.mp4` (optional)
  - `<topic>_transcription.txt`
  - `<topic>_meta.json`
  - `<topic>_run.json` (run manifest)
- Shell scripts:
  - `setup.sh`: env/dependency/ffmpeg bootstrap
  - `run.sh`: standard execution entrypoint with `--resume` and `--force-restart` flags
  - `ci.sh`: local lint/import/syntax/tests/markdown-lint sequence aligned with `.github/workflows/ci.yml`

## Key repository conventions

- User-visible content is German by default (scripts, titles, descriptions, console messages).
- Script output is spoken text only: no stage directions, sound cues, or screenplay markup.
- Pipeline scope is knowledge/education podcasts (not product videos).
- Do not introduce new external dependencies without clear justification.
- Preserve `.env`-driven config; never hardcode secrets.
- Trend focus should stay DACH-oriented (DE, AT, CH) with existing fallback chain.
- Prefer resilient behavior for upstream API issues (retry logic, fallback models, fallback music).
- Do not remove or overwrite user assets in `assets/` (cover images, optional loops).
- Tests use a partial-module-loading pattern via `exec()` to avoid triggering env validation at import time.
