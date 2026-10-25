from typer.testing import CliRunner

from onec import __version__
from onec.cli import app


def test_version() -> None:
    result = CliRunner().invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__
