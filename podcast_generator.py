import os
import time
import requests
import json
import subprocess  # Wichtig für FFmpeg Aufrufe
from pytrends.request import TrendReq
from google import genai
from google.genai import errors as genai_errors
from google.cloud import texttospeech
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

# Trage die Secrets in der .env Datei ein
GEMINI_API_KEY = _require_env("GEMINI_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = _require_env("GOOGLE_APPLICATION_CREDENTIALS")
PIXABAY_API_KEY = _require_env("PIXABAY_API_KEY")

# Podcast Einstellungen
PODCAST_NAME = "Gehirntakko"
SLOGAN = "Wissen in unter 5 Minuten"
TEMP_DIR = "temp_assets"
OUTPUT_DIR = "fertige_episoden"
ASSETS_DIR = "assets"  # Ordner für Cover-Bilder etc.

# Setup Directories
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Setup Clients (uses default endpoint)
client = genai.Client(api_key=GEMINI_API_KEY)


def pick_available_model(preferences: List[str]) -> str:
    """Pick first preferred model that is available for generateContent."""
    available = list(client.models.list())
    blocked_tokens = [
        "embedding",
        "tts",
        "image",
        "imagen",
        "veo",
        "computer-use",
        "robotics",
        "aqa",
        "native-audio",
    ]

    # First pass: match explicit preferences
    for model in available:
        short = model.name.split("/")[-1]
        if any(tok in short for tok in blocked_tokens):
            continue
        for pref in preferences:
            if short == pref or short.endswith(pref):
                return model.name  # use full name that API returns

    # Second pass: pick the first non-blocked "gemini" model
    for model in available:
        short = model.name.split("/")[-1]
        if any(tok in short for tok in blocked_tokens):
            continue
        if "gemini" in short and "embedding" not in short:
            return model.name

    names = ", ".join(m.name for m in available)
    raise RuntimeError(f"Kein verfügbares Textmodell gefunden. Verfügbare Modelle: {names}")

class PodcastGenerator:
    def __init__(self, topic):
        self.topic = topic
        self.script_content = ""
        self.audio_voice_path = ""
        self.music_path = ""
        self.final_audio_path = ""  # Umbenannt für Klarheit
        self.final_video_path = ""  # Neu für Video
        print(f"🚀 Starte Produktion für Thema: {topic}")

    # --------------------------------------------------------------------------
    # SCHRITT 1: TREND RECHERCHE (Google Trends)
    # --------------------------------------------------------------------------
    def research_trends(self):
        print("🔍 1. Analysiere Google Trends...")
        try:
            pytrends = TrendReq(hl='de-DE', tz=360)
            # Suche nach verwandten Queries zum Thema
            pytrends.build_payload([self.topic], cat=0, timeframe='now 7-d', geo='DE')
            related_queries = pytrends.related_queries()

            top_query = self.topic # Fallback

            if self.topic in related_queries and related_queries[self.topic]['top'] is not None:
                # Nimm den Top-Begriff, der gerade trendet
                df = related_queries[self.topic]['top']
                if not df.empty:
                    top_query = df.iloc[0]['query']
                    print(f"   -> Trend gefunden: '{top_query}' ist spezifischer als '{self.topic}'")
                    self.topic = top_query
            else:
                print("   -> Keine spezifischen Trends gefunden, nutze Ursprungsthema.")

        except Exception as e:
            print(f"   ⚠️ Trend-API Fehler (nutze Fallback): {e}")

        return self.topic

    # --------------------------------------------------------------------------
    # SCHRITT 2: SKRIPT GENERIERUNG (Gemini Pro)
    # --------------------------------------------------------------------------
    def generate_script(self):
        print(f"✍️ 2. Gemini schreibt das Skript über '{self.topic}'...")

        prompt = f"""
        Du bist der Host des Podcasts '{PODCAST_NAME}'. Slogan: '{SLOGAN}'.
        Schreibe ein Skript für eine Audio-Aufnahme über das Thema: '{self.topic}'.

        Vorgaben:
        1. Sprache: Deutsch, locker, duzend, energetisch.
        2. Struktur:
           - Kurzes Intro mit Slogan.
           - Hauptteil: Erkläre das Thema einfach (ELIF) und nenne 3 spannende Fakten.
           - Outro: Verabschiedung und Call-to-Action.
        3. Formatierung: Schreibe NUR den gesprochenen Text. Keine Regieanweisungen.
        4. Länge: Exakt so viel Text für ca. 3-4 Minuten Sprechzeit (ca. 450-500 Wörter).
        """
        # Wähle ein verfügbares Textmodell (per ListModels abgeglichen)
        preferred = [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.0-flash",
            "gemini-flash-latest",
            "gemini-pro-latest",
        ]

        model_name = pick_available_model(preferred)

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
        except genai_errors.ClientError as e:
            raise RuntimeError("Gemini API Fehler: prüfe GEMINI_API_KEY/Quota/Region") from e

        self.script_content = response.text

        # Skript speichern für Metadaten
        with open(f"{TEMP_DIR}/script.txt", "w", encoding="utf-8") as f:
            f.write(self.script_content)

        print("   -> Skript erfolgreich generiert.")

    # --------------------------------------------------------------------------
    # SCHRITT 3: SPRACH GENERIERUNG (Google Cloud TTS)
    # --------------------------------------------------------------------------
    def generate_voice(self):
        print("🗣️ 3. Generiere Stimme mit Google Neural2 (High Quality)...")

        # Setze Umgebungsvariable für Google Auth (falls nicht schon durch load_dotenv gesetzt)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=self.script_content)

        # Stimme konfigurieren (Männlich, Deutsch, Neural2-B ist sehr natürlich)
        voice = texttospeech.VoiceSelectionParams(
            language_code="de-DE",
            name="de-DE-Neural2-B",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.05, # Ein bisschen schneller wirkt dynamischer
            pitch=0.0
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        self.audio_voice_path = f"{TEMP_DIR}/voice_raw.mp3"
        with open(self.audio_voice_path, "wb") as out:
            out.write(response.audio_content)

        print("   -> Sprachdatei erstellt.")

    # --------------------------------------------------------------------------
    # SCHRITT 4: MUSIK BESCHAFFUNG (Pixabay API)
    # --------------------------------------------------------------------------
    def fetch_music(self):
        print("🎵 4. Suche Hintergrundmusik auf Pixabay...")

        # Fallback auf lokale Datei im assets Ordner bevorzugt
        local_music = os.path.join(ASSETS_DIR, "background_loop.mp3")
        
        if os.path.exists(local_music):
            self.music_path = local_music
            print("   -> Lokale Musikdatei 'background_loop.mp3' gefunden.")
            return

        # Fallback API Logic (vereinfacht)
        try:
            query = "lofi study beat"
            music_url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&audio_type=music"
            # Hier würde der echte Download stattfinden.
            # Für Demo erzeugen wir Stille oder Dummy, falls keine API Antwort.
            
            print("   -> Keine lokale Musik gefunden, erzeuge Dummy (Stille)...")
            self.music_path = f"{TEMP_DIR}/silence.mp3"
            AudioSegment.silent(duration=10000).export(self.music_path, format="mp3")

        except Exception as e:
            print(f"   ⚠️ Musik Fehler: {e}")
            self.music_path = None

    # --------------------------------------------------------------------------
    # SCHRITT 5: AUDIO MIXING (Pydub + FFmpeg)
    # --------------------------------------------------------------------------
    def mix_audio(self):
        print("🎛️ 5. Mische Stimme und Musik...")

        voice = AudioSegment.from_mp3(self.audio_voice_path)

        if self.music_path and os.path.exists(self.music_path):
            music = AudioSegment.from_mp3(self.music_path)
            # Musik leiser machen (-18dB)
            music = music - 18
            
            # Loop
            while len(music) < len(voice) + 5000:
                music += music
            music = music[:len(voice) + 5000]
            music = music.fade_out(3000)
            
            final_audio = music.overlay(voice, position=500)
        else:
            final_audio = voice

        # Export
        filename = f"{self.topic.replace(' ', '_')}.mp3"
        self.final_audio_path = os.path.join(OUTPUT_DIR, filename)

        final_audio.export(self.final_audio_path, format="mp3", bitrate="192k")
        print(f"   -> AUDIO EPISODE FERTIG: {self.final_audio_path}")

    # --------------------------------------------------------------------------
    # SCHRITT 6: VIDEO GENERIERUNG (FFmpeg)
    # --------------------------------------------------------------------------
    def create_video(self):
        print("🎬 6. Erstelle Video für YouTube (MP4)...")
        
        # Prüfen ob Cover Bild existiert
        cover_image = os.path.join(ASSETS_DIR, "cover.png")
        
        if not os.path.exists(cover_image):
            print(f"   ⚠️ Kein 'cover.png' im Ordner '{ASSETS_DIR}' gefunden. Überspringe Video.")
            return

        video_filename = f"{self.topic.replace(' ', '_')}_video.mp4"
        self.final_video_path = os.path.join(OUTPUT_DIR, video_filename)

        # FFmpeg Befehl: Loop Bild + Audio = Video
        cmd = [
            "ffmpeg", "-y", # Überschreiben erzwingen
            "-loop", "1",   # Bild loopen
            "-i", cover_image,
            "-i", self.final_audio_path,
            "-c:v", "libx264",     # Video Codec H.264
            "-tune", "stillimage", # Optimierung für Standbild
            "-c:a", "aac",         # Audio Codec AAC (Standard für MP4)
            "-b:a", "192k",        # Audio Bitrate
            "-pix_fmt", "yuv420p", # Pixel Format für Kompatibilität
            "-shortest",           # Video so lang wie der kürzeste Stream (Audio)
            self.final_video_path
        ]
        
        try:
            # subprocess.run führt den Befehl im Terminal aus
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
            print(f"   -> VIDEO FERTIG: {self.final_video_path}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Video Rendering Fehler: {e}")
            print("   Stelle sicher, dass FFmpeg installiert ist.")

    # --------------------------------------------------------------------------
    # SCHRITT 7: METADATEN FÜR UPLOAD
    # --------------------------------------------------------------------------
    def generate_metadata(self):
        print("📄 7. Erstelle Metadaten...")

        title = f"{PODCAST_NAME}: {self.topic} - {SLOGAN}"
        desc = f"""
        🎙️ {self.topic} - Einfach erklärt in 5 Minuten.
        
        Kapitel:
        00:00 Intro
        00:30 Hauptteil
        03:30 Fazit

        #gehirntakko #wissen #shorts #{self.topic.replace(' ', '')}
        
        (Teaser):
        {self.script_content[:150]}...
        """

        meta = {
            "title": title,
            "description": desc,
            "files": {
                "audio": self.final_audio_path,
                "video": self.final_video_path
            },
            "tags": ["Wissen", "Education", self.topic]
        }

        with open(f"{OUTPUT_DIR}/{self.topic.replace(' ', '_')}_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)

        print("   -> Metadaten gespeichert.")

# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    print(f"--- {PODCAST_NAME.upper()} AUTOMATISIERUNG ---")
    user_topic = input("Gib ein grobes Thema ein (z.B. 'Schwarze Löcher'): ")

    bot = PodcastGenerator(user_topic)

    # Pipeline ausführen
    bot.research_trends()
    bot.generate_script()
    bot.generate_voice()
    bot.fetch_music()
    bot.mix_audio()
    bot.create_video()
    bot.generate_metadata()

    print("\n------------------------------------------------")
    print("🎉 FERTIG! Ergebnisse in 'fertige_episoden'.")
    print("------------------------------------------------")