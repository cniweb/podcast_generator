import json
import os
from pathlib import Path

from conftest import _load_partial_module


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
    assert names == [
        "Trends",
        "Skript",
        "Musik",
        "Stimme",
        "Mixing",
        "Video",
        "Metadaten",
    ]


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

    assert (
        slugify("Coinkite Coldcard Q Hardware Wallet")
        == "Coinkite_Coldcard_Q_Hardware_Wallet"
    )
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
    Path(bot.checkpoint_path).write_text(
        json.dumps(checkpoint_payload), encoding="utf-8"
    )

    completed = bot.resume_completed_steps()

    assert completed == ["skript", "stimme", "mixing", "metadaten"]
    assert bot.transcript_path == str(script_path)
    assert bot.script_content == "Beispielskript"
    assert bot.audio_voice_path == str(voice_path)
    assert bot.final_audio_path == str(audio_path)
    assert bot.metadata_path == str(metadata_path)


def test_resume_invalid_checkpoint_is_discarded_when_artifacts_missing(tmp_path):
    mod = _load_partial_module()
    podcast_generator_cls = mod["PodcastGenerator"]

    mod["TEMP_DIR"] = str(tmp_path / "temp")
    mod["OUTPUT_DIR"] = str(tmp_path / "out")
    mod["ASSETS_DIR"] = str(tmp_path / "assets")
    os.makedirs(mod["TEMP_DIR"], exist_ok=True)
    os.makedirs(mod["OUTPUT_DIR"], exist_ok=True)
    os.makedirs(mod["ASSETS_DIR"], exist_ok=True)

    bot = podcast_generator_cls("Broken Resume")
    checkpoint_payload = {
        "topic": bot.topic,
        "topic_slug": bot.topic_slug,
        "current_step": "mixing",
        "status": "failed",
        "last_error": "voice generation failed",
        "completed_steps": ["skript", "stimme"],
        "artifacts": {},
    }
    Path(bot.checkpoint_path).write_text(
        json.dumps(checkpoint_payload), encoding="utf-8"
    )

    completed = bot.resume_completed_steps()

    assert completed == []
    assert not Path(bot.checkpoint_path).exists()


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
