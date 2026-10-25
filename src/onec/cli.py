import typer

from onec import __version__

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """Описание конфигураций 1С:Предприятие на Python."""


@app.command()
def version() -> None:
    """Выводит версию библиотеки"""
    typer.echo(__version__)
