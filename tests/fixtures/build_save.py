"""Build synthetic save files for tests.

Mirrors the real chunk layout observed in Zero Hour saves:
    [uint8 name_len][ASCII chunk name][uint32 size LE][payload]

No copyrighted data. Payloads are minimal but structurally faithful.
"""

from __future__ import annotations

import struct
from pathlib import Path

_U32_LE = struct.Struct("<I")


def _chunk(name: str, payload: bytes) -> bytes:
    encoded = name.encode("ascii")
    return bytes([len(encoded)]) + encoded + _U32_LE.pack(len(payload)) + payload


def _pstr(value: str) -> bytes:
    """Length-prefixed string, the way the format stores them."""
    raw = value.encode("ascii")
    return bytes([len(raw)]) + raw


def build_save(
    dest: Path,
    *,
    map_name: str = "MD_USA01.map",
    faction: str | None = "usa",
    mission: str = "mission01",
    padding: int = 0,
) -> Path:
    """Write a save whose identifying fields are recoverable."""
    state = _pstr(map_name)
    if faction:
        state += _pstr(faction)

    campaign = b""
    if faction:
        campaign += _pstr(faction)
    campaign += _pstr(mission)

    blob = _chunk("CHUNK_GameState", state) + _chunk("CHUNK_Campaign", campaign)
    if padding:
        blob += _chunk("CHUNK_GameStateMap", b"\0" * padding)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(blob)
    return dest


def build_challenge_save(dest: Path, general: str = "TankGeneral") -> Path:
    """A Generals Challenge save: no faction token, general in the map name."""
    return build_save(
        dest,
        map_name=f"GC_{general}.map",
        faction=None,
        mission="mission01",
        padding=0,
    )
