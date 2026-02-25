# Coding Conventions

**Analysis Date:** 2026-02-25

## Naming Patterns

**Files:**
- `snake_case.py` for modules (examples: `podcast_generator.py`, `utils.py`, `tests/test_utils.py`).

**Functions:**
- `snake_case` for functions and methods (examples: `_require_env` in `podcast_generator.py`, `_chunk_text` in `utils.py`).
- Leading underscore for internal helpers (examples: `_to_ssml`, `_search_rss` in `podcast_generator.py`).

**Variables:**
- `snake_case` for locals and instance attributes (examples: `script_content`, `final_audio_path` in `podcast_generator.py`).
- ALL_CAPS for constants loaded from environment (examples: `GEMINI_API_KEY`, `OUTPUT_DIR` in `podcast_generator.py`).

**Types:**
- Type hints on public/non-trivial functions (examples: `_is_rate_limited_error` in `podcast_generator.py`, `_chunk_text` in `utils.py`).
- Use built-in generics when possible (example: `List[str]` in `utils.py`, `Exception | str` in `podcast_generator.py`).

## Code Style

**Formatting:**
- Tool used: ruff (noted in `AGENTS.md`, invoked by `ci.sh`).
- 4-space indentation; no tabs (guidance in `AGENTS.md`).

**Linting:**
- Tool used: ruff (guidance in `AGENTS.md`, CI in `ci.sh`).
- Keep imports explicit; avoid wildcard imports (`AGENTS.md`).

## Import Organization

**Order:**
1. Standard library imports (e.g., `os`, `json`, `subprocess` in `podcast_generator.py`).
2. Third-party imports (e.g., `requests`, `pytrends`, `google.genai`, `pydub` in `podcast_generator.py`).
3. Local imports (e.g., `from utils import _chunk_text` in `podcast_generator.py`).

**Path Aliases:**
- Not detected (imports use relative module names like `utils` in `podcast_generator.py`).

## Error Handling

**Patterns:**
- Fail fast with `RuntimeError` for missing prerequisites (examples: `_require_env` in `podcast_generator.py`, `_require_ffmpeg` in `podcast_generator.py`).
- Catch external API failures and print warning/fallback messages (examples: `research_trends`, `fetch_music`, `_generate_episode_metadata` in `podcast_generator.py`).
- Use defensive checks for empty responses and raise clear errors (example: `_part_to_segment` in `podcast_generator.py`).

## Logging

**Framework:** `print` statements.

**Patterns:**
- Status and warnings printed inline to console (examples across `podcast_generator.py`, such as `print("🔍 1. Analysiere Google Trends...")`).

## Comments

**When to Comment:**
- Section headers and step labels in large flows (examples: numbered section comments in `podcast_generator.py`).
- Short inline comments for tricky logic (example: `_loop_music_fast` in `podcast_generator.py`).

**JSDoc/TSDoc:**
- Not applicable (Python codebase).

## Function Design

**Size:**
- Large workflow methods encapsulate step-by-step operations (examples: `generate_script`, `generate_voice` in `podcast_generator.py`).

**Parameters:**
- Explicit parameters rather than `*args/**kwargs` (examples: `_process_chunk(self, idx, chunk, model_tts, voice_name, max_attempts=3)` in `podcast_generator.py`).

**Return Values:**
- Return explicit data or `None` for search helpers (examples: `_search_rss`, `_try_today` in `podcast_generator.py`).

## Module Design

**Exports:**
- Internal helpers are kept in `utils.py` and imported directly (examples: `_chunk_text`, `_strip_formatting` in `utils.py`, imported in `podcast_generator.py`).

**Barrel Files:**
- Not used.

---

*Convention analysis: 2026-02-25*
