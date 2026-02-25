# Architecture Research

**Domain:** Podcast-Generierungstools (CLI, lokal, externe AI-APIs)
**Researched:** 2026-02-25
**Confidence:** LOW

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Orchestration                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Config   │  │ Topic    │  │ Script   │  │ TTS      │     │
│  │ & Input  │  │/Trends   │  │ Generator│  │ Generator│     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │             │            │             │            │
├───────┴─────────────┴────────────┴─────────────┴───────────┤
│                     Processing Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Fact/    │  │ Segment  │  │ Audio    │  │ Export   │     │
│  │ Source   │  │ & Cache  │  │ Mixing   │  │ & Metadata│     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
├─────────────────────────────────────────────────────────────┤
│                        Storage Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Temp     │  │ Assets   │  │ Outputs  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| CLI Orchestrator | End-to-end run, stage sequencing, error handling | Python CLI module, run script |
| Config/Input | Load .env, validate paths, parse topic args | dotenv + config loader |
| Topic/Trends | Resolve topic from user input or trend APIs | Trend provider + fallback list |
| Script Generator | Create spoken-style script with constraints | LLM provider wrapper + prompt templates |
| Fact/Source Manager | Track sources, citations, and validation flags | Metadata file + optional URL checker |
| TTS Generator | Synthesize narration audio per segment | TTS provider client + SSML rules |
| Segment & Cache | Chunk script, cache intermediate artifacts | Chunker + local cache dir |
| Audio Mixing | Normalize, duck music, mix tracks, loudness target | ffmpeg/ffprobe + mixing pipeline |
| Export & Metadata | Final audio + episode metadata bundle | MP3 export + JSON/CSV metadata |
| Storage Layer | Temp, assets, and output folders | Local filesystem with stable paths |

## Recommended Project Structure

```
src/
├── cli/                # CLI entrypoints and argument parsing
├── config/             # Env validation and path resolution
├── pipeline/           # Orchestration and stage runners
├── providers/          # LLM, TTS, trends, assets integrations
├── text/               # Prompting, chunking, script post-processing
├── audio/              # Mixing, normalization, export
├── metadata/           # Sources, licenses, episode metadata
├── storage/            # Temp/output path helpers
└── utils/              # Shared helpers (logging, retries)
```

### Structure Rationale

- **pipeline/:** Keeps stage order explicit and testable per step.
- **providers/:** Isolates external APIs for swapping/fallbacks.

## Architectural Patterns

### Pattern 1: Stage-Based Pipeline

**What:** Each generation step produces artifacts consumed by the next stage.
**When to use:** Always for deterministic, debuggable runs.
**Trade-offs:** More I/O and intermediate files, but clearer recovery.

**Example:**
```python
def run_pipeline(topic: str) -> str:
    script = generate_script(topic)
    segments = chunk_script(script)
    narration = synthesize_segments(segments)
    mixed = mix_audio(narration, background_music())
    return export_episode(mixed)
```

### Pattern 2: Provider Abstraction

**What:** Wrap LLM/TTS/trend services behind a common interface.
**When to use:** When multiple vendors or fallback models are likely.
**Trade-offs:** Slightly more boilerplate; pays off on outages.

**Example:**
```python
class TtsProvider:
    def synthesize(self, text: str, voice: str) -> bytes:
        raise NotImplementedError
```

### Pattern 3: Idempotent Runs with Cache

**What:** Cache step outputs keyed by topic + params to allow resume.
**When to use:** Long runs or rate-limited APIs.
**Trade-offs:** Needs careful cache invalidation.

## Data Flow

### Request Flow

```
User Topic/Args
    ↓
CLI Orchestrator → Config Validation → Topic Resolution
    ↓
Script Generator → Chunking/SSML → TTS per Segment
    ↓
Audio Mixing → Loudness Normalize → Export
    ↓
Episode Audio + Metadata + Logs
```

### Key Data Flows

1. **Topic to Script:** Topic input becomes script text with sources and style rules.
2. **Script to Audio:** Script is chunked, synthesized, and mixed with assets.
3. **Assets to Output:** Music/SFX and license metadata flow into final bundle.

## Build Order Implications

1. **Config + Storage:** Required for every stage; define paths and validation first.
2. **Topic/Script Generation:** Core content dependency for TTS and audio.
3. **TTS + Chunking:** Depends on script and voice rules; enables audio testing.
4. **Audio Mixing + Export:** Depends on narration output; adds loudness constraints.
5. **Metadata + Licensing:** Depends on assets and sources; finalize outputs.
6. **Resilience Layer:** Retries, caching, and cost estimation build on all stages.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k users | Single-process CLI, local filesystem is sufficient |
| 1k-100k users | Queue + worker process, cache store, parallel TTS |
| 100k+ users | Distributed job orchestration, object storage, monitoring |

### Scaling Priorities

1. **First bottleneck:** TTS latency and rate limits; add chunk parallelism and retries.
2. **Second bottleneck:** Audio processing time; batch operations or GPU-accelerated tools.

## Anti-Patterns

### Anti-Pattern 1: Single Giant Prompt for TTS

**What people do:** Send full script in one TTS call.
**Why it's wrong:** Timeouts, poor prosody control, expensive retries.
**Do this instead:** Chunk by sentence/section with consistent voice rules.

### Anti-Pattern 2: Mixing Without Loudness Targets

**What people do:** Mix voice and music without LUFS/True Peak checks.
**Why it's wrong:** Inconsistent volume and clipping.
**Do this instead:** Normalize and verify loudness targets per export.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| LLM API | HTTP client with retries/backoff | Enforce token limits, safety settings |
| TTS API | HTTP client + SSML | Specify sample rate and audio format |
| Trends API | HTTP client with regional filter | DACH focus with fallback |
| Asset Library | Download + license metadata | Persist license data with outputs |
| ffmpeg/ffprobe | Local subprocess | Validate availability on startup |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| pipeline ↔ providers | direct API calls | Keep provider errors typed |
| pipeline ↔ audio | file-based artifacts | Stable temp/output paths |
| text ↔ metadata | structured JSON | Use schema for sources/licenses |

## Sources

- No external sources used (general architecture patterns) (LOW)

---
*Architecture research for: Podcast-Generierungstools*
*Researched: 2026-02-25*
