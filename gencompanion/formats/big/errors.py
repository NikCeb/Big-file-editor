"""Errors raised by the BIG reader and writer."""

from __future__ import annotations


class ArchiveError(Exception):
    """Base for every archive problem."""


class NotAnArchive(ArchiveError):
    """Magic bytes were not BIGF or BIG4."""


class TruncatedArchive(ArchiveError):
    """The file ended before the header or index did."""


class ArchiveTooLarge(ArchiveError):
    """Writing would push the archive past the uint32 offset ceiling."""


class DuplicateEntry(ArchiveError):
    """An entry with that internal name already exists."""


class EntryNotFound(ArchiveError):
    """No entry with that internal name."""
