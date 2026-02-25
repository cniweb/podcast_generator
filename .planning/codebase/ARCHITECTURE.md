# Architecture

**Analysis Date:** 2026-02-25

## Pattern Overview

**Overall:** Single-script pipeline orchestrator with utility module.

**Key Characteristics:**
- Sequential, step-based workflow inside `PodcastGenerator` in `podcast_generator.py`.
- External integrations invoked directly from the pipeline methods in `podcast_generator.py`.
- Small shared helpers isolated in `utils.py` and imported by `podcast_generator.py`.

## Layers

**CLI/Automation Layer:**
- Purpose: Prepare environment, validate `.env`, run the generator.
- Location: `run.sh`, `setup.sh`
- Contains: Shell scripts for setup, dependency installation, environment checks, and execution.
- Depends on: `podcast_generator.py`, `.env` (existence only), `requirements.txt`.
- Used by: Developers/operators invoking `./run.sh` or `./setup.sh`.

**Orchestration Layer:**
- Purpose: End-to-end podcast pipeline coordination.
- Location: `podcast_generator.py`
- Contains: `PodcastGenerator` class, `__main__` entry, pipeline step methods.
- Depends on: `utils.py`, external SDKs (Gemini, Google TTS, pytrends), file system paths.
- Used by: `run.sh` and direct `python podcast_generator.py`.

**Utility Layer:**
- Purpose: Reusable text processing helpers for TTS and formatting cleanup.
- Location: `utils.py`
- Contains: `_chunk_text`, `_strip_formatting`, `_spell_out_abbreviations`.
- Depends on: Standard library only.
- Used by: `podcast_generator.py`.

**Testing Layer:**
- Purpose: Validate helper behavior.
- Location: `tests/`
- Contains: pytest tests for utilities and import setup.
- Depends on: `utils.py`, pytest.
- Used by: `ci.sh` and `pytest` runs.

## Data Flow

**Podcast Generation Pipeline:**

1. **Invocation**: `run.sh` validates `.env`, prepares venv, then runs `podcast_generator.py` via stdin input.
2. **Initialization**: `podcast_generator.py` loads env vars, initializes Gemini client, builds `PodcastGenerator`.
3. **Trend Resolution**: `PodcastGenerator.research_trends()` uses pytrends (and RSS fallback) to refine the topic.
4. **Script Generation**: `PodcastGenerator.generate_script()` calls Gemini text model, strips formatting via `utils.py`, writes transcript to `PODCAST_TEMP_DIR`.
5. **Music Fetch**: `PodcastGenerator.fetch_music()` tries Freesound download or local fallback in `assets/`.
6. **Voice Synthesis**: `PodcastGenerator.generate_voice()` chunks script with `_chunk_text`, uses Gemini TTS; fallback to Google Cloud TTS with SSML.
7. **Audio Mix**: `PodcastGenerator.mix_audio()` overlays voice with music via pydub and exports MP3.
8. **Video Render**: `PodcastGenerator.create_video()` uses ffmpeg to create a still-image video if `assets/cover.png|jpg` exists.
9. **Metadata Output**: `PodcastGenerator.generate_metadata()` writes transcript and JSON metadata to `PODCAST_OUTPUT_DIR`.

**State Management:**
- State is instance-based in `PodcastGenerator` (`self.topic`, `self.script_content`, paths) in `podcast_generator.py`.
- Pipeline persists intermediate files in `PODCAST_TEMP_DIR` and final outputs in `PODCAST_OUTPUT_DIR`.

## Key Abstractions

**PodcastGenerator:**
- Purpose: Encapsulates end-to-end production steps as methods.
- Examples: `podcast_generator.py` (`PodcastGenerator.generate_script`, `PodcastGenerator.generate_voice`, `PodcastGenerator.mix_audio`).
- Pattern: Stateful pipeline object with sequential step methods.

**Text Preprocessing Helpers:**
- Purpose: Normalize script text for TTS and readability.
- Examples: `utils.py` (`_chunk_text`, `_strip_formatting`, `_spell_out_abbreviations`).
- Pattern: Pure functions called by `PodcastGenerator.generate_script` and `PodcastGenerator.generate_voice`.

## Entry Points

**Shell Runner:**
- Location: `run.sh`
- Triggers: User invocation `./run.sh "<topic>"`.
- Responsibilities: Validate env, ensure venv and dependencies, clean temp dir, launch Python script.

**Python Main:**
- Location: `podcast_generator.py` (`if __name__ == "__main__":`)
- Triggers: Direct `python podcast_generator.py` or piped input from `run.sh`.
- Responsibilities: Prompt for topic, resolve trends (DACH), run pipeline steps in order.

## Error Handling

**Strategy:** Fail fast for missing required env, graceful fallbacks for external API failures.

**Patterns:**
- Required env validation in `_require_env` at import time in `podcast_generator.py`.
- External API calls wrapped with try/except and fallback behaviors in `podcast_generator.py` (e.g., trends RSS fallback, TTS fallback).

## Cross-Cutting Concerns

**Logging:** Print statements throughout `podcast_generator.py` for step progress and warnings.
**Validation:** Env presence and tool availability checks in `run.sh`, `setup.sh`, and `_require_env` in `podcast_generator.py`.
**Authentication:** External credentials via environment variables loaded in `podcast_generator.py`.

---

*Architecture analysis: 2026-02-25*
