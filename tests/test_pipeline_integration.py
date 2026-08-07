import json
from pathlib import Path

from conftest import _load_partial_module


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

    def _write_checkpoint(
        self, current_step: str, status: str, completed_steps: list[str]
    ):
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
    execute_pipeline(
        bot, generate_video=False, resume_enabled=True, force_restart=False
    )

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

    monkeypatch.setitem(
        mod,
        "_run_step",
        lambda label, action, spinner_after=10.0, defer_output=False: action(),
    )

    bot = _RecordingBot()
    execute_pipeline(bot, generate_video=True, resume_enabled=False, force_restart=True)

    assert bot.cleared == [False, True]
    assert bot.calls[0] == ("resume", False)
    assert "video" in bot.calls
    assert any(
        update[0] == "video" and update[1] == "completed"
        for update in bot.checkpoint_updates
    )


def test_execute_pipeline_writes_failed_checkpoint_on_step_error(monkeypatch):
    mod = _load_partial_module()
    execute_pipeline = mod["_execute_pipeline"]

    class _FailingBot(_RecordingBot):
        def __init__(self):
            super().__init__()
            self.failed = []

        def _write_checkpoint_error(
            self, current_step: str, completed_steps: list[str], error: Exception
        ):
            self.failed.append((current_step, list(completed_steps), str(error)))

        def generate_script(self):
            raise RuntimeError("script boom")

    monkeypatch.setitem(
        mod,
        "_run_step",
        lambda label, action, spinner_after=10.0, defer_output=False: action(),
    )

    bot = _FailingBot()

    try:
        execute_pipeline(
            bot, generate_video=False, resume_enabled=False, force_restart=False
        )
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


def test_gemini_generate_content_with_retry_does_not_retry_non_retryable_errors(
    monkeypatch,
):
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
    assert manifest["schema_version"] == 1
    assert manifest["generator"] == "podcast"
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


