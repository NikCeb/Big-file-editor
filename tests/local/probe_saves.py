"""Opt-in probe: run the save identifier against a real install.

Not part of CI. Requires Generals/Zero Hour save files on this machine.

    python tests/local/probe_saves.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from gencompanion.formats.save import list_saves  # noqa: E402

CANDIDATES = [
    Path(os.path.expanduser("~"))
    / "Documents"
    / "Command and Conquer Generals Zero Hour Data"
    / "Save",
    Path(os.path.expanduser("~"))
    / "Documents"
    / "Command and Conquer Generals Data"
    / "Save",
]


def main() -> int:
    found_any = False

    for save_dir in CANDIDATES:
        if not save_dir.is_dir():
            print(f"skip (missing): {save_dir}")
            continue

        saves = list_saves(save_dir)
        if saves:
            found_any = True
        print(f"\n{save_dir}")
        print(f"  {len(saves)} saves\n")

        for s in saves:
            print(
                f"  {s.filename:<14} {s.size:>9,}  "
                f"{s.kind:<9} "
                f"{s.display_name:<28} "
                f"{str(s.map_name)[:24]:<24} "
                f"chunks={len(s.chunks)}"
            )
            if s.problem:
                print(f"       problem: {s.problem}")

    if not found_any:
        print("No save folders found. Nothing to probe.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
