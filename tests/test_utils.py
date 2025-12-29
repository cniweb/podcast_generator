import pytest

from utils import _chunk_text, _spell_out_abbreviations, _strip_formatting


def test_strip_formatting_removes_markdown_and_asterisks():
    text = "[Link](http://x) mit *Betonung* und (Klammern)"
    assert _strip_formatting(text) == "Link mit Betonung und Klammern"


def test_spell_out_abbreviations_expands_short_uppercase():
    text = "KI und AGI sind spannend"
    assert _spell_out_abbreviations(text) == "K I und A G I sind spannend"


def test_spell_out_abbreviations_respects_stoplist():
    text = "DER KI Test"
    assert _spell_out_abbreviations(text) == "DER K I Test"


def test_chunk_text_splits_long_paragraph():
    para = "a" * 1600
    chunks = _chunk_text(para, max_chars=1500)
    assert len(chunks) == 2
    assert len(chunks[0]) <= 1500
    assert len(chunks[1]) <= 1500


def test_chunk_text_keeps_paragraphs_together_when_small():
    text = "absatz1\n\nabsatz2"
    chunks = _chunk_text(text, max_chars=50)
    assert chunks == [text]
