# Manifest-Schema und CLI-JSON Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Versionierte Manifeste und maschinenlesbare CLI-Ergebnisse bereitstellen.

**Architecture:** JSON Schema bleibt ein statisches Repository-Artefakt. Die CLI-Ausgabe referenziert das fertige Manifest und nutzt ausschließlich sichere Artefakt-/Statusdaten. Retry-Zähler werden in der Generatorinstanz geführt.

**Tech Stack:** Python JSON, JSON Schema, pytest, GitHub Actions.

## Global Constraints

- Textausgabe bleibt Standard.
- `--json` enthält keine Secrets.
- Keine Live-API-Aufrufe in Tests.

### Task 1: Manifest-Schema

**Files:**
- Create: `schemas/run-manifest-v1.json`
- Modify: `qa.py`
- Test: `tests/test_qa.py`

- [ ] Pflichtfelder und Statuswerte im Schema definieren.
- [ ] Fehlerobjekt, Runtime, Steps, Retries und Artefakte beschreiben.
- [ ] Pure Python-Validierung gegen die wichtigsten Schemaanforderungen testen.

### Task 2: `--json`-CLI-Ausgabe

**Files:**
- Modify: `podcast_generator.py`
- Modify: CLI-Tests

- [ ] `--json` ergänzen.
- [ ] Ergebnisobjekt nur am erfolgreichen/fehlgeschlagenen Laufende ausgeben.
- [ ] Manifestpfad und Artefakte ausgeben.
- [ ] Tests für valides JSON und Secretfreiheit ergänzen.

### Task 3: Laufgebundene Retry-Zähler

- [ ] Globalen Retry-Zähler in Generatorzustand verschieben.
- [ ] Tests für zwei unabhängige Generatorinstanzen ergänzen.

### Task 4: CI- und Verifikation

- [ ] Schema-/CLI-Tests, Ruff, Compile, Markdown, Shell und Security prüfen.
- [ ] PRs erstellen und CI abwarten.
- [ ] Nur grüne PRs mergen und Branches bereinigen.
