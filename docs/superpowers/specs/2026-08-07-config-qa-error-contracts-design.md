# Config-, QA- und Fehlerverträge

## Ziel

Die bereits injizierten Config-Objekte werden in zentralen Generatorpfaden tatsächlich genutzt. Manifestfehler werden strukturiert gespeichert und Retry-Zähler zuverlässig gepflegt.

## Umfang

- Productvideo verwendet `self.config` für Kanal, Output-Verzeichnis und Video-Modelle.
- Podcast verwendet `self.config` für Podcastname, Pfade und Skriptmodell in zentralen Generatorpfaden.
- Manifestfehler werden als `{type, message, retryable}` gespeichert.
- Retry-Zähler werden bei tatsächlichen Wiederholungen und Modell-/TTS-Fallbacks erhöht.
- QA bleibt der verbindliche Pipelineabschluss.
- Kritische Tests decken Config-Injektion, Fehlerobjekte und Retry-Zähler ab.

## Nicht im Umfang

- Keine neue gemeinsame Runtime-Library.
- Keine Änderung fachlicher Prompts oder Medienformate.
- Keine Lockfiles, CodeQL-Änderungen oder Plattformmatrix.

## Qualitätskriterien

- Explizit injizierte Configs beeinflussen den Lauf unabhängig von globalen Defaults.
- Manifestfehler sind maschinenlesbar und secret-frei.
- Retry-Zähler sind nicht negativ und stimmen mit tatsächlichen Wiederholungen überein.
