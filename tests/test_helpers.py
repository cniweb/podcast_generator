"""Tests fuer deterministische Hilfsfunktionen in utils.py und podcast_generator.py."""

import pytest

from conftest import _load_partial_module
from utils import _chunk_text, _count_words


# ---------------------------------------------------------------------------
# _count_words (utils.py)
# ---------------------------------------------------------------------------


class TestCountWords:
    def test_empty_string(self):
        assert _count_words("") == 0

    def test_only_whitespace(self):
        assert _count_words("   \t\n  ") == 0

    def test_single_word(self):
        assert _count_words("Hallo") == 1

    def test_multiple_words(self):
        assert _count_words("Hallo Welt wie geht es") == 5

    def test_extra_whitespace_between_words(self):
        assert _count_words("  eins   zwei   drei  ") == 3


# ---------------------------------------------------------------------------
# _chunk_text (utils.py)
# ---------------------------------------------------------------------------


class TestChunkText:
    def test_empty_text_returns_empty_list(self):
        assert _chunk_text("") == []

    def test_max_chars_zero_raises_value_error(self):
        with pytest.raises(ValueError, match="max_chars"):
            _chunk_text("irgendwas", max_chars=0)

    def test_max_chars_negative_raises_value_error(self):
        with pytest.raises(ValueError):
            _chunk_text("irgendwas", max_chars=-5)

    def test_single_paragraph_under_limit(self):
        text = "Kurzer Text."
        chunks = _chunk_text(text, max_chars=100)
        assert chunks == ["Kurzer Text."]

    def test_paragraph_over_limit_is_split(self):
        long_para = "x" * 10
        chunks = _chunk_text(long_para, max_chars=4)
        # jedes Chunk darf maximal 4 Zeichen lang sein
        assert all(len(c) <= 4 for c in chunks)
        assert "".join(chunks) == long_para

    def test_two_short_paragraphs_merged(self):
        text = "Eins.\n\nZwei."
        chunks = _chunk_text(text, max_chars=100)
        assert len(chunks) == 1
        assert "Eins." in chunks[0]
        assert "Zwei." in chunks[0]

    def test_two_paragraphs_split_when_combined_exceeds_limit(self):
        text = "Abcde.\n\nFghij."
        # max_chars=7 → jeder Paragraph (6 Zeichen) passt einzeln, aber nicht zusammen (6+2+6=14)
        chunks = _chunk_text(text, max_chars=7)
        assert len(chunks) == 2


# ---------------------------------------------------------------------------
# Hilfsfunktionen aus podcast_generator.py (via _load_partial_module)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mod():
    return _load_partial_module()


class TestParseCsvModels:
    def test_normal_list(self, mod):
        fn = mod["_parse_csv_models"]
        assert fn("a,b,c") == ["a", "b", "c"]

    def test_whitespace_stripped(self, mod):
        fn = mod["_parse_csv_models"]
        assert fn("  a , b , c  ") == ["a", "b", "c"]

    def test_empty_string_returns_empty(self, mod):
        fn = mod["_parse_csv_models"]
        assert fn("") == []

    def test_only_commas_returns_empty(self, mod):
        fn = mod["_parse_csv_models"]
        assert fn(",,,") == []


class TestRetryDelay:
    def test_attempt_1(self, mod):
        fn = mod["_retry_delay"]
        assert fn(1, 2.0) == pytest.approx(2.0)

    def test_attempt_2(self, mod):
        fn = mod["_retry_delay"]
        assert fn(2, 2.0) == pytest.approx(4.0)

    def test_attempt_3(self, mod):
        fn = mod["_retry_delay"]
        assert fn(3, 2.0) == pytest.approx(8.0)

    def test_custom_base(self, mod):
        fn = mod["_retry_delay"]
        assert fn(1, 1.5) == pytest.approx(1.5)


