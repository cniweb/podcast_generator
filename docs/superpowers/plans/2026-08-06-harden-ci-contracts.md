# CI- und Integrationsverträge härten Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CI-Sicherheit, Audit-Auswertung, Artefakte sowie CLI- und Manifest-Verträge der lokalen Generatoren angleichen.

**Architecture:** Gemeinsame CI-Schritte werden in einen wiederverwendbaren Workflow ausgelagert, während FFmpeg und fachliche Testziele als Inputs projektspezifisch bleiben. CLI- und Manifest-Erweiterungen bleiben lokal in den jeweiligen Hauptmodulen.

**Tech Stack:** GitHub Actions, reusable workflows, Python, pytest, pip-audit, Ruff, Renovate.

## Global Constraints

- Kein Deployment und keine Cloud-Ausführung.
- Keine gemeinsame Runtime-Library.
- Keine Live-API-Aufrufe in CI oder Tests.
- Bestehende CLI-Optionen und Output-Namen bleiben kompatibel.
- Keine Secrets in Logs, Artefakten oder Manifesten.

### Task 1: Action-Pinning und Workflow-Sicherheit

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/opencode.yml`
- Modify: `.github/workflows/renovate.yml`

- [ ] Alle verwendeten Action-Versionen erfassen.
- [ ] `@latest` bei OpenCode entfernen oder als begründete Ausnahme dokumentieren.
- [ ] Least-Privilege-Berechtigungen pro Workflow prüfen.
- [ ] Concurrency und Fork-/Secret-Grenzen beibehalten.
- [ ] Workflow-Syntax validieren.

### Task 2: Reusable CI und Artefakte

**Files:**
- Create: `.github/workflows/reusable-python-ci.yml`
- Modify: `.github/workflows/ci.yml`

- [ ] Inputs für Python-Versionen, Compile-Ziele, Coverage-Ziele und optionale FFmpeg-Prüfung definieren.
- [ ] Gemeinsame Schritte auslagern: Installation, Ruff, Compile, pytest, Markdown, Reports und Audit.
- [ ] Artefakte einheitlich als Test-, Coverage- und Audit-Reports mit `retention-days: 14` hochladen.
- [ ] Projektspezifische Ziele über Inputs steuern.
- [ ] Beide Matrix-Versionen erfolgreich ausführen.

### Task 3: Robuste Audit-Auswertung

**Files:**
- Modify: `.github/workflows/reusable-python-ci.yml`
- Test: `.github/scripts/parse_pip_audit.py`

- [ ] Audit-JSON in eine kleine getestete Python-Auswertung auslagern.
- [ ] Zustände `audit_error`, `clean`, `warning` und `blocking` unterscheiden.
- [ ] HIGH/CRITICAL blockieren; LOW/MODERATE warnen.
- [ ] Audit-JSON als Artefakt veröffentlichen.
- [ ] Unit-Tests für alle vier Zustände ergänzen.

### Task 4: CLI- und Manifest-Verträge

**Files:**
- Modify: `podcast_generator.py`
- Modify: `tests/test_env_and_cli.py`
- Modify: `tests/test_pipeline_integration.py`

- [ ] `--version` in der Podcast-CLI ergänzen.
- [ ] Exit-Codes für Erfolg, Laufzeitfehler und ungültige Argumente standardisieren.
- [ ] Versionswert zentral und ohne zusätzliche Runtime-Abhängigkeit bereitstellen.
- [ ] Generator-Version, Python-Version und Plattform in Run-Manifeste aufnehmen.
- [ ] Tests ergänzen, die Secrets nicht im Manifest finden.

### Task 5: Dependency-Automatisierung dokumentieren

**Files:**
- Modify: `renovate.json`
- Modify: `README.md`
- Modify: `AGENTS.md`

- [ ] Renovate als geplante Update-Automatisierung dokumentieren.
- [ ] Dependabot Security Alerts als Sicherheitskanal dokumentieren.
- [ ] Doppelzuständigkeiten und erwartete PR-Arten festhalten.

### Task 6: Verifikation und PR

- [ ] Lokale Tests, Ruff, Compile-Check, Markdown-Linting und Shell-Syntax ausführen.
- [ ] Reusable Workflows mit beiden Projekten in GitHub Actions prüfen.
- [ ] PRs erstellen, CI und Audit-Artefakte prüfen.
- [ ] Nur vollständig grüne PRs mergen.
