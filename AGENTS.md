# AGENTS.md

This guide is for agentic coding assistants working in this repository.
It captures build/test commands, style rules, and repo-specific safety constraints.

## Source Of Truth

- Primary docs: `README.md`.
- Execution scripts: `run.sh`, `setup.sh`, `ci.sh`.
- CI behavior: `.github/workflows/ci.yml`.
- Core code: `podcast_generator.py`, helper utilities in `utils.py`, tests in `tests/`.

## Workspace And Platform Notes

- Run commands from repository root.
- On Windows, run shell scripts via Git Bash or WSL.
- Python 3.12+ is expected locally (audioop compatibility note in scripts).
- Repo currently contains `.venv`; prefer using it instead of global Python.
- `run.sh` uses `.venv/bin/activate` (Unix path style).
- `ci.sh` uses `.venv/Scripts/activate` (Windows path style).
- If activation path fails on your platform, run equivalent commands manually.

## Build, Lint, And Test Commands

Setup and dependency install:
- `./setup.sh`
  - Validates `.env` keys.
  - Checks `ffmpeg` availability.
  - Installs `requirements.txt`.

End-to-end podcast run:
- `./run.sh "<Thema>"`
- `./run.sh ""` (empty topic -> trend-based topic selection)

Project CI checks:
- `./ci.sh`
  - Creates/uses `.venv`.
  - Installs dependencies + `ruff==0.6.8`.
  - Runs ruff, import sanity check, compileall, pytest, markdown lint.
- GitHub Actions status after push:
  - After every `git push`, check the latest GitHub Actions run for `main` via `gh run list --limit 5 --branch main`.
  - If the pushed commit's CI run is still in progress, inspect it again until it completes or clearly report that it is still running.
  - If the CI run fails, inspect details with `gh run view <run-id>` (and job logs as needed), attempt a targeted fix locally, rerun relevant local validation, commit the fix, push again, and re-check GitHub Actions until the build is green or you are blocked.
  - When reporting back after a push, include whether the GitHub Actions build passed, failed, or is still running.

Optional CI with setup checks:
- `./ci.sh --setup`

Direct lint commands:
- `python -m ruff check podcast_generator.py`
- `python -m ruff check --fix podcast_generator.py`

Syntax-only check:
- `python -m compileall podcast_generator.py`

Run all tests:
- `python -m pytest -q`

Single test file (important):
- `python -m pytest tests/test_utils.py`
- `python -m pytest tests/test_script_constraints.py`

Single test by expression (important):
- `python -m pytest tests/test_utils.py -k "chunk_text"`

Single test by node id (important):
- `python -m pytest tests/test_utils.py::test_chunk_text_splits_long_paragraph`
- `python -m pytest tests/test_script_constraints.py::test_validate_script_constraints_success_case`

Verbose failure output when debugging:
- `python -m pytest -vv tests/test_utils.py -k "spell_out"`

Markdown lint (used in `ci.sh`):
- `python -m pymarkdown scan .`

Dependency import sanity snippet:
- `python - <<'PY'`
- `import importlib`
- `deps = ['google.genai', 'pytrends', 'pydub', 'requests', 'dotenv']`
- `for dep in deps: importlib.import_module(dep)`
- `PY`

## Environment And Secrets

- Never hardcode credentials; load from `.env`.
- Required `.env` keys:
  - `GEMINI_API_KEY`
  - `FREESOUND_API_KEY`
  - `GOOGLE_APPLICATION_CREDENTIALS`
  - `PODCAST_NAME`
  - `PODCAST_SLOGAN`
  - `PODCAST_TEMP_DIR`
  - `PODCAST_OUTPUT_DIR`
  - `PODCAST_ASSETS_DIR`
- Do not commit `.env` or credential files.
- Missing required env vars should fail fast with clear `RuntimeError`.

## Language And Output Constraints

- User-facing copy and generated script content are German by default.
- Script output should be spoken text only.
- Do not output stage directions, sound cues, or screenplay markup.
- Trend focus is DACH (DE, AT, CH) with fallback topic behavior.

## Code Style Guidelines

General:
- Keep diffs small, focused, and minimal risk.
- Preserve established workflow and filenames.
- Prefer explicit logic over clever compact rewrites.

Imports:
- Order: standard library, third-party, local imports.
- Avoid wildcard imports.
- Keep local helper imports explicit (e.g., from `utils` import specific functions).

Formatting:
- Follow ruff expectations (`ruff check`).
- 4-space indentation; no tabs.
- Use readable line lengths and wrap long expressions cleanly.
- Prefer f-strings for interpolation.

Types:
- Add type hints for public/non-trivial functions.
- Prefer modern built-in generics (`list[str]`, `dict[str, str]`).
- Use explicit unions where needed (`str | None`).

Naming:
- `snake_case` for functions, methods, variables.
- `_leading_underscore` for internal helpers.
- `ALL_CAPS` for module-level constants.
- `CapWords` for classes (e.g., `PodcastGenerator`).

Error handling:
- Fail fast for required prerequisites (missing env vars, missing tools).
- For recoverable external failures, log warning and use fallback path.
- Error messages should be actionable and specific.

I/O and paths:
- Use `os.makedirs(..., exist_ok=True)` for required directories.
- Keep outputs under configured `PODCAST_*` directories.
- Clean temp artifacts only; do not wipe output history.
- Keep naming conventions stable (`<topic>.mp3`, `<topic>_video.mp4`, etc.).

## Testing Expectations

- Test framework: `pytest`.
- Tests reside in `tests/`.
- `tests/conftest.py` adjusts import path for local modules.
- Add/adjust tests when changing text cleanup, chunking, or validation logic in `utils.py`.
- For bug fixes, prefer adding a focused regression test.

## Repository-Specific Guardrails

- Do not remove or overwrite user assets in `assets/` (cover images, optional loops).
- Preserve DACH trend lookup and fallback chain behavior.
- Keep script-constraint enforcement intact unless task explicitly changes product behavior.
- Maintain compatibility with existing shell scripts and CI checks.

## Cursor/Copilot Rules

- No Cursor rules were found (`.cursor/rules/` and `.cursorrules` absent).
- No Copilot instruction file was found (`.github/copilot-instructions.md` absent).
- If these files are added later, treat them as additional mandatory instructions.

## Agent Operating Guidelines

- Read relevant code before making behavior changes.
- Prefer targeted edits over broad refactors.
- Do not commit secrets, generated credentials, or local environment files.
- Avoid destructive git operations (`reset --hard`, `checkout --`) unless explicitly requested.
- If uncertain about behavior changes affecting output quality, ask for clarification.
