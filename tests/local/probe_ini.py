"""Opt-in probe: round-trip the real Options.ini in a sandbox copy.

Never touches the original. Copies it to a temp folder, applies a change,
restores it, and checks the bytes match.

    python tests/local/probe_ini.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REAL = (
    Path(os.path.expanduser("~"))
    / "Documents"
    / "Command and Conquer Generals Zero Hour Data"
    / "Options.ini"
)


def main() -> int:
    if not REAL.is_file():
        print(f"skip: {REAL} not found")
        return 0

    sandbox = Path(tempfile.mkdtemp(prefix="gc_probe_"))
    os.environ["LOCALAPPDATA"] = str(sandbox / "appdata")

    from gencompanion.domain.display import (
        apply_display_changes,
        read_display_config,
    )
    from gencompanion.safety.backup import restore_to_stock

    copy = sandbox / "Options.ini"
    shutil.copy2(REAL, copy)
    original = copy.read_bytes()

    print(f"source:  {REAL}")
    print(f"sandbox: {copy}")
    print(f"size:    {len(original)} bytes\n")

    config = read_display_config(copy)
    print(f"resolution read: {config.resolution_text}")
    print(f"keys in file:    {config.raw_keys}")
    set_keys = [q.label for q in config.quality if q.current is not None]
    print(f"quality set:     {', '.join(set_keys) or '(none, all default)'}\n")

    _, changed = apply_display_changes(copy, resolution=(3840, 2160))
    print(f"applied: {changed}")
    after = copy.read_text(encoding="utf-8")
    print(f"  resolution now: {'3840 2160' in after}")
    print(f"  UserName intact: {'UserName = O_00R' in after or 'UserName' not in after}")

    restore_to_stock()
    restored = copy.read_bytes()

    identical = restored == original
    print(f"\nrestore-to-stock byte-identical: {identical}")

    shutil.rmtree(sandbox, ignore_errors=True)
    return 0 if identical else 1


if __name__ == "__main__":
    raise SystemExit(main())
