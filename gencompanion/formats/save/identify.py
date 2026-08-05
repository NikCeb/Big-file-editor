"""Save file identification. Opens read-only, always.

Format, from inspecting real Zero Hour saves:

    [uint8 name_len][ASCII chunk name][uint32 size LE][payload]

repeated. Observed chunks: CHUNK_GameState, CHUNK_Campaign.

Inside the payload, strings are length-prefixed the same way, which is how
map name, faction, and mission are recovered without understanding the rest
of the structure.

Only the first bytes are read. A 3 MB save costs one small read.
"""

from __future__ import annotations

import re
import struct
from datetime import datetime
from pathlib import Path

from .model import SaveChunk, SaveInfo

_U32_LE = struct.Struct("<I")

#: Enough to cover the identifying chunks without reading the whole save.
_SCAN_BYTES = 4096

#: Chunk names are ASCII and start with this prefix.
_CHUNK_PREFIX = b"CHUNK_"

_MISSION_RE = re.compile(rb"(mission\d+)", re.IGNORECASE)
_MAP_RE = re.compile(rb"([A-Za-z0-9_\-]+\.map)", re.IGNORECASE)
_FACTIONS = (b"usa", b"china", b"gla")

#: Generals Challenge maps carry no faction token. The general's name is in
#: the map filename instead: GC_TankGeneral.map, GC_AirGeneral.map, ...
_GC_MAP_RE = re.compile(r"^GC_(.+?)General\.map$", re.IGNORECASE)

#: Saves below this are campaign-progress markers, not full game states.
#: Observed: markers are 186-768 bytes, real saves are 2 MB and up.
_MARKER_MAX_BYTES = 100_000


def identify(path: str | Path) -> SaveInfo:
    """Read a save's identifying fields. Never opens for writing."""
    path = Path(path)
    stat = path.stat()

    info = SaveInfo(
        path=path,
        filename=path.name,
        timestamp=datetime.fromtimestamp(stat.st_mtime),
        size=stat.st_size,
    )

    if stat.st_size == 0:
        info.valid = False
        info.problem = "file is empty"
        return info

    try:
        with open(path, "rb") as fh:          # "rb" — never "r+b", never "wb"
            head = fh.read(_SCAN_BYTES)
    except OSError as exc:
        info.valid = False
        info.problem = f"could not read: {exc}"
        return info

    info.chunks = _scan_chunks(head)

    if not info.chunks:
        info.valid = False
        info.problem = "no recognisable chunk header; not a Generals save"
        return info

    info.map_name = _find_map(head)
    info.mission = _find_mission(head)
    info.faction = _find_faction(head)
    info.challenge_general = _find_challenge_general(info.map_name)
    info.is_progress_marker = stat.st_size <= _MARKER_MAX_BYTES

    return info


def _scan_chunks(blob: bytes) -> list[SaveChunk]:
    """Walk the chunk chain from the start of the file.

    Stops at the first record that does not look like a chunk, which keeps a
    corrupt or unfamiliar save from producing nonsense.
    """
    chunks: list[SaveChunk] = []
    pos = 0
    limit = len(blob)

    while pos + 1 < limit:
        name_len = blob[pos]
        if name_len == 0 or pos + 1 + name_len + 4 > limit:
            break

        raw_name = blob[pos + 1 : pos + 1 + name_len]
        if not raw_name.startswith(_CHUNK_PREFIX):
            break

        try:
            name = raw_name.decode("ascii")
        except UnicodeDecodeError:
            break

        size = _U32_LE.unpack_from(blob, pos + 1 + name_len)[0]
        chunks.append(SaveChunk(name=name, offset=pos, size=size))

        # Advance past this record. Payloads can exceed the scan window, in
        # which case we stop here and keep what we found.
        pos = pos + 1 + name_len + 4 + size
        if pos >= limit:
            break

    return chunks


def _find_map(blob: bytes) -> str | None:
    match = _MAP_RE.search(blob)
    return match.group(1).decode("ascii", "replace") if match else None


def _find_mission(blob: bytes) -> str | None:
    match = _MISSION_RE.search(blob)
    return match.group(1).decode("ascii", "replace").lower() if match else None


def _find_faction(blob: bytes) -> str | None:
    """Find a faction token that is length-prefixed, not a chance substring."""
    for faction in _FACTIONS:
        prefixed = bytes([len(faction)]) + faction
        if prefixed in blob:
            return faction.decode("ascii")
    return None


def _find_challenge_general(map_name: str | None) -> str | None:
    """Recover the Generals Challenge opponent from the map filename.

    GC maps carry no faction token, so `faction` is legitimately None for
    them. The general's name is the identifying detail instead.
    """
    if not map_name:
        return None
    match = _GC_MAP_RE.match(map_name)
    if not match:
        return None
    # "SuperWeapons" -> "Super Weapons"
    raw = match.group(1)
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", raw)
    return f"{spaced} General"


def list_saves(save_dir: str | Path) -> list[SaveInfo]:
    """Identify every .sav in a folder, newest first."""
    save_dir = Path(save_dir)
    if not save_dir.is_dir():
        return []

    saves = [identify(p) for p in sorted(save_dir.glob("*.sav"))]
    saves.sort(key=lambda s: s.timestamp, reverse=True)
    return saves
