# Stack Research

**Domain:** CLI podcast generation (script + TTS + audio mixing)
**Researched:** 2026-02-25
**Confidence:** MEDIUM

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12.x | Orchestrates pipeline and CLI | Stable for audio/AI tooling, broad ecosystem, good packaging and scripting for local CLI tools. |
| FFmpeg | 8.0.1 | Audio processing (normalize, mix, encode) | De-facto standard for audio/video pipelines; reliable CLI and filters. |
| Typer | 0.24.1 | CLI framework | Modern, type-hinted CLI with good UX and docs; built on Click. |
| OpenAI SDK | 2.24.0 | Script generation LLM client | Current official SDK; supports structured responses and streaming. |
| Google GenAI SDK | 1.64.0 | Alternative LLM client | Official Google SDK; useful for fallback or model diversity. |
| ElevenLabs SDK | 2.36.1 | TTS client | High-quality TTS with stable SDK and voice controls. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | 1.2.1 | Load .env config | Local CLI runs with many secrets and paths. |
| httpx | 0.28.1 | HTTP client | When direct REST calls are needed beyond SDK coverage. |
| soundfile | 0.13.1 | WAV/FLAC I/O | Inspect or manipulate audio without spawning ffmpeg. |
| PyAV (av) | 16.1.0 | FFmpeg bindings | When in-process decode/encode is needed, or for tighter control than shelling out. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| ruff | Lint + format | Fast, one tool for style and correctness. |
| pytest | Testing | Standard Python testing with good plugins. |

## Installation

```bash
# Core
python -m pip install "typer==0.24.1" "openai==2.24.0" "google-genai==1.64.0" "elevenlabs==2.36.1"

# Supporting
python -m pip install "python-dotenv==1.2.1" "httpx==0.28.1" "soundfile==0.13.1" "av==16.1.0"

# Dev dependencies
python -m pip install "ruff==0.15.2" "pytest==9.0.2"
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Typer | Click | When you need minimal deps or already have a Click-based CLI. |
| FFmpeg CLI | PyAV | When you need in-process transforms or frame-accurate editing. |
| ElevenLabs | Google Cloud TTS or Azure TTS | When you need enterprise SLAs, regional compliance, or specific voices not in ElevenLabs. |
| OpenAI SDK | Anthropic SDK | If your scripting models are on Anthropic or you need their safety/cost profile. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| pydub 0.25.1 | Unmaintained and old; depends on ffmpeg with limited control and weak error reporting. | FFmpeg CLI or PyAV. |
| ffmpeg-python 0.2.0 | Very old, minimal updates, can lag behind FFmpeg features. | Direct FFmpeg CLI or PyAV. |
| gTTS | Limited voices and quality; rate limits; not suitable for production-grade TTS. | ElevenLabs or cloud TTS services. |

## Stack Patterns by Variant

**If you only need offline editing and have pre-recorded audio:**
- Use FFmpeg + soundfile only
- Because you can avoid any AI dependencies and keep installs light

**If you need multi-provider LLM fallback:**
- Use OpenAI SDK + Google GenAI SDK
- Because you can switch providers without changing orchestration logic

**If you need fine-grained audio transforms in Python:**
- Use PyAV in addition to FFmpeg CLI
- Because PyAV enables in-process control while keeping FFmpeg compatibility

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| av 16.1.0 | FFmpeg 8.0.1 | PyAV bundles FFmpeg bindings; verify your system FFmpeg if mixing CLI + PyAV. |
| soundfile 0.13.1 | libsndfile 1.2+ | Requires libsndfile on some platforms; Windows wheels usually include it. |

## Sources

- https://www.python.org/downloads/ — Python 3.14.3 listed as latest; 3.12/3.13 active (MEDIUM)
- https://ffmpeg.org/download.html — FFmpeg 8.0.1 stable release info (MEDIUM)
- https://pypi.org/project/typer/ — version 0.24.1 (MEDIUM)
- https://pypi.org/project/openai/ — version 2.24.0 (MEDIUM)
- https://pypi.org/project/google-genai/ — version 1.64.0 (MEDIUM)
- https://pypi.org/project/elevenlabs/ — version 2.36.1 (MEDIUM)
- https://pypi.org/project/python-dotenv/ — version 1.2.1 (MEDIUM)
- https://pypi.org/project/httpx/ — version 0.28.1 (MEDIUM)
- https://pypi.org/project/soundfile/ — version 0.13.1 (MEDIUM)
- https://pypi.org/project/av/ — version 16.1.0 (MEDIUM)
- https://pypi.org/project/ruff/ — version 0.15.2 (MEDIUM)
- https://pypi.org/project/pytest/ — version 9.0.2 (MEDIUM)

---
*Stack research for: CLI podcast generation*
*Researched: 2026-02-25*
