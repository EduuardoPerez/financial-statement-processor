"""Extraction accounting remains visible through application results."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from application.services import StatementProcessingService
from domain.builders import TransactionBuilder
from domain.models import (
    Currency,
    ExtractionResult,
    PaymentMethod,
    SourceProvenance,
    Statement,
    Transaction,
)
from domain.services import DuplicateDetector
from domain.utils import AmountParser, DateConverter
from domain.validation import ValidationResult
from infrastructure.parsers.csv_parser import CSVStatementParser


def test_duplicate_marker_preserves_source_provenance() -> None:
    provenance = SourceProvenance("a" * 64, "row:2", "01/02/2025", "3.00", "Shop")
    transaction = Transaction(
        date(2025, 2, 1),
        "Shop",
        Decimal("3.00"),
        Currency.ARS,
        PaymentMethod.BBVA_VISA,
        provenance=provenance,
    )
    other = Transaction(
        date(2025, 2, 1),
        "Shop",
        Decimal("3.00"),
        Currency.ARS,
        PaymentMethod.BBVA_VISA,
        provenance=SourceProvenance("b" * 64, "row:3", "01/02/2025", "3.00", "Shop"),
    )

    marked, count = DuplicateDetector().mark_duplicates([transaction, other])

    assert count == 1
    assert len(marked) == 2
    assert marked[1].description.startswith("DUPLICATED:")
    assert marked[1].provenance == other.provenance
    assert hash(marked[1])


def test_processing_result_exposes_file_extraction(tmp_path: Path) -> None:
    statement = Statement(PaymentMethod.BBVA_VISA)
    statement.add_transaction(
        Transaction(
            date(2025, 2, 1),
            "Shop",
            Decimal("3.00"),
            Currency.ARS,
            PaymentMethod.BBVA_VISA,
        )
    )
    statement.extraction = ExtractionResult("a" * 64)
    statement.extraction.retain()
    statement.extraction.discard("row:3", "Invalid date")
    parser = Mock()
    parser.parse.return_value = statement
    parser.parse_with_content.return_value = (statement, "content")
    factory = Mock()
    factory.create_parser.return_value = parser
    repository = Mock()
    validator = Mock()
    validator.validate.return_value = ValidationResult(is_valid=True, errors=[])
    validator.validate_with_content.return_value = ValidationResult(
        is_valid=True, errors=[]
    )
    filenames = Mock()
    filenames.generate.return_value = "statement.xlsx"
    config = Mock(enable_validation=True, retry_attempts=0)
    service = StatementProcessingService(
        factory, repository, validator, filenames, config
    )

    result = service.process_statement(tmp_path / "input.csv", tmp_path)

    assert result.success
    assert result.extraction is statement.extraction
    assert result.extraction.rows_discarded == 1


def test_consolidation_keeps_overlap_observations_and_file_counts(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    third = tmp_path / "third.csv"
    header = "Fecha;Establecimiento;Moneda;Importe\n"
    row = "01/02/2025;Shop;Pesos;3.00\n"
    first.write_text(header + row, encoding="utf-8")
    second.write_text(header + row + "bad;Other;Pesos;4.00\n", encoding="utf-8")
    third.write_text(header + "bad;Other;Pesos;4.00\n", encoding="utf-8")

    class Detector:
        def detect_from_filename(self, path: Path) -> PaymentMethod:
            return PaymentMethod.BBVA_VISA

    parser = CSVStatementParser(
        Detector(), TransactionBuilder(DateConverter(), AmountParser())
    )
    factory = Mock()
    factory.get_supported_extensions.return_value = {".csv"}
    factory.create_parser.return_value = parser
    repository = Mock()
    validator = Mock()
    validator.validate_with_content.side_effect = lambda statement, _: ValidationResult(
        is_valid=bool(statement.transactions),
        errors=[] if statement.transactions else ["No valid transactions"],
    )
    filenames = Mock()
    filenames.generate.return_value = "individual.xlsx"
    filenames.generate_consolidated.return_value = "combined.xlsx"
    config = Mock(enable_validation=True, retry_attempts=0, max_workers=2)
    service = StatementProcessingService(
        factory, repository, validator, filenames, config
    )

    result = service.consolidate_statements(tmp_path, tmp_path)

    assert result.success
    assert result.total_transactions == 2
    assert len(result.extractions) == 3
    assert len(result.failed_files) == 1
    assert result.extractions[str(third)].rows_discarded == 1
    assert result.extractions[str(second)].rows_discarded == 1
    assert result.extractions[str(first)].rows_emitted == 1
    provenances = [t.provenance for t in result.consolidated_statement.transactions]
    assert all(provenances)
    assert provenances[0].file_sha256 != provenances[1].file_sha256
