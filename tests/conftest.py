import os
import sys
from pathlib import Path

import pytest

# Stellt sicher, dass das Projekt-Root für lokale Module importierbar ist
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_partial_module():
    """Laedt podcast_generator.py bis zum HAUPTPROGRAMM-Marker in einem Sandbox-Namespace."""
    module_path = ROOT / "podcast_generator.py"
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


@pytest.fixture(scope="session")
def partial_module():
    """Pytest-Fixture: gibt den geladenen Partial-Namespace von podcast_generator zurueck."""
    return _load_partial_module()
