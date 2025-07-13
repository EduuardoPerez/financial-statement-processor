"""
Unit tests for DuplicateDetector service.

This module tests the duplicate detection functionality for transactions.
"""

from datetime import date
from decimal import Decimal

from src.domain.models import Currency, PaymentMethod, Transaction
from src.domain.services import DuplicateDetector


class TestDuplicateDetector:
    """Test DuplicateDetector functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = DuplicateDetector()

        # Sample transactions for testing
        self.transaction1 = Transaction(
            date=date(2025, 1, 15),
            description="Test Transaction 1",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="REF001",
        )

        self.transaction2 = Transaction(
            date=date(2025, 1, 15),
            description="Test Transaction 2 - Different description",
            amount=Decimal("100.00"),  # Same amount and date as transaction1
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="REF002",
        )

        self.transaction3 = Transaction(
            date=date(2025, 1, 16),
            description="Test Transaction 3",
            amount=Decimal("100.00"),  # Same amount, different date
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="REF003",
        )

        self.transaction4 = Transaction(
            date=date(2025, 1, 15),
            description="Test Transaction 4",
            amount=Decimal("200.00"),  # Different amount, same date
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="REF004",
        )

    def test_mark_duplicates_empty_list(self):
        """Test marking duplicates with empty transaction list."""
        result_transactions, duplicate_count = self.detector.mark_duplicates([])

        assert result_transactions == []
        assert duplicate_count == 0

    def test_mark_duplicates_single_transaction(self):
        """Test marking duplicates with single transaction."""
        transactions = [self.transaction1]

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        assert len(result_transactions) == 1
        assert result_transactions[0] == self.transaction1
        assert duplicate_count == 0

    def test_mark_duplicates_no_duplicates(self):
        """Test marking duplicates when no duplicates exist."""
        transactions = [self.transaction1, self.transaction3, self.transaction4]

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        assert len(result_transactions) == 3
        assert duplicate_count == 0
        # Verify original transactions are unchanged
        for original, result in zip(transactions, result_transactions):
            assert original == result

    def test_mark_duplicates_with_duplicates(self):
        """Test marking duplicates when duplicates exist."""
        transactions = [self.transaction1, self.transaction2]  # Same date and amount

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        assert len(result_transactions) == 2
        assert duplicate_count == 1

        # First occurrence should be unchanged
        assert result_transactions[0] == self.transaction1

        # Second occurrence should be marked as duplicate
        assert result_transactions[1].date == self.transaction2.date
        assert result_transactions[1].amount == self.transaction2.amount
        assert result_transactions[1].currency == self.transaction2.currency
        assert result_transactions[1].payment_method == self.transaction2.payment_method
        assert result_transactions[1].reference == self.transaction2.reference
        assert (
            result_transactions[1].description
            == f"DUPLICATED: {self.transaction2.description}"
        )

    def test_mark_duplicates_multiple_groups(self):
        """Test marking duplicates with multiple duplicate groups."""
        # Create another pair of duplicates
        transaction5 = Transaction(
            date=date(2025, 1, 20),
            description="Transaction 5",
            amount=Decimal("300.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="REF005",
        )

        transaction6 = Transaction(
            date=date(2025, 1, 20),
            description="Transaction 6",
            amount=Decimal("300.00"),  # Same date and amount as transaction5
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="REF006",
        )

        transactions = [
            self.transaction1,
            self.transaction2,  # First duplicate group
            self.transaction3,  # No duplicate
            transaction5,
            transaction6,  # Second duplicate group
        ]

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        assert len(result_transactions) == 5
        assert duplicate_count == 2

        # Check that correct transactions are marked as duplicates
        duplicate_descriptions = [
            t.description
            for t in result_transactions
            if t.description.startswith("DUPLICATED:")
        ]
        assert len(duplicate_descriptions) == 2
        assert f"DUPLICATED: {self.transaction2.description}" in duplicate_descriptions
        assert f"DUPLICATED: {transaction6.description}" in duplicate_descriptions

    def test_mark_duplicates_three_identical_transactions(self):
        """Test marking duplicates with three identical transactions."""
        transaction_copy1 = Transaction(
            date=self.transaction1.date,
            description="Copy 1",
            amount=self.transaction1.amount,
            currency=self.transaction1.currency,
            payment_method=self.transaction1.payment_method,
            reference="COPY1",
        )

        transaction_copy2 = Transaction(
            date=self.transaction1.date,
            description="Copy 2",
            amount=self.transaction1.amount,
            currency=self.transaction1.currency,
            payment_method=self.transaction1.payment_method,
            reference="COPY2",
        )

        transactions = [self.transaction1, transaction_copy1, transaction_copy2]

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        assert len(result_transactions) == 3
        assert duplicate_count == 2

        # First transaction should be unchanged
        assert result_transactions[0] == self.transaction1

        # Second and third should be marked as duplicates
        assert result_transactions[1].description == "DUPLICATED: Copy 1"
        assert result_transactions[2].description == "DUPLICATED: Copy 2"

    def test_mark_duplicates_different_payment_methods_same_date_amount(self):
        """Test that transactions with different payment methods are still considered duplicates."""
        transaction_different_method = Transaction(
            date=self.transaction1.date,
            description="Different payment method",
            amount=self.transaction1.amount,
            currency=self.transaction1.currency,
            payment_method=PaymentMethod.BBVA_MASTERCARD,  # Different payment method
            reference="DIFF_METHOD",
        )

        transactions = [self.transaction1, transaction_different_method]

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        assert len(result_transactions) == 2
        assert duplicate_count == 1
        assert (
            result_transactions[1].description == "DUPLICATED: Different payment method"
        )

    def test_mark_duplicates_different_currencies_same_date_amount(self):
        """Test that transactions with different currencies are still considered duplicates."""
        transaction_different_currency = Transaction(
            date=self.transaction1.date,
            description="Different currency",
            amount=self.transaction1.amount,
            currency=Currency.USD,  # Different currency
            payment_method=self.transaction1.payment_method,
            reference="DIFF_CURR",
        )

        transactions = [self.transaction1, transaction_different_currency]

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        assert len(result_transactions) == 2
        assert duplicate_count == 1
        assert result_transactions[1].description == "DUPLICATED: Different currency"

    def test_mark_duplicates_negative_amounts(self):
        """Test marking duplicates with negative amounts."""
        transaction_negative1 = Transaction(
            date=date(2025, 1, 15),
            description="Negative transaction 1",
            amount=Decimal("-100.00"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="NEG1",
        )

        transaction_negative2 = Transaction(
            date=date(2025, 1, 15),
            description="Negative transaction 2",
            amount=Decimal("-100.00"),  # Same negative amount and date
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="NEG2",
        )

        transactions = [transaction_negative1, transaction_negative2]

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        assert len(result_transactions) == 2
        assert duplicate_count == 1
        assert (
            result_transactions[1].description == "DUPLICATED: Negative transaction 2"
        )

    def test_mark_duplicates_decimal_precision(self):
        """Test marking duplicates with high precision decimal amounts."""
        transaction_precise1 = Transaction(
            date=date(2025, 1, 15),
            description="Precise transaction 1",
            amount=Decimal("100.123456"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="PREC1",
        )

        transaction_precise2 = Transaction(
            date=date(2025, 1, 15),
            description="Precise transaction 2",
            amount=Decimal("100.123456"),  # Exact same precision
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
            reference="PREC2",
        )

        transactions = [transaction_precise1, transaction_precise2]

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        assert len(result_transactions) == 2
        assert duplicate_count == 1
        assert result_transactions[1].description == "DUPLICATED: Precise transaction 2"

    def test_create_duplicate_key(self):
        """Test _create_duplicate_key method."""
        key = self.detector._create_duplicate_key(self.transaction1)

        expected_key = (self.transaction1.date, self.transaction1.amount)
        assert key == expected_key

    def test_mark_as_duplicate(self):
        """Test _mark_as_duplicate method."""
        marked_transaction = self.detector._mark_as_duplicate(self.transaction1)

        assert marked_transaction.date == self.transaction1.date
        assert marked_transaction.amount == self.transaction1.amount
        assert marked_transaction.currency == self.transaction1.currency
        assert marked_transaction.payment_method == self.transaction1.payment_method
        assert marked_transaction.reference == self.transaction1.reference
        assert (
            marked_transaction.description
            == f"DUPLICATED: {self.transaction1.description}"
        )

    def test_mark_duplicates_preserves_transaction_immutability(self):
        """Test that marking duplicates doesn't modify original transactions."""
        original_description = self.transaction1.description
        transactions = [self.transaction1, self.transaction2]

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        # Original transaction should be unchanged
        assert self.transaction1.description == original_description
        assert self.transaction2.description != result_transactions[1].description

    def test_mark_duplicates_with_already_marked_duplicates(self):
        """Test behavior when transactions are already marked as duplicates."""
        already_marked = Transaction(
            date=self.transaction1.date,
            description="DUPLICATED: Already marked",
            amount=self.transaction1.amount,
            currency=self.transaction1.currency,
            payment_method=self.transaction1.payment_method,
            reference="ALREADY_MARKED",
        )

        transactions = [self.transaction1, already_marked]

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        assert len(result_transactions) == 2
        assert duplicate_count == 1
        assert (
            result_transactions[1].description
            == "DUPLICATED: DUPLICATED: Already marked"
        )

    def test_mark_duplicates_result_structure(self):
        """Test that the result has correct structure and duplicate marking."""
        transactions = [
            self.transaction3,  # Unique
            self.transaction1,  # First duplicate
            self.transaction4,  # Unique
            self.transaction2,  # Second duplicate (same as transaction1)
        ]

        result_transactions, duplicate_count = self.detector.mark_duplicates(
            transactions
        )

        assert len(result_transactions) == 4
        assert duplicate_count == 1

        # Check that all transactions are present
        descriptions = [t.description for t in result_transactions]
        assert self.transaction3.description in descriptions
        assert self.transaction1.description in descriptions
        assert self.transaction4.description in descriptions
        assert f"DUPLICATED: {self.transaction2.description}" in descriptions
