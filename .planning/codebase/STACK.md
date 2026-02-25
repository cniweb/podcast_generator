# Technology Stack

**Analysis Date:** 2026-02-25

## Languages

**Primary:**
- Python 3.12+ - Core application in `podcast_generator.py`, helpers in `utils.py`, tests in `tests/`

**Secondary:**
- Bash - Automation scripts in `run.sh`, `setup.sh`, `ci.sh`

## Runtime

**Environment:**
- Python 3.12+ (recommended) - documented in `README.md` and enforced in `run.sh`
- Python 3.13 in CI - configured in `.github/workflows/ci.yml`

**Package Manager:**
- pip - requirements in `requirements.txt`
- Lockfile: missing

## Frameworks

**Core:**
- None (standalone Python script) - entrypoint `podcast_generator.py`

**Testing:**
- pytest - unit tests in `tests/test_utils.py`

**Build/Dev:**
- ruff 0.6.8 - linting in `ci.sh` and `.github/workflows/ci.yml`
- pymarkdownlnt - markdown linting in `ci.sh`

## Key Dependencies

**Critical:**
- `google-genai` - Gemini text + audio generation in `podcast_generator.py`
- `google-cloud-texttospeech` - Google Cloud TTS fallback in `podcast_generator.py`
- `pytrends` - Google Trends data in `podcast_generator.py`
- `pydub` - audio composition in `podcast_generator.py`
- `requests` - HTTP calls to external APIs and RSS in `podcast_generator.py`

**Infrastructure:**
- `python-dotenv` - environment loading in `podcast_generator.py`
- `audioop-lts` - audioop compatibility for Python 3.12+ noted in `README.md` and `run.sh`

## Configuration

**Environment:**
- `.env` loaded via `dotenv.load_dotenv()` in `podcast_generator.py`
- Template in `.env.example` with required keys

**Build:**
- CI pipeline in `.github/workflows/ci.yml`
- Local CI script in `ci.sh`

## Platform Requirements

**Development:**
- ffmpeg + ffprobe required for audio/video in `podcast_generator.py` and `setup.sh`
- Python 3.12+ and a virtualenv created by `run.sh`

**Production:**
- Local CLI execution via `run.sh` or `python podcast_generator.py` as documented in `README.md`

---

*Stack analysis: 2026-02-25*
