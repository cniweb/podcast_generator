import os
import requests
import json
import subprocess
import re
import io
import math
import mimetypes
import time
import xml.etree.ElementTree as ET
import shutil
from pytrends.request import TrendReq
from google import genai
from google.genai import types
from google.cloud import texttospeech
from pydub import AudioSegment
from dotenv import load_dotenv
from typing import List

# ==============================================================================
# KONFIGURATION & API KEYS aus .env auslesen
# ==============================================================================
from utils import (
    _chunk_text,
    _spell_out_abbreviations,
    _strip_formatting,
    _validate_script_constraints,
)
load_dotenv()

def _require_env(var_name):
    """Liest eine benötigte Umgebungsvariable ein und bricht mit klarer Meldung ab."""
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"Environment variable {var_name} is required but not set.")
    return value

# Secrets aus der .env Datei
GEMINI_API_KEY = _require_env("GEMINI_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = _require_env("GOOGLE_APPLICATION_CREDENTIALS")
FREESOUND_API_KEY = _require_env("FREESOUND_API_KEY")

# Podcast Einstellungen aus .env
PODCAST_NAME = _require_env("PODCAST_NAME")
SLOGAN = _require_env("PODCAST_SLOGAN")
TEMP_DIR = _require_env("PODCAST_TEMP_DIR")
OUTPUT_DIR = _require_env("PODCAST_OUTPUT_DIR")
ASSETS_DIR = _require_env("PODCAST_ASSETS_DIR")

# Ordner erstellen
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Client-Setup
client = genai.Client(api_key=GEMINI_API_KEY)

# Standard-Modell für Fallbacks
DEFAULT_MODEL = "gemini-2.0-flash"

# Skript-Constraints
SCRIPT_TARGET_WORDS = 700
SCRIPT_MIN_WORDS = 650
SCRIPT_MAX_WORDS = 800
SCRIPT_MIN_PARAGRAPHS = 5
SCRIPT_EXPECTED_PARAGRAPHS = 5


def _is_rate_limited_error(err: Exception | str) -> bool:
    msg = str(err).lower()
    return " 429" in msg or "code 429" in msg or "too many requests" in msg or "rate" in msg


def _require_ffmpeg(tool_name: str) -> str:
    """Prüft, ob ffmpeg/ffprobe verfügbar ist, sonst klarer Fehler."""
    path = shutil.which(tool_name)
    if not path:
        raise RuntimeError(
            f"{tool_name} nicht gefunden. Bitte ffmpeg installieren und zum PATH hinzufügen."
        )
    return path


def _ensure_audio_tools():
    """Vorab-Check für pydub-Tools."""
    _require_ffmpeg("ffmpeg")
    _require_ffmpeg("ffprobe")


def _to_ssml(text: str) -> str:
    """Baut SSML aus Klarschrift und wandelt *Wort* in <emphasis> um."""
    def _escape_ssml(value: str) -> str:
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 1. Escaping (wichtig, damit & oder < den XML Parser nicht brechen)
    safe_text = _escape_ssml(text)

    # 2. Markdown-Bold/Italic (*Wort*) in SSML Emphasis umwandeln
    # Regex sucht nach Sternchen-Paaren und ersetzt sie durch emphasis Tags
    # Das macht die Google Cloud Stimme deutlich lebendiger.
    safe_text = re.sub(r'\*([^\*]+)\*', r'<emphasis level="moderate">\1</emphasis>', safe_text)

    paragraphs = [p.strip() for p in safe_text.split("\n\n") if p.strip()]

    ssml_parts = ["<speak>"]
    for para in paragraphs:
        # Wir verpacken Paragraphen in <p>, das erzeugt natürliche Pausen
        ssml_parts.append("<p>")
        sentences = re.split(r"(?<=[\.\?!])\s+", para)
        for sent in sentences:
            if not sent.strip():
                continue
            # Sätze in <s> Tags helfen der Intonation
            ssml_parts.append(f"<s>{sent.strip()}</s>")
        ssml_parts.append("</p>")
    ssml_parts.append("</speak>")
    return "".join(ssml_parts)


def pick_available_model(preferences: List[str]) -> str:
    """Wählt das bestmögliche Modell anhand der Präferenz-Reihenfolge."""
    try:
        available = list(client.models.list())
    except Exception as e:
        print(f"   ⚠️ Konnte Modelle nicht listen ({e}). Versuche Standard: {DEFAULT_MODEL}")
        return DEFAULT_MODEL

    blocked_tokens = ["embedding", "tts", "image", "imagen", "veo", "computer-use", "robotics", "aqa", "native-audio"]

    candidates = []
    for model in available:
        short = model.name.split("/")[-1]
        if any(tok in short for tok in blocked_tokens):
            continue
        candidates.append((short, model.name))

    for pref in preferences:
        for short, full in candidates:
            if short == pref or short.endswith(pref):
                return full

    for short, full in candidates:
        if "gemini" in short:
            return full

    return DEFAULT_MODEL

class PodcastGenerator:
    def __init__(self, topic):
        """Kapselt den End-to-End-Podcast-Flow für ein bestimmtes Thema."""
        self.topic = topic
        self.script_content = ""
        self.audio_voice_path = ""
        self.music_path = ""
        self.final_audio_path = ""
        self.final_video_path = ""
        self.sources = []
        self.transcript_path = ""
        print(f"🚀 Starte Produktion für Thema: '{topic}'")

    def _translate_topic_to_en(self, topic: str) -> str:
        """Übersetzt das Thema knapp ins Englische, falls Freesound-Suche hilft."""
        prompt = (
            "Translate the following topic into concise English keywords for a music search. "
            "Return a short phrase (max 4 words) without quotes or explanations: "
            f"{topic}"
        )
        try:
            resp = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt,
            )
            translated = (resp.text or "").strip().replace("\n", " ")
            return translated or topic
        except Exception as exc:
            print(f"   ⚠️ Übersetzung fehlgeschlagen, nutze Original: {exc}")
            return topic

    def _generate_episode_metadata(self) -> tuple[str, str]:
        """Erstellt Titel und Beschreibung basierend auf dem Transkript."""
        preferences = ["gemini-3-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash", DEFAULT_MODEL, "gemini-pro-latest"]
        model_name = pick_available_model(preferences)

        prompt = (
            "Du erstellst Veröffentlichungs-Texte für creators.spotify.com. "
            f"Podcast: {PODCAST_NAME}; Slogan: {SLOGAN}; Thema: {self.topic}. "
            "Nutze das Transkript unten, aber fasse dich kurz und präzise. "
            "Antworte ausschließlich mit JSON (ohne Markdown, Backticks oder Erklärung) im Format: {\"title\": \"...\", \"description\": \"...\"}. "
            "Constraints: title <= 200 Zeichen, deutsch, ohne Anführungszeichen, kein Hashtag. "
            "Description <= 4000 Zeichen, deutsch, 2-4 Sätze Zusammenfassung + Call-to-Action zum Folgen/Bewerten; keine Listen, keine Quotes. "
            "Transkript:\n" + self.script_content
        )

        try:
            resp = client.models.generate_content(model=model_name, contents=prompt)
            raw = resp.text or ""

            def _extract_json(candidate: str) -> str | None:
                import re
                match = re.search(r"\{.*\}", candidate, re.DOTALL)
                return match.group(0) if match else None

            data = None
            for candidate in (raw, _extract_json(raw)):
                if not candidate:
                    continue
                try:
                    data = json.loads(candidate)
                    break
                except Exception:
                    continue

            if data is None:
                raise ValueError("json parse failed")

            title = str(data.get("title", "")).strip()
            desc = str(data.get("description", "")).strip()
        except Exception:
            print("   ⚠️ Konnte Episode-Metadaten nicht parsen, nutze Fallback.")
            title = f"{PODCAST_NAME}: {self.topic}"
            desc = f"{SLOGAN}\n\n{self.script_content[:300]}..."

        title = title[:200]
        desc = desc[:4000]
        return title, desc

    # --------------------------------------------------------------------------
    # 1. TRENDS
    # --------------------------------------------------------------------------
    def research_trends(self):
        """Holt naheliegende Trends für das Thema aus Google Trends (Deutschland)."""
        print("🔍 1. Analysiere Google Trends...")
        try:
            pytrends = TrendReq(hl='de', tz=120)
            pytrends.build_payload([self.topic], cat=0, timeframe='today 1-m', geo='DE')
            related = pytrends.related_queries()
            
            if self.topic in related and related[self.topic]['top'] is not None:
                df = related[self.topic]['top']
                if not df.empty:
                    top_query = df.iloc[0]['query']
                    print(f"   -> Trend gefunden: '{top_query}'")
                    self.topic = top_query
            else:
                print("   -> Keine spezifischen Trends, nutze Ursprungsthema.")
        except Exception as e:
            if _is_rate_limited_error(e):
                print("   ⚠️ Trend-Fehler (429). Überspringe Trends-Optimierung.")
            else:
                print(f"   ⚠️ Trend-Fehler (nutze Fallback): {e}")
        return self.topic

    # --------------------------------------------------------------------------
    # 2. SKRIPT (Gemini)
    # --------------------------------------------------------------------------
    def generate_script(self):
        """Lässt Gemini ein Podcast-Skript erstellen und säubert Formatierungen."""
        print(f"✍️ 2. Gemini schreibt das Skript über '{self.topic}'...")

        # Prompt mit extremer Fokus auf Wortanzahl-Limits
        prompt = f"""Du bist Podcast-Host von '{PODCAST_NAME}'. Slogan: '{SLOGAN}'.
Schreibe ein Podcast-Skript zum Thema '{self.topic}'.

ABSOLUT STRIKTE REGELN (NICHT BREAKBAR):
1. WORTANZAHL: {SCRIPT_MIN_WORDS}-{SCRIPT_MAX_WORDS} WÖRTER! Zähle sorgfältig! KEINE AUSNAHME!
2. STRUKTUR: GENAU 5 ABSÄTZE (Doppel-Zeilenumbruch trennt sie)
   • Absatz 1: Intro (20-30 Wörter)
   • Absätze 2-4: Je ein Fakt (80-120 Wörter pro Absatz)
   • Absatz 5: Outro mit #Hashtag (20-30 Wörter)
3. STIL: Kurze Sätze. Du/Ich. Locker aber kompetent.
4. KEINE: Labels, Überschriften, Musik/Sound/Jingle, Aufzählungen, unnötige Wiederholungen
5. BETONUNG: *Wort* für Emphasis (sparsam!)
6. ENDE: Neue Zeile: QUELLEN: url1; url2; url3

SCHREIB DIREKT DEN TEXT! KEIN DRUMHERUM!"""

        fixup_prompt = (
            "Podcast-Host von '{name}'. Überarbeite STRIKT nach diesen Regeln:\n"
            "• {min_words}-{max_words} Wörter (NICHT MEHR!)\n"
            "• GENAU 5 ABSÄTZE\n"
            "• Kurze, knappe Sätze\n"
            "• KEINE Labels/Musik/Aufzählungen\n"
            "• ENDE: QUELLEN: url1; url2; url3\n\n"
            "Zu überarbeitender Text:\n{draft}"
        ).format(
            name=PODCAST_NAME,
            min_words=SCRIPT_MIN_WORDS,
            max_words=SCRIPT_MAX_WORDS,
            draft="{draft}",
        )
        
        preferred = ["gemini-3-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash", DEFAULT_MODEL, "gemini-pro-latest"]
        model_name = pick_available_model(preferred)
        print(f"   -> Verwende Modell: {model_name}")

        try:
            attempts = 3
            last_errors: list[str] = []
            raw_text = ""
            for attempt in range(1, attempts + 1):
                if attempt == 1:
                    response = client.models.generate_content(model=model_name, contents=prompt)
                else:
                    print(f"   ⚠️  Skript verletzt Constraints. Versuch {attempt}/{attempts}...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=fixup_prompt.format(draft=raw_text),
                    )

                raw_text = response.text or ""

                # Quelle extrahieren
                sources_line = ""
                kept_lines = []
                for line in raw_text.splitlines():
                    if line.strip().upper().startswith("QUELLEN:"):
                        sources_line = line
                    else:
                        kept_lines.append(line)

                if sources_line:
                    parts = sources_line.split(":", 1)[-1]
                    self.sources = [s.strip() for s in parts.split(";") if s.strip()]
                else:
                    self.sources = []

                cleaned_text = "\n".join(kept_lines)
                cleaned_text = _strip_formatting(cleaned_text)
                cleaned_text = _spell_out_abbreviations(cleaned_text)

                validation = _validate_script_constraints(
                    cleaned_text,
                    min_words=SCRIPT_MIN_WORDS,
                    max_words=SCRIPT_MAX_WORDS,
                    min_paragraphs=SCRIPT_MIN_PARAGRAPHS,
                    expected_paragraphs=SCRIPT_EXPECTED_PARAGRAPHS,
                )

                # Intelligente Nachbearbeitung: Absatz-Struktur reparieren
                if not validation["ok"] and validation["paragraph_count"] != SCRIPT_EXPECTED_PARAGRAPHS:
                    cleaned_text, fixed_validation = self._repair_paragraph_structure(cleaned_text)
                    if fixed_validation["ok"]:
                        validation = fixed_validation

                # Intelligente Nachbearbeitung: Wortanzahl reduzieren, falls zu lang
                if not validation["ok"] and validation["word_count"] > SCRIPT_MAX_WORDS:
                    cleaned_text = self._reduce_word_count(cleaned_text, SCRIPT_MAX_WORDS)
                    validation = _validate_script_constraints(
                        cleaned_text,
                        min_words=SCRIPT_MIN_WORDS,
                        max_words=SCRIPT_MAX_WORDS,
                        min_paragraphs=SCRIPT_MIN_PARAGRAPHS,
                        expected_paragraphs=SCRIPT_EXPECTED_PARAGRAPHS,
                    )

                if validation["ok"]:
                    self.script_content = cleaned_text
                    break

                summary = (
                    f"Versuch {attempt}: {', '.join(validation['errors'])} "
                    f"(Wörter: {validation['word_count']}, Absätze: {validation['paragraph_count']})"
                )
                last_errors.append(summary)

            if not self.script_content:
                raise RuntimeError(
                    "Skript verletzt nach mehreren Versuchen die Constraints: "
                    + " | ".join(last_errors)
                )

            self.transcript_path = f"{TEMP_DIR}/script.txt"
            with open(self.transcript_path, "w", encoding="utf-8") as f:
                f.write(self.script_content)

            print("   -> Skript generiert.")
        except Exception as e:
            raise RuntimeError(f"Gemini API Fehler: {e}")

    def _repair_paragraph_structure(self, text: str) -> tuple[str, dict]:
        """Versucht, Text in GENAU 5 Absätze zu reorganisieren."""
        from utils import _count_words
        
        # Extrahiere alle nicht-leeren Zeilen
        lines = [l for l in text.splitlines() if l.strip()]
        if not lines:
            return text, {"ok": False, "errors": ["Text ist leer"]}
        
        # Strategie: Versuche, den Text intelligent auf 5 größere Absätze aufzuteilen
        total_words = _count_words(text)
        target_words_per_para = total_words // 5  # Ca. 1/5 pro Absatz
        
        # Teile in groben Blöcken auf
        paragraphs = []
        current_block = []
        word_count = 0
        
        for line in lines:
            line_words = _count_words(line)
            current_block.append(line)
            word_count += line_words
            
            # Wenn wir ungefähr 1/5 pro Absatz erreicht haben und ein gutes Bruchstück-Punkt ist
            if word_count >= target_words_per_para * 0.8 and len(paragraphs) < 4:
                paragraphs.append(" ".join(current_block))
                current_block = []
                word_count = 0
        
        # Rest in den letzten Absatz
        if current_block:
            paragraphs.append(" ".join(current_block))
        
        # Falls immer noch nicht genau 5, passe an
        while len(paragraphs) < 5:
            # Teile den längsten Absatz auf
            longest_idx = max(range(len(paragraphs)), key=lambda i: _count_words(paragraphs[i]))
            longest = paragraphs[longest_idx]
            sentences = re.split(r'(?<=[.!?])\s+', longest)
            
            if len(sentences) > 2:
                mid = len(sentences) // 2
                paragraphs[longest_idx] = " ".join(sentences[:mid])
                paragraphs.insert(longest_idx + 1, " ".join(sentences[mid:]))
            else:
                break  # Kann nicht weiter teilen
        
        while len(paragraphs) > 5:
            # Merge the two shortest paragraphs
            shortest_pairs = [(i, i+1) for i in range(len(paragraphs)-1)]
            if not shortest_pairs:
                break
            merge_idx = min(shortest_pairs, key=lambda p: _count_words(paragraphs[p[0]]) + _count_words(paragraphs[p[1]]))[0]
            paragraphs[merge_idx] = paragraphs[merge_idx] + " " + paragraphs[merge_idx + 1]
            del paragraphs[merge_idx + 1]
        
        repaired_text = "\n\n".join(paragraphs)
        
        # Validiere die neue Struktur
        validation = _validate_script_constraints(
            repaired_text,
            min_words=SCRIPT_MIN_WORDS,
            max_words=SCRIPT_MAX_WORDS,
            min_paragraphs=SCRIPT_MIN_PARAGRAPHS,
            expected_paragraphs=SCRIPT_EXPECTED_PARAGRAPHS,
        )
        
        return repaired_text, validation

    def _reduce_word_count(self, text: str, target_max: int) -> str:
        """Kürzt Text intelligent auf Zielwortanzahl, indem unwichtige Wörter gelöscht werden."""
        from utils import _count_words
        
        current_words = _count_words(text)
        if current_words <= target_max:
            return text
        
        # Strategie: Entferne Fullwörter und Phrasen, die nicht essentiell sind
        removed_phrases = [
            r'\b(auch|ebenso|darüber hinaus|gemäß|laut der Forschung|wie bereits erwähnt)\b',
            r'\b(zum Beispiel|beispielsweise|etwa|etc\.|usw\.)\b',
            r',\s*(die auch|der auch|das auch)',
            r'\s*(besonders|ganz|sehr|wirklich|wirklich|definitiv|absolut)\s+',
        ]
        
        shortened = text
        for pattern in removed_phrases:
            shortened = re.sub(pattern, '', shortened, flags=re.IGNORECASE)
            current_words = _count_words(shortened)
            if current_words <= target_max:
                return shortened.strip()
        
        # Fallback: Entferne von hinten (letzte Sätze/Phrasen)
        paragraphs = [p.strip() for p in shortened.split("\n\n") if p.strip()]
        while len(paragraphs) > 0 and _count_words("\n\n".join(paragraphs)) > target_max:
            # Entferne letzte Sätze aus dem letzten Absatz
            last_para = paragraphs[-1]
            sentences = re.split(r'(?<=[.!?])\s+', last_para)
            if len(sentences) > 1:
                sentences.pop()
                paragraphs[-1] = " ".join(sentences)
            else:
                paragraphs.pop()
        
        return "\n\n".join(paragraphs).strip()

    # --------------------------------------------------------------------------
    # 3. MUSIK (Freesound.org)
    # --------------------------------------------------------------------------
    def fetch_music(self):
        """Lädt einen Musik-Loop von Freesound oder nutzt lokale/stille Fallbacks."""
        print("🎵 3. Suche Hintergrundmusik (Freesound)...")
        local_music = os.path.join(ASSETS_DIR, "background_loop.mp3")
        if os.path.exists(local_music):
            self.music_path = local_music
            print("   -> Lokale Datei 'background_loop.mp3' gefunden.")
            return

        search_topic = self._translate_topic_to_en(self.topic)
        if search_topic != self.topic:
            print(f"   -> Übersetztes Suchthema: '{search_topic}'")

        try:
            def _search_and_download(query: str) -> bool:
                url = "https://freesound.org/apiv2/search/text/"
                params = {
                    "query": query,
                    "token": FREESOUND_API_KEY,
                    "sort": "rating_desc",
                    "filter": "duration:[60 TO 300]"
                }
                resp = requests.get(url, params=params)
                data = resp.json()
                if data.get("results"):
                    track = data["results"][0]
                    track_id = track["id"]
                    detail_url = f"https://freesound.org/apiv2/sounds/{track_id}/"
                    d_r = requests.get(detail_url, params={"token": FREESOUND_API_KEY})
                    track_details = d_r.json()
                    preview_url = track_details["previews"]["preview-hq-mp3"]
                    print(f"   -> Lade herunter: {track['name']}")
                    mp3_r = requests.get(preview_url)
                    self.music_path = f"{TEMP_DIR}/music_download.mp3"
                    with open(self.music_path, "wb") as f:
                        f.write(mp3_r.content)
                    return True
                return False

            # Erst themenbezogen, dann Fallback auf lofi loop
            found = _search_and_download(f"background {search_topic}")
            if found:
                return
            print("   -> Keine passenden Treffer, versuche Standard-Loop...")
            found = _search_and_download("lofi study loop")
            if found:
                return

            print("   -> Nichts gefunden. Nutze Stille.")
            self.music_path = f"{TEMP_DIR}/silence.mp3"
            AudioSegment.silent(duration=10000).export(self.music_path, format="mp3")

        except Exception as e:
            print(f"   ⚠️ Musik-Fehler: {e}. Nutze Stille.")
            self.music_path = None

    # --------------------------------------------------------------------------
    # 4. STIMME (Google Cloud TTS mit Fallback & SSML)
    # --------------------------------------------------------------------------
    def generate_voice(self):
        """Konvertiert das Skript in Audio: Gemini TTS mit Rate-Limit-Fallback zu Cloud TTS."""
        print("🗣️ 4. Generiere Stimme (Gemini TTS, Fallback Google Cloud TTS + SSML)...")

        _ensure_audio_tools()

        model_tts = "gemini-2.5-pro-preview-tts"
        voice_name = "umbriel"
        print(f"   -> Verwende TTS-Modell: {model_tts} (Stimme: {voice_name})")

        chunks = _chunk_text(self.script_content)
        print(f"   -> Verarbeite {len(chunks)} Text-Abschnitte...")

        segments = self._tts_segments(chunks, model_tts, voice_name)

        if not segments:
            raise RuntimeError("TTS lieferte keine Segmente.")

        final_voice = segments[0]
        for seg in segments[1:]:
            final_voice = final_voice.append(seg, crossfade=100)

        self.audio_voice_path = f"{TEMP_DIR}/voice_raw.mp3"
        final_voice.export(self.audio_voice_path, format="mp3")
        print("   -> Sprachdatei erstellt.")

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return "429" in msg or "rate" in msg or "resource_exhausted" in msg

    def _part_to_segment(self, part: types.Part, chunk_idx: int, cand_idx: int) -> AudioSegment:
        if not part.inline_data or not part.inline_data.data:
            raise RuntimeError(f"Chunk {chunk_idx}: Leere Audio-Teilantwort")
        data = part.inline_data.data
        mime = part.inline_data.mime_type or "audio/wav"
        if not mime.startswith("audio/"):
            raise RuntimeError(f"Chunk {chunk_idx}: Kein Audio (mime={mime}, cand={cand_idx})")

        if "L16" in mime or "pcm" in mime:
            try:
                return AudioSegment.from_raw(
                    io.BytesIO(data),
                    sample_width=2,
                    frame_rate=24000,
                    channels=1,
                )
            except Exception as e:
                raise RuntimeError(
                    f"Chunk {chunk_idx}: PCM-Dekodierung fehlgeschlagen (mime={mime}, len={len(data)}, cand={cand_idx}): {e}"
                )

        fmt = "wav"
        if "mp3" in mime:
            fmt = "mp3"
        elif "wav" in mime:
            fmt = "wav"
        elif "ogg" in mime:
            fmt = "ogg"
        else:
            guess = mimetypes.guess_extension(mime)
            if guess:
                fmt = guess.lstrip(".")
        try:
            return AudioSegment.from_file(io.BytesIO(data), format=fmt)
        except Exception as e:
            raise RuntimeError(
                f"Chunk {chunk_idx}: Audio-Dekodierung fehlgeschlagen (mime={mime}, len={len(data)}, cand={cand_idx}): {e}"
            )

    def _generate_chunk_with_gemini(self, chunk_idx: int, chunk_text: str, model_tts: str, voice_name: str) -> AudioSegment:
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=chunk_text)]
        )

        cfg = types.GenerateContentConfig(
            temperature=1,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            ),
        )

        resp = client.models.generate_content(
            model=model_tts,
            contents=[content],
            config=cfg,
        )
        for cand_idx, cand in enumerate(resp.candidates or []):
            for part in cand.content.parts or []:
                try:
                    return self._part_to_segment(part, chunk_idx, cand_idx)
                except RuntimeError as e:
                    print(f"   ⚠️ {e}")
                    continue
        raise RuntimeError(f"Keine Audio-Daten im Response (Chunk {chunk_idx}, Modell {model_tts})")

    def _generate_chunk_with_gcloud(self, chunk_idx: int, chunk_text: str) -> AudioSegment:
        tts_client = texttospeech.TextToSpeechClient()
        voice_params = texttospeech.VoiceSelectionParams(
            language_code="de-DE",
            name="de-DE-Polyglot-1",
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.05,
            pitch=0.0,
        )
        ssml_text = _to_ssml(chunk_text)
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config,
        )
        if not response.audio_content:
            raise RuntimeError(f"Chunk {chunk_idx}: Leere Audio-Antwort von Google Cloud TTS")
        audio_bytes = io.BytesIO(response.audio_content)
        return AudioSegment.from_file(audio_bytes, format="mp3")

    def _process_chunk(self, idx, chunk, model_tts, voice_name, max_attempts=3):
        for attempt in range(1, max_attempts + 1):
            try:
                return self._generate_chunk_with_gemini(idx, chunk, model_tts, voice_name)
            except Exception as e:
                if self._is_rate_limit_error(e) and attempt < max_attempts:
                    delay = 4 ** attempt
                    print(f"   ⚠️  Rate-Limit bei Chunk {idx} (Versuch {attempt}/{max_attempts}), warte {delay}s...")
                    time.sleep(delay)
                    continue
                if self._is_rate_limit_error(e) and attempt == max_attempts:
                    print("   ⚠️  Rate-Limit erschöpft, wechsle zu Google Cloud TTS Fallback...")
                    raise e
                print(f"   ❌ Fehler bei Chunk {idx}: {e}")
                raise
        raise RuntimeError(f"Chunk {idx}: Unbekannter Fehler bei Gemini TTS")

    def _tts_segments(self, chunks, model_tts, voice_name):
        segments = []
        for idx, chunk in enumerate(chunks):
            try:
                seg = self._process_chunk(idx, chunk, model_tts, voice_name)
                segments.append(seg)
            except Exception as gem_err:
                if self._is_rate_limit_error(gem_err):
                    try:
                        print(f"      -> Nutze Cloud TTS mit SSML für Chunk {idx}...")
                        seg = self._generate_chunk_with_gcloud(idx, chunk)
                        segments.append(seg)
                        continue
                    except Exception as gc_err:
                        print(f"   ❌ Google Cloud TTS Fehler (Fallback) bei Chunk {idx}: {gc_err}")
                        raise
                raise
        return segments

    # --------------------------------------------------------------------------
    # 5. MIXING
    # --------------------------------------------------------------------------
    def mix_audio(self):
        """Mischt Stimme mit Musik-Loop und exportiert die finale MP3."""
        print("🎛️ 5. Mixing...")
        voice = AudioSegment.from_mp3(self.audio_voice_path)

        if self.music_path and os.path.exists(self.music_path):
            music = AudioSegment.from_mp3(self.music_path)
            music = music - 18 

            def _loop_music_fast(track: AudioSegment, target_ms: int) -> AudioSegment:
                """Loop per Vorverdopplung und Schnitt (spart Kopien in der Schleife)."""
                reps = max(2, math.ceil(target_ms / len(track)) + 1)
                combined = track * reps
                return combined[:target_ms]

            target_len = len(voice) + 2000  # kleiner Puffer für das Fade-Out
            music = _loop_music_fast(music, target_len)
            music = music.fade_out(1500)
            final = music.overlay(voice, position=200)
        else:
            final = voice

        filename = f"{self.topic.replace(' ', '_')}.mp3"
        self.final_audio_path = os.path.join(OUTPUT_DIR, filename)
        final.export(self.final_audio_path, format="mp3", bitrate="192k")
        print(f"   -> Audio fertig: {self.final_audio_path}")

    # --------------------------------------------------------------------------
    # 6. VIDEO (FFmpeg)
    # --------------------------------------------------------------------------
    def create_video(self):
        """Erstellt ein Standbild-Video mit Cover und finalem Audio via FFmpeg."""
        print("🎬 6. Erstelle YouTube-Video...")
        cover_png = os.path.join(ASSETS_DIR, "cover.png")
        cover_jpg = os.path.join(ASSETS_DIR, "cover.jpg")
        
        if os.path.exists(cover_png):
            cover_image = cover_png
        elif os.path.exists(cover_jpg):
            cover_image = cover_jpg
        else:
            print(f"   ⚠️ Kein Cover gefunden (weder .png noch .jpg in {ASSETS_DIR}).")
            return

        video_filename = f"{self.topic.replace(' ', '_')}_video.mp4"
        self.final_video_path = os.path.join(OUTPUT_DIR, video_filename)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", cover_image,
            "-i", self.final_audio_path,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            self.final_video_path
        ]
        
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
            print(f"   -> Video fertig: {self.final_video_path}")
        except Exception as e:
            print(f"   ❌ FFmpeg Fehler: {e}")

    # --------------------------------------------------------------------------
    # 7. METADATEN
    # --------------------------------------------------------------------------
    def generate_metadata(self, include_media: bool = True):
        """Speichert Transkript, Titel/Beschreibung und Pfade zu Audio/Video."""
        print("📄 7. Metadaten...")
        transcription_output_path = os.path.join(
            OUTPUT_DIR, f"{self.topic.replace(' ', '_')}_transcription.txt"
        )

        with open(transcription_output_path, "w", encoding="utf-8") as f:
            f.write(self.script_content)

        episode_title, episode_desc = self._generate_episode_metadata()

        meta = {
            "title": episode_title or f"{PODCAST_NAME}: {self.topic}",
            "description": episode_desc or f"{SLOGAN}\n\n{self.script_content[:150]}...",
            "episode_title": episode_title,
            "episode_description": episode_desc,
            "files": {
                "audio": self.final_audio_path if include_media else None,
                "video": self.final_video_path if include_media else None,
            },
            "sources": self.sources,
            "transcript": self.script_content,
            "transcript_file": transcription_output_path,
        }
        # ensure_ascii=False, damit Umlaute in title/description lesbar bleiben
        with open(f"{OUTPUT_DIR}/{self.topic.replace(' ', '_')}_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=4)
        print("   -> Fertig.")

def _pick_realtime_title(df_rt):
    """Liest den bestmöglichen Titel aus realtime_trending_searches."""
    if df_rt is None or df_rt.empty:
        return None
    row0 = df_rt.iloc[0]
    if "title" in df_rt.columns:
        t = row0.get("title")
        if isinstance(t, list) and t:
            return t[0]
        if isinstance(t, str) and t.strip():
            return t.strip()
    if "entityNames" in df_rt.columns:
        names = row0.get("entityNames")
        if isinstance(names, list) and names:
            return names[0]
    return None


def _search_dailytrends(pytrends, country_code, debug_today):
    """Sucht Trends über today_searches für ein Land."""
    try:
        df = pytrends.today_searches(pn=country_code)
        if df is not None:
            debug_today[country_code] = df.head().to_string(index=False)
        if df is not None and not df.empty:
            return df.iloc[0]
    except Exception as err:
        if _is_rate_limited_error(err):
            debug_today[country_code] = "dailytrends Fehler: 429"
        else:
            debug_today[country_code] = f"dailytrends Fehler: {err}"
    return None


def _search_realtime(pytrends, country_code, debug_today):
    """Sucht Trends über realtime_trending_searches für ein Land."""
    try:
        df_rt = pytrends.realtime_trending_searches(pn=country_code, count=50)
        if df_rt is not None:
            debug_today[f"{country_code}-realtime"] = df_rt.head().to_string(index=False)
        pick = _pick_realtime_title(df_rt)
        if pick:
            return pick
    except Exception as err:
        if _is_rate_limited_error(err):
            debug_today[f"{country_code}-realtime"] = "realtime Fehler: 429"
        else:
            debug_today[f"{country_code}-realtime"] = f"realtime Fehler: {err}"
    return None


def _search_legacy(pytrends, country_code, debug_today):
    """Sucht Trends über trending_searches (Legacy)."""
    try:
        pn_map = {
            'DE': 'germany',
            'AT': 'austria',
            'CH': 'switzerland',
        }
        pn_val = pn_map.get(country_code, 'germany')
        df_legacy = pytrends.trending_searches(pn=pn_val)
        if df_legacy is not None:
            debug_today[f"{country_code}-legacy"] = df_legacy.head().to_string(index=False)
        if df_legacy is not None and not df_legacy.empty:
            return df_legacy.iloc[0, 0]
    except Exception as err:
        if _is_rate_limited_error(err):
            debug_today[f"{country_code}-legacy"] = "legacy Fehler: 429"
        else:
            debug_today[f"{country_code}-legacy"] = f"legacy Fehler: {err}"
    return None


def _search_rss(country_code, debug_today):
    """Sucht Trends über das öffentliche Google Trends RSS-Feed (Fallback bei 404)."""
    geo = country_code.upper() if country_code else "DE"
    url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            debug_today[f"{geo}-rss"] = f"rss Fehler: HTTP {resp.status_code}"
            return None
        root = ET.fromstring(resp.text)
        items = root.findall("./channel/item/title")
        if not items:
            debug_today[f"{geo}-rss"] = "rss Fehler: Keine Items"
            return None
        top = items[0].text.strip() if items[0].text else None
        debug_today[f"{geo}-rss"] = top or "rss Fehler: Leerer Titel"
        return top
    except Exception as err:
        debug_today[f"{geo}-rss"] = f"rss Fehler: {err}"
        return None


def _try_today(pytrends, country_code: str, debug_today):
    """Versucht verschiedene Trend-Suchstrategien für ein Land."""
    for search_func in (_search_dailytrends, _search_realtime, _search_legacy):
        result = search_func(pytrends, country_code, debug_today)
        if result:
            return result
    # RSS-Fallback (wenn pytrends 404 liefert)
    # Bei 429 hilft RSS oft sofort; wenn RSS auch limitiert, gib None zurück.
    result = _search_rss(country_code, debug_today)
    if result:
        return result
    return None


# ==============================================================================
# HAUPTPROGRAMM
# ==============================================================================
if __name__ == "__main__":
    print(f"--- {PODCAST_NAME.upper()} AUTOMATISIERUNG ---")
    _ensure_audio_tools()
    topic = input("Thema (Lass leer für aktuellen Top-Trend): ").strip()

    if not topic:
        print("🔍 Keine Eingabe. Suche nach aktuellen Trends in Deutschland...")
        try:
            pytrends = TrendReq(hl='de', tz=120)
            debug_today = {}

            trend_topic = (
                _try_today(pytrends, 'DE', debug_today)
                or _try_today(pytrends, 'AT', debug_today)
                or _try_today(pytrends, 'CH', debug_today)
            )

            if trend_topic:
                topic = trend_topic
                print(f"📈 Top-Trend gefunden: '{topic}'")
            else:
                print("   ⚠️  Keine Trends gefunden. Nutze Fallback.")
                for code, dbg in debug_today.items():
                    print(f"   🔎 today_searches {code}: {dbg}")
                topic = "Künstliche Intelligenz"
        except Exception as e:
            print(f"   ⚠️ Fehler bei Trend-Suche: {e}. Nutze Fallback.")
            topic = "Künstliche Intelligenz"
    bot = PodcastGenerator(topic)
    
    bot.research_trends()
    bot.generate_script()
    bot.fetch_music()
    bot.generate_voice()
    bot.mix_audio()
    bot.create_video()
    bot.generate_metadata()
    
    print("\n✅ ALLES ERLEDIGT!")
