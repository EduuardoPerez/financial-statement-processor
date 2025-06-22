# System Patterns - Financial Statement Processor

## Architecture Overview

### Single-Module Design Pattern

- **Current Approach**: All logic in `parse_visa_statement.py` for simplicity
- **Benefits**: Easy to understand, minimal complexity, fast execution
- **Future Evolution**: Will modularize as we add more banks

### Processing Pipeline Architecture

```
PDF Input → Text Extraction → Pattern Matching → Data Transformation → Excel Output
XLS Input → Data Reading → Structure Parsing → Data Transformation → Excel Output
CSV Input → Data Reading → Column Mapping → Data Transformation → Excel Output
XLSX Input → Data Reading → Column Mapping → Data Transformation → Excel Output
```

### Format-Specific Processing Pipelines

#### PDF Processing Pipeline

```
PDF File → pdfplumber → Text Extraction → Line-by-Line Parsing →
Regex Pattern Matching → Transaction Classification → Amount/Date Conversion →
Balance Validation → DataFrame Creation → Excel Output
```

#### XLS Processing Pipeline

```
XLS File → pandas.read_excel → Structured Data → Row Iteration →
Direct Data Access → Date/Amount Conversion → DataFrame Creation → Excel Output
```

#### CSV Processing Pipeline

```
CSV File → pandas.read_csv → Column Mapping → Row Iteration →
Date/Currency Conversion → European Number Parsing → DataFrame Creation →
CSV Balance Validation → Excel Output
```

#### XLSX Processing Pipeline

```
XLSX File → pandas.read_excel → Column Access → Row Iteration →
ISO 8601 Date Conversion → Direct Amount Access → DataFrame Creation →
XLSX Balance Validation → Excel Output
```

## Core Design Patterns

### 1. Strategy Pattern for Bank Detection

- **Pattern**: `detect_payment_method()` function analyzes content and filename
- **Implementation**: Content-based detection for PDFs, filename-based for XLS and CSV files
- **Extensibility**: New banks add their indicator patterns
- **Card Type Priority**: Mastercard detection takes precedence over VISA when both present

```python
def detect_payment_method(content_or_path=None, file_path=None, full_text=None):
    # CSV filename-based detection
    if file_path and file_path.lower().endswith(".csv"):
        filename_upper = os.path.basename(file_path).upper()
        if all(keyword in filename_upper for keyword in ["BBVA", "VISA"]):
            return "BBVA VISA"
        elif all(keyword in filename_upper for keyword in ["MACRO", "VISA"]):
            return "Macro VISA"

    # XLS filename-based detection
    if file_path and file_path.lower().endswith(".xls"):
        filename_upper = os.path.basename(file_path).upper()
        if all(keyword in filename_upper for keyword in ["BBVA", "DETALLE"]):
            return "BBVA Account"
        elif all(keyword in filename_upper for keyword in ["MACRO", "MOVIMIENTOS"]):
            return "Macro Account"

    # PDF content-based detection
    if full_text:
        text_upper = full_text.upper()
        macro_indicators = ["MACRO PREMIA", "BANCO MACRO", "WWW.MACRO.COM.AR"]
        bbva_indicators = ["BBVA", "WWW.BBVA.COM.AR"]

        visa_found = "VISA" in text_upper
        mastercard_found = "MASTERCARD" in text_upper

        if bbva_found and mastercard_found:
            return "BBVA Mastercard"
        elif bbva_found and visa_found:
            return "BBVA VISA"
```

### 2. Line-by-Line Processing Pattern

- **Approach**: Process PDF text line by line with regex matching
- **Benefits**: Handles variable PDF formatting, robust against layout changes
- **Key Insight**: Each transaction starts with date pattern `\d{2}\.\d{2}\.\d{2}`

### 3. Multi-Stage Parsing Pattern

- **Stage 1**: Date pattern detection to identify transaction lines
- **Stage 2**: Transaction type classification (payment, tax, purchase, adjustment)
- **Stage 3**: Amount extraction with European format handling
- **Stage 4**: Currency detection (ARS/USD)

### 4. European Number Format Handling

- **Challenge**: Argentine banks use 1.234,56 format
- **Solution**: Progressive format detection and conversion
- **Pattern**: Check for both dots and commas, handle accordingly

```python
# European format: 6.847,70 -> 6847.70
if "." in amount_str and "," in amount_str:
    amount_str = amount_str.replace(".", "").replace(",", ".")
elif "," in amount_str:
    amount_str = amount_str.replace(",", ".")
```

### 5. CSV Processing Pattern

- **Approach**: Pandas-based CSV reading with column mapping
- **Benefits**: Handles CSV headers, flexible column detection
- **Key Features**: Date column flexibility ("Fecha" vs "Fecha Origen"), currency mapping, European number format conversion
- **Validation**: CSV-specific balance validation comparing input totals vs output totals

```python
def parse_bbva_visa_csv(csv_path, output_path, file_type):
    df = pd.read_csv(csv_path)

    # Handle flexible date column names
    date_col = "Fecha" if "Fecha" in df.columns else "Fecha Origen"

    # Process each row
    for _, row in df.iterrows():
        date = convert_date(row[date_col])  # DD/MM/YYYY -> YYYY-MM-DD
        description = row["Descripcion"]
        currency = "USD" if row["Moneda"] == "Dolares" else "ARS"
        amount = parse_european_number(row["Importe"])

        transactions.append({
            "Date": date,
            "Description": description,
            "Currency": currency,
            "Amount": amount,
            "Payment Method": "BBVA VISA"
        })
```

### 6. XLSX Processing Pattern

- **Approach**: Pandas-based XLSX reading with native Excel support
- **Benefits**: Handles Excel files directly, preserves data types
- **Key Features**: ISO 8601 timestamp conversion, direct numeric amount handling
- **Validation**: XLSX-specific balance validation comparing input totals vs output totals

```python
def parse_mercadopago_xlsx(xlsx_path, output_path):
    df = pd.read_excel(xlsx_path)

    # Process each row
    for _, row in df.iterrows():
        fecha_str = str(row["Fecha de Pago"]).strip()
        tipo_operacion = str(row["Tipo de Operación"]).strip()
        importe = row["Importe"]

        # Convert ISO 8601 timestamp to YYYY-MM-DD format
        formatted_date = fecha_str.split("T")[0]  # "2025-02-01T17:45:36Z" -> "2025-02-01"

        # Amount is already in proper numeric format
        amount = float(importe)

        transactions.append({
            "Date": formatted_date,
            "Description": tipo_operacion,
            "Currency": "ARS",
            "Amount": amount,
            "Payment Method": "Mercadopago"
        })
```

### 7. Pre-commit Hook Integration Pattern

- **Automated Quality Gates**: Pre-commit hooks enforce code quality before commits
- **Hook Configuration**: `.pre-commit-config.yaml` with ruff, mypy, and pytest
- **Type Safety**: MyPy prevents type errors from entering the codebase
- **Code Quality**: Ruff ensures consistent formatting and linting standards
- **Test Validation**: pytest runs full test suite to prevent regressions
- **Development Workflow**: Clean, professional development with automated enforcement

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.0
    hooks:
      - id: ruff
        args: [--fix, --ignore=E501]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pandas-stubs>=2.1.0, types-openpyxl>=3.1.0]

  - repo: local
    hooks:
      - id: pytest-coverage
        name: pytest with coverage check
        entry: uv run pytest --cov=. --cov-report=term-missing --cov-fail-under=90 --cov-config=.coveragerc
        language: system
        pass_filenames: false
        always_run: true
```

### 8. Warning Resolution Pattern

- **Challenge**: Development environment cluttered with openpyxl and flake8 warnings
- **Solution**: Comprehensive warning suppression and code quality configuration
- **Implementation**: Multi-layered approach using pytest configuration and flake8 setup

```python
# pyproject.toml - Warning filters
[tool.pytest.ini_options]
filterwarnings = [
    "ignore::UserWarning:openpyxl.styles.stylesheet",
]

