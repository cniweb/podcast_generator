# Security, Run-Manifest und Output-QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Podcast erhält Dependency-Auditing und verifizierte gemeinsame Manifest-/QA-Verträge ohne fachliche Pipelineänderung.

**Architecture:** Das bestehende Manifest und die bestehende `validate_outputs()`-Methode bleiben die zentrale Implementierung. Änderungen sind minimal und konzentrieren sich auf CI, Regressionstests und abschließende Statuskonsistenz.

**Tech Stack:** Python, pytest, pytest-cov, pip-audit, FFmpeg, GitHub Actions.

## Global Constraints

- `pip-audit` blockiert nur HIGH/CRITICAL.
- LOW/MODERATE erzeugen Warnungen, blockieren aber nicht.
- Keine echten API-Aufrufe in Tests oder CI.
- CLI-, Resume- und Output-Semantik bleiben unverändert.

### Task 1: Security-Audit in CI

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `requirements.txt`

- [ ] `pip-audit` als CI-Abhängigkeit ergänzen.
- [ ] Audit auf installierter Umgebung für Python 3.12/3.13 ausführen.
- [ ] Ausgabe nach HIGH/CRITICAL filtern und nur diese per Exit-Code blockieren.
- [ ] LOW/MODERATE als GitHub-Warnung ausgeben.
- [ ] Keine Secrets an `pip-audit` übergeben.
- [ ] Workflow-Syntax prüfen.

### Task 2: Manifest-/QA-Regressionstests

**Files:**
- Modify: `tests/test_pipeline_integration.py`

- [ ] Test für gemeinsame Manifest-Felder und Fehlerstatus ergänzen.
- [ ] Test für QA-Fehler bei fehlenden Artefakten ergänzen.
- [ ] Test für Resume-Konsistenz nach QA-Fehler ergänzen.
- [ ] Tests zunächst isoliert fehlschlagen lassen.

### Task 3: Podcast-Statuskonsistenz prüfen

**Files:**
- Modify: `podcast_generator.py`

- [ ] Sicherstellen, dass erfolgreiche Läufe erst nach `validate_outputs()` als `completed` manifestiert werden.
- [ ] Sicherstellen, dass QA-Fehler `failed` und einen Fehlertext im Manifest schreiben.
- [ ] Gemeinsame Manifest-Felder beibehalten oder minimal ergänzen.
- [ ] Resume-/Force-Restart-Verhalten unverändert lassen.

### Task 4: Verifikation und PR

- [ ] Podcast-Tests, Ruff, Compile-Check und Markdown-Linting ausführen.
- [ ] `pip-audit` lokal auf Python 3.12+ ausführen.
- [ ] Branch pushen und PR erstellen.
- [ ] Beide CI-Matrixläufe und Audit-Ergebnis prüfen.
- [ ] PR nach grüner CI mergen.
