# Podcast Generator

## What This Is

Podcast Generator is a CLI tool that takes a topic and produces a ready-to-publish podcast episode for content creators. It outputs a script, narration audio, and supporting metadata with minimal manual work.

## Core Value

Turn a topic into a complete, listenable podcast episode with minimal manual effort.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Generate a podcast script from a topic input
- [ ] Synthesize narration audio from the generated script
- [ ] Mix narration with background music and export episode audio

### Out of Scope

- Podcast hosting/distribution platform — focus is generation only
- Multi-user web dashboard — CLI-first workflow for now

## Context

- Automated, local pipeline intended to run from the CLI
- Uses external AI services for text and voice generation
- Produces audio plus metadata assets for creators

## Constraints

- **Dependencies**: Requires API keys for AI services — needed to generate script/audio
- **Environment**: Requires ffmpeg/ffprobe installed for audio/video processing

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI-first workflow | Simple local automation for creators | — Pending |
| External AI services for script/voice | Faster iteration and higher quality output | — Pending |

---
*Last updated: 2026-02-25 after initialization*
