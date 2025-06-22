"""Unit tests for domain events and event publisher.

This module tests the Observer pattern implementation for event-driven
architecture in the Financial Statement Processor.
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from domain.events import (
    Event,
    EventPublisher,
    ProcessingCompletedEvent,
    ProcessingFailedEvent,
    ProcessingStartedEvent,
    TransactionParsedEvent,
    ValidationFailedEvent,
)
from domain.models import Currency, PaymentMethod, Transaction


class TestEvent:
    """Test cases for Event base class."""

    def test_event_has_timestamp(self):
        """Test that events are created with timestamps."""
        # Create a concrete event for testing
        event = ProcessingStartedEvent(file_path=Path("test.pdf"), file_size=1000)

        assert hasattr(event, "timestamp")
        assert isinstance(event.timestamp, datetime)

    def test_event_timestamp_is_recent(self):
        """Test that event timestamp is close to current time."""
        before = datetime.now()
        event = ProcessingStartedEvent(file_path=Path("test.pdf"), file_size=1000)
        after = datetime.now()

        assert before <= event.timestamp <= after


class TestProcessingStartedEvent:
    """Test cases for ProcessingStartedEvent."""

    def test_processing_started_event_creation(self):
        """Test ProcessingStartedEvent creation with required fields."""
        file_path = Path("test.pdf")
        file_size = 1024

        event = ProcessingStartedEvent(file_path=file_path, file_size=file_size)

        assert event.file_path == file_path
        assert event.file_size == file_size
        assert isinstance(event.timestamp, datetime)

    def test_processing_started_event_inheritance(self):
        """Test that ProcessingStartedEvent inherits from Event."""
        event = ProcessingStartedEvent(file_path=Path("test.pdf"), file_size=1000)

        assert isinstance(event, Event)


class TestTransactionParsedEvent:
    """Test cases for TransactionParsedEvent."""

    def test_transaction_parsed_event_creation(self):
        """Test TransactionParsedEvent creation with transaction and progress."""
        transaction = Transaction(
            date=datetime.now().date(),
            description="Test transaction",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA,
        )
        progress = 0.5

        event = TransactionParsedEvent(transaction=transaction, progress=progress)

        assert event.transaction == transaction
        assert event.progress == progress
        assert isinstance(event.timestamp, datetime)


class TestProcessingCompletedEvent:
    """Test cases for ProcessingCompletedEvent."""

    def test_processing_completed_event_creation(self):
        """Test ProcessingCompletedEvent creation with all fields."""
        file_path = Path("input.pdf")
        output_path = Path("output.xlsx")
        transaction_count = 45
        processing_time = 2.5

        event = ProcessingCompletedEvent(
            file_path=file_path,
            output_path=output_path,
            transaction_count=transaction_count,
            processing_time=processing_time,
        )

        assert event.file_path == file_path
        assert event.output_path == output_path
        assert event.transaction_count == transaction_count
        assert event.processing_time == processing_time


class TestValidationFailedEvent:
    """Test cases for ValidationFailedEvent."""

    def test_validation_failed_event_creation(self):
        """Test ValidationFailedEvent creation with error message."""
        file_path = Path("test.pdf")
        error_message = "Balance mismatch detected"

        event = ValidationFailedEvent(file_path=file_path, error_message=error_message)

        assert event.file_path == file_path
        assert event.error_message == error_message


class TestProcessingFailedEvent:
    """Test cases for ProcessingFailedEvent."""

    def test_processing_failed_event_creation(self):
        """Test ProcessingFailedEvent creation with all error details."""
        file_path = Path("test.pdf")
        error_message = "File not found"
        exception_type = "FileNotFoundError"

        event = ProcessingFailedEvent(
            file_path=file_path,
            error_message=error_message,
            exception_type=exception_type,
        )

        assert event.file_path == file_path
        assert event.error_message == error_message
        assert event.exception_type == exception_type


class TestEventPublisher:
    """Test cases for EventPublisher."""

    def test_event_publisher_initialization(self):
        """Test EventPublisher initializes with empty subscribers."""
        publisher = EventPublisher()

        assert publisher.get_subscriber_count(ProcessingStartedEvent) == 0

    def test_subscribe_to_event_type(self):
        """Test subscribing to specific event type."""
        publisher = EventPublisher()
        handler = Mock()

        publisher.subscribe(ProcessingStartedEvent, handler)

        assert publisher.get_subscriber_count(ProcessingStartedEvent) == 1

    def test_subscribe_multiple_handlers(self):
        """Test subscribing multiple handlers to same event type."""
        publisher = EventPublisher()
        handler1 = Mock()
        handler2 = Mock()

        publisher.subscribe(ProcessingStartedEvent, handler1)
        publisher.subscribe(ProcessingStartedEvent, handler2)

        assert publisher.get_subscriber_count(ProcessingStartedEvent) == 2

    def test_publish_event_calls_subscribers(self):
        """Test publishing event calls all subscribed handlers."""
        publisher = EventPublisher()
        handler1 = Mock()
        handler2 = Mock()

        publisher.subscribe(ProcessingStartedEvent, handler1)
        publisher.subscribe(ProcessingStartedEvent, handler2)

        event = ProcessingStartedEvent(file_path=Path("test.pdf"), file_size=1000)

        publisher.publish(event)

        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)

    def test_publish_event_only_calls_matching_subscribers(self):
        """Test publishing event only calls handlers for that event type."""
        publisher = EventPublisher()
        started_handler = Mock()
        completed_handler = Mock()

        publisher.subscribe(ProcessingStartedEvent, started_handler)
        publisher.subscribe(ProcessingCompletedEvent, completed_handler)

        event = ProcessingStartedEvent(file_path=Path("test.pdf"), file_size=1000)

        publisher.publish(event)

        started_handler.assert_called_once_with(event)
        completed_handler.assert_not_called()

    def test_unsubscribe_handler(self):
        """Test unsubscribing handler from event type."""
        publisher = EventPublisher()
        handler = Mock()

        publisher.subscribe(ProcessingStartedEvent, handler)
        assert publisher.get_subscriber_count(ProcessingStartedEvent) == 1

        publisher.unsubscribe(ProcessingStartedEvent, handler)
        assert publisher.get_subscriber_count(ProcessingStartedEvent) == 0

    def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing handler that was never subscribed."""
        publisher = EventPublisher()
        handler = Mock()

        # Should not raise exception
        publisher.unsubscribe(ProcessingStartedEvent, handler)
        assert publisher.get_subscriber_count(ProcessingStartedEvent) == 0

    def test_clear_subscribers_for_event_type(self):
        """Test clearing all subscribers for specific event type."""
        publisher = EventPublisher()
        handler1 = Mock()
        handler2 = Mock()

        publisher.subscribe(ProcessingStartedEvent, handler1)
        publisher.subscribe(ProcessingStartedEvent, handler2)
        publisher.subscribe(ProcessingCompletedEvent, handler1)

        publisher.clear_subscribers(ProcessingStartedEvent)

        assert publisher.get_subscriber_count(ProcessingStartedEvent) == 0
        assert publisher.get_subscriber_count(ProcessingCompletedEvent) == 1

    def test_clear_all_subscribers(self):
        """Test clearing all subscribers for all event types."""
        publisher = EventPublisher()
        handler = Mock()

        publisher.subscribe(ProcessingStartedEvent, handler)
        publisher.subscribe(ProcessingCompletedEvent, handler)

        publisher.clear_subscribers()

        assert publisher.get_subscriber_count(ProcessingStartedEvent) == 0
        assert publisher.get_subscriber_count(ProcessingCompletedEvent) == 0

    def test_publish_with_handler_exception(self):
        """Test that handler exceptions don't stop other handlers."""
        publisher = EventPublisher()
        failing_handler = Mock(side_effect=Exception("Handler error"))
        working_handler = Mock()

        publisher.subscribe(ProcessingStartedEvent, failing_handler)
        publisher.subscribe(ProcessingStartedEvent, working_handler)

        event = ProcessingStartedEvent(file_path=Path("test.pdf"), file_size=1000)

        # Should not raise exception
        publisher.publish(event)

        # Both handlers should be called despite first one failing
        failing_handler.assert_called_once_with(event)
        working_handler.assert_called_once_with(event)

    def test_validation_requirement_processing_started_event(self):
        """
        Test validation requirement: publishing ProcessingStartedEvent
        triggers tracker output.

        This test validates the key requirement from the task.
        """
        publisher = EventPublisher()
        tracker_handler = Mock()

        publisher.subscribe(ProcessingStartedEvent, tracker_handler)

        event = ProcessingStartedEvent(file_path=Path("test.pdf"), file_size=1000)

        publisher.publish(event)

        # Validation requirement: handler is called when event is published
        tracker_handler.assert_called_once_with(event)
        assert tracker_handler.call_count == 1