class TestToSsml:
    def test_ampersand_escaped(self, mod):
        fn = mod["_to_ssml"]
        result = fn("Tom & Jerry")
        assert "&amp;" in result
        assert "&" not in result.replace("&amp;", "").replace("&lt;", "").replace(
            "&gt;", ""
        )

    def test_less_than_escaped(self, mod):
        fn = mod["_to_ssml"]
        result = fn("a < b")
        assert "&lt;" in result

    def test_greater_than_escaped(self, mod):
        fn = mod["_to_ssml"]
        result = fn("a > b")
        assert "&gt;" in result

    def test_output_wrapped_in_speak_tag(self, mod):
        fn = mod["_to_ssml"]
        result = fn("Hallo Welt.")
        assert result.strip().startswith("<speak>")
        assert result.strip().endswith("</speak>")


class TestNormalizeModelName:
    def test_strips_models_prefix(self, mod):
        fn = mod["_normalize_model_name"]
        assert fn("models/gemini-1.5-pro") == "gemini-1.5-pro"

    def test_no_prefix_unchanged(self, mod):
        fn = mod["_normalize_model_name"]
        assert fn("gemini-1.5-pro") == "gemini-1.5-pro"

    def test_empty_string(self, mod):
        fn = mod["_normalize_model_name"]
        assert fn("") == ""

    def test_none_like_empty(self, mod):
        fn = mod["_normalize_model_name"]
        assert fn(None) == ""  # type: ignore[arg-type]


class TestIsRateLimitedError:
    def test_429_in_message(self, mod):
        fn = mod["_is_rate_limited_error"]
        assert fn(Exception("HTTP error 429")) is True

    def test_resource_exhausted(self, mod):
        fn = mod["_is_rate_limited_error"]
        assert fn(Exception("resource_exhausted quota")) is True

    def test_too_many_requests(self, mod):
        fn = mod["_is_rate_limited_error"]
        assert fn(Exception("too many requests")) is True

    def test_rate_limit(self, mod):
        fn = mod["_is_rate_limited_error"]
        assert fn(Exception("rate limit exceeded")) is True

    def test_quota_exceeded_returns_false(self, mod):
        fn = mod["_is_rate_limited_error"]
        assert fn(Exception("quota exceeded for this model")) is False

    def test_requests_per_model_per_day_returns_false(self, mod):
        fn = mod["_is_rate_limited_error"]
        assert fn(Exception("requests_per_model_per_day limit")) is False

    def test_unrelated_error_returns_false(self, mod):
        fn = mod["_is_rate_limited_error"]
        assert fn(Exception("connection refused")) is False


class TestStepKey:
    def test_lowercases(self, mod):
        fn = mod["_step_key"]
        assert fn("Skript") == "skript"

    def test_strips_whitespace(self, mod):
        fn = mod["_step_key"]
        assert fn("  Audio  ") == "audio"

    def test_mixed(self, mod):
        fn = mod["_step_key"]
        assert fn("  TTS Audio  ") == "tts audio"


class TestArtifactPathOrNone:
    def test_empty_string_returns_none(self, mod):
        fn = mod["_artifact_path_or_none"]
        assert fn("") is None

    def test_nonempty_returns_path(self, mod):
        fn = mod["_artifact_path_or_none"]
        assert fn("/tmp/output.mp3") == "/tmp/output.mp3"


class TestFileSizeOrZero:
    def test_nonexistent_file_returns_zero(self, mod, tmp_path):
        fn = mod["_file_size_or_zero"]
        assert fn(str(tmp_path / "doesnotexist.mp3")) == 0

    def test_empty_path_returns_zero(self, mod):
        fn = mod["_file_size_or_zero"]
        assert fn("") == 0

    def test_existing_file_returns_size(self, mod, tmp_path):
        fn = mod["_file_size_or_zero"]
        f = tmp_path / "test.txt"
        f.write_bytes(b"hello")
        assert fn(str(f)) == 5
