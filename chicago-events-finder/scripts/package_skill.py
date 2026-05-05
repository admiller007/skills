#!/usr/bin/env python3
from __future__ import annotations

import zipfile
from pathlib import Path


SKILL_NAME = "chicago-events-finder"
PACKAGE_NAME = f"{SKILL_NAME}.skill"
INCLUDED_PATHS = [
    Path("SKILL.md"),
    Path("agents/openai.yaml"),
    Path("references/eventbrite.md"),
    Path("references/chicago-park-district.md"),
    Path("references/evvnt-sources.md"),
    Path("references/html-sources.md"),
    Path("references/meetup.md"),
    Path("references/web-sources.md"),
    Path("references/enrichment-sources.md"),
    Path("scripts/do312_events.py"),
    Path("scripts/chicago_on_the_cheap_events.py"),
    Path("scripts/chicago_park_district_events.py"),
    Path("scripts/evvnt_events.py"),
    Path("scripts/meetup_events.py"),
    Path("scripts/secret_chicago_editorial.py"),
    Path("scripts/timeout_chicago_editorial.py"),
]


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    package_path = root / PACKAGE_NAME

    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative_path in INCLUDED_PATHS:
            full_path = root / relative_path
            if not full_path.exists():
                raise SystemExit(f"Missing required path: {relative_path}")

            archive_path = Path(SKILL_NAME) / relative_path
            archive.write(full_path, archive_path.as_posix())

    print(f"Wrote {package_path}")


if __name__ == "__main__":
    main()
