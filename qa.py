from dataclasses import dataclass, field


@dataclass
class QAResult:
    ok: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    artifacts: dict[str, str | None] = field(default_factory=dict)


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
