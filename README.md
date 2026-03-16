# Podcast Generator

## Schnellstart (für neue Nutzer)

1. Voraussetzungen prüfen
   - Python 3.12+ und ffmpeg (inkl. ffprobe) im PATH
2. Setup ausführen
   - `./setup.sh`
3. Podcast erzeugen
   - `./run.sh "Dein Thema"`
   - leer lassen, um Trends automatisch zu verwenden

Ausgaben findest du in `PODCAST_OUTPUT_DIR`.
Audio, optionales Video, Transkript und Metadaten liegen dort.

## Hinweis für Windows

- `run.sh`/`setup.sh` am besten in Git Bash oder WSL ausführen
- ffmpeg manuell installieren und PATH setzen
- alternativ `podcast_generator.py` direkt mit Python starten

## Zweck

- Erstellt automatisch kurze Wissens-Podcasts.
- Enthalten: Audio, optionales Standbild-Video, Skript, TTS-Voice,
  Hintergrundmusik und Metadaten.
- Nutzt aktuelle Trends (Google Trends) für Themenanreicherung.
- Verwendet Gemini für Skript- und Voice-Generierung.
- Nutzt Freesound für lizenzfreie Musik-Snippets.

## Architektur & Ablauf

1. `run.sh "<Thema>"`
   - Lädt `.env`.
   - Prüft Pflicht-Variablen.
   - Bereinigt Arbeitsordner.
   - Aktiviert venv und startet `podcast_generator.py`.
2. `setup.sh`
   - Optionaler Helfer.
   - Prüft `.env`, FFmpeg und Python.
   - Installiert Requirements.
3. `podcast_generator.py`
   - Trends: holt Top-Query via Google Trends (pytrends) mit Fokus DACH (DE/AT/CH).
     Fällt bei Fehlschlag auf statisches Thema zurück.
   - Skript: Gemini-Textmodell generiert deutschen Sprechtext.
     Säubert Formatierung, entfernt Regie-/Sound-Anweisungen, speichert Transkript.
   - Stimme: Gemini TTS (`gemini-2.5-pro-preview-tts`, Stimme konfigurierbar)
     generiert Audio in Chunks.
     Fügt per pydub zusammen.
   - Musik: sucht Freesound nach „podcast background `topic` instrumental“.
     Fällt auf „lofi study loop“ zurück, sonst Stille.
   - Mixing: Sprachspur mit geloopter Musik unterlegt, Export als MP3.
     Video mit FFmpeg als Standbild + Audio.
   - Metadaten: JSON + Transkript-Text im Output-Ordner.

## Verwendete APIs / Tools

- Google Gemini (Text + TTS) über `google-genai` Client.
- Freesound API für Hintergrundmusik.
- Google Trends via `pytrends`.
- pydub + ffmpeg für Audio, ffmpeg für Video.

## Voraussetzungen

- ffmpeg inkl. ffprobe im PATH (Windows/macOS/Linux)
- Python 3.12+ empfohlen (wegen audioop)
- venv wird von `run.sh`/`setup.sh` angelegt
- `.env` mit allen Pflichtwerten

## .env Beispiel (Pflichtfelder + optionale Schalter)

```bash
GEMINI_API_KEY=dein_gemini_key
FREESOUND_API_KEY=dein_freesound_key
GOOGLE_APPLICATION_CREDENTIALS=google_cloud_credentials.json

PODCAST_NAME="Mein Podcast"
PODCAST_SLOGAN="Alles, was man wissen muss..."
SCRIPT_DEFAULT_MODEL=gemini-3.1-pro-preview
TTS_DEFAULT_MODEL=gemini-2.5-pro-preview-tts
TTS_FALLBACK_MODELS=gemini-2.5-flash-preview-tts
TTS_VOICE_NAME=umbriel
GENERATE_VIDEO=true
PODCAST_TEMP_DIR=temp_assets
PODCAST_OUTPUT_DIR=finished_episodes
PODCAST_ASSETS_DIR=assets
```

## Nutzung

```bash
chmod +x run.sh setup.sh
./setup.sh                            # einmalig, prüft .env/ffmpeg/requirements
./run.sh "Regieassistenz im Theater"  # erzeugt Audio/Video/Transkript/Metadaten
./run.sh --resume "Regieassistenz im Theater"  # setzt einen abgebrochenen Lauf fort
./run.sh --force-restart "Regieassistenz im Theater"  # ignoriert vorhandene Checkpoints
```

Windows (PowerShell, ohne Bash):

```powershell
python .\podcast_generator.py
```

Ausgaben:

- Audio: `<PODCAST_OUTPUT_DIR>/<Thema>.mp3`
- Video (optional): `<PODCAST_OUTPUT_DIR>/<Thema>_video.mp4` (falls `GENERATE_VIDEO=true` und Cover im Assets-Ordner vorhanden)
- Transkript: `<PODCAST_OUTPUT_DIR>/<Thema>_transcription.txt`
- Metadaten: `<PODCAST_OUTPUT_DIR>/<Thema>_meta.json`
- Run-Manifest: `<PODCAST_OUTPUT_DIR>/<Thema>_run.json`

## Konfiguration

- TTS per `.env`: `TTS_DEFAULT_MODEL`, `TTS_FALLBACK_MODELS`, `TTS_VOICE_NAME`.
- Video-Schritt optional per `.env`: `GENERATE_VIDEO=true|false` (Default: `true`).
- Unterbrechungen: Der Generator schreibt einen Checkpoint in `temp_assets/` und setzt beim nächsten Start mit gleichem Thema ab bereits abgeschlossenen Schritten fort.
- Resume-Steuerung: `--resume` setzt Checkpoints bewusst fort, `--force-restart` verwirft sie und startet sauber neu.
- Vor Abschluss prueft eine Output-QA, ob Audio, Metadaten, Transkript und optional das Video wirklich erzeugt wurden.
- Cover-Bild: `assets/cover.png` oder `assets/cover.jpg`.
- Musik-Query-Fallbacks: zuerst themenbezogen, dann „lofi study loop“, sonst Stille.

## Fehlerbehebung

- Fehler `Environment variable ... is required`: .env prüfen und Wert setzen.
- ffmpeg nicht gefunden: ffmpeg installieren und PATH prüfen.
  Danach `setup.sh` erneut ausführen.
- `audioop` fehlt: `run.sh` installiert `audioop-lts` über requirements.
  Sicherstellen, dass Python 3.12+ genutzt wird.

## Entwickler-Onboarding (Contributor)

### Repository vorbereiten

1. Abhängigkeiten installieren
   - `./setup.sh` (legt venv an, installiert Requirements)
2. Tests ausführen
   - `./ci.sh`

### Wichtige Ordner

- `assets/` – Cover und optionale Hintergrundloops
- `temp_assets/` – temporäre Arbeitsdateien (wird bei Runs genutzt)
- `finished_episodes/` – finale Outputs
- `tests/` – Unit-Tests

### Entwicklungs-Workflow

- Kleine, gezielte Änderungen bevorzugen
- Keine Secrets in Code/Logs schreiben
- Pfade unter `PODCAST_*` beibehalten
- Keine Regie-/Sound-Anweisungen ins Skript

### Häufige Stolpersteine

- ffmpeg/ffprobe fehlt → Audio-Export schlägt fehl
- pytrends 404/429 → RSS-Fallback nutzen (bereits implementiert)
- Google Cloud TTS benötigt gültige `GOOGLE_APPLICATION_CREDENTIALS`

## Hinweise für Agents / Copilot

Siehe [AGENTS.md](AGENTS.md) für Leitplanken, Arbeitsweise und Qualitätssicherung.
