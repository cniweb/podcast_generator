# Testing Patterns

**Analysis Date:** 2026-02-25

## Test Framework

**Runner:**
- pytest (dependency in `requirements.txt`).
- Config: Not detected (no `pytest.ini`, `pyproject.toml`, or `setup.cfg` found).

**Assertion Library:**
- pytest built-in `assert` statements (examples in `tests/test_utils.py`).

**Run Commands:**
```bash
./ci.sh              # Run lint + compile + tests (per `AGENTS.md`)
python -m pytest     # Run all tests (standard pytest)
python -m pytest tests/test_utils.py  # Run single file (per `AGENTS.md`)
```

## Test File Organization

**Location:**
- Tests live in `tests/` (examples: `tests/test_utils.py`, `tests/conftest.py`).

**Naming:**
- `test_*.py` (example: `tests/test_utils.py`).

**Structure:**
```
tests/
├── conftest.py
└── test_utils.py
```

## Test Structure

**Suite Organization:**
```python
def test_chunk_text_splits_long_paragraph():
    para = "a" * 1600
    chunks = _chunk_text(para, max_chars=1500)
    assert len(chunks) == 2
```

**Patterns:**
- Direct function calls with plain assertions (examples in `tests/test_utils.py`).
- No class-based test suites.

## Mocking

**Framework:**
- Not used.

**Patterns:**
- Not detected in `tests/test_utils.py`.

**What to Mock:**
- Not specified.

**What NOT to Mock:**
- Not specified.

## Fixtures and Factories

**Test Data:**
```python
text = "KI und AGI sind spannend"
assert _spell_out_abbreviations(text) == "K I und A G I sind spannend"
```

**Location:**
- Inline data in test functions (examples in `tests/test_utils.py`).

## Coverage

**Requirements:** None enforced.

**View Coverage:**
```bash
Not configured
```

## Test Types

**Unit Tests:**
- Utility-level unit tests for pure functions in `utils.py` (tests in `tests/test_utils.py`).

**Integration Tests:**
- Not detected.

**E2E Tests:**
- Not used.

## Common Patterns

**Async Testing:**
- Not applicable (no async tests detected).

**Error Testing:**
```python
assert _strip_formatting(text) == "Link mit Betonung und Klammern"
```

---

*Testing analysis: 2026-02-25*
