"""BIG archive format: reader, writer, and model."""

from .errors import (
    ArchiveError,
    ArchiveTooLarge,
    DuplicateEntry,
    EntryNotFound,
    NotAnArchive,
    TruncatedArchive,
)
from .model import MAX_ARCHIVE_SIZE, BigArchive, BigEntry
from .reader import HEADER_SIZE, open_archive
from .writer import compute_index_size, write_archive

__all__ = [
    "ArchiveError",
    "ArchiveTooLarge",
    "BigArchive",
    "BigEntry",
    "DuplicateEntry",
    "EntryNotFound",
    "HEADER_SIZE",
    "MAX_ARCHIVE_SIZE",
    "NotAnArchive",
    "TruncatedArchive",
    "compute_index_size",
    "open_archive",
    "write_archive",
]
