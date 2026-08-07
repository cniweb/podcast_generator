# Integrierte QA, Laufmetriken und Security-Checks

## Ziel

Die Output-QA wird zum verbindlichen Pipelineabschluss, Run-Manifeste enthalten Schrittmetriken und beide Repositories erhalten zusätzliche automatisierte Sicherheitsprüfungen.

## Umfang

- `validate_outputs()` liefert ein strukturiertes `QAResult` und wird am Pipelineabschluss ausgewertet.
- QA-Fehler aktualisieren das Manifest mit `failed` und führen zu Exit-Code 1.
- Run-Manifeste enthalten Dauer und Status je Pipeline-Schritt sowie Retry-Zähler, soweit verfügbar.
- CI ergänzt Secret-Scanning und CodeQL für Python, ohne API-Aufrufe auszuführen.
- Security-Ergebnisse werden als SARIF oder CI-Artefakte veröffentlicht.
- Bestehende Config-Injektion und Testmarker werden weiterverwendet.

## Nicht im Umfang

- Keine gemeinsame Runtime-Library.
- Keine Lockfiles oder Plattform-Matrix.
- Keine Änderungen der Medienpipeline oder CLI-Argumente.
- Keine Veröffentlichung generierter Medien.

## Qualitätskriterien

- Ein Lauf kann nicht als `completed` gelten, wenn QA fehlschlägt.
- Schrittmetriken enthalten keine Secrets oder Promptinhalte.
- Security-Checks bleiben für lokale CLI-Projekte reproduzierbar.
- GitHub Actions, Ruff, pytest und Markdown bleiben grün.
