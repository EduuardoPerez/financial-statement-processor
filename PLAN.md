# 🏗️ Financial Statement Processor - Architecture Improvement Plan

## 📋 Executive Summary

This document outlines a comprehensive architectural transformation plan for the Financial Statement Processor, evolving from a monolithic single-file design to a clean, modular, extensible architecture following SOLID principles and modern design patterns.

**Current State**: Functional but monolithic (1,200+ lines in single file)
**Target State**: Clean architecture with separation of concerns, design patterns, and enterprise-ready structure
**Approach**: Phased refactoring with zero regression and maintained test coverage

---

## 🔍 Current Architecture Analysis

### Strengths

- ✅ **Functional Excellence**: Processes 10 statement types across 4 file formats flawlessly
- ✅ **Comprehensive Testing**: 201 tests with 90% coverage
- ✅ **Modern Development**: Pre-commit hooks, type safety, automated quality checks
- ✅ **Data Integrity**: Robust validation and error handling

### Critical Issues Identified

#### 1. **Monolithic Design (Single Responsibility Principle Violation)**

```python
# Current: Everything in parse_visa_statement.py (1,200+ lines)
def parse_visa_pdf()        # PDF parsing
def parse_account_xls()     # XLS parsing
def parse_bbva_visa_csv()   # CSV parsing
def parse_mercadopago_xlsx() # XLSX parsing
def detect_payment_method() # Detection logic
def validate_balance()      # Validation logic
def generate_output_filename() # File naming
# ... and more
```

**Problems:**

- Single file handles PDF parsing, XLS processing, CSV handling, validation, file naming, and output generation
- Impossible to modify one aspect without risking others
- Difficult to test individual components in isolation

#### 2. **Code Duplication (DRY Principle Violation)**

```python
# Repeated patterns across parsers:
# Date conversion logic duplicated 4 times
# European number format handling duplicated 6 times
# Transaction creation logic duplicated 10 times
# Validation patterns repeated across file types
```

#### 3. **Tight Coupling (Dependency Inversion Violation)**

```python
# Direct file system dependencies
with pdfplumber.open(pdf_path) as pdf:  # Hardcoded PDF library
df = pd.read_excel(xls_path)            # Hardcoded Excel library
df.to_excel(output_path, index=False)   # Hardcoded output format
```

#### 4. **Open/Closed Principle Violation**

- Adding new banks requires modifying existing functions
- No extension points for new file formats
- Hardcoded logic prevents customization

#### 5. **Missing Design Patterns**

- No Strategy pattern for different parsing approaches
- No Factory pattern for parser creation
- No Repository pattern for data access
- No Command pattern for operations

#### 6. **Hardcoded Dependencies**

```python
# Hardcoded paths and formats
input_file = "input/MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf"
output_file = f"output/{output_filename}"
df.to_excel(output_path, index=False, sheet_name="Sheet1")  # Only Excel output
```

---

## 🎯 Target Architecture Vision

### Hexagonal Architecture (Ports & Adapters)

```plain
┌─────────────────────────────────────────────────────────────┐
│                    Application Core                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Domain        │  │   Use Cases     │  │   Services   │ │
│  │   Models        │  │   (Business     │  │   (Domain    │ │
│  │   (Transaction, │  │    Logic)       │  │    Logic)    │ │
│  │    Statement)   │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
    ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
    │   Input     │      │   Output    │      │   Config    │
    │   Adapters  │      │   Adapters  │      │   Adapters  │
    │             │      │             │      │             │
    │ PDF Parser  │      │ Excel       │      │ File        │
    │ XLS Parser  │      │ CSV         │      │ Database    │
    │ CSV Parser  │      │ JSON        │      │ Environment │
    │ XLSX Parser │      │ Database    │      │ Settings    │
    └─────────────┘      └─────────────┘      └─────────────┘
```

### Key Architectural Principles

1. **Separation of Concerns**: Each component has a single, well-defined responsibility
2. **Dependency Inversion**: Core business logic depends on abstractions, not implementations
3. **Open/Closed**: Open for extension, closed for modification
4. **Interface Segregation**: Small, focused interfaces
5. **Single Responsibility**: Each class has one reason to change

---

## 📅 Implementation Phases

## Phase 1: Core Architecture Foundation (Weeks 1-2)

### 1.1 Domain Model Creation

**Objective**: Establish core business entities and value objects

**Implementation**:

```python
# src/domain/models.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

class Currency(Enum):
    ARS = "ARS"
    USD = "USD"

class PaymentMethod(Enum):
    MACRO_VISA = "Macro VISA"
    BBVA_VISA = "BBVA VISA"
    BBVA_MASTERCARD = "BBVA Mastercard"
    BBVA_ACCOUNT = "BBVA Account"
    MACRO_ACCOUNT = "Macro Account"
    MERCADOPAGO = "Mercadopago"

@dataclass(frozen=True)
class Transaction:
    """Immutable transaction value object"""
    date: date
    description: str
    amount: Decimal
    currency: Currency
    payment_method: PaymentMethod
    reference: Optional[str] = None

    def __post_init__(self):
        if not self.description.strip():
            raise ValueError("Description cannot be empty")
        if self.amount == 0:
            raise ValueError("Amount cannot be zero")

@dataclass(frozen=True)
class Balance:
    """Immutable balance value object"""
    ars_amount: Decimal
    usd_amount: Decimal

    def total_in_currency(self, currency: Currency) -> Decimal:
        return self.ars_amount if currency == Currency.ARS else self.usd_amount

@dataclass
class Statement:
    """Statement aggregate root"""
    payment_method: PaymentMethod
    transactions: list[Transaction]
    reported_balance: Optional[Balance] = None

    def add_transaction(self, transaction: Transaction) -> None:
        if transaction.payment_method != self.payment_method:
            raise ValueError("Transaction payment method must match statement")
        self.transactions.append(transaction)

    def get_balance(self) -> Balance:
        ars_total = sum(t.amount for t in self.transactions if t.currency == Currency.ARS)
        usd_total = sum(t.amount for t in self.transactions if t.currency == Currency.USD)
        return Balance(ars_total, usd_total)

    def get_transactions_by_currency(self, currency: Currency) -> list[Transaction]:
        return [t for t in self.transactions if t.currency == currency]
```

### 1.2 Repository Pattern Implementation

**Objective**: Abstract data access and file operations

```python
# src/domain/repositories.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

class FileReader(Protocol):
    """Protocol for file reading operations"""
    def read(self, path: Path) -> bytes: ...
    def exists(self, path: Path) -> bool: ...

class FileWriter(Protocol):
    """Protocol for file writing operations"""
    def write(self, path: Path, content: bytes) -> None: ...
    def ensure_directory(self, path: Path) -> None: ...

class StatementRepository(ABC):
    """Abstract repository for statement persistence"""

    @abstractmethod
    def save_statement(self, statement: Statement, output_path: Path) -> None:
        """Save statement to specified path"""
        pass

    @abstractmethod
    def load_raw_data(self, input_path: Path) -> bytes:
        """Load raw data from input file"""
        pass

# src/infrastructure/repositories.py
class ExcelStatementRepository(StatementRepository):
    """Excel-based statement repository"""

    def __init__(self, file_reader: FileReader, file_writer: FileWriter):
        self._file_reader = file_reader
        self._file_writer = file_writer

    def save_statement(self, statement: Statement, output_path: Path) -> None:
        # Convert statement to DataFrame and save as Excel
        df = self._statement_to_dataframe(statement)
        self._file_writer.ensure_directory(output_path.parent)

        # Use pandas to save Excel file
        df.to_excel(output_path, index=False, sheet_name="Sheet1")

    def load_raw_data(self, input_path: Path) -> bytes:
        if not self._file_reader.exists(input_path):
            raise FileNotFoundError(f"File not found: {input_path}")
        return self._file_reader.read(input_path)

    def _statement_to_dataframe(self, statement: Statement) -> pd.DataFrame:
        data = []
        for transaction in statement.transactions:
            data.append({
                "Date": transaction.date.strftime("%Y-%m-%d"),
                "Description": transaction.description,
                "Currency": transaction.currency.value,
                "Amount": float(transaction.amount),
                "Payment Method": transaction.payment_method.value
            })
        return pd.DataFrame(data)
```

