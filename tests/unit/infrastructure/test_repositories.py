"""
Unit tests for infrastructure repository implementations.

This module tests the ExcelStatementRepository implementation.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from domain.models import (
    ConsolidatedStatement,
    Currency,
    PaymentMethod,
    Statement,
    Transaction,
)
from domain.repositories import FileReader, FileWriter
from infrastructure.repositories import ExcelStatementRepository


class TestExcelStatementRepository:
    """Test ExcelStatementRepository functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for repository."""
        return {
            "file_reader": Mock(spec=FileReader),
            "file_writer": Mock(spec=FileWriter),
        }

    @pytest.fixture
    def sample_statement(self):
        """Create a sample statement for testing."""
        transactions = [
            Transaction(
                date=date(2025, 1, 15),
                description="Test Transaction 1",
                amount=Decimal("100.50"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 1, 10),
                description="Test Transaction 2",
                amount=Decimal("250.75"),
                currency=Currency.USD,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
        ]
        return Statement(
            payment_method=PaymentMethod.BBVA_VISA,
            transactions=transactions,
        )

    def test_save_statement_success(self, mock_dependencies, sample_statement):
        """Test successful statement saving."""
        repository = ExcelStatementRepository(**mock_dependencies)
        output_path = Path("output/test_statement.xlsx")

        with patch("pandas.DataFrame.to_excel") as mock_to_excel:
            repository.save_statement(sample_statement, output_path)

            mock_dependencies["file_writer"].ensure_directory.assert_called_once_with(
                output_path.parent
            )
            mock_to_excel.assert_called_once_with(
                output_path, index=False, sheet_name="Sheet1", engine="openpyxl"
            )

    def test_save_statement_no_transactions_error(self, mock_dependencies):
        """Test saving statement with no transactions raises ValueError."""
        repository = ExcelStatementRepository(**mock_dependencies)
        empty_statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA,
            transactions=[],
        )
        output_path = Path("output/test.xlsx")

        with pytest.raises(
            ValueError, match="Cannot save statement with no transactions"
        ):
            repository.save_statement(empty_statement, output_path)

    def test_save_statement_excel_write_error(
        self, mock_dependencies, sample_statement
    ):
        """Test handling Excel write errors."""
        repository = ExcelStatementRepository(**mock_dependencies)
        output_path = Path("output/test_statement.xlsx")

        with patch("pandas.DataFrame.to_excel") as mock_to_excel:
            mock_to_excel.side_effect = Exception("Permission denied")

            with pytest.raises(OSError, match="Failed to save Excel file"):
                repository.save_statement(sample_statement, output_path)

    def test_load_raw_data_success(self, mock_dependencies):
        """Test successful raw data loading."""
        repository = ExcelStatementRepository(**mock_dependencies)
        input_path = Path("input/test.pdf")
        expected_data = b"mock file content"

        mock_dependencies["file_reader"].exists.return_value = True
        mock_dependencies["file_reader"].read.return_value = expected_data

        result = repository.load_raw_data(input_path)

        assert result == expected_data
        mock_dependencies["file_reader"].exists.assert_called_once_with(input_path)
        mock_dependencies["file_reader"].read.assert_called_once_with(input_path)

    def test_load_raw_data_file_not_found(self, mock_dependencies):
        """Test loading raw data when file doesn't exist."""
        repository = ExcelStatementRepository(**mock_dependencies)
        input_path = Path("nonexistent/file.pdf")

        mock_dependencies["file_reader"].exists.return_value = False

        with pytest.raises(FileNotFoundError, match="Input file not found"):
            repository.load_raw_data(input_path)

    def test_load_raw_data_permission_error(self, mock_dependencies):
        """Test loading raw data with permission error."""
        repository = ExcelStatementRepository(**mock_dependencies)
        input_path = Path("input/restricted.pdf")

        mock_dependencies["file_reader"].exists.return_value = True
        mock_dependencies["file_reader"].read.side_effect = PermissionError(
            "Access denied"
        )

        with pytest.raises(PermissionError, match="Permission denied reading"):
            repository.load_raw_data(input_path)

    def test_load_raw_data_generic_error(self, mock_dependencies):
        """Test loading raw data with generic error."""
        repository = ExcelStatementRepository(**mock_dependencies)
        input_path = Path("input/corrupted.pdf")

        mock_dependencies["file_reader"].exists.return_value = True
        mock_dependencies["file_reader"].read.side_effect = Exception("Disk error")

        with pytest.raises(OSError, match="Error reading file"):
            repository.load_raw_data(input_path)

    def test_statement_to_dataframe(self, mock_dependencies, sample_statement):
        """Test conversion of statement to DataFrame."""
        repository = ExcelStatementRepository(**mock_dependencies)

        df = repository._transactions_to_dataframe(sample_statement.transactions)

        assert len(df) == 2
        assert list(df.columns) == [
            "Date",
            "Description",
            "Currency",
            "Amount",
            "Payment Method",
        ]
        assert df.iloc[0]["Date"] == "2025-01-15"
        assert df.iloc[0]["Description"] == "Test Transaction 1"
        assert df.iloc[0]["Currency"] == "ARS"
        assert df.iloc[0]["Amount"] == "100,5"
        assert df.iloc[0]["Payment Method"] == "BBVA Visa"

    def test_save_consolidated_statement_success(
        self, mock_dependencies, sample_statement
    ):
        """Test successful consolidated statement saving."""
        repository = ExcelStatementRepository(**mock_dependencies)
        output_path = Path("output/consolidated.xlsx")

        consolidated = ConsolidatedStatement(
            transactions=sample_statement.transactions,
            source_statements=[sample_statement],
            duplicate_count=0,
        )

        with patch("pandas.DataFrame.to_excel") as mock_to_excel:
            repository.save_consolidated_statement(consolidated, output_path)

            mock_dependencies["file_writer"].ensure_directory.assert_called_once_with(
                output_path.parent
            )
            mock_to_excel.assert_called_once_with(
                output_path, index=False, sheet_name="Sheet1", engine="openpyxl"
            )

    def test_save_consolidated_statement_no_transactions_error(self, mock_dependencies):
        """Test saving consolidated statement with no transactions."""
        repository = ExcelStatementRepository(**mock_dependencies)
        output_path = Path("output/consolidated.xlsx")

        consolidated = ConsolidatedStatement(
            transactions=[],
            source_statements=[],
            duplicate_count=0,
        )

        with pytest.raises(
            ValueError, match="Cannot save consolidated statement with no transactions"
        ):
            repository.save_consolidated_statement(consolidated, output_path)

    def test_save_consolidated_statement_excel_write_error(
        self, mock_dependencies, sample_statement
    ):
        """Test handling Excel write errors for consolidated statements."""
        repository = ExcelStatementRepository(**mock_dependencies)
        output_path = Path("output/consolidated.xlsx")

        consolidated = ConsolidatedStatement(
            transactions=sample_statement.transactions,
            source_statements=[sample_statement],
            duplicate_count=0,
        )

        with patch("pandas.DataFrame.to_excel") as mock_to_excel:
            mock_to_excel.side_effect = Exception("Disk full")

            with pytest.raises(OSError, match="Failed to save consolidated Excel file"):
                repository.save_consolidated_statement(consolidated, output_path)

    def test_consolidated_to_dataframe(self, mock_dependencies, sample_statement):
        """Test conversion of consolidated statement to DataFrame."""
        repository = ExcelStatementRepository(**mock_dependencies)

        consolidated = ConsolidatedStatement(
            transactions=sample_statement.transactions,
            source_statements=[sample_statement],
            duplicate_count=0,
        )

        df = repository._transactions_to_dataframe(consolidated.transactions)

        assert len(df) == 2
        assert list(df.columns) == [
            "Date",
            "Description",
            "Currency",
            "Amount",
            "Payment Method",
        ]
        assert df.iloc[0]["Date"] == "2025-01-15"
        assert df.iloc[1]["Date"] == "2025-01-10"
