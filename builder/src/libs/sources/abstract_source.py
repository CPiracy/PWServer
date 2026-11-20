from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path, PurePath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .source_file import SourceFile


class AbstractSource(ABC):
    """A source of input files for the package builder."""

    @property
    @abstractmethod
    def path(self) -> Path:
        """Return the absolute path to the source."""

    @abstractmethod
    def list_files(self) -> list[SourceFile]:
        """Return the files available in the source."""

    @abstractmethod
    def get_file(self, path: PurePath) -> SourceFile:
        """Return the file at the given path, interpreted within this source."""

    @abstractmethod
    def get_file_sha256(self, path: PurePath) -> str:
        """Return the hexadecimal SHA-256 digest of the file at this path."""

    @abstractmethod
    def extract_file(self, file: PurePath, path: Path) -> None:
        """Write the source entry to the given filesystem path."""
