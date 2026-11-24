from __future__ import annotations

from pathlib import Path, PurePath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .abstract_source import AbstractSource


class SourceFile:
    """A file that can be extracted from a source."""

    def __init__(
        self, source: AbstractSource, path: PurePath, link: PurePath | None = None
    ) -> None:
        self._source = source
        self._path = path
        self._link = link

    @property
    def source(self) -> AbstractSource:
        """Return the source that provides this file."""
        return self._source

    @property
    def path(self) -> PurePath:
        """Return the path that identifies the file in its source."""
        return self._path

    @property
    def link(self) -> SourceFile | None:
        """Return the target file if this file is a symbolic link."""
        return self.source.get_file(self._link) if self._link is not None else None

    @property
    def mode(self) -> int:
        """Return the file mode."""
        return self.source.get_file_mode(self.resolve().path)

    @property
    def size(self) -> int:
        """Return the file size in bytes."""
        return self.source.get_file_size(self.resolve().path)

    @property
    def sha256(self) -> str:
        """Return the hexadecimal SHA-256 digest of the file contents."""
        return self.source.get_file_sha256(self.resolve().path)

    def extract(self, path: Path) -> None:
        """Write the file to the given filesystem path."""
        self.source.extract_file(self.resolve().path, path)

    def resolve(self) -> SourceFile:
        """Return the final file after following symbolic links."""
        link = self.link
        return link.resolve() if link is not None else self
