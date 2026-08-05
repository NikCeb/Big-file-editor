"""Launch option builder for Generals / Zero Hour.

Command-line switches verified against community documentation:
  https://www.cnclabs.com/generals/zerohour/command-line-arguments.aspx
  https://steamcommunity.com/sharedfiles/filedetails/?id=3202583319

The important one is -nofpslimit. It does remove the 30 FPS cap, but the
engine ties simulation speed to framerate, so the game also runs roughly
twice as fast. That is a broken game, not a quality-of-life fix, so it is
opt-in and carries a loud warning. Genuine high-FPS at correct speed needs
GenTool, which caps frames independently of game logic and is out of scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    NORMAL = "normal"
    CAUTION = "caution"


@dataclass(frozen=True, slots=True)
class LaunchSwitch:
    flag: str
    label: str
    description: str
    severity: Severity = Severity.NORMAL
    #: Warning shown when enabled. Non-empty implies the user must be told.
    warning: str = ""
    #: True when the switch takes a numeric argument (-xres 1920).
    takes_value: bool = False


SWITCHES: tuple[LaunchSwitch, ...] = (
    LaunchSwitch(
        flag="-quickstart",
        label="Skip intro movies and shell map",
        description="Boots straight to the menu. The single best launch tweak.",
    ),
    LaunchSwitch(
        flag="-noshellmap",
        label="Disable menu background battle",
        description="Keeps intro movies but drops the animated menu backdrop. "
        "Reduces menu stutter on some systems.",
    ),
    LaunchSwitch(
        flag="-nologo",
        label="Skip EA logo",
        description="Removes the publisher logo on startup.",
    ),
    LaunchSwitch(
        flag="-win",
        label="Run in a window",
        description="Windowed mode at the configured resolution. Useful on "
        "multi-monitor setups and for alt-tabbing.",
    ),
    LaunchSwitch(
        flag="-noshaders",
        label="Disable shader effects",
        description="Legacy compatibility switch for old ATI hardware. Only "
        "useful if you get random crashes.",
    ),
    LaunchSwitch(
        flag="-nofpslimit",
        label="Remove the 30 FPS cap",
        description="Lifts the framerate limit.",
        severity=Severity.CAUTION,
        warning=(
            "The engine ties game speed to framerate. Removing the cap also "
            "makes the game run roughly twice as fast — units, build times and "
            "animations all speed up. This is not a smoothness fix. For high "
            "FPS at correct speed, use GenTool instead."
        ),
    ),
)

_BY_FLAG = {s.flag: s for s in SWITCHES}


@dataclass(slots=True)
class LaunchConfig:
    """A launch configuration: which switches, plus optional resolution."""

    enabled: set[str] = field(default_factory=set)
    xres: int | None = None
    yres: int | None = None
    mod_big: str | None = None

    def enable(self, flag: str) -> None:
        if flag not in _BY_FLAG:
            raise KeyError(f"unknown switch: {flag}")
        self.enabled.add(flag)

    def disable(self, flag: str) -> None:
        self.enabled.discard(flag)

    def toggle(self, flag: str, on: bool) -> None:
        self.enable(flag) if on else self.disable(flag)

    def set_resolution(self, width: int | None, height: int | None) -> None:
        if width is not None and height is not None:
            if width < 640 or height < 480:
                raise ValueError("resolution must be at least 640x480")
        self.xres, self.yres = width, height

    def warnings(self) -> list[str]:
        """Warnings for every enabled switch that carries one."""
        return [
            _BY_FLAG[flag].warning
            for flag in sorted(self.enabled)
            if _BY_FLAG[flag].warning
        ]

    def arguments(self) -> list[str]:
        """The argument list, in a stable order."""
        args: list[str] = []
        for switch in SWITCHES:                 # declaration order, not set order
            if switch.flag in self.enabled:
                args.append(switch.flag)

        if self.xres and self.yres:
            args += ["-xres", str(self.xres), "-yres", str(self.yres)]

        if self.mod_big:
            args += ["-mod", self.mod_big]

        return args

    def command_line(self, executable: Path) -> str:
        """Full command line, quoted for display and for a shortcut target."""
        exe = f'"{executable}"' if " " in str(executable) else str(executable)
        args = self.arguments()
        return f"{exe} {' '.join(args)}".strip()

    def describe(self) -> str:
        args = self.arguments()
        return " ".join(args) if args else "(no switches — default launch)"


def switch_by_flag(flag: str) -> LaunchSwitch:
    return _BY_FLAG[flag]
