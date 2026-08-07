# CLI- und Runtime-Verträge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gemeinsame CLI-, Manifest-, Fehler-, Retry- und Testverträge für beide lokalen Generatoren umsetzen.

**Architecture:** Verträge bleiben zunächst projektintern und werden durch gleich benannte Konstanten, Fehlerklassen, Manifestfelder und Testfixtures harmonisiert. Keine gemeinsame Paketabhängigkeit wird eingeführt.

**Tech Stack:** Python, argparse, pytest, python-dotenv, bestehende Gemini-/FFmpeg-Integrationen.

## Global Constraints

- Exit-Code `0` bedeutet Erfolg.
- Exit-Code `1` bedeutet Laufzeit-, API- oder QA-Fehler.
- Exit-Code `2` bedeutet ungültige CLI-Argumente oder Konfiguration.
- Keine Secrets in Manifesten, Logs oder Tests.
- Keine Live-API-Aufrufe in Tests.

### Task 1: Gemeinsame Verträge und Fehlerklassen

**Files:**
- Modify: `podcast_generator.py`
- Test: bestehende CLI-/Pipeline-Testdateien

- [ ] Konstanten für Exit-Codes und Manifest-Schema-Version definieren.
- [ ] Fehlerklassen für Konfiguration, externe Dienste, Rate Limits, Generierung und Output-QA ergänzen.
- [ ] Bestehende RuntimeErrors gezielt auf diese Kategorien abbilden.
- [ ] Regressionstests für Fehlerklasse und Exit-Code-Vertrag ergänzen.

### Task 2: Manifest-Schema vereinheitlichen

**Files:**
- Modify: `podcast_generator.py`
- Modify: Manifest-Tests

- [ ] Felder `schema_version` und `generator` ergänzen.
- [ ] Gemeinsame Runtime-, Status-, Fehler-, Modell- und Artefaktfelder validieren.
- [ ] Secrets und Promptinhalte explizit ausschließen.
- [ ] Tests für die Manifestvariante ergänzen.

### Task 3: CLI- und Exit-Code-Verhalten

**Files:**
- Modify: `podcast_generator.py`
- Modify: `tests/test_env_and_cli.py`

- [ ] `--version` und `--help` konsistent dokumentieren.
- [ ] Ungültige Argumente über argparse mit Exit-Code 2 behandeln.
- [ ] Laufzeitfehler über kontrollierten Main-Wrapper mit Exit-Code 1 ausgeben.
- [ ] Erfolgreiche Läufe mit Exit-Code 0 abschließen.
- [ ] Tests für alle drei Exit-Codes ergänzen.

### Task 4: Retry-Konventionen und Testfixtures

**Files:**
- Modify: bestehende Podcast-Testfixtures
- Modify: `podcast_generator.py`

- [ ] Bestehende Retry-Konstanten und Backoff-Konvention dokumentieren.
- [ ] Nur Rate-Limit-, Timeout- und temporäre 5xx-Fehler wiederholen.
- [ ] Konfigurations- und Validierungsfehler nicht wiederholen.
- [ ] Dummy-Clients und Dummy-Operationen zentral wiederverwenden.
- [ ] Retry-Erfolg, Retry-Erschöpfung und Nicht-Retry-Fälle testen.

### Task 5: Dependency-Trennung prüfen

**Files:**
- Create/Modify: `requirements-dev.txt`
- Modify: `requirements.txt`, `setup.sh`, `ci.sh`, reusable CI

- [ ] Test-/Lint-/Audit-Abhängigkeiten aus Runtime-Abhängigkeiten trennen.
- [ ] Lokale CLI-Installation weiterhin mit dokumentiertem Setup ermöglichen.
- [ ] CI installiert Runtime plus Dev-Abhängigkeiten reproduzierbar.
- [ ] Keine Abhängigkeit doppelt oder widersprüchlich definieren.

### Task 6: Verifikation und PR

- [ ] Unit- und Integrationstests ausführen.
- [ ] Ruff, Compile-Check, Markdown-Linting und Shell-Syntax ausführen.
- [ ] Beide PRs erstellen und GitHub Actions abwarten.
- [ ] Nur grüne PRs mergen und Branches bereinigen.