### 1.3 Strategy Pattern for Parsers

**Objective**: Pluggable parsing strategies for different file formats

```python
# src/domain/services.py
from abc import ABC, abstractmethod
from pathlib import Path

class StatementParser(ABC):
    """Abstract strategy for parsing different statement formats"""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Determine if this parser can handle the given file"""
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> Statement:
        """Parse the file and return a Statement object"""
        pass

    @abstractmethod
    def get_supported_extensions(self) -> set[str]:
        """Return supported file extensions"""
        pass

# src/infrastructure/parsers/pdf_parser.py
class PDFStatementParser(StatementParser):
    """Strategy for parsing PDF statements"""

    def __init__(self, payment_method_detector: PaymentMethodDetector):
        self._detector = payment_method_detector

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.pdf'

    def parse(self, file_path: Path) -> Statement:
        # Extract text using pdfplumber
        with pdfplumber.open(file_path) as pdf:
            full_text = self._extract_text(pdf)

        # Detect payment method
        payment_method = self._detector.detect_from_content(full_text)

        # Create statement and parse transactions
        statement = Statement(payment_method=payment_method, transactions=[])

        # Use specific parsing strategy based on payment method
        parser_strategy = self._get_parsing_strategy(payment_method)
        transactions = parser_strategy.parse_transactions(full_text)

        for transaction in transactions:
            statement.add_transaction(transaction)

        return statement

    def get_supported_extensions(self) -> set[str]:
        return {'.pdf'}

# src/infrastructure/parsers/xls_parser.py
class XLSStatementParser(StatementParser):
    """Strategy for parsing XLS statements"""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in {'.xls', '.xlsx'}

    def parse(self, file_path: Path) -> Statement:
        # Detect payment method from filename
        payment_method = self._detector.detect_from_filename(file_path)

        # Read Excel file
        df = pd.read_excel(file_path)

        # Create statement
        statement = Statement(payment_method=payment_method, transactions=[])

        # Parse based on specific XLS format
        parser_strategy = self._get_xls_strategy(payment_method)
        transactions = parser_strategy.parse_dataframe(df)

        for transaction in transactions:
            statement.add_transaction(transaction)

        return statement

    def get_supported_extensions(self) -> set[str]:
        return {'.xls', '.xlsx'}
```

### 1.4 Factory Pattern Implementation

**Objective**: Dynamic parser creation and management

```python
# src/domain/factories.py
class ParserFactory:
    """Factory for creating appropriate parsers"""

    def __init__(self):
        self._parsers: list[StatementParser] = []

    def register_parser(self, parser: StatementParser) -> None:
        """Register a new parser strategy"""
        self._parsers.append(parser)

    def create_parser(self, file_path: Path) -> StatementParser:
        """Create appropriate parser for the given file"""
        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser

        raise ValueError(f"No parser available for file: {file_path}")

    def get_supported_extensions(self) -> set[str]:
        """Get all supported file extensions"""
        extensions = set()
        for parser in self._parsers:
            extensions.update(parser.get_supported_extensions())
        return extensions

# src/infrastructure/factories.py
class DefaultParserFactory(ParserFactory):
    """Default factory with all standard parsers"""

    def __init__(self, detector: PaymentMethodDetector):
        super().__init__()

        # Register all available parsers
        self.register_parser(PDFStatementParser(detector))
        self.register_parser(XLSStatementParser(detector))
        self.register_parser(CSVStatementParser(detector))
        self.register_parser(XLSXStatementParser(detector))
```

**Deliverables for Phase 1:**

- [ ] Domain models with value objects and entities
- [ ] Repository pattern implementation
- [ ] Strategy pattern for parsers
- [ ] Factory pattern for parser creation
- [ ] Unit tests for all new components
- [ ] Integration tests maintaining existing functionality

---

## Phase 2: SOLID Principles Implementation (Weeks 3-4)

### 2.1 Single Responsibility Principle

**Objective**: Each class has one reason to change

**Current Violations:**

```python
# Current: parse_visa_pdf() does everything
def parse_visa_pdf(pdf_path, output_path):
    # 1. File reading
    # 2. Text extraction
    # 3. Payment method detection
    # 4. Transaction parsing
    # 5. Date conversion
    # 6. Amount parsing
    # 7. Balance validation
    # 8. Excel output
    # 9. File path management
```

**Refactored Solution:**

```python
# src/application/services.py
class StatementProcessingService:
    """Single responsibility: Orchestrate statement processing"""

    def __init__(
        self,
        parser_factory: ParserFactory,
        repository: StatementRepository,
        validator: StatementValidator,
        filename_generator: FilenameGenerator
    ):
        self._parser_factory = parser_factory
        self._repository = repository
        self._validator = validator
        self._filename_generator = filename_generator

    def process_statement(self, input_path: Path, output_dir: Path) -> ProcessingResult:
        """Process a single statement file"""
        # Single responsibility: orchestration only
        parser = self._parser_factory.create_parser(input_path)
        statement = parser.parse(input_path)

        validation_result = self._validator.validate(statement)

        output_filename = self._filename_generator.generate(statement)
        output_path = output_dir / output_filename

        self._repository.save_statement(statement, output_path)

        return ProcessingResult(
            input_path=input_path,
            output_path=output_path,
            statement=statement,
            validation_result=validation_result
        )

class DateConverter:
    """Single responsibility: Date format conversion"""

    def convert_dd_mm_yy(self, date_str: str) -> date:
        """Convert DD.MM.YY format to date object"""
        day, month, year = date_str.split(".")
        year_int = int(year)
        full_year = 2000 + year_int if year_int < 50 else 1900 + year_int
        return date(full_year, int(month), int(day))

    def convert_dd_mmm_yy(self, date_str: str) -> date:
        """Convert DD-MMM-YY format to date object"""
        # Implementation for Spanish month abbreviations
        pass

class AmountParser:
    """Single responsibility: European number format parsing"""

    def parse_european_format(self, amount_str: str) -> Decimal:
        """Parse European format (1.234,56) to Decimal"""
        if "." in amount_str and "," in amount_str:
            # Format: 1.234,56 -> remove dots, convert comma to decimal
            clean_str = amount_str.replace(".", "").replace(",", ".")
        elif "," in amount_str:
            # Format: 1234,56 -> convert comma to decimal
            clean_str = amount_str.replace(",", ".")
        else:
            clean_str = amount_str

        return Decimal(clean_str)

class TransactionBuilder:
    """Single responsibility: Transaction object construction"""

    def __init__(self, date_converter: DateConverter, amount_parser: AmountParser):
        self._date_converter = date_converter
        self._amount_parser = amount_parser

    def build_from_pdf_line(
        self,
        date_str: str,
        description: str,
        amount_str: str,
        currency: Currency,
        payment_method: PaymentMethod
    ) -> Transaction:
        """Build transaction from PDF line components"""
        parsed_date = self._date_converter.convert_dd_mm_yy(date_str)
        parsed_amount = self._amount_parser.parse_european_format(amount_str)

        return Transaction(
            date=parsed_date,
            description=description.strip(),
            amount=parsed_amount,
            currency=currency,
            payment_method=payment_method
        )
```

