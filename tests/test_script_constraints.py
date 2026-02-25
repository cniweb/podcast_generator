from utils import _validate_script_constraints


def _make_paragraph(text: str, words: int = 20) -> str:
    return " ".join([text] * words)


def _make_script(paragraphs: int = 5, words_per_paragraph: int = 20) -> str:
    blocks = []
    for idx in range(paragraphs):
        blocks.append(_make_paragraph(f"Absatz{idx + 1}", words_per_paragraph))
    return "\n\n".join(blocks)


def test_validate_script_constraints_success_case():
    text = _make_script(paragraphs=5, words_per_paragraph=20)
    result = _validate_script_constraints(
        text,
        min_words=80,
        max_words=120,
        min_paragraphs=5,
        expected_paragraphs=5,
    )

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["word_count"] == 100
    assert result["paragraph_count"] == 5
    assert result["forbidden_lines"] == []


def test_validate_script_constraints_rejects_wrong_paragraph_count():
    text = _make_script(paragraphs=4, words_per_paragraph=20)
    result = _validate_script_constraints(
        text,
        min_words=80,
        max_words=120,
        min_paragraphs=3,
        expected_paragraphs=5,
    )

    assert result["ok"] is False
    assert any("Absatzanzahl" in err for err in result["errors"])
    assert result["paragraph_count"] == 4


def test_validate_script_constraints_rejects_bullets_and_numbers():
    text = "- Erster Punkt\n\n1. Zweiter Punkt\n\nDritter Absatz"
    result = _validate_script_constraints(text, min_words=1, max_words=200, min_paragraphs=1)

    assert result["ok"] is False
    assert any("Aufzählungen" in err for err in result["errors"])
    assert any("- Erster Punkt" in line for line in result["forbidden_lines"])
    assert any("1. Zweiter Punkt" in line for line in result["forbidden_lines"])


def test_validate_script_constraints_rejects_headings_labels():
    text = "Sprechtext:\n\nEin Absatz ohne Liste."
    result = _validate_script_constraints(text, min_words=1, max_words=200, min_paragraphs=1)

    assert result["ok"] is False
    assert any("Überschriften" in err for err in result["errors"])
    assert "Sprechtext:" in result["forbidden_lines"]


def test_validate_script_constraints_rejects_stage_directions():
    text = "Musik startet leise.\n\nDann geht der Text weiter."
    result = _validate_script_constraints(text, min_words=1, max_words=200, min_paragraphs=1)

    assert result["ok"] is False
    assert any("Bühnenanweisungen" in err for err in result["errors"])
    assert "Musik startet leise." in result["forbidden_lines"]


def test_validate_script_constraints_rejects_too_few_paragraphs():
    text = _make_script(paragraphs=2, words_per_paragraph=10)
    result = _validate_script_constraints(text, min_words=1, max_words=200, min_paragraphs=5)

    assert result["ok"] is False
    assert any("Zu wenige Absätze" in err for err in result["errors"])
    assert result["paragraph_count"] == 2


def test_validate_script_constraints_rejects_word_count_out_of_range():
    text = _make_script(paragraphs=5, words_per_paragraph=5)
    result = _validate_script_constraints(text, min_words=60, max_words=80, min_paragraphs=5)

    assert result["ok"] is False
    assert any("Wortanzahl" in err for err in result["errors"])
    assert result["word_count"] == 25
