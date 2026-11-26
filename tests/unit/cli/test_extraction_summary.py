"""CLI reports row loss with a locator and reason."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from application.services import ConsolidationResult, ProcessingResult
from cli.main import cli
from domain.models import ExtractionResult, PaymentMethod, Statement
from domain.validation import ValidationResult


def test_process_prints_extraction_summary(tmp_path: Path) -> None:
    input_path = tmp_path / "synthetic.csv"
    input_path.write_text("synthetic data")
    report = ExtractionResult("a" * 64)
    report.retain()
    report.discard("row:3", "Invalid date")
    statement = Statement(PaymentMethod.BBVA_VISA, extraction=report)
    result = ProcessingResult(
        input_path,
        tmp_path / "output.xlsx",
        statement,
        ValidationResult(is_valid=True, errors=[]),
        True,
        extraction=report,
    )
    service = Mock()
    service.process_statement.return_value = result
    config = Mock()
    config.output_directory = tmp_path

    with patch("cli.main.create_components", return_value=(service, Mock())):
        command = CliRunner().invoke(
            cli, ["process", str(input_path)], obj={"config": config}
        )

    assert command.exit_code == 0
    assert "2 read, 1 retained, 1 discarded" in command.output
    assert "row:3: Invalid date" in command.output


def test_failed_process_still_prints_extraction_summary(tmp_path: Path) -> None:
    input_path = tmp_path / "synthetic.csv"
    input_path.write_text("synthetic data")
    report = ExtractionResult("a" * 64)
    report.discard("row:2", "Invalid date")
    statement = Statement(PaymentMethod.BBVA_VISA, extraction=report)
    result = ProcessingResult(
        input_path,
        None,
        statement,
        ValidationResult(is_valid=False, errors=["Invalid statement"]),
        False,
        errors=["Invalid statement"],
        extraction=report,
    )
    service = Mock()
    service.process_statement.return_value = result
    config = Mock()
    config.output_directory = tmp_path

    with patch("cli.main.create_components", return_value=(service, Mock())):
        command = CliRunner().invoke(
            cli, ["process", str(input_path)], obj={"config": config}
        )

    assert command.exit_code == 1
    assert "row:2: Invalid date" in command.output


def test_consolidate_prints_failed_file_diagnostics(tmp_path: Path) -> None:
    file_path = tmp_path / "synthetic.csv"
    file_path.write_text("synthetic data")
    report = ExtractionResult("a" * 64)
    report.discard("row:2", "Invalid date")
    service = Mock()
    service.consolidate_statements.return_value = ConsolidationResult(
        input_directory=tmp_path,
        output_path=None,
        consolidated_statement=None,
        failed_files=[{"file": str(file_path), "errors": ["No valid statements"]}],
        extractions={str(file_path): report},
    )
    config = Mock()
    config.output_directory = tmp_path

    with patch("cli.main.create_components", return_value=(service, Mock())):
        command = CliRunner().invoke(
            cli, ["consolidate", str(tmp_path)], obj={"config": config}
        )

    assert command.exit_code == 1
    assert "row:2: Invalid date" in command.output
