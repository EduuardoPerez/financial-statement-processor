"""
Unit tests for domain models.

Tests the core domain entities and value objects to ensure model correctness
with comprehensive validation of business rules and constraints.
"""

from datetime import date
from decimal import Decimal

import pytest

from src.domain.models import (
    Balance,
    Currency,
    PaymentMethod,
    Statement,
    Transaction,
)


class TestCurrency:
    """Test Currency enumeration."""

    def test_currency_values(self):
        """Test currency enum values are correct."""
        assert Currency.ARS.value == "ARS"
        assert Currency.USD.value == "USD"

    def test_currency_string_representation(self):
        """Test currency string representation."""
        assert str(Currency.ARS) == "ARS"
        assert str(Currency.USD) == "USD"


class TestPaymentMethod:
    """Test PaymentMethod enumeration."""

    def test_payment_method_values(self):
        """Test payment method enum values are correct."""
        assert PaymentMethod.MACRO_VISA.value == "Macro Visa"
        assert PaymentMethod.BBVA_VISA.value == "BBVA Visa"
        assert PaymentMethod.BBVA_MASTERCARD.value == "BBVA Mastercard"
        assert PaymentMethod.BBVA_ACCOUNT.value == "BBVA Account"
        assert PaymentMethod.MACRO_ACCOUNT.value == "Macro Account"
        assert PaymentMethod.MERCADOPAGO.value == "Mercado Pago"

    def test_payment_method_string_representation(self):
        """Test payment method string representation."""
        assert str(PaymentMethod.MACRO_VISA) == "Macro Visa"
        assert str(PaymentMethod.BBVA_VISA) == "BBVA Visa"
        assert str(PaymentMethod.BBVA_MASTERCARD) == "BBVA Mastercard"
        assert str(PaymentMethod.BBVA_ACCOUNT) == "BBVA Account"
        assert str(PaymentMethod.MACRO_ACCOUNT) == "Macro Account"
        assert str(PaymentMethod.MERCADOPAGO) == "Mercado Pago"


