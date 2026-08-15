"""Order- and comment-preserving INI reader/writer for Generals config.

`configparser` is unusable here: it discards comments, reorders keys, and
normalises whitespace. Generals config files must survive a round trip
untouched except for the values the user actually changed.

The concrete hazard, seen in a real Options.ini:

    UserName = O_00R_00I_00G_00I_00N_00

That is "ORIGIN" as UTF-16 stored inside an otherwise-ASCII file. Any writer
that re-encodes values will corrupt the player's profile name. This parser
keeps every line's original text and rewrites only the lines it was told to
change.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class IniLine:
    """One physical line, kept verbatim unless its value is changed."""

    raw: str
    key: str | None = None
    value: str | None = None
    #: Text between the key and the '=' plus after it, so spacing survives.
    separator: str = " = "
    dirty: bool = False

    @property
    def is_setting(self) -> bool:
        return self.key is not None

    def render(self) -> str:
        if not self.is_setting or not self.dirty:
            return self.raw
        return f"{self.key}{self.separator}{self.value}"


class IniFile:
    """A parsed INI that can round-trip byte-identically."""

    def __init__(self, lines: list[IniLine], newline: str, encoding: str) -> None:
        self.lines = lines
        self.newline = newline
        self.encoding = encoding

    # -- reading -------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path) -> IniFile:
        path = Path(path)
        raw_bytes = path.read_bytes()

        encoding = "utf-8"
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = raw_bytes.decode("latin-1")
            encoding = "latin-1"

        newline = "\r\n" if "\r\n" in text else "\n"
        raw_lines = text.split(newline)

        # A trailing newline produces a final empty element; keep track so the
        # rewrite reproduces it exactly.
        lines = [cls._parse_line(raw) for raw in raw_lines]
        return cls(lines, newline, encoding)

    @staticmethod
    def _parse_line(raw: str) -> IniLine:
        stripped = raw.strip()
        if not stripped or stripped.startswith((";", "#", "[")):
            return IniLine(raw=raw)

        if "=" not in raw:
            return IniLine(raw=raw)

        key_part, _, value_part = raw.partition("=")
        key = key_part.strip()
        if not key:
            return IniLine(raw=raw)

        # Preserve exact spacing around '='.
        separator = key_part[len(key_part.rstrip()) :] + "=" + (
            value_part[: len(value_part) - len(value_part.lstrip())]
        )
        return IniLine(
            raw=raw,
            key=key,
            value=value_part.strip(),
            separator=separator or " = ",
        )

    # -- access --------------------------------------------------------

    def get(self, key: str, default: str | None = None) -> str | None:
        folded = key.casefold()
        for line in self.lines:
            if line.key and line.key.casefold() == folded:
                return line.value
        return default

    def keys(self) -> list[str]:
        return [line.key for line in self.lines if line.key]

    def as_dict(self) -> dict[str, str]:
        return {
            line.key: line.value  # type: ignore[misc]
            for line in self.lines
            if line.key is not None and line.value is not None
        }

    def set(self, key: str, value: str) -> None:
        """Change a value, or append the key if it is absent."""
        folded = key.casefold()
        for line in self.lines:
            if line.key and line.key.casefold() == folded:
                if line.value != value:
                    line.value = value
                    line.dirty = True
                return

        # Append before any trailing blank line so the file stays tidy.
        insert_at = len(self.lines)
        while insert_at > 0 and not self.lines[insert_at - 1].raw.strip():
            insert_at -= 1
        self.lines.insert(
            insert_at,
            IniLine(raw="", key=key, value=value, separator=" = ", dirty=True),
        )

    @property
    def dirty(self) -> bool:
        return any(line.dirty for line in self.lines)

    def changed_keys(self) -> list[str]:
        return [line.key for line in self.lines if line.dirty and line.key]

    # -- writing -------------------------------------------------------

    def render(self) -> str:
        return self.newline.join(line.render() for line in self.lines)

    def save(self, path: str | Path) -> Path:
        """Write atomically: temp file, then replace."""
        import os

        path = Path(path)
        tmp = path.with_name(f".{path.name}.tmp")
        try:
            tmp.write_bytes(self.render().encode(self.encoding))
            os.replace(tmp, path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        return path


def parse_resolution(value: str | None) -> tuple[int, int] | None:
    """Options.ini stores resolution space-separated: `2560 1440`."""
    if not value:
        return None
    parts = value.split()
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def format_resolution(width: int, height: int) -> str:
    return f"{width} {height}"
