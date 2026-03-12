import json
import os
import sys
from pathlib import Path


def _load_partial_module():
    module_path = Path(__file__).resolve().parent.parent / "podcast_generator.py"
    source = module_path.read_text(encoding="utf-8")
    marker = "# ==============================================================================\n# HAUPTPROGRAMM"
    cutoff = source.find(marker)
    if cutoff == -1:
        raise RuntimeError("main marker not found")
    partial_source = source[:cutoff]

    os.environ.setdefault("GEMINI_API_KEY", "test-key")
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "dummy.json")
    os.environ.setdefault("FREESOUND_API_KEY", "dummy-key")
    os.environ.setdefault("PODCAST_NAME", "Test Podcast")
    os.environ.setdefault("PODCAST_SLOGAN", "Test Slogan")
    os.environ.setdefault("PODCAST_TEMP_DIR", "temp_assets")
    os.environ.setdefault("PODCAST_OUTPUT_DIR", "finished_episodes")
    os.environ.setdefault("PODCAST_ASSETS_DIR", "assets")
    os.environ.setdefault("SCRIPT_DEFAULT_MODEL", "gemini-3.1-pro-preview")

    class _DummyModels:
        def list(self):
            return []

    class _DummyClient:
        def __init__(self, *args, **kwargs):
            self.models = _DummyModels()

    import google

    setattr(google, "genai", type("GenAIStub", (), {"Client": _DummyClient}))

    namespace = {"__name__": "podcast_generator_test"}
    exec(compile(partial_source, str(module_path), "exec"), namespace)
    return namespace


class _BotStub:
    def research_trends(self):
        return None

    def generate_script(self):
        return None

    def fetch_music(self):
        return None

    def generate_voice(self):
        return None

    def mix_audio(self):
        return None

    def create_video(self):
        return None

    def generate_metadata(self):
        return None


def test_build_step_plan_includes_video_when_enabled():
    mod = _load_partial_module()
    build_step_plan = mod["_build_step_plan"]
    plan = build_step_plan(_BotStub(), True)

    names = [entry[0] for entry in plan]
    assert names == ["Trends", "Skript", "Musik", "Stimme", "Mixing", "Video", "Metadaten"]


def test_build_step_plan_renumbers_when_video_disabled():
    mod = _load_partial_module()
    build_step_plan = mod["_build_step_plan"]
    plan = build_step_plan(_BotStub(), False)

    names = [entry[0] for entry in plan]
    assert names == ["Trends", "Skript", "Musik", "Stimme", "Mixing", "Metadaten"]
    assert len(plan) == 6


def test_slugify_filename_normalizes_topic():
    mod = _load_partial_module()
    slugify = mod["_slugify_filename"]

    assert slugify("Coinkite Coldcard Q Hardware Wallet") == "Coinkite_Coldcard_Q_Hardware_Wallet"
    assert slugify("  !!!  ") == "podcast_run"


def test_resume_completed_steps_restores_checkpoint_artifacts(tmp_path):
    mod = _load_partial_module()
    podcast_generator_cls = mod["PodcastGenerator"]

    mod["TEMP_DIR"] = str(tmp_path / "temp")
    mod["OUTPUT_DIR"] = str(tmp_path / "out")
    mod["ASSETS_DIR"] = str(tmp_path / "assets")
    os.makedirs(mod["TEMP_DIR"], exist_ok=True)
    os.makedirs(mod["OUTPUT_DIR"], exist_ok=True)
    os.makedirs(mod["ASSETS_DIR"], exist_ok=True)

    bot = podcast_generator_cls("Resume Topic")

    script_path = Path(mod["TEMP_DIR"]) / f"{bot.topic_slug}_script.txt"
    voice_path = Path(mod["TEMP_DIR"]) / f"{bot.topic_slug}_voice_raw.mp3"
    audio_path = Path(mod["OUTPUT_DIR"]) / f"{bot.topic_slug}.mp3"
    metadata_path = Path(mod["OUTPUT_DIR"]) / f"{bot.topic_slug}_meta.json"

    script_path.write_text("Beispielskript", encoding="utf-8")
    voice_path.write_bytes(b"voice")
    audio_path.write_bytes(b"audio")
    metadata_path.write_text("{}", encoding="utf-8")

    checkpoint_payload = {
        "topic": bot.topic,
        "topic_slug": bot.topic_slug,
        "current_step": "mixing",
        "status": "completed",
        "completed_steps": ["skript", "stimme", "mixing", "metadaten"],
        "artifacts": {},
    }
    Path(bot.checkpoint_path).write_text(json.dumps(checkpoint_payload), encoding="utf-8")

    completed = bot.resume_completed_steps()

    assert completed == ["skript", "stimme", "mixing", "metadaten"]
    assert bot.transcript_path == str(script_path)
    assert bot.script_content == "Beispielskript"
    assert bot.audio_voice_path == str(voice_path)
    assert bot.final_audio_path == str(audio_path)
    assert bot.metadata_path == str(metadata_path)


def test_parse_cli_args_supports_resume_and_force_restart_flags():
    mod = _load_partial_module()
    parse_cli_args = mod["_parse_cli_args"]

    args = parse_cli_args(["--resume", "Mein Thema"])
    assert args.resume is True
    assert args.force_restart is False
    assert args.topic == "Mein Thema"

    args = parse_cli_args(["--force-restart"])
    assert args.resume is False
    assert args.force_restart is True
    assert args.topic is None


def test_configure_logger_adds_single_console_handler():
    mod = _load_partial_module()
    logger = mod["LOGGER"]
    configure_logger = mod["_configure_logger"]

    handler_count = len(logger.handlers)
    configure_logger()

    assert len(logger.handlers) == handler_count
