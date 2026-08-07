# Integrierte QA, Laufmetriken und Security-Checks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** QA verbindlich in die Pipeline integrieren, Schrittmetriken erfassen und Security-Checks erweitern.

**Architecture:** QAResult bleibt ein kleines internes Ergebnisobjekt. Pipeline-Schritte werden über einen dünnen Timing-Wrapper gemessen; Manifeste speichern nur Status, Dauer und Zähler. Security bleibt in separaten GitHub-Workflows.

**Tech Stack:** Python, pytest, GitHub CodeQL, GitHub Secret Scanning, SARIF.

## Global Constraints

- Keine Live-API-Aufrufe in Security- oder Unit-Tests.
- Keine Prompts, API-Keys oder Credentials in Metriken/Manifesten.
- Bestehende CLI-Argumente und Output-Namen bleiben kompatibel.

### Task 1: QAResult in die Pipeline integrieren

**Files:**
- Modify: `qa.py`
- Modify: `podcast_generator.py`
- Test: `tests/test_qa.py`, `tests/test_pipeline_integration.py`

- [ ] `validate_outputs()` gibt QAResult zurück.
- [ ] Pipeline wirft nur bei `result.ok == False` den bestehenden QA-Fehler.
- [ ] Warnings werden geloggt und im Manifest erfasst.
- [ ] Tests für erfolgreichen, warnenden und fehlerhaften Abschluss ergänzen.

### Task 2: Schrittmetriken ergänzen

**Files:**
- Modify: `podcast_generator.py`
- Modify: `productvideo_generator.py`
- Test: Manifest-/Pipeline-Tests

- [ ] Schrittstatus und Dauer messen.
- [ ] Podcast-Step-Plan-Metriken integrieren.
- [ ] Productvideo-Schritte ebenfalls erfassen.
- [ ] Manifestfelder `steps` und `retries` ergänzen.
- [ ] Tests auf Dauer-/Statusfelder ohne Secrets ergänzen.

### Task 3: Security-Workflows

**Files:**
- Create: `.github/workflows/security.yml` je Repository

- [ ] CodeQL-Python-Analyse auf Push/PR und wöchentlich einrichten.
- [ ] Secret-Scanning über GitHub-Mechanismen berücksichtigen.
- [ ] SARIF-Ergebnisse über feste Action-SHAs veröffentlichen.
- [ ] Keine API-Secrets in Security-Jobs verwenden.

### Task 4: Verifikation und PR

- [ ] Unit-/Integrationstests, Ruff, Compile, Markdown und Shell prüfen.
- [ ] CI- und Security-Workflows abwarten.
- [ ] PRs nach grünen Checks mergen und Branches bereinigen.
