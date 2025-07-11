# Domain layer - Core business logic and entities

from .builders import (
    ProcessingReport,
    ProcessingReportBuilder,
    StatementBuilder,
    TransactionBuilder,
)
from .commands import (
    BatchProcessCommand,
    Command,
    CommandResult,
    ProcessStatementCommand,
)
from .detectors import BankDetector, PaymentMethodDetector
from .events import (
    Event,
    EventPublisher,
    ProcessingCompletedEvent,
    ProcessingFailedEvent,
    ProcessingStartedEvent,
    TransactionParsedEvent,
    ValidationFailedEvent,
)
from .factories import ParserFactory
from .filename import FilenameGenerator
from .models import Balance, Currency, PaymentMethod, Statement, Transaction
from .repositories import FileReader, FileWriter, StatementRepository
from .services import StatementParser
from .utils import AmountParser, DateConverter
from .validation import StatementValidator, ValidationResult

__all__ = [
    # Commands
    "Command",
    "CommandResult",
    "ProcessStatementCommand",
    "BatchProcessCommand",
    # Core Models
    "Currency",
    "PaymentMethod",
    "Transaction",
    "Balance",
    "Statement",
    # Services & Builders
    "TransactionBuilder",
    "StatementBuilder",
    "ProcessingReport",
    "ProcessingReportBuilder",
    "StatementParser",
    "PaymentMethodDetector",
    # Utilities
    "DateConverter",
    "AmountParser",
    "FilenameGenerator",
    # Detection & Validation
    "BankDetector",
    "ValidationResult",
    "StatementValidator",
    # Events
    "Event",
    "EventPublisher",
    "ProcessingStartedEvent",
    "TransactionParsedEvent",
    "ProcessingCompletedEvent",
    "ValidationFailedEvent",
    "ProcessingFailedEvent",
    # Repositories & Factories
    "FileReader",
    "FileWriter",
    "StatementRepository",
    "ParserFactory",
]
