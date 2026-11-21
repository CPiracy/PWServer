import sys
from pathlib import Path
from typing import Annotated

import typer

from src.libs.config.config_builder import ConfigBuilder

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
) -> None:
    """Create a package build configuration."""
    builder = ConfigBuilder(sources, batch=batch)
    result = builder.build()

    if not (include or exclude):
        result.save(output)
        return

    if include:
        typer.echo(f"Included files ({len(builder.included)})")
        for file in builder.included:
            typer.echo(f"  {file.path} -> {file.destination}")

    if exclude:
        typer.echo(f"Excluded files ({len(builder.excluded)})")
        for file in builder.excluded:
            typer.echo(f"  {file.path}")


@app.callback()
def main() -> None:
    """Prepare Perfect World server and game data files for Debian packaging."""


if __name__ == "__main__":
    app(prog_name=sys.argv[0])
