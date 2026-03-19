import argparse
import logging
import os
import builtins
import requests
import json
import subprocess
import re
import io
import math
import mimetypes
import sys
import threading
import time
import xml.etree.ElementTree as ET
import shutil
import concurrent.futures
from contextlib import contextmanager
from pytrends.request import TrendReq
from google import genai
from google.genai import types
from google.cloud import texttospeech
from pydub import AudioSegment
from dotenv import load_dotenv
from typing import Callable, List

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


_PRINT_LOCK = threading.Lock()
_ACTIVE_SPINNER = None
_SPINNER_LINE_ACTIVE = False
_SPINNER_DEFER_OUTPUT = False
_DEFERRED_STDOUT_PRINTS: list[tuple[tuple, dict]] = []
LOGGER = logging.getLogger("podcast_generator")


def _safe_print(*args, **kwargs):
    """Stellt sicher, dass Log-Zeilen nicht in Spinner-Zeilen geschrieben werden."""
    global _SPINNER_LINE_ACTIVE
    with _PRINT_LOCK:
        file_target = kwargs.get("file", sys.stdout)
        if _SPINNER_DEFER_OUTPUT and file_target is sys.stdout:
            _DEFERRED_STDOUT_PRINTS.append((args, dict(kwargs)))
            return
        if _SPINNER_LINE_ACTIVE:
            builtins.print("", file=sys.stderr, flush=True)
            _SPINNER_LINE_ACTIVE = False
        builtins.print(*args, **kwargs)


print = _safe_print


class _ConsoleLogHandler(logging.Handler):
    """Leitet Logging durch die spinner-sichere Konsolenausgabe."""

    def emit(self, record: logging.LogRecord):
        message = self.format(record)
        target = sys.stderr if record.levelno >= logging.WARNING else sys.stdout
        _safe_print(message, file=target)


def _configure_logger():
    if LOGGER.handlers:
        return
    handler = _ConsoleLogHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False


def log_info(message: str):
    LOGGER.info(message)


def log_warning(message: str):
    LOGGER.warning(message)


def log_error(message: str):
    LOGGER.error(message)


_configure_logger()


class ResumeConsistencyError(RuntimeError):
    """Checkpoint verweist auf unvollstaendige oder fehlende Artefakte."""


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
SCRIPT_DEFAULT_MODEL = _require_env("SCRIPT_DEFAULT_MODEL")
TTS_DEFAULT_MODEL = os.getenv("TTS_DEFAULT_MODEL", "gemini-2.5-pro-preview-tts").strip()
TTS_FALLBACK_MODELS = os.getenv(
    "TTS_FALLBACK_MODELS",
    "gemini-2.5-flash-preview-tts",
)
TTS_VOICE_NAME = os.getenv("TTS_VOICE_NAME", "umbriel").strip()
GENERATE_VIDEO = os.getenv("GENERATE_VIDEO", "true").strip().lower() in {"1", "true", "yes", "on"}

# Ordner erstellen
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Client-Setup
client = genai.Client(api_key=GEMINI_API_KEY)

# Standard-Modell für Fallbacks
DEFAULT_MODEL = SCRIPT_DEFAULT_MODEL

# Skript-Constraints
SCRIPT_TARGET_WORDS = 700
SCRIPT_MIN_WORDS = 650
SCRIPT_MAX_WORDS = 800
SCRIPT_MIN_PARAGRAPHS = 5
SCRIPT_EXPECTED_PARAGRAPHS = 5
_MODEL_NAMES_CACHE: set[str] | None = None
HTTP_TIMEOUT_SECONDS = 20
HTTP_RETRY_ATTEMPTS = 3
GEMINI_RETRY_ATTEMPTS = 3
GEMINI_RETRY_BASE_DELAY = 2