### 2.2 Open/Closed Principle

**Objective**: Open for extension, closed for modification

**Current Problem:**

```python
# Adding new bank requires modifying existing functions
def detect_payment_method(content_or_path, file_path, full_text):
    # Hardcoded bank detection logic
    if "MACRO PREMIA" in text_upper:
        return "Macro VISA"
    elif "BBVA" in text_upper:
        return "BBVA VISA"
    # Adding Santander requires modifying this function
```

#### **Solution: Extension Points**

```python
# src/domain/services.py
class PaymentMethodDetector:
    """Extensible payment method detection"""

    def __init__(self):
        self._detectors: list[BankDetector] = []

    def register_detector(self, detector: BankDetector) -> None:
        """Register new bank detector without modifying existing code"""
        self._detectors.append(detector)

    def detect_from_content(self, content: str) -> PaymentMethod:
        """Detect payment method using registered detectors"""
        for detector in self._detectors:
            if detector.can_detect(content):
                return detector.get_payment_method(content)

        raise ValueError("Unknown payment method")

# src/infrastructure/detectors.py
class BankDetector(ABC):
    """Abstract detector for bank identification"""

    @abstractmethod
    def can_detect(self, content: str) -> bool:
        """Check if this detector can identify the bank"""
        pass

    @abstractmethod
    def get_payment_method(self, content: str) -> PaymentMethod:
        """Return the specific payment method"""
        pass

class MacroDetector(BankDetector):
    """Detector for Macro bank statements"""

    def can_detect(self, content: str) -> bool:
        indicators = ["MACRO PREMIA", "BANCO MACRO", "WWW.MACRO.COM.AR"]
        return any(indicator in content.upper() for indicator in indicators)

    def get_payment_method(self, content: str) -> PaymentMethod:
        if "VISA" in content.upper():
            return PaymentMethod.MACRO_VISA
        return PaymentMethod.MACRO_ACCOUNT

class BBVADetector(BankDetector):
    """Detector for BBVA bank statements"""

    def can_detect(self, content: str) -> bool:
        indicators = ["BBVA", "WWW.BBVA.COM.AR"]
        return any(indicator in content.upper() for indicator in indicators)

    def get_payment_method(self, content: str) -> PaymentMethod:
        content_upper = content.upper()
        if "MASTERCARD" in content_upper:
            return PaymentMethod.BBVA_MASTERCARD
        elif "VISA" in content_upper:
            return PaymentMethod.BBVA_VISA
        return PaymentMethod.BBVA_ACCOUNT

# Adding Santander support (EXTENSION without MODIFICATION)
class SantanderDetector(BankDetector):
    """Detector for Santander bank statements"""

    def can_detect(self, content: str) -> bool:
        indicators = ["SANTANDER", "BANCO SANTANDER"]
        return any(indicator in content.upper() for indicator in indicators)

    def get_payment_method(self, content: str) -> PaymentMethod:
        return PaymentMethod.SANTANDER_VISA  # New enum value
```

### 2.3 Dependency Inversion Principle

**Objective**: Depend on abstractions, not concretions

**Current Problem:**

```python
# Direct dependencies on concrete implementations
import pdfplumber  # Hardcoded PDF library
import pandas as pd  # Hardcoded data processing
import openpyxl  # Hardcoded Excel library

def parse_visa_pdf(pdf_path, output_path):
    with pdfplumber.open(pdf_path) as pdf:  # Concrete dependency
        # ...
    df.to_excel(output_path, index=False)  # Concrete dependency
```

#### **Solution: Abstract Interfaces**

```python
# src/domain/ports.py
class PDFReader(Protocol):
    """Abstract interface for PDF reading"""
    def extract_text(self, file_path: Path) -> str: ...

class ExcelWriter(Protocol):
    """Abstract interface for Excel writing"""
    def write_statement(self, statement: Statement, file_path: Path) -> None: ...

class DataProcessor(Protocol):
    """Abstract interface for data processing"""
    def create_dataframe(self, transactions: list[Transaction]) -> Any: ...
    def sort_by_date(self, data: Any) -> Any: ...

# src/infrastructure/adapters.py
class PdfPlumberAdapter(PDFReader):
    """Concrete implementation using pdfplumber"""

    def extract_text(self, file_path: Path) -> str:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        return full_text

class PandasExcelAdapter(ExcelWriter):
    """Concrete implementation using pandas"""

    def write_statement(self, statement: Statement, file_path: Path) -> None:
        data = []
        for transaction in statement.transactions:
            data.append({
                "Date": transaction.date.strftime("%Y-%m-%d"),
                "Description": transaction.description,
                "Currency": transaction.currency.value,
                "Amount": float(transaction.amount),
                "Payment Method": transaction.payment_method.value
            })

        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False, sheet_name="Sheet1")

# src/infrastructure/parsers/pdf_parser.py (Updated)
class PDFStatementParser(StatementParser):
    """PDF parser using dependency injection"""

    def __init__(
        self,
        pdf_reader: PDFReader,  # Abstract dependency
        detector: PaymentMethodDetector,
        transaction_builder: TransactionBuilder
    ):
        self._pdf_reader = pdf_reader
        self._detector = detector
        self._transaction_builder = transaction_builder

    def parse(self, file_path: Path) -> Statement:
        # Use abstraction instead of concrete implementation
        full_text = self._pdf_reader.extract_text(file_path)

        payment_method = self._detector.detect_from_content(full_text)
        statement = Statement(payment_method=payment_method, transactions=[])

        # Parse transactions using injected dependencies
        transactions = self._parse_transactions(full_text, payment_method)

        for transaction in transactions:
            statement.add_transaction(transaction)

        return statement
```

**Deliverables for Phase 2:**

- [ ] Single responsibility classes for all major functions
- [ ] Extension points for new banks and formats
- [ ] Abstract interfaces for all external dependencies
- [ ] Dependency injection container setup
- [ ] Comprehensive unit tests for each component
- [ ] Integration tests ensuring backward compatibility

---

## Phase 3: Advanced Design Patterns (Weeks 5-6)

### 3.1 Command Pattern for Operations

**Objective**: Encapsulate operations as objects for undo, logging, and queuing

```python
# src/domain/commands.py
class Command(ABC):
    """Abstract command interface"""

    @abstractmethod
    def execute(self) -> CommandResult: ...

    @abstractmethod
    def undo(self) -> None: ...

    @abstractmethod
    def can_undo(self) -> bool: ...

@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    message: str
    data: Any = None
    execution_time: float = 0.0

class ProcessStatementCommand(Command):
    """Command to process a single statement"""

    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        processing_service: StatementProcessingService
    ):
        self._input_path = input_path
        self._output_path = output_path
        self._processing_service = processing_service
        self._result: Optional[ProcessingResult] = None

    def execute(self) -> CommandResult:
        start_time = time.time()

        try:
            self._result = self._processing_service.process_statement(
                self._input_path,
                self._output_path.parent
            )

            execution_time = time.time() - start_time

            return CommandResult(
                success=True,
                message=f"Successfully processed {self._input_path.name}",
                data=self._result,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time

            return CommandResult(
                success=False,
                message=f"Failed to process {self._input_path.name}: {str(e)}",
                execution_time=execution_time
            )

    def undo(self) -> None:
        """Remove generated output file"""
        if self._result and self._result.output_path.exists():
            self._result.output_path.unlink()

    def can_undo(self) -> bool:
        return self._result is not None

class BatchProcessCommand(Command):
    """Command to process multiple statements"""

    def __init__(self, commands: list[Command]):
        self._commands = commands
        self._executed_commands: list[Command] = []

    def execute(self) -> CommandResult:
        results = []
        start_time = time.time()

        for command in self._commands:
            result = command.execute()
            results.append(result)

            if result.success:
                self._executed_commands.append(command)
            else:
                # Stop on first failure and rollback
                self.undo()
                break

        execution_time = time.time() - start_time
        success_count = sum(1 for r in results if r.success)

        return CommandResult(
            success=success_count == len(self._commands),
            message=f"Processed {success_count}/{len(self._commands)} statements",
            data=results,
            execution_time=execution_time
        )

    def undo(self) -> None:
        """Undo all successfully executed commands"""
        for command in reversed(self._executed_commands):
            if command.can_undo():
                command.undo()
        self._executed_commands.clear()

    def can_undo(self) -> bool:
        return len(self._executed_commands) > 0

# src/application/services.py
class CommandProcessor:
    """Service for executing and managing commands"""

    def __init__(self):
        self._history: list[Command] = []

    def execute(self, command: Command) -> CommandResult:
        """Execute command and add to history"""
        result = command.execute()

        if result.success:
            self._history.append(command)

        return result

    def undo_last(self) -> bool:
        """Undo the last successful command"""
        if not self._history:
            return False

        last_command = self._history.pop()
        if last_command.can_undo():
            last_command.undo()
            return True

        return False

    def get_history(self) -> list[Command]:
        """Get command execution history"""
        return self._history.copy()
```

