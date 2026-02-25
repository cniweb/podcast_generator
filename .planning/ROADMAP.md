# Roadmap: Podcast Generator

## Overview

Deliver a CLI pipeline that turns a topic into a complete, listenable podcast episode by progressively adding spoken-style scripting, reliable narration, polished audio processing, and distribution-ready outputs.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Script Generation** - Produce spoken-style scripts from a topic input.
- [ ] **Phase 2: Narration Generation** - Turn scripts into reliable narration audio.
- [ ] **Phase 3: Audio Processing** - Normalize narration and mix with background music.
- [ ] **Phase 4: Export & Metadata** - Export publishable outputs with metadata and licensing.

## Phase Details

### Phase 1: Script Generation
**Goal**: Users can turn a topic into a narration-ready script.
**Depends on**: Nothing (first phase)
**Requirements**: SCRIPT-01, SCRIPT-02
**Success Criteria** (what must be TRUE):
  1. User can provide a topic and receive a spoken-style script in one CLI run.
  2. The script length and structure are suitable for narration without manual editing.
**Plans**: 1 plan

Plans:
- [ ] 01-script-generation-01-PLAN.md — Enforce script constraints with validation, retries, and tests

### Phase 2: Narration Generation
**Goal**: Users can generate stable narration audio from scripts.
**Depends on**: Phase 1
**Requirements**: TTS-01, TTS-02
**Success Criteria** (what must be TRUE):
  1. User can generate narration audio from the script via the CLI.
  2. Long scripts are automatically chunked so narration completes without failures.
**Plans**: TBD

### Phase 3: Audio Processing
**Goal**: Users get consistent audio quality with optional background music.
**Depends on**: Phase 2
**Requirements**: AUDIO-01, AUDIO-02
**Success Criteria** (what must be TRUE):
  1. Narration audio is normalized to a consistent loudness target across runs.
  2. Background music can be mixed at safe levels without overpowering narration.
**Plans**: TBD

### Phase 4: Export & Metadata
**Goal**: Users can export publishable episode assets with required metadata.
**Depends on**: Phase 3
**Requirements**: EXPORT-01, EXPORT-02, LICENSE-01
**Success Criteria** (what must be TRUE):
  1. User can export the final episode audio as MP3 with basic metadata.
  2. Show notes and transcript are generated for the episode.
  3. Music license/source metadata is stored alongside outputs.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Script Generation | 1/1 | Complete | 2026-02-25 |
| 2. Narration Generation | 0/0 | Not started | - |
| 3. Audio Processing | 0/0 | Not started | - |
| 4. Export & Metadata | 0/0 | Not started | - |
