# Config-Injektion und Testtrennung

## Ziel

Die Generatoren sollen ihre typisierte Konfiguration tatsächlich übergeben bekommen, die Output-QA als strukturierte Abschlussprüfung verwenden und Unit-/Integrationsprüfungen klar trennen.

## Umfang

- `ProductVideoGenerator` und `PodcastGenerator` akzeptieren ein optionales Config-Objekt.
- CLI-Aufrufe erzeugen die Config einmal und injizieren sie in den Generator.
- Bestehende Tests und externe CLI-Nutzung bleiben kompatibel.
- Output-QA gibt strukturierte Ergebnisse zurück und wirft nur an der Pipelinegrenze einen Fehler.
- pytest-Marker `unit`, `integration`, `requires_ffmpeg` und `network` werden definiert.
- CI führt standardmäßig nur deterministische Tests aus und schließt `network` aus.
- Security-Findings werden geprüft; es werden nur verifizierte Dependency-Updates übernommen.

## Nicht im Umfang

- Keine gemeinsame Runtime-Library.
- Keine Lockfiles oder uv-Einführung.
- Keine CodeQL-/Plattformmatrix.
- Keine Änderung fachlicher Medienpipelines.

## Qualitätskriterien

- Generatoren sind ohne globale Konfigurationsmutation isoliert testbar.
- QA-Fehler werden im Manifest und Exit-Code korrekt dargestellt.
- Marker sind dokumentiert und CI reproduzierbar.
- GitHub Actions, Ruff, pytest und Audit bleiben grün.
