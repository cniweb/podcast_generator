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