def _parse_csv_models(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _slugify_filename(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return slug.strip("_") or "podcast_run"


def _retry_delay(attempt: int, base_delay: float = 2.0) -> float:
    return base_delay * (2 ** (attempt - 1))


def _request_with_retry(url: str, **kwargs) -> requests.Response:
    timeout = kwargs.pop("timeout", HTTP_TIMEOUT_SECONDS)
    last_error: Exception | None = None
    for attempt in range(1, HTTP_RETRY_ATTEMPTS + 1):
        try:
            response = requests.get(url, timeout=timeout, **kwargs)
            if response.status_code >= 500 or response.status_code == 429:
                raise RuntimeError(f"HTTP {response.status_code}")
            return response
        except Exception as exc:
            last_error = exc
            if attempt == HTTP_RETRY_ATTEMPTS:
                break
            delay = _retry_delay(attempt, 1.5)
            log_warning(f"   ⚠️ HTTP-Versuch {attempt}/{HTTP_RETRY_ATTEMPTS} fehlgeschlagen ({exc}), warte {delay:.1f}s...")
            time.sleep(delay)
    raise RuntimeError(f"HTTP-Anfrage fehlgeschlagen: {last_error}")


def _gemini_generate_content_with_retry(*, model: str, contents, config=None):
    last_error: Exception | None = None
    for attempt in range(1, GEMINI_RETRY_ATTEMPTS + 1):
        try:
            if config is None:
                return client.models.generate_content(model=model, contents=contents)
            return client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as exc:
            last_error = exc
            retryable = _is_rate_limited_error(exc) or "timeout" in str(exc).lower() or "503" in str(exc)
            if not retryable or attempt == GEMINI_RETRY_ATTEMPTS:
                break
            delay = _retry_delay(attempt, GEMINI_RETRY_BASE_DELAY)
            log_warning(
                f"   ⚠️ Gemini-Versuch {attempt}/{GEMINI_RETRY_ATTEMPTS} fuer Modell {model} fehlgeschlagen ({exc}), warte {delay:.1f}s..."
            )
            time.sleep(delay)
    raise RuntimeError(f"Gemini-Aufruf fehlgeschlagen ({model}): {last_error}")


def _tts_model_preferences() -> list[str]:
    ordered: list[str] = []
    for model in [TTS_DEFAULT_MODEL, *_parse_csv_models(TTS_FALLBACK_MODELS)]:
        if model and model not in ordered:
            ordered.append(model)
    if not ordered:
        ordered = ["gemini-2.5-flash-preview-tts", "gemini-2.5-pro-preview-tts"]
    return ordered


def _normalize_model_name(model_name: str) -> str:
    return (model_name or "").replace("models/", "").strip()


def _discover_model_names() -> set[str]:
    """Liest verfügbare Modellnamen einmalig aus und cached sie."""
    global _MODEL_NAMES_CACHE
    if _MODEL_NAMES_CACHE is not None:
        return _MODEL_NAMES_CACHE

    try:
        discovered: set[str] = set()
        for model in client.models.list():
            short = _normalize_model_name(getattr(model, "name", ""))
            if short:
                discovered.add(short)
        _MODEL_NAMES_CACHE = discovered
        return discovered
    except Exception as e:
        log_warning(f"   ⚠️ Model Discovery fehlgeschlagen ({e}).")
        _MODEL_NAMES_CACHE = set()
        return _MODEL_NAMES_CACHE


def _discover_script_models() -> set[str]:
    blocked_tokens = {"embedding", "tts", "image", "imagen", "veo", "computer-use", "robotics", "aqa", "native-audio"}
    candidates: set[str] = set()
    for model in _discover_model_names():
        if any(tok in model for tok in blocked_tokens):
            continue
        candidates.add(model)
    return candidates


def _resolve_script_model(preferences: List[str]) -> str:
    """Wählt ein verfügbares Script-Modell gemäß Präferenzliste."""
    cleaned = [_normalize_model_name(m) for m in preferences if _normalize_model_name(m)]
    available = _discover_script_models()

    if not available:
        fallback = cleaned[0] if cleaned else DEFAULT_MODEL
        log_warning(f"   ⚠️ Keine Script-Modelle discoverbar. Nutze Fallback: {fallback}")
        return fallback

    for pref in cleaned:
        if pref in available:
            return pref

    gemini_candidates = sorted(m for m in available if "gemini" in m)
    fallback = gemini_candidates[0] if gemini_candidates else (cleaned[0] if cleaned else DEFAULT_MODEL)
    log_warning(f"   ⚠️ Kein bevorzugtes Script-Modell verfügbar. Nutze Discovery-Fallback: {fallback}")
    return fallback


def _discover_tts_models() -> set[str]:
    """Liest verfügbare TTS-Modelle aus der Gemini API aus."""
    discovered: set[str] = set()
    for model in _discover_model_names():
        if "tts" in model.lower():
            discovered.add(model)
    if not discovered:
        log_warning("   ⚠️ Keine TTS-Modelle discoverbar. Nutze konfigurierte TTS-Modelle.")
    return discovered


def _resolve_tts_models(preferences: list[str]) -> list[str]:
    """Filtert bevorzugte Modelle auf tatsächlich verfügbare TTS-Modelle."""
    cleaned = [_normalize_model_name(m) for m in preferences if _normalize_model_name(m)]
    available = _discover_tts_models()
    if not available:
        return cleaned

    resolved = [m for m in cleaned if m in available]
    dropped = [m for m in cleaned if m not in available]
    if dropped:
        log_warning(f"   ⚠️ Nicht verfügbare TTS-Modelle übersprungen: {', '.join(dropped)}")
    if resolved:
        return resolved

    discovered = sorted(available)
    log_warning(f"   ⚠️ Kein konfiguriertes TTS-Modell verfügbar. Nutze Discovery-Fallback: {', '.join(discovered)}")
    return discovered


def _is_rate_limited_error(err: Exception | str) -> bool:
    msg = str(err).lower()
    if "requests_per_model_per_day" in msg or "quota exceeded" in msg:
        return False
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


class _AsciiDotsSpinner:
    """Einfacher ASCII-Spinner für lange Schritte in der Konsole."""

    def __init__(self, label: str, interval: float = 0.35, start_after: float = 0.0, defer_stdout: bool = False):
        self.label = label
        self.interval = interval
        self.start_after = start_after
        self.defer_stdout = defer_stdout
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._enabled = sys.stdout.isatty()
        self._shown = False

    def start(self):
        global _ACTIVE_SPINNER, _SPINNER_DEFER_OUTPUT
        if not self._enabled:
            return
        self._stop_event.clear()
        with _PRINT_LOCK:
            _ACTIVE_SPINNER = self
            _SPINNER_DEFER_OUTPUT = False
            _DEFERRED_STDOUT_PRINTS.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        global _SPINNER_LINE_ACTIVE, _SPINNER_DEFER_OUTPUT
        if self.start_after > 0 and self._stop_event.wait(self.start_after):
            return
        tick = 0
        while not self._stop_event.is_set():
            self._shown = True
            dots = "." * ((tick % 3) + 1)
            with _PRINT_LOCK:
                builtins.print(f"\r   {self.label} {dots:<3}", end="", flush=True, file=sys.stderr)
                _SPINNER_LINE_ACTIVE = True
                _SPINNER_DEFER_OUTPUT = self.defer_stdout
            tick += 1
            self._stop_event.wait(self.interval)

    def stop(self, status: str = "abgeschlossen"):
        global _ACTIVE_SPINNER, _SPINNER_LINE_ACTIVE, _SPINNER_DEFER_OUTPUT
        if not self._enabled:
            return
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
        with _PRINT_LOCK:
            if self._shown:
                builtins.print("\r", end="", file=sys.stderr, flush=True)
                builtins.print(f"   {self.label} ... {status}", file=sys.stderr, flush=True)
            _SPINNER_DEFER_OUTPUT = False
            _ACTIVE_SPINNER = None
            _SPINNER_LINE_ACTIVE = False
            for args, kwargs in _DEFERRED_STDOUT_PRINTS:
                builtins.print(*args, **kwargs)
            _DEFERRED_STDOUT_PRINTS.clear()


@contextmanager
def _with_spinner(label: str, start_after: float = 0.0, defer_stdout: bool = False):
    spinner = _AsciiDotsSpinner(label, start_after=start_after, defer_stdout=defer_stdout)
    spinner.start()
    try:
        yield
    finally:
        spinner.stop("abgeschlossen")


def _run_step(step_label: str, action: Callable[[], object], spinner_after: float = 10.0, defer_output: bool = False):
    with _with_spinner(f"{step_label} läuft", start_after=spinner_after, defer_stdout=defer_output):
        result = action()
    log_info(f"✅ {step_label} erfolgreich abgeschlossen.")
    return result


def _build_step_plan(bot: "PodcastGenerator", generate_video: bool) -> list[tuple[str, Callable[[], object], bool]]:
    """Erzeugt den dynamischen Ausführungsplan inkl. optionalem Videoschritt."""
    plan: list[tuple[str, Callable[[], object], bool]] = [
        ("Trends", bot.research_trends, False),
        ("Skript", bot.generate_script, True),
        ("Musik", bot.fetch_music, True),
        ("Stimme", bot.generate_voice, True),
        ("Mixing", bot.mix_audio, False),
    ]
    if generate_video:
        plan.append(("Video", bot.create_video, False))
    plan.append(("Metadaten", bot.generate_metadata, True))
    return plan


def _step_key(step_name: str) -> str:
    return step_name.strip().lower()


def _execute_pipeline(
    bot: "PodcastGenerator",
    generate_video: bool,
    resume_enabled: bool = False,
    force_restart: bool = False,
):
    if force_restart:
        bot._clear_checkpoint()
    completed_steps = bot.resume_completed_steps(enabled=resume_enabled)

    step_plan = _build_step_plan(bot, generate_video)
    total_steps = len(step_plan)
    for idx, (step_name, step_action, defer_output) in enumerate(step_plan, start=1):
        step_key = _step_key(step_name)
        step_label = f"Schritt {idx}/{total_steps} ({step_name})"
        if step_key in completed_steps:
            log_info(f"⏭️ {step_label} bereits abgeschlossen. Überspringe.")
            continue
        bot._write_checkpoint(step_key, "running", completed_steps)
        try:
            _run_step(step_label, step_action, defer_output=defer_output)
        except Exception as exc:
            bot._write_checkpoint_error(step_key, completed_steps, exc)
            raise
        completed_steps.append(step_key)
        bot._write_checkpoint(step_key, "completed", completed_steps)

    if not generate_video:
        log_info("⏭️ Videoschritt deaktiviert (GENERATE_VIDEO=false).")

    bot._clear_checkpoint(quiet=True)


def _artifact_path_or_none(path: str) -> str | None:
    return path or None


def _file_size_or_zero(path: str) -> int:
    if not path or not os.path.exists(path):
        return 0
    return os.path.getsize(path)


def _format_subprocess_error(cmd: list[str], exc: subprocess.CalledProcessError | Exception) -> str:
    command_str = " ".join(cmd)
    if isinstance(exc, subprocess.CalledProcessError):
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        output = stderr.strip() or stdout.strip()
        details = output[-800:] if output else "keine weitere Ausgabe"
        return (
            f"Subprocess fehlgeschlagen (exit={exc.returncode}). "
            f"Kommando: {command_str}. Details: {details}"
        )
    return f"Subprocess fehlgeschlagen. Kommando: {command_str}. Fehler: {exc}"


def _parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Podcast-Generator starten")
    parser.add_argument("topic", nargs="?", help="Podcast-Thema; leer = Trend-Fallback")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="setzt einen vorhandenen Checkpoint fuer dasselbe Thema fort",
    )
    parser.add_argument(
        "--force-restart",
        action="store_true",
        help="ignoriert vorhandene Checkpoints und startet komplett neu",
    )
    return parser.parse_args(argv)


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
    return _resolve_script_model(preferences)

class PodcastGenerator:
    def __init__(self, topic):
        """Kapselt den End-to-End-Podcast-Flow für ein bestimmtes Thema."""
        self.topic = topic
        self.topic_slug = _slugify_filename(topic.replace(" ", "_"))
        self.script_content = ""
        self.audio_voice_path = ""
        self.music_path = ""
        self.final_audio_path = ""
        self.final_video_path = ""
        self.metadata_path = ""
        self.run_manifest_path = ""
        self.sources = []
        self.transcript_path = ""
        self.checkpoint_path = os.path.join(TEMP_DIR, f"{self.topic_slug}_checkpoint.json")
        print(f"🚀 Starte Produktion für Thema: '{topic}'\n")

    def write_run_manifest(
        self,
        *,
        started_at: float,
        finished_at: float,
        generate_video: bool,
        resume_enabled: bool,
        force_restart: bool,
        status: str,
        error: str | None = None,
    ):
        manifest_path = os.path.join(OUTPUT_DIR, f"{self.topic_slug}_run.json")
        payload = {
            "topic": self.topic,
            "topic_slug": self.topic_slug,
            "podcast_name": PODCAST_NAME,
            "status": status,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": round(max(0.0, finished_at - started_at), 2),
            "options": {
                "generate_video": generate_video,
                "resume_enabled": resume_enabled,
                "force_restart": force_restart,
            },
            "models": {
                "script_default": SCRIPT_DEFAULT_MODEL,
                "tts_default": TTS_DEFAULT_MODEL,
                "tts_fallbacks": _parse_csv_models(TTS_FALLBACK_MODELS),
                "tts_voice": TTS_VOICE_NAME,
            },
            "artifacts": {
                "audio": _artifact_path_or_none(self.final_audio_path),
                "video": _artifact_path_or_none(self.final_video_path),
                "script": _artifact_path_or_none(self.transcript_path),
                "metadata": _artifact_path_or_none(self.metadata_path),
                "checkpoint": _artifact_path_or_none(self.checkpoint_path if os.path.exists(self.checkpoint_path) else ""),
            },
            "sources": self.sources,
            "error": error,
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        self.run_manifest_path = manifest_path
        log_info(f"   -> Run-Manifest gespeichert: {manifest_path}")

    def validate_outputs(self, generate_video: bool):
        issues: list[str] = []

        if not self.final_audio_path or not os.path.exists(self.final_audio_path):
            issues.append("Finale Audio-Datei fehlt")
        elif _file_size_or_zero(self.final_audio_path) == 0:
            issues.append("Finale Audio-Datei ist leer")
        else:
            try:
                audio = AudioSegment.from_mp3(self.final_audio_path)
                if len(audio) < 30_000:
                    issues.append("Finale Audio-Datei ist kuerzer als 30 Sekunden")
            except Exception as exc:
                issues.append(f"Finale Audio-Datei konnte nicht gelesen werden: {exc}")

        if not self.audio_voice_path or not os.path.exists(self.audio_voice_path):
            issues.append("Stimmen-Datei fehlt")

        if not self.metadata_path or not os.path.exists(self.metadata_path):
            issues.append("Metadaten-Datei fehlt")

        transcript_output = os.path.join(OUTPUT_DIR, f"{self.topic_slug}_transcription.txt")
        if not os.path.exists(transcript_output):
            issues.append("Transkript-Datei fehlt")

        if generate_video:
            if not self.final_video_path or not os.path.exists(self.final_video_path):
                issues.append("Video-Datei fehlt")
            elif _file_size_or_zero(self.final_video_path) == 0:
                issues.append("Video-Datei ist leer")

        if issues:
            raise RuntimeError("Output-QA fehlgeschlagen: " + "; ".join(issues))

        log_info("🔎 Output-QA erfolgreich: Audio, Metadaten und optionale Artefakte sind plausibel.")

    def _write_checkpoint(self, current_step: str, status: str, completed_steps: list[str]):
        payload = {
            "topic": self.topic,
            "topic_slug": self.topic_slug,
            "current_step": current_step,
            "status": status,
            "updated_at": time.time(),
            "last_error": None,
            "completed_steps": completed_steps,
            "artifacts": {
                "script": self.transcript_path,
                "voice": self.audio_voice_path,
                "music": self.music_path,
                "audio": self.final_audio_path,
                "video": self.final_video_path,
                "metadata": self.metadata_path,
            },
        }
        with open(self.checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _write_checkpoint_error(self, current_step: str, completed_steps: list[str], error: Exception):
        payload = {
            "topic": self.topic,
            "topic_slug": self.topic_slug,
            "current_step": current_step,
            "status": "failed",
            "updated_at": time.time(),
            "last_error": str(error),
            "completed_steps": completed_steps,
            "artifacts": {
                "script": self.transcript_path,
                "voice": self.audio_voice_path,
                "music": self.music_path,
                "audio": self.final_audio_path,
                "video": self.final_video_path,
                "metadata": self.metadata_path,
            },
        }
        with open(self.checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _load_checkpoint(self) -> dict | None:
        if not os.path.exists(self.checkpoint_path):
            return None
        try:
            with open(self.checkpoint_path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("topic") != self.topic:
                return None
            return data
        except Exception as e:
            print(f"   ⚠️ Checkpoint konnte nicht geladen werden: {e}")
            return None

    def _clear_checkpoint(self, quiet: bool = False):
        if os.path.exists(self.checkpoint_path):
            os.remove(self.checkpoint_path)
            if not quiet:
                print("🧹 Vorhandener Checkpoint verworfen. Starte komplett neu.")

    def _restore_from_checkpoint(self, completed_steps: list[str]):
        if "skript" in completed_steps and not self.transcript_path:
            script_path = os.path.join(TEMP_DIR, f"{self.topic_slug}_script.txt")
            if os.path.exists(script_path):
                with open(script_path, encoding="utf-8") as f:
                    self.script_content = f.read()
                self.transcript_path = script_path

        if "musik" in completed_steps and not self.music_path:
            for candidate in (
                os.path.join(ASSETS_DIR, "background_loop.mp3"),
                os.path.join(TEMP_DIR, f"{self.topic_slug}_music_download.mp3"),
                os.path.join(TEMP_DIR, f"{self.topic_slug}_silence.mp3"),
            ):
                if os.path.exists(candidate):
                    self.music_path = candidate
                    break

        if "stimme" in completed_steps and not self.audio_voice_path:
            voice_path = os.path.join(TEMP_DIR, f"{self.topic_slug}_voice_raw.mp3")
            if os.path.exists(voice_path):
                self.audio_voice_path = voice_path

        if "mixing" in completed_steps and not self.final_audio_path:
            audio_path = os.path.join(OUTPUT_DIR, f"{self.topic_slug}.mp3")
            if os.path.exists(audio_path):
                self.final_audio_path = audio_path

        if "video" in completed_steps and not self.final_video_path:
            video_path = os.path.join(OUTPUT_DIR, f"{self.topic_slug}_video.mp4")
            if os.path.exists(video_path):
                self.final_video_path = video_path

        if "metadaten" in completed_steps and not self.metadata_path:
            metadata_path = os.path.join(OUTPUT_DIR, f"{self.topic_slug}_meta.json")
            if os.path.exists(metadata_path):
                self.metadata_path = metadata_path

    def _validate_resume_state(self, completed_steps: list[str]):
        required_artifacts = {
            "skript": [(self.transcript_path, "Script-Datei")],
            "musik": [(self.music_path, "Musik-Datei")],
            "stimme": [(self.audio_voice_path, "Stimmen-Datei")],
            "mixing": [(self.final_audio_path, "Finale Audio-Datei")],
            "video": [(self.final_video_path, "Video-Datei")],
            "metadaten": [
                (self.metadata_path, "Metadaten-Datei"),
                (self.transcript_path or os.path.join(OUTPUT_DIR, f"{self.topic_slug}_transcription.txt"), "Transkript-Datei"),
            ],
        }
        missing: list[str] = []
        for step in completed_steps:
            for path, label in required_artifacts.get(step, []):
                if not path or not os.path.exists(path):
                    missing.append(f"{label} fehlt fuer Schritt '{step}'")
        if missing:
            raise ResumeConsistencyError("; ".join(missing))

    def resume_completed_steps(self, enabled: bool = True) -> list[str]:
        if not enabled:
            return []
        checkpoint = self._load_checkpoint()
        if not checkpoint:
            return []
        completed_steps = checkpoint.get("completed_steps", [])
        try:
            self._restore_from_checkpoint(completed_steps)
            self._validate_resume_state(completed_steps)
        except ResumeConsistencyError as exc:
            log_warning(f"   ⚠️ Resume-Checkpoint unbrauchbar: {exc}. Starte neu.")
            self._clear_checkpoint(quiet=True)
            return []
        if checkpoint.get("last_error"):
            log_warning(f"   ⚠️ Letzter Fehler im Checkpoint: {checkpoint['last_error']}")
        log_info(f"↩️ Checkpoint gefunden. Überspringe bereits abgeschlossene Schritte: {', '.join(completed_steps)}")
        return completed_steps

    def _translate_topic_to_en(self, topic: str) -> str:
        """Übersetzt das Thema knapp ins Englische, falls Freesound-Suche hilft."""
        prompt = (
            "Translate the following topic into concise English keywords for a music search. "
            "Return a short phrase (max 4 words) without quotes or explanations: "
            f"{topic}"
        )
        try:
            resp = _gemini_generate_content_with_retry(model=DEFAULT_MODEL, contents=prompt)
            translated = (resp.text or "").strip().replace("\n", " ")
            return translated or topic
        except Exception as exc:
            print(f"   ⚠️ Übersetzung fehlgeschlagen, nutze Original: {exc}")
            return topic

    def _generate_episode_metadata(self) -> tuple[str, str]:
        """Erstellt Titel und Beschreibung basierend auf dem Transkript."""
        preferences = [
            "gemini-3.1-pro-preview",
            "gemini-3-pro-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            DEFAULT_MODEL,
            "gemini-pro-latest",
        ]
        model_name = pick_available_model(preferences)

        prompt = (
            "Du erstellst Veröffentlichungs-Texte für creators.spotify.com. "
            f"Podcast: {PODCAST_NAME}; Slogan: {SLOGAN}; Thema: {self.topic}. "
            "Nutze das Transkript unten, aber fasse dich kurz und präzise. "
            "Constraints: title <= 200 Zeichen, deutsch, ohne Anführungszeichen, kein Hashtag. "
            "Description <= 4000 Zeichen, deutsch, 2-4 Sätze Zusammenfassung + Call-to-Action zum Folgen/Bewerten; keine Listen, keine Quotes. "
            "Transkript:\n" + self.script_content
        )

        try:
            from pydantic import BaseModel, Field

            class EpisodeMetadata(BaseModel):
                title: str = Field(description="The title of the episode (max 200 chars).")
                description: str = Field(description="The description of the episode (max 4000 chars).")

            cfg = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EpisodeMetadata,
                temperature=0.7,
            )

            resp = _gemini_generate_content_with_retry(model=model_name, contents=prompt, config=cfg)
            raw = resp.text or ""

            data = json.loads(raw)
            title = str(data.get("title", "")).strip()
            desc = str(data.get("description", "")).strip()
        except Exception as e:
            print(f"   ⚠️ Konnte Episode-Metadaten nicht parsen, nutze Fallback ({e}).")
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
        system_instruction = f"Du bist Redakteur und Podcast-Host des preisgekrönten Podcasts '{PODCAST_NAME}'. Slogan: '{SLOGAN}'."
        
        prompt = f"""Schreibe ein Podcast-Skript zum Thema '{self.topic}'.

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
            "Überarbeite den folgenden Text STRIKT nach diesen Regeln:\n"
            "• {min_words}-{max_words} Wörter (NICHT MEHR!)\n"
            "• GENAU 5 ABSÄTZE\n"
            "• Kurze, knappe Sätze\n"
            "• KEINE Labels/Musik/Aufzählungen\n"
            "• ENDE: QUELLEN: url1; url2; url3\n\n"
            "Zu überarbeitender Text:\n{draft}"
        ).format(
            min_words=SCRIPT_MIN_WORDS,
            max_words=SCRIPT_MAX_WORDS,
            draft="{draft}",
        )
        
        preferred = [
            "gemini-3.1-pro-preview",
            "gemini-3-pro-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            DEFAULT_MODEL,
            "gemini-pro-latest",
        ]
        model_name = pick_available_model(preferred)
        print(f"   -> Verwende Modell: {model_name}")

        try:
            cfg = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )

            attempts = 3
            last_errors: list[str] = []
            raw_text = ""
            for attempt in range(1, attempts + 1):
                if attempt == 1:
                    response = _gemini_generate_content_with_retry(model=model_name, contents=prompt, config=cfg)
                else:
                    print(f"   ⚠️  Skript verletzt Constraints. Versuch {attempt}/{attempts}...")
                    response = _gemini_generate_content_with_retry(
                        model=model_name,
                        contents=fixup_prompt.format(draft=raw_text),
                        config=cfg
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

            self.transcript_path = os.path.join(TEMP_DIR, f"{self.topic_slug}_script.txt")
            with open(self.transcript_path, "w", encoding="utf-8") as f:
                f.write(self.script_content)

            print("   -> Skript generiert.")
        except Exception as e:
            raise RuntimeError(f"Gemini API Fehler: {e}")

    def _repair_paragraph_structure(self, text: str) -> tuple[str, dict]:
        """Versucht, Text in GENAU 5 Absätze zu reorganisieren."""
        from utils import _count_words
        
        # Extrahiere alle nicht-leeren Zeilen
        lines = [line for line in text.splitlines() if line.strip()]
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
                resp = _request_with_retry(url, params=params)
                data = resp.json()
                if data.get("results"):
                    track = data["results"][0]
                    track_id = track["id"]
                    detail_url = f"https://freesound.org/apiv2/sounds/{track_id}/"
                    d_r = _request_with_retry(detail_url, params={"token": FREESOUND_API_KEY})
                    track_details = d_r.json()
                    preview_url = track_details["previews"]["preview-hq-mp3"]
                    print(f"   -> Lade herunter: {track['name']}")
                    mp3_r = _request_with_retry(preview_url)
                    self.music_path = os.path.join(TEMP_DIR, f"{self.topic_slug}_music_download.mp3")
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
            self.music_path = os.path.join(TEMP_DIR, f"{self.topic_slug}_silence.mp3")
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

        tts_models = _resolve_tts_models(_tts_model_preferences())
        voice_name = TTS_VOICE_NAME or "umbriel"
        print(f"   -> Verwende TTS-Modelle: {', '.join(tts_models)} (Stimme: {voice_name})")

        chunks = _chunk_text(self.script_content)
        print(f"   -> Verarbeite {len(chunks)} Text-Abschnitte...")

        segments = self._tts_segments(chunks, tts_models, voice_name)

        # Remove any Nones in case something went terribly wrong
        valid_segments = [s for s in segments if s is not None]

        if not valid_segments:
            raise RuntimeError("TTS lieferte keine Segmente.")

        final_voice = valid_segments[0]
        for seg in valid_segments[1:]:
            final_voice = final_voice.append(seg, crossfade=100)

        self.audio_voice_path = os.path.join(TEMP_DIR, f"{self.topic_slug}_voice_raw.mp3")
        final_voice.export(self.audio_voice_path, format="mp3")
        print("   -> Sprachdatei erstellt.")

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        if "requests_per_model_per_day" in msg or "quota exceeded" in msg:
            return False
        return (
            "429" in msg
            or "resource_exhausted" in msg
            or "too many requests" in msg
        )

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
            temperature=0.3,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            ),
        )

        resp = _gemini_generate_content_with_retry(model=model_tts, contents=[content], config=cfg)
        for cand_idx, cand in enumerate(resp.candidates or []):
            if not cand.content:
                print(f"   ⚠️ Leerer Content in Candidate {cand_idx} (Grund: {getattr(cand, 'finish_reason', 'Unbekannt')})")
                continue
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
            name="de-DE-Journey-D",
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

    def _tts_segments(self, chunks, tts_models, voice_name):
        segments = [None] * len(chunks)

        def _process_single(idx, chunk):
            gem_err: Exception | None = None
            for model_tts in tts_models:
                try:
                    seg = self._process_chunk(idx, chunk, model_tts, voice_name)
                    print(f"   ✅ Chunk {idx + 1}/{len(chunks)} fertig ({model_tts})")
                    return idx, seg
                except Exception as err:
                    gem_err = err
                    print(f"   ⚠️ Modell-Fallback: {model_tts} fehlgeschlagen (Chunk {idx}): {err}")

            try:
                print(f"      -> Nutze Cloud TTS mit SSML für Chunk {idx}...")
                seg = self._generate_chunk_with_gcloud(idx, chunk)
                print(f"   ✅ Chunk {idx + 1}/{len(chunks)} fertig (Cloud TTS)")
                return idx, seg
            except Exception as gc_err:
                print(f"   ❌ Google Cloud TTS Fehler (Fallback) bei Chunk {idx}: {gc_err}")
                raise gem_err or gc_err

        # Verarbeite maximal 3 Chunks gleichzeitig (schont API-Rate-Limits)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(_process_single, i, chunk) for i, chunk in enumerate(chunks)]
            for future in concurrent.futures.as_completed(futures):
                idx, seg = future.result()
                segments[idx] = seg

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

        filename = f"{self.topic_slug}.mp3"
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

        video_filename = f"{self.topic_slug}_video.mp4"
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
            subprocess.run(cmd, capture_output=True, check=True)
            print(f"   -> Video fertig: {self.final_video_path}")
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                _format_subprocess_error(cmd, exc)
                + " | Hinweis: Pruefe Cover-Datei, ffmpeg-Installation und Audio-Eingabedatei."
            ) from exc
        except Exception as exc:
            raise RuntimeError(_format_subprocess_error(cmd, exc)) from exc

    # --------------------------------------------------------------------------
    # 7. METADATEN
    # --------------------------------------------------------------------------
    def generate_metadata(self, include_media: bool = True):
        """Speichert Transkript, Titel/Beschreibung und Pfade zu Audio/Video."""
        print("📄 7. Metadaten...")
        transcription_output_path = os.path.join(
            OUTPUT_DIR, f"{self.topic_slug}_transcription.txt"
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
        meta_output_path = os.path.join(OUTPUT_DIR, f"{self.topic_slug}_meta.json")
        with open(meta_output_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=4)
        self.metadata_path = meta_output_path
        print(f"   -> Transkript gespeichert: {transcription_output_path}")
        print(f"   -> Metadaten gespeichert: {meta_output_path}")

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
        resp = _request_with_retry(url, headers=headers, timeout=10)
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
    args = _parse_cli_args()
    if args.resume and args.force_restart:
        raise RuntimeError("--resume und --force-restart koennen nicht gleichzeitig genutzt werden.")

    run_started_at = time.time()

    print(f"--- {PODCAST_NAME.upper()} AUTOMATISIERUNG ---")
    _ensure_audio_tools()
    topic = (args.topic or "").strip()
    if topic:
        print(f"Thema aus CLI: '{topic}'")
        print()
    else:
        topic = input("Thema (Lass leer für aktuellen Top-Trend): ").strip()
        if topic and not sys.stdin.isatty():
            print()

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
    run_error: str | None = None
    try:
        _execute_pipeline(bot, GENERATE_VIDEO, resume_enabled=args.resume, force_restart=args.force_restart)
        bot.validate_outputs(GENERATE_VIDEO)
    except Exception as exc:
        run_error = str(exc)
        bot.write_run_manifest(
            started_at=run_started_at,
            finished_at=time.time(),
            generate_video=GENERATE_VIDEO,
            resume_enabled=args.resume,
            force_restart=args.force_restart,
            status="failed",
            error=run_error,
        )
        raise

    bot.write_run_manifest(
        started_at=run_started_at,
        finished_at=time.time(),
        generate_video=GENERATE_VIDEO,
        resume_enabled=args.resume,
        force_restart=args.force_restart,
        status="completed",
    )
    
    print("\n✅ ALLES ERLEDIGT!")
