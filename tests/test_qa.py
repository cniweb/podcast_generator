from qa import validate_manifest
import pytest


@pytest.mark.unit
def test_validate_manifest_accepts_completed_manifest():
    manifest = {
        "schema_version": 1,
        "generator": "podcast",
        "topic": "Test",
        "status": "completed",
        "runtime": {},
        "models": {},
        "artifacts": {},
        "error": None,
    }
    assert validate_manifest(manifest).ok


@pytest.mark.unit
def test_validate_manifest_rejects_unknown_status():
    result = validate_manifest({"schema_version": 1, "status": "unknown"})
    assert not result.ok
    assert "Ungültiger Manifest-Status" in result.errors


def test_qa_result_preserves_warnings_and_artifacts():
    from qa import QAResult

    result = QAResult(
        ok=True,
        warnings=["ffprobe fehlt"],
        artifacts={"audio": "audio.mp3"},
    )
    assert result.ok
    assert result.warnings == ["ffprobe fehlt"]
    assert result.artifacts["audio"] == "audio.mp3"
