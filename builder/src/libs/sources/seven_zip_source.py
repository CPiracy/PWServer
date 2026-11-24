from pathlib import Path, PurePath, PurePosixPath
from posixpath import normpath

from py7zr import SevenZipFile
from py7zr.io import BytesIOFactory, HashIOFactory

from .abstract_source import AbstractSource
from .source_file import SourceFile


class SevenZipSource(AbstractSource):
    """A 7z archive used as a source of input files."""

    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self._files: dict[PurePosixPath, int] = {}
        self._sizes: dict[PurePosixPath, int] = {}

        with SevenZipFile(self.path, "r") as archive:
            for file in archive.files:
                if file.is_file:
                    entry = PurePosixPath(file.filename)
                    self._files[entry] = file.posix_mode or 0
                    self._sizes[entry] = file.uncompressed
            self._links = self._filter_links(self._read_links(archive))

    def list_files(self) -> list[SourceFile]:
        """Return available source files in path order."""
        paths = self._files.keys() | self._links.keys()
        return [SourceFile(self, path, self._links.get(path)) for path in sorted(paths)]

    def get_file(self, path: PurePath) -> SourceFile | None:
        """Return the archive file at the given path, or None."""
        entry = PurePosixPath(path)
        if entry in self._files or entry in self._links:
            return SourceFile(self, entry, self._links.get(entry))
        return None

    def get_file_mode(self, path: PurePath) -> int:
        """Return the mode stored for the archive entry."""
        return self._files.get(PurePosixPath(path), 0)

    def get_file_size(self, path: PurePath) -> int:
        """Return the uncompressed size of the archive entry in bytes."""
        return self._sizes.get(PurePosixPath(path), 0)

    def get_file_sha256(self, path: PurePath) -> str:
        """Return the hexadecimal SHA-256 digest of the archive entry."""
        name = path.as_posix()
        factory = HashIOFactory()
        with SevenZipFile(self.path, "r") as archive:
            archive.extract(targets=[name], factory=factory)
        return factory.get(name).read().hex()

    def extract_file(self, file: PurePath, path: Path) -> None:
        """Write the archive entry to the given filesystem path."""
        name = file.as_posix()
        with SevenZipFile(self.path, "r") as archive:
            factory = BytesIOFactory(archive.getinfo(name).uncompressed)
            archive.extract(targets=[name], factory=factory)
        path.write_bytes(factory.get(name).read())

    def _filter_links(
        self, links: dict[PurePosixPath, PurePosixPath]
    ) -> dict[PurePosixPath, PurePosixPath]:
        """Keep links whose chains end at an archive file."""
        result = {}
        for path, target in links.items():
            seen = {path}
            while target in links and target not in seen:
                seen.add(target)
                target = links[target]
            if target in self._files and target not in seen:
                result[path] = links[path]
        return result

    @staticmethod
    def _read_links(archive: SevenZipFile) -> dict[PurePosixPath, PurePosixPath]:
        """Read symbolic link targets from their archive entries."""
        members = [file for file in archive.files if file.is_symlink]
        if not members:
            return {}

        factory = BytesIOFactory(max(file.uncompressed for file in members))
        archive.extract(targets=[file.filename for file in members], factory=factory)
        links = {}
        for file in members:
            path = PurePosixPath(file.filename)
            data = factory.get(path.as_posix()).read()
            target = path.parent / PurePosixPath(
                data.decode("utf-8", errors="surrogateescape")
            )
            links[path] = PurePosixPath(normpath(target.relative_to(target.anchor)))
        return links
