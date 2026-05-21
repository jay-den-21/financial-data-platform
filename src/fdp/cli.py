import typer

app = typer.Typer(help="Financial data platform command line interface.")


@app.callback()
def main() -> None:
    """Project CLI entrypoint."""

