"""
Unit tests for CSVStatementParser infrastructure component.

Covers CSV data loading, including encoding handling for Argentine bank
exports that ship in Latin-1 instead of UTF-8.
"""

from unittest.mock import Mock

import pytest

from domain.builders import TransactionBuilder
from infrastructure.parsers.csv_parser import CSVStatementParser

_BBVA_VISA_CSV_CONTENT = (
    "Numero Tarjeta;Fecha Origen;Establecimiento;Numero Comprobante;Moneda;Importe\n"
    "XXXX XXXX XXXX 0000;02/07/2026;COMISIÓN BLACK;0000000;Pesos;65,206.61\n"
    "XXXX XXXX XXXX 7968;02/07/2026;UALA   *DURHAM;0000348;Pesos;175,490\n"
)


class TestCSVStatementParserLoading:
    """Unit tests for CSVStatementParser._load_csv_data"""

    @pytest.fixture
    def csv_parser(self):
        """Create CSVStatementParser instance with mocked dependencies"""
        detector = Mock()
        transaction_builder = Mock(spec=TransactionBuilder)
        return CSVStatementParser(detector, transaction_builder)

    def test_load_csv_data_latin1_encoding(self, csv_parser, tmp_path):
        """CSV files exported in Latin-1 (ISO-8859-1) must load correctly.

        Regression: BBVA exports 'Movimientos' CSVs in Latin-1. Rows with
        accented characters (e.g. 'COMISIÓN BLACK') contain bytes like 0xD3
        that are invalid UTF-8, so loading with the default encoding fails
        and the whole file is rejected.
        """
        # Arrange
        csv_file = tmp_path / "BBVA-VISA-Movimientos.csv"
        csv_file.write_bytes(_BBVA_VISA_CSV_CONTENT.encode("latin-1"))

        # Act
        df = csv_parser._load_csv_data(csv_file)

        # Assert
        assert len(df) == 2
        assert df["Establecimiento"].iloc[0] == "COMISIÓN BLACK"

    def test_load_csv_data_utf8_encoding(self, csv_parser, tmp_path):
        """CSV files in UTF-8 must keep loading correctly."""
        # Arrange
        csv_file = tmp_path / "BBVA-VISA-Movimientos.csv"
        csv_file.write_bytes(_BBVA_VISA_CSV_CONTENT.encode("utf-8"))

        # Act
        df = csv_parser._load_csv_data(csv_file)

        # Assert
        assert len(df) == 2
        assert df["Establecimiento"].iloc[0] == "COMISIÓN BLACK"

    def test_load_csv_data_empty_file_raises(self, csv_parser, tmp_path):
        """Empty CSV files must still raise a ValueError."""
        # Arrange
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text(
            "Numero Tarjeta;Fecha Origen;Establecimiento;"
            "Numero Comprobante;Moneda;Importe\n"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="No data found in CSV file"):
            csv_parser._load_csv_data(csv_file)
