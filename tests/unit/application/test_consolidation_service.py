"""
Unit tests for StatementProcessingService consolidation features.

This module tests the consolidation functionality of StatementProcessingService.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from application.services import StatementProcessingService
from domain.factories import ParserFactory
from domain.filename import FilenameGenerator
from domain.models import PaymentMethod, Statement
from domain.repositories import StatementRepository
from domain.validation import StatementValidator
from infrastructure.config import ProcessingConfig


class TestStatementProcessingServiceConsolidation:
    """Test consolidation features of StatementProcessingService"""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for StatementProcessingService"""
        return {
            "parser_factory": Mock(spec=ParserFactory),
            "repository": Mock(spec=StatementRepository),
            "validator": Mock(spec=StatementValidator),
            "filename_generator": Mock(spec=FilenameGenerator),
            "processing_config": ProcessingConfig(),
            "balance_extraction_service": Mock(),
        }

    @pytest.fixture
    def sample_statement(self):
        """Create a sample statement for testing"""
        return Statement(
            payment_method=PaymentMethod.BBVA_VISA,
            transactions=[],
        )

    def test_consolidate_statements_no_files_found(self, mock_dependencies):
        """Test consolidation when no supported files are found"""
        service = StatementProcessingService(**mock_dependencies)
        input_dir = Path("empty_dir")
        output_dir = Path("output")

        # Mock that no files are found
        mock_dependencies["parser_factory"].get_supported_extensions.return_value = [
            ".pdf",
            ".csv",
        ]

        with patch.object(Path, "glob", return_value=[]):
            result = service.consolidate_statements(input_dir, output_dir)

        assert result.success is False
        assert result.output_path is None
        assert result.consolidated_statement is None
        assert "No supported files found in directory" in result.errors

    def test_discover_statement_files(self, mock_dependencies):
        """Test _discover_statement_files method"""
        service = StatementProcessingService(**mock_dependencies)
        input_dir = Path("test_dir")

        mock_dependencies["parser_factory"].get_supported_extensions.return_value = [
            ".pdf",
            ".csv",
        ]

        with patch.object(Path, "glob") as mock_glob:
            mock_glob.side_effect = [
                [Path("file1.pdf")],  # *.pdf
                [Path("file3.PDF")],  # *.PDF
                [Path("file2.csv")],  # *.csv
                [],  # *.CSV
            ]

            files = service._discover_statement_files(input_dir)

        # Should find unique files and sort them
        assert len(files) == 3
        assert Path("file1.pdf") in files
        assert Path("file2.csv") in files
        assert Path("file3.PDF") in files

    def test_process_individual_file_success(self, mock_dependencies, sample_statement):
        """Test _process_individual_file with successful processing"""
        service = StatementProcessingService(**mock_dependencies)
        file_path = Path("test.pdf")

        # Mock successful process_statement
        with patch.object(service, "process_statement") as mock_process:
            mock_result = Mock()
            mock_result.success = True
            mock_result.statement = sample_statement
            mock_result.errors = []
            mock_process.return_value = mock_result

            statement, errors = service._process_individual_file(file_path)

        assert statement == sample_statement
        assert errors == []

    def test_process_individual_file_failure(self, mock_dependencies):
        """Test _process_individual_file with failed processing"""
        service = StatementProcessingService(**mock_dependencies)
        file_path = Path("test.pdf")

        # Mock failed process_statement
        with patch.object(service, "process_statement") as mock_process:
            mock_result = Mock()
            mock_result.success = False
            mock_result.statement = None
            mock_result.errors = ["Parse error"]
            mock_process.return_value = mock_result

            statement, errors = service._process_individual_file(file_path)

        assert statement is None
        assert errors == ["Parse error"]

    def test_process_individual_file_exception(self, mock_dependencies):
        """Test _process_individual_file with exception"""
        service = StatementProcessingService(**mock_dependencies)
        file_path = Path("test.pdf")

        # Mock exception in process_statement
        with patch.object(service, "process_statement") as mock_process:
            mock_process.side_effect = Exception("Unexpected error")

            statement, errors = service._process_individual_file(file_path)

        assert statement is None
        assert errors == ["Unexpected error"]

    def test_collect_all_transactions(self, mock_dependencies):
        """Test _collect_all_transactions method"""
        service = StatementProcessingService(**mock_dependencies)

        # Create statements with mock transactions
        statements = [Mock(), Mock()]
        statements[0].transactions = ["tx1", "tx2"]
        statements[1].transactions = ["tx3", "tx4", "tx5"]

        transactions = service._collect_all_transactions(statements)

        assert transactions == ["tx1", "tx2", "tx3", "tx4", "tx5"]

    def test_sort_transactions_chronologically(self, mock_dependencies):
        """Test _sort_transactions_chronologically method"""
        service = StatementProcessingService(**mock_dependencies)

        # Create mock transactions with dates
        from datetime import date

        tx1 = Mock()
        tx1.date = date(2025, 1, 15)
        tx2 = Mock()
        tx2.date = date(2025, 1, 10)
        tx3 = Mock()
        tx3.date = date(2025, 1, 20)

        transactions = [tx1, tx2, tx3]
        sorted_transactions = service._sort_transactions_chronologically(transactions)

        # Should be sorted by date ascending
        assert sorted_transactions == [tx2, tx1, tx3]

    def test_consolidate_statements_no_valid_statements(self, mock_dependencies):
        """Test consolidation when no valid statements can be processed"""
        service = StatementProcessingService(**mock_dependencies)
        input_dir = Path("test_dir")
        output_dir = Path("output")

        mock_dependencies["parser_factory"].get_supported_extensions.return_value = [
            ".pdf"
        ]

        with patch.object(Path, "glob", return_value=[Path("file1.pdf")]):
            with patch.object(service, "_process_individual_file") as mock_process:
                mock_process.return_value = (None, ["Parse error"])

                result = service.consolidate_statements(input_dir, output_dir)

        assert result.success is False
        assert result.output_path is None
        assert result.consolidated_statement is None
        assert len(result.failed_files) == 1
        assert "No valid statements could be processed" in result.errors

    def test_consolidate_statements_save_failure(
        self, mock_dependencies, sample_statement
    ):
        """Test consolidation when saving fails"""
        service = StatementProcessingService(**mock_dependencies)
        input_dir = Path("test_dir")
        output_dir = Path("output")

        mock_dependencies["parser_factory"].get_supported_extensions.return_value = [
            ".pdf"
        ]
        mock_dependencies[
            "filename_generator"
        ].generate_consolidated.return_value = "consolidated.xlsx"

        with patch.object(Path, "glob", return_value=[Path("file1.pdf")]):
            with patch.object(service, "_process_individual_file") as mock_process:
                mock_process.return_value = (sample_statement, [])

                with patch("domain.services.DuplicateDetector") as mock_detector_class:
                    mock_detector = Mock()
                    mock_detector.mark_duplicates.return_value = ([], 0)
                    mock_detector_class.return_value = mock_detector

                    # Mock save failure
                    mock_dependencies[
                        "repository"
                    ].save_statement.side_effect = Exception("Save failed")

                    result = service.consolidate_statements(input_dir, output_dir)

        assert result.success is False
        assert result.output_path is None
        assert "Failed to save consolidated file" in result.errors[0]
