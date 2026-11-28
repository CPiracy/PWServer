import re
from collections import defaultdict
from pathlib import Path, PurePath, PurePosixPath

import questionary

from ..source.package_file import PackageFile
from ..source.source_factory import SourceFactory
from ..source.source_file import SourceFile
from .config import Config


class ConfigBuilder:
    """Build a package configuration from ordered input sources."""

    _PW_EXTENSIONS = (
        "bht",
        "clt",
        "conf",
        "dat",
        "data",
        "dhmap",
        "hmap",
        "lua",
        "nmd",
        "octr",
        "rmap",
        "sev",
        "so",
        "sql",
        "txt",
        "wmap",
        "xml",
    )
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
    _PW_FILTER_LAYERS = (
        {
            "rule": re.compile(rf".*\.({'|'.join(_PW_EXTENSIONS)})"),
            "exceptions": (re.compile(r"(.*/)?[^/.]+"),),
        },
        {
            "rule": re.compile(r"[\N{NULL}-\N{DELETE}]+"),
            "exceptions": (),
        },
        {
            "rule": re.compile(r"(?!(.*/)?(dbhome|backup)/).*"),
            "exceptions": (),
        },
        {
            "rule": re.compile(r"(?!.*(report|log\.txt)$).*"),
            "exceptions": (),
        },
        {
            "rule": re.compile(r"(?!.*\.txt$).*"),
            "exceptions": (re.compile(r"(.*/)?gdeliveryd/.*\.txt"),),
        },
        {
            "rule": re.compile(r"(?!.*\.xml$).*"),
            "exceptions": (re.compile(r"(.*/)?gacd/gacd\.xml"),),
        },
        {
            "rule": re.compile(r"(?!(.*/)?gamed/config/.+/[^/.]+$).*"),
            "exceptions": (),
        },
        {
            "rule": re.compile(r"(?!(.*/)?gamed/config/.+/.*\.(data|sev)$).*"),
            "exceptions": (
                re.compile(r"(.*/)?gamed/config/.+/npcgen[^/]*\.data"),
                re.compile(
                    r"(.*/)?gamed/config/.+/(precinct|region|path|map_desp)\.sev"
                ),
            ),
        },
    )
    _PW_DESTINATION_REGEX = (
        re.compile(rf"(.*/)?(?P<path>({'|'.join(_PW_DIRECTORIES)})/.+)"),
        re.compile(rf"(.*/)?(?P<path>{'|'.join(_PW_FILES)})"),
    )
    _PW_GROUP_REGEX = re.compile(
        r"(?P<prefix>(.*/)?[A-Za-z]+)[^A-Za-z/.][^/.]*(?P<suffix>|\.data|\.conf)"
    )
    _PW_GROUP_EXCEPTIONS = (
        re.compile(r"gamed/config/.+/npcgen_\d+\.data"),
        re.compile(r"gamed/config/gshop\d+\.data"),
        re.compile(r"gamed/config/domain2(_cross)?\.data"),
        re.compile(r"gdeliveryd/domain\d+\.data"),
    )

    def __init__(
        self, paths: list[Path], *, batch: bool = False, sha256: bool = False
    ) -> None:
        self._paths = tuple(paths)
        self._batch = batch
        self._sha256 = sha256
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
        for group in grouped.values():
            self._select(group)
        return Config(self.included)

    def _filter(self, path: PurePath) -> PurePosixPath | None:
        """Return an allowed server path, or None."""
        posix = path.as_posix()
        for layer in self._PW_FILTER_LAYERS:
            if not layer["rule"].fullmatch(posix) and not any(
                exception.fullmatch(posix) for exception in layer["exceptions"]
            ):
                return None

        for regex in self._PW_DESTINATION_REGEX:
            match = regex.fullmatch(posix)
            if match:
                return PurePosixPath(match["path"])
        return None

    def _group(
        self, filtered: dict[PurePosixPath, list[SourceFile]]
    ) -> dict[PurePosixPath, list[PackageFile]]:
        """Group candidates while retaining each original destination."""
        grouped: dict[PurePosixPath, list[PackageFile]] = defaultdict(list)
        for destination, files in filtered.items():
            key = destination
            posix = destination.as_posix()
            match = self._PW_GROUP_REGEX.fullmatch(posix)
            if match and not any(
                regex.fullmatch(posix) for regex in self._PW_GROUP_EXCEPTIONS
            ):
                key = PurePosixPath(match["prefix"] + match["suffix"])
            grouped[key].extend(PackageFile(file, destination) for file in files)
        return grouped

    def _label(self, group: list[PackageFile]) -> dict[PackageFile, str]:
        """Return menu labels for the package candidates."""
        labels: dict[PackageFile, str] = {}
        sizes: dict[int, PackageFile] = {}
        hashes: dict[int, dict[str, PackageFile]] = {}

        for file in group:
            name = file.path.name
            target = file.resolve()
            if target is not file:
                labels[file] = f"{name} (link to {target.path.name})"
                continue

            size = file.size
            reference = sizes.setdefault(size, file)
            if reference is file:
                labels[file] = name
                continue

            labels[file] = f"{name} (size of {reference.path.name})"
            if not self._sha256:
                continue

            if size not in hashes:
                hashes[size] = {reference.sha256: reference}

            copy = hashes[size].setdefault(file.sha256, file)
            if copy is not file:
                labels[file] = f"{name} (same as {copy.path.name})"

        return labels

    def _select(self, group: list[PackageFile]) -> None:
        """Select a package file and exclude the other candidates."""
        group.sort(key=lambda file: len(file.destination.name))
        selected = group[0]
        destination = selected.destination

        if len(group) > 1 and not self._batch:
            labels = self._label(group)
            selected = questionary.select(
                f"Choose a file for {destination}:",
                choices=[
                    questionary.Choice(
                        labels[file],
                        value=file,
                        description=file.source.path,
                    )
                    for file in group
                ],
                pointer=None,
                style=questionary.Style([("highlighted", "reverse")]),
            ).unsafe_ask()

        self.included.append(PackageFile(selected.source_file, destination))
        self.excluded.extend(file.source_file for file in group if file is not selected)
