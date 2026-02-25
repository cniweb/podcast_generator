---
phase: 01-script-generation
plan: 01
subsystem: script
tags: [validation, pytest, gemini]

# Dependency graph
requires: []
provides:
  - Deterministic script constraint validation helpers
  - Generate-script retry enforcement for narration-ready output
affects: [script-generation, narration-generation]

# Tech tracking
tech-stack:
  added: []
  patterns: [Post-generation constraint validation with retry prompt]

key-files:
  created: [tests/test_script_constraints.py]
  modified: [utils.py, podcast_generator.py]

key-decisions:
  - "Enforce 650–800 word band with minimum 5 paragraphs and up to 3 attempts to meet narration constraints."

patterns-established:
  - "Validate cleaned script output before downstream processing"
  - "Retry with fix-up prompt when constraints fail"

requirements-completed: [SCRIPT-01, SCRIPT-02]

# Metrics
duration: 0 min
completed: 2026-02-25
---

# Phase 01 Plan 01: Script Generation Summary

**Deterministic script validation with retries to enforce narration-ready structure and length.**

## Performance

- **Duration:** 0 min
- **Started:** 2026-02-25T22:27:13Z
- **Completed:** 2026-02-25T22:27:34Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added script constraint helpers that detect forbidden lines, word count, and paragraph structure.
- Introduced retry logic in `generate_script()` to re-prompt until constraints pass or fail with clear errors.
- Locked SCRIPT-01/02 behaviors with focused pytest coverage.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add script constraint helpers with unit tests** - `f0b94c0` (feat)
2. **Task 2: Enforce constraints with retry logic in generate_script** - `e847abf` (feat)

**Plan metadata:** _pending_

## Files Created/Modified
- `utils.py` - Adds word counting and constraint validation utilities.
- `tests/test_script_constraints.py` - Exercises success/failure cases for SCRIPT-01/02 rules.
- `podcast_generator.py` - Enforces constraints with retries and actionable errors.

## Decisions Made
- Enforced a 650–800 word range with minimum 5 paragraphs and a max of 3 attempts to meet narration constraints.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Script generation now enforces length and structure deterministically.
- Ready to proceed with narration generation tasks.

---
*Phase: 01-script-generation*
*Completed: 2026-02-25*

## Self-Check: PASSED
