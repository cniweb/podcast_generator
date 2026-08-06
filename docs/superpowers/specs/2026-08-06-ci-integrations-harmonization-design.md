# CI- und Integrationsharmonisierung

## Ziel

Der lokale CLI-Charakter des Podcast-Generators bleibt unverändert. Dieses Vorhaben harmonisiert nur Entwicklungsqualität und externe Integrationsgrenzen mit `productvideo_generator`.

## Umfang

- GitHub Actions verwenden einheitliche Sicherheits-, Cache- und Concurrency-Regeln.
- CI prüft Abhängigkeiten, Ruff, Python-Kompilierung, Tests und Markdown.
- Testresultate und Coverage werden reproduzierbar erzeugt und als Artefakte veröffentlicht.
- Lokale Skripte verwenden konsistente Python-/venv-Aufrufe und bleiben ohne Cloud-Deployment nutzbar.
- Dependency-Updates werden über Renovate in beiden Repositories gleich behandelt.
- FFmpeg bleibt eine lokale bzw. CI-Systemvoraussetzung des Podcast-Generators.

## Nicht im Umfang

- Kein Deployment und keine Veröffentlichung generierter Medien.
- Keine echten Gemini-, Trends-, Freesound- oder Google-Cloud-Aufrufe in CI.
- Keine Zusammenlegung der fachlichen Generator-Pipelines.
- Keine Änderungen an API-Secrets, Credentials oder generierten lokalen Dateien.

## Umsetzung

1. Baseline pro Repository erfassen: Status, Tests, Ruff, Compile-Check und Markdown-Linting.
2. Productvideo-CI an die gemeinsame Qualitätsbasis anpassen.
3. Productvideo-Lokalwerkzeuge an plattformtaugliche `python -m`-Aufrufe anpassen.
4. Renovate für Productvideo ergänzen und Dependency-Konfiguration vergleichen.
5. Podcast-CI und Lokalwerkzeuge auf dieselben Sicherheits- und Ausführungsstandards bringen.
6. FFmpeg in CI explizit prüfen, ohne automatische Paketinstallation im Testlauf.
7. Jeden Schritt mit den betroffenen Tests und Lintern prüfen.
8. Pro Repository Commits erstellen, Branches pushen und Pull Requests öffnen.
9. GitHub-Actions-Ergebnisse prüfen und Fehler gezielt beheben.
10. Nur grüne Pull Requests mergen.

## Qualitätskriterien

- Keine Änderung der CLI-Eingaben, Resume-Optionen oder Output-Namenskonventionen.
- Unit-Tests bleiben netzwerkfrei und deterministisch.
- CI nutzt Least-Privilege-Berechtigungen.
- CI-Läufe desselben Branches werden durch Concurrency begrenzt.
- Action-Versionen werden nicht unkontrolliert über `latest` bezogen.
- Lokale Checks und GitHub Actions führen dieselben wesentlichen Prüfungen aus.
