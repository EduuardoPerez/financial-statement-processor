"""Unit tests for infrastructure observers.

This module tests the concrete observer implementations that respond to domain
events for progress tracking and validation reporting.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from domain.events import (
    ProcessingCompletedEvent,
    ProcessingFailedEvent,
    ProcessingStartedEvent,
    TransactionParsedEvent,
    ValidationFailedEvent,
)
from domain.models import Currency, PaymentMethod, Transaction
from infrastructure.observers import ProgressTracker, ValidationReporter


class TestProgressTracker:
    """Test cases for ProgressTracker observer."""

    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initializes with default state."""
        tracker = ProgressTracker()

        assert tracker.current_file is None
        assert tracker.file_size == 0
        assert tracker.processed_transactions == 0
        assert tracker.start_time is None
        assert tracker.errors == []

    @patch("builtins.print")
    @patch("time.time", return_value=1000.0)
    def test_handle_processing_started(self, mock_time, mock_print):
        """Test handling processing started event produces output."""
        tracker = ProgressTracker()
        event = ProcessingStartedEvent(file_path=Path("test.pdf"), file_size=1024)

        tracker.handle_processing_started(event)

        # Verify state updates
        assert tracker.current_file == Path("test.pdf")
        assert tracker.file_size == 1024
        assert tracker.processed_transactions == 0
        assert tracker.start_time == 1000.0
        assert tracker.errors == []

        # Verify output (validation requirement)
        assert mock_print.call_count == 3
        mock_print.assert_any_call("🚀 Started processing: test.pdf")
        mock_print.assert_any_call("   File size: 1,024 bytes")

    @patch("builtins.print")
    def test_handle_transaction_parsed_progress_update(self, mock_print):
        """Test transaction parsed event updates progress."""
        tracker = ProgressTracker()
        transaction = Transaction(
            date=datetime.now().date(),
            description="Test transaction",
            amount=100.0,
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        # Process 10 transactions to trigger progress output
        for i in range(10):
            event = TransactionParsedEvent(
                transaction=transaction, progress=(i + 1) / 10.0
            )
            tracker.handle_transaction_parsed(event)

        assert tracker.processed_transactions == 10

        # Should print progress at 10th transaction
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "📊 Progress: 10 transactions" in call_args
        assert "(100.0%)" in call_args

    @patch("builtins.print")
    def test_handle_transaction_parsed_no_spam(self, mock_print):
        """Test transaction parsed doesn't spam output for every transaction."""
        tracker = ProgressTracker()
        transaction = Transaction(
            date=datetime.now().date(),
            description="Test transaction",
            amount=100.0,
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )

        # Process 5 transactions (less than 10)
        for i in range(5):
            event = TransactionParsedEvent(
                transaction=transaction, progress=(i + 1) / 10.0
            )
            tracker.handle_transaction_parsed(event)

        assert tracker.processed_transactions == 5

        # Should not print progress (less than 10 transactions)
        mock_print.assert_not_called()

    @patch("builtins.print")
    @patch("time.time", return_value=1002.5)
    def test_handle_processing_completed(self, mock_time, mock_print):
        """Test handling processing completed event."""
        tracker = ProgressTracker()
        tracker.start_time = 1000.0  # Set start time

        event = ProcessingCompletedEvent(
            file_path=Path("test.pdf"),
            output_path=Path("output.xlsx"),
            transaction_count=45,
            processing_time=2.5,
        )

        tracker.handle_processing_completed(event)

        # Verify state reset
        assert tracker.current_file is None
        assert tracker.file_size == 0
        assert tracker.processed_transactions == 0
        assert tracker.start_time is None

        # Verify output
        assert mock_print.call_count == 4
        mock_print.assert_any_call("✅ Completed: test.pdf")
        mock_print.assert_any_call("   📈 Transactions: 45")
        mock_print.assert_any_call("   ⏱️  Duration: 2.50s")
        mock_print.assert_any_call("   📁 Output: output.xlsx")

    @patch("builtins.print")
    def test_handle_validation_failed(self, mock_print):
        """Test handling validation failed event."""
        tracker = ProgressTracker()
        event = ValidationFailedEvent(
            file_path=Path("test.pdf"), error_message="Balance mismatch"
        )

        tracker.handle_validation_failed(event)

        # Verify error is recorded
        assert len(tracker.errors) == 1
        assert (
            "❌ Validation failed for test.pdf: Balance mismatch" in tracker.errors[0]
        )

        # Verify output
        mock_print.assert_called_once()

    @patch("builtins.print")
    @patch("time.time", return_value=1001.5)
    def test_handle_processing_failed(self, mock_time, mock_print):
        """Test handling processing failed event."""
        tracker = ProgressTracker()
        tracker.start_time = 1000.0  # Set start time

        event = ProcessingFailedEvent(
            file_path=Path("test.pdf"),
            error_message="File not found",
            exception_type="FileNotFoundError",
        )

        tracker.handle_processing_failed(event)

        # Verify error is recorded
        assert len(tracker.errors) == 1
        assert "❌ Processing failed for test.pdf: File not found" in tracker.errors[0]

        # Verify state reset
        assert tracker.current_file is None
        assert tracker.start_time is None

        # Verify output
        assert mock_print.call_count == 3
        mock_print.assert_any_call("   ⏱️  Duration: 1.50s")
        mock_print.assert_any_call("   🔧 Error type: FileNotFoundError")

    def test_get_error_summary_no_errors(self):
        """Test error summary when no errors occurred."""
        tracker = ProgressTracker()

        summary = tracker.get_error_summary()

        assert summary == "✅ All processing completed successfully"

    def test_get_error_summary_with_errors(self):
        """Test error summary when errors occurred."""
        tracker = ProgressTracker()
        tracker.errors = [
            "❌ Validation failed for file1.pdf: Balance mismatch",
            "❌ Processing failed for file2.pdf: File not found",
        ]

        summary = tracker.get_error_summary()

        assert "❌ 2 errors encountered:" in summary
        assert "Balance mismatch" in summary
        assert "File not found" in summary

    def test_validation_requirement_processing_started_triggers_output(self):
        """
        Test validation requirement: ProcessingStartedEvent triggers tracker output.

        This is the key validation requirement from the task.
        """
        with patch("builtins.print") as mock_print:
            tracker = ProgressTracker()
            event = ProcessingStartedEvent(file_path=Path("test.pdf"), file_size=1000)

            # This should trigger output (validation requirement)
            tracker.handle_processing_started(event)

            # Verify output was produced
            assert mock_print.called
            assert mock_print.call_count >= 1

            # Verify the output contains expected content
            calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("🚀 Started processing: test.pdf" in call for call in calls)


class TestValidationReporter:
    """Test cases for ValidationReporter observer."""

    def test_validation_reporter_initialization(self):
        """Test ValidationReporter initializes with empty collections."""
        reporter = ValidationReporter()

        assert reporter.validation_errors == []
        assert reporter.validation_warnings == []

    @patch("builtins.print")
    def test_handle_validation_failed(self, mock_print):
        """Test handling validation failed event."""
        reporter = ValidationReporter()
        event = ValidationFailedEvent(
            file_path=Path("test.pdf"), error_message="Balance mismatch detected"
        )

        reporter.handle_validation_failed(event)

        # Verify error is recorded
        assert len(reporter.validation_errors) == 1
        expected_error = "Validation error in test.pdf: Balance mismatch detected"
        assert reporter.validation_errors[0] == expected_error

        # Verify output
        mock_print.assert_called_once_with(f"🔍 {expected_error}")

    @patch("builtins.print")
    def test_handle_processing_completed_no_errors(self, mock_print):
        """Test processing completed with no validation errors."""
        reporter = ValidationReporter()
        event = ProcessingCompletedEvent(
            file_path=Path("test.pdf"),
            output_path=Path("output.xlsx"),
            transaction_count=45,
            processing_time=2.5,
        )

        reporter.handle_processing_completed(event)

        # Should print validation passed message
        mock_print.assert_called_once_with("🔍 Validation passed for test.pdf")

    @patch("builtins.print")
    def test_handle_processing_completed_with_errors(self, mock_print):
        """Test processing completed with validation errors."""
        reporter = ValidationReporter()
        reporter.validation_errors = ["Some validation error"]

        event = ProcessingCompletedEvent(
            file_path=Path("test.pdf"),
            output_path=Path("output.xlsx"),
            transaction_count=45,
            processing_time=2.5,
        )

        reporter.handle_processing_completed(event)

        # Should not print validation passed message
        mock_print.assert_not_called()

    def test_get_validation_summary_no_issues(self):
        """Test validation summary when no issues occurred."""
        reporter = ValidationReporter()

        summary = reporter.get_validation_summary()

        assert summary == "🔍 All validations passed successfully"

    def test_get_validation_summary_with_errors(self):
        """Test validation summary with errors."""
        reporter = ValidationReporter()
        reporter.validation_errors = ["Error 1", "Error 2"]

        summary = reporter.get_validation_summary()

        assert "❌ 2 validation errors:" in summary
        assert "  - Error 1" in summary
        assert "  - Error 2" in summary

    def test_get_validation_summary_with_warnings(self):
        """Test validation summary with warnings."""
        reporter = ValidationReporter()
        reporter.validation_warnings = ["Warning 1", "Warning 2"]

        summary = reporter.get_validation_summary()

        assert "⚠️  2 validation warnings:" in summary
        assert "  - Warning 1" in summary
        assert "  - Warning 2" in summary

    def test_get_validation_summary_with_errors_and_warnings(self):
        """Test validation summary with both errors and warnings."""
        reporter = ValidationReporter()
        reporter.validation_errors = ["Error 1"]
        reporter.validation_warnings = ["Warning 1"]

        summary = reporter.get_validation_summary()

        assert "❌ 1 validation errors:" in summary
        assert "⚠️  1 validation warnings:" in summary
        assert "  - Error 1" in summary
        assert "  - Warning 1" in summary

    def test_clear_results(self):
        """Test clearing validation results."""
        reporter = ValidationReporter()
        reporter.validation_errors = ["Error 1"]
        reporter.validation_warnings = ["Warning 1"]

        reporter.clear_results()

        assert reporter.validation_errors == []
        assert reporter.validation_warnings == []