### 3.2 Observer Pattern for Progress Tracking

**Objective**: Decouple progress reporting from business logic

```python
# src/domain/events.py
class Event(ABC):
    """Base class for domain events"""
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ProcessingStartedEvent(Event):
    file_path: Path
    file_size: int

@dataclass
class TransactionParsedEvent(Event):
    transaction: Transaction
    progress: float  # 0.0 to 1.0

@dataclass
class ProcessingCompletedEvent(Event):
    file_path: Path
    output_path: Path
    transaction_count: int
    processing_time: float

@dataclass
class ValidationFailedEvent(Event):
    file_path: Path
    error_message: str

class EventPublisher:
    """Publisher for domain events"""

    def __init__(self):
        self._subscribers: dict[type, list[Callable]] = {}

    def subscribe(self, event_type: type, handler: Callable[[Event], None]) -> None:
        """Subscribe to specific event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        """Publish event to all subscribers"""
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    # Log error but don't stop other handlers
                    logger.error(f"Error in event handler: {e}")

# src/infrastructure/observers.py
class ProgressTracker:
    """Observer for tracking processing progress"""

    def __init__(self):
        self.current_file: Optional[Path] = None
        self.total_transactions = 0
        self.processed_transactions = 0
        self.start_time: Optional[datetime] = None

    def handle_processing_started(self, event: ProcessingStartedEvent) -> None:
        """Handle processing started event"""
        self.current_file = event.file_path
        self.start_time = event.timestamp
        self.processed_transactions = 0
        print(f"Started processing: {event.file_path.name}")

    def handle_transaction_parsed(self, event: TransactionParsedEvent) -> None:
        """Handle transaction parsed event"""
        self.processed_transactions += 1
        if self.processed_transactions % 10 == 0:  # Update every 10 transactions
            print(f"Processed {self.processed_transactions} transactions...")

    def handle_processing_completed(self, event: ProcessingCompletedEvent) -> None:
        """Handle processing completed event"""
        duration = (event.timestamp - self.start_time).total_seconds()
        print(f"✅ Completed: {event.file_path.name}")
        print(f"   Transactions: {event.transaction_count}")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Output: {event.output_path}")

class ValidationReporter:
    """Observer for validation reporting"""

    def __init__(self):
        self.validation_errors: list[str] = []

    def handle_validation_failed(self, event: ValidationFailedEvent) -> None:
        """Handle validation failure event"""
        error_msg = f"❌ Validation failed for {event.file_path.name}: {event.error_message}"
        self.validation_errors.append(error_msg)
        print(error_msg)

    def get_error_summary(self) -> str:
        """Get summary of all validation errors"""
        if not self.validation_errors:
            return "✅ All validations passed"

        return f"❌ {len(self.validation_errors)} validation errors:\n" + "\n".join(self.validation_errors)
```

### 3.3 Builder Pattern for Complex Objects

**Objective**: Flexible construction of complex statements and reports

```python
# src/domain/builders.py
class StatementBuilder:
    """Builder for constructing Statement objects"""

    def __init__(self):
        self._payment_method: Optional[PaymentMethod] = None
        self._transactions: list[Transaction] = []
        self._reported_balance: Optional[Balance] = None

    def with_payment_method(self, payment_method: PaymentMethod) -> "StatementBuilder":
        """Set the payment method"""
        self._payment_method = payment_method
        return self

    def add_transaction(self, transaction: Transaction) -> "StatementBuilder":
        """Add a transaction to the statement"""
        self._transactions.append(transaction)
        return self

    def add_transactions(self, transactions: list[Transaction]) -> "StatementBuilder":
        """Add multiple transactions to the statement"""
        self._transactions.extend(transactions)
        return self

    def with_reported_balance(self, balance: Balance) -> "StatementBuilder":
        """Set the reported balance"""
        self._reported_balance = balance
        return self

    def build(self) -> Statement:
        """Build the final Statement object"""
        if self._payment_method is None:
            raise ValueError("Payment method is required")

        statement = Statement(
            payment_method=self._payment_method,
            transactions=self._transactions.copy(),
            reported_balance=self._reported_balance
        )

        # Validate all transactions match payment method
        for transaction in self._transactions:
            if transaction.payment_method != self._payment_method:
                raise ValueError(f"Transaction payment method {transaction.payment_method} does not match statement payment method {self._payment_method}")

        return statement

    def reset(self) -> "StatementBuilder":
        """Reset builder for reuse"""
        self._payment_method = None
        self._transactions.clear()
        self._reported_balance = None
        return self

class ProcessingReportBuilder:
    """Builder for processing reports"""

    def __init__(self):
        self._processed_files: list[Path] = []
        self._failed_files: list[tuple[Path, str]] = []
        self._total_transactions = 0
        self._processing_time = 0.0
        self._validation_results: list[ValidationResult] = []

    def add_successful_file(self, file_path: Path, transaction_count: int) -> "ProcessingReportBuilder":
        """Add a successfully processed file"""
        self._processed_files.append(file_path)
        self._total_transactions += transaction_count
        return self

    def add_failed_file(self, file_path: Path, error_message: str) -> "ProcessingReportBuilder":
        """Add a failed file"""
        self._failed_files.append((file_path, error_message))
        return self

    def with_processing_time(self, time_seconds: float) -> "ProcessingReportBuilder":
        """Set total processing time"""
        self._processing_time = time_seconds
        return self

    def add_validation_result(self, result: ValidationResult) -> "ProcessingReportBuilder":
        """Add validation result"""
        self._validation_results.append(result)
        return self

    def build(self) -> ProcessingReport:
        """Build the final processing report"""
        return ProcessingReport(
            processed_files=self._processed_files.copy(),
            failed_files=self._failed_files.copy(),
            total_transactions=self._total_transactions,
            processing_time=self._processing_time,
            validation_results=self._validation_results.copy(),
            success_rate=len(self._processed_files) / (len(self._processed_files) + len(self._failed_files)) if (self._processed_files or self._failed_files) else 0.0
        )

@dataclass
class ProcessingReport:
    """Report of batch processing results"""
    processed_files: list[Path]
    failed_files: list[tuple[Path, str]]
    total_transactions: int
    processing_time: float
    validation_results: list[ValidationResult]
    success_rate: float

    def print_summary(self) -> None:
        """Print formatted summary"""
        print(f"\n{'='*60}")
        print("BATCH PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful files: {len(self.processed_files)}")
        print(f"❌ Failed files: {len(self.failed_files)}")
        print(f"📊 Success rate: {self.success_rate:.1%}")
        print(f"📈 Total transactions: {self.total_transactions}")
        print(f"⏱️  Processing time: {self.processing_time:.2f}s")

        if self.failed_files:
            print(f"\n❌ Failed Files:")
            for file_path, error in self.failed_files:
                print(f"   {file_path.name}: {error}")
```

