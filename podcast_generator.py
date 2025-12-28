import os
import time
import requests
import json
import subprocess
import re
import io
import mimetypes
from pytrends.request import TrendReq
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydub import AudioSegment
from dotenv import load_dotenv
from typing import List

# ==============================================================================
# KONFIGURATION & API KEYS
# ==============================================================================
load_dotenv()

def _require_env(var_name):
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"Environment variable {var_name} is required but not set.")
    return value

# Secrets aus der .env Datei
GEMINI_API_KEY = _require_env("GEMINI_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = _require_env("GOOGLE_APPLICATION_CREDENTIALS")
FREESOUND_API_KEY = _require_env("FREESOUND_API_KEY")

# Podcast Einstellungen
PODCAST_NAME = "Gehirntakko"
SLOGAN = "Wissen in unter 5 Minuten"
TEMP_DIR = "temp_assets"
OUTPUT_DIR = "finished_episodes"
ASSETS_DIR = "assets"

# Ordner erstellen
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Client Setup
client = genai.Client(api_key=GEMINI_API_KEY)


def _spell_out_abbreviations(text: str) -> str:
    """Expand 2-3 letter uppercase abbreviations (e.g., KI -> K I) for TTS clarity."""
    pattern = re.compile(r"(?<!#)\b([A-ZÄÖÜ]{2,3})\b")
    stoplist = {
        "DER", "DIE", "DAS", "UND", "DEN", "DEM", "DES", "EIN", "EINE",
        "VON", "MIT", "AUS", "IM", "IN", "AM", "BEI", "AUF", "FÜR", "AN",
        "IST", "SIND", "ICH", "DU", "ER", "SIE", "ES", "WIR", "IHR"
    }

    def repl(match: re.Match) -> str:
        word = match.group(1)
        if word in stoplist:
            return word
        return " ".join(list(word))

    return pattern.sub(repl, text)


def _strip_formatting(text: str) -> str:
    """
    Entfernt Formatierungen; Sternchen werden entfernt (kein SSML-Emphasis nötig).
    """
    text = re.sub(r"\[\s*([^\]]+)\s*\]", r"\1", text)
    text = re.sub(r"\(\s*([^\)]+)\s*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = text.replace("*", "")
    return text


def _to_ssml(text: str) -> str:
    """Wandelt Text in SSML ohne <emphasis>; nur Absätze/Sätze für Atempausen."""
    def _escape_ssml(value: str) -> str:
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    safe_text = _escape_ssml(text)
    paragraphs = [p.strip() for p in safe_text.split("\n\n") if p.strip()]

    ssml_parts = ["<speak>"]
    for para in paragraphs:
        sentences = re.split(r"(?<=[\.\?!])\s+", para)
        for sent in sentences:
            if not sent.strip():
                continue
            ssml_parts.append(f"<s>{sent.strip()}</s>")
        ssml_parts.append("<break time=\"300ms\"/>")
    ssml_parts.append("</speak>")
    return "".join(ssml_parts)


def _chunk_text(text: str, max_chars: int = 1500) -> List[str]:
    """Chunk text to respect TTS limits, splitting by paragraphs."""
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        # Wenn ein einzelner Paragraph zu lang ist, müssen wir ihn leider hart teilen
        if para_len > max_chars:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_len = 0
            
            # Groben Split machen
            chunks.append(para[:max_chars]) # Vereinfacht, besser wäre wortweiser Split
            # (Für Podcast Skripte sind Absätze meist < 1500 Zeichen)
            continue

        if current_len + para_len + 2 <= max_chars:
            current.append(para)
            current_len += para_len + 2
        else:
            if current:
                chunks.append("\n\n".join(current))
            current = [para]
            current_len = para_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks

def pick_available_model(preferences: List[str]) -> str:
    """Wählt das bestmögliche Modell anhand der Präferenz-Reihenfolge."""
    try:
        available = list(client.models.list())
    except Exception as e:
        print(f"   ⚠️ Konnte Modelle nicht listen ({e}). Versuche Standard: gemini-2.0-flash")
        return "gemini-2.0-flash"

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

    return "gemini-2.0-flash"

class PodcastGenerator:
    def __init__(self, topic):
        self.topic = topic
        self.script_content = ""
        self.audio_voice_path = ""
        self.music_path = ""
        self.final_audio_path = ""
        self.final_video_path = ""
        self.sources = []
        self.transcript_path = ""
        print(f"🚀 Starte Produktion für Thema: {topic}")

    # --------------------------------------------------------------------------
    # 1. TRENDS
    # --------------------------------------------------------------------------
    def research_trends(self):
        print("🔍 1. Analysiere Google Trends...")
        try:
            pytrends = TrendReq(hl='de-DE', tz=360)
            pytrends.build_payload([self.topic], cat=0, timeframe='now 7-d', geo='DE')
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
            print(f"   ⚠️ Trend-Fehler (nutze Fallback): {e}")
        return self.topic

    # --------------------------------------------------------------------------
    # 2. SKRIPT (Gemini)
    # --------------------------------------------------------------------------
    def generate_script(self):
        print(f"✍️ 2. Gemini schreibt das Skript über '{self.topic}'...")

        # Prompt optimiert für SSML Betonung
        prompt = f"""
        Du bist der Host des Podcasts '{PODCAST_NAME}'. Slogan: '{SLOGAN}'.
        Schreibe ein Skript für eine Audio-Aufnahme über das Thema: '{self.topic}'.
        
        Vorgaben:
        1. Rolle: Du bist ein charismatischer Wissens-Erklärer (ca. 30 Jahre alt). Dein Stil ist locker, aber kompetent. Du nutzt "Ich" und "Du".
        2. Betonung: Wenn du ein Wort besonders betonen willst (für Dramatik oder Wichtigkeit), setze es in *Sternchen*. Beispiel: "Das ist *wirklich* unglaublich." (Nutze das sparsam, aber gezielt).
        3. Struktur:
           - Knackiges Intro (Begrüßung + Slogan).
           - 3 faszinierende Fakten (Deep Dive).
           - Kurzes, warmes Outro.
        4. Formatierung: Reiner Sprechtext. Keine Regieanweisungen ("Lacht", "Musik", "Sound", "Jingle"), keine Labels oder Überschriften wie "Sprechtext" oder "---", keine Trennerlinien, kein Text vor dem eigentlichen gesprochenen Einstieg.
        5. Länge: Ca. 700 Wörter.
        6. Metadaten: Am Ende eine Zeile: "QUELLEN: url1; url2".
        7. Sprache: Deutsch
        8. Vermeide Aufzählungen oder nummerierte Listen im gesprochenen Text.
        9. Nutze Absätze für natürliche Pausen (2 Zeilenumbrüche).
        10. Vermeide Fachjargon; erkläre komplexe Begriffe einfach.
        11. Vermeide Wiederholungen und Füllwörter.
        12. Schreibe so, dass es sich natürlich anhört, wenn es vorgelesen wird.
        13. Erwähne am Ende das die Zuhörer den Podcast gerene bewerten können und uns folgen sollen (#Gehirntakko).
        """
        
        preferred = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-pro-latest"]
        model_name = pick_available_model(preferred)
        print(f"   -> Verwende Modell: {model_name}")

        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            raw_text = response.text

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
            self.script_content = _spell_out_abbreviations(cleaned_text)

            self.transcript_path = f"{TEMP_DIR}/script.txt"
            with open(self.transcript_path, "w", encoding="utf-8") as f:
                f.write(self.script_content)

            print("   -> Skript generiert.")
        except Exception as e:
            raise RuntimeError(f"Gemini API Fehler: {e}")

    # --------------------------------------------------------------------------
    # 3. STIMME (Google Cloud TTS)
    # --------------------------------------------------------------------------
    def generate_voice(self):
        print("🗣️ 3. Generiere Stimme (Gemini TTS)...")

        model_tts = "gemini-2.5-pro-preview-tts"
        voice_name = "gacrux"

        def _part_to_segment(part: types.Part, chunk_idx: int, cand_idx: int) -> AudioSegment:
            if not part.inline_data or not part.inline_data.data:
                raise RuntimeError(f"Chunk {chunk_idx}: Leere Audio-Teilantwort")
            data = part.inline_data.data
            mime = part.inline_data.mime_type or "audio/wav"
            if not mime.startswith("audio/"):
                raise RuntimeError(f"Chunk {chunk_idx}: Kein Audio (mime={mime}, cand={cand_idx})")

            # Spezialfall: rohes PCM (audio/L16;codec=pcm;rate=24000)
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

        chunks = _chunk_text(self.script_content)
        segments: List[AudioSegment] = []

        print(f"   -> Verarbeite {len(chunks)} Text-Abschnitte...")

        for idx, chunk in enumerate(chunks):
            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=chunk)]
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

            try:
                resp = client.models.generate_content(
                    model=model_tts,
                    contents=[content],
                    config=cfg,
                )
                # Kandidaten auf verwertbare Inline-Audio-Daten prüfen
                found = False
                for cand_idx, cand in enumerate(resp.candidates or []):
                    for part in cand.content.parts or []:
                        try:
                            seg = _part_to_segment(part, idx, cand_idx)
                        except RuntimeError as e:
                            print(f"   ⚠️ {e}")
                            continue
                        segments.append(seg)
                        found = True
                        break
                    if found:
                        break
                if not found:
                    raise RuntimeError(f"Keine Audio-Daten im Response (Chunk {idx})")
            except Exception as e:
                print(f"   ❌ Fehler bei Chunk {idx}: {e}")
                raise

        if not segments:
            raise RuntimeError("TTS lieferte keine Segmente.")

        final_voice = segments[0]
        for seg in segments[1:]:
            final_voice = final_voice.append(seg, crossfade=100)

        self.audio_voice_path = f"{TEMP_DIR}/voice_raw.mp3"
        final_voice.export(self.audio_voice_path, format="mp3")
        print("   -> Sprachdatei erstellt.")

    # --------------------------------------------------------------------------
    # 4. MUSIK (Freesound.org)
    # --------------------------------------------------------------------------
    def fetch_music(self):
        print("🎵 4. Suche Hintergrundmusik (Freesound)...")
        local_music = os.path.join(ASSETS_DIR, "background_loop.mp3")
        if os.path.exists(local_music):
            self.music_path = local_music
            print("   -> Lokale Datei 'background_loop.mp3' gefunden.")
            return

        try:
            url = "https://freesound.org/apiv2/search/text/"
            params = {
                "query": "lofi study loop",
                "token": FREESOUND_API_KEY,
                "sort": "rating_desc",
                "filter": "duration:[60 TO 300]"
            }
            r = requests.get(url, params=params)
            data = r.json()
            
            if data.get('results'):
                track = data['results'][0]
                track_id = track['id']
                detail_url = f"https://freesound.org/apiv2/sounds/{track_id}/"
                d_r = requests.get(detail_url, params={"token": FREESOUND_API_KEY})
                track_details = d_r.json()
                
                preview_url = track_details['previews']['preview-hq-mp3']
                print(f"   -> Lade herunter: {track['name']}")
                
                mp3_r = requests.get(preview_url)
                self.music_path = f"{TEMP_DIR}/music_download.mp3"
                with open(self.music_path, "wb") as f:
                    f.write(mp3_r.content)
                return

            print("   -> Nichts gefunden. Nutze Stille.")
            self.music_path = f"{TEMP_DIR}/silence.mp3"
            AudioSegment.silent(duration=10000).export(self.music_path, format="mp3")

        except Exception as e:
            print(f"   ⚠️ Musik-Fehler: {e}. Nutze Stille.")
            self.music_path = None

    # --------------------------------------------------------------------------
    # 5. MIXING
    # --------------------------------------------------------------------------
    def mix_audio(self):
        print("🎛️ 5. Mixing...")
        voice = AudioSegment.from_mp3(self.audio_voice_path)

        if self.music_path and os.path.exists(self.music_path):
            music = AudioSegment.from_mp3(self.music_path)
            music = music - 18 
            
            while len(music) < len(voice) + 5000:
                music += music
            music = music[:len(voice) + 5000]
            music = music.fade_out(3000)
            final = music.overlay(voice, position=500)
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
    def generate_metadata(self):
        print("📄 7. Metadaten...")
        transcription_output_path = os.path.join(
            OUTPUT_DIR, f"{self.topic.replace(' ', '_')}_transcription.txt"
        )

        with open(transcription_output_path, "w", encoding="utf-8") as f:
            f.write(self.script_content)

        meta = {
            "title": f"{PODCAST_NAME}: {self.topic}",
            "description": f"{SLOGAN}\n\n{self.script_content[:150]}...",
            "files": {
                "audio": self.final_audio_path,
                "video": self.final_video_path
            },
            "sources": self.sources,
            "transcript": self.script_content,
            "transcript_file": transcription_output_path
        }
        with open(f"{OUTPUT_DIR}/{self.topic.replace(' ', '_')}_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4)
        print("   -> Fertig.")

# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    print(f"--- {PODCAST_NAME.upper()} AUTOMATISIERUNG ---")
    topic = input("Thema: ")
    bot = PodcastGenerator(topic)
    
    bot.research_trends()
    bot.generate_script()
    bot.generate_voice()
    bot.fetch_music()
    bot.mix_audio()
    bot.create_video()
    bot.generate_metadata()
    
    print("\n✅ ALLES ERLEDIGT!")