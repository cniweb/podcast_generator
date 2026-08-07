# Output-Pipeline härten

## Ziel

Die Productvideo-Ausführung soll bei API-Hängern, Modell-Fallbacks und Teilfehlern deterministisch abbrechen und nur validierte Artefakte als erfolgreich markieren. Gemeinsame Output-QA-Verträge werden auf den Podcast übertragen, ohne die Pipelines zusammenzulegen.

## Umfang

- Veo-Polling erhält maximale Wartezeit und begrenzte Abfrageanzahl.
- Primär- und Fallbackmodellfehler führen bei vollständigem Fehlschlag zu einem eindeutigen `GenerationError`.
- Productvideo- und Podcast-Manifest werden gegen ein kleines Schema validiert.
- Output-QA liefert strukturierte Fehler und Warnungen.
- JSON-, Audio- und Videodateien werden möglichst atomar geschrieben.
- Kritische Fehlerpfade erhalten deterministische Tests.
- Die bekannte moderate Dependency-Warnung wird analysiert und, falls sicher möglich, behoben.

## Nicht im Umfang

- Keine neue gemeinsame Runtime-Library.
- Keine Änderung der fachlichen Prompts oder Medienformate.
- Keine Live-API-Aufrufe in Tests.
- Kein Deployment.

## Qualitätskriterien

- Kein unbegrenztes Warten auf externe Operationen.
- Kein erfolgreicher Lauf bei fehlenden oder ungültigen Artefakten.
- Abgebrochene Schreibvorgänge hinterlassen keine halbfertigen Zielartefakte.
- Unit- und Integrationstests bleiben deterministisch.
