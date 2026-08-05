"""Save identification tests.

Includes the guarantee that matters most: there is no write path. The spec
makes saves read-only by design, and `test_no_write_path_exists` fails if
anyone ever adds one.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gencompanion.formats import save as save_pkg  # noqa: E402
from gencompanion.formats.save import identify, list_saves  # noqa: E402
from tests.fixtures.build_save import build_challenge_save, build_save  # noqa: E402


def test_identifies_campaign_save(tmp_path: Path) -> None:
    # Padding must exceed the progress-marker threshold, or this is correctly
    # classified as a marker rather than a full save.
    path = build_save(tmp_path / "00000000.sav", padding=200_000)
    info = identify(path)

    assert info.valid
    assert info.faction == "usa"
    assert info.mission == "mission01"
    assert info.map_name == "MD_USA01.map"
    assert info.kind == "campaign"
    assert info.display_name == "USA — mission01"


def test_identifies_challenge_save(tmp_path: Path) -> None:
    """GC saves carry no faction; the general comes from the map name."""
    path = build_challenge_save(tmp_path / "gc.sav", "TankGeneral")
    info = identify(path)

    assert info.valid
    assert info.faction is None
    assert info.challenge_general == "Tank General"
    assert info.display_name == "Challenge — Tank General"
    assert not info.is_campaign


def test_multiword_challenge_general(tmp_path: Path) -> None:
    path = build_challenge_save(tmp_path / "gc2.sav", "SuperWeaponsGeneral")
    info = identify(path)
    assert info.challenge_general == "Super Weapons General"


def test_progress_marker_detected(tmp_path: Path) -> None:
    """Small saves record campaign progress, not a full game state."""
    small = build_save(tmp_path / "small.sav", padding=0)
    large = build_save(tmp_path / "large.sav", padding=200_000)

    assert identify(small).is_progress_marker
    assert identify(small).kind == "progress"
    assert not identify(large).is_progress_marker
    assert identify(large).kind == "campaign"


def test_chunks_are_walked(tmp_path: Path) -> None:
    path = build_save(tmp_path / "c.sav", padding=1024)
    info = identify(path)
    names = [c.name for c in info.chunks]
    assert "CHUNK_GameState" in names
    assert "CHUNK_Campaign" in names


def test_empty_file_is_invalid(tmp_path: Path) -> None:
    path = tmp_path / "empty.sav"
    path.write_bytes(b"")
    info = identify(path)
    assert not info.valid
    assert info.problem == "file is empty"


def test_garbage_is_invalid(tmp_path: Path) -> None:
    path = tmp_path / "junk.sav"
    path.write_bytes(b"\xff" * 512)
    info = identify(path)
    assert not info.valid
    assert "not a Generals save" in (info.problem or "")


def test_degrades_without_crashing(tmp_path: Path) -> None:
    """Unfamiliar contents still yield the guaranteed floor fields."""
    path = tmp_path / "odd.sav"
    path.write_bytes(b"\x0fCHUNK_GameState" + b"\x04\x00\x00\x00" + b"\x00" * 4)
    info = identify(path)
    assert info.filename == "odd.sav"
    assert info.size > 0
    assert info.timestamp is not None


def test_list_saves_sorts_newest_first(tmp_path: Path) -> None:
    import os
    import time

    a = build_save(tmp_path / "a.sav")
    time.sleep(0.01)
    b = build_save(tmp_path / "b.sav")
    os.utime(a, (time.time() - 3600, time.time() - 3600))

    saves = list_saves(tmp_path)
    assert [s.filename for s in saves] == ["b.sav", "a.sav"]


def test_list_saves_on_missing_dir(tmp_path: Path) -> None:
    assert list_saves(tmp_path / "nope") == []


def test_no_write_path_exists() -> None:
    """Saves are read-only by design. No module may open one for writing.

    Parses the AST rather than scanning text, so comments and docstrings that
    mention write modes do not trip it. Only real open() calls count.
    """
    import ast

    write_modes = {"w", "wb", "a", "ab", "r+", "r+b", "w+", "w+b", "x", "xb"}
    package_dir = Path(save_pkg.__file__).parent

    for source_file in sorted(package_dir.glob("*.py")):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name not in {"open", "open_text", "write_text", "write_bytes"}:
                continue

            assert name == "open", (
                f"{source_file.name} calls {name}() — saves are read-only"
            )

            # open(path) defaults to "r"; an explicit mode is arg 1 or keyword.
            mode: str | None = None
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value

            assert mode not in write_modes, (
                f"{source_file.name} line {node.lineno} opens a file with "
                f"mode {mode!r} — saves must never be opened for writing"
            )
