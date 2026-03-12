from pathlib import Path


def _load_partial_module():
    module_path = Path(__file__).resolve().parent.parent / "podcast_generator.py"
    source = module_path.read_text(encoding="utf-8")
    marker = "# ==============================================================================\n# HAUPTPROGRAMM"
    cutoff = source.find(marker)
    if cutoff == -1:
        raise RuntimeError("main marker not found")
    partial_source = source[:cutoff]

    import os

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


class _RecordingBot:
    def __init__(self):
        self.calls = []
        self.checkpoint_updates = []
        self.cleared = []

    def _clear_checkpoint(self, quiet: bool = False):
        self.cleared.append(quiet)

    def resume_completed_steps(self, enabled: bool = True):
        self.calls.append(("resume", enabled))
        return ["trends"] if enabled else []

    def _write_checkpoint(self, current_step: str, status: str, completed_steps: list[str]):
        self.checkpoint_updates.append((current_step, status, list(completed_steps)))

    def research_trends(self):
        self.calls.append("trends")

    def generate_script(self):
        self.calls.append("skript")

    def fetch_music(self):
        self.calls.append("musik")

    def generate_voice(self):
        self.calls.append("stimme")

    def mix_audio(self):
        self.calls.append("mixing")

    def create_video(self):
        self.calls.append("video")

    def generate_metadata(self):
        self.calls.append("metadaten")


def test_execute_pipeline_skips_completed_and_clears_checkpoint(monkeypatch):
    mod = _load_partial_module()
    execute_pipeline = mod["_execute_pipeline"]

    recorded_labels = []

    def fake_run_step(label, action, spinner_after=10.0, defer_output=False):
        recorded_labels.append((label, defer_output))
        return action()

    monkeypatch.setitem(mod, "_run_step", fake_run_step)

    bot = _RecordingBot()
    execute_pipeline(bot, generate_video=False, resume_enabled=True, force_restart=False)

    assert ("resume", True) in bot.calls
    assert "trends" not in bot.calls
    assert [label for label, _ in recorded_labels] == [
        "Schritt 2/6 (Skript)",
        "Schritt 3/6 (Musik)",
        "Schritt 4/6 (Stimme)",
        "Schritt 5/6 (Mixing)",
        "Schritt 6/6 (Metadaten)",
    ]
    assert bot.cleared == [True]


def test_execute_pipeline_force_restart_clears_before_running(monkeypatch):
    mod = _load_partial_module()
    execute_pipeline = mod["_execute_pipeline"]

    monkeypatch.setitem(mod, "_run_step", lambda label, action, spinner_after=10.0, defer_output=False: action())

    bot = _RecordingBot()
    execute_pipeline(bot, generate_video=True, resume_enabled=False, force_restart=True)

    assert bot.cleared == [False, True]
    assert bot.calls[0] == ("resume", False)
    assert "video" in bot.calls
    assert any(update[0] == "video" and update[1] == "completed" for update in bot.checkpoint_updates)