**Deliverables for Phase 3:**

- [ ] Command pattern implementation for operations
- [ ] Observer pattern for progress tracking and events
- [ ] Builder pattern for complex object construction
- [ ] Event-driven architecture with domain events
- [ ] Comprehensive logging and monitoring
- [ ] Advanced error handling and recovery

---

## Phase 4: Performance & Enterprise Features (Weeks 7-8)

### 4.1 Performance Optimizations

**Objective**: Optimize for large-scale processing and enterprise use

#### Async Processing Pipeline

```python
# src/infrastructure/async_processing.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncIterator

class AsyncStatementProcessor:
    """Asynchronous statement processor for high-throughput scenarios"""

    def __init__(
        self,
        parser_factory: ParserFactory,
        repository: StatementRepository,
        max_workers: int = 4
    ):
        self._parser_factory = parser_factory
        self._repository = repository
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_batch(self, file_paths: list[Path], output_dir: Path) -> AsyncIterator[ProcessingResult]:
        """Process multiple files concurrently"""
        semaphore = asyncio.Semaphore(self._executor._max_workers)

        async def process_single(file_path: Path) -> ProcessingResult:
            async with semaphore:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self._executor,
                    self._process_file_sync,
                    file_path,
                    output_dir
                )

        tasks = [process_single(path) for path in file_paths]

        for completed_task in asyncio.as_completed(tasks):
            yield await completed_task

    def _process_file_sync(self, file_path: Path, output_dir: Path) -> ProcessingResult:
        """Synchronous file processing for thread executor"""
        parser = self._parser_factory.create_parser(file_path)
        statement = parser.parse(file_path)

        output_filename = self._generate_filename(statement)
        output_path = output_dir / output_filename

        self._repository.save_statement(statement, output_path)

        return ProcessingResult(
            input_path=file_path,
            output_path=output_path,
            statement=statement,
            processing_time=0.0  # Would be measured in real implementation
        )

# Usage example
async def main():
    processor = AsyncStatementProcessor(parser_factory, repository)
    file_paths = [Path("input/file1.pdf"), Path("input/file2.xls")]

    async for result in processor.process_batch(file_paths, Path("output")):
        print(f"Processed: {result.input_path.name} -> {result.output_path.name}")
```

#### Memory-Efficient Streaming

```python
# src/infrastructure/streaming.py
class StreamingStatementParser:
    """Memory-efficient parser for large files"""

    def __init__(self, chunk_size: int = 1000):
        self._chunk_size = chunk_size

    def parse_large_csv(self, file_path: Path) -> Iterator[Transaction]:
        """Parse large CSV files in chunks"""
        chunk_reader = pd.read_csv(file_path, chunksize=self._chunk_size)

        for chunk in chunk_reader:
            for _, row in chunk.iterrows():
                yield self._parse_csv_row(row)

    def parse_large_excel(self, file_path: Path) -> Iterator[Transaction]:
        """Parse large Excel files sheet by sheet"""
        with pd.ExcelFile(file_path) as excel_file:
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)

                for _, row in df.iterrows():
                    yield self._parse_excel_row(row)

    def _parse_csv_row(self, row: pd.Series) -> Transaction:
        """Parse individual CSV row to Transaction"""
        # Implementation details...
        pass

    def _parse_excel_row(self, row: pd.Series) -> Transaction:
        """Parse individual Excel row to Transaction"""
        # Implementation details...
        pass
```

### 4.2 Configuration Management

**Objective**: Externalize configuration for different environments

```python
# src/infrastructure/config.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 5

@dataclass
class ProcessingConfig:
    """Processing behavior configuration"""
    max_workers: int = 4
    chunk_size: int = 1000
    timeout_seconds: int = 300
    retry_attempts: int = 3
    enable_validation: bool = True
    enable_balance_checking: bool = True

@dataclass
class OutputConfig:
    """Output format configuration"""
    default_format: str = "excel"
    excel_sheet_name: str = "Sheet1"
    csv_delimiter: str = ","
    include_index: bool = False
    date_format: str = "%Y-%m-%d"

@dataclass
class ApplicationConfig:
    """Main application configuration"""
    input_directory: Path
    output_directory: Path
    processing: ProcessingConfig
    output: OutputConfig
    database: Optional[DatabaseConfig] = None
    log_level: str = "INFO"
    enable_async: bool = False

    @classmethod
    def from_yaml(cls, config_path: Path) -> "ApplicationConfig":
        """Load configuration from YAML file"""
        with open(config_path, 'r') as file:
            config_data = yaml.safe_load(file)

        return cls(
            input_directory=Path(config_data["input_directory"]),
            output_directory=Path(config_data["output_directory"]),
            processing=ProcessingConfig(**config_data.get("processing", {})),
            output=OutputConfig(**config_data.get("output", {})),
            database=DatabaseConfig(**config_data["database"]) if "database" in config_data else None,
            log_level=config_data.get("log_level", "INFO"),
            enable_async=config_data.get("enable_async", False)
        )

    @classmethod
    def from_environment(cls) -> "ApplicationConfig":
        """Load configuration from environment variables"""
        import os

        return cls(
            input_directory=Path(os.getenv("FSP_INPUT_DIR", "input")),
            output_directory=Path(os.getenv("FSP_OUTPUT_DIR", "output")),
            processing=ProcessingConfig(
                max_workers=int(os.getenv("FSP_MAX_WORKERS", "4")),
                chunk_size=int(os.getenv("FSP_CHUNK_SIZE", "1000")),
                timeout_seconds=int(os.getenv("FSP_TIMEOUT", "300")),
                retry_attempts=int(os.getenv("FSP_RETRY_ATTEMPTS", "3")),
                enable_validation=os.getenv("FSP_ENABLE_VALIDATION", "true").lower() == "true",
                enable_balance_checking=os.getenv("FSP_ENABLE_BALANCE_CHECK", "true").lower() == "true"
            ),
            output=OutputConfig(
                default_format=os.getenv("FSP_OUTPUT_FORMAT", "excel"),
                excel_sheet_name=os.getenv("FSP_EXCEL_SHEET", "Sheet1"),
                csv_delimiter=os.getenv("FSP_CSV_DELIMITER", ","),
                include_index=os.getenv("FSP_INCLUDE_INDEX", "false").lower() == "true",
                date_format=os.getenv("FSP_DATE_FORMAT", "%Y-%m-%d")
            ),
            log_level=os.getenv("FSP_LOG_LEVEL", "INFO"),
            enable_async=os.getenv("FSP_ENABLE_ASYNC", "false").lower() == "true"
        )

# config/development.yaml
input_directory: "input"
output_directory: "output"
log_level: "DEBUG"
enable_async: false

processing:
  max_workers: 2
  chunk_size: 500
  timeout_seconds: 60
  retry_attempts: 2
  enable_validation: true
  enable_balance_checking: true

output:
  default_format: "excel"
  excel_sheet_name: "Transactions"
  include_index: false
  date_format: "%Y-%m-%d"

# config/production.yaml
input_directory: "/app/data/input"
output_directory: "/app/data/output"
log_level: "INFO"
enable_async: true

processing:
  max_workers: 8
  chunk_size: 2000
  timeout_seconds: 600
  retry_attempts: 5
  enable_validation: true
  enable_balance_checking: true

output:
  default_format: "excel"
  excel_sheet_name: "Sheet1"
  include_index: false
  date_format: "%Y-%m-%d"

database:
  host: "postgres.internal"
  port: 5432
  database: "financial_statements"
  username: "fsp_user"
  password: "${DB_PASSWORD}"
  pool_size: 10
```

