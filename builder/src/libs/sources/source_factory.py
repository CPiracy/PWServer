from pathlib import Path

from .abstract_source import AbstractSource


class SourceFactory:
    """A factory for input sources."""

    def create(self, path: Path) -> AbstractSource:
        """Create a source for the given path."""
        raise NotImplementedError
