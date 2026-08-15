"""Display settings: read and write Options.ini safely.

Resolution is the one verified hardware fix. The in-game menu offers a short
list of 4:3 modes, but Options.ini accepts anything, which is how a 2003 game
ends up running at 2560x1440.

Format note: resolution is stored space-separated ("2560 1440"), not with an
x. Getting that wrong writes a value the game silently ignores.

Every write here goes through safety.backup first.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..formats.ini import IniFile, format_resolution, parse_resolution
from ..safety.backup import Journal, backup_file

#: Keys this screen manages. Anything else in the file is left untouched.
RESOLUTION_KEY = "Resolution"

#: Settings worth surfacing, with their safe values. Sourced from community
#: documentation of Options.ini; a user's file only contains keys they have
#: changed, so absence means "default", not "unsupported".
_QUALITY_KEYS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("StaticGameLOD", "Detail preset", ("Low", "Medium", "High", "Custom")),
    ("IdealStaticGameLOD", "Detail preset (ideal)", ("Low", "Medium", "High", "Custom")),
    ("TextureReduction", "Texture reduction", ("0", "1", "2")),
    ("UseShadowVolumes", "Unit shadows", ("yes", "no")),
    ("UseShadowDecals", "Shadow decals", ("yes", "no")),
    ("UseCloudMap", "Cloud map", ("yes", "no")),
    ("UseLightMap", "Light map", ("yes", "no")),
    ("ShowTrees", "Trees", ("yes", "no")),
    ("ShowSoftWaterEdge", "Soft water edges", ("yes", "no")),
    ("ExtraAnimations", "Extra animations", ("yes", "no")),
    ("HeatEffects", "Heat effects", ("yes", "no")),
    ("DynamicLOD", "Dynamic detail", ("yes", "no")),
    ("BuildingOcclusion", "Building occlusion", ("yes", "no")),
    ("AntiAliasing", "Anti-aliasing", ("0", "1", "2", "3")),
)


@dataclass(slots=True)
class QualitySetting:
    key: str
    label: str
    choices: tuple[str, ...]
    current: str | None  # None means absent from the file, i.e. game default


@dataclass(slots=True)
class DisplayConfig:
    """Current state of the display-related settings in Options.ini."""

    path: Path
    resolution: tuple[int, int] | None
    quality: list[QualitySetting]
    raw_keys: int

    @property
    def resolution_text(self) -> str:
        if self.resolution is None:
            return "not set"
        return f"{self.resolution[0]} x {self.resolution[1]}"


def read_display_config(options_ini: Path) -> DisplayConfig:
    ini = IniFile.load(options_ini)

    quality = [
        QualitySetting(key=key, label=label, choices=choices, current=ini.get(key))
        for key, label, choices in _QUALITY_KEYS
    ]

    return DisplayConfig(
        path=options_ini,
        resolution=parse_resolution(ini.get(RESOLUTION_KEY)),
        quality=quality,
        raw_keys=len(ini.keys()),
    )


def apply_display_changes(
    options_ini: Path,
    *,
    resolution: tuple[int, int] | None = None,
    quality: dict[str, str] | None = None,
    journal: Journal | None = None,
) -> tuple[Path, list[str]]:
    """Write display settings, backing up first.

    Returns (written path, changed key names). Makes no write and takes no
    backup when nothing actually differs.
    """
    ini = IniFile.load(options_ini)

    if resolution is not None:
        ini.set(RESOLUTION_KEY, format_resolution(*resolution))

    for key, value in (quality or {}).items():
        ini.set(key, value)

    changed = ini.changed_keys()
    if not changed:
        return options_ini, []

    journal = journal if journal is not None else Journal.load()
    is_baseline = not journal.has_baseline(options_ini)
    backup_file(
        options_ini,
        reason="display settings: " + ", ".join(changed),
        journal=journal,
        is_baseline=is_baseline,
    )

    ini.save(options_ini)
    return options_ini, changed


def common_resolutions() -> tuple[tuple[int, int], ...]:
    return (
        (1280, 720),
        (1366, 768),
        (1600, 900),
        (1920, 1080),
        (2560, 1080),
        (2560, 1440),
        (3440, 1440),
        (3840, 2160),
    )
