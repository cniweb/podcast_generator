import pytest

from config import ConfigurationError, load_config


@pytest.mark.unit
def test_load_config_resolves_relative_paths(tmp_path):
    values = {
        "GEMINI_API_KEY": "secret",
        "GOOGLE_APPLICATION_CREDENTIALS": "credentials.json",
        "FREESOUND_API_KEY": "freesound",
        "PODCAST_NAME": "Podcast",
        "PODCAST_SLOGAN": "Slogan",
        "SCRIPT_DEFAULT_MODEL": "script",
        "PODCAST_TEMP_DIR": "temp",
        "PODCAST_OUTPUT_DIR": "output",
        "PODCAST_ASSETS_DIR": "assets",
    }
    config = load_config(values, tmp_path)
    assert config.output_dir == tmp_path / "output"
    assert config.google_application_credentials == tmp_path / "credentials.json"


@pytest.mark.unit
def test_load_config_reports_missing_values():
    with pytest.raises(ConfigurationError, match="GEMINI_API_KEY"):
        load_config({}, "/tmp")
