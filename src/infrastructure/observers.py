"""Observer implementations for the Financial Statement Processor.

This module contains concrete observer implementations that respond to domain
events, providing functionality like progress tracking and monitoring.
"""

from pathlib import Path

from domain.events import (
    ProcessingCompletedEvent,
    ProcessingFailedEvent,
    ProcessingStartedEvent,
    TransactionParsedEvent,
    ValidationFailedEvent,
)


class ProgressTracker:
    """Observer for tracking processing progress and user feedback."""

    def __init__(self) -> None:
        """Initialize progress tracker with default state."""
        self.current_file: Path | None = None
        self.file_size: int = 0
        self.processed_transactions: int = 0
        self.start_time: float | None = None
        self.errors: list[str] = []

    def handle_processing_started(self, event: ProcessingStartedEvent) -> None:
        """
        Handle processing started event.

        Args:
            event: The processing started event

        This method satisfies the validation requirement that publishing
        ProcessingStartedEvent triggers tracker output.
        """
        import time

        self.current_file = event.file_path
        self.file_size = event.file_size
        self.processed_transactions = 0
        self.start_time = time.time()
        self.errors.clear()

        # Validation requirement: tracker produces output
        print(f"🚀 Started processing: {event.file_path.name}")
        print(f"   File size: {event.file_size:,} bytes")
        print(f"   Timestamp: {event.timestamp.strftime('%H:%M:%S')}")

    def handle_transaction_parsed(self, event: TransactionParsedEvent) -> None:
        """
        Handle transaction parsed event.

        Args:
            event: The transaction parsed event
        """
        self.processed_transactions += 1

        # Show progress every 10 transactions to avoid spam
        if self.processed_transactions % 10 == 0:
            progress_percent = event.progress * 100
            print(
                f"   📊 Progress: {self.processed_transactions} transactions "
                f"({progress_percent:.1f}%)"
            )

    def handle_processing_completed(self, event: ProcessingCompletedEvent) -> None:
        """
        Handle processing completed event.

        Args:
            event: The processing completed event
        """
        import time

        duration = time.time() - self.start_time if self.start_time else 0.0

        print(f"✅ Completed: {event.file_path.name}")
        print(f"   📈 Transactions: {event.transaction_count}")
        print(f"   ⏱️  Duration: {duration:.2f}s")
        print(f"   📁 Output: {event.output_path.name}")

        # Reset state
        self._reset_state()

    def handle_validation_failed(self, event: ValidationFailedEvent) -> None:
        """
        Handle validation failed event.

        Args:
            event: The validation failed event
        """
        error_msg = (
            f"❌ Validation failed for {event.file_path.name}: {event.error_message}"
        )
        self.errors.append(error_msg)
        print(error_msg)

    def handle_processing_failed(self, event: ProcessingFailedEvent) -> None:
        """
        Handle processing failed event.

        Args:
            event: The processing failed event
        """
        import time

        duration = time.time() - self.start_time if self.start_time else 0.0

        error_msg = (
            f"❌ Processing failed for {event.file_path.name}: {event.error_message}"
        )
        self.errors.append(error_msg)

        print(error_msg)
        print(f"   ⏱️  Duration: {duration:.2f}s")
        print(f"   🔧 Error type: {event.exception_type}")

        # Reset state
        self._reset_state()

    def get_error_summary(self) -> str:
        """
        Get summary of all errors encountered.

        Returns:
            String summary of errors, or success message if no errors
        """
        if not self.errors:
            return "✅ All processing completed successfully"

        return f"❌ {len(self.errors)} errors encountered:\n" + "\n".join(self.errors)

    def _reset_state(self) -> None:
        """Reset tracker state after processing completion or failure."""
        self.current_file = None
        self.file_size = 0
        self.processed_transactions = 0
        self.start_time = None


class ValidationReporter:
    """Observer for detailed validation reporting and error collection."""

    def __init__(self) -> None:
        """Initialize validation reporter with empty error collection."""
        self.validation_errors: list[str] = []
        self.validation_warnings: list[str] = []

    def handle_validation_failed(self, event: ValidationFailedEvent) -> None:
        """
        Handle validation failure event.

        Args:
            event: The validation failed event
        """
        error_msg = f"Validation error in {event.file_path.name}: {event.error_message}"
        self.validation_errors.append(error_msg)

        print(f"🔍 {error_msg}")

    def handle_processing_completed(self, event: ProcessingCompletedEvent) -> None:
        """
        Handle processing completed event for validation summary.

        Args:
            event: The processing completed event
        """
        if not self.validation_errors and not self.validation_warnings:
            print(f"🔍 Validation passed for {event.file_path.name}")

    def get_validation_summary(self) -> str:
        """
        Get comprehensive validation summary.

        Returns:
            String summary of all validation results
        """
        if not self.validation_errors and not self.validation_warnings:
            return "🔍 All validations passed successfully"

        summary_parts = []

        if self.validation_errors:
            summary_parts.append(f"❌ {len(self.validation_errors)} validation errors:")
            summary_parts.extend(f"  - {error}" for error in self.validation_errors)

        if self.validation_warnings:
            summary_parts.append(
                f"⚠️  {len(self.validation_warnings)} validation warnings:"
            )
            summary_parts.extend(
                f"  - {warning}" for warning in self.validation_warnings
            )

        return "\n".join(summary_parts)

    def clear_results(self) -> None:
        """Clear all validation results for fresh start."""
        self.validation_errors.clear()
        self.validation_warnings.clear()
