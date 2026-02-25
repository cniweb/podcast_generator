---
phase: 01-script-generation
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - podcast_generator.py
  - utils.py
  - tests/test_script_constraints.py
autonomous: true
requirements:
  - SCRIPT-01
  - SCRIPT-02

must_haves:
  truths:
    - "User can provide a topic and receive a spoken-style script in one CLI run."
    - "Script output is narration-ready: no headings, lists, or stage directions."
    - "Script includes intro + three fact sections + outro with natural paragraph breaks."
    - "Script word count stays within the defined tolerance band."
  artifacts:
    - path: "utils.py"
      provides: "Script validation helpers (word count, forbidden lines, structure checks)"
    - path: "podcast_generator.py"
      provides: "Generate-script flow that retries/fixes until constraints pass"
    - path: "tests/test_script_constraints.py"
      provides: "Unit tests locking SCRIPT-01/02 constraints"
  key_links:
    - from: "podcast_generator.py"
      to: "utils.py"
      via: "_validate_script_constraints call in generate_script"
      pattern: "_validate_script_constraints"
    - from: "tests/test_script_constraints.py"
      to: "utils.py"
      via: "imports and assertions on validation helpers"
      pattern: "_validate_script_constraints"
---

<objective>
Add deterministic script-constraint validation, retries, and tests so CLI users consistently receive narration-ready scripts that meet structure and length requirements.

Purpose: Enforce SCRIPT-01/02 without relying solely on prompt compliance.
Output: Validation helpers + tests, and generate_script flow that re-prompts until constraints pass.
</objective>

<execution_context>
@C:/Users/Admin/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/Admin/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-script-generation/01-RESEARCH.md
@podcast_generator.py
@utils.py
@tests/test_utils.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add script constraint helpers with unit tests</name>
  <files>utils.py, tests/test_script_constraints.py</files>
  <action>
Create validation helpers in `utils.py` to enforce narration-ready constraints after formatting cleanup, and add focused pytest coverage.

Implementation details:
- Add `_count_words(text: str) -> int` that counts word tokens (split on whitespace after stripping extra spaces).
- Add `_validate_script_constraints(text: str, min_words: int, max_words: int, min_paragraphs: int) -> dict` returning keys: `ok` (bool), `errors` (list[str]), `word_count` (int), `paragraph_count` (int), and `forbidden_lines` (list[str]).
- For paragraphs, split on double newlines and count non-empty paragraphs.
- Detect forbidden lines/patterns (case-insensitive): headings/labels like "Sprechtext:", divider lines ("---"), bullets/numbered lists (line starts with "-", "*", "1."), and stage-direction cues ("Musik", "Jingle", "Sound", "Atmos", "Beat", "Lacht", "faded"). Record offending lines and add an error per category.
- If `word_count` outside `min_words`/`max_words` add an error, and if `paragraph_count` < `min_paragraphs` add an error.
- Keep helpers internal (leading underscore) and follow existing utils style.

Tests (`tests/test_script_constraints.py`):
- Validate success case with 5+ paragraphs, word count within range, and no forbidden lines.
- Validate failures for: bullets/numbered lists, heading labels, stage directions, too few paragraphs, and word count outside range.
- Use direct assertions on `ok`, `errors`, and metrics; avoid mocking.
  </action>
  <verify>
    <automated>python -m pytest tests/test_script_constraints.py</automated>
  </verify>
  <done>Validation helpers return accurate `ok`/errors/metrics and tests pass for success/failure cases.</done>
</task>

<task type="auto">
  <name>Task 2: Enforce constraints with retry logic in generate_script</name>
  <files>podcast_generator.py</files>
  <action>
Update `PodcastGenerator.generate_script()` to enforce SCRIPT-01/02 with deterministic validation and limited retries.

Implementation details:
- Introduce constants near the script-generation section: `SCRIPT_TARGET_WORDS = 700`, `SCRIPT_MIN_WORDS = 650`, `SCRIPT_MAX_WORDS = 800`, `SCRIPT_MIN_PARAGRAPHS = 5`.
- After extracting the QUELLEN line and cleaning text via `_strip_formatting` and `_spell_out_abbreviations`, call `_validate_script_constraints` with the constants.
- If validation fails, retry up to 2 additional attempts (total 3 tries). For retries, prompt Gemini with a fix-up prompt that includes the previous draft and explicit constraints: spoken-only text, no headings/lists/stage directions, 5 paragraphs (intro + 3 facts + outro), and word count band. Require the QUELLEN line at the end. Keep German language requirement.
- If still invalid after retries, raise a `RuntimeError` that includes the collected error summaries for easier diagnosis.
- Preserve existing source parsing behavior; if QUELLEN line is missing, keep `sources` empty but continue (do not fail purely on missing sources).
- Keep logging consistent with existing print-based status output.
  </action>
  <verify>
    <automated>python -m pytest tests/test_script_constraints.py</automated>
  </verify>
  <done>`generate_script()` validates outputs and retries until constraints pass or errors out with actionable messaging.</done>
</task>

</tasks>

<verification>
- `python -m pytest tests/test_script_constraints.py` passes.
- `python -m compileall podcast_generator.py` passes.
</verification>

<success_criteria>
- Script generation enforces structure and length deterministically and retries on violations.
- Script constraint helpers are covered by unit tests.
</success_criteria>

<output>
After completion, create `.planning/phases/01-script-generation/01-script-generation-01-SUMMARY.md`.
</output>
