"""Backup, journal, and restore.

This layer is the one that can destroy a user's config, so the tests focus on
the two guarantees: nothing is overwritten without a copy, and restore never
touches a file the app did not write.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gencompanion.domain.display import (  # noqa: E402
    apply_display_changes,
    read_display_config,
)
from gencompanion.safety.backup import (  # noqa: E402
    MAX_BACKUPS,
    Journal,
    backup_file,
    prune,
    restore,
    restore_to_stock,
)


@pytest.fixture(autouse=True)
def isolated_appdata(tmp_path, monkeypatch):
    """Keep every test's journal and backups out of the real app data dir."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))
    yield


@pytest.fixture
def options_ini(tmp_path: Path) -> Path:
    path = tmp_path / "Options.ini"
    path.write_text(
        "Gamma = 50\n"
        "Resolution = 800 600\n"
        "StaticGameLOD = Low\n"
        "UserName = O_00R_00I_00G_00I_00N_00\n",
        encoding="utf-8",
    )
    return path


# -- backup ----------------------------------------------------------


def test_backup_copies_file(options_ini: Path) -> None:
    original = options_ini.read_bytes()
    entry = backup_file(options_ini, "test")

    assert entry.exists()
    assert entry.backup_path.read_bytes() == original


def test_backup_of_missing_file_records_absence(tmp_path: Path) -> None:
    """Restoring must be able to delete a file that did not exist before."""
    entry = backup_file(tmp_path / "nothing.ini", "test")
    assert entry.backup is None
    assert not entry.exists()


def test_journal_survives_reload(options_ini: Path) -> None:
    backup_file(options_ini, "first")
    backup_file(options_ini, "second")

    reloaded = Journal.load()
    assert len(reloaded.for_target(options_ini)) == 2


def test_corrupt_journal_line_is_skipped(options_ini: Path) -> None:
    from gencompanion.safety.backup import journal_path

    backup_file(options_ini, "good")
    with open(journal_path(), "a", encoding="utf-8") as fh:
        fh.write("{ not json\n")

    assert len(Journal.load().entries) == 1


# -- restore ---------------------------------------------------------


def test_restore_puts_content_back(options_ini: Path) -> None:
    original = options_ini.read_text(encoding="utf-8")
    entry = backup_file(options_ini, "before edit")

    options_ini.write_text("Resolution = 9999 9999\n", encoding="utf-8")
    restore(entry)

    assert options_ini.read_text(encoding="utf-8") == original


def test_restore_removes_file_that_did_not_exist(tmp_path: Path) -> None:
    target = tmp_path / "new.ini"
    entry = backup_file(target, "creating")
    target.write_text("created by us\n", encoding="utf-8")

    restore(entry)
    assert not target.exists()


def test_restore_marks_entry_not_applied(options_ini: Path) -> None:
    entry = backup_file(options_ini, "test")
    restore(entry)

    reloaded = Journal.load()
    match = next(e for e in reloaded.entries if e.id == entry.id)
    assert match.applied is False


def test_restore_to_stock_uses_oldest_state(options_ini: Path) -> None:
    """Stock means before the app ever touched it, not the last change."""
    original = options_ini.read_text(encoding="utf-8")

    backup_file(options_ini, "change 1")
    options_ini.write_text("Resolution = 1280 720\n", encoding="utf-8")

    backup_file(options_ini, "change 2")
    options_ini.write_text("Resolution = 1920 1080\n", encoding="utf-8")

    restore_to_stock()
    assert options_ini.read_text(encoding="utf-8") == original


def test_restore_to_stock_ignores_untouched_files(tmp_path: Path) -> None:
    """A file the app never wrote must survive restore-to-stock untouched."""
    ours = tmp_path / "Options.ini"
    ours.write_text("Gamma = 50\n", encoding="utf-8")

    theirs = tmp_path / "HandEdited.ini"
    theirs.write_text("do not touch me\n", encoding="utf-8")

    backup_file(ours, "our change")
    ours.write_text("Gamma = 99\n", encoding="utf-8")

    restore_to_stock()

    assert ours.read_text(encoding="utf-8") == "Gamma = 50\n"
    assert theirs.read_text(encoding="utf-8") == "do not touch me\n"


# -- retention -------------------------------------------------------


def test_prune_keeps_baseline(tmp_path: Path) -> None:
    target = tmp_path / "f.ini"
    target.write_text("x\n", encoding="utf-8")

    journal = Journal.load()
    backup_file(target, "baseline", journal=journal, is_baseline=True)
    for i in range(MAX_BACKUPS + 5):
        backup_file(target, f"change {i}", journal=journal)

    reloaded = Journal.load()
    assert any(e.is_baseline for e in reloaded.entries)
    non_baseline = [e for e in reloaded.entries if not e.is_baseline]
    assert len(non_baseline) <= MAX_BACKUPS


def test_prune_returns_zero_when_under_cap(options_ini: Path) -> None:
    backup_file(options_ini, "one")
    assert prune() == 0


# -- display integration ---------------------------------------------


def test_apply_writes_and_backs_up(options_ini: Path) -> None:
    original = options_ini.read_text(encoding="utf-8")

    path, changed = apply_display_changes(options_ini, resolution=(2560, 1440))

    assert "Resolution" in changed
    assert "2560 1440" in path.read_text(encoding="utf-8")

    entries = Journal.load().for_target(options_ini)
    assert entries
    assert entries[0].backup_path.read_text(encoding="utf-8") == original


def test_apply_with_no_change_writes_nothing(options_ini: Path) -> None:
    """No diff means no write and no backup, so history stays meaningful."""
    _, changed = apply_display_changes(options_ini, resolution=(800, 600))
    assert changed == []
    assert not Journal.load().for_target(options_ini)


def test_apply_preserves_utf16_username(options_ini: Path) -> None:
    """The UserName UTF-16 pattern must survive a resolution change."""
    apply_display_changes(options_ini, resolution=(1920, 1080))
    text = options_ini.read_text(encoding="utf-8")
    assert "UserName = O_00R_00I_00G_00I_00N_00" in text


def test_apply_preserves_unrelated_keys(options_ini: Path) -> None:
    apply_display_changes(options_ini, resolution=(1920, 1080))
    text = options_ini.read_text(encoding="utf-8")
    assert "Gamma = 50" in text
    assert "StaticGameLOD = Low" in text


def test_read_display_config(options_ini: Path) -> None:
    config = read_display_config(options_ini)
    assert config.resolution == (800, 600)
    assert config.resolution_text == "800 x 600"

    lod = next(q for q in config.quality if q.key == "StaticGameLOD")
    assert lod.current == "Low"

    absent = next(q for q in config.quality if q.key == "AntiAliasing")
    assert absent.current is None


def test_quality_change_is_written(options_ini: Path) -> None:
    _, changed = apply_display_changes(
        options_ini, quality={"AntiAliasing": "2"}
    )
    assert "AntiAliasing" in changed
    assert "AntiAliasing = 2" in options_ini.read_text(encoding="utf-8")


def test_full_cycle_apply_then_restore(options_ini: Path) -> None:
    """The path that matters: change something, then undo it completely."""
    original = options_ini.read_text(encoding="utf-8")

    apply_display_changes(options_ini, resolution=(3840, 2160))
    assert "3840 2160" in options_ini.read_text(encoding="utf-8")

    restore_to_stock()
    assert options_ini.read_text(encoding="utf-8") == original
