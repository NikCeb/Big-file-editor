"""Save file identification. Read-only, no write path exists."""

from .identify import identify, list_saves
from .model import SaveChunk, SaveInfo

__all__ = ["SaveChunk", "SaveInfo", "identify", "list_saves"]
