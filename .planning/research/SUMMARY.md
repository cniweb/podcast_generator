# Project Research Summary

**Project:** Podcast Generator
**Domain:** CLI podcast generation (script + TTS + audio mixing)
**Researched:** 2026-02-25
**Confidence:** MEDIUM

## Executive Summary

This project is a CLI-first podcast generator that turns a topic into a ready-to-publish episode (script, narration audio, and metadata). Experts build this as a stage-based pipeline: config + topic resolution → LLM script → chunked TTS → audio mixing + loudness normalization → export + metadata. The research aligns on a Python orchestration layer with FFmpeg as the audio backbone and provider abstractions for LLM/TTS to keep vendor flexibility and resilience.

The recommended approach is to ship an MVP that validates the core promise: topic-to-script, TTS narration, and a baseline mastering pipeline with MP3 export. Keep the system modular (pipeline stages + provider wrappers) and enforce spoken-style scripting and segment-level TTS. Use FFmpeg for mixing and loudness targets, and persist metadata/licenses early to avoid legal risk. Defer high-complexity integrations (publishing targets, batch automation, multi-voice) until post-validation.

Key risks are (1) scripts that are not TTS-optimized, (2) inconsistent audio quality without loudness targets, (3) licensing and source provenance gaps, and (4) brittle external API integrations. Mitigations are explicit spoken-style rules, chunking + SSML, loudness checks (LUFS/True Peak), license metadata persistence, and retry/idempotent patterns for API calls.

## Key Findings

### Recommended Stack

The research supports a Python 3.12 CLI orchestrator with FFmpeg 8.x for audio processing, and provider SDKs for LLM/TTS (OpenAI + Google GenAI for text, ElevenLabs for voice). This stack maximizes local CLI reliability, audio quality control, and vendor flexibility. Avoid pydub and ffmpeg-python due to maintenance and control limitations.

**Core technologies:**
- **Python 3.12.x:** Pipeline orchestration and CLI runtime — stable audio/AI ecosystem and packaging.
- **FFmpeg 8.0.1:** Mixing, normalization, and export — de-facto audio pipeline standard.
- **Typer 0.24.1:** CLI framework — modern typed CLI with good UX.
- **OpenAI SDK 2.24.0:** Script generation — official SDK with structured responses.
- **Google GenAI SDK 1.64.0:** LLM fallback/diversity — vendor resilience.
- **ElevenLabs SDK 2.36.1:** TTS narration — high-quality voices and controls.

### Expected Features

MVP must cover topic → script → TTS → loudness-normalized output with MP3 export. Differentiators add polish (mastering, chaptering, multi-voice), while publishing integrations and batch automation are best deferred.

**Must have (table stakes):**
- Topic input → spoken-style script generation — core value.
- TTS narration output — listenable episode.
- Audio post-processing (loudness normalization + mix) — baseline quality.
- Export MP3 + basic metadata — usable in podcast workflows.

**Should have (competitive):**
- Show notes + transcript — distribution and accessibility.
- Background music mix with license tracking — polished output without legal risk.
- Automatic chaptering — premium navigation and SEO.

**Defer (v2+):**
- Publishing integrations — operational complexity.
- Batch/watch-folder automation — requires job management.
- Multi-voice narration — higher TTS cost/complexity.

### Architecture Approach

Use a stage-based pipeline with provider abstractions and idempotent caching. Each stage emits artifacts for the next (script → segments → narration → mix → export). Keep boundaries clean between providers, text processing, audio pipeline, and metadata so each can evolve independently.

**Major components:**
1. **CLI Orchestrator + Config/Input** — validate env, parse topic, control run order.
2. **Script + TTS Pipeline** — prompt templates, chunking, SSML rules, TTS per segment.
3. **Audio Mixing + Export** — FFmpeg-based loudness targets, ducking, and final MP3 with metadata.
4. **Metadata/Assets** — sources, licenses, show notes, transcript outputs.

### Critical Pitfalls

