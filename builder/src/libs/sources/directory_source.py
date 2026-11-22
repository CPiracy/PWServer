from hashlib import file_digest
from pathlib import Path, PurePath
from shutil import copyfile

from .abstract_source import AbstractSource
from .source_file import SourceFile


class DirectorySource(AbstractSource):
    """A directory used as a source of input files."""

    def __init__(self, path: Path) -> None:
        super().__init__(path)
        if not self.path.is_dir():
            raise NotADirectoryError(self.path)

    def list_files(self) -> list[SourceFile]:
        """Return available source files in path order."""
        return [
            file
            for path in sorted(self.path.rglob("*"))
            if (file := self.get_file(path)) is not None
        ]

    def get_file(self, path: PurePath) -> SourceFile | None:
        """Return a file in this source, or None if no file matches the path."""
        entry = self.path / path
        if entry.is_file() and entry.resolve(strict=True).is_relative_to(self.path):
            if entry.is_symlink():
                return SourceFile(self, entry, entry.parent / entry.readlink())
            return SourceFile(self, entry)
        return None

    def get_file_mode(self, path: PurePath) -> int:
        """Return the file mode from filesystem metadata."""
        return (self.path / path).stat().st_mode

    def get_file_sha256(self, path: PurePath) -> str:
        """Return the hexadecimal SHA-256 digest of the file contents."""
        with (self.path / path).open("rb") as stream:
            return file_digest(stream, "sha256").hexdigest()

    def extract_file(self, file: PurePath, path: Path) -> None:
        """Copy the file contents to the given path."""
        copyfile(self.path / file, path)
