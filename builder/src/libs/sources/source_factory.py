from pathlib import Path

from .abstract_source import AbstractSource
from .directory_source import DirectorySource
from .seven_zip_source import SevenZipSource


class SourceFactory:
    """A factory for input sources."""

    def create(self, path: Path) -> AbstractSource:
        """Create a source for the given path."""
        if path.is_dir():
            return DirectorySource(path)
        if path.suffix.lower() == ".7z":
            return SevenZipSource(path)
        raise NotImplementedError(f"No source reader for {path}")