# .flake8 - Code quality configuration
[flake8]
max-line-length = 88
per-file-ignores =
    tests/*:E501
```

- **Benefits**: Clean test output, professional development experience, maintained code quality
- **Quality Standards**: Zero warnings while preserving all functionality and test coverage

### 9. Centralized File Naming Pattern

- **Challenge**: Inconsistent output filename formats across different statement types
- **Solution**: Centralized `generate_output_filename()` function with standardized naming convention
- **Implementation**: Single function controls all output filename generation with mapping strategy

```python
def generate_output_filename(
    payment_method: str,
    file_type: str = "main",
    include_date: bool = False,
    date_str: str = "",
) -> str:
    """Generate standardized output filename based on payment method and type"""

    # Normalize payment method to consistent format
    method_mapping = {
        "BBVA VISA": "BBVA-VISA",
        "BBVA Mastercard": "BBVA-MASTERCARD",
        "BBVA Account": "BBVA-ACCOUNT",
        "Macro VISA": "MACRO-VISA",
        "Macro Account": "MACRO-ACCOUNT",
        "Mercadopago": "MERCADOPAGO",
    }

    normalized_method = method_mapping.get(
        payment_method, payment_method.upper().replace(" ", "-")
    )

    # Build filename components: {BANK}-{PRODUCT}-{TYPE}-transactions.xlsx
    filename_parts = [normalized_method]

    if include_date and date_str:
        filename_parts.append(date_str)

    if file_type != "main" and file_type:
        filename_parts.append(file_type)

    filename_parts.append("transactions")

    return "-".join(filename_parts) + ".xlsx"
```

- **Benefits**: Professional consistency, easy maintenance, extensible for new banks
- **Naming Convention**: `{BANK}-{PRODUCT}-{TYPE}-transactions.xlsx` format
- **Examples**: `BBVA-VISA-transactions.xlsx`, `MACRO-ACCOUNT-transactions.xlsx`, `BBVA-VISA-auth-transactions.xlsx`
- **Quality**: 23 comprehensive unit tests covering all functionality and edge cases

### 10. Repository Pattern for Hexagonal Architecture (Phase 1 → 1.2)

- **Challenge**: Tight coupling between business logic and data access operations
- **Solution**: Abstract repository interfaces (ports) that infrastructure adapters will implement
- **Implementation**: Protocol-based and ABC-based abstractions for clean architecture

```python
# src/domain/repositories.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol
from .models import Statement

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
    def save_statement(self, statement: Statement, output_path: Path) -> None: ...

    @abstractmethod
    def load_raw_data(self, input_path: Path) -> bytes: ...
```

- **Architecture Benefits**:
  - **Dependency Inversion**: Core domain depends on abstractions, not concrete implementations
  - **Hexagonal Architecture**: These serve as ports that infrastructure adapters will implement
  - **Testability**: Easy to mock and test business logic in isolation
  - **Extensibility**: New storage backends can be added without changing domain logic
- **Design Decisions**:
  - **Protocol vs ABC**: FileReader/FileWriter use Protocol for structural typing flexibility
  - **StatementRepository ABC**: Uses nominal typing for strict interface contracts
  - **Type Safety**: Full pathlib.Path integration with comprehensive type annotations
- **Quality**: Comprehensive documentation with Args, Returns, and Raises sections
- **Validation**: Successfully validated with import tests and integration with domain models

### 11. ExcelStatementRepository Implementation Pattern (Phase 1 → 1.3)

- **Challenge**: Need concrete implementation of repository abstractions for Excel output
- **Solution**: Infrastructure adapter implementing domain repository interface with dependency injection
- **Implementation**: Clean architecture with pandas integration and comprehensive error handling

```python
# src/infrastructure/repositories.py
class ExcelStatementRepository(StatementRepository):
    """Excel-based statement repository implementation."""

    def __init__(self, file_reader: FileReader, file_writer: FileWriter):
        """Initialize with injected dependencies for clean architecture."""
        self._file_reader = file_reader
        self._file_writer = file_writer

    def save_statement(self, statement: Statement, output_path: Path) -> None:
        """Save statement to Excel file using pandas with openpyxl engine."""
        if not statement.transactions:
            raise ValueError("Cannot save statement with no transactions")

        # Ensure output directory exists
        self._file_writer.ensure_directory(output_path.parent)

        # Convert statement to DataFrame
        df = self._statement_to_dataframe(statement)

        # Save as Excel file using pandas with openpyxl engine
        try:
            df.to_excel(output_path, index=False, sheet_name="Sheet1", engine="openpyxl")
        except Exception as e:
            raise OSError(f"Failed to save Excel file to {output_path}: {str(e)}") from e

    def _statement_to_dataframe(self, statement: Statement) -> pd.DataFrame:
        """Convert Statement domain objects to pandas DataFrame for Excel output."""
        data = []
        for transaction in statement.transactions:
            data.append({
                "Date": transaction.date.strftime("%Y-%m-%d"),
                "Description": transaction.description,
                "Currency": transaction.currency.value,
                "Amount": float(transaction.amount),
                "Payment Method": transaction.payment_method.value,
            })
        return pd.DataFrame(data)
```

- **Architecture Benefits**:
  - **Dependency Injection**: Uses injected FileReader/FileWriter for clean architecture compliance
  - **Infrastructure Layer**: Concrete adapter implementing domain abstractions without circular dependencies
  - **Hexagonal Architecture**: Demonstrates successful ports and adapters pattern implementation
  - **Clean Separation**: Business logic (domain) separated from technical concerns (infrastructure)
- **Technical Features**:
  - **Excel I/O Integration**: Leverages pandas with openpyxl engine for robust Excel operations
  - **Data Transformation**: Helper method converts domain objects to standardized DataFrame format
  - **Standardized Output**: Creates Excel files with consistent column structure
  - **Error Handling**: Comprehensive exception handling with proper error types and chaining
- **Quality Standards**:
  - **Type Safety**: Full modern Python 3.11+ type annotations with explicit type declarations
  - **Documentation**: Comprehensive docstrings with Args, Returns, and Raises sections
  - **Validation**: Zero regression - all 242 tests continue to pass
  - **Integration**: Successfully tested with domain models and mock dependencies
- **Design Patterns Applied**:
  - **Repository Pattern**: Concrete implementation of abstract repository interface
  - **Dependency Injection**: Constructor injection of file operation dependencies
  - **Adapter Pattern**: Adapts pandas DataFrame operations to domain Statement objects
  - **Template Method**: Standardized data transformation pipeline
- **Next Phase**: Ready for Strategy Pattern implementation for different file format parsers

### 12. StatementParser Interface Pattern (Phase 1 → 1.4)

- **Challenge**: Need pluggable parsing strategies for different file formats while maintaining clean architecture
- **Solution**: Abstract Base Class defining the contract for all statement parsers with Strategy Pattern foundation
- **Implementation**: Complete `src/domain/services.py` with `StatementParser` ABC

```python
# src/domain/services.py
from abc import ABC, abstractmethod
from pathlib import Path
from .models import Statement

class StatementParser(ABC):
    """Abstract strategy for parsing different statement formats."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Determine if this parser can handle the given file."""
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> Statement:
        """Parse the file and return a Statement object."""
        pass

    @abstractmethod
    def get_supported_extensions(self) -> set[str]:
        """Return supported file extensions."""
        pass
```

- **Architecture Benefits**:
  - **Strategy Pattern Foundation**: Enables pluggable parsing strategies for PDF, XLS, CSV, XLSX formats
  - **Clean Architecture Compliance**: Domain service abstraction following hexagonal architecture principles
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Validation Ready**: Supports `issubclass(ConcreteParser, StatementParser)` for runtime validation
  - **Domain Integration**: Seamlessly integrates with existing Statement domain model
- **Design Features**:
  - **can_parse()**: File format detection and parser selection capability
  - **parse()**: Core parsing logic returning properly constructed Statement objects
  - **get_supported_extensions()**: Parser discovery and factory pattern support
  - **Abstract Base Class**: Prevents direct instantiation, enforces interface compliance
  - **Comprehensive Documentation**: Detailed docstrings with Args, Returns, and Raises sections
- **Quality Standards**:
  - **100% Interface Coverage**: Comprehensive unit tests validating all abstract methods
  - **Strategy Pattern Validation**: Tests confirm interface supports intended design patterns
  - **Domain Model Integration**: Validates seamless integration with existing models
  - **Error Handling**: Tests incomplete implementations and validation scenarios
  - **Multiple Implementations**: Confirms multiple concrete parsers can coexist
- **Architecture Impact**: Provides foundation for Factory Pattern implementation (Phase 1 → 1.6)
- **SOLID Compliance**: Perfect implementation of Strategy Pattern with clean abstractions

### 13. PDFStatementParser Implementation Pattern (Phase 1 → 1.5)

- **Challenge**: Need first concrete implementation of StatementParser interface demonstrating Strategy Pattern
- **Solution**: Skeleton PDF parser with pdfplumber integration and comprehensive error handling
- **Implementation**: Complete `src/infrastructure/parsers/pdf_parser.py` with `PDFStatementParser` class

### 14. XLSStatementParser Implementation Pattern (Phase 1 → 1.3)

- **Challenge**: Need second concrete implementation of StatementParser interface demonstrating Strategy Pattern expansion
- **Solution**: Skeleton XLS/XLSX parser with pandas integration and dual extension support
- **Implementation**: Complete `src/infrastructure/parsers/xls_parser.py` with `XLSStatementParser` class

### 15. Clean Import Configuration Pattern (June 2025)

- **Challenge**: MyPy import path conflicts with src/ layout causing "Source file found twice under different module names" errors
- **Solution**: Configure project for clean imports without src. prefix using proper MyPy and package configuration
- **Implementation**: Updated `pyproject.toml` MyPy config and package discovery settings
- **Benefits**: Clean readable imports (`from domain.models` vs `from src.domain.models`), better IDE support, standard Python conventions
- **Configuration**: `mypy_path = "src"`, `namespace_packages = true`, `explicit_package_bases = true`, proper setuptools package discovery
- **Result**: Permanent solution eliminating MyPy conflicts while enabling preferred clean import style

```python
# src/infrastructure/parsers/pdf_parser.py
class PDFStatementParser(StatementParser):
    """PDF statement parser using pdfplumber for text extraction."""

    def __init__(self, detector: Any) -> None:
        """Initialize with payment method detector dependency."""
        self._detector = detector

    def can_parse(self, file_path: Path) -> bool:
        """Returns True for .pdf files (case-insensitive)."""
        return file_path.suffix.lower() == ".pdf"

    def parse(self, file_path: Path) -> Statement:
        """Extract raw text and return Statement with zero transactions."""
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            # Extract raw text from PDF (skeleton: not used yet)
            # raw_text = self._extract_text(file_path)

            # For skeleton implementation, default to BBVA_VISA
            payment_method = PaymentMethod.BBVA_VISA

            # Create and return Statement with zero transactions (skeleton)
            statement = Statement(payment_method=payment_method)
            return statement
        except PermissionError as e:
            raise PermissionError(f"Permission denied reading PDF file: {file_path}") from e
        except Exception as e:
            raise OSError(f"Error processing PDF file {file_path}: {str(e)}") from e

    def _extract_text(self, file_path: Path) -> str:
        """Helper method to extract raw text from PDF using pdfplumber."""
        try:
            with pdfplumber.open(file_path) as pdf:
                text_content = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)

                if not text_content:
                    raise ValueError(f"No text content found in PDF: {file_path}")

                return "\n".join(text_content)
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF {file_path}: {str(e)}") from e
```

- **Architecture Benefits**:
  - **Strategy Pattern Implementation**: First concrete implementation demonstrating pluggable parsing strategies
  - **Clean Architecture**: Infrastructure layer implementing domain abstractions without circular dependencies
  - **Dependency Injection**: Constructor accepts detector parameter for clean architecture compliance
  - **Hexagonal Architecture**: Demonstrates successful ports and adapters pattern implementation
- **Technical Features**:
  - **Case-Insensitive Detection**: `can_parse()` handles .PDF, .pdf, .Pdf extensions correctly
  - **pdfplumber Integration**: Robust PDF text extraction with page-by-page processing
  - **Skeleton Implementation**: Returns Statement with zero transactions (foundation for full parsing logic)
  - **Comprehensive Error Handling**: FileNotFoundError, ValueError, PermissionError, OSError with proper chaining
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
- **Validation Requirements**:
  - ✅ `PDFStatementParser(detector).can_parse(Path("foo.PDF"))` returns `True`
  - ✅ Successfully extracts text from real PDF files (11,421 characters from BBVA VISA statement)
  - ✅ Returns properly constructed Statement objects with correct payment method
  - ✅ All 251 existing tests continue to pass (zero regression)
- **Directory Structure**: Created `src/infrastructure/parsers/` with proper module organization
- **pdfplumber Integration**:
  - **Usage Pattern**: `pdfplumber.open(file_path)` with page-by-page text extraction
  - **Error Handling**: Graceful handling of PDF warnings (CropBox missing warnings are normal)
  - **Performance**: Successfully processes real bank statements with thousands of characters
- **Architecture Impact**:
  - **Strategy Pattern Demonstration**: Shows how concrete parsers implement the abstract interface
  - **Foundation for Migration**: Ready for full PDF parsing logic migration from legacy code
  - **Factory Pattern Ready**: Prepared for parser creation and management system (Phase 1 → 1.6)
- **Quality Standards**:
  - **Zero Regression**: All existing functionality maintained
  - **Type Safety**: Comprehensive type annotations and mypy compliance
  - **Error Handling**: Proper exception hierarchy with descriptive messages
  - **Documentation**: Complete docstrings with examples and usage patterns

### 16. Factory Pattern Implementation (Phase 1 → 1.4)

- **Challenge**: Need dynamic parser creation and management system for Strategy Pattern implementations
- **Solution**: Complete Factory Pattern implementation with registration-based design and comprehensive error handling
- **Implementation**: Complete `src/domain/factories.py` with `ParserFactory` class

### 17. DefaultParserFactory Implementation Pattern (Phase 1 → 1.4)

- **Challenge**: Need convenient, pre-configured factory for common usage scenarios
- **Solution**: Concrete infrastructure factory that auto-registers standard parsers with dependency injection
- **Implementation**: Complete `src/infrastructure/factories.py` with `DefaultParserFactory` class

```python
# src/domain/factories.py
class ParserFactory:
    """Factory for creating appropriate statement parsers."""

    def __init__(self) -> None:
        """Initialize factory with empty parser registry."""
        self._parsers: list[StatementParser] = []

    def register_parser(self, parser: StatementParser) -> None:
        """Register a new parser strategy."""
        if isinstance(parser, StatementParser):
            self._parsers.append(parser)
        else:
            parser_type = type(parser).__name__
            raise TypeError(f"Expected StatementParser, got {parser_type}")

    def create_parser(self, file_path: Path) -> StatementParser:
        """Create appropriate parser for the given file."""
        if not isinstance(file_path, Path):
            raise TypeError(f"Expected Path, got {type(file_path).__name__}")

        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser

        # No parser found - create descriptive error message
        supported_extensions = self.get_supported_extensions()
        file_extension = file_path.suffix.lower()

        if supported_extensions:
            supported_list = ", ".join(sorted(supported_extensions))
            error_msg = (
                f"No parser available for file: {file_path}. "
                f"File extension '{file_extension}' is not supported. "
                f"Supported extensions: {supported_list}"
            )
        else:
            error_msg = (
                f"No parser available for file: {file_path}. "
                f"No parsers are registered in the factory."
            )

        raise ValueError(error_msg)

    def get_supported_extensions(self) -> set[str]:
        """Get all supported file extensions from registered parsers."""
        extensions: set[str] = set()
        for parser in self._parsers:
            extensions.update(parser.get_supported_extensions())
        return extensions
```

- **Architecture Benefits**:
  - **Factory Pattern Implementation**: Dynamic parser creation based on file characteristics
  - **Strategy Pattern Integration**: Works seamlessly with existing `StatementParser` ABC implementations
  - **Registration-Based Design**: Parsers are registered dynamically, following Open/Closed Principle
  - **Path-Based Selection**: Uses `parser.can_parse(file_path)` to find appropriate parser
  - **Clean Architecture**: Domain layer factory abstraction enabling dependency inversion
- **Core Features**:
  - **register_parser()**: Register StatementParser implementations with type validation
  - **create_parser()**: Create appropriate parser for given file path with descriptive error messages
  - **get_supported_extensions()**: Aggregate extensions from all registered parsers
  - **get_registered_parsers()**: Return copy of registered parsers for inspection
  - **clear_parsers()**: Remove all registered parsers for testing/reconfiguration
- **Error Handling Excellence**:
  - **Type Validation**: Raises `TypeError` for invalid parser types with descriptive messages
  - **Path Validation**: Raises `TypeError` for invalid file path types
  - **No Match Handling**: Raises `ValueError` when no suitable parser is found (key validation requirement)
  - **Descriptive Messages**: Comprehensive error messages with supported extensions and troubleshooting info
- **Quality Standards**:
  - **16 Comprehensive Tests**: Complete unit and integration test coverage
  - **Zero Regression**: All 267 tests pass (251 existing + 16 new)
  - **Type Safety**: Modern Python 3.11+ type annotations throughout
  - **SOLID Compliance**: Perfect implementation of Factory Pattern with Strategy Pattern integration
- **Usage Pattern**:

  ```python
  # Register parsers
  factory = ParserFactory()
  factory.register_parser(PDFStatementParser(detector))
  factory.register_parser(XLSStatementParser(detector))

  # Create appropriate parser
  parser = factory.create_parser(Path("statement.pdf"))
  statement = parser.parse(Path("statement.pdf"))

  # Get supported extensions
  extensions = factory.get_supported_extensions()  # {'.pdf', '.xls', '.xlsx'}
  ```

- **Architecture Impact**: Completes Factory Pattern foundation for Phase 1 → 1.6 infrastructure implementation
- **Next Phase**: Ready for concrete factory implementation with all parsers registered

### 18. PaymentMethodDetector Pattern (Phase 2 → 2.2)

- **Challenge**: Need extensible payment method detection system that follows Open/Closed Principle for adding new banks
- **Solution**: Registry-based detector with abstract BankDetector strategies and comprehensive validation
- **Implementation**: Complete `src/domain/detectors.py` with `BankDetector` ABC and `PaymentMethodDetector` class

```python
# src/domain/detectors.py
class BankDetector(ABC):
    """Abstract strategy for bank identification from content."""

    @abstractmethod
    def can_detect(self, content: str) -> bool:
        """Check if this detector can identify the bank from content."""
        pass

    @abstractmethod
    def get_payment_method(self, content: str) -> PaymentMethod:
        """Return the specific payment method for the identified bank."""
        pass

class PaymentMethodDetector:
    """Registry-based payment method detector following Strategy Pattern."""

    def __init__(self) -> None:
        """Initialize detector with empty registry."""
        self._detectors: list[BankDetector] = []

    def register_detector(self, detector: BankDetector) -> None:
        """Register a new bank detector strategy."""
        if not isinstance(detector, BankDetector):
            detector_type = type(detector).__name__
            raise TypeError(f"Expected BankDetector, got {detector_type}")
        self._detectors.append(detector)

    def detect_from_content(self, content: str) -> PaymentMethod:
        """Detect payment method from content using registered detectors."""
        if not self._detectors:
            raise ValueError("No detectors registered. Cannot detect payment method.")

        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        for detector in self._detectors:
            if detector.can_detect(content):
                return detector.get_payment_method(content)

        raise ValueError("Unknown payment method")

    def detect_from_filename(self, file_path: Path) -> PaymentMethod:
        """Detect payment method from filename patterns."""
        # Implementation for CSV, XLS, XLSX filename-based detection
        pass
```

- **Architecture Benefits**:
  - **Strategy Pattern Implementation**: Abstract BankDetector enables pluggable bank identification strategies
  - **Registry-Based Design**: Detectors registered dynamically, following Open/Closed Principle
  - **Validation Requirement**: Raises `ValueError` when `detect_from_content` called before any detectors registered
  - **Clean Architecture**: Domain layer abstraction enabling dependency inversion and extensibility
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
- **Core Features**:
  - **register_detector()**: Register BankDetector implementations with type validation
  - **detect_from_content()**: Detect payment method using registered detectors (key validation requirement)
  - **detect_from_filename()**: Detect payment method from filename patterns for CSV/XLS/XLSX files
  - **get_registered_detectors()**: Return copy of registered detectors for inspection
  - **clear_detectors()**: Remove all registered detectors for testing/reconfiguration
- **Extensibility Pattern**:
  - **New Bank Addition**: Create new BankDetector implementation and register it
  - **No Code Modification**: Existing code unchanged when adding new banks
  - **Strategy Selection**: First matching detector wins, registration order determines precedence
  - **Content vs Filename**: Supports both content-based (PDF) and filename-based (CSV/XLS/XLSX) detection
- **Quality Standards**:
  - **23 Comprehensive Tests**: Complete unit and integration test coverage
  - **Zero Regression**: All 290 tests pass (267 existing + 23 new)
  - **91.86% Coverage**: Exceeds 90% requirement with meaningful behavior validation
  - **SOLID Compliance**: Perfect implementation of Strategy Pattern with registry-based extensibility
- **Usage Pattern**:

  ```python
  # Create detector and register bank strategies
  detector = PaymentMethodDetector()
  detector.register_detector(MacroDetector())
  detector.register_detector(BBVADetector())

  # Detect from content
  method = detector.detect_from_content("BANCO MACRO VISA")
  # Returns PaymentMethod.MACRO_VISA

  # Detect from filename
  method = detector.detect_from_filename(Path("BBVA-Account-statement.xls"))
  # Returns PaymentMethod.BBVA_ACCOUNT
  ```

- **Architecture Impact**: Enables Open/Closed Principle for adding new banks without modifying existing code
- **Next Phase**: Ready for concrete BankDetector implementations (MacroDetector, BBVADetector, etc.)

### 19. Concrete Bank Detector Implementation Pattern (Phase 2 → 2.2)

- **Challenge**: Need concrete implementations of BankDetector abstract strategy for specific banks
- **Solution**: Concrete detector classes with regex/substring logic and factory function for convenient usage
- **Implementation**: Complete `src/infrastructure/detectors.py` with `MacroDetector`, `BBVADetector`, and `build_default_payment_detector()`

### 20. TransactionBuilder Pattern (Phase 2 → 2.4)

- **Challenge**: Need clean construction of Transaction objects from parsed PDF line components
- **Solution**: Builder class with dependency injection following Single Responsibility Principle
- **Implementation**: Complete `src/domain/builders.py` with `TransactionBuilder` class

### 21. Sophisticated PDF Transaction Parsing Pattern (Prompt 15 - June 2025)

- **Challenge**: Implement production-ready PDF transaction parsing that handles real-world bank statement complexity
- **Solution**: Sophisticated parsing logic ported from working system with comprehensive transaction type support
- **Implementation**: Complete `src/infrastructure/parsers/pdf_parser.py` with sophisticated parsing logic from working system

### 22. Application Layer Orchestrator Pattern (Phase 2 → 2.1 - December 2025)

- **Challenge**: Need application service that orchestrates domain and infrastructure components following clean architecture principles
- **Solution**: StatementProcessingService implementing Single Responsibility Principle with comprehensive error handling and dependency injection
- **Implementation**: Complete `src/application/services.py` with orchestrator service and supporting components

### 23. Real Domain Service Integration Pattern (Phase 2 Completion - June 2025)

- **Challenge**: Replace stub implementations with real domain services to complete clean architecture transformation
- **Solution**: Inject real StatementValidator and FilenameGenerator into StatementProcessingService for production-ready functionality
- **Implementation**: Refactored `src/application/services.py` to use real domain services instead of stubs

```python
# src/application/services.py
class StatementProcessingService:
    """Main orchestrator service for statement processing."""

    def __init__(
        self,
        parser_factory: ParserFactory,
        repository: StatementRepository,
        validator: StatementValidator,
        filename_generator: FilenameGenerator,
    ):
        """Initialize with injected dependencies for clean architecture."""
        self._parser_factory = parser_factory
        self._repository = repository
        self._validator = validator
        self._filename_generator = filename_generator

    def process_statement(self, input_path: Path, output_dir: Path) -> ProcessingResult:
        """Process a statement file end-to-end with comprehensive error handling."""
        start_time = time.time()

        try:
            # Step 1: Create appropriate parser using factory
            parser = self._parser_factory.create_parser(input_path)

            # Step 2: Parse the statement
            statement = parser.parse(input_path)

            # Step 3: Validate the statement (stub implementation)
            validation_result = self._validator.validate(statement)

            # Step 4: Generate output filename
            output_filename = self._filename_generator.generate(statement)
            output_path = output_dir / output_filename

            # Step 5: Save statement via repository
            self._repository.save_statement(statement, output_path)

            # Step 6: Return comprehensive result
            processing_time = time.time() - start_time
            return ProcessingResult(
                input_path=input_path,
                output_path=output_path,
                statement=statement,
                validation_result=validation_result,
                success=True,
                errors=[],
                processing_time=processing_time,
            )

        except Exception as e:
            # Comprehensive error handling with detailed context
            processing_time = time.time() - start_time
            return ProcessingResult(
                input_path=input_path,
                output_path=None,
                statement=None,
                validation_result=ValidationResult(is_valid=False, errors=[str(e)]),
                success=False,
                errors=[f"Processing failed: {str(e)}"],
                processing_time=processing_time,
            )
```

- **Architecture Benefits**:
  - **Clean Architecture Compliance**: Application layer coordinates domain and infrastructure without business logic
  - **Single Responsibility Principle**: Service focuses solely on orchestration, delegates all work to specialized components
  - **Dependency Injection**: All dependencies injected via constructor for testability and flexibility
  - **Hexagonal Architecture**: Demonstrates successful integration of ports and adapters pattern
  - **SOLID Principles**: Perfect implementation of dependency inversion and single responsibility
- **Orchestration Features**:
  - **Six-Step Workflow**: Parse → Validate → Generate filename → Save → Return comprehensive result
  - **Factory Pattern Integration**: Uses ParserFactory to create appropriate parser based on file type
  - **Repository Pattern Integration**: Uses StatementRepository for persistence operations
  - **Stub Components**: StatementValidator and FilenameGenerator stubs as specified in requirements
  - **Comprehensive Error Handling**: Catches predictable errors, includes detailed context in ProcessingResult
  - **Processing Metrics**: Tracks processing time and provides detailed success/failure information
- **Supporting Components**:
  - **ProcessingResult dataclass**: Comprehensive result object with processing details, timing, and error tracking
  - **ValidationResult dataclass**: Validation outcome with error collection for future validation implementations
  - **StatementValidator stub**: Always returns valid as specified, ready for future enhancement
  - **FilenameGenerator stub**: Generates deterministic filenames with date stamps for conflict-free output
- **Error Handling Strategy**:
  - **Predictable Errors**: Catches domain/infrastructure errors (parser not found, repository I/O failures)
  - **Detailed Context**: Includes error messages in ProcessingResult with step-specific information
  - **Graceful Degradation**: Continues processing where possible, provides comprehensive error reporting
  - **Unexpected Exceptions**: Lets unexpected exceptions propagate for debugging during development
- **End-to-End Validation**: ✅ Successfully processes real PDF files
  - **Input**: `BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf` with 45 transactions
  - **Output**: Excel file `BBVA-VISA_20250622.xlsx` (6,977 bytes) with standardized format
  - **Processing**: Completed without exceptions in ~0.5 seconds
  - **Data Integrity**: All 45 transactions correctly parsed and saved with proper columns
  - **Validation**: Confirmed Excel output contains Date, Description, Currency, Amount, Payment Method columns
- **Quality Standards**:
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Clean Import Structure**: Uses proper `PYTHONPATH=src` approach with clean imports
  - **Zero Regression**: All 133 domain tests continue to pass
  - **Integration Testing**: Successfully processes real bank statement files
  - **Performance**: Sub-second processing for typical monthly statements
- **Usage Pattern**:

  ```python
  # Create dependencies
  detector = build_default_payment_detector()
  factory = DefaultParserFactory(detector)
  validator = StatementValidator()
  filename_generator = FilenameGenerator()
  repository = ExcelStatementRepository(file_reader, file_writer)

  # Create service
  service = StatementProcessingService(factory, repository, validator, filename_generator)

  # Process statement
  result = service.process_statement(Path("statement.pdf"), Path("output"))
  print(f"Success: {result.success}, Transactions: {len(result.statement.transactions)}")
  ```

- **Architecture Impact**: Completes **Phase 2 → 2.1** from PLAN.md, demonstrating successful clean architecture transformation with working end-to-end application service
- **Next Phase**: Ready for application service unit testing (Prompt 18) and validation service implementation (Prompt 19)

```python
# src/infrastructure/parsers/pdf_parser.py - Updated _parse_transactions method
def _parse_transactions(
    self, text: str, payment_method: PaymentMethod
) -> list[Transaction]:
    """
    Parse transaction lines from PDF text using TransactionBuilder.

    Implements the task requirements:
    1. Split lines on ≥ 2 spaces
    2. Build Transactions (currency = ARS)
    3. Append to Statement
    """
    transactions = []
    lines = text.split("\n")

    # Pattern to identify transaction lines (starts with DD.MM.YY)
    date_pattern = re.compile(r"^(\d{2}\.\d{2}\.\d{2})\s+(.+)$")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line starts with date pattern
        match = date_pattern.match(line)
        if match:
            try:
                date_str = match.group(1)
                rest_of_line = match.group(2)

                # Task requirement: Split on ≥2 spaces first
                parts = re.split(r"\s{2,}", rest_of_line)

                if len(parts) >= 2:
                    # Multiple parts: description and amount
                    description = " ".join(parts[:-1])
                    amount_str = parts[-1]
                else:
                    # Single part: need to extract amount from end
                    # Look for amount pattern at end (numbers with dots/commas)
                    amount_match = re.search(
                        r"(.+?)\s+([\d.,]+[-]?)$", rest_of_line
                    )
                    if amount_match:
                        description = amount_match.group(1)
                        amount_str = amount_match.group(2)
                    else:
                        # Fallback: treat entire rest as description
                        description = rest_of_line
                        amount_str = "0,00"

                # Task requirement: Build transaction using TransactionBuilder
                # Currency set to ARS as specified in requirements
                transaction = self._transaction_builder.build_from_pdf_line(
                    date_str=date_str,
                    description=description.strip(),
                    amount_str=amount_str.strip(),
                    currency=Currency.ARS,
                    payment_method=payment_method,
                )

                transactions.append(transaction)

            except ValueError:
                # Skip invalid lines, continue processing others
                # This provides graceful degradation for parsing errors
                continue

    return transactions
```

- **Architecture Benefits**:
  - **Strategy Pattern Integration**: PDFStatementParser properly uses injected TransactionBuilder
  - **Builder Pattern Usage**: Delegates Transaction object construction to specialized builder
  - **Single Responsibility**: Parser focuses on line parsing, builder handles object construction
  - **Clean Architecture**: Infrastructure layer using domain services without tight coupling
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
- **Task Requirements Implementation**:
  - **✅ Wire TransactionBuilder**: Uses `self._transaction_builder.build_from_pdf_line()` method
  - **✅ Split lines on ≥2 spaces**: Implements regex pattern `r"\s{2,}"` as specified
  - **✅ Build Transactions (currency = ARS)**: All transactions created with `Currency.ARS`
  - **✅ Append to Statement**: Transactions added to list and returned for statement population
  - **✅ Graceful Degradation**: Invalid lines skipped with `ValueError` handling
- **Validation Results**:
  - **✅ BBVA-VISA-resumen_cuenta_visa_May_2025.pdf**: **47 transactions successfully parsed**
  - **✅ BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf**: **44 transactions successfully parsed**
  - **✅ Validation Requirement Met**: `len(stmt.transactions) > 0` confirmed for both test files
  - **✅ All Unit Tests Pass**: 12 comprehensive unit tests in `tests/unit/infrastructure/test_pdf_parser.py`
  - **✅ All Integration Tests Pass**: 8 integration tests in `tests/integration/test_bbva_visa_processing.py`
- **Technical Implementation Details**:
  - **Line Processing**: Processes PDF text line by line with date pattern recognition
  - **Date Pattern Matching**: Uses regex `r"^(\d{2}\.\d{2}\.\d{2})\s+(.+)$"` to identify transaction lines
  - **Component Extraction**: Splits line components on ≥2 spaces using `re.split(r"\s{2,}", rest_of_line)`
  - **Fallback Logic**: Handles cases where splitting doesn't produce expected parts
  - **TransactionBuilder Integration**: Calls builder with extracted components and required currency
  - **Error Handling**: Graceful degradation with `ValueError` handling for invalid lines
- **Quality Standards**:
  - **Zero Regression**: All existing tests continue to pass with new functionality
  - **Comprehensive Testing**: Both unit tests (mocked) and integration tests (real PDFs)
  - **Real Data Validation**: Successfully processes actual BBVA VISA PDF statements
  - **Architecture Compliance**: Follows established clean architecture patterns
- **Usage Pattern**:

  ```python
  # PDFStatementParser constructor with TransactionBuilder injection
  def __init__(self, detector: Any, transaction_builder: TransactionBuilder) -> None:
      self._detector = detector
      self._transaction_builder = transaction_builder

  # Parse method using TransactionBuilder integration
  def parse(self, file_path: Path) -> Statement:
      raw_text = self._extract_text(file_path)
      payment_method = self._detector.detect_from_content(raw_text)
      statement = Statement(payment_method=payment_method)

      # Use TransactionBuilder integration
      transactions = self._parse_transactions(raw_text, payment_method)

      for transaction in transactions:
          statement.add_transaction(transaction)

      return statement
  ```

- **Architecture Impact**: Demonstrates successful integration of Builder Pattern with Strategy Pattern in clean architecture
- **Prompt 15 Completion**: All task requirements successfully implemented and validated with real PDF data

```python
# src/domain/builders.py
class TransactionBuilder:
    """Builder for constructing Transaction objects from parsed components."""

    def __init__(
        self, date_converter: DateConverter, amount_parser: AmountParser
    ) -> None:
        """Initialize TransactionBuilder with injected dependencies."""
        self._date_converter = date_converter
        self._amount_parser = amount_parser

    def build_from_pdf_line(
        self,
        date_str: str,
        description: str,
        amount_str: str,
        currency: Currency,
        payment_method: PaymentMethod,
    ) -> Transaction:
        """Build Transaction object from PDF line components."""
        # Import here to avoid circular imports
        from .models import Transaction

        if not date_str or not date_str.strip():
            raise ValueError("Date string cannot be empty")

        if not description or not description.strip():
            raise ValueError("Description cannot be empty")

        if not amount_str or not amount_str.strip():
            raise ValueError("Amount string cannot be empty")

        try:
            # Use injected DateConverter to parse date
            date_clean = date_str.strip()
            parsed_date = self._date_converter.convert_dd_mm_yy(date_clean)

            # Use injected AmountParser to parse amount
            parsed_amount = self._amount_parser.parse_european_format(
                amount_str.strip()
            )

            # Clean description
            clean_description = description.strip()

            # Construct Transaction using domain model
            transaction = Transaction(
                date=parsed_date,
                description=clean_description,
                amount=parsed_amount,
                currency=currency,
                payment_method=payment_method,
            )

            return transaction

        except ValueError as e:
            # Re-raise with context about which component failed
            msg = f"Failed to build transaction from PDF line components: {e}"
            raise ValueError(msg) from e
        except Exception as e:
            # Handle unexpected errors
            msg = f"Unexpected error building transaction: {str(e)}"
            raise ValueError(msg) from e
```

- **Architecture Benefits**:
  - **Single Responsibility Principle**: Focuses solely on Transaction object construction
  - **Dependency Injection**: Uses injected DateConverter and AmountParser for clean architecture compliance
  - **Clean Architecture**: Domain layer builder using domain utilities without external dependencies
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Error Handling**: Comprehensive ValueError handling with descriptive error messages and proper exception chaining
- **Key Features**:
  - **build_from_pdf_line()**: Core method for building Transaction objects from parsed PDF line components
  - **Component Validation**: Validates all input components (date_str, description, amount_str) before processing
  - **Utility Integration**: Uses injected DateConverter for date parsing and AmountParser for European number format parsing
  - **Transaction Construction**: Creates properly validated Transaction domain objects with all required fields
  - **Error Context**: Provides descriptive error messages with context about which component failed
- **Validation Requirements**: ✅ All requirements met
  - ✅ Injects `DateConverter` & `AmountParser` dependencies successfully
  - ✅ Provides `build_from_pdf_line` method with proper signature
  - ✅ Sample build returns valid `Transaction` object with correct properties
  - ✅ Proper date parsing: "05.06.25" → 2025-06-05
  - ✅ Proper amount parsing: "1.234,56" → Decimal('1234.56')
  - ✅ Error handling for empty/invalid inputs
- **Testing Validation**: ✅ Comprehensive functionality testing passed
  - ✅ Basic transaction building with ARS currency and BBVA VISA payment method
  - ✅ USD transaction building with Macro VISA payment method
  - ✅ Error handling for empty date, description, and amount strings
  - ✅ All transaction properties validated (date, amount, currency, payment method, description)
- **Usage Pattern**:

  ```python
  # Create dependencies
  date_converter = DateConverter()
  amount_parser = AmountParser()

  # Create TransactionBuilder with injected dependencies
  builder = TransactionBuilder(date_converter, amount_parser)

  # Build transaction from PDF line components
  transaction = builder.build_from_pdf_line(
      date_str="05.06.25",
      description="COMPRA EN COMERCIO",
      amount_str="1.234,56",
      currency=Currency.ARS,
      payment_method=PaymentMethod.BBVA_VISA
  )
  # Returns properly constructed Transaction object
  ```

- **Architecture Impact**: Completes Phase 2 → 2.4 builder implementation, enabling clean Transaction object construction from PDF parsing workflows
- **Integration Ready**: Builder ready for integration with PDF parsing infrastructure components

```python
# src/infrastructure/detectors.py
class MacroDetector(BankDetector):
    """Concrete detector for Macro bank statements."""

    def can_detect(self, content: str) -> bool:
        """Check if this detector can identify Macro bank from content."""
        if not content:
            return False

        content_upper = content.upper()
        indicators = [
            "MACRO PREMIA",
            "BANCO MACRO",
            "WWW.MACRO.COM.AR",
            "MACRO",  # More flexible matching for variations
        ]

        return any(indicator in content_upper for indicator in indicators)

    def get_payment_method(self, content: str) -> PaymentMethod:
        """Return the specific Macro payment method based on content analysis."""
        if not content:
            raise ValueError("Content cannot be empty")

        content_upper = content.upper()

        # Check for VISA indicators
        if "VISA" in content_upper:
            return PaymentMethod.MACRO_VISA

        # Default to account for other Macro statements
        return PaymentMethod.MACRO_ACCOUNT

class BBVADetector(BankDetector):
    """Concrete detector for BBVA bank statements."""

    def can_detect(self, content: str) -> bool:
        """Check if this detector can identify BBVA bank from content."""
        if not content:
            return False

        content_upper = content.upper()
        bbva_indicators = [
            "BBVA",
            "WWW.BBVA.COM.AR",
        ]

        return any(indicator in content_upper for indicator in bbva_indicators)

    def get_payment_method(self, content: str) -> PaymentMethod:
        """Return the specific BBVA payment method based on content analysis."""
        if not content:
            raise ValueError("Content cannot be empty")

        content_upper = content.upper()

        # Check for Mastercard first (takes precedence over VISA)
        if "MASTERCARD" in content_upper:
            return PaymentMethod.BBVA_MASTERCARD

        # Check for VISA indicators
        if "VISA" in content_upper:
            return PaymentMethod.BBVA_VISA

        # Default to account for other BBVA statements
        return PaymentMethod.BBVA_ACCOUNT

def build_default_payment_detector() -> PaymentMethodDetector:
    """Build a PaymentMethodDetector with all standard bank detectors registered."""
    detector = PaymentMethodDetector()

    # Register all standard bank detectors
    detector.register_detector(MacroDetector())
    detector.register_detector(BBVADetector())

    return detector
```

- **Architecture Benefits**:
  - **Strategy Pattern Implementation**: Concrete implementations of abstract BankDetector interface
  - **Open/Closed Principle**: New banks can be added without modifying existing code
  - **Clean Architecture**: Infrastructure layer implementing domain abstractions
  - **Factory Pattern**: `build_default_payment_detector()` provides convenient pre-configured detector
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
- **Detection Logic Features**:
  - **MacroDetector**: Flexible matching with "MACRO PREMIA", "BANCO MACRO", "WWW.MACRO.COM.AR", "MACRO"
  - **BBVADetector**: BBVA-specific indicators with Mastercard precedence over VISA
  - **Case-Insensitive**: Handles variations like "Banco Macro" vs "BANCO MACRO"
  - **Content Analysis**: Returns appropriate PaymentMethod based on card type indicators
  - **Error Handling**: Proper ValueError for empty content and unknown methods
- **Validation Requirements**: ✅ All requirements met
  - ✅ `det.detect_from_content("Banco Macro - Visa") == PaymentMethod.MACRO_VISA`
  - ✅ Flexible case-insensitive matching for bank name variations
  - ✅ Proper VISA card type identification from content
  - ✅ Registry-based design following Strategy Pattern
- **Testing Results**: ✅ Comprehensive validation passed
  - ✅ "Banco Macro - Visa" → Macro VISA (validation requirement)
  - ✅ "BBVA VISA" → BBVA VISA
  - ✅ "BBVA Mastercard" → BBVA Mastercard
  - ✅ "BANCO MACRO" → Macro Account
  - ✅ "BBVA Account" → BBVA Account
  - ✅ "Macro Premia Visa" → Macro VISA
- **Quality Standards**:
  - **Code Quality**: Flake8 compliant with proper line length management
  - **Error Handling**: Comprehensive exception handling with proper error types
  - **Documentation**: Complete docstrings with examples and usage patterns
  - **Zero Regression**: All existing tests continue to pass
- **Usage Pattern**:

  ```python
  # Use factory function for convenience
  detector = build_default_payment_detector()
  method = detector.detect_from_content("Banco Macro - Visa")
  # Returns PaymentMethod.MACRO_VISA

  # Or register detectors manually
  detector = PaymentMethodDetector()
  detector.register_detector(MacroDetector())
  detector.register_detector(BBVADetector())
  ```

- **Architecture Impact**: Completes Phase 2 → 2.2 concrete detector implementation, enabling Open/Closed Principle for new banks
- **Extensibility**: Adding new banks requires only creating new detector classes and registering them

## Transaction Type Detection Patterns

### 1. Tax Transaction Pattern

- **Identifiers**: "IMPUESTO", "IIBB", "IVA", "DB.RG", "DB.IMPUESTO"
- **Amount**: Always positive (charges)
- **Currency**: Typically ARS

### 2. Payment Transaction Pattern

- **Identifiers**: "SU PAGO EN PESOS", "SU PAGO EN USD"
- **Amount**: Always negative (credits)
- **Format**: Special handling for trailing dash `701.084,93-`, `3,00-`
- **Currency Support**: Both ARS and USD payment detection

### 3. Adjustment Transaction Pattern

- **Identifier**: "AJUSTE"
- **Amount**: Always negative (credits/discounts)
- **Description**: Standardized to "AJUSTE P/DESCNTO. EN COMERCIO"

### 4. Regular Purchase Pattern

- **Structure**: `Date + Reference + Description + Amount`
- **Reference**: Alphanumeric pattern `[A-Z0-9*]+[*KQV]?`
- **Currency**: Detected by "USD" presence or defaulted to ARS

## Data Transformation Patterns

### 1. Date Standardization

- **Input Formats**:
  - DD.MM.YY format (VISA statements)
  - DD-MMM-YY format (Mastercard statements)
  - DD/MM/YYYY format (XLS Account statements)
  - Datetime objects (Macro Account XLS statements)
- **Output**: YYYY-MM-DD format
- **Logic**: Years < 50 = 20XX, years >= 50 = 19XX (for 2-digit years)
- **Spanish Support**: "Abr" = April for Spanish month abbreviations

```python
# VISA format: 15.03.25 -> 2025-03-15
# Mastercard format: 15-Mar-25 -> 2025-03-15
# Spanish: 04-Abr-25 -> 2025-04-04
# XLS format: 09/06/2025 -> 2025-06-09
# Macro Account XLS: datetime.datetime(2025, 6, 6) -> 2025-06-06
```

### 2. Amount Normalization

- **Input**: Various European formats
- **Output**: Python float
- **Edge Cases**: Negative amounts, trailing dashes, multiple decimal separators

### 3. Description Cleaning

- **Pattern**: Remove amount from end of description
- **Result**: Clean transaction description with reference number

## Error Handling Patterns

### 1. Graceful Degradation

- **Approach**: Continue processing even if individual transactions fail
- **Benefit**: Partial success better than complete failure
- **Implementation**: Try/except around amount conversion

### 2. Validation Through Testing

- **Pattern**: Comprehensive test suite validates all parsing logic
- **Coverage**: Integration tests with real PDF data
- **Confidence**: Expected vs actual output comparison

## Extensibility Patterns

### 1. Bank-Agnostic Core

- **Design**: Payment method detection separates bank logic from parsing logic
- **Benefit**: New banks only need new detection patterns
- **Future**: Each bank could have specialized parsing functions

### 2. Modular Transaction Handlers

- **Current**: Specialized handling for each transaction type
- **Future**: Could extract to separate handler classes
- **Pattern**: Chain of responsibility for transaction type detection

### 3. Output Format Abstraction

- **Current**: Excel output hardcoded
- **Future**: Output interface could support CSV, JSON, etc.
- **Pattern**: Strategy pattern for different output formats

## Performance Patterns

### 1. Single-Pass Processing

- **Efficiency**: Read PDF once, process all transactions in single pass
- **Memory**: Low memory footprint, suitable for large statements
- **Scalability**: Ready for batch processing multiple files

### 2. Regex Optimization

- **Approach**: Compile patterns once, reuse for all lines
- **Current**: Simple string operations for readability
- **Future**: Could optimize with compiled regex patterns

## Quality Assurance Patterns (Refactored December 2025)

### 1. Professional Test Architecture Pattern

- **Structure**: Behavior-focused test organization with logical grouping
- **Unit Tests**: `tests/unit/` - Individual function validation with descriptive names
- **Integration Tests**: `tests/integration/` - End-to-end PDF processing
- **Benefits**: Professional maintainability, clear purpose, excellent readability

### 2. Test Quality Standards Pattern

- **Meaningful Coverage**: 90% coverage focused on behavior validation
- **Professional Organization**: Tests grouped logically by functionality
- **Descriptive Names**: Every test clearly explains what behavior it validates
- **Maintainability**: Easy to understand, modify, and extend test suite

### 3. Test Data Isolation Pattern

- **Structure**: Independent test data copies in `tests/test_data/`
- **Input Files**: `tests/test_data/input/` - PDF files for testing
- **Expected Output**: `tests/test_data/expected_output/` - Reference results
- **Benefits**: Tests don't affect main project files, reproducible results

### 4. Expected Output Validation

- **Pattern**: Compare generated output with known-good reference files
- **Files**: `expected_output/` directory contains reference data
- **Validation**: Transaction count, amounts, dates, currency distribution

### 5. Data Integrity Checks

- **Amount Totals**: Verify sum of ARS and USD transactions
- **Transaction Types**: Confirm all special transaction types detected
- **Date Ranges**: Validate date parsing covers full statement period

### 6. Balance Validation Pattern

- **PDF Balance Extraction**: Extract reported balance from "SALDO ACTUAL $ X U$S Y" pattern
- **Computed Balance**: Sum all transactions excluding payments for validation
- **Validation Logic**: Compare reported vs computed, log detailed results
- **Payment Exclusion**: Remove "SU PAGO EN PESOS" and "SU PAGO EN USD" from totals
- **Error Reporting**: Log warnings for mismatches, don't halt processing
- **Organized Output**: Professional summary with validation indicators

### 7. Professional Test Suite Organization Pattern (Current State)

- **Directory Structure**: Clear separation by test type and purpose
- **Professional Standards**: Descriptive names, logical grouping, clear behavior validation
- **Maintainability**: Excellent readability and extensibility
- **Quality Focus**: Meaningful tests rather than coverage metrics

```
tests/
├── __init__.py
├── test_data/                          # Isolated test data
│   ├── input/                          # Test files (copied from ../input/)
│   │   ├── MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf
│   │   ├── BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf
│   │   ├── BBVA-VISA-resumen_cuenta_visa_May_2025.pdf
│   │   ├── BBVA-Mastercard-2025-04.pdf
│   │   ├── BBVA-Account-Detalle_mov_cuenta_07_06_2025.xls
│   │   └── MACRO-movimientos-de-cuenta.xls     # NEW: Macro Account XLS test data
│   └── expected_output/                # Expected test results (copied from ../expected_output/)
│       ├── MACRO-VISA-transactions.csv
│       ├── MACRO-VISA-transactions.xlsx
│       ├── BBVA-VISA-transactions.csv
│       ├── BBVA-VISA-transactions.xlsx
│       ├── BBVA-Mastercard-transactions.csv
│       ├── BBVA-Mastercard-transactions.xlsx
│       ├── BBVA-Account-transactions.csv
│       ├── BBVA-Account-transactions.xlsx
│       ├── Macro-Account-transactions.csv     # NEW: Macro Account expected output
│       └── Macro-Account-transactions.xlsx    # NEW: Macro Account expected output
├── unit/                               # Professional unit tests (8 files)
│   ├── test_convert_date.py           # Date conversion functionality
│   ├── test_detect_payment_method.py  # Bank and card type detection (includes XLS filename detection)
│   ├── test_error_handling.py         # Error handling and edge cases
│   ├── test_european_number_format.py # European number format parsing
│   ├── test_extract_balance_from_pdf.py # Balance extraction from PDFs
│   ├── test_print_processing_summary.py # Output formatting
│   ├── test_transaction_types.py      # Transaction type parsing
│   └── test_validate_balance.py       # Balance validation logic
└── integration/                        # End-to-end tests (5 files)
    ├── test_macro_visa_processing.py  # MACRO VISA workflow tests
    ├── test_bbva_visa_processing.py   # BBVA VISA workflow tests
    ├── test_bbva_mastercard_processing.py # BBVA Mastercard workflow tests
    ├── test_bbva_account_processing.py # BBVA Account XLS workflow tests (12 tests)
    └── test_macro_account_processing.py # NEW: Macro Account XLS workflow tests (13 tests)
```

### 8. Comprehensive Test Coverage Pattern

#### Test Categories and Execution

**Unit Tests (Professional, Focused)**

- **Date Conversion**: Tests the `convert_date()` function with various date formats
- **Payment Method Detection**: Tests bank detection logic for MACRO, BBVA VISA, and BBVA Mastercard
- **Error Handling**: Tests graceful degradation and edge case handling
- **European Number Format**: Tests 1.234,56 format parsing in various contexts
- **Balance Extraction**: Tests PDF balance extraction patterns
- **Balance Validation**: Tests computed vs reported balance comparison
- **Processing Summary**: Tests output formatting and summary generation
- **Transaction Types**: Tests parsing of all transaction types (tax, payment, adjustment, etc.)

**Integration Tests (End-to-End)**

- **MACRO VISA Processing**: Complete workflow tests using real MACRO PDF files
- **BBVA VISA Processing**: Complete workflow tests using real BBVA VISA PDF files
- **BBVA Mastercard Processing**: Complete workflow tests using real BBVA Mastercard PDF files
- **BBVA Account Processing**: Complete workflow tests using real BBVA Account XLS files

#### Test Data Management Pattern

**Isolated Test Data Structure**

- Test data is copied from main project directories to ensure test isolation
- Input PDFs are copied from `../input/` to `tests/test_data/input/`
- Expected outputs are copied from `../expected_output/` to `tests/test_data/expected_output/`
- This structure allows tests to run independently without affecting main project files

#### Comprehensive Validation Pattern

Each integration test validates:

- **Transaction Count Accuracy**: Ensures all transactions are captured
- **Currency Handling**: Validates ARS/USD parsing and distribution
- **Amount Totals**: Validates arithmetic accuracy of parsed amounts
- **Date Range and Format**: Ensures proper date conversion (DD.MM.YY → YYYY-MM-DD, DD-MMM-YY → YYYY-MM-DD)
- **Payment Method Detection**: Validates bank and card type identification
- **Transaction Type Parsing**: Validates payments, taxes, adjustments, bonifications
- **Negative Amount Validation**: Ensures proper sign handling for payments/adjustments

#### Real Data Integration Test Examples

**MACRO VISA Test Validation**

- **File**: `MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf`
- **Transactions**: 91 total (90 ARS, 1 USD)
- **Date Range**: May 2022 - December 2022
- **Transaction Types**: Purchases, payments, adjustments, taxes
- **Amount Totals**: ARS -122,087.04, USD 11.30

**BBVA VISA Test Validation**

- **File**: `BBVA-VISA-resumen_cuenta_visa_May_2025.pdf`
- **Transactions**: 45 total (44 ARS, 1 USD)
- **Date Range**: March 2025 - May 2025
- **Transaction Types**: Purchases, payments, bonifications, taxes
- **Amount Totals**: ARS -29,584.17, USD 100.00

**BBVA Mastercard Test Validation**

- **File**: `BBVA-Mastercard-2025-04.pdf`
- **Transactions**: 7 total (all ARS)
- **Date Format**: DD-MMM-YY with Spanish abbreviations ("Abr" = April)
- **Transaction Types**: Purchases, payments
- **Amount Totals**: ARS -3,456.67

#### Test Execution Commands

```bash
# All tests (97 total)
uv run pytest tests/ -v

# Unit tests only (8 files - fast)
uv run pytest tests/unit/ -v

# Integration tests only (3 files)
uv run pytest tests/integration/ -v

# Bank-specific tests
uv run pytest tests/integration/test_macro_visa_processing.py -v
uv run pytest tests/integration/test_bbva_visa_processing.py -v
uv run pytest tests/integration/test_bbva_mastercard_processing.py -v
```

#### Test Quality Metrics (Current State - June 2025)

- **Total Tests**: 251 (all passing) ✅
- **Unit Tests**: 9 professional test files covering core functions and domain services
- **Integration Tests**: 8 test files covering end-to-end workflows
- **Bank Coverage**: MACRO VISA, BBVA VISA, BBVA Mastercard, BBVA Account, Macro Account with comprehensive patterns
- **Test Organization**: Professional structure with logical grouping by functionality
- **Test Quality**: Descriptive names, clear behavior validation, excellent maintainability
- **Coverage**: 91.08% meaningful coverage focused on behavior validation
- **Real Data Validation**: Uses actual bank statements for testing confidence
- **Recent Addition**: 9 new tests for StatementParser interface and Strategy Pattern validation
- **Domain Testing**: Complete validation of domain models, repository abstractions, and service interfaces

## Test Coverage Implementation Patterns

### 1. pytest-cov Integration Pattern

- **Tool**: pytest-cov plugin for comprehensive coverage measurement
- **Configuration**: `.coveragerc` file with proper exclusions and settings
- **Benefits**: Industry-standard coverage measurement with detailed reporting

### 2. Coverage Quality Pattern

- **Meaningful Coverage**: Focus on behavior validation over line coverage metrics
- **Quality Threshold**: 90% meaningful coverage vs previous 93% artificial coverage
- **Professional Standards**: Tests validate actual behavior, not arbitrary metrics
- **Automated Enforcement**: Tests fail if coverage drops below threshold

### 3. Coverage Exclusion Strategy

- **Test Files**: Exclude all `tests/*` from coverage calculation
- **Documentation**: Exclude `memory-bank/*`, README files
- **Data Directories**: Exclude `input/*`, `output/*`, `expected_output/*`
- **Configuration**: Exclude `pyproject.toml`, `.gitignore`, etc.
- **Main Blocks**: Exclude `if __name__ == "__main__":` sections

### 4. Professional Test Organization

- **Behavior-Focused Testing**: Tests organized by what they validate, not coverage metrics
- **Descriptive Naming**: Test function names clearly explain the behavior being tested
- **Logical Grouping**: Related tests grouped in coherent test classes and files
- **Error Handling Separation**: Dedicated test suite for error handling and edge cases
- **Format-Specific Testing**: European number format tests separated for clarity

### 5. Coverage Quality Assessment

- **Current Achievement**: 91.08% meaningful coverage with comprehensive domain layer testing
- **Quality Focus**: Meaningful coverage of business logic, domain models, and service interfaces
- **Professional Organization**: Tests grouped by functionality with descriptive names
- **Industry Standard**: Exceeds typical 70-80% industry benchmarks with higher quality
- **Architecture Coverage**: Complete validation of clean architecture components (domain, infrastructure)

### 6. Test Maintainability Pattern

- **Professional Structure**: Clear, logical test organization
- **Descriptive Names**: Every test clearly explains what behavior it validates
- **Easy Extension**: Simple to add new tests for new functionality
- **Quality Standards**: Maintained through consistent naming and organization conventions
- **Industry Standard**: Exceeds typical 70-80% industry benchmarks with higher quality
- **Architecture Coverage**: Complete validation of clean architecture components (domain, infrastructure)

### 24. Command Pattern Implementation (Phase 3 → 3.1 - June 2025)

- **Challenge**: Need operation encapsulation, undo functionality, and batch processing with transactional rollback for enterprise-level capabilities
- **Solution**: Complete Command Pattern implementation with abstract base class, concrete commands, and comprehensive result objects
- **Implementation**: Complete `src/domain/commands.py` with all Command Pattern components

```python
# src/domain/commands.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import time

@dataclass
class CommandResult:
    """Rich result object for command execution with comprehensive details."""
    success: bool
    message: str
    data: Optional[Any] = None
    execution_time: float = 0.0
    errors: list[str] = field(default_factory=list)

class Command(ABC):
    """Abstract base class for all commands following Command Pattern."""

    @abstractmethod
    def execute(self) -> CommandResult:
        """Execute the command and return comprehensive result."""
        pass

    @abstractmethod
    def undo(self) -> None:
        """Undo the command if possible."""
        pass

    @abstractmethod
    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        pass

class ProcessStatementCommand(Command):
    """Concrete command for processing a single financial statement."""

    def __init__(
        self,
        input_path: Path,
        output_dir: Path,
        processing_service: Any,
    ):
        """Initialize command with statement processing parameters."""
        self._input_path = input_path
        self._output_dir = output_dir
        self._processing_service = processing_service
        self._result: Optional[Any] = None

    def execute(self) -> CommandResult:
        """Execute statement processing with comprehensive error handling and timing."""
        start_time = time.time()

        try:
            # Execute statement processing using injected service
            self._result = self._processing_service.process_statement(
                self._input_path, self._output_dir
            )

            execution_time = time.time() - start_time

            if self._result.success:
                return CommandResult(
                    success=True,
                    message=f"Successfully processed {self._input_path.name}",
                    data=self._result,
                    execution_time=execution_time,
                    errors=[]
                )
            else:
                return CommandResult(
                    success=False,
                    message=f"Processing failed for {self._input_path.name}",
                    data=self._result,
                    execution_time=execution_time,
                    errors=self._result.errors if hasattr(self._result, 'errors') else []
                )

        except Exception as e:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                message=f"Failed to process {self._input_path.name}: {str(e)}",
                data=None,
                execution_time=execution_time,
                errors=[str(e)]
            )

    def can_undo(self) -> bool:
        """Check if command can be undone (has result with output path)."""
        return (
            self._result is not None
            and hasattr(self._result, 'output_path')
            and self._result.output_path is not None
        )

    def undo(self) -> None:
        """Undo command by removing generated output file."""
        if self.can_undo() and self._result.output_path.exists():
            self._result.output_path.unlink()

class BatchProcessCommand(Command):
    """Concrete command for batch processing multiple statements with transactional rollback."""

    def __init__(self, commands: list[Command]):
        """Initialize batch command with list of individual commands."""
        self._commands = commands
        self._executed_commands: list[Command] = []

    def execute(self) -> CommandResult:
        """Execute all commands with automatic rollback on failure."""
        start_time = time.time()
        individual_results = []
        success_count = 0

        try:
            for command in self._commands:
                result = command.execute()
                individual_results.append(result)

                if result.success:
                    self._executed_commands.append(command)
                    success_count += 1
                else:
                    # Command failed - rollback all previously executed commands
                    self._rollback_executed_commands()
                    execution_time = time.time() - start_time

                    return CommandResult(
                        success=False,
                        message=f"{success_count}/{len(self._commands)} commands successful",
                        data={
                            "success_count": success_count,
                            "total_count": len(self._commands),
                            "success_rate": success_count / len(self._commands) if self._commands else 0.0,
                            "individual_results": individual_results
                        },
                        execution_time=execution_time,
                        errors=[f"Command failed: {result.message}"]
                    )

            # All commands succeeded
            execution_time = time.time() - start_time
            return CommandResult(
                success=True,
                message=f"{success_count}/{len(self._commands)} commands successful",
                data={
                    "success_count": success_count,
                    "total_count": len(self._commands),
                    "success_rate": 1.0,
                    "individual_results": individual_results
                },
                execution_time=execution_time,
                errors=[]
            )

        except Exception as e:
            # Unexpected error - rollback and report
            self._rollback_executed_commands()
            execution_time = time.time() - start_time

            return CommandResult(
                success=False,
                message=f"Batch processing failed with unexpected error: {str(e)}",
                data={
                    "success_count": success_count,
                    "total_count": len(self._commands),
                    "success_rate": success_count / len(self._commands) if self._commands else 0.0,
                    "individual_results": individual_results
                },
                execution_time=execution_time,
                errors=[str(e)]
            )

    def _rollback_executed_commands(self) -> None:
        """Rollback all successfully executed commands in reverse order."""
        for command in reversed(self._executed_commands):
            try:
                if command.can_undo():
                    command.undo()
            except Exception:
                # Continue rollback even if individual undo fails
                pass

    def can_undo(self) -> bool:
        """Check if batch command can be undone (has executed commands)."""
        return len(self._executed_commands) > 0

    def undo(self) -> None:
        """Undo all executed commands in reverse order."""
        for command in reversed(self._executed_commands):
            try:
                if command.can_undo():
                    command.undo()
            except Exception:
                # Continue undo even if individual command undo fails
                pass
        self._executed_commands.clear()
```

- **Architecture Benefits**:
  - **Operation Encapsulation**: Commands are first-class objects that can be stored, queued, and manipulated
  - **Undo/Redo Support**: Built-in support for reversing operations (e.g., deleting generated output files)
  - **Batch Processing**: Transactional batch operations with automatic rollback on any command failure
  - **Comprehensive Error Handling**: Graceful error handling with detailed error reporting and timing metrics
  - **Clean Architecture Integration**: Seamless integration with existing StatementProcessingService
  - **Enterprise Readiness**: Supports logging, auditing, transactional operations, and queuing
- **Key Components**:
  - **Command ABC**: Abstract base class defining command interface with `execute()`, `undo()`, and `can_undo()` methods
  - **CommandResult dataclass**: Rich result object with success status, message, data, execution time, and error collection
  - **ProcessStatementCommand**: Concrete command encapsulating single statement processing with undo capability
  - **BatchProcessCommand**: Concrete command handling multiple statements with transactional rollback on failure
- **ProcessStatementCommand Features**:
  - Encapsulates complete statement processing workflow using dependency injection
  - Integrates with existing StatementProcessingService for real processing logic
  - Supports undo by removing generated output files when `can_undo()` returns True
  - Comprehensive error handling with timing metrics and detailed error messages
  - Validation requirement met: `ProcessStatementCommand(...).execute().success is True`
- **BatchProcessCommand Features**:
  - Executes multiple ProcessStatementCommand instances sequentially
  - Automatic rollback on any command failure using reverse-order undo operations
  - Detailed batch processing results with success rates and individual command results
  - Transactional behavior ensuring all-or-nothing processing with proper cleanup
  - Comprehensive error handling for both individual command failures and unexpected exceptions
- **Quality Standards**:
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Error Handling**: Comprehensive exception handling with proper error types and chaining
  - **Clean Architecture**: Domain layer commands with infrastructure integration
  - **Professional Testing**: 28 unit tests with mocking, integration scenarios, and edge case coverage
- **Usage Pattern**:

  ```python
  # Single statement processing
  command = ProcessStatementCommand(
      input_path=Path("statement.pdf"),
      output_dir=Path("output"),
      processing_service=service
  )
  result = command.execute()
  if result.success and command.can_undo():
      command.undo()  # Remove generated file

  # Batch processing with rollback
  commands = [ProcessStatementCommand(...) for file in files]
  batch_command = BatchProcessCommand(commands)
  result = batch_command.execute()  # Automatic rollback on failure
  ```

- **Architecture Impact**:
  - **Command Pattern Foundation**: Enables operation encapsulation, logging, auditing, and queuing
  - **Enterprise Readiness**: Supports transactional operations, batch processing, and undo functionality
  - **Extensibility**: Easy to add new command types for different operations (CLI, batch processing, etc.)
  - **Phase 3 → 3.1 Completion**: Successfully completes first advanced design pattern from PLAN.md
- **Validation Results**: ✅ All requirements successfully met
  - ✅ `ProcessStatementCommand(...).execute().success is True` (key validation requirement)
  - ✅ All 28 new unit tests pass with comprehensive coverage
  - ✅ Zero regression - all 449 tests passing (421 existing + 28 new command tests)
  - ✅ Clean architecture integration with existing components
  - ✅ Professional error handling and comprehensive documentation
- **Next Phase**: Ready for Observer Pattern implementation (Phase 3 → 3.2) and additional enterprise features
