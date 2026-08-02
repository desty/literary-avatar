"""Verify that prepared assets match the published provenance manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "provenance.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures = []

    for relative_path, expected_hash in manifest["assets"].items():
        path = ROOT / relative_path
        if not path.exists():
            failures.append(f"missing: {relative_path}")
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            failures.append(
                f"hash mismatch: {relative_path}\n"
                f"  expected {expected_hash}\n"
                f"  actual   {actual_hash}"
            )

    if failures:
        raise SystemExit("\n".join(failures))

    print(f"[ok] Verified {len(manifest['assets'])} prepared assets")


if __name__ == "__main__":
    main()
