"""Build synthetic BIG archives for tests.

No copyrighted assets. Every fixture is generated from scratch, byte-exact to
the real format so round-trip tests prove something.
"""

from __future__ import annotations

import struct
from pathlib import Path

_U32_BE = struct.Struct(">I")
_U32_LE = struct.Struct("<I")
HEADER_SIZE = 16


def build_archive(
    dest: Path,
    files: dict[str, bytes],
    *,
    magic: bytes = b"BIGF",
) -> Path:
    """Write a valid archive containing `files` (internal name -> bytes)."""
    index_size = HEADER_SIZE
    for name in files:
        index_size += 8 + len(name.encode("utf-8")) + 1

    data_size = sum(len(blob) for blob in files.values())
    archive_size = index_size + data_size

    offset = index_size
    records: list[tuple[str, int, int]] = []
    for name, blob in files.items():
        records.append((name, offset, len(blob)))
        offset += len(blob)

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as out:
        out.write(magic)
        out.write(_U32_LE.pack(archive_size))
        out.write(_U32_BE.pack(len(files)))
        out.write(_U32_BE.pack(index_size))

        for name, entry_offset, size in records:
            out.write(_U32_BE.pack(entry_offset))
            out.write(_U32_BE.pack(size))
            out.write(name.encode("utf-8"))
            out.write(b"\0")

        for blob in files.values():
            out.write(blob)

    return dest


def sample_files() -> dict[str, bytes]:
    """A small spread: nested paths, an INI, binary, and an empty entry."""
    return {
        "Data\\INI\\GameData.ini": b"Framerate = 30\r\nResolution = 800 600\r\n",
        "Data\\INI\\Object\\Vehicle.ini": b"; vehicle definitions\r\n",
        "Art\\Textures\\logo.tga": bytes(range(256)) * 4,
        "readme.txt": b"synthetic fixture",
        "empty.dat": b"",
    }
