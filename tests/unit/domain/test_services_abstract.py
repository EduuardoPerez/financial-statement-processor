"""
Unit tests for abstract service classes in domain/services.

This module tests the abstract base classes and their concrete implementations.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.domain.models import Currency, PaymentMethod, Statement, Transaction
from src.domain.services import (
    BalanceExtractor,
    BalanceExtractorExtended,
    StatementParser,
)


class ConcreteStatementParser(StatementParser):
    """Concrete implementation for testing."""

    def can_parse(self, file_path: Path) -> bool:
        """Test implementation."""
        return file_path.suffix.lower() == ".test"

    def parse(self, file_path: Path) -> Statement:
        """Test implementation."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        transaction = Transaction(
            date=date(2025, 1, 1),
            description="Test transaction",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )
        statement.add_transaction(transaction)
        return statement

    def get_supported_extensions(self) -> set[str]:
        """Test implementation."""
        return {".test"}


class ConcreteBalanceExtractor(BalanceExtractor):
    """Concrete implementation for testing."""

    def extract_balance(
        self, content: str, payment_method: PaymentMethod
    ) -> dict[str, Decimal]:
        """Test implementation."""
        return {"ars": Decimal("100.00"), "usd": Decimal("0.00")}

    def can_extract(self, payment_method: PaymentMethod) -> bool:
        """Test implementation."""
        return payment_method == PaymentMethod.BBVA_VISA


class ConcreteBalanceExtractorExtended(BalanceExtractorExtended):
    """Concrete implementation for testing."""

    def extract_balance(
        self, content: str, payment_method: PaymentMethod
    ) -> dict[str, Decimal]:
        """Test implementation."""
        return {"ars": Decimal("200.00"), "usd": Decimal("50.00")}

    def can_extract(self, payment_method: PaymentMethod) -> bool:
        """Test implementation."""
        return payment_method in {PaymentMethod.BBVA_VISA, PaymentMethod.MACRO_VISA}


class TestStatementParser:
    """Test StatementParser abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            StatementParser()

    def test_concrete_implementation_works(self):
        """Test concrete implementation of abstract class."""
        parser = ConcreteStatementParser()
        assert isinstance(parser, StatementParser)

        # Test can_parse
        test_file = Path("test.test")
        assert parser.can_parse(test_file) is True

        non_test_file = Path("test.pdf")
        assert parser.can_parse(non_test_file) is False

        # Test get_supported_extensions
        extensions = parser.get_supported_extensions()
        assert extensions == {".test"}

    def test_parse_with_content_default_implementation(self):
        """Test default implementation of parse_with_content."""
        parser = ConcreteStatementParser()
        test_file = Path("test.test")

        # Test parse_with_content default implementation
        statement, content = parser.parse_with_content(test_file)

        # Should return statement and empty string for content
        assert isinstance(statement, Statement)
        assert content == ""
        assert len(statement.transactions) == 1
        assert statement.transactions[0].description == "Test transaction"


class TestBalanceExtractor:
    """Test BalanceExtractor abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            BalanceExtractor()

    def test_concrete_implementation_works(self):
        """Test concrete implementation of abstract class."""
        extractor = ConcreteBalanceExtractor()
        assert isinstance(extractor, BalanceExtractor)

        # Test can_extract
        assert extractor.can_extract(PaymentMethod.BBVA_VISA) is True
        assert extractor.can_extract(PaymentMethod.MACRO_VISA) is False

        # Test extract_balance
        result = extractor.extract_balance("test content", PaymentMethod.BBVA_VISA)
        assert result == {"ars": Decimal("100.00"), "usd": Decimal("0.00")}


class TestBalanceExtractorExtended:
    """Test BalanceExtractorExtended abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            BalanceExtractorExtended()

    def test_concrete_implementation_works(self):
        """Test concrete implementation of extended abstract class."""
        extractor = ConcreteBalanceExtractorExtended()
        assert isinstance(extractor, BalanceExtractorExtended)
        assert isinstance(extractor, BalanceExtractor)  # Should inherit from base

        # Test can_extract
        assert extractor.can_extract(PaymentMethod.BBVA_VISA) is True
        assert extractor.can_extract(PaymentMethod.MACRO_VISA) is True
        assert extractor.can_extract(PaymentMethod.MERCADOPAGO) is False

        # Test extract_balance
        result = extractor.extract_balance("test content", PaymentMethod.BBVA_VISA)
        assert result == {"ars": Decimal("200.00"), "usd": Decimal("50.00")}

    def test_extended_functionality(self):
        """Test extended functionality specific to BalanceExtractorExtended."""
        extractor = ConcreteBalanceExtractorExtended()

        # Test that it supports multiple payment methods
        supported_methods = [
            PaymentMethod.BBVA_VISA,
            PaymentMethod.MACRO_VISA,
        ]

        for method in supported_methods:
            assert extractor.can_extract(method) is True
            result = extractor.extract_balance("content", method)
            assert "ars" in result
            assert "usd" in result


class TestAbstractClassInheritance:
    """Test abstract class inheritance behaviors."""

    def test_subclass_relationships(self):
        """Test that subclasses maintain proper relationships."""
        parser = ConcreteStatementParser()
        extractor = ConcreteBalanceExtractor()
        extended_extractor = ConcreteBalanceExtractorExtended()

        # Test isinstance relationships
        assert isinstance(parser, StatementParser)
        assert isinstance(extractor, BalanceExtractor)
        assert isinstance(extended_extractor, BalanceExtractorExtended)
        assert isinstance(extended_extractor, BalanceExtractor)

        # Test class hierarchy
        assert issubclass(ConcreteStatementParser, StatementParser)
        assert issubclass(ConcreteBalanceExtractor, BalanceExtractor)
        assert issubclass(ConcreteBalanceExtractorExtended, BalanceExtractorExtended)
        assert issubclass(BalanceExtractorExtended, BalanceExtractor)

    def test_abstract_method_enforcement(self):
        """Test that abstract methods are properly enforced."""

        # Creating incomplete concrete class should fail
        class IncompleteParser(StatementParser):
            def can_parse(self, file_path: Path) -> bool:
                return True

            # Missing parse() and get_supported_extensions()

        with pytest.raises(TypeError):
            IncompleteParser()

        class IncompleteExtractor(BalanceExtractor):
            def extract_balance(
                self, content: str, payment_method: PaymentMethod
            ) -> dict[str, Decimal]:
                return {"ars": Decimal("0"), "usd": Decimal("0")}

            # Missing can_extract()

        with pytest.raises(TypeError):
            IncompleteExtractor()
