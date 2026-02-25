# Phase 1: Script Generation - Research

**Researched:** 2026-02-25
**Domain:** LLM-based script generation for narration-ready podcast scripts (CLI)
**Confidence:** MEDIUM

## Summary

Phase 1 can largely reuse the existing code paths in `podcast_generator.py` for script generation. The current implementation already accepts a topic, calls Gemini via `google-genai`, enforces a spoken-style prompt with length and structure constraints, strips formatting, and writes a transcript. Planning should focus on ensuring the prompt reliably produces narration-ready text (no stage directions, no headings), and that post-processing enforces structural constraints (intro + 3 facts + outro) and length targets around ~700 words.

The repository already encodes several constraints in the prompt: German language, no lists, spoken style, and a sources line. It also performs cleanup via `_strip_formatting` and `_spell_out_abbreviations`, and writes the transcript to a temp file. For Phase 1 planning, the main work is to validate the prompt and post-processing against requirements SCRIPT-01 and SCRIPT-02, define enforcement/validation rules, and add tests in `tests/` (if missing) to lock in structure and length.

**Primary recommendation:** Use the existing `PodcastGenerator.generate_script()` flow (Gemini + cleanup) and add deterministic validation/cleanup steps plus tests to guarantee narration-ready structure and length.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCRIPT-01 | User can provide a topic and receive a spoken-style script | Existing Gemini prompt + cleanup pipeline in `podcast_generator.py` fulfills spoken-style generation; add tests to lock behavior |
| SCRIPT-02 | Script output enforces length and structure suitable for narration | Prompt specifies intro + 3 facts + outro and ~700 words; recommend validation/re-prompting to enforce |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| google-genai | unpinned | Gemini text generation for scripts | Already used in `podcast_generator.py` and required for script generation |
| python-dotenv | unpinned | Load `.env` for API keys and config | Existing project convention for configuration |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | unpinned | Unit tests for script utilities and constraints | Use for enforcing SCRIPT-01/02 via tests |
| pytrends | unpinned | Topic enrichment via trends | Only when topic is empty; script generation uses resulting topic |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| google-genai | Google Cloud Vertex AI / OpenAI SDK | Would require new keys, config, and code paths; not aligned with existing repo |

**Installation:**
```bash
pip install -r requirements.txt
```

## Architecture Patterns

### Recommended Project Structure
```
podcast_generator.py      # end-to-end orchestration
utils.py                  # text utilities (_strip_formatting, _chunk_text)
tests/                    # pytest unit tests
```

### Pattern 1: Prompt-then-clean pipeline
**What:** Generate text with an explicit, structured prompt, then sanitize and normalize the output before saving.
**When to use:** Any time the raw model output is used for narration or downstream processing.
**Example:**
```python
# Source: podcast_generator.py (local code)
response = client.models.generate_content(model=model_name, contents=prompt)
raw_text = response.text
cleaned_text = _strip_formatting(raw_text)
cleaned_text = _spell_out_abbreviations(cleaned_text)
```

### Pattern 2: Explicit structure instructions
**What:** Include a required structure (intro + 3 facts + outro) and length target in the prompt.
**When to use:** When the output must be narration-ready without manual editing.
**Example:**
```text
# Source: podcast_generator.py (local code)
"Struktur: Knackiges Intro ... 3 faszinierende Fakten ... kurzes Outro."
"Länge: Ca. 700 Wörter."
```

### Anti-Patterns to Avoid
- **Relying solely on prompt compliance:** Model output can drift; add post-generation checks and enforce constraints.
- **Including stage directions in output:** Any cues like "Musik" or "Jingle" violate narration-only requirements; strip or re-prompt.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM request handling | Custom HTTP calls | `google-genai` client | Handles auth, model selection, and response parsing |
| Environment config | Manual os.getenv everywhere | `python-dotenv` + `_require_env` | Standardized missing-key errors |

**Key insight:** The repo already uses a single LLM client and prompt; adding a second ad-hoc client increases failure modes without benefit for Phase 1.

## Common Pitfalls

### Pitfall 1: Model output includes headings or lists
**What goes wrong:** The prompt asks for "no lists" and "no labels" but the model sometimes returns headings or bullets.
**Why it happens:** LLMs may default to structured list outputs unless filtered.
**How to avoid:** Add a post-processing validation step to detect headings/bullets and either re-prompt or strip them.
**Warning signs:** Lines starting with '-', '*', '1.', or labels like "Sprechtext:".

### Pitfall 2: Length drift
**What goes wrong:** Output is too short or too long for narration.
**Why it happens:** "Ca. 700 Wörter" is a soft constraint.
**How to avoid:** Count words after cleanup and re-prompt if outside tolerance band (define a target range).
**Warning signs:** Word count far below 600 or above 900.

### Pitfall 3: Stage directions leak into script
**What goes wrong:** Output contains "Musik", "Jingle", or "Lacht".
**Why it happens:** Models trained on script formats insert cues.
**How to avoid:** Filter common cue tokens and re-prompt or strip lines containing them.
**Warning signs:** Bracketed text or keywords like "Sound", "Beat", "Atmos".

## Code Examples

Verified patterns from local sources:

### Generate and clean script
```python
# Source: podcast_generator.py (local code)
response = client.models.generate_content(model=model_name, contents=prompt)
raw_text = response.text

cleaned_text = _strip_formatting(raw_text)
cleaned_text = _spell_out_abbreviations(cleaned_text)
```

### Strip formatting and preserve narration-only text
```python
# Source: utils.py (local code)
text = re.sub(r"\*(.*?)\*", r"\1", text)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Free-form LLM prompt | Structured prompt + cleanup | existing in repo | More consistent narration-ready text |

**Deprecated/outdated:**
- None observed in repo scope for Phase 1.

## Open Questions

1. **Word-count tolerance band**
   - What we know: Prompt targets ~700 words; no enforcement exists.
   - What's unclear: Acceptable min/max word count for SCRIPT-02.
   - Recommendation: Define a range (e.g., 650-800) in planning and enforce via validation/re-prompt.

2. **Source line handling**
   - What we know: Prompt requests a "QUELLEN:" line; code strips it and stores URLs.
   - What's unclear: Should source URLs be required or optional for Phase 1.
   - Recommendation: Treat missing sources as non-blocking but log a warning; decide in planning.

## Sources

### Primary (HIGH confidence)
- Local code: `podcast_generator.py` — script generation prompt and cleanup
- Local code: `utils.py` — `_strip_formatting`, `_spell_out_abbreviations`
- Local docs: `README.md` — describes script generation behavior

### Secondary (MEDIUM confidence)
- None (Phase 1 primarily relies on local implementation)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM — based on existing repo deps, versions unpinned
- Architecture: HIGH — derived directly from existing code patterns
- Pitfalls: MEDIUM — inferred from common LLM behavior and repo constraints

**Research date:** 2026-02-25
**Valid until:** 2026-03-25
