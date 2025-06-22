"""Domain validation services for financial statements."""

from dataclasses import dataclass, field
from decimal import Decimal

from .models import Statement


@dataclass
class ValidationResult:
    """Result of statement validation with errors and warnings."""

    is_valid: bool
    errors: list[str]
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message and mark validation as invalid."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message without affecting validity."""
        self.warnings.append(message)


class StatementValidator:
    """Domain service for validating financial statements."""

    def __init__(self, balance_tolerance: Decimal = Decimal("0.01")):
        """
        Initialize validator with configurable balance tolerance.

        Args:
            balance_tolerance: Maximum allowed difference for balance
                validation
        """
        self._balance_tolerance = balance_tolerance

    def validate(self, statement: Statement) -> ValidationResult:
        """
        Validate a financial statement for consistency and correctness.

        Args:
            statement: The statement to validate

        Returns:
            ValidationResult indicating if statement is valid with any
            errors/warnings

        Example:
            >>> validator = StatementValidator()
            >>> result = validator.validate(statement)
            >>> if not result.is_valid:
            ...     print(f"Validation failed: {result.errors}")
        """
        if not statement:
            return ValidationResult(is_valid=False, errors=["Statement cannot be None"])

        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Validate basic statement structure
        self._validate_basic_structure(statement, result)

        # Validate balance consistency if reported balance is available
        if statement.reported_balance is not None:
            self._validate_balance_consistency(statement, result)
        else:
            result.add_warning("No reported balance available for validation")

        # Validate transactions
        self._validate_transactions(statement, result)

        return result

    def _validate_basic_structure(
        self, statement: Statement, result: ValidationResult
    ) -> None:
        """Validate basic statement structure and required fields."""
        if not statement.payment_method:
            result.add_error("Statement must have a payment method")

        has_transactions = hasattr(statement, "transactions")
        if not has_transactions or statement.transactions is None:
            result.add_error("Statement must have a transactions list")
            return

        if len(statement.transactions) == 0:
            result.add_warning("Statement has no transactions")

    def _validate_balance_consistency(
        self, statement: Statement, result: ValidationResult
    ) -> None:
        """
        Validate that computed balance matches reported balance.

        Core requirement: balance mismatches set is_valid to False.
        """
        computed_balance = statement.get_balance()
        reported_balance = statement.reported_balance

        # Validate ARS balance
        reported_ars = reported_balance.ars_amount  # type: ignore[union-attr]
        computed_ars = computed_balance.ars_amount
        ars_diff = abs(reported_ars - computed_ars)
        if ars_diff >= self._balance_tolerance:
            result.add_error(
                f"ARS balance mismatch: reported "
                f"{reported_ars}, computed "
                f"{computed_ars}, difference {ars_diff}"
            )

        # Validate USD balance
        reported_usd = reported_balance.usd_amount  # type: ignore[union-attr]
        computed_usd = computed_balance.usd_amount
        usd_diff = abs(reported_usd - computed_usd)
        if usd_diff >= self._balance_tolerance:
            result.add_error(
                f"USD balance mismatch: reported "
                f"{reported_usd}, computed "
                f"{computed_usd}, difference {usd_diff}"
            )

    def _validate_transactions(
        self, statement: Statement, result: ValidationResult
    ) -> None:
        """Validate individual transactions for consistency."""
        # Check if transactions attribute exists
        if not hasattr(statement, "transactions"):
            return  # Error already added in basic structure validation

        if not statement.transactions:
            return

        for i, transaction in enumerate(statement.transactions):
            # Note: Transaction payment method validation is handled by
            # Statement.add_transaction() in the domain model
            # Note: Empty description and zero amount validation is handled by
            # Transaction.__post_init__() in the domain model

            # Additional validation can be added here if needed
            pass


__all__ = ["ValidationResult", "StatementValidator"]
