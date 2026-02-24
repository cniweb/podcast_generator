# AGENTS.md

This guide is for agentic coding assistants working in this repo. It summarizes how
to build, test, and follow existing code style and project rules.

## Source Of Truth

- README contains the main workflow and user instructions.
- Shell scripts: run.sh, setup.sh, ci.sh.
- This file merges the above with local conventions in the codebase.

## Build, Lint, Test

General notes:
- Prefer running commands from repo root.
- Use Git Bash or WSL on Windows for .sh scripts.
- Python 3.12+ is expected (audioop behavior).

Setup:
- ./setup.sh
  - Validates .env and installs Python requirements.
  - Checks for ffmpeg/ffprobe.

End-to-end run:
- ./run.sh "<topic>"
  - Use empty topic for trend-based topic selection.
  - Cleans temp dir, keeps outputs.

CI checks (lint + tests):
- ./ci.sh
  - Installs ruff, runs ruff check, compileall, pytest.

Optional CI setup (requires .env):
- ./ci.sh --setup

Single test file:
- python -m pytest tests/test_utils.py

Single test by name:
- python -m pytest tests/test_utils.py -k "test_chunk_text"

Single test (node id style):
- python -m pytest tests/test_utils.py::test_chunk_text_splits_long_paragraph

Quick lint (ruff):
- python -m ruff check podcast_generator.py

Auto-fix lint (ruff):
- python -m ruff check --fix podcast_generator.py

Syntax check only:
- python -m compileall podcast_generator.py

Import check (deps):
- python - <<'PY'
import importlib
deps = ['google.genai','pytrends','pydub','requests','dotenv']
for dep in deps:
    importlib.import_module(dep)
PY

## Environment And Secrets

- Never hardcode secrets. Use .env.
- Required .env keys:
  - GEMINI_API_KEY, FREESOUND_API_KEY, GOOGLE_APPLICATION_CREDENTIALS
  - PODCAST_NAME, PODCAST_SLOGAN
  - PODCAST_TEMP_DIR, PODCAST_OUTPUT_DIR, PODCAST_ASSETS_DIR
- Do not commit .env or credentials files.

## Language And Output Rules

- User-facing text is German by default.
- Generated podcast script should be spoken text only. No stage/sound cues.
- Trend focus: DACH (DE, AT, CH). If trends fail, fall back to static topic.

## Code Style Guidelines

General:
- Keep diffs minimal and focused.
- Avoid deleting user assets (assets/cover.png, assets/cover.jpg, loops).
- Keep paths under PODCAST_* dirs stable.
- Prefer logging warnings for recoverable errors rather than aborting.

Imports:
- Standard library imports at top, then third-party, then local.
- Keep imports explicit; avoid wildcard imports.
- Local helpers live in utils.py and are imported directly.

Formatting:
- The repo uses ruff for linting; follow ruff defaults.
- 4-space indentation, no tabs.
- Use f-strings for string formatting where practical.
- Keep lines readable; wrap long strings with parentheses.

Types:
- Use type hints for public helpers and non-trivial functions.
- Prefer built-in generics (list[str], dict[str, str]) where supported.
- When a function accepts multiple types, be explicit (e.g., str | None).

Naming:
- snake_case for functions/variables.
- Leading underscore for internal helpers (_require_env).
- Constants in ALL_CAPS.
- Classes use CapWords (PodcastGenerator).

Error Handling:
- Validate required env vars early and fail fast with clear RuntimeError.
- For external API calls, catch exceptions and log warnings; use safe fallback.
- Provide actionable error messages (missing ffmpeg, missing .env keys).

I/O And Paths:
- Use os.makedirs(..., exist_ok=True) for required folders.
- Do not delete output dir content; only clean temp dir.
- Maintain output naming conventions (<topic>.mp3, <topic>_video.mp4, etc.).

Testing:
- Tests live in tests/ and use pytest.
- conftest.py adjusts sys.path to import local modules.
- Add tests for text utilities in utils.py.

## Repository-Specific Rules

- Use .env values; never hardcode API keys or creds.
- Avoid stage directions in generated scripts.
- Keep trend logic to DACH focus with fallback.
- When unsure about a behavior change that affects output quality, ask user.

## Agent Behavior

- Read existing code before changing behavior.
- Prefer small, targeted edits and document rationale in PR/commit message.
- Avoid destructive git commands (reset --hard, checkout --).
