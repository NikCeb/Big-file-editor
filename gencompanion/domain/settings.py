"""Persisted app settings: manual path overrides and preferences.

Stored as JSON under %LOCALAPPDATA%\\GeneralsCompanion\\settings.json.

Manual overrides always beat auto-detection. A user who picks a folder is
telling us something we could not work out ourselves, so we never second-guess
it or silently fall back to a detected path.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

_APP_DIR_NAME = "GeneralsCompanion"
_SETTINGS_FILE = "settings.json"


def app_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return Path(base) / _APP_DIR_NAME


def settings_path() -> Path:
    return app_data_dir() / _SETTINGS_FILE


@dataclass(slots=True)
class Overrides:
    """User-chosen paths, keyed by edition ("zerohour" | "generals")."""

    install_paths: dict[str, str] = field(default_factory=dict)
    user_data_paths: dict[str, str] = field(default_factory=dict)

    def install_for(self, edition: str) -> Path | None:
        raw = self.install_paths.get(edition)
        return Path(raw) if raw else None

    def user_data_for(self, edition: str) -> Path | None:
        raw = self.user_data_paths.get(edition)
        return Path(raw) if raw else None

    def set_install(self, edition: str, path: Path | None) -> None:
        if path is None:
            self.install_paths.pop(edition, None)
        else:
            self.install_paths[edition] = str(path)

    def set_user_data(self, edition: str, path: Path | None) -> None:
        if path is None:
            self.user_data_paths.pop(edition, None)
        else:
            self.user_data_paths[edition] = str(path)

    def any_set(self) -> bool:
        return bool(self.install_paths or self.user_data_paths)


@dataclass(slots=True)
class Settings:
    overrides: Overrides = field(default_factory=Overrides)

    @classmethod
    def load(cls) -> Settings:
        path = settings_path()
        if not path.is_file():
            return cls()

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # A corrupt settings file must never stop the app starting.
            return cls()

        overrides_raw = raw.get("overrides", {})
        return cls(
            overrides=Overrides(
                install_paths=dict(overrides_raw.get("install_paths", {})),
                user_data_paths=dict(overrides_raw.get("user_data_paths", {})),
            )
        )

    def save(self) -> Path:
        path = settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        tmp = path.with_name(f".{path.name}.tmp")
        try:
            tmp.write_text(
                json.dumps(asdict(self), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            os.replace(tmp, path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        return path


def looks_like_user_data(path: Path) -> tuple[bool, str]:
    """Check a folder is plausibly a Generals user-data folder.

    Returns (ok, reason). Used to give the user a real answer when they pick
    the wrong folder, rather than silently accepting it.
    """
    if not path.is_dir():
        return False, "not a folder"

    markers = ("Options.ini", "Skirmish.ini", "Save", "Maps", "Replays")
    found = [m for m in markers if (path / m).exists()]

    if not found:
        return False, (
            "no Generals data found here — expected Options.ini, a Save folder, "
            "or Maps"
        )
    return True, f"found {', '.join(found)}"


def looks_like_install(path: Path) -> tuple[bool, str]:
    """Check a folder is plausibly a Generals install folder."""
    if not path.is_dir():
        return False, "not a folder"

    executables = [n for n in ("generals.exe", "game.dat") if (path / n).exists()]
    bigs = list(path.glob("*.big"))

    if not executables and not bigs:
        return False, (
            "no game files found here — expected generals.exe, game.dat, "
            "or .big archives"
        )

    parts: list[str] = []
    if executables:
        parts.append(", ".join(executables))
    if bigs:
        parts.append(f"{len(bigs)} .big archives")
    return True, f"found {'; '.join(parts)}"