### 4.3 CLI Interface

**Objective**: Professional command-line interface for all operations

```python
# src/cli/main.py
import click
from pathlib import Path
from typing import Optional

@click.group()
@click.option("--config", "-c", type=click.Path(exists=True), help="Configuration file path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: bool):
    """Financial Statement Processor CLI"""
    ctx.ensure_object(dict)

    if config:
        ctx.obj["config"] = ApplicationConfig.from_yaml(Path(config))
    else:
        ctx.obj["config"] = ApplicationConfig.from_environment()

    if verbose:
        ctx.obj["config"].log_level = "DEBUG"

@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "-f", type=click.Choice(["excel", "csv", "json"]), default="excel", help="Output format")
@click.pass_context
def process(ctx: click.Context, input_file: str, output: Optional[str], format: str):
    """Process a single statement file"""
    config = ctx.obj["config"]
    input_path = Path(input_file)

    if output:
        output_path = Path(output)
    else:
        output_path = config.output_directory / f"{input_path.stem}_transactions.{format}"

    # Initialize services
    processor = create_processor(config)

    try:
        result = processor.process_statement(input_path, output_path.parent)
        click.echo(f"✅ Successfully processed {input_path.name}")
        click.echo(f"   Output: {result.output_path}")
        click.echo(f"   Transactions: {len(result.statement.transactions)}")
    except Exception as e:
        click.echo(f"❌ Failed to process {input_path.name}: {str(e)}", err=True)
        raise click.ClickException(str(e))

@cli.command()
@click.argument("input_directory", type=click.Path(exists=True, file_okay=False))
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory")
@click.option("--pattern", "-p", default="*", help="File pattern to match")
@click.option("--parallel", is_flag=True, help="Enable parallel processing")
@click.option("--max-workers", type=int, help="Maximum number of worker threads")
@click.pass_context
def batch(ctx: click.Context, input_directory: str, output_dir: Optional[str], pattern: str, parallel: bool, max_workers: Optional[int]):
    """Process multiple statement files in batch"""
    config = ctx.obj["config"]
    input_path = Path(input_directory)

    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = config.output_directory

    # Find matching files
    files = list(input_path.glob(pattern))
    if not files:
        click.echo(f"No files found matching pattern '{pattern}' in {input_directory}")
        return

    click.echo(f"Found {len(files)} files to process")

    # Configure processing
    if max_workers:
        config.processing.max_workers = max_workers

    if parallel or config.enable_async:
        processor = create_async_processor(config)
        asyncio.run(process_batch_async(processor, files, output_path))
    else:
        processor = create_processor(config)
        process_batch_sync(processor, files, output_path)

@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.pass_context
def validate(ctx: click.Context, input_file: str):
    """Validate a statement file without processing"""
    config = ctx.obj["config"]
    input_path = Path(input_file)

    try:
        # Parse file
        parser_factory = create_parser_factory(config)
        parser = parser_factory.create_parser(input_path)
        statement = parser.parse(input_path)

        # Validate
        validator = create_validator(config)
        result = validator.validate(statement)

        if result.is_valid:
            click.echo(f"✅ {input_path.name} is valid")
            click.echo(f"   Transactions: {len(statement.transactions)}")
            click.echo(f"   Balance: ARS {statement.get_balance().ars_amount}, USD {statement.get_balance().usd_amount}")
        else:
            click.echo(f"❌ {input_path.name} has validation errors:")
            for error in result.errors:
                click.echo(f"   - {error}")

    except Exception as e:
        click.echo(f"❌ Failed to validate {input_path.name}: {str(e)}", err=True)
        raise click.ClickException(str(e))

@cli.command()
@click.pass_context
def info(ctx: click.Context):
    """Show system information and configuration"""
    config = ctx.obj["config"]

    click.echo("Financial Statement Processor")
    click.echo("=" * 40)
    click.echo(f"Input Directory: {config.input_directory}")
    click.echo(f"Output Directory: {config.output_directory}")
    click.echo(f"Log Level: {config.log_level}")
    click.echo(f"Async Processing: {config.enable_async}")
    click.echo(f"Max Workers: {config.processing.max_workers}")
    click.echo(f"Default Output Format: {config.output.default_format}")

    # Show supported file types
    parser_factory = create_parser_factory(config)
    extensions = parser_factory.get_supported_extensions()
    click.echo(f"Supported Extensions: {', '.join(sorted(extensions))}")

if __name__ == "__main__":
    cli()
```

**Deliverables for Phase 4:**

- [ ] Async processing pipeline for high-throughput scenarios
- [ ] Memory-efficient streaming for large files
- [ ] Comprehensive configuration management
- [ ] Professional CLI interface with all operations
- [ ] Performance monitoring and metrics
- [ ] Enterprise logging and audit trails

---

## 🧪 Testing Strategy

### Test Architecture Evolution

#### Current State

- 201 tests with 90% coverage
- Integration tests with real files
- Professional test organization

#### Enhanced Testing Strategy

