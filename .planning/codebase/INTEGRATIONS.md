# External Integrations

**Analysis Date:** 2026-02-25

## APIs & External Services

**AI/Generation:**
- Google Gemini - script generation + Gemini TTS in `podcast_generator.py`
  - SDK/Client: `google-genai`
  - Auth: `GEMINI_API_KEY`

**Audio/TTS:**
- Google Cloud Text-to-Speech - fallback TTS in `podcast_generator.py`
  - SDK/Client: `google-cloud-texttospeech`
  - Auth: `GOOGLE_APPLICATION_CREDENTIALS`

**Trends/Discovery:**
- Google Trends - topic research in `podcast_generator.py`
  - SDK/Client: `pytrends`
  - Auth: None (public)
- Google Trends RSS - fallback trend feed in `podcast_generator.py`
  - Endpoint: `https://trends.google.com/trends/trendingsearches/daily/rss?geo=...`

**Audio Assets:**
- Freesound API - background music search/download in `podcast_generator.py`
  - SDK/Client: direct HTTP via `requests`
  - Auth: `FREESOUND_API_KEY`

## Data Storage

**Databases:**
- Not detected

**File Storage:**
- Local filesystem only - outputs in `PODCAST_OUTPUT_DIR`, temp in `PODCAST_TEMP_DIR` from `.env` used in `podcast_generator.py`

**Caching:**
- None

## Authentication & Identity

**Auth Provider:**
- Environment variable–based API keys - loaded with `python-dotenv` in `podcast_generator.py`

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- Console logging via `print()` in `podcast_generator.py`

## CI/CD & Deployment

**Hosting:**
- Not detected (local CLI execution described in `README.md`)

**CI Pipeline:**
- GitHub Actions in `.github/workflows/ci.yml`

## Environment Configuration

**Required env vars:**
- `GEMINI_API_KEY`, `FREESOUND_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`
- `PODCAST_NAME`, `PODCAST_SLOGAN`, `PODCAST_TEMP_DIR`, `PODCAST_OUTPUT_DIR`, `PODCAST_ASSETS_DIR`
- Source of truth in `.env.example` and enforced in `run.sh`/`setup.sh`

**Secrets location:**
- `.env` (present) - not read

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

*Integration audit: 2026-02-25*