1. **Script not optimized for TTS** — enforce spoken-style rules, pronunciation lexicon, SSML, and chunking.
2. **Inconsistent audio quality** — define LUFS targets, apply normalization/limiter, verify True Peak.
3. **Licensing violations (music/voice)** — use licensed assets only and persist license metadata.
4. **Brittle API integrations** — retries/backoff, idempotency keys, and fallback providers.
5. **Fact errors/hallucinations** — require sources, add review/verification step.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Core Content Pipeline (MVP)
**Rationale:** Script generation and TTS are hard dependencies for all downstream audio stages.
**Delivers:** Topic → script (spoken style), chunked TTS narration, basic MP3 export.
**Addresses:** Topic → script, TTS narration, export MP3 + metadata.
**Avoids:** TTS-unfriendly scripts, hallucinations, and DACH-irrelevant topics.

### Phase 2: Audio Quality + Resilience
**Rationale:** Audio mixing and robust API integration determine perceived quality and stability.
**Delivers:** Loudness-normalized mix (LUFS/True Peak), music ducking, retry/idempotent API runs.
**Uses:** FFmpeg 8.x, provider abstractions, caching hooks.
**Implements:** Audio mixing/export components and resilience layer.

### Phase 3: Distribution-Ready Metadata
**Rationale:** Show notes/transcripts and license tracking make outputs usable and compliant.
**Delivers:** Show notes + transcript, asset license metadata, chaptering.
**Addresses:** Show notes/transcripts, background music presets with licensing, chapter metadata.

### Phase 4: Scale & Differentiators (Post-PMF)
**Rationale:** High complexity features should wait until MVP adoption validates demand.
**Delivers:** Batch/watch-folder automation, multi-voice narration, publishing integrations.

### Phase Ordering Rationale

- Script → TTS → audio mix is a strict dependency chain; phases follow this order.
- Provider abstractions and cacheability protect against API outages and cost spikes.
- Early metadata and licensing prevent legal risk before adding distribution features.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** Audio mastering defaults (LUFS targets, EQ/limiter chain) and FFmpeg filter tuning.
- **Phase 4:** Publishing APIs and auth workflows; batch automation reliability and cost controls.

Phases with standard patterns (skip research-phase):
- **Phase 1:** CLI orchestration, prompt templating, and chunked TTS are well-established patterns.
- **Phase 3:** Transcript/show notes generation follows standard LLM summarization workflows.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Versions and choices validated via official package sources. |
| Features | MEDIUM | Derived from competitor feature sets and common expectations. |
| Architecture | LOW | Based on general patterns without external validation. |
| Pitfalls | MEDIUM | Domain experience patterns; not tied to formal sources. |

**Overall confidence:** MEDIUM

### Gaps to Address

- **Audio mastering defaults:** Validate LUFS/True Peak targets and mixing chain for target platforms.
- **Source verification workflow:** Decide how much factual checking is required vs. manual review.
- **Licensing policy:** Confirm allowable asset sources and how license metadata is stored.
- **Scaling thresholds:** Define when to add caching/parallelism based on expected usage.

## Sources

### Primary (HIGH confidence)
- None identified in research.

### Secondary (MEDIUM confidence)
- https://ffmpeg.org/download.html — FFmpeg 8.0.1 release info.
- https://pypi.org/project/typer/ — Typer 0.24.1.
- https://pypi.org/project/openai/ — OpenAI SDK 2.24.0.
- https://pypi.org/project/google-genai/ — Google GenAI SDK 1.64.0.
- https://pypi.org/project/elevenlabs/ — ElevenLabs SDK 2.36.1.
- https://pypi.org/project/python-dotenv/ — python-dotenv 1.2.1.
- https://pypi.org/project/httpx/ — httpx 0.28.1.
- https://pypi.org/project/soundfile/ — soundfile 0.13.1.
- https://pypi.org/project/av/ — PyAV 16.1.0.
- https://pypi.org/project/ruff/ — ruff 0.15.2.
- https://pypi.org/project/pytest/ — pytest 9.0.2.
- https://auphonic.com/features — audio processing feature expectations.
- https://auphonic.com/workflows-api — automation patterns.
- https://www.descript.com/podcasting — competitor feature set.
- https://riverside.fm/ai — competitor feature set.

### Tertiary (LOW confidence)
- Architecture patterns and pitfalls derived from domain experience (no external validation).

---
*Research completed: 2026-02-25*
*Ready for roadmap: yes*
