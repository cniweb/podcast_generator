from dataclasses import dataclass, field


@dataclass
class QAResult:
    ok: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    artifacts: dict[str, str | None] = field(default_factory=dict)

    def raise_if_failed(self):
        if not self.ok:
            raise RuntimeError("Output-QA fehlgeschlagen: " + "; ".join(self.errors))


def validate_manifest(manifest):
    required = {
        "schema_version", "generator", "topic", "status", "runtime",
        "models", "artifacts", "error",
    }
    errors = [f"Manifest-Feld fehlt: {key}" for key in sorted(required - manifest.keys())]
    if manifest.get("schema_version") != 1:
        errors.append("Nicht unterstützte Manifest-Schema-Version")
    if manifest.get("status") not in {"running", "completed", "failed"}:
        errors.append("Ungültiger Manifest-Status")
    return QAResult(ok=not errors, errors=errors)


def validate_manifest_schema(manifest):
    result = validate_manifest(manifest)
    if not isinstance(manifest.get("retries", 0), int):
        result.errors.append("Manifest-Retries müssen ganzzahlig sein")
    result.ok = not result.errors
    return result


def safe_result_payload(manifest):
    return {
        "status": manifest.get("status"),
        "manifest": manifest.get("manifest_path"),
        "artifacts": manifest.get("artifacts", {}),
        "warnings": manifest.get("warnings", []),
        "error": manifest.get("error"),
    }
