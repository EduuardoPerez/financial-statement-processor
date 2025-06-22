"""
Unit tests for domain builder classes.

This module tests the builder classes that construct domain objects,
ensuring they follow the Single Responsibility Principle and produce
objects equivalent to direct constructor usage.
"""

from datetime import date
from decimal import Decimal

import pytest

from domain.builders import StatementBuilder, TransactionBuilder
from domain.models import (
    Balance,
    Currency,
    PaymentMethod,
    Statement,
    Transaction,
)
from domain.utils import AmountParser, DateConverter


class TestStatementBuilder:
    """Unit tests for StatementBuilder fluent interface."""

    def test_builder_equals_direct_construction_minimal(self):
        """Test builder-produced statement equals direct constructor result (minimal)."""
        payment_method = PaymentMethod.BBVA_VISA

        # Build using StatementBuilder
        builder = StatementBuilder()
        built_statement = builder.with_payment_method(payment_method).build()

        # Create using direct constructor
        direct_statement = Statement(payment_method=payment_method)

        # Validate they are equivalent
        assert built_statement.payment_method == direct_statement.payment_method
        assert built_statement.transactions == direct_statement.transactions
        assert built_statement.reported_balance == direct_statement.reported_balance
        assert len(built_statement.transactions) == 0
        assert len(direct_statement.transactions) == 0

    def test_builder_equals_direct_construction_with_transactions(self):
        """Test builder-produced statement equals direct constructor result (with transactions)."""
        payment_method = PaymentMethod.MACRO_VISA
        transactions = [
            Transaction(
                date=date(2025, 6, 22),
                description="Test Transaction 1",
                amount=Decimal("100.50"),
                currency=Currency.ARS,
                payment_method=payment_method,
            ),
            Transaction(
                date=date(2025, 6, 23),
                description="Test Transaction 2",
                amount=Decimal("-50.25"),
                currency=Currency.USD,
                payment_method=payment_method,
            ),
        ]

        # Build using StatementBuilder
        builder = StatementBuilder()
        built_statement = (
            builder.with_payment_method(payment_method)
            .add_transactions(transactions)
            .build()
        )

        # Create using direct constructor
        direct_statement = Statement(
            payment_method=payment_method,
            transactions=transactions.copy(),
        )

        # Validate they are equivalent
        assert built_statement.payment_method == direct_statement.payment_method
        assert len(built_statement.transactions) == len(direct_statement.transactions)
        assert built_statement.transactions == direct_statement.transactions
        assert built_statement.reported_balance == direct_statement.reported_balance

    def test_builder_equals_direct_construction_with_balance(self):
        """Test builder-produced statement equals direct constructor result (with balance)."""
        payment_method = PaymentMethod.BBVA_MASTERCARD
        balance = Balance(Decimal("1000.00"), Decimal("100.00"))

        # Build using StatementBuilder
        builder = StatementBuilder()
        built_statement = (
            builder.with_payment_method(payment_method)
            .with_reported_balance(balance)
            .build()
        )

        # Create using direct constructor
        direct_statement = Statement(
            payment_method=payment_method,
            reported_balance=balance,
        )

        # Validate they are equivalent
        assert built_statement.payment_method == direct_statement.payment_method
        assert built_statement.transactions == direct_statement.transactions
        assert built_statement.reported_balance == direct_statement.reported_balance
        assert built_statement.reported_balance.ars_amount == Decimal("1000.00")
        assert built_statement.reported_balance.usd_amount == Decimal("100.00")

    def test_builder_equals_direct_construction_complete(self):
        """Test builder-produced statement equals direct constructor result (complete)."""
        payment_method = PaymentMethod.MERCADOPAGO
        transactions = [
            Transaction(
                date=date(2025, 6, 22),
                description="Complete Test Transaction",
                amount=Decimal("250.75"),
                currency=Currency.ARS,
                payment_method=payment_method,
            ),
        ]
        balance = Balance(Decimal("500.00"), Decimal("50.00"))

        # Build using StatementBuilder
        builder = StatementBuilder()
        built_statement = (
            builder.with_payment_method(payment_method)
            .add_transactions(transactions)
            .with_reported_balance(balance)
            .build()
        )

        # Create using direct constructor
        direct_statement = Statement(
            payment_method=payment_method,
            transactions=transactions.copy(),
            reported_balance=balance,
        )

        # Validate they are equivalent
        assert built_statement.payment_method == direct_statement.payment_method
        assert built_statement.transactions == direct_statement.transactions
        assert built_statement.reported_balance == direct_statement.reported_balance

        # Validate computed balances are the same
        assert (
            built_statement.get_balance().ars_amount
            == direct_statement.get_balance().ars_amount
        )
        assert (
            built_statement.get_balance().usd_amount
            == direct_statement.get_balance().usd_amount
        )

    def test_fluent_interface_chaining(self):
        """Test fluent interface method chaining works correctly."""
        payment_method = PaymentMethod.BBVA_ACCOUNT
        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Chaining Test",
            amount=Decimal("75.25"),
            currency=Currency.ARS,
            payment_method=payment_method,
        )
        balance = Balance(Decimal("200.00"), Decimal("20.00"))

        # Test method chaining
        statement = (
            StatementBuilder()
            .with_payment_method(payment_method)
            .add_transaction(transaction)
            .with_reported_balance(balance)
            .build()
        )

        assert statement.payment_method == payment_method
        assert len(statement.transactions) == 1
        assert statement.transactions[0] == transaction
        assert statement.reported_balance == balance

    def test_add_single_transaction(self):
        """Test adding a single transaction to the builder."""
        builder = StatementBuilder()
        payment_method = PaymentMethod.MACRO_ACCOUNT
        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Single Transaction",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=payment_method,
        )

        statement = (
            builder.with_payment_method(payment_method)
            .add_transaction(transaction)
            .build()
        )

        assert len(statement.transactions) == 1
        assert statement.transactions[0] == transaction

    def test_add_multiple_transactions_separately(self):
        """Test adding multiple transactions one by one."""
        builder = StatementBuilder()
        payment_method = PaymentMethod.BBVA_VISA

        transaction1 = Transaction(
            date=date(2025, 6, 22),
            description="Transaction 1",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=payment_method,
        )

        transaction2 = Transaction(
            date=date(2025, 6, 23),
            description="Transaction 2",
            amount=Decimal("200.00"),
            currency=Currency.USD,
            payment_method=payment_method,
        )

        statement = (
            builder.with_payment_method(payment_method)
            .add_transaction(transaction1)
            .add_transaction(transaction2)
            .build()
        )

        assert len(statement.transactions) == 2
        assert statement.transactions[0] == transaction1
        assert statement.transactions[1] == transaction2

    def test_add_transactions_list(self):
        """Test adding multiple transactions as a list."""
        builder = StatementBuilder()
        payment_method = PaymentMethod.MACRO_VISA

        transactions = [
            Transaction(
                date=date(2025, 6, 22),
                description="List Transaction 1",
                amount=Decimal("150.00"),
                currency=Currency.ARS,
                payment_method=payment_method,
            ),
            Transaction(
                date=date(2025, 6, 23),
                description="List Transaction 2",
                amount=Decimal("250.00"),
                currency=Currency.USD,
                payment_method=payment_method,
            ),
        ]

        statement = (
            builder.with_payment_method(payment_method)
            .add_transactions(transactions)
            .build()
        )

        assert len(statement.transactions) == 2
        assert statement.transactions == transactions

    def test_reset_functionality(self):
        """Test builder can be reset and reused."""
        builder = StatementBuilder()
        payment_method1 = PaymentMethod.BBVA_VISA
        payment_method2 = PaymentMethod.MACRO_VISA

        transaction1 = Transaction(
            date=date(2025, 6, 22),
            description="First Statement Transaction",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=payment_method1,
        )

        transaction2 = Transaction(
            date=date(2025, 6, 23),
            description="Second Statement Transaction",
            amount=Decimal("200.00"),
            currency=Currency.USD,
            payment_method=payment_method2,
        )

        # Build first statement
        statement1 = (
            builder.with_payment_method(payment_method1)
            .add_transaction(transaction1)
            .build()
        )

        # Reset and build second statement
        statement2 = (
            builder.reset()
            .with_payment_method(payment_method2)
            .add_transaction(transaction2)
            .build()
        )

        # Validate statements are different and correct
        assert statement1.payment_method == payment_method1
        assert len(statement1.transactions) == 1
        assert statement1.transactions[0] == transaction1

        assert statement2.payment_method == payment_method2
        assert len(statement2.transactions) == 1
        assert statement2.transactions[0] == transaction2

    def test_build_requires_payment_method(self):
        """Test that build() raises ValueError when payment method is not set."""
        builder = StatementBuilder()

        with pytest.raises(
            ValueError, match="Payment method is required to build Statement"
        ):
            builder.build()

    def test_transaction_list_isolation(self):
        """Test that builder creates independent transaction lists (no mutation)."""
        builder = StatementBuilder()
        payment_method = PaymentMethod.BBVA_MASTERCARD

        transaction = Transaction(
            date=date(2025, 6, 22),
            description="Isolation Test",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=payment_method,
        )

        # Build statement
        statement = (
            builder.with_payment_method(payment_method)
            .add_transaction(transaction)
            .build()
        )

        # Add more transactions to builder
        new_transaction = Transaction(
            date=date(2025, 6, 23),
            description="New Transaction",
            amount=Decimal("200.00"),
            currency=Currency.USD,
            payment_method=payment_method,
        )
        builder.add_transaction(new_transaction)

        # Original statement should be unchanged
        assert len(statement.transactions) == 1
        assert statement.transactions[0] == transaction

    def test_statement_validation_integration(self):
        """Test that builder integrates with Statement validation."""
        builder = StatementBuilder()
        payment_method = PaymentMethod.BBVA_VISA

        # Create transaction with mismatched payment method
        wrong_transaction = Transaction(
            date=date(2025, 6, 22),
            description="Wrong Payment Method",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.MACRO_VISA,  # Different from statement
        )

        # This should work during building (no validation yet)
        statement = (
            builder.with_payment_method(payment_method)
            .add_transaction(wrong_transaction)
            .build()
        )

        # But Statement should enforce validation when adding transactions
        with pytest.raises(ValueError, match="does not match statement payment method"):
            statement.add_transaction(wrong_transaction)


