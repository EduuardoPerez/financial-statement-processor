"""
Unit tests for the FilenameGenerator domain service.
"""

import re
from datetime import date
from decimal import Decimal

import pytest

from domain.filename import FilenameGenerator
from domain.models import Currency, PaymentMethod, Statement, Transaction


class TestFilenameGenerator:
    """Test the FilenameGenerator domain service."""

    @pytest.fixture
    def generator(self):
        """Create FilenameGenerator instance for testing."""
        return FilenameGenerator()

    @pytest.fixture
    def sample_transaction(self):
        """Create a sample transaction for testing."""
        return Transaction(
            date=date(2025, 3, 28),
            description="Test Transaction",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

    def test_generate_bbva_visa_filename(self, generator, sample_transaction):
        """Test filename generation for BBVA VISA statement."""
        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA, transactions=[sample_transaction]
        )

        result = generator.generate(statement)

        assert result == "BBVA_VISA_20250328.xlsx"

    def test_generate_bbva_mastercard_filename(self, generator):
        """Test filename generation for BBVA Mastercard statement."""
        transaction = Transaction(
            date=date(2025, 4, 15),
            description="Mastercard Purchase",
            amount=Decimal("250.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_MASTERCARD,
        )
        statement = Statement(
            payment_method=PaymentMethod.BBVA_MASTERCARD, transactions=[transaction]
        )

        result = generator.generate(statement)

        assert result == "BBVA_MASTERCARD_20250415.xlsx"

    def test_generate_bbva_account_filename(self, generator):
        """Test filename generation for BBVA Account statement."""
        transaction = Transaction(
            date=date(2025, 6, 7),
            description="Account Transfer",
            amount=Decimal("1000.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_ACCOUNT,
        )
        statement = Statement(
            payment_method=PaymentMethod.BBVA_ACCOUNT, transactions=[transaction]
        )

        result = generator.generate(statement)

        assert result == "BBVA_ACCOUNT_20250607.xlsx"

    def test_generate_macro_visa_filename(self, generator):
        """Test filename generation for Macro VISA statement."""
        transaction = Transaction(
            date=date(2025, 12, 22),
            description="Macro Purchase",
            amount=Decimal("75.25"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.MACRO_VISA,
        )
        statement = Statement(
            payment_method=PaymentMethod.MACRO_VISA, transactions=[transaction]
        )

        result = generator.generate(statement)

        assert result == "MACRO_VISA_20251222.xlsx"

    def test_generate_macro_account_filename(self, generator):
        """Test filename generation for Macro Account statement."""
        transaction = Transaction(
            date=date(2025, 1, 1),
            description="New Year Transfer",
            amount=Decimal("500.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.MACRO_ACCOUNT,
        )
        statement = Statement(
            payment_method=PaymentMethod.MACRO_ACCOUNT, transactions=[transaction]
        )

        result = generator.generate(statement)

        assert result == "MACRO_ACCOUNT_20250101.xlsx"

    def test_generate_mercadopago_filename(self, generator):
        """Test filename generation for Mercadopago statement."""
        transaction = Transaction(
            date=date(2025, 8, 30),
            description="MP Payment",
            amount=Decimal("150.75"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.MERCADOPAGO,
        )
        statement = Statement(
            payment_method=PaymentMethod.MERCADOPAGO, transactions=[transaction]
        )

        result = generator.generate(statement)

        assert result == "MERCADOPAGO_20250830.xlsx"

    def test_generate_with_multiple_transactions_uses_earliest_date(self, generator):
        """Test that filename uses earliest transaction date."""
        transactions = [
            Transaction(
                date=date(2025, 3, 30),
                description="Later Transaction",
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 3, 15),
                description="Earlier Transaction",
                amount=Decimal("200.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 3, 25),
                description="Middle Transaction",
                amount=Decimal("150.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
        ]
        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA, transactions=transactions
        )

        result = generator.generate(statement)

        # Should use earliest date (2025-03-15)
        assert result == "BBVA_VISA_20250315.xlsx"

    def test_generate_with_mixed_currencies(self, generator):
        """Test filename generation with mixed currency transactions."""
        transactions = [
            Transaction(
                date=date(2025, 5, 10),
                description="ARS Transaction",
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 5, 5),
                description="USD Transaction",
                amount=Decimal("50.00"),
                currency=Currency.USD,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
        ]
        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA, transactions=transactions
        )

        result = generator.generate(statement)

        # Should use earliest date regardless of currency
        assert result == "BBVA_VISA_20250505.xlsx"

    def test_generate_empty_statement_raises_error(self, generator):
        """Test that empty statement raises ValueError."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA, transactions=[])

        with pytest.raises(ValueError, match="Cannot generate filename"):
            generator.generate(statement)

    def test_filename_matches_required_pattern(self, generator, sample_transaction):
        """Test that generated filename matches required regex pattern."""
        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA, transactions=[sample_transaction]
        )

        result = generator.generate(statement)

        # Pattern: ^[A-Z_]+_\d{8}\.xlsx$
        pattern = r"^[A-Z_]+_\d{8}\.xlsx$"
        assert re.match(pattern, result), f"Filename '{result}' does not match pattern"

    def test_all_payment_methods_generate_valid_filenames(self, generator):
        """Test that all payment methods generate valid filenames."""
        test_date = date(2025, 6, 15)

        for payment_method in PaymentMethod:
            transaction = Transaction(
                date=test_date,
                description="Test Transaction",
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                payment_method=payment_method,
            )
            statement = Statement(
                payment_method=payment_method, transactions=[transaction]
            )

            result = generator.generate(statement)

            # Verify pattern compliance
            pattern = r"^[A-Z_]+_\d{8}\.xlsx$"
            assert re.match(pattern, result), (
                f"Payment method {payment_method} generated invalid filename: {result}"
            )

            # Verify date is correct
            assert "20250615" in result, (
                f"Filename {result} does not contain expected date"
            )

            # Verify extension
            assert result.endswith(".xlsx"), (
                f"Filename {result} does not have .xlsx extension"
            )

    def test_get_method_prefix_known_methods(self, generator):
        """Test _get_method_prefix for all known payment methods."""
        expected_mappings = {
            PaymentMethod.BBVA_VISA: "BBVA_VISA",
            PaymentMethod.BBVA_MASTERCARD: "BBVA_MASTERCARD",
            PaymentMethod.BBVA_ACCOUNT: "BBVA_ACCOUNT",
            PaymentMethod.MACRO_VISA: "MACRO_VISA",
            PaymentMethod.MACRO_ACCOUNT: "MACRO_ACCOUNT",
            PaymentMethod.MERCADOPAGO: "MERCADOPAGO",
        }

        for payment_method, expected_prefix in expected_mappings.items():
            result = generator._get_method_prefix(payment_method)
            assert result == expected_prefix

    def test_date_formatting_edge_cases(self, generator):
        """Test date formatting for edge cases."""
        edge_dates = [
            (date(2025, 1, 1), "20250101"),  # New Year
            (date(2025, 12, 31), "20251231"),  # New Year's Eve
            (date(2025, 2, 28), "20250228"),  # Non-leap year Feb 28
            (date(2024, 2, 29), "20240229"),  # Leap year Feb 29
        ]

        for test_date, expected_date_str in edge_dates:
            transaction = Transaction(
                date=test_date,
                description="Edge Case Transaction",
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )
            statement = Statement(
                payment_method=PaymentMethod.BBVA_VISA, transactions=[transaction]
            )

            result = generator.generate(statement)

            assert expected_date_str in result, (
                f"Date {test_date} not formatted correctly in {result}"
            )

    def test_filename_components_order(self, generator, sample_transaction):
        """Test that filename components are in correct order."""
        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA, transactions=[sample_transaction]
        )

        result = generator.generate(statement)

        # Expected format: METHOD_PREFIX_YYYYMMDD.xlsx
        parts = result.replace(".xlsx", "").split("_")

        # Should have at least 3 parts: BBVA, VISA, YYYYMMDD
        assert len(parts) >= 3

        # Last part should be the date (8 digits)
        date_part = parts[-1]
        assert len(date_part) == 8
        assert date_part.isdigit()
        assert date_part == "20250328"

    def test_filename_uniqueness_by_date(self, generator):
        """Test that different dates generate different filenames."""
        dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),
            date(2025, 2, 1),
            date(2025, 12, 31),
        ]

        filenames = []
        for test_date in dates:
            transaction = Transaction(
                date=test_date,
                description="Test Transaction",
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )
            statement = Statement(
                payment_method=PaymentMethod.BBVA_VISA, transactions=[transaction]
            )

            filename = generator.generate(statement)
            filenames.append(filename)

        # All filenames should be unique
        assert len(set(filenames)) == len(filenames)

    def test_filename_consistency_same_input(self, generator, sample_transaction):
        """Test that same input generates same filename consistently."""
        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA, transactions=[sample_transaction]
        )

        # Generate filename multiple times
        results = [generator.generate(statement) for _ in range(5)]

        # All results should be identical
        assert all(result == results[0] for result in results)
        assert results[0] == "BBVA_VISA_20250328.xlsx"
