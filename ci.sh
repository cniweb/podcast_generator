#!/bin/bash
# Führt Linting, Syntax-Check und Tests für podcast_generator im venv aus.
set -euo pipefail

python_bin="python3"
ruff_version="0.6.8"

# Virtuelle Umgebung sicherstellen
if [[ ! -d .venv ]]; then
    $python_bin -m venv .venv
fi
source .venv/bin/activate

# Optional: Setup erneut nutzen, falls Umgebungs- und FFmpeg-Checks gewünscht sind (benötigt .env)
if [[ "${1:-}" == "--setup" ]]; then
    ./setup.sh
fi

$python_bin -m pip install --upgrade pip
$python_bin -m pip install -r requirements.txt
$python_bin -m pip install ruff=="$ruff_version"

# Linting
$python_bin -m ruff check --fix podcast_generator.py
$python_bin -m ruff check podcast_generator.py

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
$python_bin -m compileall podcast_generator.py

# Tests
$python_bin -m pytest -q

echo "All checks passed."