class TestTransactionBuilder:
    """Unit tests for TransactionBuilder (existing functionality)."""

    @pytest.fixture
    def transaction_builder(self):
        """Create TransactionBuilder with dependencies."""
        date_converter = DateConverter()
        amount_parser = AmountParser()
        return TransactionBuilder(date_converter, amount_parser)

    def test_build_from_pdf_line_basic(self, transaction_builder):
        """Test basic transaction building from PDF line components."""
        transaction = transaction_builder.build_from_pdf_line(
            date_str="22.06.25",
            description="Test Purchase",
            amount_str="1.234,56",
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        assert transaction.date == date(2025, 6, 22)
        assert transaction.description == "Test Purchase"
        assert transaction.amount == Decimal("1234.56")
        assert transaction.currency == Currency.ARS
        assert transaction.payment_method == PaymentMethod.BBVA_VISA

    def test_build_from_pdf_line_validation_errors(self, transaction_builder):
        """Test validation errors in TransactionBuilder."""
        # Empty date string
        with pytest.raises(ValueError, match="Date string cannot be empty"):
            transaction_builder.build_from_pdf_line(
                date_str="",
                description="Test",
                amount_str="100,00",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

        # Empty description
        with pytest.raises(ValueError, match="Description cannot be empty"):
            transaction_builder.build_from_pdf_line(
                date_str="22.06.25",
                description="",
                amount_str="100,00",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

        # Empty amount string
        with pytest.raises(ValueError, match="Amount string cannot be empty"):
            transaction_builder.build_from_pdf_line(
                date_str="22.06.25",
                description="Test",
                amount_str="",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )
