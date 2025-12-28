import os
import time
import requests
import json
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

# Setup Directories
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
        self.final_path = ""
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
           - Outro: Verabschiedung.
        3. Formatierung: Schreibe NUR den gesprochenen Text. Keine Regieanweisungen wie *lacht* oder [Intro Musik].
        4. Länge: Exakt so viel Text für ca. 3-4 Minuten Sprechzeit (ca. 450-500 Wörter).
        """
        # Wähle ein verfügbares Textmodell (per ListModels abgeglichen)
        # Prefer aktuell verfügbare Textmodelle (aus ListModels ersichtlich)
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
    # SCHRITT 3: SPRACH GENERIERUNG (Google Cloud TTS / "Veo"-Ersatz)
    # --------------------------------------------------------------------------
    def generate_voice(self):
        print("🗣️ 3. Generiere Stimme mit Google Neural2 (High Quality)...")

        # Setze Umgebungsvariable für Google Auth
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

        query = "lofi study beat" # Passend für "Wissen"
        url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}&category=music"
        # Hinweis: Pixabay Music API ist separat, oft nutzt man die Audio URL direkt wenn API Key vorhanden.
        # Fallback Mock für diesen Code, da Pixabay Music API Endpunkte variieren:
        # Wir laden hier exemplarisch eine freie MP3 von einer URL, wenn keine API Antwort kommt.

        # Hier simulieren wir den Download einer passenden Datei (Royalty Free)
        # In der Realität: Request an Pixabay API -> URL extrahieren -> Download
        try:
             # Beispiel: Ein generischer Royalty Free Link (Platzhalter)
             # Du musst hier die echte Logic der Pixabay Audio API einfügen
             # Documentation: https://pixabay.com/api/docs/#api_search_audio

            music_url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q=lofi&audio_type=music"
            r = requests.get(music_url)
            data = r.json()

            if data['hits']:
                download_url = data['hits'][0]['pageURL'] # Achtung: API gibt oft nur PageURL, direct link requires scraping or full access
                # FÜR DEMO ZWECKE: Wir nehmen an, wir haben eine lokale Datei "background_loop.mp3"
                # da direkte MP3 Downloads via API oft Tokens brauchen.
                if os.path.exists("assets/background_loop.mp3"):
                     self.music_path = "assets/background_loop.mp3"
                     print("   -> Lokale Musikdatei gefunden.")
                     return

            print("   -> Lade Default-Musik (Mock)...")
            # In Production: requests.get(download_url)
            self.music_path = f"{TEMP_DIR}/music.mp3"
            # Erstelle leere Datei als Platzhalter, damit Code nicht crasht, falls kein Download
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

            # Musik leiser machen (-20dB)
            music = music - 20

            # Musik loopen, falls sie kürzer ist als die Stimme
            while len(music) < len(voice) + 5000: # +5 Sek Outro Puffer
                music += music

            # Musik auf Länge der Stimme + 5 Sek trimmen
            music = music[:len(voice) + 5000]

            # Fade out Musik am Ende
            music = music.fade_out(3000)

            # Overlay (Stimme über Musik)
            final_audio = music.overlay(voice, position=1000) # Stimme startet nach 1 Sekunde
        else:
            final_audio = voice
            print("   -> Keine Musik gefunden, nutze nur Stimme.")

        # Export
        filename = f"{self.topic.replace(' ', '_')}_final.mp3"
        self.final_path = os.path.join(OUTPUT_DIR, filename)

        final_audio.export(self.final_path, format="mp3", bitrate="192k")
        print(f"✅ EPISODE FERTIG: {self.final_path}")

    # --------------------------------------------------------------------------
    # SCHRITT 6: METADATEN FÜR UPLOAD
    # --------------------------------------------------------------------------
    def generate_metadata(self):
        print("📄 6. Erstelle Metadaten für Spotify for Podcasters...")

        title = f"{PODCAST_NAME}: {self.topic} - {SLOGAN}"
        desc = f"In dieser Folge geht es um {self.topic}. \n\n{self.script_content[:100]}...\n\nGeneriert mit KI."

        meta = {
            "title": title,
            "description": desc,
            "file_path": self.final_path,
            "tags": ["Wissen", "Education", self.topic, "Shorts"]
        }

        with open(f"{OUTPUT_DIR}/{self.topic.replace(' ', '_')}_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)

        print("   -> Metadaten gespeichert. Bereit für manuellen Upload.")

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
    bot.generate_voice() # Hier wird Google Cloud TTS genutzt
    bot.fetch_music()    # Hier muss ein eigener MP3 Pfad oder gültiger API Key rein
    bot.mix_audio()
    bot.generate_metadata()

    print("\n------------------------------------------------")
    print("🎉 FERTIG! Die Datei liegt im Ordner 'fertige_episoden'.")
    print("⚠️  Nächster Schritt: Lade die MP3 und die Texte aus der JSON")
    print("    bei Spotify for Podcasters hoch.")
    print("------------------------------------------------")