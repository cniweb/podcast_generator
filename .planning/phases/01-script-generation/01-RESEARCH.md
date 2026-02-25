# Phase 1: Script Generation - Research

**Researched:** 2026-02-25
**Domain:** LLM-based script generation for narration-ready podcast scripts (CLI)
**Confidence:** MEDIUM

## Summary

Phase 1 already has a functional script-generation flow in `podcast_generator.py`. It accepts a topic, builds a structured German prompt (intro + 3 facts + outro), calls Gemini through `google-genai`, strips formatting, expands abbreviations, validates length and paragraph count, and retries up to three times when constraints fail. Planning should focus on solidifying constraint enforcement and validation coverage for SCRIPT-01/SCRIPT-02, not on redesigning the stack.

The current constraints are encoded in both the prompt and a validation helper in `utils.py`. The validation checks word count range, minimum paragraphs, and forbidden constructs (labels, dividers, bullets, stage directions). There is already a dedicated test file for script constraints. A good plan should tighten any remaining gaps: deterministic detection of the intro/3-facts/outro structure, consistent source line handling, and retry behavior that is testable and bounded.

**Primary recommendation:** Plan around the existing `PodcastGenerator.generate_script()` pipeline, add deterministic structure validation, and expand tests in `tests/test_script_constraints.py` to lock in narration-ready output.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCRIPT-01 | User can provide a topic and receive a spoken-style script | Existing prompt + Gemini call + cleanup pipeline in `podcast_generator.py` already yields a spoken-style script; tests can verify narration-only output |
| SCRIPT-02 | Script output enforces length and structure suitable for narration | `_validate_script_constraints` enforces word count and paragraph minimum; prompt defines intro/3 facts/outro; plan should add deterministic structure checks and expand tests |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| google-genai | unpinned | Gemini text generation for scripts | Current production path for script generation in `podcast_generator.py` |
| python-dotenv | unpinned | Load `.env` config for keys and paths | Existing configuration pattern in repo |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | unpinned | Unit tests for text utilities and constraints | Already used in `tests/` for script constraints |
| pytrends | unpinned | Topic enrichment when input is empty | Only impacts topic selection prior to script generation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| google-genai | Other LLM SDKs | Would require new credentials and code paths; no value for Phase 1 scope |

**Installation:**
```bash
pip install -r requirements.txt
```

## Architecture Patterns

### Recommended Project Structure
```
podcast_generator.py      # end-to-end orchestration
utils.py                  # text utilities and script validation
tests/                    # pytest unit tests
```

### Pattern 1: Prompt -> cleanup -> validate -> retry
**What:** Generate with a strict prompt, clean the text, validate constraints, and retry with a fix-up prompt when invalid.
**When to use:** Any time narration-readiness and structure must be guaranteed.
**Example:**
```python
# Source: podcast_generator.py (local code)
response = client.models.generate_content(model=model_name, contents=prompt)
raw_text = response.text or ""

cleaned_text = _strip_formatting(raw_text)
cleaned_text = _spell_out_abbreviations(cleaned_text)

validation = _validate_script_constraints(
    cleaned_text,
    min_words=SCRIPT_MIN_WORDS,
    max_words=SCRIPT_MAX_WORDS,
    min_paragraphs=SCRIPT_MIN_PARAGRAPHS,
)
```

### Pattern 2: Constraint-driven prompt
**What:** Encode spoken-style rules directly in the prompt (no labels, no stage directions, no lists, German only).
**When to use:** To reduce cleanup burden and minimize retries.
**Example:**
```text
# Source: podcast_generator.py (local code)
"Reiner Sprechtext. Keine Regieanweisungen oder Buhnenanweisungen."
"Struktur: Intro + 3 Fakten + Outro."
```

### Anti-Patterns to Avoid
- **Prompt-only enforcement:** Always validate; LLMs drift.
- **Loose structure wording:** If intro/3-facts/outro is required, add explicit validation to avoid ambiguous outputs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM request handling | Raw HTTP calls | `google-genai` client | Already in use; handles auth and response parsing |
| Script validation | Ad-hoc regex in multiple places | `_validate_script_constraints` in `utils.py` | Centralized, testable constraint logic |

**Key insight:** Consistency comes from a single validation entry point and tests, not duplicated checks across modules.

## Common Pitfalls

### Pitfall 1: Labels, bullets, or headings leak into output
**What goes wrong:** Model returns "Sprechtext:" or list formatting despite prompt instructions.
**Why it happens:** LLM defaults to structured output when unsure.
**How to avoid:** Keep validation as a gate and retry with the fix-up prompt.
**Warning signs:** Lines matching the heading/bullet patterns in `_validate_script_constraints`.

### Pitfall 2: Length drift outside narration range
**What goes wrong:** Output falls outside 650-800 words (or chosen band).
**Why it happens:** "ca. 700" is soft; generation variance.
**How to avoid:** Enforce range in validation and use bounded retries.
**Warning signs:** Validation error "Wortanzahl ausserhalb" and repeated retries.

### Pitfall 3: Structure is correct in prose but not detectable
**What goes wrong:** Intro/3-facts/outro exist conceptually but cannot be validated deterministically.
**Why it happens:** No explicit markers or patterns to detect sections.
**How to avoid:** Define a lightweight structural heuristic (e.g., 5+ paragraphs with specific transition cues) or introduce minimally intrusive markers that can be stripped.
**Warning signs:** Scripts pass length but feel unstructured in manual review.

## Code Examples

Verified patterns from local sources:

### Script constraint validation
```python
# Source: utils.py (local code)
result = _validate_script_constraints(text, min_words=650, max_words=800, min_paragraphs=5)
if not result["ok"]:
    raise RuntimeError("Skript verletzt Constraints")
```

### Constraint tests already in repo
```python
# Source: tests/test_script_constraints.py (local code)
assert result["ok"] is False
assert any("Aufzaehlungen" in err for err in result["errors"])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Free-form prompt only | Structured prompt + cleanup + validation + retries | Existing in repo | More consistent narration-ready output |

**Deprecated/outdated:**
- None observed in repo scope for Phase 1.

## Open Questions

1. **Deterministic structure validation**
   - What we know: Prompt mandates intro + 3 facts + outro; validation does not check this explicitly.
   - What's unclear: Whether to add markers in the prompt or rely on heuristics.
   - Recommendation: Decide on a low-friction structure check and add tests to prevent regressions.

2. **Source line strictness**
   - What we know: Prompt requests a "QUELLEN:" line; code parses it when present.
   - What's unclear: Whether missing sources should fail SCRIPT-02.
   - Recommendation: Treat sources as optional for Phase 1 unless requirements say otherwise; log warnings if absent.

## Sources

### Primary (HIGH confidence)
- Local code: `podcast_generator.py` - script prompt, retries, cleanup, validation
- Local code: `utils.py` - `_validate_script_constraints`, `_strip_formatting`, `_spell_out_abbreviations`
- Local tests: `tests/test_script_constraints.py` - constraint expectations
- Local docs: `README.md` - behavior summary

### Secondary (MEDIUM confidence)
- None (Phase 1 relies on local implementation)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - based on existing repo deps, versions unpinned
- Architecture: HIGH - derived directly from existing code patterns
- Pitfalls: MEDIUM - based on known LLM behavior and repo constraints

**Research date:** 2026-02-25
**Valid until:** 2026-03-25
