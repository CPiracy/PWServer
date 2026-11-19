import sys

import typer

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    options_metavar="",
)


@app.callback()
def main() -> None:
    """Prepare Perfect World server and game data files for Debian packaging."""


if __name__ == "__main__":
    app(prog_name=sys.argv[0])
