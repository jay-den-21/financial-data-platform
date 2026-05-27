from typer.testing import CliRunner

from fdp.cli import app


def test_cli_registers_instrument_ingest_command() -> None:
    result = CliRunner().invoke(app, ["ingest", "instruments", "--help"])

    assert result.exit_code == 0
    assert "--market" in result.output
    assert "--source" in result.output

