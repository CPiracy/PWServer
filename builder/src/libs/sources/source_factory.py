from pathlib import Path

from .abstract_source import AbstractSource
from .directory_source import DirectorySource


class SourceFactory:
    """A factory for input sources."""

    def create(self, path: Path) -> AbstractSource:
        """Create a source for the given path."""
        if path.is_dir():
            return DirectorySource(path)
        raise NotImplementedError(f"No source reader for {path}")
