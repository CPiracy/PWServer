from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path, PurePath, PurePosixPath

from ..sources.source_factory import SourceFactory
from ..sources.source_file import SourceFile
from .package_file import PackageFile


class Config:
    """The selected files and their destinations in the package."""

    def __init__(self, files: list[PackageFile]) -> None:
        self.files = files

    def save(self, path: Path) -> None:
        """Save the package destinations grouped by source path."""
        sources: defaultdict[str, dict[str, str]] = defaultdict(dict)
        for file in self.files:
            sources[str(file.source.path)][str(file.path)] = str(file.destination)
        path.write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Config:
        """Load the selected file paths and their package destinations."""
        sources = json.loads(path.read_text(encoding="utf-8"))
        source_factory = SourceFactory()
        files = []
        for source_path, entries in sources.items():
            source = source_factory.create(Path(source_path))
            for entry_path, destination in entries.items():
                entry = PurePath(entry_path)
                source_file = source.get_file(entry) or SourceFile(source, entry)
                files.append(PackageFile(source_file, PurePosixPath(destination)))
        return cls(files)

    def filter(self, func: Callable[[PackageFile], bool]) -> Config:
        """Return a config with the matching package files in order."""
        return Config([file for file in self.files if func(file)])
