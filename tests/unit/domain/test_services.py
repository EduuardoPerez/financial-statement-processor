"""
Unit tests for domain services module.

This module tests the abstract service interfaces that form the core business
logic contracts in our hexagonal architecture.
"""

from abc import ABC
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.domain.models import Currency, PaymentMethod, Statement, Transaction
from src.domain.services import StatementParser


class TestStatementParser:
    """Test cases for StatementParser abstract base class."""

    def test_statement_parser_is_abstract_base_class(self):
        """Test that StatementParser is properly configured as an ABC."""
        assert issubclass(StatementParser, ABC)

    def test_cannot_instantiate_abstract_class(self):
        """Test that StatementParser cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            StatementParser()

    def test_abstract_methods_are_defined(self):
        """Test that all required abstract methods are defined."""
        required_methods = ["can_parse", "parse", "get_supported_extensions"]

        for method_name in required_methods:
            assert hasattr(StatementParser, method_name)
            method = getattr(StatementParser, method_name)
            assert callable(method)

    def test_issubclass_validation_works(self):
        """Test that issubclass validation works as required by the specification."""

        class ConcreteParser(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return True

            def parse(self, file_path: Path) -> Statement:
                return Statement(payment_method=PaymentMethod.BBVA_VISA)

            def get_supported_extensions(self) -> set[str]:
                return {".pdf"}

        # This is the key validation requirement from the task
        assert issubclass(ConcreteParser, StatementParser)

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that concrete implementations can be instantiated and used."""

        class TestParser(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return file_path.suffix.lower() == ".test"

            def parse(self, file_path: Path) -> Statement:
                # Create a minimal valid statement
                statement = Statement(payment_method=PaymentMethod.MACRO_VISA)
                transaction = Transaction(
                    date=date(2025, 1, 15),
                    description="Test Transaction",
                    amount=Decimal("100.50"),
                    currency=Currency.ARS,
                    payment_method=PaymentMethod.MACRO_VISA,
                )
                statement.add_transaction(transaction)
                return statement

            def get_supported_extensions(self) -> set[str]:
                return {".test"}

        # Should be able to instantiate concrete implementation
        parser = TestParser()

        # Test can_parse method
        test_file = Path("statement.test")
        assert parser.can_parse(test_file) is True

        non_test_file = Path("statement.pdf")
        assert parser.can_parse(non_test_file) is False

        # Test get_supported_extensions method
        extensions = parser.get_supported_extensions()
        assert extensions == {".test"}

        # Test parse method returns valid Statement
        statement = parser.parse(test_file)
        assert isinstance(statement, Statement)
        assert statement.payment_method == PaymentMethod.MACRO_VISA
        assert len(statement.transactions) == 1
        assert statement.transactions[0].description == "Test Transaction"

    def test_multiple_concrete_implementations(self):
        """Test that multiple concrete implementations can coexist."""

        class PDFParser(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return file_path.suffix.lower() == ".pdf"

            def parse(self, file_path: Path) -> Statement:
                return Statement(payment_method=PaymentMethod.BBVA_VISA)

            def get_supported_extensions(self) -> set[str]:
                return {".pdf"}

        class XLSParser(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return file_path.suffix.lower() in {".xls", ".xlsx"}

            def parse(self, file_path: Path) -> Statement:
                return Statement(payment_method=PaymentMethod.BBVA_ACCOUNT)

            def get_supported_extensions(self) -> set[str]:
                return {".xls", ".xlsx"}

        # Both should be valid subclasses
        assert issubclass(PDFParser, StatementParser)
        assert issubclass(XLSParser, StatementParser)

        # Both should be instantiable
        pdf_parser = PDFParser()
        xls_parser = XLSParser()

        # They should have different behaviors
        pdf_file = Path("statement.pdf")
        xls_file = Path("statement.xls")

        assert pdf_parser.can_parse(pdf_file) is True
        assert pdf_parser.can_parse(xls_file) is False

        assert xls_parser.can_parse(xls_file) is True
        assert xls_parser.can_parse(pdf_file) is False

        assert pdf_parser.get_supported_extensions() == {".pdf"}
        assert xls_parser.get_supported_extensions() == {".xls", ".xlsx"}

    def test_incomplete_implementation_cannot_be_instantiated(self):
        """Test that incomplete implementations cannot be instantiated."""

        class IncompleteParser(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return True

            # Missing parse() and get_supported_extensions() methods

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteParser()

    def test_parser_interface_supports_strategy_pattern(self):
        """Test that the interface supports the Strategy Pattern as intended."""

        class MockParserA(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return file_path.name.startswith("type_a")

            def parse(self, file_path: Path) -> Statement:
                return Statement(payment_method=PaymentMethod.BBVA_VISA)

            def get_supported_extensions(self) -> set[str]:
                return {".pdf"}

        class MockParserB(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return file_path.name.startswith("type_b")

            def parse(self, file_path: Path) -> Statement:
                return Statement(payment_method=PaymentMethod.MACRO_VISA)

            def get_supported_extensions(self) -> set[str]:
                return {".xls"}

        # Simulate a parser factory using the strategy pattern
        parsers = [MockParserA(), MockParserB()]

        def find_parser(file_path: Path) -> StatementParser | None:
            for parser in parsers:
                if parser.can_parse(file_path):
                    return parser
            return None

        # Test strategy selection
        type_a_file = Path("type_a_statement.pdf")
        type_b_file = Path("type_b_statement.xls")
        unknown_file = Path("unknown_statement.csv")

        parser_a = find_parser(type_a_file)
        parser_b = find_parser(type_b_file)
        parser_unknown = find_parser(unknown_file)

        assert isinstance(parser_a, MockParserA)
        assert isinstance(parser_b, MockParserB)
        assert parser_unknown is None

        # Test that different parsers produce different results
        statement_a = parser_a.parse(type_a_file)
        statement_b = parser_b.parse(type_b_file)

        assert statement_a.payment_method == PaymentMethod.BBVA_VISA
        assert statement_b.payment_method == PaymentMethod.MACRO_VISA

    def test_interface_integrates_with_domain_models(self):
        """Test that the interface properly integrates with existing domain models."""

        class IntegrationTestParser(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return True

            def parse(self, file_path: Path) -> Statement:
                # Create statement with multiple transactions and currencies
                statement = Statement(payment_method=PaymentMethod.MERCADOPAGO)

                # Add ARS transaction
                ars_transaction = Transaction(
                    date=date(2025, 1, 15),
                    description="ARS Purchase",
                    amount=Decimal("-150.75"),
                    currency=Currency.ARS,
                    payment_method=PaymentMethod.MERCADOPAGO,
                    reference="REF001",
                )
                statement.add_transaction(ars_transaction)

                # Add USD transaction
                usd_transaction = Transaction(
                    date=date(2025, 1, 16),
                    description="USD Payment",
                    amount=Decimal("50.00"),
                    currency=Currency.USD,
                    payment_method=PaymentMethod.MERCADOPAGO,
                    reference="REF002",
                )
                statement.add_transaction(usd_transaction)

                return statement

            def get_supported_extensions(self) -> set[str]:
                return {".xlsx"}

        parser = IntegrationTestParser()
        statement = parser.parse(Path("test.xlsx"))

        # Verify integration with domain models
        assert isinstance(statement, Statement)
        assert statement.payment_method == PaymentMethod.MERCADOPAGO
        assert len(statement.transactions) == 2

        # Test domain model methods work correctly
        balance = statement.get_balance()
        assert balance.ars_amount == Decimal("-150.75")
        assert balance.usd_amount == Decimal("50.00")

        ars_transactions = statement.get_transactions_by_currency(Currency.ARS)
        usd_transactions = statement.get_transactions_by_currency(Currency.USD)

        assert len(ars_transactions) == 1
        assert len(usd_transactions) == 1
        assert ars_transactions[0].description == "ARS Purchase"
        assert usd_transactions[0].description == "USD Payment"
