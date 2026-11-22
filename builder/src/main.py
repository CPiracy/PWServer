import sys
from itertools import groupby
from pathlib import Path
from typing import Annotated

import typer

from src.libs.config.config_builder import ConfigBuilder
from src.libs.config.package_file import PackageFile
from src.libs.sources.source_file import SourceFile

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    options_metavar="",
)


@app.command(options_metavar="")
def config(
    sources: Annotated[
        list[Path],
        typer.Argument(help="Directories, ZIP/7z/TAR archives, or VMDK disk images."),
    ],
    output: Annotated[
        Path, typer.Option("--output", help="Output configuration file.")
    ] = Path("config.json"),
    batch: Annotated[
        bool, typer.Option("--batch", help="Non-interactive mode without prompting.")
    ] = False,
    include: Annotated[
        bool, typer.Option("--include", help="Show included files.")
    ] = False,
    exclude: Annotated[
        bool, typer.Option("--exclude", help="Show excluded files.")
    ] = False,
    color: Annotated[
        bool,
        typer.Option("--color", help="Force colorizing when output is redirected."),
    ] = False,
) -> None:
    """Create a package build configuration."""
    builder = ConfigBuilder(sources, batch=batch)
    result = builder.build()

    if not (include or exclude):
        result.save(output)
        return

    files: list[SourceFile] = []
    if include:
        files.extend(builder.included)
    if exclude:
        files.extend(builder.excluded)

    files.sort(key=lambda file: (file.source.path, str(file.path)))
    for source, group in groupby(files, key=lambda file: file.source.path):
        typer.echo(source)
        for file in group:
            if isinstance(file, PackageFile):
                path = typer.style(file.path, fg=typer.colors.GREEN)
                line = f"{path} -> {file.destination}"
            else:
                line = typer.style(file.path, fg=typer.colors.RED)
            typer.echo(f"  {line}", color=color or None)


@app.callback()
def main() -> None:
    """Prepare Perfect World server and game data files for Debian packaging."""


if __name__ == "__main__":
    app(prog_name=sys.argv[0])
