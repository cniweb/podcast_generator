"""Classify pip-audit JSON output for GitHub Actions."""

import json
import sys


def classify_report(report):
    findings = []
    for dependency in report.get("dependencies", []):
        for vulnerability in dependency.get("vulns", []):
            findings.append(
                {
                    "name": dependency.get("name", "unknown"),
                    "version": dependency.get("version", "unknown"),
                    "id": vulnerability.get("id", "unknown"),
                    "severity": str(vulnerability.get("severity", "")).upper(),
                }
            )
    blocking = [
        item for item in findings if item["severity"] in {"HIGH", "CRITICAL"}
    ]
    return ("blocking" if blocking else "warning" if findings else "clean"), findings


def main(argv=None):
    try:
        with open((argv or sys.argv[1:])[0], encoding="utf-8") as handle:
            status, findings = classify_report(json.load(handle))
    except (IndexError, OSError, json.JSONDecodeError) as exc:
        print(f"::error title=pip-audit::Audit-Auswertung fehlgeschlagen: {exc}")
        return 2
    for finding in findings:
        level = "error" if status == "blocking" else "warning"
        print(
            f"::{level} title=pip-audit::"
            f"{finding['name']} {finding['version']}: {finding['id']}"
        )
    return 1 if status == "blocking" else 0


if __name__ == "__main__":
    raise SystemExit(main())
