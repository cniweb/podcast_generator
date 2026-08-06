# CI- und Integrationsharmonisierung Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die lokale CLI-Anwendung behält ihre Audio-/Video-Pipeline, erhält aber dieselben reproduzierbaren CI-, Sicherheits- und Dependency-Standards wie `productvideo_generator`.

**Architecture:** Die Änderungen bleiben auf Workflow-, Dependency- und Shell-Skript-Ebene. Echte externe APIs werden nicht in CI aufgerufen; Tests verwenden Stubs und Partial-Module-Loading. FFmpeg wird als CI-Voraussetzung geprüft, nicht durch ein Setup-Skript automatisch installiert.

**Tech Stack:** GitHub Actions, Python 3.12/3.13, pytest, pytest-cov, Ruff, pymarkdownlnt, Renovate, FFmpeg, Bash.

## Global Constraints

- Kein Deployment und keine Veröffentlichung generierter Medien.
- Keine echten Gemini-, Trends-, Freesound- oder Google-Cloud-Aufrufe in CI.
- CLI-Eingaben, `--resume`, `--force-restart` und Output-Namen bleiben unverändert.
- Secrets, Credentials, `.env` und generierte Dateien bleiben untracked.
- Actions werden auf feste Versionen gepinnt; `latest` wird nicht verwendet.
- FFmpeg bleibt notwendige lokale/CI-Infrastruktur.

### Task 1: Baseline prüfen

**Files:** Keine Änderungen.

- [ ] `git status --short --branch` ausführen.
- [ ] Vorhandene venv und `python3` ermitteln.
- [ ] `python -m pytest -q`, Ruff, Compile-Check und Markdown-Check ausführen.
- [ ] Fehlende lokale Tools dokumentieren, ohne Codeänderungen vorzutäuschen.

### Task 2: CI-Workflow harmonisieren

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] `permissions: contents: read` und Concurrency pro Workflow/Ref ergänzen.
- [ ] Python-Matrix `3.12`, `3.13` verwenden.
- [ ] Testausgabe als JUnit- und Coverage-Artefakte veröffentlichen.
- [ ] Vor dem Testlauf `ffmpeg -version` und `ffprobe -version` prüfen.
- [ ] Bestehendes Coverage-Gate von `40` Prozent beibehalten und explizit dokumentieren.
- [ ] Action-Versionen konsistent und ohne `latest` verwenden.
- [ ] YAML-Struktur mit `actionlint` oder einem vergleichbaren Syntaxcheck prüfen.

### Task 3: Lokale Skripte konsolidieren

**Files:**
- Modify: `ci.sh`
- Modify: `setup.sh`
- Modify: `run.sh`

- [ ] Eine Unix-kompatible Python-Auswahl über `${PYTHON_BIN:-python3}` verwenden.
- [ ] Venv-Aufrufe konsequent über `.venv/bin/python` und `.venv/bin/pip` ausführen.
- [ ] `python -m ...` statt globaler Tool-Aufrufe verwenden.
- [ ] FFmpeg-Prüfung in Setup und CI beibehalten, aber keine automatische Paketinstallation in CI ausführen.
- [ ] Bestehende Resume-/Force-Restart-Semantik unverändert lassen.
- [ ] Shell-Syntax mit `bash -n` prüfen.

### Task 4: Dependency-Automatisierung abgleichen

**Files:**
- Modify: `renovate.json`
- Modify: `.github/workflows/renovate.yml`

- [ ] Renovate-Konfiguration mit Productvideo kompatibel halten.
- [ ] Renovate-Action auf feste Version pinnen.
- [ ] `RENOVATE_TOKEN` ausschließlich als Secret verwenden.
- [ ] Workflow- und JSON-Syntax prüfen.

### Task 5: Gesamtprüfung und Commit

- [ ] `python -m ruff check podcast_generator.py utils.py tests/` erfolgreich ausführen.
- [ ] `python -m compileall podcast_generator.py utils.py` erfolgreich ausführen.
- [ ] `python -m pytest -q --cov=podcast_generator --cov=utils --cov-report=term-missing --cov-fail-under=40 --junitxml=test-results.xml` erfolgreich ausführen.
- [ ] `python -m pymarkdown -c .pymarkdown.toml scan .` erfolgreich ausführen.
- [ ] `git diff --check` erfolgreich ausführen.
- [ ] Einen fokussierten Commit erstellen.
- [ ] Branch pushen, PR öffnen und CI abwarten.