class TestTransaction:
    """Test Transaction value object."""

    def test_valid_construction_with_required_fields(self):
        """Test transaction construction with all required fields."""
        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Test purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        assert transaction.date == date(2025, 6, 22)
        assert transaction.description == "Test purchase"
        assert transaction.amount == Decimal("100.50")
        assert transaction.currency == Currency.ARS
        assert transaction.payment_method == PaymentMethod.BBVA_VISA
        assert transaction.reference is None

    def test_valid_construction_with_optional_reference(self):
        """Test transaction construction with optional reference."""
        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Test purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="REF123456",
        )

        assert transaction.reference == "REF123456"

    def test_transaction_is_immutable(self):
        """Test that transaction objects are immutable (frozen)."""
        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Test purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        with pytest.raises(AttributeError):
            transaction.amount = Decimal("200.00")  # type: ignore

    def test_rejects_empty_description(self):
        """Test transaction rejects empty string description."""
        with pytest.raises(ValueError, match="Transaction description cannot be empty"):
            Transaction(
                date=date(2025, 6, 22),
                description="",
                amount=Decimal("100.50"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_rejects_whitespace_only_description(self):
        """Test transaction rejects whitespace-only description."""
        with pytest.raises(ValueError, match="Transaction description cannot be empty"):
            Transaction(
                date=date(2025, 6, 22),
                description="   \t\n   ",
                amount=Decimal("100.50"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_rejects_zero_amount(self):
        """Test transaction rejects zero amount."""
        with pytest.raises(ValueError, match="Transaction amount cannot be zero"):
            Transaction(
                date=date(2025, 6, 22),
                description="Test purchase",
                amount=Decimal("0"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_is_credit_positive_amount(self):
        """Test is_credit returns True for positive amounts."""
        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Credit transaction",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        assert transaction.is_credit() is True
        assert transaction.is_debit() is False

    def test_is_debit_negative_amount(self):
        """Test is_debit returns True for negative amounts."""
        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Debit transaction",
            amount=Decimal("-100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        assert transaction.is_debit() is True
        assert transaction.is_credit() is False

    def test_get_absolute_amount(self):
        """Test get_absolute_amount returns absolute value."""
        positive_transaction = Transaction(
            date=date(2025, 6, 22),
            description="Credit transaction",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        negative_transaction = Transaction(
            date=date(2025, 6, 22),
            description="Debit transaction",
            amount=Decimal("-100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        assert positive_transaction.get_absolute_amount() == Decimal("100.50")
        assert negative_transaction.get_absolute_amount() == Decimal("100.50")


class TestBalance:
    """Test Balance value object."""

    def test_valid_construction(self):
        """Test balance construction with positive and negative amounts."""
        balance = Balance(
            ars_amount=Decimal("1000.50"),
            usd_amount=Decimal("-200.25"),
        )

        assert balance.ars_amount == Decimal("1000.50")
        assert balance.usd_amount == Decimal("-200.25")

    def test_balance_is_immutable(self):
        """Test that balance objects are immutable (frozen)."""
        balance = Balance(
            ars_amount=Decimal("1000.50"),
            usd_amount=Decimal("-200.25"),
        )

        with pytest.raises(AttributeError):
            balance.ars_amount = Decimal("2000.00")  # type: ignore

    def test_total_in_currency_ars(self):
        """Test total_in_currency returns correct ARS amount."""
        balance = Balance(
            ars_amount=Decimal("1000.50"),
            usd_amount=Decimal("-200.25"),
        )

        assert balance.total_in_currency(Currency.ARS) == Decimal("1000.50")

    def test_total_in_currency_usd(self):
        """Test total_in_currency returns correct USD amount."""
        balance = Balance(
            ars_amount=Decimal("1000.50"),
            usd_amount=Decimal("-200.25"),
        )

        assert balance.total_in_currency(Currency.USD) == Decimal("-200.25")

    def test_total_in_currency_invalid_currency(self):
        """Test total_in_currency raises error for invalid currency."""
        balance = Balance(
            ars_amount=Decimal("1000.50"),
            usd_amount=Decimal("-200.25"),
        )

        # Test with None to trigger the else clause in total_in_currency
        with pytest.raises(ValueError, match="Unsupported currency"):
            balance.total_in_currency(None)  # type: ignore

    def test_is_zero_both_currencies_zero(self):
        """Test is_zero returns True when both currencies are zero."""
        balance = Balance(
            ars_amount=Decimal("0"),
            usd_amount=Decimal("0"),
        )

        assert balance.is_zero() is True

    def test_is_zero_one_currency_non_zero(self):
        """Test is_zero returns False when any currency is non-zero."""
        balance_ars_non_zero = Balance(
            ars_amount=Decimal("100.00"),
            usd_amount=Decimal("0"),
        )

        balance_usd_non_zero = Balance(
            ars_amount=Decimal("0"),
            usd_amount=Decimal("50.00"),
        )

        assert balance_ars_non_zero.is_zero() is False
        assert balance_usd_non_zero.is_zero() is False

    def test_has_positive_balance(self):
        """Test has_positive_balance returns True when any currency is positive."""
        balance_ars_positive = Balance(
            ars_amount=Decimal("100.00"),
            usd_amount=Decimal("-50.00"),
        )

        balance_usd_positive = Balance(
            ars_amount=Decimal("-100.00"),
            usd_amount=Decimal("50.00"),
        )

        balance_both_negative = Balance(
            ars_amount=Decimal("-100.00"),
            usd_amount=Decimal("-50.00"),
        )

        assert balance_ars_positive.has_positive_balance() is True
        assert balance_usd_positive.has_positive_balance() is True
        assert balance_both_negative.has_positive_balance() is False

    def test_has_negative_balance(self):
        """Test has_negative_balance returns True when any currency is negative."""
        balance_ars_negative = Balance(
            ars_amount=Decimal("-100.00"),
            usd_amount=Decimal("50.00"),
        )

        balance_usd_negative = Balance(
            ars_amount=Decimal("100.00"),
            usd_amount=Decimal("-50.00"),
        )

        balance_both_positive = Balance(
            ars_amount=Decimal("100.00"),
            usd_amount=Decimal("50.00"),
        )

        assert balance_ars_negative.has_negative_balance() is True
        assert balance_usd_negative.has_negative_balance() is True
        assert balance_both_positive.has_negative_balance() is False


class TestStatement:
    """Test Statement aggregate root."""

    def test_valid_construction_empty_statement(self):
        """Test statement construction with payment method only."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        assert statement.payment_method == PaymentMethod.BBVA_VISA
        assert statement.transactions == []
        assert statement.reported_balance is None

    def test_valid_construction_with_reported_balance(self):
        """Test statement construction with reported balance."""
        reported_balance = Balance(
            ars_amount=Decimal("1000.00"),
            usd_amount=Decimal("0"),
        )

        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA,
            reported_balance=reported_balance,
        )

        assert statement.reported_balance == reported_balance

    def test_add_transaction_matching_payment_method(self):
        """Test adding transaction with matching payment method."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Test purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        statement.add_transaction(transaction)

        assert len(statement.transactions) == 1
        assert statement.transactions[0] == transaction

    def test_add_transaction_rejects_mismatched_payment_method(self):
        """Test add_transaction rejects transaction with mismatched payment method."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Test purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.MACRO_VISA,  # Different payment method
        )

        with pytest.raises(
            ValueError,
            match="Transaction payment method 'Macro Visa' does not match statement payment method 'BBVA Visa'",
        ):
            statement.add_transaction(transaction)

    def test_add_transactions_all_matching(self):
        """Test adding multiple transactions with matching payment methods."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        transactions = [
            Transaction(
                date=date(2025, 6, 22),
                description="Purchase 1",
                amount=Decimal("100.50"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 23),
                description="Purchase 2",
                amount=Decimal("-50.25"),
                currency=Currency.USD,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
        ]

        statement.add_transactions(transactions)

        assert len(statement.transactions) == 2
        assert statement.transactions == transactions

    def test_add_transactions_rejects_any_mismatched(self):
        """Test add_transactions rejects if any transaction has mismatched payment method."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        transactions = [
            Transaction(
                date=date(2025, 6, 22),
                description="Purchase 1",
                amount=Decimal("100.50"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 23),
                description="Purchase 2",
                amount=Decimal("-50.25"),
                currency=Currency.USD,
                payment_method=PaymentMethod.MACRO_VISA,  # Mismatched
            ),
        ]

        with pytest.raises(
            ValueError,
            match="Transaction payment method 'Macro Visa' does not match statement payment method 'BBVA Visa'",
        ):
            statement.add_transactions(transactions)

        # First transaction was added before the second failed
        assert len(statement.transactions) == 1
        assert statement.transactions[0].description == "Purchase 1"

    def test_get_balance_single_currency(self):
        """Test get_balance calculation with single currency transactions."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        transactions = [
            Transaction(
                date=date(2025, 6, 22),
                description="Credit",
                amount=Decimal("100.50"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 23),
                description="Debit",
                amount=Decimal("-50.25"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
        ]

        statement.add_transactions(transactions)
        balance = statement.get_balance()

        assert balance.ars_amount == Decimal("50.25")
        assert balance.usd_amount == Decimal("0")

    def test_get_balance_multiple_currencies(self):
        """Test get_balance calculation with multiple currency transactions."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        transactions = [
            Transaction(
                date=date(2025, 6, 22),
                description="ARS Credit",
                amount=Decimal("1000.50"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 23),
                description="USD Debit",
                amount=Decimal("-200.25"),
                currency=Currency.USD,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 24),
                description="ARS Debit",
                amount=Decimal("-500.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
        ]

        statement.add_transactions(transactions)
        balance = statement.get_balance()

        assert balance.ars_amount == Decimal("500.50")
        assert balance.usd_amount == Decimal("-200.25")

    def test_get_balance_empty_statement(self):
        """Test get_balance returns zero balance for empty statement."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        balance = statement.get_balance()

        assert balance.ars_amount == Decimal("0")
        assert balance.usd_amount == Decimal("0")
        assert balance.is_zero() is True

    def test_get_transactions_by_currency(self):
        """Test filtering transactions by currency."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        ars_transaction = Transaction(
            date=date(2025, 6, 22),
            description="ARS Transaction",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        usd_transaction = Transaction(
            date=date(2025, 6, 23),
            description="USD Transaction",
            amount=Decimal("-50.25"),
            currency=Currency.USD,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        statement.add_transactions([ars_transaction, usd_transaction])

        ars_transactions = statement.get_transactions_by_currency(Currency.ARS)
        usd_transactions = statement.get_transactions_by_currency(Currency.USD)

        assert len(ars_transactions) == 1
        assert ars_transactions[0] == ars_transaction
        assert len(usd_transactions) == 1
        assert usd_transactions[0] == usd_transaction

    def test_get_transactions_by_date_range(self):
        """Test filtering transactions by date range."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        transactions = [
            Transaction(
                date=date(2025, 6, 20),
                description="Before range",
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 22),
                description="In range",
                amount=Decimal("200.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 25),
                description="After range",
                amount=Decimal("300.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
        ]

        statement.add_transactions(transactions)

        filtered_transactions = statement.get_transactions_by_date_range(
            start_date=date(2025, 6, 21),
            end_date=date(2025, 6, 24),
        )

        assert len(filtered_transactions) == 1
        assert filtered_transactions[0].description == "In range"

    def test_get_credit_and_debit_transactions(self):
        """Test filtering credit and debit transactions."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        credit_transaction = Transaction(
            date=date(2025, 6, 22),
            description="Credit",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        debit_transaction = Transaction(
            date=date(2025, 6, 23),
            description="Debit",
            amount=Decimal("-50.25"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        statement.add_transactions([credit_transaction, debit_transaction])

        credit_transactions = statement.get_credit_transactions()
        debit_transactions = statement.get_debit_transactions()

        assert len(credit_transactions) == 1
        assert credit_transactions[0] == credit_transaction
        assert len(debit_transactions) == 1
        assert debit_transactions[0] == debit_transaction

    def test_transaction_counting_methods(self):
        """Test transaction counting methods."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        transactions = [
            Transaction(
                date=date(2025, 6, 22),
                description="ARS Transaction 1",
                amount=Decimal("100.50"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 23),
                description="ARS Transaction 2",
                amount=Decimal("-50.25"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 24),
                description="USD Transaction",
                amount=Decimal("25.00"),
                currency=Currency.USD,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
        ]

        statement.add_transactions(transactions)

        assert statement.get_transaction_count() == 3
        assert statement.get_transaction_count_by_currency(Currency.ARS) == 2
        assert statement.get_transaction_count_by_currency(Currency.USD) == 1

    def test_is_empty(self):
        """Test is_empty method."""
        empty_statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        assert empty_statement.is_empty() is True

        non_empty_statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Test",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )
        non_empty_statement.add_transaction(transaction)
        assert non_empty_statement.is_empty() is False

    def test_get_date_range(self):
        """Test get_date_range method."""
        empty_statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        assert empty_statement.get_date_range() is None

        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        transactions = [
            Transaction(
                date=date(2025, 6, 25),
                description="Latest",
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 20),
                description="Earliest",
                amount=Decimal("200.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
            Transaction(
                date=date(2025, 6, 22),
                description="Middle",
                amount=Decimal("300.00"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            ),
        ]

        statement.add_transactions(transactions)
        date_range = statement.get_date_range()

        assert date_range == (date(2025, 6, 20), date(2025, 6, 25))

    def test_validate_balance_no_reported_balance(self):
        """Test validate_balance returns True when no reported balance."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Test",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )
        statement.add_transaction(transaction)

        assert statement.validate_balance() is True

    def test_validate_balance_matches_within_tolerance(self):
        """Test validate_balance returns True when balances match within tolerance."""
        reported_balance = Balance(
            ars_amount=Decimal("100.00"),
            usd_amount=Decimal("0"),
        )

        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA,
            reported_balance=reported_balance,
        )

        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Test",
            amount=Decimal("100.005"),  # Within default 0.01 tolerance
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        statement.add_transaction(transaction)

        assert statement.validate_balance() is True

    def test_validate_balance_exceeds_tolerance(self):
        """Test validate_balance returns False when difference exceeds tolerance."""
        reported_balance = Balance(
            ars_amount=Decimal("100.00"),
            usd_amount=Decimal("0"),
        )

        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA,
            reported_balance=reported_balance,
        )

        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Test",
            amount=Decimal("102.00"),  # Exceeds default 0.01 tolerance
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        statement.add_transaction(transaction)

        assert statement.validate_balance() is False

    def test_validate_balance_custom_tolerance(self):
        """Test validate_balance with custom tolerance."""
        reported_balance = Balance(
            ars_amount=Decimal("100.00"),
            usd_amount=Decimal("0"),
        )

        statement = Statement(
            payment_method=PaymentMethod.BBVA_VISA,
            reported_balance=reported_balance,
        )

        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Test",
            amount=Decimal("105.00"),  # 5.00 difference
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        statement.add_transaction(transaction)

        # Should fail with default tolerance
        assert statement.validate_balance() is False

        # Should pass with higher tolerance
        assert statement.validate_balance(tolerance=Decimal("10.00")) is True
