"""BIG archive writer.

Rebuilds header, index, and every entry offset from scratch. Offsets cannot be
carried over from the source: adding, removing, or resizing any entry shifts
every entry after it.

Writes go to a temp file beside the destination and are renamed into place only
after the result parses back cleanly. A crash mid-write leaves the original
untouched.
"""

from __future__ import annotations

import os
import struct
from pathlib import Path

from .errors import ArchiveTooLarge
from .model import MAX_ARCHIVE_SIZE, BigArchive, BigEntry
from .reader import HEADER_SIZE, open_archive

_U32_BE = struct.Struct(">I")
_U32_LE = struct.Struct("<I")


def compute_index_size(entries: list[BigEntry]) -> int:
    """Header plus every index record, which is where entry data starts."""
    total = HEADER_SIZE
    for entry in entries:
        total += 8 + len(_name_bytes(entry)) + 1
    return total


def write_archive(
    archive: BigArchive,
    dest: str | Path,
    *,
    verify: bool = True,
) -> Path:
    """Write `archive` to `dest`. Returns the written path.

    Raises ArchiveTooLarge if the result would cross the uint32 ceiling.
    """
    dest = Path(dest)
    entries = archive.entries

    index_size = compute_index_size(entries)
    data_size = sum(entry.size for entry in entries)
    archive_size = index_size + data_size

    if archive_size > MAX_ARCHIVE_SIZE:
        raise ArchiveTooLarge(
            f"archive would be {archive_size:,} bytes, past the {MAX_ARCHIVE_SIZE:,} "
            f"limit imposed by uint32 offsets. Remove or shrink entries."
        )

    # Assign offsets in list order, starting where the index ends.
    offset = index_size
    layout: list[tuple[BigEntry, int]] = []
    for entry in entries:
        layout.append((entry, offset))
        offset += entry.size

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.name}.tmp")

    try:
        with open(tmp, "wb") as out:
            out.write(archive.format.encode("ascii"))
            out.write(_U32_LE.pack(archive_size))   # little-endian
            out.write(_U32_BE.pack(len(entries)))   # big-endian
            out.write(_U32_BE.pack(index_size))     # big-endian

            for entry, entry_offset in layout:
                out.write(_U32_BE.pack(entry_offset))
                out.write(_U32_BE.pack(entry.size))
                out.write(_name_bytes(entry))
                out.write(b"\0")

            for entry, entry_offset in layout:
                if out.tell() != entry_offset:
                    raise AssertionError(
                        f"offset drift at {entry.name!r}: at {out.tell()}, "
                        f"index says {entry_offset}"
                    )
                written = entry.copy_to(out)
                if written != entry.size:
                    raise AssertionError(
                        f"{entry.name!r} wrote {written} bytes, expected {entry.size}"
                    )

            out.flush()
            os.fsync(out.fileno())

        if verify:
            check = open_archive(tmp)
            if len(check) != len(entries):
                raise AssertionError(
                    f"verification failed: wrote {len(entries)} entries, "
                    f"read back {len(check)}"
                )

        os.replace(tmp, dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise

    archive.dirty = False
    return dest


def _name_bytes(entry: BigEntry) -> bytes:
    """Original bytes when unchanged, so round-trips stay byte-identical."""
    if entry.raw_name:
        try:
            if entry.raw_name.decode("utf-8") == entry.name:
                return entry.raw_name
        except UnicodeDecodeError:
            if entry.raw_name.decode("latin-1") == entry.name:
                return entry.raw_name
    return entry.name.encode("utf-8")
