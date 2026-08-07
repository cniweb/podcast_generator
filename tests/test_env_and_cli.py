"""Tests fuer Umgebungsvariablen-Validierung, CLI-Topic-Eingabe und Verzeichnis-Erstellung."""

from pathlib import Path

from conftest import _load_partial_module


# ---------------------------------------------------------------------------
# _require_env Tests
# ---------------------------------------------------------------------------


def test_require_env_returns_value_when_set(monkeypatch):
    mod = _load_partial_module()
    require_env = mod["_require_env"]
    monkeypatch.setenv("_TEST_REQUIRE_ENV_VAR", "hello")

    assert require_env("_TEST_REQUIRE_ENV_VAR") == "hello"


def test_require_env_raises_for_missing_variable(monkeypatch):
    mod = _load_partial_module()
    require_env = mod["_require_env"]
    monkeypatch.delenv("_TEST_MISSING_VAR", raising=False)

    try:
        require_env("_TEST_MISSING_VAR")
    except RuntimeError as exc:
        assert "_TEST_MISSING_VAR" in str(exc)
        assert "required" in str(exc).lower()
    else:
        raise AssertionError("_require_env should have raised RuntimeError")


def test_require_env_raises_for_empty_string(monkeypatch):
    mod = _load_partial_module()
    require_env = mod["_require_env"]
    monkeypatch.setenv("_TEST_EMPTY_VAR", "")

    try:
        require_env("_TEST_EMPTY_VAR")
    except RuntimeError as exc:
        assert "_TEST_EMPTY_VAR" in str(exc)
    else:
        raise AssertionError("_require_env should reject empty strings")


# ---------------------------------------------------------------------------
# CLI-Argument / Topic Tests
# ---------------------------------------------------------------------------


def test_parse_cli_args_topic_provided():
    mod = _load_partial_module()
    parse_cli_args = mod["_parse_cli_args"]

    args = parse_cli_args(["Kuenstliche Intelligenz"])
    assert args.topic == "Kuenstliche Intelligenz"
    assert args.resume is False
    assert args.force_restart is False


def test_cli_version_is_defined():
    mod = _load_partial_module()
    assert mod["VERSION"] == "0.1.0"


def test_parse_cli_args_no_topic():
    mod = _load_partial_module()
    parse_cli_args = mod["_parse_cli_args"]

    args = parse_cli_args([])
    assert args.topic is None


def test_parse_cli_args_resume_with_topic():
    mod = _load_partial_module()
    parse_cli_args = mod["_parse_cli_args"]

    args = parse_cli_args(["--resume", "Blockchain"])
    assert args.topic == "Blockchain"
    assert args.resume is True


def test_parse_cli_args_force_restart_with_topic():
    mod = _load_partial_module()
    parse_cli_args = mod["_parse_cli_args"]

    args = parse_cli_args(["--force-restart", "Cloud Computing"])
    assert args.topic == "Cloud Computing"
    assert args.force_restart is True


# ---------------------------------------------------------------------------
# Verzeichnis-Erstellung (TEMP_DIR, OUTPUT_DIR, ASSETS_DIR)
# ---------------------------------------------------------------------------


def test_output_directories_are_created(tmp_path, monkeypatch):
    """Stellt sicher, dass die konfigurierten Verzeichnisse bei Modul-Init erstellt werden."""
    temp_dir = str(tmp_path / "test_temp")
    output_dir = str(tmp_path / "test_output")
    assets_dir = str(tmp_path / "test_assets")

    monkeypatch.setenv("PODCAST_TEMP_DIR", temp_dir)
    monkeypatch.setenv("PODCAST_OUTPUT_DIR", output_dir)
    monkeypatch.setenv("PODCAST_ASSETS_DIR", assets_dir)

    mod = _load_partial_module()

    assert Path(mod["TEMP_DIR"]).exists()
    assert Path(mod["OUTPUT_DIR"]).exists()
    assert Path(mod["ASSETS_DIR"]).exists()


def test_generator_accepts_explicit_config(tmp_path):
    mod = _load_partial_module()
    config = mod["load_config"](
        {
            "GEMINI_API_KEY": "key",
            "GOOGLE_APPLICATION_CREDENTIALS": "credentials.json",
            "FREESOUND_API_KEY": "freesound",
            "PODCAST_NAME": "Injected Podcast",
            "PODCAST_SLOGAN": "Injected Slogan",
            "SCRIPT_DEFAULT_MODEL": "script",
            "PODCAST_TEMP_DIR": "temp",
            "PODCAST_OUTPUT_DIR": "output",
            "PODCAST_ASSETS_DIR": "assets",
        },
        tmp_path,
    )
    generator = mod["PodcastGenerator"]("Injected Topic", config=config)
    assert generator.config is config
