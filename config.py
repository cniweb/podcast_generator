from dataclasses import dataclass
from pathlib import Path
import os


class ConfigurationError(RuntimeError):
    """Raised when required podcast configuration is missing or invalid."""


@dataclass(frozen=True)
class PodcastConfig:
    gemini_api_key: str
    google_application_credentials: Path
    freesound_api_key: str
    podcast_name: str
    slogan: str
    script_model: str
    temp_dir: Path
    output_dir: Path
    assets_dir: Path


def load_config(env=None, base_dir=None):
    values = os.environ if env is None else env
    root = Path(base_dir or Path.cwd())
    names = (
        "GEMINI_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS", "FREESOUND_API_KEY",
        "PODCAST_NAME", "PODCAST_SLOGAN", "SCRIPT_DEFAULT_MODEL",
        "PODCAST_TEMP_DIR", "PODCAST_OUTPUT_DIR", "PODCAST_ASSETS_DIR",
    )
    missing = [name for name in names if not values.get(name)]
    if missing:
        raise ConfigurationError("Fehlende Variablen: " + ", ".join(missing))

    def resolve(name):
        path = Path(values[name])
        return path if path.is_absolute() else root / path

    return PodcastConfig(
        gemini_api_key=values["GEMINI_API_KEY"],
        google_application_credentials=resolve("GOOGLE_APPLICATION_CREDENTIALS"),
        freesound_api_key=values["FREESOUND_API_KEY"],
        podcast_name=values["PODCAST_NAME"],
        slogan=values["PODCAST_SLOGAN"],
        script_model=values["SCRIPT_DEFAULT_MODEL"],
        temp_dir=resolve("PODCAST_TEMP_DIR"),
        output_dir=resolve("PODCAST_OUTPUT_DIR"),
        assets_dir=resolve("PODCAST_ASSETS_DIR"),
    )
