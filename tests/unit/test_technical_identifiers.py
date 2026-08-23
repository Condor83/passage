from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
ALLOWLIST_PATH = ROOT / "docs/development/technical-identifier-allowlist.json"
IDENTIFIERS = (
    "scripture" + "_chat",
    "scripture" + "-chat",
    "Scripture" + "Chat",
    "Scripture" + " Chat",
    "SCRIPTURE" + "_CHAT",
    "SCRIPTURE" + " CHAT",
)
SEARCH_ROOTS = (
    ROOT / ".agents",
    ROOT / "docs",
    ROOT / "src",
    ROOT / "supabase",
    ROOT / "tests",
    ROOT / "wiki",
)


def test_legacy_technical_identifiers_exist_only_in_reviewed_historical_lines() -> None:
    allowlist = json.loads(ALLOWLIST_PATH.read_text())
    historical_file = allowlist["historical_file"]
    allowed_lines = {
        (path, line_number)
        for path, line_numbers in allowlist["allowed_lines"].items()
        for line_number in line_numbers
    }
    observed_allowed: set[tuple[str, int]] = set()
    unexpected: list[str] = []

    for root in SEARCH_ROOTS:
        for path in root.rglob("*"):
            if not path.is_file() or path == ALLOWLIST_PATH or ".venv" in path.parts:
                continue
            try:
                lines = path.read_text().splitlines()
            except UnicodeDecodeError:
                continue
            relative = path.relative_to(ROOT).as_posix()
            for line_number, line in enumerate(lines, start=1):
                if not any(identifier in line for identifier in IDENTIFIERS):
                    continue
                if relative == historical_file:
                    continue
                key = (relative, line_number)
                if key in allowed_lines:
                    observed_allowed.add(key)
                else:
                    unexpected.append(f"{relative}:{line_number}:{line.strip()}")

    assert unexpected == []
    assert observed_allowed == allowed_lines