def test_run_manifest_has_common_status_and_artifact_fields(tmp_path):
    mod = _load_partial_module()
    podcast_generator_cls = mod["PodcastGenerator"]

    mod["OUTPUT_DIR"] = str(tmp_path / "out")
    mod["TEMP_DIR"] = str(tmp_path / "temp")
    mod["ASSETS_DIR"] = str(tmp_path / "assets")
    Path(mod["OUTPUT_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["TEMP_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["ASSETS_DIR"]).mkdir(parents=True, exist_ok=True)

    bot = podcast_generator_cls("Common Fields")
    bot.write_run_manifest(
        started_at=10.0,
        finished_at=15.25,
        generate_video=False,
        resume_enabled=False,
        force_restart=False,
        status="failed",
        error="qa failed",
    )

    manifest = json.loads(Path(bot.run_manifest_path).read_text(encoding="utf-8"))
    assert {
        "topic",
        "status",
        "started_at",
        "finished_at",
        "duration_seconds",
        "models",
        "artifacts",
        "error",
    } <= manifest.keys()
    assert manifest["duration_seconds"] == 5.25
    assert manifest["error"] == "qa failed"


def test_validate_outputs_accepts_present_audio_and_metadata(tmp_path, monkeypatch):
    mod = _load_partial_module()
    podcast_generator_cls = mod["PodcastGenerator"]

    mod["OUTPUT_DIR"] = str(tmp_path / "out")
    mod["TEMP_DIR"] = str(tmp_path / "temp")
    mod["ASSETS_DIR"] = str(tmp_path / "assets")
    Path(mod["OUTPUT_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["TEMP_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["ASSETS_DIR"]).mkdir(parents=True, exist_ok=True)

    bot = podcast_generator_cls("QA Topic")
    bot.final_audio_path = str(Path(mod["OUTPUT_DIR"]) / "QA_Topic.mp3")
    bot.audio_voice_path = str(Path(mod["TEMP_DIR"]) / "QA_Topic_voice.mp3")
    bot.metadata_path = str(Path(mod["OUTPUT_DIR"]) / "QA_Topic_meta.json")
    transcript_path = Path(mod["OUTPUT_DIR"]) / "QA_Topic_transcription.txt"

    Path(bot.final_audio_path).write_bytes(b"audio")
    Path(bot.audio_voice_path).write_bytes(b"voice")
    Path(bot.metadata_path).write_text("{}", encoding="utf-8")
    transcript_path.write_text("transcript", encoding="utf-8")

    class _Audio:
        def __len__(self):
            return 31_000

    monkeypatch.setattr(mod["AudioSegment"], "from_mp3", lambda _path: _Audio())

    bot.validate_outputs(generate_video=False)


def test_manifest_write_leaves_no_temporary_files(tmp_path):
    mod = _load_partial_module()
    podcast_generator_cls = mod["PodcastGenerator"]
    mod["OUTPUT_DIR"] = str(tmp_path / "out")
    mod["TEMP_DIR"] = str(tmp_path / "temp")
    mod["ASSETS_DIR"] = str(tmp_path / "assets")
    Path(mod["OUTPUT_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["TEMP_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["ASSETS_DIR"]).mkdir(parents=True, exist_ok=True)

    bot = podcast_generator_cls("Atomic Manifest")
    bot.write_run_manifest(
        started_at=1.0,
        finished_at=2.0,
        generate_video=False,
        resume_enabled=False,
        force_restart=False,
        status="completed",
    )

    assert Path(bot.run_manifest_path).exists()
    assert list(Path(mod["OUTPUT_DIR"]).glob(".tmp-*")) == []


def test_validate_outputs_rejects_missing_required_artifacts(tmp_path):
    mod = _load_partial_module()
    podcast_generator_cls = mod["PodcastGenerator"]

    mod["OUTPUT_DIR"] = str(tmp_path / "out")
    mod["TEMP_DIR"] = str(tmp_path / "temp")
    mod["ASSETS_DIR"] = str(tmp_path / "assets")
    Path(mod["OUTPUT_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["TEMP_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["ASSETS_DIR"]).mkdir(parents=True, exist_ok=True)

    bot = podcast_generator_cls("Broken QA")

    try:
        bot.validate_outputs(generate_video=True)
    except RuntimeError as exc:
        assert "Output-QA fehlgeschlagen" in str(exc)
        assert "Finale Audio-Datei fehlt" in str(exc)
        assert "Video-Datei fehlt" in str(exc)
    else:
        raise AssertionError("validate_outputs should have raised")


def test_format_subprocess_error_includes_exit_code_and_output():
    mod = _load_partial_module()
    format_subprocess_error = mod["_format_subprocess_error"]
    called_process_error = mod["subprocess"].CalledProcessError(
        1,
        ["ffmpeg", "-i", "input.mp3"],
        stderr=b"ffmpeg exploded",
    )

    message = format_subprocess_error(
        ["ffmpeg", "-i", "input.mp3"], called_process_error
    )

    assert "exit=1" in message
    assert "ffmpeg -i input.mp3" in message
    assert "ffmpeg exploded" in message


def test_create_video_raises_detailed_ffmpeg_error(tmp_path, monkeypatch):
    mod = _load_partial_module()
    podcast_generator_cls = mod["PodcastGenerator"]

    mod["OUTPUT_DIR"] = str(tmp_path / "out")
    mod["TEMP_DIR"] = str(tmp_path / "temp")
    mod["ASSETS_DIR"] = str(tmp_path / "assets")
    Path(mod["OUTPUT_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["TEMP_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(mod["ASSETS_DIR"]).mkdir(parents=True, exist_ok=True)

    cover_path = Path(mod["ASSETS_DIR"]) / "cover.png"
    cover_path.write_bytes(b"cover")

    bot = podcast_generator_cls("Video Failure")
    bot.final_audio_path = str(Path(mod["OUTPUT_DIR"]) / "Video_Failure.mp3")
    Path(bot.final_audio_path).write_bytes(b"audio")

    def fake_run(*args, **kwargs):
        raise mod["subprocess"].CalledProcessError(
            1, kwargs.get("args", args[0]), stderr=b"bad ffmpeg"
        )

    monkeypatch.setattr(mod["subprocess"], "run", fake_run)

    try:
        bot.create_video()
    except RuntimeError as exc:
        assert "exit=1" in str(exc)
        assert "bad ffmpeg" in str(exc)
        assert "Pruefe Cover-Datei" in str(exc)
    else:
        raise AssertionError("create_video should have raised")
