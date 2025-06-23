"""
Unit tests for domain builder classes.

This module tests the builder classes that construct domain objects,
ensuring they follow the Single Responsibility Principle and produce
objects equivalent to direct constructor usage.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from domain.builders import (
    ProcessingReport,
    ProcessingReportBuilder,
    StatementBuilder,
    TransactionBuilder,
)
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
        """Test builder equals direct constructor result (with transactions)."""
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

    def test_build_from_pdf_line_invalid_date_format(self, transaction_builder):
        """Test TransactionBuilder with invalid date format."""
        with pytest.raises(ValueError, match="Failed to build transaction"):
            transaction_builder.build_from_pdf_line(
                date_str="invalid-date",
                description="Test",
                amount_str="100,00",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_build_from_pdf_line_invalid_amount_format(self, transaction_builder):
        """Test TransactionBuilder with invalid amount format."""
        with pytest.raises(ValueError, match="Failed to build transaction"):
            transaction_builder.build_from_pdf_line(
                date_str="22.06.25",
                description="Test",
                amount_str="invalid-amount",
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA,
            )

    def test_build_from_pdf_line_whitespace_handling(self, transaction_builder):
        """Test TransactionBuilder handles whitespace correctly."""
        transaction = transaction_builder.build_from_pdf_line(
            date_str="  22.06.25  ",
            description="  Test Purchase  ",
            amount_str="  1.234,56  ",
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        assert transaction.date == date(2025, 6, 22)
        assert transaction.description == "Test Purchase"
        assert transaction.amount == Decimal("1234.56")

    def test_build_from_pdf_line_usd_currency(self, transaction_builder):
        """Test TransactionBuilder with USD currency."""
        transaction = transaction_builder.build_from_pdf_line(
            date_str="22.06.25",
            description="USD Purchase",
            amount_str="500,75",
            currency=Currency.USD,
            payment_method=PaymentMethod.MACRO_VISA,
        )

        assert transaction.currency == Currency.USD
        assert transaction.payment_method == PaymentMethod.MACRO_VISA
        assert transaction.amount == Decimal("500.75")


class TestProcessingReport:
    """Unit tests for ProcessingReport dataclass."""

    def test_processing_report_creation(self):
        """Test ProcessingReport creation with basic data."""
        successful_files = [Path("file1.pdf"), Path("file2.pdf")]
        failed_files = [(Path("file3.pdf"), "Parse error")]

        report = ProcessingReport(
            successful_files=successful_files,
            failed_files=failed_files,
            total_processing_time=10.5,
            total_transactions=100,
        )

        assert report.successful_files == successful_files
        assert report.failed_files == failed_files
        assert report.total_processing_time == 10.5
        assert report.total_transactions == 100

    def test_success_rate_calculation(self):
        """Test success rate calculation for various scenarios."""
        # 100% success rate
        report = ProcessingReport([Path("file1.pdf")], [])
        assert report.success_rate == 1.0

        # 0% success rate
        report = ProcessingReport([], [(Path("file1.pdf"), "error")])
        assert report.success_rate == 0.0

        # 50% success rate
        report = ProcessingReport([Path("file1.pdf")], [(Path("file2.pdf"), "error")])
        assert report.success_rate == 0.5

        # 75% success rate
        report = ProcessingReport(
            [Path("file1.pdf"), Path("file2.pdf"), Path("file3.pdf")],
            [(Path("file4.pdf"), "error")],
        )
        assert report.success_rate == 0.75

        # No files processed
        report = ProcessingReport([], [])
        assert report.success_rate == 0.0

    def test_total_files_property(self):
        """Test total_files property calculation."""
        report = ProcessingReport(
            [Path("file1.pdf"), Path("file2.pdf")],
            [(Path("file3.pdf"), "error"), (Path("file4.pdf"), "error")],
        )
        assert report.total_files == 4

        # Empty report
        report = ProcessingReport([], [])
        assert report.total_files == 0

    def test_print_summary_no_failures(self, capsys):
        """Test print_summary with no failed files."""
        report = ProcessingReport(
            [Path("file1.pdf"), Path("file2.pdf")],
            [],
            total_processing_time=5.25,
            total_transactions=50,
        )

        report.print_summary()
        captured = capsys.readouterr()

        assert "BATCH PROCESSING SUMMARY" in captured.out
        assert "✅ Successful files: 2" in captured.out
        assert "❌ Failed files: 0" in captured.out
        assert "📊 Success rate: 100.0%" in captured.out
        assert "📈 Total transactions: 50" in captured.out
        assert "⏱️  Processing time: 5.25s" in captured.out

    def test_print_summary_with_failures(self, capsys):
        """Test print_summary with failed files."""
        report = ProcessingReport(
            [Path("file1.pdf")],
            [(Path("file2.pdf"), "Parse error"), (Path("file3.pdf"), "IO error")],
            total_processing_time=3.75,
            total_transactions=25,
        )

        report.print_summary()
        captured = capsys.readouterr()

        assert "✅ Successful files: 1" in captured.out
        assert "❌ Failed files: 2" in captured.out
        assert "📊 Success rate: 33.3%" in captured.out
        assert "❌ Failed Files:" in captured.out
        assert "file2.pdf: Parse error" in captured.out
        assert "file3.pdf: IO error" in captured.out

    def test_processing_report_immutable(self):
        """Test that ProcessingReport is immutable (frozen dataclass)."""
        report = ProcessingReport([Path("file1.pdf")], [])

        with pytest.raises(AttributeError):
            report.successful_files = [Path("file2.pdf")]

        with pytest.raises(AttributeError):
            report.total_processing_time = 10.0


class TestProcessingReportBuilder:
    """Unit tests for ProcessingReportBuilder fluent interface."""

    def test_builder_basic_functionality(self):
        """Test basic ProcessingReportBuilder functionality."""
        builder = ProcessingReportBuilder()
        report = (
            builder.add_success(Path("file1.pdf"), 45)
            .add_failure(Path("file2.pdf"), "Parse error")
            .with_processing_time(12.5)
            .build()
        )

        assert len(report.successful_files) == 1
        assert report.successful_files[0] == Path("file1.pdf")
        assert len(report.failed_files) == 1
        assert report.failed_files[0] == (Path("file2.pdf"), "Parse error")
        assert report.total_processing_time == 12.5
        assert report.total_transactions == 45
        assert report.success_rate == 0.5

    def test_builder_multiple_successes(self):
        """Test adding multiple successful files."""
        builder = ProcessingReportBuilder()
        report = (
            builder.add_success(Path("file1.pdf"), 20)
            .add_success(Path("file2.pdf"), 30)
            .add_success(Path("file3.pdf"), 25)
            .build()
        )

        assert len(report.successful_files) == 3
        assert report.total_transactions == 75
        assert report.success_rate == 1.0

    def test_builder_multiple_failures(self):
        """Test adding multiple failed files."""
        builder = ProcessingReportBuilder()
        report = (
            builder.add_failure(Path("file1.pdf"), "Parse error")
            .add_failure(Path("file2.pdf"), "IO error")
            .add_failure(Path("file3.pdf"), "Corrupt file")
            .build()
        )

        assert len(report.failed_files) == 3
        assert report.success_rate == 0.0
        assert report.total_transactions == 0

    def test_builder_mixed_results(self):
        """Test builder with mixed success and failure results."""
        builder = ProcessingReportBuilder()
        report = (
            builder.add_success(Path("good1.pdf"), 40)
            .add_failure(Path("bad1.pdf"), "Error 1")
            .add_success(Path("good2.pdf"), 35)
            .add_failure(Path("bad2.pdf"), "Error 2")
            .add_success(Path("good3.pdf"), 50)
            .with_processing_time(25.75)
            .build()
        )

        assert len(report.successful_files) == 3
        assert len(report.failed_files) == 2
        assert report.total_transactions == 125
        assert report.success_rate == 0.6
        assert report.total_processing_time == 25.75

    def test_builder_reset_functionality(self):
        """Test builder reset and reuse."""
        builder = ProcessingReportBuilder()

        # Build first report
        report1 = (
            builder.add_success(Path("file1.pdf"), 20)
            .add_failure(Path("file2.pdf"), "Error")
            .build()
        )

        # Reset and build second report
        report2 = (
            builder.reset()
            .add_success(Path("file3.pdf"), 30)
            .add_success(Path("file4.pdf"), 40)
            .build()
        )

        # Validate reports are independent
        assert len(report1.successful_files) == 1
        assert len(report1.failed_files) == 1
        assert report1.total_transactions == 20

        assert len(report2.successful_files) == 2
        assert len(report2.failed_files) == 0
        assert report2.total_transactions == 70

    def test_builder_empty_report(self):
        """Test building an empty report."""
        builder = ProcessingReportBuilder()
        report = builder.build()

        assert len(report.successful_files) == 0
        assert len(report.failed_files) == 0
        assert report.total_transactions == 0
        assert report.total_processing_time == 0.0
        assert report.success_rate == 0.0

    def test_builder_fluent_interface_chaining(self):
        """Test fluent interface method chaining."""
        report = (
            ProcessingReportBuilder()
            .add_success(Path("file1.pdf"), 10)
            .add_success(Path("file2.pdf"), 20)
            .add_failure(Path("file3.pdf"), "Error message")
            .with_processing_time(15.5)
            .build()
        )

        assert report.success_rate == 2 / 3  # 2 successes, 1 failure
        assert report.total_transactions == 30
        assert report.total_processing_time == 15.5

    def test_builder_transaction_count_accumulation(self):
        """Test that transaction counts accumulate correctly."""
        builder = ProcessingReportBuilder()
        report = (
            builder.add_success(Path("file1.pdf"), 15)
            .add_success(Path("file2.pdf"), 25)
            .add_success(Path("file3.pdf"), 35)
            .add_failure(Path("file4.pdf"), "Error")  # No transactions
            .build()
        )

        assert report.total_transactions == 75  # 15 + 25 + 35
        assert len(report.successful_files) == 3
        assert len(report.failed_files) == 1

    def test_builder_default_transaction_count(self):
        """Test builder with default transaction count (0)."""
        builder = ProcessingReportBuilder()
        report = (
            builder.add_success(Path("file1.pdf"))  # No transaction count
            .add_success(Path("file2.pdf"), 20)
            .build()
        )

        assert report.total_transactions == 20  # 0 + 20
        assert len(report.successful_files) == 2
