r"""Find Generals / Zero Hour installs and their user-data folders.

The user-data folder (Documents\...Data\) holds Options.ini and saves, and
exists even when the install folder does not. Detection reports them
separately so the tool still works for whichever it finds.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

Edition = str  # "zerohour" | "generals"

_USER_DATA_DIRS: dict[Edition, str] = {
    "zerohour": "Command and Conquer Generals Zero Hour Data",
    "generals": "Command and Conquer Generals Data",
}

_EXE_NAMES: dict[Edition, tuple[str, ...]] = {
    "zerohour": ("generals.exe", "game.dat"),
    "generals": ("generals.exe", "game.dat"),
}

_INSTALL_HINTS: dict[Edition, tuple[str, ...]] = {
    "zerohour": (
        r"Command and Conquer Generals Zero Hour",
        r"Command & Conquer Generals Zero Hour",
        r"Command and Conquer Generals Zero Hour\Command and Conquer Generals Zero Hour",
        r"EA Games\Command & Conquer Generals Zero Hour",
        r"Origin Games\Command and Conquer Generals Zero Hour",
        r"Steam\steamapps\common\Command and Conquer Generals Zero Hour",
        r"Steam\steamapps\common\Command & Conquer Generals Zero Hour",
    ),
    "generals": (
        r"Command and Conquer Generals",
        r"Command & Conquer Generals",
        r"EA Games\Command & Conquer Generals",
        r"Origin Games\Command and Conquer Generals",
        r"Steam\steamapps\common\Command and Conquer Generals",
    ),
}

_LABELS: dict[Edition, str] = {
    "zerohour": "Zero Hour",
    "generals": "Generals",
}


@dataclass(slots=True)
class GameInstall:
    edition: Edition
    label: str
    #: Folder holding the executable. None when only user data was found.
    install_path: Path | None = None
    #: Documents\...Data\ — Options.ini, Skirmish.ini, Save\.
    user_data_path: Path | None = None
    executable: Path | None = None
    big_files: list[Path] = field(default_factory=list)

    @property
    def options_ini(self) -> Path | None:
        if self.user_data_path is None:
            return None
        path = self.user_data_path / "Options.ini"
        return path if path.exists() else None

    @property
    def skirmish_ini(self) -> Path | None:
        if self.user_data_path is None:
            return None
        path = self.user_data_path / "Skirmish.ini"
        return path if path.exists() else None

    @property
    def save_dir(self) -> Path | None:
        if self.user_data_path is None:
            return None
        path = self.user_data_path / "Save"
        return path if path.is_dir() else None

    @property
    def is_playable(self) -> bool:
        """True when we found something we can actually launch."""
        return self.executable is not None

    @property
    def has_config(self) -> bool:
        return self.options_ini is not None

    def summary(self) -> str:
        bits: list[str] = []
        if self.executable:
            bits.append("install")
        if self.has_config:
            bits.append("config")
        if self.save_dir:
            count = len(list(self.save_dir.glob("*.sav")))
            bits.append(f"{count} saves")
        return ", ".join(bits) if bits else "nothing found"


def _search_roots() -> list[Path]:
    roots: list[Path] = []
    for var in ("ProgramFiles(x86)", "ProgramFiles", "ProgramW6432"):
        value = os.environ.get(var)
        if value:
            roots.append(Path(value))

    # Common non-default drives.
    for letter in ("C", "D", "E", "F"):
        drive = Path(f"{letter}:\\")
        if drive.exists():
            roots.append(drive / "Games")
            roots.append(drive / "Program Files (x86)")
            roots.append(drive)

    seen: set[Path] = set()
    unique: list[Path] = []
    for root in roots:
        if root not in seen and root.exists():
            seen.add(root)
            unique.append(root)
    return unique


def _find_install_dir(edition: Edition) -> tuple[Path | None, Path | None]:
    """Return (install_dir, executable) for an edition, if found."""
    for root in _search_roots():
        for hint in _INSTALL_HINTS[edition]:
            candidate = root / hint
            if not candidate.is_dir():
                continue
            for exe_name in _EXE_NAMES[edition]:
                exe = candidate / exe_name
                if exe.exists():
                    return candidate, exe
            return candidate, None
    return None, None


def _find_user_data(edition: Edition) -> Path | None:
    documents = Path(os.path.expanduser("~")) / "Documents"
    candidate = documents / _USER_DATA_DIRS[edition]
    return candidate if candidate.is_dir() else None


def detect_installs() -> list[GameInstall]:
    """Find every Generals edition present on this machine."""
    installs: list[GameInstall] = []

    for edition in ("zerohour", "generals"):
        install_dir, executable = _find_install_dir(edition)
        user_data = _find_user_data(edition)

        if install_dir is None and user_data is None:
            continue

        big_files: list[Path] = []
        if install_dir is not None:
            big_files = sorted(install_dir.glob("*.big"))

        installs.append(
            GameInstall(
                edition=edition,
                label=_LABELS[edition],
                install_path=install_dir,
                user_data_path=user_data,
                executable=executable,
                big_files=big_files,
            )
        )

    return installs


def is_windows() -> bool:
    return sys.platform == "win32"
