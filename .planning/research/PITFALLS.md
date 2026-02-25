# Pitfalls Research

**Domain:** Podcast-Generierungstools (CLI, lokal, externe AI-APIs)
**Researched:** 2026-02-25
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Skript nicht TTS-optimiert

**What goes wrong:**
KI-Skript klingt geschrieben statt gesprochen; Betonung, Zahlen, Abkuerzungen und Fremdwoerter werden falsch vorgelesen.

**Why it happens:**
Prompting fokussiert auf Textqualitaet, nicht auf Sprechbarkeit; keine Aussprache- und Stilregeln.

**How to avoid:**
Sprechstil-Regeln erzwingen (kurze Saetze, harte Umbrueche, gesprochene Zahlen), Aussprache-Lexikon und Post-Processing fuer TTS.

**Warning signs:**
Viele Nachbearbeitungen am Skript, TTS-Ausgabe klingt roboterhaft, haeufige Fehlbetonungen.

**Phase to address:**
Phase 1 (MVP-Textpipeline und Prompting)

---

### Pitfall 2: Audioqualitaet inkonsistent (Lautheit, Rauschen, Mix)

**What goes wrong:**
Episode klingt unprofessionell: falsche Lautheit, schwankende Pegel, Musik ueberdeckt Stimme.

**Why it happens:**
Kein Loudness-Target, kein Limiter/Compressor, kein standardisierter Mix-Workflow.

**How to avoid:**
LUFS-Ziel definieren (z. B. -16 LUFS fuer Stereo), Normalisierung, Limiter und Sidechain/Ducking in der Pipeline.

**Warning signs:**
Nutzer melden „zu leise/zu laut“, Peaks ueber -1 dBFS, Clippen in Ausgaben.

**Phase to address:**
Phase 2 (Audio-Mixing und Export)

---

### Pitfall 3: Lizenzverletzungen bei Musik/SFX/Voice

**What goes wrong:**
Unlizenzierte Assets oder ungeeignete Voice-Rechte fuehren zu rechtlichen Risiken.

**Why it happens:**
Assets werden aus beliebigen Quellen bezogen; Lizenzmodelle (kommerziell, Weitergabe, Derivate) werden ignoriert.

**How to avoid:**
Nur klar lizenzierte Quellen, Lizenz-Checks im Workflow, Metadaten zu Herkunft und Lizenz speichern.

**Warning signs:**
Fehlende Lizenzangaben in Outputs, gemischte Asset-Quellen ohne Nachweis.

**Phase to address:**
Phase 1 (Datenquellen und Asset-Pipeline)

---

### Pitfall 4: Externe AI-APIs nicht robust integriert

**What goes wrong:**
Fehlschlaege durch Rate Limits, Zeitouts, wechselnde Modellversionen; Pipeline bricht ab.

**Why it happens:**
Kein Retry/Backoff, keine Idempotenz, keine Fehlerklassifizierung.

**How to avoid:**
Retry-Strategien, Timeouts, Fallback-Modelle, Idempotenz-Keys, und klarer Error-Handling-Pfad.

**Warning signs:**
Unstabile Runs, manuelle Neustarts, hohes Fehlerrauschen in Logs.

**Phase to address:**
Phase 2 (Stabilitaet und Fehlerbehandlung)

---

### Pitfall 5: Inhaltliche Ungenauigkeit/Halluzinationen

**What goes wrong:**
Falsche Fakten oder Quellenangaben im Skript schaedigen Vertrauen.

**Why it happens:**
Kein Faktencheck, kein Quellen-Workflow, unkritische Uebernahme des LLM-Outputs.

**How to avoid:**
Quellenpflicht fuer Fakten, Zitat-Workflow, optionale Verifikation via URL-Checks oder manuelle Freigabe.

**Warning signs:**
Widersprueche im Skript, fehlende Quellenangaben, Nutzerfeedback zu Fehlern.

**Phase to address:**
Phase 1 (Inhaltserzeugung und Validierung)

---

### Pitfall 6: DACH-spezifische Trends/Quellen ignoriert

**What goes wrong:**
Themen wirken irrelevant fuer Zielregion; unpassende Namen/Begriffe.

**Why it happens:**
Trend-APIs ohne Regionalfilter, Standard-englische Quellen.

