# Typisierte Konfiguration und formale QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Konfiguration, Manifeste und Output-QA explizit typisieren und kritische Fehlerpfade absichern.

**Architecture:** Je Projekt entsteht ein kleines internes Konfigurations-/QA-Modul ohne gemeinsame externe Library. Die bestehenden Pipelineklassen konsumieren die geprüften Werte, während CLI und Output-Namen stabil bleiben.

**Tech Stack:** Python `dataclasses`, `pathlib`, JSON, pytest, bestehende FFmpeg-/Gemini-Integrationen.

## Global Constraints

- Keine gemeinsame Runtime-Library.
- Keine Live-API-Aufrufe in Tests.
- Bestehende CLI-Optionen und Output-Namen bleiben kompatibel.
- Secrets werden nicht im Config-Objekt serialisiert oder geloggt.

### Task 1: Typisierte Konfiguration

**Files:**
- Create: `config.py`
- Modify: `podcast_generator.py`
- Test: `tests/test_config.py`

- [ ] Unveränderliche Config-Dataclass mit Pflicht-/Optionalfeldern definieren.
- [ ] Umgebung zentral laden und Pflichtvariablen gesammelt validieren.
- [ ] Pfade relativ zum Projektverzeichnis auflösen.
- [ ] Bestehende globale Werte kompatibel aus Config ableiten.
- [ ] Tests für vollständige, fehlende und ungültige Konfiguration ergänzen.

### Task 2: Formale Manifest-/QA-Validierung

**Files:**
- Create: `qa.py`
- Modify: `podcast_generator.py`
- Test: `tests/test_qa.py`

- [ ] Manifestpflichtfelder und erlaubte Statuswerte prüfen.
- [ ] Strukturierte QA-Ergebnisse mit `ok`, `warnings`, `errors`, `artifacts` liefern.
- [ ] Fehlende/ungültige Medien und JSON-Referenzen erfassen.
- [ ] Bestehende `validate_outputs()`-Aufrufe kompatibel halten.
- [ ] Tests für gültige und ungültige Manifeste/Artefakte ergänzen.

### Task 3: Kritische Podcast-Fehlerpfade

- [ ] Resume-Konsistenzfehler testen.
- [ ] QA-Fehlerstatus im Manifest testen.
- [ ] FFmpeg-/Subprocess-Fehler testen.
- [ ] Atomare Writes bei Fehler testen.

### Task 4: Verifikation

- [ ] Productvideo-Config-/QA-Module analog ergänzen.
- [ ] Tests, Ruff, Compile, Markdown und Shell-Syntax ausführen.
- [ ] PRs erstellen, CI prüfen, nur grüne PRs mergen.
