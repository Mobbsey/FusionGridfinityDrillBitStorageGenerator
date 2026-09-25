"""Increment the patch component of the Fusion add-in manifest version."""

import json
import re
from pathlib import Path


MANIFEST_PATH = Path("DrillBitGridfinity.manifest")
SEMANTIC_VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    current_version = manifest.get("version", "")
    match = SEMANTIC_VERSION.fullmatch(current_version)

    if match is None:
        raise SystemExit(
            f"Expected a major.minor.patch version, found {current_version!r}"
        )

    major, minor, patch = map(int, match.groups())
    next_version = f"{major}.{minor}.{patch + 1}"
    manifest["version"] = next_version
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Updated manifest version: {current_version} -> {next_version}")


if __name__ == "__main__":
    main()
