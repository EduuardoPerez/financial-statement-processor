"""Unit tests for domain validation services."""

from datetime import date
from decimal import Decimal

import pytest

from domain.models import Balance, Currency, PaymentMethod, Statement, Transaction
from domain.validation import StatementValidator, ValidationResult


class TestValidationResult:
    """Unit tests for ValidationResult class."""

    def test_validation_result_creation(self):
        """Test ValidationResult creation with basic parameters."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_add_error_marks_invalid(self):
        """Test that adding an error marks validation as invalid."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        result.add_error("Test error")

        assert result.is_valid is False
        assert "Test error" in result.errors

    def test_add_warning_preserves_validity(self):
        """Test that adding a warning doesn't affect validity."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        result.add_warning("Test warning")

        assert result.is_valid is True
        assert "Test warning" in result.warnings

    def test_multiple_errors_and_warnings(self):
        """Test handling multiple errors and warnings."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        result.add_error("Error 1")
        result.add_error("Error 2")
        result.add_warning("Warning 1")
        result.add_warning("Warning 2")

        assert result.is_valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 2
        assert "Error 1" in result.errors
        assert "Error 2" in result.errors
        assert "Warning 1" in result.warnings
        assert "Warning 2" in result.warnings


class TestStatementValidator:
    """Unit tests for StatementValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a StatementValidator instance for testing."""
        return StatementValidator()

    @pytest.fixture
    def valid_transaction(self):
        """Create a valid transaction for testing."""
        return Transaction(
            date=date(2025, 1, 15),
            description="Test Purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

    @pytest.fixture
    def valid_statement(self, valid_transaction):
        """Create a valid statement for testing."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        statement.add_transaction(valid_transaction)
        statement.reported_balance = Balance(
            ars_amount=Decimal("100.50"), usd_amount=Decimal("0.00")
        )
        return statement

    def test_validate_none_statement(self, validator):
        """Test validation of None statement."""
        result = validator.validate(None)

        assert result.is_valid is False
        assert "Statement cannot be None" in result.errors

    def test_validate_valid_statement(self, validator, valid_statement):
        """Test validation of a valid statement."""
        result = validator.validate(valid_statement)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_statement_without_payment_method(self, validator):
        """Test validation of statement without payment method."""
        statement = Statement(payment_method=None)

        result = validator.validate(statement)

        assert result.is_valid is False
        assert "Statement must have a payment method" in result.errors

    def test_validate_statement_without_transactions_list(self, validator):
        """Test validation of statement without transactions attribute."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        # Remove transactions attribute to simulate malformed statement
        delattr(statement, "transactions")

        result = validator.validate(statement)

        assert result.is_valid is False
        assert "Statement must have a transactions list" in result.errors

    def test_validate_statement_with_empty_transactions(self, validator):
        """Test validation of statement with no transactions."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        result = validator.validate(statement)

        assert result.is_valid is True  # Empty transactions is just a warning
        assert "Statement has no transactions" in result.warnings

    def test_validate_statement_without_reported_balance(
        self, validator, valid_transaction
    ):
        """Test validation of statement without reported balance."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        statement.add_transaction(valid_transaction)

        result = validator.validate(statement)

        assert result.is_valid is True
        assert "No reported balance available for validation" in result.warnings

    def test_validate_balance_consistency_ars_mismatch(
        self, validator, valid_transaction
    ):
        """Test validation with ARS balance mismatch."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        statement.add_transaction(valid_transaction)  # Amount: 100.50 ARS
        statement.reported_balance = Balance(
            ars_amount=Decimal("200.00"),
            usd_amount=Decimal("0.00"),  # Mismatch
        )

        result = validator.validate(statement)

        assert result.is_valid is False
        assert any("ARS balance mismatch" in error for error in result.errors)

    def test_validate_balance_consistency_usd_mismatch(self, validator):
        """Test validation with USD balance mismatch."""
        usd_transaction = Transaction(
            date=date(2025, 1, 15),
            description="USD Purchase",
            amount=Decimal("50.00"),
            currency=Currency.USD,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        statement.add_transaction(usd_transaction)
        statement.reported_balance = Balance(
            ars_amount=Decimal("0.00"),
            usd_amount=Decimal("100.00"),  # Mismatch
        )

        result = validator.validate(statement)

        assert result.is_valid is False
        assert any("USD balance mismatch" in error for error in result.errors)

    def test_validate_balance_consistency_both_mismatch(self, validator):
        """Test validation with both ARS and USD balance mismatches."""
        ars_transaction = Transaction(
            date=date(2025, 1, 15),
            description="ARS Purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )
        usd_transaction = Transaction(
            date=date(2025, 1, 16),
            description="USD Purchase",
            amount=Decimal("50.00"),
            currency=Currency.USD,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        statement.add_transaction(ars_transaction)
        statement.add_transaction(usd_transaction)
        statement.reported_balance = Balance(
            ars_amount=Decimal("200.00"),  # Mismatch
            usd_amount=Decimal("100.00"),  # Mismatch
        )

        result = validator.validate(statement)

        assert result.is_valid is False
        assert any("ARS balance mismatch" in error for error in result.errors)
        assert any("USD balance mismatch" in error for error in result.errors)

    def test_validate_balance_within_tolerance(self, validator, valid_transaction):
        """Test validation with balance difference within tolerance."""
        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        statement.add_transaction(valid_transaction)  # Amount: 100.50 ARS
        statement.reported_balance = Balance(
            ars_amount=Decimal("100.505"),  # Within 0.01 tolerance
            usd_amount=Decimal("0.00"),
        )

        result = validator.validate(statement)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_transaction_payment_method_mismatch(self, validator):
        """Test that domain model prevents payment method mismatches."""
        transaction = Transaction(
            date=date(2025, 1, 15),
            description="Test Purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.MACRO_VISA,  # Different from statement
        )

        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)

        # Domain model should prevent adding mismatched transactions
        with pytest.raises(ValueError, match="payment method"):
            statement.add_transaction(transaction)

    def test_validate_transaction_empty_description(self, validator):
        """Test that domain model prevents empty descriptions."""
        # Domain model should prevent creating transactions with empty descriptions
        with pytest.raises(ValueError, match="description cannot be empty"):
            Transaction(
                date=date(2025, 1, 15),
                description="",  # Empty description
                amount=Decimal("100.50"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_validate_transaction_zero_amount(self, validator):
        """Test that domain model prevents zero amounts."""
        # Domain model should prevent creating transactions with zero amounts
        with pytest.raises(ValueError, match="amount cannot be zero"):
            Transaction(
                date=date(2025, 1, 15),
                description="Zero Amount Transaction",
                amount=Decimal("0.00"),  # Zero amount
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_custom_balance_tolerance(self):
        """Test validator with custom balance tolerance."""
        validator = StatementValidator(balance_tolerance=Decimal("0.10"))

        transaction = Transaction(
            date=date(2025, 1, 15),
            description="Test Purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        statement.add_transaction(transaction)
        statement.reported_balance = Balance(
            ars_amount=Decimal("100.55"),  # 0.05 difference, within 0.10 tolerance
            usd_amount=Decimal("0.00"),
        )

        result = validator.validate(statement)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_balance_tolerance_exceeded(self):
        """Test validator when balance difference exceeds tolerance."""
        validator = StatementValidator(balance_tolerance=Decimal("0.10"))

        transaction = Transaction(
            date=date(2025, 1, 15),
            description="Test Purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
        statement.add_transaction(transaction)
        statement.reported_balance = Balance(
            ars_amount=Decimal("100.70"),  # 0.20 difference, exceeds 0.10 tolerance
            usd_amount=Decimal("0.00"),
        )

        result = validator.validate(statement)

        assert result.is_valid is False
        assert any("ARS balance mismatch" in error for error in result.errors)
