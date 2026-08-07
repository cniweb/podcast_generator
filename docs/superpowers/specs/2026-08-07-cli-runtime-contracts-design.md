# CLI- und Runtime-Verträge

## Ziel

Die lokalen CLI-Generatoren verwenden gemeinsame, dokumentierte Verträge für Exit-Codes, Run-Manifeste, Fehlerklassen, Retries und Testfixtures, ohne ihre fachlich unterschiedlichen Medienpipelines zu vereinigen.

## Umfang

- Gemeinsame Exit-Codes: `0` Erfolg, `1` Laufzeit/API/QA-Fehler, `2` ungültige CLI-Argumente oder Konfiguration.
- Gemeinsames Manifest-Schema mit `schema_version`, Generator, Version, Status, Runtime, Modellen, Artefakten und Fehler.
- Gemeinsame Fehlerkategorien für Konfiguration, externe Dienste, Rate Limits, Generierung und Output-QA.
- Productvideo erhält begrenzte Retry-/Backoff-Logik für geeignete externe Fehler.
- Bestehende Podcast-Retry-Logik wird auf den gemeinsamen Vertrag geprüft, nicht unnötig neu geschrieben.
- Testfixtures werden je Repository zentralisiert, ohne neue externe Runtime-Abhängigkeit.
- Runtime- und Entwicklungsabhängigkeiten werden getrennt, sofern die vorhandenen Skripte und CI-Verträge dabei kompatibel bleiben.

## Nicht im Umfang

- Keine gemeinsame Runtime-Library zwischen den Repositories.
- Keine Änderung der fachlichen Audio-/Video-Pipelines.
- Keine Änderung bestehender CLI-Optionen außer der standardisierten Fehler-/Versionsbehandlung.
- Keine Live-API-Aufrufe in Tests.

## Qualitätskriterien

- Alle neuen Verträge sind durch deterministische Tests abgedeckt.
- Fehlermeldungen bleiben deutsch und enthalten keine Secrets.
- Manifestdateien enthalten keine API-Keys, Prompts oder Credentials.
- CI, Ruff, Compile-Checks, Markdown-Linting und CLI-Tests bleiben grün.
