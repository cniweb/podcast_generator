---
phase: 01-script-generation
plan: 02
type: execute
wave: 2
depends_on: ["01"]
files_modified:
  - utils.py
  - tests/test_script_constraints.py
  - podcast_generator.py
autonomous: true
requirements:
  - SCRIPT-01
  - SCRIPT-02
gap_closure: true

must_haves:
  truths:
    - "Script includes intro + three fact sections + outro with natural paragraph breaks."
    - "Script always matches the intro + three fact sections + outro structure without manual edits."
  artifacts:
    - path: "utils.py"
      provides: "Structure-aware script validation (intro + 3 facts + outro heuristics)"
    - path: "tests/test_script_constraints.py"
      provides: "Tests that fail on missing intro/3-facts/outro structure"
    - path: "podcast_generator.py"
      provides: "Generate-script flow that enforces structure validation"
  key_links:
    - from: "podcast_generator.py"
      to: "utils.py"
      via: "_validate_script_constraints call with structure expectations"
      pattern: "_validate_script_constraints"
    - from: "tests/test_script_constraints.py"
      to: "utils.py"
      via: "structure expectations asserted in tests"
      pattern: "expected_paragraphs|structure"
---

<objective>
Close the verification gap by adding deterministic validation and tests for the intro + three facts + outro structure.

Purpose: Ensure SCRIPT-02 is enforced without manual inspection.
Output: Structure-aware validation helpers, tests, and generate_script wiring.
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
@.planning/phases/01-script-generation/01-VERIFICATION.md
@.planning/phases/01-script-generation/01-script-generation-01-SUMMARY.md
@utils.py
@podcast_generator.py
@tests/test_script_constraints.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add deterministic structure validation and tests</name>
  <files>utils.py, tests/test_script_constraints.py</files>
  <action>
Extend `_validate_script_constraints` to enforce the intro + 3 facts + outro structure deterministically.

Implementation details:
- Add an optional parameter like `expected_paragraphs: int | None = None` (or a separate `_validate_script_structure` helper) that can enforce an exact paragraph count.
- Treat the required structure as exactly 5 paragraphs (intro + 3 facts + outro). If the paragraph count differs, add a clear error message for structure failure.
- Keep existing forbidden-line and word-count checks intact.
- Update tests in `tests/test_script_constraints.py` to cover structure enforcement: one case that passes with exactly 5 paragraphs, and one case that fails with 4 or 6 paragraphs and asserts the structure error.
- Keep output German for error text, consistent with existing validation messages.
  </action>
  <verify>
    <automated>python -m pytest tests/test_script_constraints.py</automated>
  </verify>
  <done>Structure validation fails when paragraph count deviates from the required intro/3-facts/outro layout, with tests covering both pass and fail cases.</done>
</task>

<task type="auto">
  <name>Task 2: Wire structure enforcement into generate_script retries</name>
  <files>podcast_generator.py</files>
  <action>
Update `PodcastGenerator.generate_script()` to pass the structure expectation into validation and retry until the structure matches.

Implementation details:
- Use the existing `SCRIPT_MIN_PARAGRAPHS`/constants and add or reuse a constant for the exact paragraph count (5) to represent intro + 3 facts + outro.
- Pass the expected paragraph count into `_validate_script_constraints` (or call a new structure helper) so validation can reject incorrect structure, not just too few paragraphs.
- Keep the existing fix-up prompt guidance for structure, and ensure retry errors include the new structure failure message for diagnostics.
  </action>
  <verify>
    <automated>python -m pytest tests/test_script_constraints.py</automated>
  </verify>
  <done>generate_script retries until the script meets the exact intro/3-facts/outro paragraph structure or raises a clear error after the final attempt.</done>
</task>

</tasks>

<verification>
- `python -m pytest tests/test_script_constraints.py` passes.
- `python -m compileall podcast_generator.py` passes.
</verification>

<success_criteria>
- Structure validation deterministically enforces intro + 3 facts + outro.
- Tests fail if the paragraph structure deviates from the required layout.
</success_criteria>

<output>
After completion, create `.planning/phases/01-script-generation/01-script-generation-02-SUMMARY.md`.
</output>
