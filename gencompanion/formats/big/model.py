"""BIG archive data model.

Entry data is never held in memory. A BigEntry points either at a byte range
in the source archive or at a pending file on disk, and is read on demand.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Iterator, Literal

# uint32 offsets cap the format. Refuse writes that would cross this.
MAX_ARCHIVE_SIZE = 0xFFFFFFFF

BigFormat = Literal["BIGF", "BIG4"]


@dataclass(slots=True)
class BigEntry:
    """One file inside an archive.

    Either `archive_path` + `offset` (data lives in the source archive) or
    `pending_path` (data is a file staged on disk, not yet written).
    """

    name: str
    size: int
    offset: int = 0
    archive_path: Path | None = None
    pending_path: Path | None = None
    #: True when the original name was not valid UTF-8 and was decoded latin-1.
    name_is_fallback: bool = False
    #: Original name bytes, preserved verbatim so a round-trip is byte-identical.
    raw_name: bytes = b""

    @property
    def is_pending(self) -> bool:
        return self.pending_path is not None

    @property
    def extension(self) -> str:
        _, _, ext = self.name.rpartition(".")
        return ext.lower() if ext and ext != self.name else ""

    @property
    def directory(self) -> str:
        """Internal folder path, backslash-separated, no trailing slash."""
        head, sep, _ = self.name.rpartition("\\")
        return head if sep else ""

    def read(self, chunk_size: int = 1 << 20) -> Iterator[bytes]:
        """Yield this entry's bytes in chunks. Never loads the whole entry."""
        if self.pending_path is not None:
            with open(self.pending_path, "rb") as fh:
                while chunk := fh.read(chunk_size):
                    yield chunk
            return

        if self.archive_path is None:
            raise ValueError(f"entry {self.name!r} has no data source")

        with open(self.archive_path, "rb") as fh:
            fh.seek(self.offset)
            remaining = self.size
            while remaining > 0:
                chunk = fh.read(min(chunk_size, remaining))
                if not chunk:
                    raise ValueError(
                        f"entry {self.name!r} truncated: expected {self.size} bytes, "
                        f"{self.size - remaining} available"
                    )
                remaining -= len(chunk)
                yield chunk

    def read_all(self) -> bytes:
        """Read the entry fully. Only for entries known to be small."""
        return b"".join(self.read())

    def copy_to(self, dest: BinaryIO) -> int:
        written = 0
        for chunk in self.read():
            dest.write(chunk)
            written += len(chunk)
        return written


@dataclass(slots=True)
class BigArchive:
    path: Path | None
    format: BigFormat = "BIGF"
    entries: list[BigEntry] = field(default_factory=list)
    dirty: bool = False
    #: Entries the reader could not trust, kept for the warnings panel.
    warnings: list[str] = field(default_factory=list)
    #: Set when the header disagreed with the file badly enough to block writes.
    read_only: bool = False

    def __len__(self) -> int:
        return len(self.entries)

    def find(self, name: str) -> BigEntry | None:
        folded = name.casefold()
        for entry in self.entries:
            if entry.name.casefold() == folded:
                return entry
        return None

    def directories(self) -> list[str]:
        """Every distinct internal folder, sorted."""
        seen: set[str] = set()
        for entry in self.entries:
            parts = entry.directory.split("\\") if entry.directory else []
            for depth in range(1, len(parts) + 1):
                seen.add("\\".join(parts[:depth]))
        return sorted(seen)

    def total_data_size(self) -> int:
        return sum(entry.size for entry in self.entries)
