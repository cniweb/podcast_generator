# External Adapter Seams

## Ziel

Die externen Dienste des Podcast Generators werden hinter kleinen Interfaces
verborgen. Die Pipeline bleibt fachlich unverändert; DACH-Trends, Fallbacks,
TTS-Verträge, Dateinamen und CLI-Verhalten bleiben stabil.

## Architektur

Ein `adapters.py`-Modul definiert `TrendProvider`, `TextGenerator`,
`MusicProvider`, `SpeechSynthesizer`, `MediaRenderer` und die zugehörigen
Ergebnisverträge. Bestehende HTTP-, Gemini-, Google-Cloud-TTS- und
Dateisystemzugriffe werden als konkrete Adapter implementiert. Der Generator
akzeptiert optionale Adapter und verwendet standardmäßig die Produktionsadapter.

Tests injizieren In-Memory-Adapter. Dadurch werden keine echten Netzwerkaufrufe
benötigt und die fachlichen Methoden werden über ihre externe seam getestet.

## Umfang

- Adapter für Trends, Text, Musik, Sprache, Video und Artefaktpersistenz.
- Bestehende Retry-/Fallback-Logik bleibt erhalten.
- Keine neuen Laufzeitabhängigkeiten.
- Keine Änderung an CLI-Ausgabe oder Manifestformat.
- Deterministische Tests für Injektion und die bestehenden Produktionspfade.
