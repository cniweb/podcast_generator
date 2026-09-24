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

## Lessons Learned

- Append durable, repo-specific lessons here as single bullets (cause + fix); merge duplicates and keep this section short so the file keeps improving instead of growing stale.
- After editing `AGENTS.md`, run `python -m pymarkdown -c .pymarkdown.toml scan AGENTS.md` — the file must stay lint-clean (`ci.sh` and CI scan the whole repo, only line-length is disabled).
- Push rejected after a remote PR merge landed: stash local edits, `git pull --rebase`, resolve conflicts, pop the stash, push again.
- Upstream doc rewrites vs local appends (e.g. tooling blocks): resolve by union — keep the upstream rewrite, re-append the local block, then re-lint (watch MD025 single-H1).

<!-- gitnexus:start -->

## GitNexus — Code Intelligence

This project is indexed by GitNexus as **podcast_generator** (736 symbols, 1312 relationships, 47 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/podcast_generator/context` | Codebase overview, check index freshness |
| `gitnexus://repo/podcast_generator/clusters` | All functional areas |
| `gitnexus://repo/podcast_generator/processes` | All execution flows |
| `gitnexus://repo/podcast_generator/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
