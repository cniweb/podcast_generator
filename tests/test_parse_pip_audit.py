import importlib.machinery
import importlib.util
from pathlib import Path
from typing import cast


def _load_parser():
    path = Path(__file__).parents[1] / ".github/scripts/parse_pip_audit.py"
    spec = importlib.util.spec_from_file_location("parse_pip_audit", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(
        cast(importlib.machinery.ModuleSpec, spec)
    )
    spec.loader.exec_module(module)
    return module


def test_classify_clean_report():
    assert _load_parser().classify_report({"dependencies": []}) == ("clean", [])


def test_classify_warning_report():
    report = {"dependencies": [{"name": "demo", "version": "1", "vulns": [{"id": "CVE-1", "severity": "MODERATE"}]}]}
    status, findings = _load_parser().classify_report(report)
    assert status == "warning"
    assert findings[0]["id"] == "CVE-1"


def test_classify_blocking_report():
    report = {"dependencies": [{"name": "demo", "version": "1", "vulns": [{"id": "CVE-2", "severity": "HIGH"}]}]}
    assert _load_parser().classify_report(report)[0] == "blocking"
