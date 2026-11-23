import re
from collections import defaultdict
from pathlib import Path, PurePath, PurePosixPath

from ..sources.source_factory import SourceFactory
from ..sources.source_file import SourceFile
from .config import Config
from .package_file import PackageFile


class ConfigBuilder:
    """Build a package configuration from ordered input sources."""

    _PW_DIRECTORIES = (
        "gacd",
        "gamed",
        "gamedbd",
        "gauthd",
        "gdeliveryd",
        "gfactiond",
        "glinkd",
        "licenseservice",
        "logservice",
        "uniquenamed",
    )
    _PW_FILES = (
        r"home/license\.conf",
        r"licenseservice\.sql",
        r"pw\d+\.sql",
    )
    _PW_REGEX = (
        re.compile(rf"(^|.*/)(?P<path>({'|'.join(_PW_DIRECTORIES)})/.+)"),
        re.compile(rf"(^|.*/)(?P<path>{'|'.join(_PW_FILES)})"),
    )

    def __init__(self, paths: list[Path], *, batch: bool = False) -> None:
        self._paths = tuple(paths)
        self._batch = batch
        self.included: list[PackageFile] = []
        self.excluded: list[SourceFile] = []

    def build(self) -> Config:
        """Build the configuration for this instance. Call once."""
        factory = SourceFactory()
        filtered: dict[PurePosixPath, list[SourceFile]] = defaultdict(list)
        for path in self._paths:
            for file in factory.create(path).list_files():
                destination = self._filter(file.path)
                if destination is None:
                    self.excluded.append(file)
                else:
                    filtered[destination].append(file)

        grouped = self._group(filtered)
        for destination, group in grouped.items():
            self._select(group, destination)
        return Config(self.included)

    def _filter(self, path: PurePath) -> PurePosixPath | None:
        """Return a server path for an original source path, or None."""
        posix = path.as_posix()
        for regex in self._PW_REGEX:
            match = regex.fullmatch(posix)
            if match:
                return PurePosixPath(match["path"])
        return None

    def _group(
        self, filtered: dict[PurePosixPath, list[SourceFile]]
    ) -> dict[PurePosixPath, list[SourceFile]]:
        """Group candidates by their final package destinations."""
        return filtered

    def _select(
        self,
        group: list[SourceFile],
        destination: PurePosixPath,
    ) -> None:
        """Update the included and excluded lists for one destination."""
        selected, *rejected = group
        self.included.append(PackageFile(selected, destination))
        self.excluded.extend(rejected)