**How to avoid:**
Regionale Trendabfrage (DE/AT/CH), Sprach- und Quellenfilter, Fallback-Topics definieren.

**Warning signs:**
Niedrige Relevanz in Nutzerfeedback, Themen wirken „global“ statt lokal.

**Phase to address:**
Phase 1 (Topic- und Trendlogik)

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keine persistente Metadatenablage (nur Dateien) | Schnellere MVP-Lieferung | Keine Nachvollziehbarkeit von Quellen, Lizenzen, Prompts | Nur MVP, wenn Outputs kurzlebig sind |
| Harte Datei-/Ordnernamen | Weniger Konfiguration | Bricht bei Mehrfachruns oder parallelen Jobs | Nie bei Mehrfachruns |
| Kein Caching von AI-Aufrufen | Einfacher Code | Hohe Kosten, laengere Laufzeiten | Nur bei sehr kleiner Nutzung |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Text-LLM | Prompting ohne Token-Budget und Laengenlimit | Laengenlimits erzwingen und chunking verwenden |
| TTS-API | Keine Kontrolle ueber Sampling-Rate/Format | Ausgabeformat festlegen und vor Mix normalisieren |
| Asset-Quelle (Musik/SFX) | Lizenztyp nicht gespeichert | Lizenzmetadaten mit Output persistieren |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Serielle API-Aufrufe ohne Parallelisierung | Runs dauern sehr lange | Parallelisierung pro Segment, aber Rate Limits beachten | Ab 5-10 Segmenten pro Episode |
| Volltext in einem TTS-Call | Lange Wartezeit oder Fehler | Segmentierung nach Saetzen/Abschnitten | Ab 10-15 Minuten Skript |
| Unkomprimierte Zwischenformate | Hoher Speicherverbrauch | Zwischendateien komprimieren/loeschen | Mehrere Runs lokal |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| API-Keys in Logs oder Outputs | Key-Leak, Kostenrisiko | Secrets maskieren, .env nie exportieren |
| Ungepruefte Remote-URLs fuer Quellen | Prompt-Injection/Manipulation | Whitelist, Sanitize, manuelle Freigabe |
| Unsichere Temp-Verzeichnisse | Datenleak auf Mehrbenutzer-Systemen | Isolierte Temp-Pfade und Permissions |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Unklare Fehlermeldungen bei API-Fehlern | Nutzer kann nicht handeln | Konkrete Anleitung (Key fehlt, Rate Limit, Retry) |
| Keine Vorschau/Review des Skripts | Fehler landen direkt im Audio | Script-Review-Option vor TTS |
| Intransparente Laufzeit/Kosten | Ueberraschung und Frust | Schaetzung vor Run (Zeit/Token/Preis) |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Audio-Export:** Lautheitsnormalisierung fehlt — verifiziere LUFS-Ziel und True Peak
- [ ] **Skript-Erstellung:** Quellen fehlen — verifiziere Quellenliste/Footnotes
- [ ] **TTS:** Aussprachefehler — verifiziere Aussprache-Lexikon/SSML-Regeln
- [ ] **Asset-Nutzung:** Lizenz unklar — verifiziere Lizenztyp und Herkunft

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| TTS-Qualitaet schlecht | MEDIUM | Skript nach Sprechregeln anpassen, TTS erneut generieren |
| Mix zu laut/zu leise | LOW | Normalisierung und Limiter neu anwenden |
| Faktenfehler im Skript | MEDIUM | Quellen nachziehen, Segment neu generieren, Audio neu mixen |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Skript nicht TTS-optimiert | Phase 1 | Hoerprobe pro Segment, Sprechregeln angewendet |
| Audioqualitaet inkonsistent | Phase 2 | LUFS/True-Peak Checks im Export |
| Lizenzverletzungen | Phase 1 | Lizenzmetadaten in Output-Dateien |
| Unrobuste API-Integration | Phase 2 | Fehlerklasse + Retry-Tests |
| Faktenfehler/Halluzinationen | Phase 1 | Quellenpflicht + Review-Workflow |
| DACH-Relevanz ignoriert | Phase 1 | Regionale Quellen/Trends dokumentiert |

## Sources

- Erfahrungswissen aus Audio- und TTS-Pipelines (LOW)
- Allgemeine LLM-Integrationsrisiken (LOW)

---
*Pitfalls research for: Podcast-Generierungstools*
*Researched: 2026-02-25*
