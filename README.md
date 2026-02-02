# Podcast Generator

## Schnellstart (für neue Nutzer)

1. Voraussetzungen prüfen
   - Python 3.12+ und ffmpeg im PATH
2. Setup ausführen
   - `./setup.sh`
3. Podcast erzeugen
   - `./run.sh "Dein Thema"`
   - leer lassen, um Trends automatisch zu verwenden

Ausgaben findest du in `PODCAST_OUTPUT_DIR` (Audio, Video, Transkript und Metadaten).

## Zweck

- Erstellt automatisch kurze Wissens-Podcasts (Audio + optionales Standbild-Video) mit Skript, TTS-Voice, Hintergrundmusik und Metadaten.
- Nutzt aktuelle Trends (Google Trends) für Themenanreicherung.
- Verwendet Gemini für Skript- und Voice-Generierung sowie Freesound für lizenzfreie Musik-Snippets.

## Architektur & Ablauf

1. `run.sh "<Thema>"`
   - Lädt `.env`, prüft alle Pflicht-Variablen, bereinigt Arbeitsordner, aktiviert venv und startet `podcast_generator.py`.
2. `setup.sh`
   - Optionaler Helfer: prüft `.env`, FFmpeg, Python, installiert Requirements.
3. `podcast_generator.py`
   - Trends: holt Top-Query via Google Trends (pytrends) mit Fokus DACH (DE/AT/CH); fällt bei Fehlschlag auf statisches Thema zurück.
   - Skript: Gemini-Textmodell generiert deutschen Sprechtext, säubert Formatierung, entfernt Regie-/Sound-Anweisungen, speichert Transkript.
   - Stimme: Gemini TTS (`gemini-2.5-pro-preview-tts`, Stimme konfigurierbar) generiert Audio in Chunks, fügt per pydub zusammen.
   - Musik: sucht Freesound nach „podcast background `topic` instrumental“, fällt auf „lofi study loop“ zurück, sonst Stille.
   - Mixing: Sprachspur mit geloopter Musik unterlegt, Export als MP3; Video mit FFmpeg als Standbild + Audio.
   - Metadaten: JSON + Transkript-Text im Output-Ordner.

## Verwendete APIs / Tools

- Google Gemini (Text + TTS) über `google-genai` Client.
- Freesound API für Hintergrundmusik.
- Google Trends via `pytrends`.
- pydub + ffmpeg für Audio, ffmpeg für Video.

## Voraussetzungen

- ffmpeg im PATH (Windows/macOS/Linux)
- Python 3.12+ empfohlen (wegen audioop); venv wird von `run.sh`/`setup.sh` angelegt
- `.env` mit allen Pflichtwerten.

## .env Beispiel (alle Pflichtfelder)

```bash
GEMINI_API_KEY=dein_gemini_key
FREESOUND_API_KEY=dein_freesound_key
GOOGLE_APPLICATION_CREDENTIALS=google_cloud_credentials.json

PODCAST_NAME="Mein Podcast"
PODCAST_SLOGAN="Alles, was man wissen muss..."
PODCAST_TEMP_DIR=temp_assets
PODCAST_OUTPUT_DIR=finished_episodes
PODCAST_ASSETS_DIR=assets
```

## Nutzung

```bash
chmod +x run.sh setup.sh
./setup.sh           # einmalig, prüft .env/ffmpeg/requirements
./run.sh "Regieassistenz im Theater"  # erzeugt Audio/Video/Metadaten
```

Ausgaben:

- Audio: `<PODCAST_OUTPUT_DIR>/<Thema>.mp3`
- Video: `<PODCAST_OUTPUT_DIR>/<Thema>_video.mp4` (falls Cover im Assets-Ordner vorhanden)
- Transkript: `<PODCAST_OUTPUT_DIR>/<Thema>_transcription.txt`
- Metadaten: `<PODCAST_OUTPUT_DIR>/<Thema>_meta.json`

## Konfiguration

- Stimme anpassen in [podcast_generator.py](podcast_generator.py) via `voice_name` (unter "3. STIMME").
- Cover-Bild: `assets/cover.png` oder `assets/cover.jpg`.
- Musik-Query-Fallbacks: zuerst themenbezogen, dann „lofi study loop“, sonst Stille.

## Fehlerbehebung

- Fehler "Environment variable ... is required": .env prüfen und Wert setzen.
- ffmpeg nicht gefunden: ffmpeg installieren und PATH prüfen, danach `setup.sh` erneut ausführen
- Audioop fehlt: `run.sh` installiert `audioop-lts` über requirements; sicherstellen, dass Python 3.12+ genutzt wird.

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
- Keine Regie-/Sound-Anweisungen ins Skript

### Häufige Stolpersteine

- ffmpeg/ffprobe fehlt → Audio-Export schlägt fehl
- pytrends 404/429 → RSS-Fallback nutzen (bereits implementiert)
- Google Cloud TTS benötigt gültige `GOOGLE_APPLICATION_CREDENTIALS`

## Hinweise für Agents / Copilot

Siehe [AGENTS.md](AGENTS.md) für Leitplanken, Arbeitsweise und Qualitätssicherung.
