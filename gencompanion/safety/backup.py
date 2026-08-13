"""Backups and the change journal.

Every write the app makes goes through here first. Two guarantees:

1. Nothing is overwritten without a restorable copy taken first.
2. Restore only ever touches files this app wrote.

The second is why a journal exists rather than just a folder of backups.
Scanning a directory cannot tell the difference between a file we changed and
one the user hand-edited, and restoring over the latter would destroy their
work. The journal is the authority: if it is not recorded, we do not touch it.

Layout under %LOCALAPPDATA%\\GeneralsCompanion\\:

    backups\\<timestamp>_<name>      the copies
    journal.jsonl                    append-only record, one JSON per line
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from ..domain.settings import app_data_dir

#: Non-baseline backups are capped; the first-run baseline is never evicted.
MAX_BACKUPS = 50

_TIMESTAMP_FMT = "%Y%m%d_%H%M%S"


def backups_dir() -> Path:
    return app_data_dir() / "backups"


def journal_path() -> Path:
    return app_data_dir() / "journal.jsonl"


@dataclass(slots=True)
class JournalEntry:
    """One recorded write. `backup` is the copy taken before it happened."""

    id: str
    target: str
    backup: str | None
    timestamp: str
    reason: str
    is_baseline: bool = False
    #: False once the entry has been rolled back, so restore is idempotent.
    applied: bool = True

    @property
    def target_path(self) -> Path:
        return Path(self.target)

    @property
    def backup_path(self) -> Path | None:
        return Path(self.backup) if self.backup else None

    @property
    def when(self) -> datetime:
        try:
            return datetime.strptime(self.timestamp, _TIMESTAMP_FMT)
        except ValueError:
            return datetime.fromtimestamp(0)

    def exists(self) -> bool:
        backup = self.backup_path
        return backup is not None and backup.is_file()


class Journal:
    """Append-only record of every write, and the authority for restore."""

    def __init__(self, entries: list[JournalEntry] | None = None) -> None:
        self.entries: list[JournalEntry] = entries or []

    @classmethod
    def load(cls) -> Journal:
        path = journal_path()
        if not path.is_file():
            return cls()

        entries: list[JournalEntry] = []
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(JournalEntry(**json.loads(line)))
                except (json.JSONDecodeError, TypeError):
                    # One bad line must not cost the whole journal.
                    continue
        except OSError:
            return cls()

        return cls(entries)

    def append(self, entry: JournalEntry) -> None:
        """Record an entry and flush immediately.

        Flushed before the write it describes completes, so a crash leaves a
        journal that over-reports rather than one that loses a backup.
        """
        self.entries.append(entry)

        path = journal_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry), sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    def rewrite(self) -> None:
        """Rewrite the whole journal. Used after eviction or rollback."""
        path = journal_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        tmp = path.with_name(f".{path.name}.tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                for entry in self.entries:
                    fh.write(json.dumps(asdict(entry), sort_keys=True) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise

    def for_target(self, target: Path) -> list[JournalEntry]:
        """Entries for one file, newest first."""
        wanted = str(target)
        matches = [e for e in self.entries if e.target == wanted]
        return sorted(matches, key=lambda e: e.timestamp, reverse=True)

    def targets(self) -> list[Path]:
        """Every distinct file this app has ever written."""
        seen: dict[str, None] = {}
        for entry in self.entries:
            seen.setdefault(entry.target, None)
        return [Path(t) for t in seen]

    def has_baseline(self, target: Path) -> bool:
        return any(
            e.is_baseline and e.target == str(target) for e in self.entries
        )

    def restorable(self) -> list[JournalEntry]:
        """Applied entries whose backup file still exists, newest first."""
        live = [e for e in self.entries if e.applied and e.exists()]
        return sorted(live, key=lambda e: e.timestamp, reverse=True)


def backup_file(
    target: Path,
    reason: str,
    *,
    journal: Journal | None = None,
    is_baseline: bool = False,
) -> JournalEntry:
    """Copy `target` aside and record it. Call before writing.

    A missing target still produces an entry with no backup, so restore knows
    the file did not exist beforehand and can delete it on rollback.
    """
    journal = journal if journal is not None else Journal.load()

    stamp = datetime.now().strftime(_TIMESTAMP_FMT)
    entry_id = uuid.uuid4().hex[:12]

    backup_path: Path | None = None
    if target.is_file():
        backups_dir().mkdir(parents=True, exist_ok=True)
        backup_path = backups_dir() / f"{stamp}_{entry_id}_{target.name}"
        shutil.copy2(target, backup_path)

    entry = JournalEntry(
        id=entry_id,
        target=str(target),
        backup=str(backup_path) if backup_path else None,
        timestamp=stamp,
        reason=reason,
        is_baseline=is_baseline,
    )
    journal.append(entry)
    prune(journal)
    return entry


def restore(entry: JournalEntry, journal: Journal | None = None) -> Path:
    """Put a backed-up file back, and mark the entry rolled back."""
    journal = journal if journal is not None else Journal.load()
    target = entry.target_path
    backup = entry.backup_path

    if backup is None:
        # The file did not exist before the recorded write, so undoing that
        # write means removing it again.
        target.unlink(missing_ok=True)
    else:
        if not backup.is_file():
            raise FileNotFoundError(f"backup missing: {backup}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, target)

    for candidate in journal.entries:
        if candidate.id == entry.id:
            candidate.applied = False
    journal.rewrite()
    return target


def restore_to_stock(journal: Journal | None = None) -> list[Path]:
    """Undo every write this app has made, oldest backup per target.

    Only journalled targets are touched. A file the app never wrote is never
    restored over, so hand edits made outside the app survive.
    """
    journal = journal if journal is not None else Journal.load()
    restored: list[Path] = []

    for target in journal.targets():
        history = journal.for_target(target)
        if not history:
            continue

        # Oldest entry holds the state before we ever touched this file.
        oldest = min(history, key=lambda e: e.timestamp)
        if not oldest.exists() and oldest.backup is not None:
            continue

        try:
            restore(oldest, journal)
            restored.append(target)
        except OSError:
            continue

    return restored


def prune(journal: Journal | None = None) -> int:
    """Evict oldest non-baseline backups past MAX_BACKUPS. Returns count."""
    journal = journal if journal is not None else Journal.load()

    evictable = sorted(
        (e for e in journal.entries if not e.is_baseline and e.backup),
        key=lambda e: e.timestamp,
    )
    excess = len(evictable) - MAX_BACKUPS
    if excess <= 0:
        return 0

    removed = 0
    for entry in evictable[:excess]:
        backup = entry.backup_path
        if backup is not None:
            try:
                backup.unlink(missing_ok=True)
            except OSError:
                continue
        journal.entries.remove(entry)
        removed += 1

    if removed:
        journal.rewrite()
    return removed
