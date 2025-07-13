"""Domain validation services for financial statements."""

from dataclasses import dataclass, field
from decimal import Decimal

from infrastructure.extractors import BalanceExtractionService

from .models import Currency, Statement


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


@dataclass
class EnhancedValidationResult(ValidationResult):
    """Enhanced validation result with detailed balance information."""

    reported_ars: Decimal | None = None
    reported_usd: Decimal | None = None
    computed_ars: Decimal | None = None
    computed_usd: Decimal | None = None
    ars_difference: Decimal | None = None
    usd_difference: Decimal | None = None
    transaction_count: int = 0
    payment_method: str | None = None

    def print_detailed_summary(self, filename: str) -> None:
        """Print detailed validation summary with legacy script formatting."""
        print(f"\n{'=' * 60}")
        print(f"VALIDATION SUMMARY: {filename}")
        print(f"{'=' * 60}")
        print(f"Transactions Processed: {self.transaction_count}")
        print(f"Payment Method: {self.payment_method}")

        if self.reported_ars is not None and self.computed_ars is not None:
            print("\nBALANCE VALIDATION:")
            print(f"  Reported ARS: {self.reported_ars:,.2f}")
            print(f"  Computed ARS: {self.computed_ars:,.2f}")
            ars_diff = abs(
                self.ars_difference if self.ars_difference is not None else Decimal("0")
            )
            tolerance = Decimal("0.01")
            ars_match = "✅ YES" if ars_diff < tolerance else "❌ NO"
            print(f"  ARS Match: {ars_match}")

            print(f"  Reported USD: {self.reported_usd:,.2f}")
            print(f"  Computed USD: {self.computed_usd:,.2f}")
            usd_diff = abs(
                self.usd_difference if self.usd_difference is not None else Decimal("0")
            )
            usd_match = "✅ YES" if usd_diff < tolerance else "❌ NO"
            print(f"  USD Match: {usd_match}")

        if not self.is_valid:
            print("\n❌ VALIDATION ERRORS:")
            for error in self.errors:
                print(f"   • {error}")

        if self.warnings:
            print("\n⚠️  VALIDATION WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")


class StatementValidator:
    """Domain service for validating financial statements."""

    def __init__(
        self,
        balance_tolerance: Decimal = Decimal("0.01"),
        balance_extraction_service: BalanceExtractionService | None = None,
    ):
        """
        Initialize validator with configurable balance tolerance.

        Args:
            balance_tolerance: Maximum difference for balance validation
            balance_extraction_service: Service for extracting balances
        """
        self._balance_tolerance = balance_tolerance
        self._balance_service = balance_extraction_service

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
            self._validate_balance_with_payment_exclusion(statement, result)
        else:
            result.add_warning("No reported balance available for validation")

        # Validate transactions
        self._validate_transactions(statement, result)

        return result

    def validate_with_content(
        self, statement: Statement, raw_content: str
    ) -> ValidationResult:
        """Validate statement with raw content for balance extraction."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Basic validation
        self._validate_basic_structure(statement, result)

        # Extract balance from content if service available
        if self._balance_service and raw_content:
            extracted_balance = self._balance_service.extract_balance(
                raw_content, statement.payment_method
            )
            if extracted_balance:
                # Create Balance object and set on statement
                from .models import Balance

                reported_balance = Balance(
                    ars_amount=extracted_balance["ars"],
                    usd_amount=extracted_balance["usd"],
                )
                # Set on statement (mutable field)
                statement.reported_balance = reported_balance

        # Validate balance with payment exclusion
        if statement.reported_balance:
            self._validate_balance_with_payment_exclusion(statement, result)
        else:
            result.add_warning("No reported balance available for validation")

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

    def _validate_balance_with_payment_exclusion(
        self, statement: Statement, result: ValidationResult
    ) -> None:
        """Validate balance excluding payment transactions."""
        # Calculate computed balance excluding payments
        computed_balance = self._calculate_balance_excluding_payments(statement)
        reported_balance = statement.reported_balance

        # Ensure reported_balance is not None (should be checked by caller)
        if reported_balance is None:
            result.add_error("No reported balance available for validation")
            return

        # Validate ARS balance
        reported_ars = reported_balance.ars_amount
        computed_ars = computed_balance["ars"]
        ars_diff = abs(reported_ars - computed_ars)

        if ars_diff >= self._balance_tolerance:
            result.add_error(
                f"ARS balance mismatch: reported {reported_ars:,.2f}, "
                f"computed {computed_ars:,.2f}, difference {ars_diff:.2f}"
            )

        # Validate USD balance
        reported_usd = reported_balance.usd_amount
        computed_usd = computed_balance["usd"]
        usd_diff = abs(reported_usd - computed_usd)

        if usd_diff >= self._balance_tolerance:
            result.add_error(
                f"USD balance mismatch: reported {reported_usd:,.2f}, "
                f"computed {computed_usd:,.2f}, difference {usd_diff:.2f}"
            )

    def _calculate_balance_excluding_payments(
        self, statement: Statement
    ) -> dict[str, Decimal]:
        """Calculate balance excluding payment transactions."""
        ars_total = Decimal("0.0")
        usd_total = Decimal("0.0")

        # Payment transaction identifiers
        payment_descriptions = {"SU PAGO EN PESOS", "SU PAGO EN USD"}

        for transaction in statement.transactions:
            # Skip payment transactions
            if transaction.description in payment_descriptions:
                continue

            if transaction.currency == Currency.ARS:
                ars_total += transaction.amount
            elif transaction.currency == Currency.USD:
                usd_total += transaction.amount

        return {"ars": ars_total, "usd": usd_total}

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
