# Config-Injektion und Testtrennung Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generatoren explizit mit typisierter Config versorgen und Testtypen reproduzierbar trennen.

**Architecture:** Config-Injektion erfolgt über optionale Konstruktorparameter und einen CLI-Factory-/Default-Pfad. QA liefert `QAResult`; die Pipeline entscheidet über Fehlerstatus und Exit-Code. pytest-Konfiguration registriert gemeinsame Marker.

**Tech Stack:** Python dataclasses, pytest markers, pytest.ini/pyproject, bestehende CI.

## Global Constraints

- Bestehende CLI-Aufrufe bleiben kompatibel.
- Keine globalen Secrets in Tests oder Manifesten.
- Keine Live-Netzwerkaufrufe in CI.
- Fachliche Pipeline bleibt unverändert.

### Task 1: Config-Injektion Podcast

**Files:**
- Modify: `podcast_generator.py`
- Modify: `tests/test_env_and_cli.py`

- [ ] Konstruktor akzeptiert `config: PodcastConfig | None`.
- [ ] CLI lädt Config einmal und injiziert sie.
- [ ] Resume-/Output-Pfade nutzen die injizierte Config.
- [ ] Test mit isolierter Config ergänzen.

### Task 2: Config-Injektion Productvideo-Vertrag spiegeln

- [ ] Productvideo-Kompatibilität prüfen, ohne fremde Runtime-Dateien zu verändern.
- [ ] Gemeinsame Konstruktor-/Factory-Dokumentation aktualisieren.

### Task 3: QA-Abschlussvertrag

**Files:**
- Modify: `qa.py`
- Modify: `podcast_generator.py`
- Modify: QA-Tests

- [ ] QAResult um strukturierte Artefaktinformationen und Warnungen ergänzen.
- [ ] `validate_outputs()` gibt QAResult zurück oder wandelt ihn an der Pipelinegrenze in den bestehenden Fehler um.
- [ ] Manifest und QAResult konsistent halten.
- [ ] Tests für Warnungen, Fehler und erfolgreichen Abschluss ergänzen.

### Task 4: Testmarker und CI

**Files:**
- Create/Modify: `pytest.ini` oder `pyproject.toml`
- Modify: CI-Workflow
- Modify: Tests

- [ ] Marker `unit`, `integration`, `requires_ffmpeg`, `network` registrieren.
- [ ] Pure Config-/QA-/Parser-Tests als `unit` markieren.
- [ ] Pipeline-/FFmpeg-Tests passend markieren.
- [ ] CI standardmäßig mit `-m "not network"` ausführen.

### Task 5: Security-Findings

- [ ] Dependabot-/pip-audit-Status nach den Änderungen prüfen.
- [ ] Keine unbegründeten Ignore-Regeln hinzufügen.
- [ ] Verifizierte Updates separat behandeln.

### Task 6: Verifikation und PR

- [ ] Marker-Selektoren, Tests, Ruff, Compile, Markdown und Shell ausführen.
- [ ] PRs erstellen und GitHub-CI prüfen.
- [ ] Nur grüne PRs mergen und Branches bereinigen.
