"""BIG reader/writer tests.

The round-trip test is the one that matters: open an archive, write it back
with no edits, and the bytes must be identical. If endianness is wrong anywhere
this fails immediately.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gencompanion.formats.big import (  # noqa: E402
    ArchiveTooLarge,
    NotAnArchive,
    open_archive,
    write_archive,
)
from tests.fixtures.build_big import build_archive, sample_files  # noqa: E402


@pytest.fixture
def archive_path(tmp_path: Path) -> Path:
    return build_archive(tmp_path / "test.big", sample_files())


def test_reads_entry_count(archive_path: Path) -> None:
    archive = open_archive(archive_path)
    assert len(archive) == len(sample_files())
    assert not archive.warnings
    assert not archive.read_only


def test_reads_names_and_sizes(archive_path: Path) -> None:
    archive = open_archive(archive_path)
    expected = sample_files()
    for entry in archive.entries:
        assert entry.name in expected
        assert entry.size == len(expected[entry.name])


def test_entry_data_matches(archive_path: Path) -> None:
    archive = open_archive(archive_path)
    expected = sample_files()
    for entry in archive.entries:
        assert entry.read_all() == expected[entry.name]


def test_roundtrip_is_byte_identical(archive_path: Path, tmp_path: Path) -> None:
    """The acceptance criterion: open then write with no edits changes nothing."""
    original = archive_path.read_bytes()
    archive = open_archive(archive_path)
    out = write_archive(archive, tmp_path / "out.big")
    assert out.read_bytes() == original


def test_header_endianness(archive_path: Path) -> None:
    """archive_size is little-endian; count and index_size are big-endian."""
    raw = archive_path.read_bytes()
    assert raw[:4] == b"BIGF"

    archive_size_le = struct.unpack_from("<I", raw, 4)[0]
    entry_count_be = struct.unpack_from(">I", raw, 8)[0]

    assert archive_size_le == len(raw)
    assert entry_count_be == len(sample_files())

    # The same fields read with the wrong endianness must not accidentally
    # agree, or the test proves nothing.
    assert struct.unpack_from(">I", raw, 4)[0] != len(raw)


def test_rejects_non_archive(tmp_path: Path) -> None:
    bad = tmp_path / "notanarchive.big"
    bad.write_bytes(b"XXXX" + bytes(64))
    with pytest.raises(NotAnArchive):
        open_archive(bad)


def test_truncated_index_is_survivable(tmp_path: Path) -> None:
    """A damaged index costs the bad entries and a warning, not the archive."""
    path = build_archive(tmp_path / "t.big", sample_files())
    raw = bytearray(path.read_bytes())
    # Claim far more entries than the file can hold.
    struct.pack_into(">I", raw, 8, 9999)
    path.write_bytes(bytes(raw))

    archive = open_archive(path)
    assert archive.read_only
    assert archive.warnings
    assert len(archive) < 9999


def test_offset_past_eof_is_skipped(tmp_path: Path) -> None:
    path = build_archive(tmp_path / "t.big", sample_files())
    raw = bytearray(path.read_bytes())
    # First index record sits right after the 16-byte header.
    struct.pack_into(">I", raw, 16, 0xFFFFFF00)
    path.write_bytes(bytes(raw))

    archive = open_archive(path)
    assert archive.read_only
    assert any("past end of file" in w for w in archive.warnings)
    assert len(archive) == len(sample_files()) - 1


def test_empty_entry_survives_roundtrip(tmp_path: Path) -> None:
    path = build_archive(tmp_path / "e.big", {"empty.dat": b""})
    archive = open_archive(path)
    assert archive.entries[0].size == 0
    out = write_archive(archive, tmp_path / "out.big")
    assert out.read_bytes() == path.read_bytes()


def test_directories_are_derived(archive_path: Path) -> None:
    archive = open_archive(archive_path)
    dirs = archive.directories()
    assert "Data" in dirs
    assert "Data\\INI" in dirs
    assert "Data\\INI\\Object" in dirs


def test_oversized_archive_is_refused(tmp_path: Path, monkeypatch) -> None:
    path = build_archive(tmp_path / "t.big", {"a.txt": b"x"})
    archive = open_archive(path)
    archive.entries[0].size = 0xFFFFFFFF
    with pytest.raises(ArchiveTooLarge):
        write_archive(archive, tmp_path / "big.big")
