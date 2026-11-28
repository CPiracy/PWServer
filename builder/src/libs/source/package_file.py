from pathlib import Path, PurePosixPath

from .source_file import SourceFile


class PackageFile(SourceFile):
    """A source file selected for a package destination."""

    def __init__(self, source_file: SourceFile, destination: PurePosixPath) -> None:
        self._destination = destination
        self._source_file = source_file
        self._source = self._source_file._source
        self._path = self._source_file._path
        self._link = self._source_file._link

    @property
    def source_file(self) -> SourceFile:
        """Return the selected source file."""
        return self._source_file

    @property
    def destination(self) -> PurePosixPath:
        """Return the destination path inside the package."""
        return self._destination

    def extract(self, path: Path) -> None:
        """Extract the file to its destination inside the server directory."""
        target = path / self.destination
        target.parent.mkdir(parents=True, exist_ok=True)
        super().extract(target)
