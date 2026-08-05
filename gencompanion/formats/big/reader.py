"""BIG archive reader.

Endianness is the trap in this format, and getting it wrong produces archives
the game silently refuses to load:

    magic          4 bytes ASCII   "BIGF" or "BIG4"
    archive_size   uint32 LITTLE   total file size
    entry_count    uint32 BIG      number of index records
    index_size     uint32 BIG      header + index block size

and per index record:

    offset         uint32 BIG      absolute offset of the entry's data
    size           uint32 BIG      entry length in bytes
    name           cstring         null-terminated, backslash separators

Only archive_size is little-endian. Everything else is big-endian.

The reader is deliberately forgiving: a damaged index costs you the bad
entries and a warning, not the whole archive. Anything it cannot trust sets
`read_only` so a rebuild can never write the damage back out.
"""

from __future__ import annotations

import struct
from pathlib import Path

from .errors import NotAnArchive, TruncatedArchive
from .model import BigArchive, BigEntry, BigFormat

HEADER_SIZE = 16
_MAGICS: tuple[bytes, ...] = (b"BIGF", b"BIG4")
_U32_BE = struct.Struct(">I")
_U32_LE = struct.Struct("<I")

#: An index record is 8 bytes plus at least a null terminator.
_MIN_RECORD_SIZE = 9


def open_archive(path: str | Path) -> BigArchive:
    """Parse an archive's header and index. Entry data is not read."""
    path = Path(path)
    file_size = path.stat().st_size

    if file_size < HEADER_SIZE:
        raise TruncatedArchive(
            f"{path.name} is {file_size} bytes, too small to hold a header"
        )

    with open(path, "rb") as fh:
        header = fh.read(HEADER_SIZE)

        magic = header[:4]
        if magic not in _MAGICS:
            raise NotAnArchive(
                f"{path.name} does not start with BIGF or BIG4 "
                f"(found {magic!r})"
            )

        archive_size = _U32_LE.unpack_from(header, 4)[0]
        entry_count = _U32_BE.unpack_from(header, 8)[0]
        index_size = _U32_BE.unpack_from(header, 12)[0]

        archive = BigArchive(path=path, format=magic.decode("ascii"))  # type: ignore[arg-type]

        if archive_size != file_size:
            archive.warnings.append(
                f"header claims {archive_size} bytes, file is {file_size}"
            )

        # A count that cannot physically fit means a corrupt header. Read what
        # the file can actually hold rather than trusting the number.
        max_possible = max(0, (file_size - HEADER_SIZE) // _MIN_RECORD_SIZE)
        if entry_count > max_possible:
            archive.warnings.append(
                f"header claims {entry_count} entries but the file can hold at "
                f"most {max_possible}; reading what fits"
            )
            archive.read_only = True
            entry_count = max_possible

        index_bytes = fh.read(max(0, index_size - HEADER_SIZE)) if index_size else b""
        if len(index_bytes) < (index_size - HEADER_SIZE):
            # Index block is short; fall back to reading records until we run out.
            fh.seek(HEADER_SIZE)
            index_bytes = fh.read()
            archive.read_only = True
            archive.warnings.append("index block is shorter than the header claims")

    archive.entries = _parse_index(index_bytes, entry_count, file_size, path, archive)
    return archive


def _parse_index(
    blob: bytes,
    entry_count: int,
    file_size: int,
    path: Path,
    archive: BigArchive,
) -> list[BigEntry]:
    entries: list[BigEntry] = []
    pos = 0
    blob_len = len(blob)

    for index in range(entry_count):
        if pos + 8 > blob_len:
            archive.warnings.append(
                f"index ended after {len(entries)} of {entry_count} entries"
            )
            archive.read_only = True
            break

        offset = _U32_BE.unpack_from(blob, pos)[0]
        size = _U32_BE.unpack_from(blob, pos + 4)[0]
        pos += 8

        terminator = blob.find(b"\0", pos)
        if terminator == -1:
            archive.warnings.append(
                f"entry {index} has an unterminated name; stopping"
            )
            archive.read_only = True
            break

        raw_name = blob[pos:terminator]
        pos = terminator + 1

        name, is_fallback = _decode_name(raw_name)

        # Offsets past EOF mean the record is junk. Skip it, keep the rest.
        if offset + size > file_size:
            archive.warnings.append(
                f"{name or f'entry {index}'} points past end of file "
                f"(offset {offset}, size {size}); skipped"
            )
            archive.read_only = True
            continue

        entries.append(
            BigEntry(
                name=name,
                size=size,
                offset=offset,
                archive_path=path,
                name_is_fallback=is_fallback,
                raw_name=raw_name,
            )
        )

    return entries


def _decode_name(raw: bytes) -> tuple[str, bool]:
    """Decode an entry name, falling back to latin-1.

    Returns the name and whether the fallback was used. `raw_name` keeps the
    original bytes so writing back is byte-identical either way.
    """
    try:
        return raw.decode("utf-8"), False
    except UnicodeDecodeError:
        return raw.decode("latin-1"), True
