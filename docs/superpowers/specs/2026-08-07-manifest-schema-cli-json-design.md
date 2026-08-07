# Manifest-Schema und CLI-JSON

## Ziel

Die beiden lokalen CLIs erhalten ein versioniertes Manifest-Schema, maschinenlesbare Abschlussausgabe und weniger globale Laufzustände.

## Umfang

- JSON Schema `schemas/run-manifest-v1.json` je Repository.
- CI validiert erzeugte Test-Manifeste gegen das Schema.
- `--json` gibt am Ende eine kompakte Ergebnisstruktur mit Status, Manifest und Artefakten aus.
- CLI-JSON enthält keine Secrets, Prompts oder Credentials.
- Retry-Zähler werden pro Generatorlauf statt global geführt.
- Bestehende Textausgabe bleibt Standard.

## Nicht im Umfang

- Keine vollständige Zerlegung der Hauptmodule.
- Keine Lockfiles oder Plattformmatrix.
- Keine Änderung fachlicher Medienpipelines.

## Qualitätskriterien

- Schemaänderungen werden über `schema_version` versioniert.
- JSON-Ausgabe ist valides JSON und stabil maschinenlesbar.
- Standard-CLI ohne `--json` bleibt kompatibel.
- Tests, Ruff, CodeQL und CI bleiben grün.
