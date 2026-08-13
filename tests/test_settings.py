"""Settings, path overrides, and folder validation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gencompanion.domain.detect import detect_installs  # noqa: E402
from gencompanion.domain.settings import (  # noqa: E402
    Overrides,
    Settings,
    looks_like_install,
    looks_like_user_data,
)
from tests.fixtures.build_big import build_archive  # noqa: E402


# -- overrides -------------------------------------------------------


def test_override_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    settings = Settings()
    settings.overrides.set_user_data("zerohour", tmp_path / "MySaves")
    settings.save()

    reloaded = Settings.load()
    assert reloaded.overrides.user_data_for("zerohour") == tmp_path / "MySaves"


def test_override_can_be_cleared(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    settings = Settings()
    settings.overrides.set_install("generals", tmp_path / "Game")
    settings.save()

    settings.overrides.set_install("generals", None)
    settings.save()

    assert Settings.load().overrides.install_for("generals") is None


def test_corrupt_settings_does_not_crash(tmp_path: Path, monkeypatch) -> None:
    """A bad settings file must never stop the app starting."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    target = tmp_path / "GeneralsCompanion" / "settings.json"
    target.parent.mkdir(parents=True)
    target.write_text("{ this is not json", encoding="utf-8")

    settings = Settings.load()
    assert not settings.overrides.any_set()


def test_missing_settings_returns_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert not Settings.load().overrides.any_set()


# -- folder validation -----------------------------------------------


def test_user_data_folder_recognised(tmp_path: Path) -> None:
    (tmp_path / "Options.ini").write_text("Resolution = 1920 1080\n")
    (tmp_path / "Save").mkdir()

    ok, reason = looks_like_user_data(tmp_path)
    assert ok
    assert "Options.ini" in reason


def test_wrong_folder_rejected_with_reason(tmp_path: Path) -> None:
    (tmp_path / "holiday.jpg").write_bytes(b"\xff\xd8\xff")

    ok, reason = looks_like_user_data(tmp_path)
    assert not ok
    assert "Options.ini" in reason  # tells the user what was expected


def test_install_folder_recognised_by_exe(tmp_path: Path) -> None:
    (tmp_path / "generals.exe").write_bytes(b"MZ")
    ok, reason = looks_like_install(tmp_path)
    assert ok
    assert "generals.exe" in reason


def test_install_folder_recognised_by_archives(tmp_path: Path) -> None:
    """A repacked install may have no exe but still hold archives."""
    build_archive(tmp_path / "INI.big", {"a.ini": b"x = 1"})
    ok, reason = looks_like_install(tmp_path)
    assert ok
    assert ".big" in reason


def test_empty_folder_rejected(tmp_path: Path) -> None:
    assert not looks_like_install(tmp_path)[0]
    assert not looks_like_user_data(tmp_path)[0]


def test_file_is_not_a_folder(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    target.write_text("x")
    ok, reason = looks_like_user_data(target)
    assert not ok
    assert reason == "not a folder"


# -- detection with overrides ----------------------------------------


def test_override_is_used_by_detection(tmp_path: Path) -> None:
    """A user-chosen folder wins, even somewhere detection would never look."""
    custom = tmp_path / "D_drive" / "MyGeneralsSaves"
    (custom / "Save").mkdir(parents=True)
    (custom / "Options.ini").write_text("Resolution = 800 600\n")

    overrides = Overrides()
    overrides.set_user_data("zerohour", custom)

    installs = detect_installs(overrides)
    zh = next((i for i in installs if i.edition == "zerohour"), None)

    assert zh is not None
    assert zh.user_data_path == custom
    assert zh.manual_user_data is True
    assert zh.options_ini == custom / "Options.ini"


def test_nonexistent_override_is_ignored(tmp_path: Path) -> None:
    """A stale override must not shadow a real detected path."""
    overrides = Overrides()
    overrides.set_user_data("zerohour", tmp_path / "deleted")

    installs = detect_installs(overrides)
    zh = next((i for i in installs if i.edition == "zerohour"), None)
    if zh is not None:
        assert zh.user_data_path != tmp_path / "deleted"
        assert zh.manual_user_data is False


def test_install_override_finds_executable(tmp_path: Path) -> None:
    custom = tmp_path / "PortableGenerals"
    custom.mkdir()
    (custom / "generals.exe").write_bytes(b"MZ")

    overrides = Overrides()
    overrides.set_install("zerohour", custom)

    installs = detect_installs(overrides)
    zh = next(i for i in installs if i.edition == "zerohour")

    assert zh.install_path == custom
    assert zh.executable == custom / "generals.exe"
    assert zh.is_playable
    assert zh.manual_install is True


def test_detection_without_overrides_still_works() -> None:
    """Passing nothing must behave exactly as before."""
    installs = detect_installs()
    assert isinstance(installs, list)
    for install in installs:
        assert install.manual_install is False
        assert install.manual_user_data is False
