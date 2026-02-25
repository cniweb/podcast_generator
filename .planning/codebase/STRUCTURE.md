# Codebase Structure

**Analysis Date:** 2026-02-25

## Directory Layout

```
podcast_generator/
├── .planning/                # Planning outputs (codebase maps)
│   └── codebase/              # Architecture/stack/quality docs
├── .github/                   # CI workflow and GitHub metadata
├── assets/                    # Cover image and optional audio loops
├── finished_episodes/         # Final output artifacts
├── temp_assets/               # Temporary working files
├── tests/                     # Pytest tests
├── podcast_generator.py       # Main pipeline script
├── utils.py                   # Shared helper functions
├── requirements.txt           # Python dependencies
├── run.sh                     # Runner script
├── setup.sh                   # Setup script
├── ci.sh                      # CI script (lint + tests)
└── README.md                  # Usage and workflow documentation
```

## Directory Purposes

**.planning/codebase/**
- Purpose: Stores architecture/stack/quality/concerns documentation.
- Contains: `CONVENTIONS.md`, `TESTING.md`, `STACK.md`, `INTEGRATIONS.md`, `CONCERNS.md`.
- Key files: `.planning/codebase/STACK.md`, `.planning/codebase/TESTING.md`.

**assets/**
- Purpose: Static assets required for audio/video output.
- Contains: `cover.png` (or `cover.jpg`), optional `background_loop.mp3`.
- Key files: `assets/cover.png`.

**finished_episodes/**
- Purpose: Output artifacts produced by the pipeline.
- Contains: MP3, MP4, transcript, and metadata JSON.
- Key files: `finished_episodes/<topic>.mp3`, `finished_episodes/<topic>_meta.json`.

**temp_assets/**
- Purpose: Temporary working files (cleaned by `run.sh`).
- Contains: Script text, temporary audio chunks, downloaded music.
- Key files: `temp_assets/script.txt`, `temp_assets/voice_raw.mp3`.

**tests/**
- Purpose: Pytest suite for utility functions.
- Contains: `test_utils.py`, `conftest.py`.
- Key files: `tests/test_utils.py`.

## Key File Locations

**Entry Points:**
- `run.sh`: Main runner for end-to-end generation.
- `podcast_generator.py`: Python CLI entry (`__main__`) executing the pipeline.

**Configuration:**
- `requirements.txt`: Python dependencies.
- `.env` (exists; contents not read): Environment configuration consumed by `run.sh` and `podcast_generator.py`.

**Core Logic:**
- `podcast_generator.py`: Pipeline orchestration, external API calls, file generation.
- `utils.py`: Text processing helpers for script cleanup and chunking.

**Testing:**
- `tests/test_utils.py`: Tests for `utils.py` functions.
- `tests/conftest.py`: Ensures project root on import path.

## Naming Conventions

**Files:**
- `snake_case.py` for modules (e.g., `podcast_generator.py`, `test_utils.py`).
- Shell scripts use `*.sh` (e.g., `run.sh`, `setup.sh`).

**Directories:**
- Lowercase with underscores (e.g., `temp_assets/`, `finished_episodes/`).

## Where to Add New Code

**New Feature:**
- Primary code: `podcast_generator.py` (add new pipeline step methods to `PodcastGenerator`).
- Tests: `tests/` for new utility behaviors (follow `tests/test_utils.py`).

**New Component/Module:**
- Implementation: New `*.py` at repo root alongside `utils.py` if it is a reusable helper.

**Utilities:**
- Shared helpers: `utils.py` (pure functions used by `podcast_generator.py`).

## Special Directories

**.planning/**
- Purpose: Planning artifacts used by agent workflows.
- Generated: Yes.
- Committed: Yes (contains docs like `.planning/codebase/STACK.md`).

**.venv/**
- Purpose: Local virtual environment.
- Generated: Yes.
- Committed: No (should remain uncommitted).

---

*Structure analysis: 2026-02-25*
