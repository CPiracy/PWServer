import sys
from pathlib import Path
from typing import Annotated

import typer

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
    typer.echo("Configuration generation is not implemented yet.", err=True)
    raise typer.Exit(code=1)


@app.callback()
def main() -> None:
    """Prepare Perfect World server and game data files for Debian packaging."""


if __name__ == "__main__":
    app(prog_name=sys.argv[0])
