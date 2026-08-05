"""Order- and comment-preserving INI handling."""

from .parser import IniFile, IniLine, format_resolution, parse_resolution

__all__ = ["IniFile", "IniLine", "format_resolution", "parse_resolution"]
