#!/bin/bash
# Führt Linting, Syntax-Check und Tests für podcast_generator im venv aus.
set -euo pipefail

python_bin="python3"
ruff_version="0.6.8"

if ! $python_bin -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'; then
    echo "Python 3.12 oder neuer erforderlich."
    exit 1
fi

# Virtuelle Umgebung sicherstellen
if [[ ! -d .venv ]]; then
    $python_bin -m venv .venv
fi
source .venv/bin/activate
python_bin=".venv/bin/python"

# Optional: Setup erneut nutzen, falls Umgebungs- und FFmpeg-Checks gewünscht sind (benötigt .env)
if [[ "${1:-}" == "--setup" ]]; then
    ./setup.sh
fi

$python_bin -m pip install --upgrade pip
$python_bin -m pip install -r requirements.txt
$python_bin -m pip install ruff=="$ruff_version"

# Linting
$python_bin -m ruff check --fix podcast_generator.py utils.py tests/
$python_bin -m ruff check podcast_generator.py utils.py tests/

# Import-Prüfung
$python_bin - <<'PY'
import importlib
deps = [
    'google.genai',
    'pytrends',
    'pydub',
    'requests',
    'dotenv',
]
for dep in deps:
    try:
        importlib.import_module(dep)
    except Exception as exc:
        raise SystemExit(f"Import failed for {dep}: {exc}")
PY

# Syntax-Prüfung
$python_bin -m compileall podcast_generator.py utils.py

# Tests
$python_bin -m pytest -q --cov=podcast_generator --cov=utils --cov-report=term-missing --cov-fail-under=40 --junitxml=test-results.xml

# Markdown lint
$python_bin -m pymarkdown -c .pymarkdown.toml scan .

echo "All checks passed."
