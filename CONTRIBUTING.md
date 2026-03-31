# Beitragen zu podcast_generator

Vielen Dank fuer deinen Beitrag.

## Voraussetzungen

- Python 3.12+ (wegen audioop-Kompatibilitaet)
- ffmpeg inkl. ffprobe im PATH
- Eine konfigurierte `.env`-Datei im Repository-Root

Erforderliche `.env`-Variablen:

- `GEMINI_API_KEY`
- `FREESOUND_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `PODCAST_NAME`
- `PODCAST_SLOGAN`
- `SCRIPT_DEFAULT_MODEL`
- `PODCAST_TEMP_DIR`
- `PODCAST_OUTPUT_DIR`
- `PODCAST_ASSETS_DIR`

Optionale Einstellungen:

- `TTS_DEFAULT_MODEL`
- `TTS_FALLBACK_MODELS`
- `TTS_VOICE_NAME`
- `GENERATE_VIDEO`

## Lokales Setup

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows
source .venv/bin/activate       # macOS/Linux
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Oder nutze:

```bash
./setup.sh
```

## Lokal ausfuehren

```bash
./run.sh "Dein Thema"
./run.sh --resume "Dein Thema"
./run.sh --force-restart "Dein Thema"
```

Ohne explizites Thema (Trend-Fallback):

```bash
./run.sh
```

## Lint, Kompilieren und Tests

Nutze dieselben Checks wie in CI:

```bash
python -m ruff check podcast_generator.py utils.py tests/
python -m compileall podcast_generator.py utils.py
python -m pytest -q
python -m pymarkdown scan .
```

Einen einzelnen Test ausfuehren:

```bash
python -m pytest -q tests/test_utils.py::test_chunk_text_splits_long_paragraph
```

Oder den kombinierten lokalen Ablauf:

```bash
./ci.sh
```

## Repository-spezifische Konventionen

- Nutzerseitiger Text bleibt auf Deutsch (Skripte, Titel, Beschreibungen).
- Skript-Output ist reiner Sprechtext, keine Regieanweisungen oder Sound-Cues.
- Trendverhalten bleibt DACH-fokussiert (DE, AT, CH) mit Fallback-Kette.
- Konfiguration bleibt `.env`-getrieben; Secrets werden nie hardcodiert.
- Bevorzuge robuste Fallbacks bei externen API-Problemen.
- Keine Assets in `assets/` ueberschreiben oder loeschen.

## Pull-Request-Checkliste

Vor dem Oeffnen eines PRs:

1. Lint + Tests lokal ausfuehren (`./ci.sh`).
1. Aenderungen minimal und auf das Thema begrenzen.
1. Doku aktualisieren, wenn Verhalten, Kommandos oder Konfiguration angepasst wurden.
1. Eine klare Zusammenfassung geben, was geaendert wurde und wie es validiert wurde.
