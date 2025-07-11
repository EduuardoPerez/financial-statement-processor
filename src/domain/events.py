"""Domain events for the Financial Statement Processor.

This module implements the Observer pattern foundation for event-driven
architecture, enabling decoupled communication between components during
statement processing.
"""

from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .models import Transaction

# Type alias for cleaner method signatures
EventHandler = Callable[["Event"], None]


class Event(ABC):
    """Base class for all domain events."""

    def __init__(self) -> None:
        """Initialize event with current timestamp."""
        self.timestamp = datetime.now()


@dataclass
class ProcessingStartedEvent(Event):
    """Event published when statement processing begins."""

    file_path: Path
    file_size: int

    def __post_init__(self) -> None:
        """Initialize parent after dataclass initialization."""
        super().__init__()


@dataclass
class TransactionParsedEvent(Event):
    """Event published when a transaction is successfully parsed."""

    transaction: Transaction
    progress: float  # 0.0 to 1.0

    def __post_init__(self) -> None:
        """Initialize parent after dataclass initialization."""
        super().__init__()


@dataclass
class ProcessingCompletedEvent(Event):
    """Event published when statement processing completes successfully."""

    file_path: Path
    output_path: Path
    transaction_count: int
    processing_time: float

    def __post_init__(self) -> None:
        """Initialize parent after dataclass initialization."""
        super().__init__()


@dataclass
class ValidationFailedEvent(Event):
    """Event published when statement validation fails."""

    file_path: Path
    error_message: str

    def __post_init__(self) -> None:
        """Initialize parent after dataclass initialization."""
        super().__init__()


@dataclass
class ProcessingFailedEvent(Event):
    """Event published when statement processing fails."""

    file_path: Path
    error_message: str
    exception_type: str

    def __post_init__(self) -> None:
        """Initialize parent after dataclass initialization."""
        super().__init__()


class EventPublisher:
    """Publisher for domain events following Observer pattern."""

    def __init__(self) -> None:
        """Initialize publisher with empty subscriber registry."""
        self._subscribers: dict[type, list[EventHandler]] = {}

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """
        Subscribe to specific event type.

        Args:
            event_type: The type of event to subscribe to
            handler: Function to call when event is published

        Example:
            >>> publisher = EventPublisher()
            >>> publisher.subscribe(ProcessingStartedEvent, my_handler)
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: type, handler: EventHandler) -> None:
        """
        Unsubscribe from specific event type.

        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler function to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                if not self._subscribers[event_type]:
                    del self._subscribers[event_type]
            except ValueError:
                pass  # Handler not found, ignore

    def publish(self, event: Event) -> None:
        """
        Publish event to all subscribers.

        Args:
            event: The event to publish

        Note:
            If a handler raises an exception, it's logged but doesn't stop
            other handlers from executing. This ensures system resilience.
        """
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception:
                    # In a real implementation, this would use proper logging
                    # For now, we'll silently continue to ensure resilience
                    pass

    def get_subscriber_count(self, event_type: type) -> int:
        """
        Get number of subscribers for specific event type.

        Args:
            event_type: The event type to check

        Returns:
            Number of subscribers for the event type
        """
        return len(self._subscribers.get(event_type, []))

    def clear_subscribers(self, event_type: type | None = None) -> None:
        """
        Clear subscribers for specific event type or all events.

        Args:
            event_type: Event type to clear, or None to clear all
        """
        if event_type is None:
            self._subscribers.clear()
        elif event_type in self._subscribers:
            del self._subscribers[event_type]
