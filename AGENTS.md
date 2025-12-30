# AGENT Guide for GitHub Copilot

This repository uses GitHub Copilot (and similar agents) to automate podcast generation. Follow these guardrails and improve them over time.

## Mission

- Keep the pipeline working end-to-end: trend lookup → script → TTS → music → mix → video → metadata.
- Stay safe: do not leak secrets from .env; avoid destructive git commands.
- Be concise; prefer small, targeted changes with clear rationale.

## Operating Rules

- Default language: German for user-visible text; use concise German docstrings and plain-language comments so the flow stays understandable.
- Avoid adding stage/sound directions to generated scripts; spoken text only.
- Environment: rely on `.env` variables; never hardcode keys.
- Trend region focus: DACH (DE, AT, CH). If trends fail, fall back to static topic.
- When unsure, ask the user instead of guessing.

## Editing Guidelines

- Prefer minimal diffs; use `apply_patch` for single-file edits.
- Keep audio/script output paths stable under `PODCAST_*` dirs.
- Don’t delete user assets (cover.png/jpg, background loops).
- Log non-fatal errors instead of aborting the whole run when possible.

## Quality Checks

- Run `./run.sh "<topic>"` for an end-to-end test when feasible.
- Verify trend debug output if topic is auto-selected.
- Ensure generated script contains no stage directions or sound cues.

## Continuous Refinement

- Whenever you notice repetitive fixes, add/update checks or prompts here.
- Record known pitfalls (e.g., pytrends 404) and current mitigations.
- Keep this file short; remove obsolete steps as the pipeline stabilizes.
