"""Save file model. Read-only by design.

There is deliberately no field model, no offset table, and no write path.
Saves are parsed far enough to identify and validate them, nothing more.
Editing save values is a trainer; this tool is not that.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(slots=True, frozen=True)
class SaveChunk:
    """One `[len][name][uint32 size][payload]` record."""

    name: str
    offset: int
    size: int


@dataclass(slots=True)
class SaveInfo:
    """What we can tell about a save without deep parsing.

    The first four fields are the guaranteed floor. Everything after is
    best-effort and may be None on an unfamiliar save.
    """

    path: Path
    filename: str
    timestamp: datetime
    size: int
    valid: bool = True
    problem: str | None = None

    # Best-effort.
    mission: str | None = None
    faction: str | None = None
    map_name: str | None = None
    difficulty: str | None = None
    #: Generals Challenge opponent, e.g. "Tank General". GC saves carry no
    #: faction token, so this is how they are identified instead.
    challenge_general: str | None = None
    #: Small saves that record campaign progress rather than a full game state.
    is_progress_marker: bool = False
    chunks: list[SaveChunk] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        if self.challenge_general:
            return f"Challenge — {self.challenge_general}"
        if self.mission and self.faction:
            return f"{self.faction.upper()} — {self.mission}"
        if self.map_name:
            return self.map_name
        return self.filename

    @property
    def kind(self) -> str:
        if self.is_progress_marker:
            return "progress"
        if self.challenge_general:
            return "challenge"
        if self.mission:
            return "campaign"
        return "unknown"

    @property
    def is_campaign(self) -> bool:
        return self.mission is not None and not self.challenge_general
