# Codebase Concerns

**Analysis Date:** 2026-02-25

## Tech Debt

**Monolithic main script:**
- Issue: Multiple responsibilities (env loading, trend lookup, script generation, TTS, audio mixing, video, metadata) in a single file, making changes risky and difficult to test in isolation.
- Files: `podcast_generator.py`
- Impact: High coupling and slow iteration; changes in one area can break unrelated flows.
- Fix approach: Split into modules (e.g., `trends.py`, `script.py`, `tts.py`, `audio.py`, `metadata.py`) and keep a slim CLI entry.

**Import-time env requirements:**
- Issue: Required env vars are read and validated at import time, which makes importing the module impossible without a configured `.env`.
- Files: `podcast_generator.py`
- Impact: Limits testability and reuse; any import without env crashes immediately.
- Fix approach: Move env validation into `__main__` or a configuration loader that is invoked explicitly by the CLI.

**Unpinned dependencies:**
- Issue: Requirements are not version-pinned.
- Files: `requirements.txt`
- Impact: Builds can break on upstream changes; reproducing failures is difficult.
- Fix approach: Pin exact versions and update intentionally (e.g., `google-genai==...`).

## Known Bugs

**Emphasis markup never reaches SSML:**
- Symptoms: Prompts instruct using `*word*` for emphasis, but emphasis is stripped before TTS. SSML emphasis in `_to_ssml` never triggers.
- Files: `utils.py`, `podcast_generator.py`
- Trigger: `_strip_formatting` removes `*...*` in `generate_script`, then `_to_ssml` sees no asterisks.
- Workaround: None in current flow.

**run.sh ignores selected Python binary:**
- Symptoms: Script may fail on systems where `python3` is unavailable but `python3.12` (or custom `PYTHON_BIN`) exists.
- Files: `run.sh`
- Trigger: Execution uses `python3` directly instead of `$PYTHON_BIN`.
- Workaround: Manually run `python3.12 podcast_generator.py`.

## Security Considerations

**Filename/path injection from topic:**
- Risk: `topic` is used directly in filenames with only space replacement; path separators or special characters can create invalid paths or unintended directories.
- Files: `podcast_generator.py`
- Current mitigation: None beyond `replace(' ', '_')`.
- Recommendations: Normalize to a safe slug (whitelist characters, strip path separators, limit length).

**Unsafe temp directory deletion:**
- Risk: `run.sh` deletes all contents of `PODCAST_TEMP_DIR` without safety checks; a misconfigured path could delete important files.
- Files: `run.sh`
- Current mitigation: None.
- Recommendations: Add guardrails (disallow root/empty paths, require temp dir to be within project, confirm directory exists and matches expected pattern).

## Performance Bottlenecks

**In-memory audio looping for long tracks:**
- Problem: `_loop_music_fast` creates a multiplied audio segment before slicing; for long episodes this can be large in memory.
- Files: `podcast_generator.py`
- Cause: `track * reps` duplicates audio in-memory.
- Improvement path: Use chunked concatenation or ffmpeg filter/concat to loop without large memory spikes.

## Fragile Areas

**Network calls without timeouts or retries:**
- Files: `podcast_generator.py`
- Why fragile: `requests.get` calls for Freesound and RSS can hang indefinitely or fail transiently.
- Safe modification: Add request timeouts and retry/backoff logic around external calls.
- Test coverage: None for network failure handling.

**External service dependence without isolation:**
- Files: `podcast_generator.py`
- Why fragile: Gemini, Google Cloud TTS, and Freesound are called directly; failures bubble into runtime errors with limited recovery beyond specific fallbacks.
- Safe modification: Introduce adapters/wrappers with explicit error handling and mocked tests.
- Test coverage: Not covered.

## Scaling Limits

**Not detected**

## Dependencies at Risk

**pytrends (unofficial API):**
- Risk: Frequent 404/429 and API changes.
- Impact: Trend discovery fails and falls back to static topic.
- Migration plan: Add caching, configurable fallback topics, or alternative trend sources.
- Files: `podcast_generator.py`

## Missing Critical Features

**Not detected**

## Test Coverage Gaps

**Core workflow untested:**
- What's not tested: Trend lookup, script generation, TTS chunking, audio mixing, video creation, metadata export.
- Files: `podcast_generator.py`
- Risk: Regressions in production flow go unnoticed.
- Priority: High

**Only utility helpers tested:**
- What's not tested: Integration between utilities and main pipeline.
- Files: `tests/test_utils.py`, `utils.py`
- Risk: Behavior drifts between helpers and pipeline usage.
- Priority: Medium

---

*Concerns audit: 2026-02-25*
