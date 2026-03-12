import json
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


def test_execute_pipeline_writes_failed_checkpoint_on_step_error(monkeypatch):
    mod = _load_partial_module()
    execute_pipeline = mod["_execute_pipeline"]

    class _FailingBot(_RecordingBot):
        def __init__(self):
            super().__init__()
            self.failed = []

        def _write_checkpoint_error(self, current_step: str, completed_steps: list[str], error: Exception):
            self.failed.append((current_step, list(completed_steps), str(error)))

        def generate_script(self):
            raise RuntimeError("script boom")

    monkeypatch.setitem(mod, "_run_step", lambda label, action, spinner_after=10.0, defer_output=False: action())

    bot = _FailingBot()

    try:
        execute_pipeline(bot, generate_video=False, resume_enabled=False, force_restart=False)
    except RuntimeError as exc:
        assert str(exc) == "script boom"
    else:
        raise AssertionError("pipeline should have raised")

    assert bot.failed == [("skript", ["trends"], "script boom")]


def test_request_with_retry_retries_until_success(monkeypatch):
    mod = _load_partial_module()
    request_with_retry = mod["_request_with_retry"]

    attempts = {"count": 0}

    class _Resp:
        def __init__(self, status_code):
            self.status_code = status_code

    def fake_get(url, timeout=0, **kwargs):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary network issue")
        return _Resp(200)

    monkeypatch.setattr(mod["requests"], "get", fake_get)
    monkeypatch.setattr(mod["time"], "sleep", lambda *_args: None)

    response = request_with_retry("https://example.com")

    assert response.status_code == 200
    assert attempts["count"] == 3


def test_request_with_retry_raises_after_exhausting_retryable_http_status(monkeypatch):
    mod = _load_partial_module()
    request_with_retry = mod["_request_with_retry"]

    attempts = {"count": 0}

    class _Resp:
        def __init__(self, status_code):
            self.status_code = status_code

    def fake_get(url, timeout=0, **kwargs):
        attempts["count"] += 1
        return _Resp(503)

    monkeypatch.setattr(mod["requests"], "get", fake_get)
    monkeypatch.setattr(mod["time"], "sleep", lambda *_args: None)

    try:
        request_with_retry("https://example.com")
    except RuntimeError as exc:
        assert "HTTP-Anfrage fehlgeschlagen" in str(exc)
    else:
        raise AssertionError("request_with_retry should have raised")

    assert attempts["count"] == mod["HTTP_RETRY_ATTEMPTS"]


def test_gemini_generate_content_with_retry_retries_retryable_errors(monkeypatch):
    mod = _load_partial_module()
    generate_with_retry = mod["_gemini_generate_content_with_retry"]

    class _Models:
        def __init__(self):
            self.calls = 0

        def generate_content(self, **kwargs):
            self.calls += 1
            if self.calls < 3:
                raise RuntimeError("429 rate limit")
            return "ok"

    models = _Models()
    monkeypatch.setattr(mod["client"], "models", models)
    monkeypatch.setattr(mod["time"], "sleep", lambda *_args: None)

    response = generate_with_retry(model="gemini-test", contents="prompt")

    assert response == "ok"
    assert models.calls == 3


def test_gemini_generate_content_with_retry_does_not_retry_non_retryable_errors(monkeypatch):
    mod = _load_partial_module()
    generate_with_retry = mod["_gemini_generate_content_with_retry"]

    class _Models:
        def __init__(self):
            self.calls = 0

        def generate_content(self, **kwargs):
            self.calls += 1
            raise RuntimeError("400 bad request")

    models = _Models()
    monkeypatch.setattr(mod["client"], "models", models)
    monkeypatch.setattr(mod["time"], "sleep", lambda *_args: None)

    try:
        generate_with_retry(model="gemini-test", contents="prompt")
    except RuntimeError as exc:
        assert "Gemini-Aufruf fehlgeschlagen" in str(exc)
    else:
        raise AssertionError("generate_with_retry should have raised")

    assert models.calls == 1


def test_write_run_manifest_persists_execution_metadata(tmp_path):
    mod = _load_partial_module()
    podcast_generator_cls = mod["PodcastGenerator"]

    mod["OUTPUT_DIR"] = str(tmp_path / "out")
    mod["TEMP_DIR"] = str(tmp_path / "temp")
    mod["ASSETS_DIR"] = str(tmp_path / "assets")
    Path(mod["OUTPUT_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["TEMP_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["ASSETS_DIR"]).mkdir(parents=True, exist_ok=True)

    bot = podcast_generator_cls("Manifest Topic")
    bot.final_audio_path = str(Path(mod["OUTPUT_DIR"]) / "Manifest_Topic.mp3")
    bot.metadata_path = str(Path(mod["OUTPUT_DIR"]) / "Manifest_Topic_meta.json")
    bot.sources = ["https://example.com/source"]

    bot.write_run_manifest(
        started_at=100.0,
        finished_at=112.5,
        generate_video=False,
        resume_enabled=True,
        force_restart=False,
        status="completed",
    )

    manifest = json.loads(Path(bot.run_manifest_path).read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    assert manifest["duration_seconds"] == 12.5
    assert manifest["options"]["resume_enabled"] is True
    assert manifest["options"]["generate_video"] is False
    assert manifest["artifacts"]["audio"] == bot.final_audio_path
    assert manifest["artifacts"]["video"] is None
    assert manifest["sources"] == ["https://example.com/source"]


def test_write_run_manifest_records_failures(tmp_path):
    mod = _load_partial_module()
    podcast_generator_cls = mod["PodcastGenerator"]

    mod["OUTPUT_DIR"] = str(tmp_path / "out")
    mod["TEMP_DIR"] = str(tmp_path / "temp")
    mod["ASSETS_DIR"] = str(tmp_path / "assets")
    Path(mod["OUTPUT_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["TEMP_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["ASSETS_DIR"]).mkdir(parents=True, exist_ok=True)

    bot = podcast_generator_cls("Manifest Failure")
    Path(bot.checkpoint_path).write_text("{}", encoding="utf-8")

    bot.write_run_manifest(
        started_at=5.0,
        finished_at=8.0,
        generate_video=True,
        resume_enabled=False,
        force_restart=True,
        status="failed",
        error="boom",
    )

    manifest = json.loads(Path(bot.run_manifest_path).read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
    assert manifest["error"] == "boom"
    assert manifest["options"]["force_restart"] is True
    assert manifest["artifacts"]["checkpoint"] == bot.checkpoint_path
