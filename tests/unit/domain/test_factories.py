"""
Unit tests for ParserFactory domain service.

This module tests the ParserFactory implementation including parser registration,
creation, and error handling scenarios. Tests validate the Factory Pattern
implementation and Strategy Pattern integration.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from domain.factories import ParserFactory
from domain.models import PaymentMethod, Statement
from domain.services import StatementParser


class TestParserFactory:
    """Test suite for ParserFactory class."""

    def test_factory_initialization(self):
        """Test factory initializes with empty parser registry."""
        factory = ParserFactory()

        assert factory.get_registered_parsers() == []
        assert factory.get_supported_extensions() == set()

    def test_register_parser_valid(self):
        """Test registering a valid StatementParser."""
        factory = ParserFactory()
        mock_parser = Mock(spec=StatementParser)

        factory.register_parser(mock_parser)

        registered_parsers = factory.get_registered_parsers()
        assert len(registered_parsers) == 1
        assert registered_parsers[0] is mock_parser

    def test_register_parser_invalid_type(self):
        """Test registering invalid parser type raises TypeError."""
        factory = ParserFactory()
        invalid_parser = "not a parser"

        with pytest.raises(TypeError, match="Expected StatementParser, got str"):
            factory.register_parser(invalid_parser)

    def test_register_multiple_parsers(self):
        """Test registering multiple parsers."""
        factory = ParserFactory()
        mock_parser1 = Mock(spec=StatementParser)
        mock_parser2 = Mock(spec=StatementParser)

        factory.register_parser(mock_parser1)
        factory.register_parser(mock_parser2)

        registered_parsers = factory.get_registered_parsers()
        assert len(registered_parsers) == 2
        assert mock_parser1 in registered_parsers
        assert mock_parser2 in registered_parsers

    def test_create_parser_success(self):
        """Test successful parser creation for supported file."""
        factory = ParserFactory()
        mock_parser = Mock(spec=StatementParser)
        mock_parser.can_parse.return_value = True

        factory.register_parser(mock_parser)

        file_path = Path("test.pdf")
        result = factory.create_parser(file_path)

        assert result is mock_parser
        mock_parser.can_parse.assert_called_once_with(file_path)

    def test_create_parser_no_match_raises_value_error(self):
        """Test create_parser raises ValueError when no parser matches."""
        factory = ParserFactory()
        mock_parser = Mock(spec=StatementParser)
        mock_parser.can_parse.return_value = False
        mock_parser.get_supported_extensions.return_value = {".pdf"}

        factory.register_parser(mock_parser)

        file_path = Path("test.xlsx")

        with pytest.raises(ValueError) as exc_info:
            factory.create_parser(file_path)

        error_message = str(exc_info.value)
        assert "No parser available for file" in error_message
        assert "test.xlsx" in error_message
        assert "File extension '.xlsx' is not supported" in error_message
        assert "Supported extensions: .pdf" in error_message

    def test_create_parser_no_parsers_registered(self):
        """Test create_parser with no registered parsers."""
        factory = ParserFactory()
        file_path = Path("test.pdf")

        with pytest.raises(ValueError) as exc_info:
            factory.create_parser(file_path)

        error_message = str(exc_info.value)
        assert "No parser available for file" in error_message
        assert "No parsers are registered in the factory" in error_message

    def test_create_parser_invalid_path_type(self):
        """Test create_parser with invalid path type raises TypeError."""
        factory = ParserFactory()

        with pytest.raises(TypeError, match="Expected Path, got str"):
            factory.create_parser("not_a_path")

    def test_create_parser_first_match_wins(self):
        """Test create_parser returns first matching parser."""
        factory = ParserFactory()

        mock_parser1 = Mock(spec=StatementParser)
        mock_parser1.can_parse.return_value = True

        mock_parser2 = Mock(spec=StatementParser)
        mock_parser2.can_parse.return_value = True

        factory.register_parser(mock_parser1)
        factory.register_parser(mock_parser2)

        file_path = Path("test.pdf")
        result = factory.create_parser(file_path)

        assert result is mock_parser1
        mock_parser1.can_parse.assert_called_once_with(file_path)
        mock_parser2.can_parse.assert_not_called()

    def test_get_supported_extensions_empty(self):
        """Test get_supported_extensions with no parsers."""
        factory = ParserFactory()

        extensions = factory.get_supported_extensions()

        assert extensions == set()

    def test_get_supported_extensions_single_parser(self):
        """Test get_supported_extensions with single parser."""
        factory = ParserFactory()
        mock_parser = Mock(spec=StatementParser)
        mock_parser.get_supported_extensions.return_value = {".pdf", ".txt"}

        factory.register_parser(mock_parser)

        extensions = factory.get_supported_extensions()

        assert extensions == {".pdf", ".txt"}
        mock_parser.get_supported_extensions.assert_called_once()

    def test_get_supported_extensions_multiple_parsers(self):
        """Test get_supported_extensions aggregates from multiple parsers."""
        factory = ParserFactory()

        mock_parser1 = Mock(spec=StatementParser)
        mock_parser1.get_supported_extensions.return_value = {".pdf"}

        mock_parser2 = Mock(spec=StatementParser)
        mock_parser2.get_supported_extensions.return_value = {".xls", ".xlsx"}

        factory.register_parser(mock_parser1)
        factory.register_parser(mock_parser2)

        extensions = factory.get_supported_extensions()

        assert extensions == {".pdf", ".xls", ".xlsx"}

    def test_get_registered_parsers_returns_copy(self):
        """Test get_registered_parsers returns copy to prevent external modification."""
        factory = ParserFactory()
        mock_parser = Mock(spec=StatementParser)

        factory.register_parser(mock_parser)

        parsers1 = factory.get_registered_parsers()
        parsers2 = factory.get_registered_parsers()

        # Should be equal but not the same object
        assert parsers1 == parsers2
        assert parsers1 is not parsers2

        # Modifying returned list shouldn't affect factory
        parsers1.clear()
        assert len(factory.get_registered_parsers()) == 1

    def test_clear_parsers(self):
        """Test clear_parsers removes all registered parsers."""
        factory = ParserFactory()
        mock_parser1 = Mock(spec=StatementParser)
        mock_parser2 = Mock(spec=StatementParser)

        factory.register_parser(mock_parser1)
        factory.register_parser(mock_parser2)
        assert len(factory.get_registered_parsers()) == 2

        factory.clear_parsers()

        assert factory.get_registered_parsers() == []
        assert factory.get_supported_extensions() == set()


class TestParserFactoryIntegration:
    """Integration tests for ParserFactory with concrete parser implementations."""

    def test_factory_with_concrete_parsers(self):
        """Test factory behavior with concrete parser implementations."""

        class MockPDFParser(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return file_path.suffix.lower() == ".pdf"

            def parse(self, file_path: Path) -> Statement:
                return Statement(payment_method=PaymentMethod.BBVA_VISA)

            def get_supported_extensions(self) -> set[str]:
                return {".pdf"}

        class MockXLSParser(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return file_path.suffix.lower() in {".xls", ".xlsx"}

            def parse(self, file_path: Path) -> Statement:
                return Statement(payment_method=PaymentMethod.BBVA_ACCOUNT)

            def get_supported_extensions(self) -> set[str]:
                return {".xls", ".xlsx"}

        factory = ParserFactory()
        pdf_parser = MockPDFParser()
        xls_parser = MockXLSParser()

        factory.register_parser(pdf_parser)
        factory.register_parser(xls_parser)

        # Test PDF file
        pdf_parser_result = factory.create_parser(Path("statement.pdf"))
        assert isinstance(pdf_parser_result, MockPDFParser)

        # Test XLS file
        xls_parser_result = factory.create_parser(Path("statement.xls"))
        assert isinstance(xls_parser_result, MockXLSParser)

        # Test XLSX file
        xlsx_parser_result = factory.create_parser(Path("statement.xlsx"))
        assert isinstance(xlsx_parser_result, MockXLSParser)

        # Test unsupported file
        with pytest.raises(ValueError, match="No parser available for file"):
            factory.create_parser(Path("statement.csv"))

        # Test supported extensions
        extensions = factory.get_supported_extensions()
        assert extensions == {".pdf", ".xls", ".xlsx"}

    def test_parser_registration_order_matters(self):
        """Test that parser registration order affects selection."""

        class GenericParser(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return True  # Accepts any file

            def parse(self, file_path: Path) -> Statement:
                return Statement(payment_method=PaymentMethod.BBVA_VISA)

            def get_supported_extensions(self) -> set[str]:
                return {"*"}

        class SpecificPDFParser(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return file_path.suffix.lower() == ".pdf"

            def parse(self, file_path: Path) -> Statement:
                return Statement(payment_method=PaymentMethod.MACRO_VISA)

            def get_supported_extensions(self) -> set[str]:
                return {".pdf"}

        factory = ParserFactory()
        generic_parser = GenericParser()
        specific_parser = SpecificPDFParser()

        # Register specific parser first
        factory.register_parser(specific_parser)
        factory.register_parser(generic_parser)

        # Should get specific parser for PDF files
        result = factory.create_parser(Path("test.pdf"))
        assert isinstance(result, SpecificPDFParser)

        # Clear and register in opposite order
        factory.clear_parsers()
        factory.register_parser(generic_parser)
        factory.register_parser(specific_parser)

        # Should get generic parser (first registered)
        result = factory.create_parser(Path("test.pdf"))
        assert isinstance(result, GenericParser)
