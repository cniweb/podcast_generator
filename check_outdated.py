#!/usr/bin/env python3
"""Prueft, ob die Pakete in requirements.txt neuere Versionen auf PyPI haben.

Verwendung:
    python check_outdated.py               # zeigt Tabelle, Exit 0
    python check_outdated.py --strict      # Exit 1 wenn Updates verfuegbar

Dieses Skript macht keine Aenderungen. Es dient als lokaler Ersatz fuer
'renovate --dry-run', um schnell zu sehen, welche Abhaengigkeiten veraltet sind.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
import urllib.error
import json
from pathlib import Path


# Zeige keine urllib3-Warnungen bei Timeouts
REQUIREMENTS_FILE = Path(__file__).resolve().parent / "requirements.txt"
PYPI_URL = "https://pypi.org/pypi/{package}/json"
REQUEST_TIMEOUT = 10  # Sekunden pro PyPI-Abfrage


def _parse_requirements(path: Path) -> list[tuple[str, str]]:
    """Liest requirements.txt und gibt (package_name, version_spec)-Paare zurueck."""
    packages: list[tuple[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Unterstuetzt: pkg>=1.2.3  pkg==1.2.3  pkg~=1.2  pkg  pkg[extra]>=1.0
        match = re.match(
            r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*([><=!~][><=!~]?\s*[\d.*]+.*)?$",
            line,
        )
        if match:
            name = match.group(1)
            spec = (match.group(2) or "").strip()
            packages.append((name, spec))
        else:
            print(f"  [SKIP] Zeile nicht parsebar: {line!r}", file=sys.stderr)
    return packages


def _pinned_version(spec: str) -> str | None:
    """Extrahiert die Versionsnummer aus einem Versions-Spec (z.B. '>=1.2.3' -> '1.2.3')."""
    match = re.search(r"[\d]+[\d.]*", spec)
    return match.group(0) if match else None


def _latest_pypi_version(package: str) -> str | None:
    """Fragt PyPI nach der aktuellsten stabilen Version eines Pakets."""
    url = PYPI_URL.format(package=package)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "check-outdated/1.0"})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["info"]["version"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # Paket nicht auf PyPI gefunden
        raise
    except Exception:
        return None


def _version_tuple(version: str) -> tuple[int, ...]:
    """Wandelt '1.2.3' in (1, 2, 3) um fuer einfachen Vergleich."""
    try:
        return tuple(int(x) for x in version.split(".") if x.isdigit())
    except Exception:
        return (0,)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Gibt Exit-Code 1 zurueck wenn Updates verfuegbar sind.",
    )
    parser.add_argument(
        "--requirements",
        default=str(REQUIREMENTS_FILE),
        help=f"Pfad zu requirements.txt (Standard: {REQUIREMENTS_FILE})",
    )
    args = parser.parse_args()

    req_path = Path(args.requirements)
    if not req_path.exists():
        print(f"Fehler: {req_path} nicht gefunden.", file=sys.stderr)
        return 2

    packages = _parse_requirements(req_path)
    if not packages:
        print("Keine Pakete in requirements.txt gefunden.")
        return 0

    print(f"\nPruefe {len(packages)} Pakete gegen PyPI ...\n")
    print(f"{'Paket':<35} {'Gepinnt':<15} {'Aktuell auf PyPI':<20} Status")
    print("-" * 80)

    updates_available = 0

    for name, spec in packages:
        pinned = _pinned_version(spec) if spec else None
        latest = _latest_pypi_version(name)

        if latest is None:
            status = "? (PyPI-Fehler)"
            print(f"{name:<35} {spec or '(kein Pin)':<15} {'?':<20} {status}")
            continue

        if pinned is None:
            status = "kein Pin"
            print(f"{name:<35} {'(kein Pin)':<15} {latest:<20} {status}")
            continue

        if _version_tuple(latest) > _version_tuple(pinned):
            status = "UPDATE verfuegbar"
            updates_available += 1
        else:
            status = "aktuell"

        print(f"{name:<35} {spec:<15} {latest:<20} {status}")

    print()

    if updates_available:
        print(f"=> {updates_available} Paket(e) haben Updates verfuegbar.")
        print("   Renovate erstellt automatisch einen PR, sobald es auf main laeuft.")
        if args.strict:
            return 1
    else:
        print("=> Alle Pakete sind aktuell.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
