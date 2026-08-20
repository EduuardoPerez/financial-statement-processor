"""
Unit tests for StatementProcessingService.

This module contains comprehensive unit tests for the application layer
StatementProcessingService, focusing on mocking dependencies and validating
ProcessingResult objects according to Prompt 18 requirements.
"""

import time
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

import pytest

from application.services import StatementProcessingService
from domain.factories import ParserFactory
from domain.filename import FilenameGenerator
from domain.models import Currency, PaymentMethod, Statement, Transaction
from domain.repositories import StatementRepository
from domain.services import StatementParser
from domain.validation import StatementValidator, ValidationResult
from infrastructure.config import ProcessingConfig


class TestStatementProcessingService:
    """Unit tests for StatementProcessingService"""

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
        """Create a sample statement with transactions for testing"""
        transactions = [
            Transaction(
                date=date(2025, 6, 22),
                description="Test Transaction 1",
                amount=Decimal("100.50"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 21),
                description="Test Transaction 2",
                amount=Decimal("250.75"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 20),
                description="Test Transaction 3",
                amount=Decimal("75.25"),
                currency=Currency.USD,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
        ]

        return Statement(
            payment_method=PaymentMethod.BBVA_VISA,
            transactions=transactions,
        )

    def test_process_statement_success(self, mock_dependencies, sample_statement):
        """Test successful statement processing workflow"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("test_statement.pdf")
        output_dir = Path("output")
        expected_output_path = output_dir / "BBVA-VISA_20250622.xlsx"

        # Configure mocks
        mock_parser = Mock(spec=StatementParser)
        mock_validation_result = ValidationResult(is_valid=True, errors=[])

        mock_dependencies["parser_factory"].create_parser.return_value = mock_parser
        mock_parser.parse.return_value = sample_statement
        # Set up parse_with_content to return tuple (statement, content)
        mock_parser.parse_with_content.return_value = (sample_statement, "mock content")
        mock_dependencies["validator"].validate.return_value = mock_validation_result
        mock_dependencies[
            "validator"
        ].validate_with_content.return_value = mock_validation_result
        mock_dependencies[
            "filename_generator"
        ].generate.return_value = "BBVA-VISA_20250622.xlsx"

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert - Prompt 18 Requirements
        assert result.success is True
        assert result.statement is not None
        assert len(result.statement.transactions) > 0  # Requirement: transactions > 0
        assert result.output_path is not None
        assert result.output_path.suffix == ".xlsx"  # Requirement: .suffix == ".xlsx"

        # Additional assertions
        assert result.input_path == input_path
        assert result.output_path == expected_output_path
        assert result.statement == sample_statement
        assert result.validation_result == mock_validation_result
        assert len(result.errors) == 0
        assert result.processing_time > 0.0

        # Verify dependency interactions
        mock_dependencies["parser_factory"].create_parser.assert_called_once_with(
            input_path
        )
        # Enhanced parsing path uses parse_with_content instead of parse
        mock_parser.parse_with_content.assert_called_once_with(input_path)
        mock_dependencies["validator"].validate_with_content.assert_called_once_with(
            sample_statement, "mock content"
        )
        mock_dependencies["filename_generator"].generate.assert_called_once_with(
            sample_statement
        )
        mock_dependencies["repository"].save_statement.assert_called_once_with(
            sample_statement, expected_output_path
        )

    def test_processing_result_has_transactions(
        self, mock_dependencies, sample_statement
    ):
        """Test that ProcessingResult contains transactions > 0 (Prompt 18 requirement)"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("test_statement.pdf")
        output_dir = Path("output")

        # Configure mocks for successful processing
        mock_parser = Mock(spec=StatementParser)
        mock_validation_result = ValidationResult(is_valid=True, errors=[])

        mock_dependencies["parser_factory"].create_parser.return_value = mock_parser
        mock_parser.parse.return_value = sample_statement
        # Set up parse_with_content to return tuple (statement, content)
        mock_parser.parse_with_content.return_value = (sample_statement, "mock content")
        mock_dependencies["validator"].validate.return_value = mock_validation_result
        mock_dependencies[
            "validator"
        ].validate_with_content.return_value = mock_validation_result
        mock_dependencies[
            "filename_generator"
        ].generate.return_value = "test-transactions.xlsx"

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert - Specific Prompt 18 requirement
        assert result.statement is not None
        assert len(result.statement.transactions) > 0
        assert len(result.statement.transactions) == 3  # Our sample has 3 transactions
        assert all(isinstance(t, Transaction) for t in result.statement.transactions)

    def test_output_file_is_xlsx(self, mock_dependencies, sample_statement):
        """Test that output file has .xlsx suffix (Prompt 18 requirement)"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("test_statement.pdf")
        output_dir = Path("output")

        # Configure mocks
        mock_parser = Mock(spec=StatementParser)
        mock_validation_result = ValidationResult(is_valid=True, errors=[])

        mock_dependencies["parser_factory"].create_parser.return_value = mock_parser
        mock_parser.parse.return_value = sample_statement
        # Set up parse_with_content to return tuple (statement, content)
        mock_parser.parse_with_content.return_value = (sample_statement, "mock content")
        mock_dependencies["validator"].validate.return_value = mock_validation_result
        mock_dependencies[
            "validator"
        ].validate_with_content.return_value = mock_validation_result
        mock_dependencies[
            "filename_generator"
        ].generate.return_value = "MACRO-VISA-transactions.xlsx"

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert - Specific Prompt 18 requirement
        assert result.output_path is not None
        output_path = result.output_path  # Type narrowing for MyPy
        assert output_path.suffix == ".xlsx"
        assert output_path.name == "MACRO-VISA-transactions.xlsx"
        assert result.success is True

    def test_process_statement_parser_creation_fails(self, mock_dependencies):
        """Test error handling when parser creation fails"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("unsupported_file.xyz")
        output_dir = Path("output")

        mock_dependencies["parser_factory"].create_parser.side_effect = ValueError(
            "No parser available for file: unsupported_file.xyz"
        )

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert
        assert result.success is False
        assert result.statement is None
        assert result.output_path is None
        assert len(result.errors) == 1
        assert "No parser available" in result.errors[0]
        assert result.processing_time > 0.0

    def test_process_statement_parsing_fails(self, mock_dependencies):
        """Test error handling when statement parsing fails"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("corrupted_statement.pdf")
        output_dir = Path("output")

        mock_parser = Mock(spec=StatementParser)
        mock_dependencies["parser_factory"].create_parser.return_value = mock_parser
        mock_parser.parse.side_effect = Exception("Failed to extract text from PDF")
        mock_parser.parse_with_content.side_effect = Exception(
            "Failed to extract text from PDF"
        )

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert
        assert result.success is False
        assert result.statement is None
        assert result.output_path is None
        assert len(result.errors) == 1
        assert "Failed to extract text from PDF" in result.errors[0]

    def test_process_statement_validation_fails(
        self, mock_dependencies, sample_statement
    ):
        """Test error handling when statement validation fails"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("invalid_statement.pdf")
        output_dir = Path("output")

        mock_parser = Mock(spec=StatementParser)
        mock_validation_result = ValidationResult(
            is_valid=False, errors=["Balance mismatch", "Invalid transaction date"]
        )

        mock_dependencies["parser_factory"].create_parser.return_value = mock_parser
        mock_parser.parse.return_value = sample_statement
        # Set up parse_with_content to return tuple (statement, content)
        mock_parser.parse_with_content.return_value = (sample_statement, "mock content")
        mock_dependencies["validator"].validate.return_value = mock_validation_result
        mock_dependencies[
            "validator"
        ].validate_with_content.return_value = mock_validation_result

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert
        assert result.success is False
        assert result.statement == sample_statement  # Statement was parsed successfully
        assert result.output_path is None
        assert len(result.errors) == 2
        assert "Balance mismatch" in result.errors
        assert "Invalid transaction date" in result.errors
        assert result.validation_result == mock_validation_result

    def test_process_statement_filename_generation_fails(
        self, mock_dependencies, sample_statement
    ):
        """Test error handling when filename generation fails"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("test_statement.pdf")
        output_dir = Path("output")

        mock_parser = Mock(spec=StatementParser)
        mock_validation_result = ValidationResult(is_valid=True, errors=[])

        mock_dependencies["parser_factory"].create_parser.return_value = mock_parser
        mock_parser.parse.return_value = sample_statement
        # Set up parse_with_content to return tuple (statement, content)
        mock_parser.parse_with_content.return_value = (sample_statement, "mock content")
        mock_dependencies["validator"].validate.return_value = mock_validation_result
        mock_dependencies[
            "validator"
        ].validate_with_content.return_value = mock_validation_result
        mock_dependencies["filename_generator"].generate.side_effect = Exception(
            "Failed to generate filename"
        )

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert
        assert result.success is False
        assert result.statement == sample_statement
        assert result.output_path is None
        assert len(result.errors) == 1
        assert "Failed to generate filename" in result.errors[0]

    def test_process_statement_save_fails(self, mock_dependencies, sample_statement):
        """Test error handling when statement saving fails"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("test_statement.pdf")
        output_dir = Path("output")
        expected_output_path = output_dir / "test-transactions.xlsx"

        mock_parser = Mock(spec=StatementParser)
        mock_validation_result = ValidationResult(is_valid=True, errors=[])

        mock_dependencies["parser_factory"].create_parser.return_value = mock_parser
        mock_parser.parse.return_value = sample_statement
        # Set up parse_with_content to return tuple (statement, content)
        mock_parser.parse_with_content.return_value = (sample_statement, "mock content")
        mock_dependencies["validator"].validate.return_value = mock_validation_result
        mock_dependencies[
            "validator"
        ].validate_with_content.return_value = mock_validation_result
        mock_dependencies[
            "filename_generator"
        ].generate.return_value = "test-transactions.xlsx"
        mock_dependencies["repository"].save_statement.side_effect = PermissionError(
            "Permission denied: cannot write to output directory"
        )

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert
        assert result.success is False
        assert result.statement == sample_statement
        assert result.output_path == expected_output_path
        assert len(result.errors) == 1
        assert "Permission denied" in result.errors[0]

    def test_process_statement_unexpected_error(self, mock_dependencies):
        """Test error handling for unexpected exceptions"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("test_statement.pdf")
        output_dir = Path("output")

        # Simulate unexpected error during parser creation
        mock_dependencies["parser_factory"].create_parser.side_effect = RuntimeError(
            "Unexpected system error"
        )

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert
        assert result.success is False
        assert result.statement is None
        assert result.output_path is None
        assert len(result.errors) == 1
        assert "Unexpected system error" in result.errors[0]

    def test_processing_time_measurement(self, mock_dependencies, sample_statement):
        """Test that processing time is properly measured"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("test_statement.pdf")
        output_dir = Path("output")

        # Configure mocks with artificial delay
        mock_parser = Mock(spec=StatementParser)
        mock_validation_result = ValidationResult(is_valid=True, errors=[])

        def slow_parse(path):
            time.sleep(0.1)  # Simulate processing time
            return sample_statement

        mock_dependencies["parser_factory"].create_parser.return_value = mock_parser
        mock_parser.parse.side_effect = slow_parse
        # Set up parse_with_content to return tuple (statement, content)
        mock_parser.parse_with_content.side_effect = lambda path: (
            slow_parse(path),
            "mock content",
        )
        mock_dependencies["validator"].validate.return_value = mock_validation_result
        mock_dependencies[
            "validator"
        ].validate_with_content.return_value = mock_validation_result
        mock_dependencies[
            "filename_generator"
        ].generate.return_value = "test-transactions.xlsx"

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert
        assert result.success is True
        assert result.processing_time >= 0.1  # Should include the artificial delay
        assert result.processing_time < 1.0  # But not too long for a simple test

    def test_validation_error_during_validation_step(
        self, mock_dependencies, sample_statement
    ):
        """Test error handling when validation step itself throws an exception"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("test_statement.pdf")
        output_dir = Path("output")

        mock_parser = Mock(spec=StatementParser)
        mock_dependencies["parser_factory"].create_parser.return_value = mock_parser
        mock_parser.parse.return_value = sample_statement
        # Set up parse_with_content to return tuple (statement, content)
        mock_parser.parse_with_content.return_value = (sample_statement, "mock content")
        mock_dependencies["validator"].validate.side_effect = Exception(
            "Validation system error"
        )
        mock_dependencies["validator"].validate_with_content.side_effect = Exception(
            "Validation system error"
        )

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert
        assert result.success is False
        assert result.statement == sample_statement
        assert result.output_path is None
        assert len(result.errors) == 1
        assert "Validation system error" in result.errors[0]
        assert result.validation_result.is_valid is False
        assert "Validation system error" in result.validation_result.errors


# Import required for fixtures