```python
# tests/unit/domain/test_models.py
class TestTransaction:
    """Unit tests for Transaction value object"""

    def test_transaction_creation_valid(self):
        """Test valid transaction creation"""
        transaction = Transaction(
            date=date(2025, 1, 15),
            description="Test Purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA
        )

        assert transaction.date == date(2025, 1, 15)
        assert transaction.description == "Test Purchase"
        assert transaction.amount == Decimal("100.50")
        assert transaction.currency == Currency.ARS
        assert transaction.payment_method == PaymentMethod.BBVA_VISA

    def test_transaction_immutable(self):
        """Test transaction immutability"""
        transaction = Transaction(
            date=date(2025, 1, 15),
            description="Test Purchase",
            amount=Decimal("100.50"),
            currency=Currency.ARS,
            payment_method=PaymentMethod.BBVA_VISA
        )

        with pytest.raises(AttributeError):
            transaction.amount = Decimal("200.00")

    def test_transaction_validation_empty_description(self):
        """Test validation for empty description"""
        with pytest.raises(ValueError, match="Description cannot be empty"):
            Transaction(
                date=date(2025, 1, 15),
                description="",
                amount=Decimal("100.50"),
                currency=Currency.ARS,
                payment_method=PaymentMethod.BBVA_VISA
            )

# tests/unit/application/test_services.py
class TestStatementProcessingService:
    """Unit tests for StatementProcessingService"""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies"""
        return {
            "parser_factory": Mock(spec=ParserFactory),
            "repository": Mock(spec=StatementRepository),
            "validator": Mock(spec=StatementValidator),
            "filename_generator": Mock(spec=FilenameGenerator)
        }

    def test_process_statement_success(self, mock_dependencies):
        """Test successful statement processing"""
        # Arrange
        service = StatementProcessingService(**mock_dependencies)
        input_path = Path("test.pdf")
        output_dir = Path("output")

        mock_parser = Mock(spec=StatementParser)
        mock_statement = Mock(spec=Statement)
        mock_validation_result = Mock(spec=ValidationResult)

        mock_dependencies["parser_factory"].create_parser.return_value = mock_parser
        mock_parser.parse.return_value = mock_statement
        mock_dependencies["validator"].validate.return_value = mock_validation_result
        mock_dependencies["filename_generator"].generate.return_value = "test-transactions.xlsx"

        # Act
        result = service.process_statement(input_path, output_dir)

        # Assert
        assert result.input_path == input_path
        assert result.output_path == output_dir / "test-transactions.xlsx"
        assert result.statement == mock_statement
        assert result.validation_result == mock_validation_result

        mock_dependencies["parser_factory"].create_parser.assert_called_once_with(input_path)
        mock_parser.parse.assert_called_once_with(input_path)
        mock_dependencies["validator"].validate.assert_called_once_with(mock_statement)
        mock_dependencies["repository"].save_statement.assert_called_once()

# tests/integration/test_end_to_end.py
class TestEndToEndProcessing:
    """End-to-end integration tests"""

    @pytest.fixture
    def test_config(self):
        """Create test configuration"""
        return ApplicationConfig(
            input_directory=Path("tests/test_data/input"),
            output_directory=Path("tests/test_data/output"),
            processing=ProcessingConfig(max_workers=1),
            output=OutputConfig()
        )

    def test_process_macro_visa_pdf(self, test_config):
        """Test complete processing of Macro VISA PDF"""
        # Arrange
        input_file = test_config.input_directory / "MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf"
        expected_output = test_config.output_directory / "MACRO-VISA-transactions.xlsx"

        processor = create_processor(test_config)

        # Act
        result = processor.process_statement(input_file, test_config.output_directory)

        # Assert
        assert result.output_path.exists()
        assert len(result.statement.transactions) == 91

        # Verify output file content
        df = pd.read_excel(result.output_path)
        assert len(df) == 91
        assert set(df.columns) == {"Date", "Description", "Currency", "Amount", "Payment Method"}
        assert df["Payment Method"].iloc[0] == "Macro VISA"

# tests/performance/test_performance.py
class TestPerformance:
    """Performance tests for large-scale processing"""

    @pytest.mark.performance
    def test_large_file_processing(self):
        """Test processing of large files"""
        # Generate large test file
        large_file = self.create_large_test_file(10000)  # 10k transactions

        start_time = time.time()
        processor = create_processor(test_config)
        result = processor.process_statement(large_file, Path("output"))
        processing_time = time.time() - start_time

        # Performance assertions
        assert processing_time < 30.0  # Should process in under 30 seconds
        assert len(result.statement.transactions) == 10000

    @pytest.mark.performance
    def test_batch_processing_performance(self):
        """Test batch processing performance"""
        files = [self.create_test_file(1000) for _ in range(10)]  # 10 files, 1k transactions each

        start_time = time.time()
        processor = create_async_processor(test_config)
        results = asyncio.run(processor.process_batch(files, Path("output")))
        processing_time = time.time() - start_time

        # Performance assertions
        assert processing_time < 60.0  # Should process all files in under 1 minute
        assert len(list(results)) == 10
```

### Test Coverage Goals

- **Unit Tests**: 95% coverage for domain models and services
- **Integration Tests**: 100% coverage for all supported file formats
- **Performance Tests**: Baseline performance metrics for large files
- **Contract Tests**: API contracts between layers
- **Property-Based Tests**: Edge cases and data validation

---

## 📊 Migration Strategy

### Zero-Regression Approach

#### Phase-by-Phase Migration

1. **Parallel Implementation**: Build new architecture alongside existing code
2. **Feature Flags**: Toggle between old and new implementations
3. **Gradual Migration**: Move one file format at a time
4. **Comprehensive Testing**: Maintain 100% test coverage throughout
5. **Performance Monitoring**: Ensure no performance degradation

#### Migration Steps

```python
# Step 1: Feature Flag Implementation
class FeatureFlags:
    """Feature flags for gradual migration"""

    def __init__(self):
        self.use_new_pdf_parser = os.getenv("USE_NEW_PDF_PARSER", "false").lower() == "true"
        self.use_new_xls_parser = os.getenv("USE_NEW_XLS_PARSER", "false").lower() == "true"
        self.use_new_validation = os.getenv("USE_NEW_VALIDATION", "false").lower() == "true"
        self.use_new_repository = os.getenv("USE_NEW_REPOSITORY", "false").lower() == "true"

# Step 2: Hybrid Implementation
def process_statement_hybrid(input_path: Path, output_path: Path) -> ProcessingResult:
    """Hybrid implementation using feature flags"""
    flags = FeatureFlags()

    if flags.use_new_pdf_parser and input_path.suffix.lower() == '.pdf':
        # Use new architecture
        parser_factory = create_new_parser_factory()
        parser = parser_factory.create_parser(input_path)
        statement = parser.parse(input_path)

        if flags.use_new_repository:
            repository = create_new_repository()
            repository.save_statement(statement, output_path)
        else:
            # Use legacy save method
            legacy_save_statement(statement, output_path)
    else:
        # Use legacy implementation
        return legacy_process_statement(input_path, output_path)

# Step 3: Gradual Rollout
migration_phases = [
    {"name": "PDF Parser", "flag": "USE_NEW_PDF_PARSER", "week": 1},
    {"name": "XLS Parser", "flag": "USE_NEW_XLS_PARSER", "week": 2},
    {"name": "Validation", "flag": "USE_NEW_VALIDATION", "week": 3},
    {"name": "Repository", "flag": "USE_NEW_REPOSITORY", "week": 4},
]
```

#### Rollback Strategy

```python
# Emergency rollback capability
class RollbackManager:
    """Manage rollbacks during migration"""

    def __init__(self):
        self.rollback_flags = {
            "EMERGENCY_ROLLBACK": False,
            "ROLLBACK_PDF_PARSER": False,
            "ROLLBACK_XLS_PARSER": False,
            "ROLLBACK_VALIDATION": False,
        }

    def check_rollback_conditions(self) -> bool:
        """Check if rollback is needed"""
        # Monitor error rates, performance metrics
        error_rate = self.get_current_error_rate()
        performance_degradation = self.check_performance_degradation()

        return error_rate > 0.05 or performance_degradation > 0.2

    def execute_rollback(self, component: str) -> None:
        """Execute rollback for specific component"""
        self.rollback_flags[f"ROLLBACK_{component}"] = True
        logger.warning(f"Rollback executed for {component}")
```

---

## 📈 Benefits & ROI Analysis

### Immediate Benefits

#### Maintainability Improvements

- **Reduced Complexity**: Single-responsibility classes vs. 1,200-line monolith
- **Easier Debugging**: Isolated components enable focused troubleshooting
- **Faster Development**: Clear interfaces accelerate feature development
- **Reduced Risk**: Changes isolated to specific components

#### Code Quality Enhancements

- **SOLID Compliance**: All principles properly implemented
- **Design Patterns**: Industry-standard patterns for common problems
- **Type Safety**: Comprehensive type annotations with mypy validation
- **Test Coverage**: Enhanced testability with isolated components

### Long-term Benefits

#### Scalability & Performance

- **Async Processing**: Handle high-volume batch processing
- **Memory Efficiency**: Streaming for large files
- **Parallel Processing**: Multi-threaded execution for better throughput
- **Resource Optimization**: Efficient resource utilization

#### Extensibility & Future-Proofing

- **New Banks**: Add support without modifying existing code
- **New Formats**: Plugin architecture for additional file types
- **Output Formats**: Easy addition of CSV, JSON, database outputs
- **Enterprise Features**: Ready for advanced requirements

### ROI Metrics

#### Development Velocity

- **Feature Development**: 50% faster due to clear interfaces
- **Bug Fixes**: 70% faster due to isolated components
- **Testing**: 60% faster due to focused unit tests
- **Code Reviews**: 40% faster due to smaller, focused changes

#### Maintenance Costs

- **Reduced Debugging Time**: Clear separation of concerns
- **Lower Regression Risk**: Isolated changes with comprehensive tests
- **Easier Onboarding**: New developers understand modular structure faster
- **Documentation**: Self-documenting code through clear interfaces

---

## 🎯 Success Criteria & Metrics

