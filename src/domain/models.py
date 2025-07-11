"""
Core domain models for the Financial Statement Processor.

This module contains the fundamental business entities and value objects that
form the foundation of the domain layer in our clean architecture
implementation.

Classes:
    Currency: Enumeration of supported currencies
    PaymentMethod: Enumeration of supported payment methods
    Transaction: Immutable transaction value object
    Balance: Immutable balance value object
    Statement: Statement aggregate root
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum


class Currency(Enum):
    """Enumeration of supported currencies."""

    ARS = "ARS"  # Argentine Peso
    USD = "USD"  # US Dollar

    def __str__(self) -> str:
        return self.value


class PaymentMethod(Enum):
    """Enumeration of supported payment methods."""

    MACRO_VISA = "Macro VISA"
    BBVA_VISA = "BBVA VISA"
    BBVA_MASTERCARD = "BBVA Mastercard"
    BBVA_ACCOUNT = "BBVA Account"
    MACRO_ACCOUNT = "Macro Account"
    MERCADOPAGO = "Mercadopago"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Transaction:
    """
    Immutable transaction value object.

    Represents a single financial transaction with all required attributes.
    Once created, the transaction cannot be modified (immutable).

    Attributes:
        date: Transaction date
        description: Transaction description
        amount: Transaction amount (positive or negative)
        currency: Transaction currency
        payment_method: Payment method used
        reference: Optional reference number
    """

    date: date
    description: str
    amount: Decimal
    currency: Currency
    payment_method: PaymentMethod
    reference: str | None = None

    def __post_init__(self) -> None:
        """Validate transaction data after initialization."""
        if not self.description or not self.description.strip():
            raise ValueError("Transaction description cannot be empty")

        if self.amount == Decimal("0"):
            raise ValueError("Transaction amount cannot be zero")

        # Validate that description is not just whitespace
        if not self.description.strip():
            raise ValueError("Transaction description cannot be only whitespace")

    def is_credit(self) -> bool:
        """Check if transaction is a credit (positive amount)."""
        return self.amount > Decimal("0")

    def is_debit(self) -> bool:
        """Check if transaction is a debit (negative amount)."""
        return self.amount < Decimal("0")

    def get_absolute_amount(self) -> Decimal:
        """Get the absolute value of the transaction amount."""
        return abs(self.amount)


@dataclass(frozen=True)
class Balance:
    """
    Immutable balance value object.

    Represents a balance with separate amounts for different currencies.
    Provides utility methods for balance calculations and comparisons.

    Attributes:
        ars_amount: Balance in Argentine Pesos
        usd_amount: Balance in US Dollars
    """

    ars_amount: Decimal
    usd_amount: Decimal

    def total_in_currency(self, currency: Currency) -> Decimal:
        """
        Get the total balance for a specific currency.

        Args:
            currency: The currency to get the balance for

        Returns:
            The balance amount for the specified currency
        """
        if currency == Currency.ARS:
            return self.ars_amount
        elif currency == Currency.USD:
            return self.usd_amount
        else:
            raise ValueError(f"Unsupported currency: {currency}")

    def is_zero(self) -> bool:
        """Check if both currency balances are zero."""
        return self.ars_amount == Decimal("0") and self.usd_amount == Decimal("0")

    def has_positive_balance(self) -> bool:
        """Check if any currency has a positive balance."""
        return self.ars_amount > Decimal("0") or self.usd_amount > Decimal("0")

    def has_negative_balance(self) -> bool:
        """Check if any currency has a negative balance."""
        return self.ars_amount < Decimal("0") or self.usd_amount < Decimal("0")


@dataclass
class Statement:
    """
    Statement aggregate root.

    Represents a financial statement containing multiple transactions.
    This is the main aggregate that manages transactions and enforces
    business rules and invariants.

    Attributes:
        payment_method: Payment method for this statement
        transactions: List of transactions in this statement
        reported_balance: Optional balance as reported by the institution
    """

    payment_method: PaymentMethod
    transactions: list[Transaction] = field(default_factory=list)
    reported_balance: Balance | None = None

    def add_transaction(self, transaction: Transaction) -> None:
        """
        Add a transaction to the statement.

        Args:
            transaction: The transaction to add

        Raises:
            ValueError: If transaction payment method doesn't match statement
        """
        if transaction.payment_method != self.payment_method:
            raise ValueError(
                f"Transaction payment method '{transaction.payment_method}' "
                f"does not match statement payment method "
                f"'{self.payment_method}'"
            )

        self.transactions.append(transaction)

    def add_transactions(self, transactions: list[Transaction]) -> None:
        """
        Add multiple transactions to the statement.

        Args:
            transactions: List of transactions to add

        Raises:
            ValueError: If any transaction payment method doesn't match
                statement
        """
        for transaction in transactions:
            self.add_transaction(transaction)

    def get_balance(self) -> Balance:
        """
        Calculate the current balance from all transactions.

        Returns:
            Balance object with totals for each currency
        """
        ars_total = Decimal("0")
        usd_total = Decimal("0")

        for transaction in self.transactions:
            if transaction.currency == Currency.ARS:
                ars_total += transaction.amount
            elif transaction.currency == Currency.USD:
                usd_total += transaction.amount

        return Balance(ars_amount=ars_total, usd_amount=usd_total)

    def get_transactions_by_currency(self, currency: Currency) -> list[Transaction]:
        """
        Get all transactions for a specific currency.

        Args:
            currency: The currency to filter by

        Returns:
            List of transactions in the specified currency
        """
        return [t for t in self.transactions if t.currency == currency]

    def get_transactions_by_date_range(
        self, start_date: date, end_date: date
    ) -> list[Transaction]:
        """
        Get transactions within a specific date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of transactions within the date range
        """
        return [t for t in self.transactions if start_date <= t.date <= end_date]

    def get_credit_transactions(self) -> list[Transaction]:
        """Get all credit transactions (positive amounts)."""
        return [t for t in self.transactions if t.is_credit()]

    def get_debit_transactions(self) -> list[Transaction]:
        """Get all debit transactions (negative amounts)."""
        return [t for t in self.transactions if t.is_debit()]

    def get_transaction_count(self) -> int:
        """Get the total number of transactions."""
        return len(self.transactions)

    def get_transaction_count_by_currency(self, currency: Currency) -> int:
        """
        Get the number of transactions for a specific currency.

        Args:
            currency: The currency to count transactions for

        Returns:
            Number of transactions in the specified currency
        """
        return len(self.get_transactions_by_currency(currency))

    def is_empty(self) -> bool:
        """Check if the statement has no transactions."""
        return len(self.transactions) == 0

    def get_date_range(self) -> tuple[date, date] | None:
        """
        Get the date range covered by transactions in this statement.

        Returns:
            Tuple of (earliest_date, latest_date) or None if no transactions
        """
        if not self.transactions:
            return None

        dates = [t.date for t in self.transactions]
        return (min(dates), max(dates))

    def validate_balance(self, tolerance: Decimal = Decimal("0.01")) -> bool:
        """
        Validate the calculated balance against the reported balance.

        Args:
            tolerance: Acceptable difference between calculated and reported
                balance

        Returns:
            True if balances match within tolerance, False otherwise
        """
        if self.reported_balance is None:
            return True  # No reported balance to validate against

        calculated_balance = self.get_balance()

        ars_diff = abs(calculated_balance.ars_amount - self.reported_balance.ars_amount)
        usd_diff = abs(calculated_balance.usd_amount - self.reported_balance.usd_amount)

        return ars_diff <= tolerance and usd_diff <= tolerance
