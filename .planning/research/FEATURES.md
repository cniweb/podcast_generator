# Feature Research

**Domain:** Podcast-Generierungstools (CLI, lokal, externe AI-APIs)
**Researched:** 2026-02-25
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Topic input -> script generation | Core promise of a generator is a usable script from a topic | MEDIUM | Needs prompt templates, length control, spoken style rules |
| TTS narration output | Users expect a full audio episode, not just text | MEDIUM | Voice selection, format control, SSML, chunking |
| Audio post-processing (loudness normalization, noise reduction) | Baseline quality must be listenable and consistent | MEDIUM | LUFS targets, limiter, optional denoise | 
| Export formats + metadata | Podcast files need correct formats and tags | LOW | MP3/WAV export, ID3 tags, title/description |
| Show notes / transcript | Discovery and accessibility are standard | MEDIUM | Auto summaries, timestamps, transcript generation |
| Background music mix | Many tools provide a polished, mixed output | MEDIUM | Ducking, music library integration, license tracking |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| One-click mastering pipeline (leveling, EQ, filler removal) | Pro sound without DAW skills; reduces editing time | HIGH | Needs multistage audio processing and safe defaults (Auphonic-style) |
| Automatic chaptering + structured metadata | Improves navigation and SEO; makes output feel premium | MEDIUM | Requires transcript + topic segmentation |
| Batch generation / watch-folder automation | Scales content production for teams | HIGH | File watchers, job queue, idempotent runs |
| Multi-voice or role-based narration | More engaging episodes; differentiates from mono voice | MEDIUM | Speaker tagging, voice switching, pacing rules |
| Integrated publishing targets | Shortens path from generation to distribution | HIGH | Hosting API integrations, auth handling |
| Personalized style presets (tone, pacing, brand lexicon) | Consistent voice across episodes and teams | MEDIUM | Prompt profiles + reusable config |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Fully automated publishing without review | Faster workflow | High risk of factual or style errors going live | Require review/approve step; optional auto-publish toggle |
| Unlimited voice cloning by default | Sounds personal/brand aligned | Legal and consent risks; misuse potential | Explicit opt-in with consent verification |
| Real-time generation for long episodes | Instant results | High cost, fragile pipelines, lower quality | Async jobs with progress + partial previews |
| Bundled music without license tracking | Convenience | Rights violations and takedowns | Enforce licensed sources + metadata persistence |

## Feature Dependencies

```
Script generation
    └──requires──> Topic input + prompt templates
                       └──requires──> Config/env validation

TTS narration
    └──requires──> Script generation
                       └──requires──> Chunking + SSML rules

Audio post-processing
    └──requires──> TTS narration
                       └──requires──> ffmpeg/ffprobe availability

Show notes / transcript
    └──requires──> Script or audio output

Publishing targets
    └──requires──> Export formats + metadata

Batch automation
    └──requires──> Idempotent runs + artifact caching
```

### Dependency Notes

- **TTS narration requires script generation:** Without a stable script, voice synthesis output is unusable and inconsistent.
- **Audio post-processing requires TTS narration:** Loudness, EQ, and mix steps need rendered audio to operate on.
- **Publishing targets require export metadata:** Most hosts need correct tags, titles, and descriptions to accept uploads.
- **Batch automation requires idempotent runs + caching:** Prevents repeat API costs and enables retries.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] Topic -> script generation (spoken style) — validates core value
- [ ] TTS narration output — delivers listenable episode
- [ ] Audio mix + loudness normalization — baseline quality control
- [ ] Export MP3 + basic metadata — makes output usable in podcast workflows

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Show notes + transcript — improves distribution and accessibility
- [ ] Background music presets + license metadata — polished output without risk

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Automatic publishing integrations — adds operational complexity
- [ ] Batch generation / watch folders — requires robust job management
- [ ] Multi-voice narration — higher TTS cost and complexity

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Topic -> script generation | HIGH | MEDIUM | P1 |
| TTS narration output | HIGH | MEDIUM | P1 |
| Audio mix + loudness normalization | HIGH | MEDIUM | P1 |
| Export MP3 + metadata | MEDIUM | LOW | P1 |
| Show notes + transcript | MEDIUM | MEDIUM | P2 |
| Background music presets | MEDIUM | MEDIUM | P2 |
| Automatic publishing | MEDIUM | HIGH | P3 |
| Multi-voice narration | MEDIUM | MEDIUM | P3 |
| Batch generation automation | LOW | HIGH | P3 |

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| Audio cleanup + loudness | Auphonic: denoise, leveling, loudness specs | Riverside: Magic Audio | Build minimal loudness + optional denoise in pipeline |
| Transcription + show notes | Auphonic: Speech2Text + shownotes | Riverside: AI show notes | Generate transcript + concise show notes after audio |
| Text-based editing tools | Descript: text-based edit workflow | Riverside: text-based editor | Out of scope for CLI MVP; keep script-level edits |
| Clips/repurposing | Descript: clips + social assets | Riverside: Magic Clips | Not in scope; consider later if video output added |
| Publishing integrations | Riverside: publishing + analytics | Auphonic: automatic publishing targets | Defer; design metadata output for later integration |

## Sources

- https://auphonic.com/features
- https://auphonic.com/workflows-api
- https://www.descript.com/podcasting
- https://riverside.fm/ai

---
*Feature research for: Podcast-Generierungstools*
*Researched: 2026-02-25*