### Technical Metrics

#### Code Quality

- [ ] **Cyclomatic Complexity**: Reduce from 15+ to <5 per function
- [ ] **Lines of Code per Class**: Maximum 100 lines per class
- [ ] **Test Coverage**: Maintain 90%+ with enhanced unit test coverage
- [ ] **Type Coverage**: 100% type annotation coverage with mypy

#### Performance Metrics

- [ ] **Processing Speed**: No degradation in single-file processing
- [ ] **Memory Usage**: 30% reduction through streaming optimizations
- [ ] **Batch Processing**: 3x improvement in multi-file processing
- [ ] **Startup Time**: <2 seconds for CLI initialization

#### Maintainability Metrics

- [ ] **Coupling**: Reduce coupling between components by 80%
- [ ] **Cohesion**: Increase cohesion within components by 60%
- [ ] **Documentation**: 100% API documentation coverage
- [ ] **Code Duplication**: Eliminate 90% of duplicated logic

### Business Metrics

#### Development Efficiency

- [ ] **Feature Development Time**: 50% reduction in new feature implementation
- [ ] **Bug Resolution Time**: 70% reduction in average bug fix time
- [ ] **Code Review Time**: 40% reduction in review cycle time
- [ ] **Onboarding Time**: 60% reduction for new team members

#### Quality Metrics

- [ ] **Bug Rate**: 80% reduction in production bugs
- [ ] **Regression Rate**: 90% reduction in regression issues
- [ ] **Customer Satisfaction**: Maintain 100% accuracy while improving speed
- [ ] **Technical Debt**: 75% reduction in technical debt score

---

## 🛠️ Implementation Timeline

### Phase 1: Foundation (Weeks 1-2)

#### **Week 1**

- [ ] Domain model implementation
- [ ] Repository pattern setup
- [ ] Basic strategy pattern for parsers
- [ ] Unit tests for domain models

#### **Week 2**

- [ ] Factory pattern implementation
- [ ] Integration tests setup
- [ ] Feature flag infrastructure
- [ ] Parallel implementation start

### Phase 2: SOLID Implementation (Weeks 3-4)

#### **Week 3**

- [ ] Single responsibility refactoring
- [ ] Open/closed principle implementation
- [ ] Extension points for new banks
- [ ] Enhanced unit test coverage

#### **Week 4**

- [ ] Dependency inversion implementation
- [ ] Abstract interfaces creation
- [ ] Dependency injection setup
- [ ] Integration test updates

### Phase 3: Advanced Patterns (Weeks 5-6)

#### **Week 5**

- [ ] Command pattern implementation
- [ ] Observer pattern for events
- [ ] Builder pattern for complex objects
- [ ] Event-driven architecture

#### **Week 6**

- [ ] Advanced error handling
- [ ] Comprehensive logging
- [ ] Performance monitoring
- [ ] Documentation updates

### Phase 4: Enterprise Features (Weeks 7-8)

#### **Week 7**

- [ ] Async processing pipeline
- [ ] Configuration management
- [ ] CLI interface implementation
- [ ] Performance optimizations

#### **Week 8**

- [ ] Final testing and validation
- [ ] Performance benchmarking
- [ ] Documentation completion
- [ ] Migration execution

---

## 🔧 Development Guidelines

### Code Standards

#### Naming Conventions

```python
# Classes: PascalCase
class StatementProcessor:
    pass

# Functions/Methods: snake_case
def process_statement(input_path: Path) -> Statement:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3

# Private methods: _snake_case
def _parse_transaction_line(self, line: str) -> Transaction:
    pass
```

#### Type Annotations

```python
# Always use type hints
def process_batch(
    self,
    file_paths: list[Path],
    output_dir: Path
) -> list[ProcessingResult]:
    pass

# Use Protocol for interfaces
class FileReader(Protocol):
    def read(self, path: Path) -> bytes: ...

# Use Union for optional types
def get_balance(self) -> Balance | None:
    pass
```

#### Error Handling

```python
# Specific exceptions
class StatementParsingError(Exception):
    """Raised when statement parsing fails"""
    pass

# Proper error context
try:
    statement = parser.parse(file_path)
except StatementParsingError as e:
    logger.error(f"Failed to parse {file_path}: {e}")
    raise ProcessingError(f"Cannot process {file_path}") from e
```

### Testing Standards

#### Test Organization

```python
# Arrange-Act-Assert pattern
def test_process_statement_success(self):
    # Arrange
    input_path = Path("test.pdf")
    processor = StatementProcessor()

    # Act
    result = processor.process(input_path)

    # Assert
    assert result.success
    assert len(result.transactions) > 0
```

#### Mock Usage

```python
# Use specific mocks
@patch('src.infrastructure.adapters.PdfPlumberAdapter')
def test_pdf_parsing(self, mock_pdf_adapter):
    mock_pdf_adapter.extract_text.return_value = "test content"
    # Test implementation
```

### Documentation Standards

#### Docstring Format

```python
def process_statement(self, input_path: Path, output_dir: Path) -> ProcessingResult:
    """
    Process a financial statement file.

    Args:
        input_path: Path to the input statement file
        output_dir: Directory for output files

    Returns:
        ProcessingResult containing processing details

    Raises:
        StatementParsingError: If the file cannot be parsed
        ValidationError: If the statement fails validation

    Example:
        >>> processor = StatementProcessor()
        >>> result = processor.process_statement(Path("statement.pdf"), Path("output"))
        >>> print(f"Processed {len(result.transactions)} transactions")
    """
```

---

## 📚 Resources & References

### Design Patterns

- **Strategy Pattern**: Gang of Four Design Patterns
- **Factory Pattern**: Effective Java by Joshua Bloch
- **Repository Pattern**: Domain-Driven Design by Eric Evans
- **Command Pattern**: Design Patterns: Elements of Reusable Object-Oriented Software

### Architecture Principles

- **SOLID Principles**: Clean Code by Robert C. Martin
- **Hexagonal Architecture**: Ports and Adapters by Alistair Cockburn
- **Clean Architecture**: Clean Architecture by Robert C. Martin
- **Domain-Driven Design**: Domain-Driven Design by Eric Evans

### Python Best Practices

- **Type Hints**: PEP 484, 585, 604
- **Dataclasses**: PEP 557
- **Protocols**: PEP 544
- **Modern Python**: Effective Python by Brett Slatkin

### Testing Resources

- **Test-Driven Development**: Test Driven Development by Kent Beck
- **Testing Patterns**: xUnit Test Patterns by Gerard Meszaros
- **Python Testing**: Python Testing with pytest by Brian Okken

---

## 🎉 Conclusion

This comprehensive architectural transformation plan provides a roadmap for evolving the Financial Statement Processor from a functional but monolithic design to a clean, modular, enterprise-ready architecture. The phased approach ensures zero regression while delivering significant improvements in maintainability, extensibility, and performance.

### Key Achievements

1. **SOLID Compliance**: Full implementation of all SOLID principles
2. **Design Patterns**: Strategic use of proven patterns for common problems
3. **Clean Architecture**: Hexagonal architecture with clear separation of concerns
4. **Enterprise Ready**: Async processing, configuration management, and CLI interface
5. **Zero Regression**: Careful migration strategy with comprehensive testing

### Next Steps

1. **Review and Approval**: Stakeholder review of the proposed architecture
2. **Team Preparation**: Training on new patterns and practices
3. **Environment Setup**: Development environment configuration
4. **Phase 1 Execution**: Begin with domain model implementation
5. **Continuous Monitoring**: Track metrics and adjust as needed

The transformation will result in a robust, scalable, and maintainable system that serves as a foundation for future enhancements and enterprise requirements.

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Status**: Ready for Implementation
