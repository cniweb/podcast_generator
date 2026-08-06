# CI- und Integrationsverträge härten

## Ziel

Die beiden lokalen CLI-Projekte erhalten eine wartbarere, sicherere und stärker harmonisierte CI-/Integrationsbasis, ohne Deployment oder fachliche Pipeline-Zusammenlegung.

## Umfang

- GitHub-Actions werden auf nachvollziehbare feste Versionen oder Commit-SHAs geprüft und `@latest` wird entfernt, sofern sicher möglich.
- Gemeinsame CI-Schritte werden über einen wiederverwendbaren Workflow harmonisiert oder als bewusst projektspezifisch dokumentiert.
- Test-, Coverage- und Audit-Artefakte erhalten ein einheitliches Format und eine definierte Aufbewahrungsdauer.
- `pip-audit` unterscheidet Audit-Fehler, keine Findings, Warnungen sowie HIGH/CRITICAL-Funde nachvollziehbar.
- Beide CLIs unterstützen einheitlich `--version` und standardisierte Exit-Codes, ohne bestehende Optionen zu brechen.
- Run-Manifeste enthalten Generator-Version und Laufzeitumgebung, aber keine Secrets.
- Renovate und Dependabot erhalten klar getrennte Verantwortlichkeiten.

## Nicht im Umfang

- Kein Deployment und keine Cloud-Ausführung.
- Keine gemeinsame Runtime-Library.
- Keine Änderung der fachlichen Medienpipelines.
- Keine Live-API-Aufrufe in CI oder Tests.

## Qualitätskriterien

- Beide Repositories bleiben lokal ausführbare CLI-Anwendungen.
- Alle Änderungen werden auf Feature-Branches entwickelt und per PR gemerged.
- Ruff, pytest, Compile-Check, Markdown-Linting und GitHub Actions bleiben grün.
- CLI- und Manifest-Änderungen erhalten Regressionstests.
