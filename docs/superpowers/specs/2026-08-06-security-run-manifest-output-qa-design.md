# Security, Run-Manifest und Output-QA

## Ziel

Die lokale Podcast-CLI erhält reproduzierbare Dependency-Sicherheitsprüfungen und eine mit `productvideo_generator` kompatible Abschluss- und Manifeststruktur, ohne ihre Audio-/Video-Pipeline zu verändern.

## Umfang

- `pip-audit` läuft in CI und blockiert nur bei HIGH/CRITICAL-Schwachstellen.
- LOW/MODERATE-Schwachstellen werden sichtbar gewarnt, blockieren den Build aber nicht.
- Das bestehende Podcast-Manifest wird auf gemeinsame Status-, Laufzeit-, Modell-, Artefakt- und Fehlerfelder geprüft und bei Bedarf minimal ergänzt.
- Der bestehende eigene Output-QA-Schritt bleibt erhalten und wird als verbindlicher Abschluss der Pipeline dokumentiert/getestet.
- Resume- und Force-Restart-Semantik bleiben unverändert.

## Nicht im Umfang

- Keine neuen Cloud- oder Deployment-Jobs.
- Keine echten API-Aufrufe in Tests oder CI.
- Keine gemeinsame Runtime-Bibliothek.
- Keine Änderung der CLI-Argumente oder Output-Namenskonventionen.

## Fehlerverhalten

- QA-Fehler setzen den Laufstatus auf `failed` und führen zu einem Fehler-Exit-Code.
- API-, Konfigurations- und lokale Artefaktfehler bleiben unterscheidbar.
- Secrets und Credentials erscheinen weder im Manifest noch in Audit-Logs.

## Teststrategie

- Regressionstests decken Manifest, QA, Fehlerstatus und Resume-Konsistenz ab.
- Beide CI-Workflows führen `pip-audit` auf Python 3.12 und 3.13 aus.
