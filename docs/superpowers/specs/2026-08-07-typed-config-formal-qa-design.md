# Typisierte Konfiguration und formale QA

## Ziel

Die beiden lokalen Generatoren erhalten klarere Konfigurationsgrenzen, formale Manifest-/Output-Validierung und gezielte Tests für kritische Fehlerpfade, ohne die fachlichen Medienpipelines zusammenzulegen.

## Umfang

- Konfiguration wird je Projekt in einem unveränderlichen, typisierten Objekt gebündelt.
- Pflicht- und optionale Umgebungsvariablen werden zentral validiert.
- Manifestvalidierung prüft `schema_version`, `generator`, Status, Runtime, Modelle, Artefakte und Fehlerfeld.
- Output-QA liefert strukturierte Fehler/Warnungen und bewahrt bestehende CLI-Semantik.
- Kritische Fehlerpfade werden gezielt getestet: Konfiguration, Polling, Fallback, QA, Resume und atomare Writes.

## Nicht im Umfang

- Keine gemeinsame Runtime-Library.
- Keine Änderung der fachlichen Prompts oder Medienformate.
- Keine Lockfile-/uv-Einführung.
- Keine CodeQL- oder Plattform-Matrix in diesem Block.
- Keine Live-API-Aufrufe in Tests.

## Qualitätskriterien

- Konfigurationsobjekte enthalten keine ausgegebenen Secrets.
- Ungültige Manifeste werden vor dem Erfolgsstatus abgewiesen.
- Bestehende CLI-Optionen und Output-Namen bleiben kompatibel.
- Tests, Ruff, Compile, Markdown und CI bleiben grün.
