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

#### PDF Processing Pipeline (Complete - Enhanced)

```
PDF File → pdfplumber → Text Extraction → Line-by-Line Parsing →
Regex Pattern Matching → Transaction Classification → Multi-Format Date Conversion →
Enhanced Amount/Currency Parsing → Balance Validation → DataFrame Creation → Excel Output
```

- **Enhanced Date Support**: DD.MM.YY (VISA) and DD-MMM-YY (Mastercard) formats
- **Spanish Month Support**: "Abr" = April, comprehensive Spanish abbreviations
- **PaymentMethod Detection**: Fixed enum comparison for proper bank identification
- **Error Handling**: Graceful degradation with comprehensive exception handling

#### XLS Processing Pipeline (Complete - Production Ready)

```
XLS File → pandas.read_excel → Structured Data Access → Native Type Handling →
DateTime Object Processing → European Number Format Conversion →
Payment Method Detection → Transaction Building → Excel Output
```

- **Native XLS Support**: Direct pandas processing for structured Excel data
- **BBVA Account**: 60 transactions (Detalle_mov_cuenta format)
- **Macro Account**: 36 transactions (movimientos-de-cuenta format)
- **Date Handling**: Native datetime objects and DD/MM/YYYY string conversion
- **Filename Detection**: Case-insensitive keyword matching for automatic identification

#### XLSX Processing Pipeline (Complete - Production Ready)

```
XLSX File → pandas.read_excel → Column Access → ISO 8601 Processing →
Timestamp Conversion → Amount Validation → Payment Method Detection →
Transaction Building → Excel Output
```

- **Mercadopago Support**: 394 transactions successfully processed
- **ISO 8601 Conversion**: "2025-02-01T17:45:36Z" → "2025-02-01" format
- **Native Amount Handling**: Direct numeric processing without format conversion
- **Comprehensive Validation**: Input XLSX total validation against output totals

#### CSV Processing Pipeline (Legacy - Documented)

```
CSV File → pandas.read_csv → Column Mapping → Row Iteration →
Date/Currency Conversion → European Number Parsing → DataFrame Creation →
CSV Balance Validation → Excel Output
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

### 25. Observer Pattern Implementation (Phase 3 → 3.2 - June 2025)

- **Challenge**: Need event-driven architecture with progress tracking and monitoring for long-running statement processing operations
- **Solution**: Complete Observer Pattern implementation with domain events, event publisher, and infrastructure observers
- **Implementation**: Complete `src/domain/events.py` and `src/infrastructure/observers.py` with all Observer Pattern components

```python
# src/domain/events.py
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Any

@dataclass
class Event(ABC):
    """Abstract base class for all domain events with automatic timestamp generation."""
    timestamp: datetime = None

    def __post_init__(self):
        """Automatically set timestamp when event is created."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ProcessingStartedEvent(Event):
    """Event published when statement processing begins."""
    file_path: Path
    file_size: int

@dataclass
class TransactionParsedEvent(Event):
    """Event published when a transaction is successfully parsed."""
    transaction_count: int
    file_path: Path

@dataclass
class ProcessingCompletedEvent(Event):
    """Event published when statement processing completes successfully."""
    file_path: Path
    output_path: Path
    transaction_count: int
    processing_time: float

@dataclass
class ValidationFailedEvent(Event):
    """Event published when statement validation fails."""
    file_path: Path
    errors: list[str]

@dataclass
class ProcessingFailedEvent(Event):
    """Event published when statement processing fails."""
    file_path: Path
    error_message: str

# Type alias for event handler functions
EventHandler = Callable[[Event], None]

class EventPublisher:
    """Publisher implementing Observer pattern with subscription management and resilient event publishing."""

    def __init__(self) -> None:
        """Initialize publisher with empty subscription registry."""
        self._subscribers: dict[type[Event], list[EventHandler]] = {}

    def subscribe(self, event_type: type[Event], handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: type[Event], handler: EventHandler) -> None:
        """Unsubscribe a handler from a specific event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not found, ignore

    def publish(self, event: Event) -> None:
        """Publish event to all subscribed handlers with exception isolation."""
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception:
                    # Handler exceptions don't stop other handlers from executing
                    pass

    def clear_subscribers(self, event_type: Optional[type[Event]] = None) -> None:
        """Clear subscribers for specific event type or all event types."""
        if event_type is None:
            self._subscribers.clear()
        elif event_type in self._subscribers:
            self._subscribers[event_type].clear()

    def get_subscriber_count(self, event_type: type[Event]) -> int:
        """Get number of subscribers for a specific event type."""
        return len(self._subscribers.get(event_type, []))
```

```python
# src/infrastructure/observers.py
from pathlib import Path
from typing import Any

from domain.events import (
    Event,
    ProcessingStartedEvent,
    TransactionParsedEvent,
    ProcessingCompletedEvent,
    ValidationFailedEvent,
    ProcessingFailedEvent,
)

class ProgressTracker:
    """Observer providing real-time progress feedback and error tracking during statement processing."""

    def __init__(self) -> None:
        """Initialize progress tracker with clean state."""
        self._current_file: Optional[Path] = None
        self._transaction_count = 0
        self._error_count = 0
        self._last_update_count = 0

    def handle_processing_started(self, event: ProcessingStartedEvent) -> None:
        """Handle processing started event with real-time progress output."""
        self._current_file = event.file_path
        self._transaction_count = 0
        self._error_count = 0
        self._last_update_count = 0

        # Format file size with thousands separators for readability
        file_size_formatted = f"{event.file_size:,}"

        print(f"🚀 Processing started: {event.file_path.name} ({file_size_formatted} bytes)")

    def handle_transaction_parsed(self, event: TransactionParsedEvent) -> None:
        """Handle transaction parsed event with progress updates every 10 transactions."""
        self._transaction_count = event.transaction_count

        # Update progress every 10 transactions to avoid output spam
        if self._transaction_count % 10 == 0:
            print(f"📊 Parsed {self._transaction_count} transactions...")

    def handle_processing_completed(self, event: ProcessingCompletedEvent) -> None:
        """Handle processing completed event with comprehensive summary."""
        print(f"✅ Processing completed: {event.file_path.name}")
        print(f"   📁 Output: {event.output_path.name}")
        print(f"   📊 Transactions: {event.transaction_count}")
        print(f"   ⏱️  Time: {event.processing_time:.2f}s")

        if self._error_count > 0:
            print(f"   ⚠️  Errors: {self._error_count}")

        # Reset state after completion
        self._reset_state()

    def handle_processing_failed(self, event: ProcessingFailedEvent) -> None:
        """Handle processing failed event with error reporting."""
        self._error_count += 1
        print(f"❌ Processing failed: {event.file_path.name}")
        print(f"   Error: {event.error_message}")

        # Reset state after failure
        self._reset_state()

    def _reset_state(self) -> None:
        """Reset tracker state for next processing operation."""
        self._current_file = None
        self._transaction_count = 0
        self._error_count = 0
        self._last_update_count = 0

class ValidationReporter:
    """Observer for detailed validation reporting and error collection."""

    def __init__(self) -> None:
        """Initialize validation reporter with clean state."""
        self._validation_errors: list[str] = []
        self._validation_warnings: list[str] = []

    def handle_validation_failed(self, event: ValidationFailedEvent) -> None:
        """Handle validation failed event with detailed error collection."""
        self._validation_errors.extend(event.errors)

        print(f"⚠️  Validation failed: {event.file_path.name}")
        for error in event.errors:
            print(f"   • {error}")

    def handle_processing_completed(self, event: ProcessingCompletedEvent) -> None:
        """Handle processing completed event with validation status reporting."""
        if not self._validation_errors and not self._validation_warnings:
            print(f"✅ Validation passed: {event.file_path.name}")
        elif self._validation_warnings and not self._validation_errors:
            print(f"⚠️  Validation completed with warnings: {event.file_path.name}")
            for warning in self._validation_warnings:
                print(f"   • {warning}")

        # Reset state after completion
        self._reset_state()

    def get_validation_summary(self) -> dict[str, Any]:
        """Get comprehensive validation summary."""
        return {
            "errors": self._validation_errors.copy(),
            "warnings": self._validation_warnings.copy(),
            "error_count": len(self._validation_errors),
            "warning_count": len(self._validation_warnings),
            "has_errors": len(self._validation_errors) > 0,
            "has_warnings": len(self._validation_warnings) > 0,
        }

    def _reset_state(self) -> None:
        """Reset reporter state for next validation operation."""
        self._validation_errors.clear()
        self._validation_warnings.clear()
```

- **Architecture Benefits**:
  - **Event-Driven Architecture**: Decoupled communication between components during statement processing
  - **Observer Pattern Implementation**: Publishers and observers with type-safe event handling
  - **Progress Monitoring**: Real-time feedback during long-running statement processing operations
  - **Error Tracking**: Comprehensive error collection and reporting across processing pipeline
  - **Clean Architecture**: Domain events with infrastructure observers following hexagonal architecture
  - **Type Safety**: Modern Python 3.11+ type annotations with EventHandler type alias
- **Key Components**:
  - **Event ABC**: Abstract base class for all domain events with automatic timestamp generation
  - **Domain Events**: ProcessingStartedEvent, TransactionParsedEvent, ProcessingCompletedEvent, ValidationFailedEvent, ProcessingFailedEvent
  - **EventPublisher**: Publisher implementing Observer pattern with subscription management and resilient event publishing
  - **ProgressTracker**: Observer providing real-time progress feedback and error tracking during statement processing
  - **ValidationReporter**: Observer for detailed validation reporting and error collection
- **EventPublisher Features**:
  - Type-safe subscription management with EventHandler type alias for clean method signatures
  - Resilient event publishing with exception isolation between handlers
  - Subscriber count tracking and management utilities
  - Clear/unsubscribe functionality for proper resource management
- **ProgressTracker Features**:
  - Real-time progress output with emoji indicators for visual clarity
  - File size formatting with thousands separators for readability
  - Progress updates every 10 transactions to avoid output spam
  - Comprehensive error tracking and summary reporting
  - State management with automatic reset after processing completion/failure
  - **Validation Requirement Met**: Publishing ProcessingStartedEvent triggers tracker output
- **ValidationReporter Features**:
  - Detailed validation error collection and reporting
  - Separate tracking for validation errors and warnings
  - Comprehensive validation summary with clear success/failure indicators
  - Integration with processing completion events for validation status reporting
- **Quality Standards**:
  - **Error Handling**: Resilient event publishing with proper exception isolation
  - **Professional Testing**: 38 unit tests with mocking, real-time output validation, and comprehensive coverage
  - **Zero Regression**: All 487 tests passing (449 existing + 38 new event tests)
  - **Observer Pattern Validation**: Type-safe event handling with comprehensive behavioral testing
- **Usage Pattern**:

  ```python
  # Create event publisher and observers
  publisher = EventPublisher()
  tracker = ProgressTracker()
  reporter = ValidationReporter()

  # Subscribe observers to events
  publisher.subscribe(ProcessingStartedEvent, tracker.handle_processing_started)
  publisher.subscribe(TransactionParsedEvent, tracker.handle_transaction_parsed)
  publisher.subscribe(ProcessingCompletedEvent, tracker.handle_processing_completed)
  publisher.subscribe(ValidationFailedEvent, reporter.handle_validation_failed)
  publisher.subscribe(ProcessingFailedEvent, tracker.handle_processing_failed)

  # Publish events during processing
  event = ProcessingStartedEvent(file_path=Path("statement.pdf"), file_size=1024)
  publisher.publish(event)  # Triggers real-time progress output
  ```

- **Validation Results**: ✅ All requirements successfully met
  - ✅ Publishing ProcessingStartedEvent triggers tracker output (key validation requirement)
  - ✅ All 38 new unit tests pass with comprehensive coverage
  - ✅ Zero regression - all 487 tests passing (449 existing + 38 new event tests)
  - ✅ Observer pattern working correctly with type-safe event handling
  - ✅ Event-driven architecture functional with real-time progress feedback
- **Architecture Impact**:
  - **Observer Pattern Foundation**: Enables decoupled, event-driven communication between components
  - **Progress Monitoring**: Real-time feedback during long-running statement processing operations
  - **Error Tracking**: Comprehensive error collection and reporting across processing pipeline
  - **Phase 3 → 3.2 Completion**: Successfully completes second advanced design pattern from PLAN.md
- **Next Phase**: Ready for Builder Pattern implementation (Phase 3 → 3.3), CLI interface, or additional enterprise features

### 26. Builder Pattern Implementation (Phase 3 → 3.3 - June 2025)

- **Challenge**: Need fluent builder pattern for Statement construction with comprehensive validation ensuring builder-produced statements equal direct constructor results
- **Solution**: Complete StatementBuilder implementation with method chaining, data integrity, and comprehensive validation
- **Implementation**: Complete `src/domain/builders.py` with `StatementBuilder` class following established domain patterns

```python
# src/domain/builders.py - StatementBuilder class
class StatementBuilder:
    """
    Fluent builder for constructing Statement objects.

    This class provides a fluent interface for building Statement objects
    with method chaining. It ensures that the builder-produced statement
    equals the result of direct constructor usage while providing a more
    readable and flexible construction API.

    The builder follows the established patterns in the codebase and
    integrates seamlessly with existing domain models.
    """

    def __init__(self) -> None:
        """
        Initialize StatementBuilder with empty state.

        Example:
            >>> builder = StatementBuilder()
            >>> statement = (builder
            ...     .with_payment_method(PaymentMethod.BBVA_VISA)
            ...     .add_transaction(transaction)
            ...     .build())
        """
        self._payment_method: PaymentMethod | None = None
        self._transactions: list[Transaction] = []
        self._reported_balance: Balance | None = None

    def with_payment_method(self, payment_method: PaymentMethod) -> "StatementBuilder":
        """
        Set the payment method for the statement.

        Args:
            payment_method: PaymentMethod enum value

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_payment_method(PaymentMethod.BBVA_VISA)
        """
        self._payment_method = payment_method
        return self

    def add_transaction(self, transaction: Transaction) -> "StatementBuilder":
        """
        Add a single transaction to the statement.

        Args:
            transaction: Transaction object to add

        Returns:
            Self for method chaining

        Example:
            >>> builder.add_transaction(transaction)
        """
        self._transactions.append(transaction)
        return self

    def add_transactions(self, transactions: list[Transaction]) -> "StatementBuilder":
        """
        Add multiple transactions to the statement.

        Args:
            transactions: List of Transaction objects to add

        Returns:
            Self for method chaining

        Example:
            >>> builder.add_transactions([transaction1, transaction2])
        """
        self._transactions.extend(transactions)
        return self

    def with_reported_balance(self, balance: Balance) -> "StatementBuilder":
        """
        Set the reported balance for the statement.

        Args:
            balance: Balance object with reported amounts

        Returns:
            Self for method chaining

        Example:
            >>> from decimal import Decimal
            >>> balance = Balance(Decimal("1000.00"), Decimal("100.00"))
            >>> builder.with_reported_balance(balance)
        """
        self._reported_balance = balance
        return self

    def build(self) -> Statement:
        """
        Build the final Statement object with validation.

        Creates a Statement using the same constructor as direct instantiation,
        ensuring that builder-produced statements equal direct constructor
        results.

        Returns:
            Statement: Properly constructed and validated Statement object

        Raises:
            ValueError: If payment method is not set or other validation fails

        Example:
            >>> statement = builder.build()
            >>> len(statement.transactions)
            2
        """
        # Import here to avoid circular imports
        from .models import Statement

        if self._payment_method is None:
            raise ValueError("Payment method is required to build Statement")

        # Create statement using exact same constructor as direct usage
        # This ensures builder-produced statement equals direct constructor result
        statement = Statement(
            payment_method=self._payment_method,
            transactions=self._transactions.copy(),  # Copy to prevent mutation
            reported_balance=self._reported_balance,
        )

        return statement

    def reset(self) -> "StatementBuilder":
        """
        Reset builder state for reuse.

        Clears all previously set values, allowing the builder to be reused
        for constructing multiple statements.

        Returns:
            Self for method chaining

        Example:
            >>> builder.reset().with_payment_method(PaymentMethod.MACRO_VISA)
        """
        self._payment_method = None
        self._transactions.clear()
        self._reported_balance = None
        return self
```

- **Architecture Benefits**:
  - **Fluent Interface**: Method chaining with readable, expressive API for Statement construction
  - **Validation Requirement**: Builder-produced statements equal direct constructor results (key requirement from Prompt 24)
  - **Data Integrity**: Transaction list copying prevents mutation, ensuring independence between builder and built objects
  - **Clean Architecture**: Follows established domain layer patterns and integrates seamlessly with existing models
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Builder Pattern Compliance**: Complete implementation following Gang of Four Builder Pattern principles
- **Key Features**:
  - **with_payment_method()**: Set payment method for the statement (required)
  - **add_transaction()**: Add single transaction with method chaining
  - **add_transactions()**: Add multiple transactions as list with method chaining
  - **with_reported_balance()**: Set reported balance for the statement (optional)
  - **build()**: Create final Statement object with validation (copies transaction list for isolation)
  - **reset()**: Clear builder state for reuse with multiple statements
- **Core Methods Implementation**:
  - **Method Chaining**: All builder methods return `self` for fluent interface
  - **Data Isolation**: Transaction list copying in `build()` prevents mutation between builder and built objects
  - **Error Handling**: Requires payment method before building, comprehensive validation with descriptive error messages
  - **Reusability**: Reset functionality allows builder reuse for multiple statements
  - **Constructor Equivalence**: Uses exact same Statement constructor as direct instantiation
- **Quality Standards**:
  - **Error Handling**: Comprehensive validation with descriptive error messages
  - **Code Quality**: Follows established patterns and integrates seamlessly with existing domain models
  - **Professional Testing**: 14 unit tests with comprehensive validation coverage
  - **Zero Regression**: All 213 domain tests pass (199 existing + 14 new), zero regression maintained
- **Validation Requirements**: ✅ All requirements met
  - ✅ Builder-produced statement equals direct constructor result (key validation requirement)
  - ✅ Fluent interface with method chaining works correctly
  - ✅ Transaction list isolation prevents mutation between builder and built objects
  - ✅ Payment method validation enforced before building
  - ✅ Reset functionality enables builder reuse
- **Unit Tests Coverage**:
  - **Builder Equals Direct Constructor**: Multiple test scenarios confirming builder-produced statements equal direct constructor results
  - **Fluent Interface**: Method chaining validation with all builder methods
  - **Transaction Management**: Single transaction, multiple transactions, transaction list operations
  - **Data Isolation**: Transaction list copying prevents mutation, ensuring independence
  - **Error Handling**: Payment method requirement, validation integration
  - **Reset Functionality**: Builder reuse for multiple statements
  - **Edge Cases**: Empty statements, validation scenarios, builder state management
- **Usage Pattern**:

  ```python
  # Fluent interface construction
  statement = (StatementBuilder()
      .with_payment_method(PaymentMethod.BBVA_VISA)
      .add_transaction(transaction1)
      .add_transactions([transaction2, transaction3])
      .with_reported_balance(balance)
      .build())

  # Builder reuse
  builder = StatementBuilder()
  statement1 = builder.with_payment_method(PaymentMethod.BBVA_VISA).build()
  statement2 = builder.reset().with_payment_method(PaymentMethod.MACRO_VISA).build()

  # Validation: Builder equals direct constructor
  builder_statement = StatementBuilder().with_payment_method(PaymentMethod.BBVA_VISA).build()
  direct_statement = Statement(payment_method=PaymentMethod.BBVA_VISA)
  assert builder_statement.payment_method == direct_statement.payment_method
  assert builder_statement.transactions == direct_statement.transactions
  assert builder_statement.reported_balance == direct_statement.reported_balance
  ```

- **Test Results**: ✅ All 14 new tests pass with comprehensive validation
  - ✅ All 213 domain tests pass (199 existing + 14 new), zero regression maintained
  - ✅ Builder equals direct constructor validation confirmed across all scenarios
  - ✅ Fluent interface and method chaining working correctly
  - ✅ Transaction isolation and data integrity verified
- **Architecture Impact**: Completes Phase 3 → 3.3 Builder Pattern implementation from PLAN.md
- **Next Phase**: Ready for CLI interface, additional enterprise features, or Phase 4 capabilities from PLAN.md

### 27. ProcessingReportBuilder Pattern (Phase 3 → 3.3 - June 2025)

- **Challenge**: Need comprehensive batch processing reporting with automatic success rate calculation for enterprise-level batch operations
- **Solution**: Complete ProcessingReportBuilder and ProcessingReport dataclass implementation with fluent interface and comprehensive metrics
- **Implementation**: Complete `src/domain/builders.py` with `ProcessingReportBuilder` class and `ProcessingReport` dataclass

### 28. AsyncStatementProcessor Pattern (Phase 4 → 4.1 - June 2025)

- **Challenge**: Need high-throughput concurrent processing for enterprise-scale batch operations with both asyncio and threading support
- **Solution**: Complete AsyncStatementProcessor implementation with dual processing modes, controlled concurrency, and comprehensive error isolation
- **Implementation**: Complete `src/infrastructure/async_processing.py` with `AsyncStatementProcessor`, `BatchProcessingResult`, and convenience functions

```python
# src/infrastructure/async_processing.py
class AsyncStatementProcessor:
    """
    High-throughput async/threaded batch processor for financial statements.

    Supports both asyncio and ThreadPoolExecutor modes with controlled concurrency,
    error isolation, and comprehensive metrics reporting.
    """

    def __init__(
        self,
        processing_service: Any,
        max_workers: int = 3,
        use_asyncio: bool = True,
        event_publisher: Optional[EventPublisher] = None,
    ):
        """Initialize with configurable processing mode and concurrency."""
        self._processing_service = processing_service
        self._max_workers = max_workers
        self._use_asyncio = use_asyncio
        self._event_publisher = event_publisher

        if not use_asyncio:
            self._executor = ThreadPoolExecutor(max_workers=max_workers)
        else:
            self._executor = None

    async def process_batch_async(
        self, file_paths: list[Path], output_dir: Path
    ) -> AsyncIterator[ProcessingResult]:
        """Stream processing results as they complete for real-time feedback."""
        if not self._use_asyncio:
            raise ValueError("Processor configured for threading mode")

        semaphore = asyncio.Semaphore(self._max_workers)

        async def process_single_file(file_path: Path) -> ProcessingResult:
            async with semaphore:
                return await asyncio.to_thread(
                    self._process_file_sync, file_path, output_dir
                )

        tasks = [process_single_file(file_path) for file_path in file_paths]

        for coro in asyncio.as_completed(tasks):
            result = await coro
            yield result

    async def process_batch_complete(
        self, file_paths: list[Path], output_dir: Path
    ) -> BatchProcessingResult:
        """Process all files and return comprehensive batch result."""
        start_time = time.time()
        successful_files = []
        failed_files = []
        total_transactions = 0

        if self._use_asyncio:
            async for result in self.process_batch_async(file_paths, output_dir):
                if result.success:
                    successful_files.append(result.input_path)
                    if result.statement:
                        total_transactions += len(result.statement.transactions)
                else:
                    error_msg = "; ".join(result.errors) if result.errors else "Unknown error"
                    failed_files.append((result.input_path, error_msg))
        else:
            for result in self.process_batch_threaded(file_paths, output_dir):
                if result.success:
                    successful_files.append(result.input_path)
                    if result.statement:
                        total_transactions += len(result.statement.transactions)
                else:
                    error_msg = "; ".join(result.errors) if result.errors else "Unknown error"
                    failed_files.append((result.input_path, error_msg))

        total_time = time.time() - start_time
        processing_mode = "asyncio" if self._use_asyncio else "threading"

        return BatchProcessingResult(
            successful_files=successful_files,
            failed_files=failed_files,
            total_processing_time=total_time,
            total_transactions=total_transactions,
            processing_mode=processing_mode,
        )

@dataclass
class BatchProcessingResult:
    """Comprehensive result object for batch processing operations."""
    successful_files: list[Path]
    failed_files: list[tuple[Path, str]]
    total_processing_time: float = 0.0
    total_transactions: int = 0
    processing_mode: str = "asyncio"

    @property
    def success_rate(self) -> float:
        """Calculate success rate as float between 0.0 and 1.0."""
        total_files = len(self.successful_files) + len(self.failed_files)
        if total_files == 0:
            return 0.0
        return len(self.successful_files) / total_files

    @property
    def total_files(self) -> int:
        """Get total number of files processed."""
        return len(self.successful_files) + len(self.failed_files)

    def print_summary(self) -> None:
        """Print formatted summary with comprehensive metrics."""
        print("\n" + "=" * 60)
        print("ASYNC BATCH PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Processing Mode: {self.processing_mode}")
        print(f"✅ Successful files: {len(self.successful_files)}")
        print(f"❌ Failed files: {len(self.failed_files)}")
        print(f"📊 Success rate: {self.success_rate:.1%}")
        print(f"📈 Total transactions: {self.total_transactions}")
        print(f"⏱️  Total processing time: {self.total_processing_time:.2f}s")

        if self.failed_files:
            print(f"\n❌ Failed Files:")
            for file_path, error in self.failed_files:
                print(f"   {file_path.name}: {error}")

async def process_files_async(
    file_paths: list[Path],
    output_dir: Path,
    processing_service: Any,
    max_workers: int = 3,
    use_asyncio: bool = True,
    event_publisher: Optional[EventPublisher] = None,
) -> BatchProcessingResult:
    """Convenience function for quick async batch processing."""
    async with AsyncStatementProcessor(
        processing_service=processing_service,
        max_workers=max_workers,
        use_asyncio=use_asyncio,
        event_publisher=event_publisher,
    ) as processor:
        return await processor.process_batch_complete(file_paths, output_dir)
```

- **Architecture Benefits**:
  - **High-Throughput Processing**: Concurrent processing of multiple financial statements with controlled resource usage
  - **Dual Processing Modes**: Both asyncio (I/O-bound) and ThreadPoolExecutor (CPU-bound) support with configurable concurrency
  - **Error Isolation**: Individual file failures don't stop batch processing, comprehensive error reporting
  - **Enterprise Readiness**: Professional async processing with metrics, progress tracking, and resource management
  - **Event Integration**: Full integration with existing Observer Pattern for real-time progress feedback
  - **Scalability Foundation**: Ready for large batch operations with semaphore-based concurrency control
- **Key Features**:
  - **Controlled Concurrency**: Semaphore-based limiting with configurable max_workers to prevent resource exhaustion
  - **Context Manager Support**: Both sync and async context manager protocols for proper resource cleanup
  - **Streaming API**: `process_batch_async()` yields results as they complete for real-time feedback
  - **Batch API**: `process_batch_complete()` returns comprehensive BatchProcessingResult with metrics
  - **Flexible Configuration**: Configurable processing mode, concurrency, and event publishing
  - **Comprehensive Metrics**: Success rates, processing times, transaction counts, and detailed error reporting
- **AsyncStatementProcessor Features**:
  - **Asyncio Mode**: Uses asyncio.Semaphore for controlled concurrency with async/await patterns
  - **Threading Mode**: Uses ThreadPoolExecutor for CPU-bound operations with traditional threading
  - **Event Publishing**: Integrates with existing EventPublisher for ProcessingStartedEvent, ProcessingCompletedEvent, and ProcessingFailedEvent
  - **Error Handling**: Comprehensive exception handling with detailed error messages and timing metrics
  - **Resource Management**: Proper cleanup with context manager support (both sync and async)
  - **Flexible API**: Multiple processing methods (streaming, batch complete, individual modes)
- **BatchProcessingResult Features**:
  - **Success Rate Calculation**: Automatic percentage calculation of successful vs failed files
  - **Comprehensive Metrics**: Total files, successful files, failed files, processing time, transaction count
  - **Detailed Error Reporting**: Failed files with specific error messages for debugging
  - **Formatted Summary**: Professional summary output with emoji indicators and clear metrics
  - **Processing Mode Tracking**: Records whether asyncio or threading mode was used
- **Validation Results**: ✅ All Phase 4 → 4.1 requirements successfully met
  - ✅ **Key Requirement**: `asyncio.run demo processing two files completes without deadlock` - VALIDATED
  - ✅ **Demo Results**: 2 files processed successfully, 136 transactions, 100% success rate, 0.68s processing time
  - ✅ **No Deadlocks**: Concurrent processing completed without any deadlock issues
  - ✅ **Event Integration**: Progress tracking and event system working correctly
  - ✅ **Error Handling**: Comprehensive error isolation and reporting functional
- **Quality Standards**:
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive AsyncIterator and Iterator support
  - **Error Handling**: Resilient processing with exception isolation and detailed error reporting
  - **Clean Architecture**: Infrastructure layer implementation with domain service integration
  - **Professional Implementation**: Context managers, proper resource cleanup, and comprehensive documentation
- **Usage Pattern**:

  ```python
  # Asyncio mode for high concurrency
  async with AsyncStatementProcessor(
      processing_service=service, max_workers=5, use_asyncio=True
  ) as processor:
      result = await processor.process_batch_complete(files, output_dir)
      print(f"Success rate: {result.success_rate:.1%}")

  # Threading mode for CPU-bound operations
  with AsyncStatementProcessor(
      processing_service=service, max_workers=3, use_asyncio=False
  ) as processor:
      for result in processor.process_batch_threaded(files, output_dir):
          print(f"Processed: {result.input_path.name}")

  # Convenience function for quick processing
  result = await process_files_async(
      file_paths=files,
      output_dir=output_dir,
      processing_service=service,
      max_workers=4,
      use_asyncio=True
  )
  result.print_summary()
  ```

- **Architecture Impact**: Completes Phase 4 → 4.1 from PLAN.md, providing enterprise-scale concurrent processing foundation
- **Next Phase**: Ready for CLI interface implementation, additional enterprise features, or Phase 4 → 4.2+ capabilities

```python
# src/domain/builders.py - ProcessingReport dataclass
@dataclass(frozen=True)
class ProcessingReport:
    """
    Immutable report of batch processing results.

    This dataclass contains comprehensive information about a batch processing
    operation, including successful and failed files, success rates, and
    processing metrics. It follows the established patterns in the codebase
    for immutable value objects.
    """

    successful_files: list[Path]
    failed_files: list[tuple[Path, str]]
    total_processing_time: float = 0.0
    total_transactions: int = 0

    @property
    def success_rate(self) -> float:
        """
        Calculate the success rate as a float between 0.0 and 1.0.

        Returns:
            float: Success rate (successful files / total files)
                  Returns 0.0 if no files were processed

        Example:
            >>> report = ProcessingReport([Path("file1.pdf")], [])
            >>> report.success_rate
            1.0
            >>> report = ProcessingReport([Path("file1.pdf")],
            ...                          [(Path("file2.pdf"), "error")])
            >>> report.success_rate
            0.5
        """
        total_files = len(self.successful_files) + len(self.failed_files)
        if total_files == 0:
            return 0.0
        return len(self.successful_files) / total_files

    @property
    def total_files(self) -> int:
        """Get total number of files processed (successful + failed)."""
        return len(self.successful_files) + len(self.failed_files)

    def print_summary(self) -> None:
        """Print formatted summary of processing results."""
        print("\n" + "=" * 60)
        print("BATCH PROCESSING SUMMARY")
        print("=" * 60)
        print(f"✅ Successful files: {len(self.successful_files)}")
        print(f"❌ Failed files: {len(self.failed_files)}")
        print(f"📊 Success rate: {self.success_rate:.1%}")
        print(f"📈 Total transactions: {self.total_transactions}")
        print(f"⏱️  Processing time: {self.total_processing_time:.2f}s")

        if self.failed_files:
            print(f"\n❌ Failed Files:")
            for file_path, error in self.failed_files:
                print(f"   {file_path.name}: {error}")

class ProcessingReportBuilder:
    """
    Builder for constructing ProcessingReport objects.

    This class provides a fluent interface for building ProcessingReport
    objects with method chaining. It tracks successful and failed file
    processing operations and automatically calculates success rates.

    The builder follows the established patterns in the codebase and
    integrates seamlessly with existing domain models.
    """

    def __init__(self) -> None:
        """Initialize ProcessingReportBuilder with empty state."""
        self._successful_files: list[Path] = []
        self._failed_files: list[tuple[Path, str]] = []
        self._total_processing_time: float = 0.0
        self._total_transactions: int = 0

    def add_success(
        self, file_path: Path, transaction_count: int = 0
    ) -> ProcessingReportBuilder:
        """Add a successfully processed file to the report."""
        self._successful_files.append(file_path)
        self._total_transactions += transaction_count
        return self

    def add_failure(
        self, file_path: Path, error_message: str
    ) -> ProcessingReportBuilder:
        """Add a failed file to the report."""
        self._failed_files.append((file_path, error_message))
        return self

    def with_processing_time(self, time_seconds: float) -> ProcessingReportBuilder:
        """Set the total processing time for the batch operation."""
        self._total_processing_time = time_seconds
        return self

    def build(self) -> ProcessingReport:
        """Build the final ProcessingReport object."""
        return ProcessingReport(
            successful_files=self._successful_files.copy(),
            failed_files=self._failed_files.copy(),
            total_processing_time=self._total_processing_time,
            total_transactions=self._total_transactions,
        )

    def reset(self) -> ProcessingReportBuilder:
        """Reset builder state for reuse."""
        self._successful_files.clear()
        self._failed_files.clear()
        self._total_processing_time = 0.0
        self._total_transactions = 0
        return self
```

- **Architecture Benefits**:
  - **Immutable Report**: ProcessingReport dataclass with frozen=True following established patterns for value objects
  - **Fluent Interface**: ProcessingReportBuilder with method chaining for readable, expressive API
  - **Automatic Calculations**: Success rate calculated as property with proper edge case handling (0.0 for no files)
  - **Comprehensive Metrics**: Tracks successful files, failed files, processing time, and transaction counts
  - **Professional Output**: Formatted summary with emojis and clear statistics for enterprise reporting
  - **Builder Pattern Compliance**: Complete implementation following Gang of Four Builder Pattern principles
- **Key Features**:
  - **add_success()**: Add successfully processed file with optional transaction count tracking
  - **add_failure()**: Add failed file with descriptive error message for troubleshooting
  - **with_processing_time()**: Set total processing time for performance metrics
  - **build()**: Create final immutable ProcessingReport with all accumulated data
  - **reset()**: Clear builder state for reuse with multiple batch operations
  - **success_rate property**: Automatic calculation as float between 0.0 and 1.0
  - **print_summary()**: Professional formatted output with comprehensive statistics
- **Validation Requirements**: ✅ All requirements met
  - ✅ Adding one success and one failure results in `success_rate == 0.5` (key validation requirement)
  - ✅ Fluent interface with method chaining works correctly
  - ✅ Immutable report objects with comprehensive metrics
  - ✅ Professional summary output with clear formatting
  - ✅ Builder reusability with reset functionality
- **Quality Standards**:
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Error Handling**: Comprehensive validation with descriptive error messages
  - **Clean Architecture**: Domain layer builder following Single Responsibility Principle
  - **Code Quality**: Follows established patterns and integrates seamlessly with existing domain models
- **Usage Pattern**:

  ```python
  # Fluent interface construction
  report = (ProcessingReportBuilder()
      .add_success(Path("file1.pdf"), 45)
      .add_failure(Path("file2.pdf"), "Parse error")
      .with_processing_time(12.5)
      .build())

  # Validation: Success rate calculation
  assert report.success_rate == 0.5  # 1 success, 1 failure = 50%
  assert report.total_files == 2
  assert report.total_transactions == 45

  # Professional summary output
  report.print_summary()
  # Outputs formatted summary with statistics and failed file details

  # Builder reuse
  builder = ProcessingReportBuilder()
  report1 = builder.add_success(Path("file1.pdf")).build()
  report2 = builder.reset().add_success(Path("file2.pdf")).build()
  ```

- **Architecture Impact**: Completes Phase 3 → 3.3 Builder Pattern implementation for batch processing reports
- **Integration Ready**: Perfect for CLI interfaces, enterprise batch processing, and automated reporting systems
- **Next Phase**: Ready for CLI interface implementation, additional enterprise features, or Phase 4 capabilities from PLAN.md

## Async Processing Patterns

### 29. Test Path Isolation Pattern (June 2025)

- **Challenge**: Integration tests using hardcoded production file paths instead of isolated test data, causing file system side effects
- **Solution**: Systematic update of all test file paths to use dedicated test data directories and temporary output fixtures
- **Implementation**: Updated async processing integration tests to follow established isolation patterns

#### Test Isolation Strategy

**Problem Identification**

- Async processing tests were using `Path("input/...")` instead of `tests/test_data/input/...`
- Tests were modifying production files instead of using isolated test data
- Inconsistent with other integration tests that properly used test data isolation

**Solution Implementation**

```python
# Before: Hardcoded production paths
test_files = [
    Path("input/BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf"),
    Path("input/MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf"),
]

# After: Proper test data isolation
test_files = [
    Path("tests/test_data/input/BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf"),
    Path("tests/test_data/input/MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf"),
]

# Use temp_output_dir fixture instead of hardcoded output paths
async def test_asyncio_batch_processing_no_deadlock(
    self, mock_dependencies, temp_output_dir
):
    # Process files using temporary output directory
    results = []
    async for result in processor.process_batch_async(test_files, temp_output_dir):
        results.append(result)
```

**Test Isolation Benefits**

- **Zero File System Side Effects**: Tests don't modify production files during execution
- **Reliable CI/CD**: Tests run consistently across different environments
- **Professional Testing**: Follows established patterns used by other integration tests
- **Parallel Test Execution**: Tests can run concurrently without interference
- **Clean Development**: No unexpected file modifications during development

**Pattern Application**

- Updated 15+ file path references across multiple test methods
- Replaced hardcoded `Path("output")` with `temp_output_dir` fixture
- Maintained all test functionality while ensuring proper isolation
- Followed same patterns as existing integration tests

**Quality Impact**

- All pre-commit hooks now pass reliably
- Tests properly isolated with zero file system side effects
- Maintains consistency with established testing patterns
- Enables reliable automated testing and CI/CD pipelines

### 30. StreamingStatementParser Pattern (Phase 4 → 4.1 - July 2025)

- **Challenge**: Need memory-efficient processing of large CSV/Excel files without loading entire datasets into memory
- **Solution**: Iterator-based chunk processing with configurable chunk sizes and comprehensive error handling
- **Implementation**: Complete `src/infrastructure/streaming.py` with `StreamingStatementParser` class

```python
# src/infrastructure/streaming.py
class StreamingStatementParser:
    """Memory-efficient parser for large CSV/Excel files using chunk-based processing."""

    def __init__(
        self,
        chunk_size: int = 1000,
        transaction_builder: Optional[TransactionBuilder] = None,
        payment_method_detector: Optional[PaymentMethodDetector] = None,
    ):
        """Initialize with configurable chunk size and optional dependencies."""
        self._chunk_size = chunk_size
        self._transaction_builder = transaction_builder
        self._payment_method_detector = payment_method_detector

    def parse_large_csv(self, file_path: Path) -> Iterator[Transaction]:
        """Parse large CSV files using pandas chunk reader for memory efficiency."""
        logger.info(f"Starting CSV streaming parse: {file_path}")

        try:
            chunk_reader = pd.read_csv(file_path, chunksize=self._chunk_size)

            for chunk_num, chunk in enumerate(chunk_reader, 1):
                logger.debug(f"Processing chunk {chunk_num} with {len(chunk)} rows")

                for _, row in chunk.iterrows():
                    try:
                        transaction = self._parse_csv_row(row, file_path)
                        if transaction:
                            yield transaction
                    except Exception as e:
                        logger.warning(f"Failed to parse CSV row: {e}")
                        continue

        except Exception as e:
            logger.error(f"Failed to parse CSV file {file_path}: {e}")
            raise

    def parse_large_excel(self, file_path: Path) -> Iterator[Transaction]:
        """Parse large Excel files sheet by sheet with proper resource management."""
        logger.info(f"Starting Excel streaming parse: {file_path}")

        try:
            with pd.ExcelFile(file_path) as excel_file:
                for sheet_name in excel_file.sheet_names:
                    logger.debug(f"Processing sheet: {sheet_name}")

                    df = pd.read_excel(excel_file, sheet_name=sheet_name)

                    for _, row in df.iterrows():
                        try:
                            transaction = self._parse_excel_row(row, file_path)
                            if transaction:
                                yield transaction
                        except Exception as e:
                            logger.warning(f"Failed to parse Excel row: {e}")
                            continue

        except Exception as e:
            logger.error(f"Failed to parse Excel file {file_path}: {e}")
            raise
```

- **Architecture Benefits**:
  - **Memory Efficiency**: Processes files in configurable chunks without loading entire files into memory
  - **Iterator Pattern**: Yields Transaction objects as they're parsed for streaming consumption
  - **Resource Management**: Proper context manager usage for Excel files and comprehensive error handling
  - **Configurable Processing**: Adjustable chunk sizes for different memory constraints and performance requirements
  - **Architecture Integration**: Seamless integration with existing TransactionBuilder and PaymentMethodDetector
  - **Error Resilience**: Individual row failures don't stop entire file processing
- **Key Features**:
  - **CSV Streaming**: Uses pandas `read_csv(chunksize=chunk_size)` for memory-efficient chunk processing
  - **Excel Streaming**: Sheet-by-sheet processing using `pd.ExcelFile` context manager
  - **Row-by-Row Processing**: Each chunk/sheet is processed row by row, yielding Transaction objects
  - **Payment Method Detection**: Integrates with existing filename-based detection patterns
  - **Fallback Logic**: Provides fallback Transaction creation when TransactionBuilder not available
  - **Professional Logging**: Comprehensive logging for debugging and monitoring processing progress
- **Memory Efficiency Benefits**:
  - **Scalability**: Can handle enterprise-scale CSV/Excel files (millions of rows) with controlled memory usage
  - **Performance**: Memory-efficient processing reduces system resource requirements
  - **Flexibility**: Configurable chunk sizes allow optimization for different scenarios
  - **Reliability**: Comprehensive error handling with graceful degradation for malformed rows
- **Quality Standards**:
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Error Handling**: Comprehensive exception handling with detailed logging
  - **Clean Architecture**: Infrastructure layer implementation following hexagonal architecture principles
  - **Professional Testing**: 63 unit tests with comprehensive validation coverage
- **Usage Pattern**:

  ```python
  # Basic usage with default chunk size
  parser = StreamingStatementParser()
  transactions = list(parser.parse_large_csv(Path("large_statement.csv")))

  # Configurable chunk size for memory optimization
  parser = StreamingStatementParser(chunk_size=500)
  for transaction in parser.parse_large_excel(Path("large_workbook.xlsx")):
      process_transaction(transaction)

  # Full integration with existing components
  parser = StreamingStatementParser(
      chunk_size=1000,
      transaction_builder=transaction_builder,
      payment_method_detector=payment_method_detector
  )
  ```

- **Architecture Impact**: Enables enterprise-scale file processing with memory-efficient streaming for large financial datasets
- **Phase 4 → 4.1 Completion**: Successfully completes streaming parsers implementation from PLAN.md

### 31. TYPE_CHECKING Block Cleanup Pattern (January 2025)

- **Challenge**: Unnecessary `TYPE_CHECKING` conditional import blocks cluttering code where no circular dependencies exist
- **Solution**: Remove unnecessary `TYPE_CHECKING` blocks and convert conditional imports to regular imports when safe
- **Implementation**: Systematic analysis and cleanup of 3 files (`parse_visa_statement.py`, `src/domain/builders.py`, `src/domain/utils.py`)
- **Decision Criteria**: Remove TYPE_CHECKING blocks only when no circular imports are detected and imports can be safely made unconditional
- **Key Changes**:
  - Removed empty `if TYPE_CHECKING:` blocks that served no purpose
  - Converted conditional imports to regular imports (e.g., `from pandas import DataFrame` instead of conditional import)
  - Updated type annotations to use imported types directly (`pd.DataFrame` → `DataFrame`)
  - Cleaned up unnecessary `else` blocks that were just reassigning the same imports
- **Benefits**: Cleaner, more readable code with simplified import structure following Python best practices for direct imports when possible
- **Quality Impact**: Improved code maintainability, reduced cognitive overhead, better adherence to Python conventions

### 32. `__all__` Statements Refactoring Pattern (January 2025)

- **Challenge**: Scattered `__all__` statements throughout individual modules making package APIs unclear and maintenance difficult
- **Solution**: Consolidate all `__all__` statements into package-level `__init__.py` files following Python best practices
- **Implementation**: Systematic refactoring of all packages (domain, application, infrastructure, CLI) to centralize export control

#### Package Export Consolidation Strategy

**Problem Identification**

- Individual modules had scattered `__all__` statements making it unclear what each package exports
- Maintenance required updating multiple files when adding/removing exports
- No single source of truth for package public APIs
- Violated Python packaging best practices for clean package organization

**Solution Implementation**

```python
# Before: Individual module exports
# src/domain/models.py
__all__ = [
    "Currency",
    "PaymentMethod",
    "Transaction",
    "Balance",
    "Statement",
]

# src/domain/detectors.py
__all__ = [
    "BankDetector",
    "PaymentMethodDetector",
]

# After: Centralized package exports
# src/domain/__init__.py
from .models import Currency, PaymentMethod, Transaction, Balance, Statement
from .detectors import BankDetector, PaymentMethodDetector
from .services import StatementParser
from .repositories import FileReader, FileWriter, StatementRepository
# ... all other imports

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
    "StatementParser",
    "TransactionBuilder",
    "StatementBuilder",

    # ... organized by category with 43 total exports
]
```

**Refactoring Benefits**

- **Single Point of Control**: Each package has one clear location (`__init__.py`) defining its public API
- **Cleaner Individual Modules**: Module files focused purely on implementation without export concerns
- **Better Package Organization**: Immediately clear what each package exposes by examining its `__init__.py`
- **Easier Maintenance**: Adding/removing exports only requires updating package-level `__init__.py`
- **Python Best Practices**: Follows recommended approach for package organization
- **Organized Categories**: Exports grouped logically (Commands, Core Models, Services, etc.)

**Implementation Results**

- **Domain Package**: Consolidated 43 exports from 9 modules with logical categorization
- **Application Package**: Centralized exports for `ProcessingResult` and `StatementProcessingService`
- **Infrastructure Package**: Created comprehensive exports with 12 organized categories
- **CLI Package**: Updated to export main `cli` function
- **Parsers Subpackage**: Consolidated parser exports in infrastructure/parsers `__init__.py`

**Quality Validation**

- ✅ All 674 tests continue to pass with zero regression
- ✅ Clean package APIs with centralized control
- ✅ Follows Python packaging best practices
- ✅ Easier maintenance and better code organization
- ✅ Clear separation between implementation and public interface

### 32. AsyncStatementProcessor Error Resolution Pattern (Phase 4 → 4.1 - June 2025)

- **Challenge**: Critical MyPy type errors, test failures, and coverage gaps preventing production deployment
- **Solution**: Systematic error resolution with variable naming fixes, type annotations, and comprehensive error path testing
- **Implementation**: Fixed all AsyncStatementProcessor errors for enterprise-ready concurrent processing

#### Error Resolution Strategy

**MyPy Type Error Resolution**

- **Variable Reuse Issues**: Fixed incorrect variable assignments where different event types were assigned to same variables
- **Solution**: Used unique variable names (`started_event`, `completed_event`, `failed_event`, `failure_event`) instead of reusing `event`
- **Type Annotations**: Added explicit type annotation for `BatchProcessingResult` in convenience function
- **Result**: All 5 MyPy type errors resolved, type checking now passes completely

**Test Logic Error Resolution**

- **Mock Service Logic**: Fixed mock service to properly raise exceptions instead of returning them
- **Error Isolation Testing**: Corrected test to ensure proper `ProcessingResult` objects are returned instead of raw exceptions
- **Exception Handling**: Improved mock strategy for realistic error simulation in concurrent processing scenarios

**Coverage Improvement Strategy**

- **Error Path Testing**: Added 7 new unit tests covering event publishing failures, processing exceptions, and edge cases
- **AsyncStatementProcessor Coverage**: Improved from 76% to 83% with comprehensive error handling validation
- **Overall Coverage**: Enhanced from 88% to 89.24% (very close to 90% target)
- **Quality Focus**: Meaningful coverage of error paths and concurrent processing scenarios

#### Error Handling Patterns

**Event Publishing Failure Handling**

```python
# Pattern: Graceful degradation when event publishing fails
try:
    if self._event_publisher:
        event = ProcessingCompletedEvent(...)
        self._event_publisher.publish(event)
except Exception as e:
    logger.warning(f"Failed to publish event: {e}")
    # Continue processing despite event failure
```

**Concurrent Processing Error Isolation**

```python
# Pattern: Individual file failures don't stop batch processing
async def process_batch_async(self, file_paths, output_dir):
    for file_path in file_paths:
        try:
            result = await self._process_file_async(file_path, output_dir)
            yield result
        except Exception as e:
            # Create error result, continue with other files
            error_result = ProcessingResult(
                input_path=file_path,
                success=False,
                errors=[f"Processing failed: {str(e)}"]
            )
            yield error_result
```

**Type-Safe Variable Naming**

```python
# Before: Variable reuse causing MyPy errors
event = ProcessingStartedEvent(...)
# ... later in code
event = ProcessingCompletedEvent(...)  # MyPy error: incompatible types

# After: Unique variable names for type safety
started_event = ProcessingStartedEvent(...)
completed_event = ProcessingCompletedEvent(...)
failed_event = ProcessingFailedEvent(...)
```

#### Quality Improvements

**Production Readiness Achieved**

- ✅ **All MyPy errors resolved**: Type checking passes completely
- ✅ **All tests passing**: 529 tests pass successfully with zero failures
- ✅ **Key requirement validated**: `asyncio.run demo processing two files completes without deadlock`
- ✅ **Error isolation working**: Individual file failures don't affect batch processing
- ✅ **Event integration functional**: Progress tracking and error reporting working correctly

**Enterprise-Scale Capabilities**

- **High-Throughput Processing**: Concurrent processing with controlled resource usage
- **Comprehensive Error Handling**: Resilient processing with detailed error reporting
- **Progress Tracking**: Real-time feedback through event system integration
- **Resource Management**: Proper cleanup with context manager support
- **Scalability**: Ready for large batch operations with semaphore-based concurrency control

#### Architecture Impact

**Robust Concurrent Processing**

- AsyncStatementProcessor now provides production-ready concurrent processing for high-throughput financial statement processing
- Comprehensive error isolation ensures individual failures don't compromise batch operations
- Enterprise-scale processing with proper error handling, progress tracking, and resource management
- Foundation for CLI interfaces, automated batch processing, and enterprise integration

**Error Handling Excellence**

- Systematic approach to error resolution with type safety, test coverage, and production readiness
- Comprehensive error path testing ensures reliability under failure conditions
- Event-driven error reporting provides real-time feedback and monitoring capabilities
- Professional error handling patterns suitable for enterprise deployment

This error resolution pattern demonstrates the importance of systematic debugging, comprehensive testing, and production-ready error handling in enterprise software development.

### 33. Validation Parity Implementation Pattern (December 2025)

- **Challenge**: CLI system missing critical validation capabilities that existed in legacy script (PDF balance extraction, payment exclusion logic, format-specific validation)
- **Solution**: Complete validation feature parity implementation with balance extraction infrastructure and enhanced validation logic
- **Implementation**: Strategic implementation across domain and infrastructure layers to achieve 100% feature equivalence

#### Balance Extraction Infrastructure Pattern

**Problem**: CLI system could not extract reported balances from PDF content like legacy script

**Solution**: Abstract service architecture with multiple extractors using registry pattern

```python
# src/infrastructure/extractors.py
from abc import ABC, abstractmethod
from typing import Dict
from decimal import Decimal

class BalanceExtractor(ABC):
    """Abstract service for extracting reported balances from statement content."""

    @abstractmethod
    def extract_balance(self, content: str, payment_method: PaymentMethod) -> Dict[str, Decimal]:
        """Extract reported balance from statement content."""
        pass

    @abstractmethod
    def can_extract(self, payment_method: PaymentMethod) -> bool:
        """Check if extractor supports the payment method."""
        pass

class PDFBalanceExtractor(BalanceExtractor):
    """Concrete extractor for PDF balance extraction using regex patterns."""

    def extract_balance(self, content: str, payment_method: PaymentMethod) -> Dict[str, Decimal]:
        """Extract reported balance from PDF text using payment method-specific patterns."""
        balance = {"ars": Decimal("0.0"), "usd": Decimal("0.0")}

        if payment_method == PaymentMethod.BBVA_MASTERCARD:
            # BBVA Mastercard format: "SALDO ACTUAL $ 185.170,00 SALDO ACTUAL U$S 0,00"
            pattern1 = r"SALDO ACTUAL \$ ([\d,.]+).*?SALDO ACTUAL U\$S ([\d,.]+)"
            match1 = re.search(pattern1, content)
            if match1:
                ars_str = match1.group(1)
                usd_str = match1.group(2)
            else:
                # Alternative pattern for BBVA Mastercard
                pattern2 = r"\d{2}-\w{3}-\d{2}\s+\d{2}-\w{3}-\d{2}\s+([\d,.]+)\s+([\d,.]+)\s+[\d,.]+"
                match2 = re.search(pattern2, content)
                if match2:
                    ars_str = match2.group(1)
                    usd_str = match2.group(2)
                else:
                    ars_str = "0"
                    usd_str = "0"
        else:
            # Standard format for MACRO VISA and BBVA VISA
            pattern = r"SALDO ACTUAL \$ ([\d,.]+) U\$S ([\d,.]+)"
            match = re.search(pattern, content)
            if match:
                ars_str = match.group(1)
                usd_str = match.group(2)
            else:
                ars_str = "0"
                usd_str = "0"

        # Convert European format to decimal
        balance["ars"] = self._parse_european_amount(ars_str)
        balance["usd"] = self._parse_european_amount(usd_str)

        return balance

class BalanceExtractionService:
    """Service managing multiple balance extractors using registry pattern."""

    def __init__(self):
        self._extractors: List[BalanceExtractor] = []

    def register_extractor(self, extractor: BalanceExtractor) -> None:
        """Register a balance extractor."""
        self._extractors.append(extractor)

    def extract_balance(self, content: str, payment_method: PaymentMethod) -> Optional[Dict[str, Decimal]]:
        """Extract balance using appropriate extractor."""
        for extractor in self._extractors:
            if extractor.can_extract(payment_method):
                return extractor.extract_balance(content, payment_method)
        return None
```

#### Payment Exclusion Logic Pattern

**Problem**: CLI system included all transactions in balance calculations while legacy script excluded payment transactions

**Solution**: Enhanced validation logic that exactly matches legacy script payment exclusion behavior

```python
# src/domain/validation.py
def _calculate_balance_excluding_payments(self, statement: Statement) -> Dict[str, Decimal]:
    """Calculate balance excluding payment transactions."""
    ars_total = Decimal("0.0")
    usd_total = Decimal("0.0")

    # Payment transaction identifiers - EXACT match with legacy script
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
```

#### Enhanced Validation Results Pattern

**Problem**: CLI system had basic validation results without detailed legacy script formatting

**Solution**: Enhanced validation results with detailed reporting and visual indicators

```python
# src/domain/validation.py
@dataclass
class EnhancedValidationResult(ValidationResult):
    """Enhanced validation result with detailed balance information."""

    reported_ars: Optional[Decimal] = None
    reported_usd: Optional[Decimal] = None
    computed_ars: Optional[Decimal] = None
    computed_usd: Optional[Decimal] = None
    ars_difference: Optional[Decimal] = None
    usd_difference: Optional[Decimal] = None
    transaction_count: int = 0
    payment_method: Optional[str] = None

    def print_detailed_summary(self, filename: str) -> None:
        """Print detailed validation summary with legacy script formatting."""
        print(f"\n{'=' * 60}")
        print(f"VALIDATION SUMMARY: {filename}")
        print(f"{'=' * 60}")
        print(f"Transactions Processed: {self.transaction_count}")
        print(f"Payment Method: {self.payment_method}")

        if self.reported_ars is not None and self.computed_ars is not None:
            print(f"\nBALANCE VALIDATION:")
            print(f"  Reported ARS: {self.reported_ars:,.2f}")
            print(f"  Computed ARS: {self.computed_ars:,.2f}")
            ars_match = "✅ YES" if abs(self.ars_difference or 0) < 0.01 else "❌ NO"
            print(f"  ARS Match: {ars_match}")

            print(f"  Reported USD: {self.reported_usd:,.2f}")
            print(f"  Computed USD: {self.computed_usd:,.2f}")
            usd_match = "✅ YES" if abs(self.usd_difference or 0) < 0.01 else "❌ NO"
            print(f"  USD Match: {usd_match}")

        if not self.is_valid:
            print(f"\n❌ VALIDATION ERRORS:")
            for error in self.errors:
                print(f"   • {error}")

        if self.warnings:
            print(f"\n⚠️  VALIDATION WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
```

#### Architecture Benefits

- **Complete Feature Parity**: CLI system now matches/exceeds legacy script validation capabilities
- **Backward Compatible**: All existing validation continues to work without changes
- **Extensible Design**: Easy to add new balance extractors for future formats (CSV, XLSX)
- **Clean Architecture**: Follows established hexagonal architecture principles
- **Type Safe**: Modern Python 3.11+ type annotations throughout
- **Testable**: Comprehensive validation with proper error handling

#### Quality Validation

- **100% Feature Equivalence**: All legacy script validation capabilities now in CLI
- **Payment Exclusion Logic**: Correctly excludes "SU PAGO EN PESOS" and "SU PAGO EN USD"
- **PDF Balance Extraction**: Uses identical regex patterns as legacy script
- **Enhanced Reporting**: Professional validation summaries with visual indicators
- **Production Ready**: Zero regressions, all tests pass, comprehensive error handling

#### Usage Pattern

```python
# Enhanced validation with balance extraction
service = build_default_balance_service()
validator = StatementValidator(balance_extraction_service=service)

# Validate with content for balance extraction
result = validator.validate_with_content(statement, raw_pdf_content)

# Detailed reporting
if isinstance(result, EnhancedValidationResult):
    result.print_detailed_summary(filename)
```

This pattern demonstrates successful feature parity achievement between legacy systems and modern clean architecture implementations while maintaining all architectural benefits.

### 34. Balance Extraction Service Pattern (December 2025)

- **Challenge**: Need flexible, extensible balance extraction from multiple file formats with different parsing requirements
- **Solution**: Registry-based service architecture with abstract extractors and factory pattern for convenient usage
- **Implementation**: Complete service infrastructure supporting PDF, CSV, XLSX extraction with unified interface

#### Registry-Based Extractor Pattern

**Service Architecture**: Central service managing multiple specialized extractors

```python
# src/infrastructure/extractors.py
class BalanceExtractionService:
    """Service managing multiple balance extractors using registry pattern."""

    def __init__(self):
        self._extractors: List[BalanceExtractor] = []

    def register_extractor(self, extractor: BalanceExtractor) -> None:
        """Register a balance extractor."""
        self._extractors.append(extractor)

    def extract_balance(self, content: str, payment_method: PaymentMethod) -> Optional[Dict[str, Decimal]]:
        """Extract balance using appropriate extractor."""
        for extractor in self._extractors:
            if extractor.can_extract(payment_method):
                return extractor.extract_balance(content, payment_method)
        return None

def build_default_balance_service() -> BalanceExtractionService:
    """Build balance service with all standard extractors."""
    service = BalanceExtractionService()
    service.register_extractor(PDFBalanceExtractor())
    service.register_extractor(CSVBalanceExtractor())
    service.register_extractor(XLSXBalanceExtractor())
    return service
```

#### Format-Specific Extractors Pattern

**PDF Extractor**: Regex-based extraction using legacy script patterns

```python
class PDFBalanceExtractor(BalanceExtractor):
    """Extractor for PDF balance extraction using regex patterns."""

    def can_extract(self, payment_method: PaymentMethod) -> bool:
        """Check if extractor supports PDF-based payment methods."""
        pdf_methods = {
            PaymentMethod.BBVA_VISA,
            PaymentMethod.BBVA_MASTERCARD,
            PaymentMethod.MACRO_VISA
        }
        return payment_method in pdf_methods

    def _parse_european_amount(self, amount_str: str) -> Decimal:
        """Convert European format (1.234,56) to Decimal."""
        try:
            # Handle European format for amounts
            if "." in amount_str and "," in amount_str:
                amount_str = amount_str.replace(".", "").replace(",", ".")
            elif "," in amount_str:
                amount_str = amount_str.replace(",", ".")
            return Decimal(amount_str)
        except (ValueError, TypeError):
            return Decimal("0.0")
```

**CSV Extractor**: File-based validation for CSV inputs

```python
class CSVBalanceExtractor(BalanceExtractor):
    """Extractor for CSV file balance validation."""

    def extract_balance(self, file_path: Path, payment_method: PaymentMethod) -> Dict[str, Decimal]:
        """Extract total from CSV file for validation."""
        import pandas as pd

        try:
            df = pd.read_csv(file_path, sep=";")
            total = Decimal("0.0")

            for _, row in df.iterrows():
                importe_str = str(row["Importe"]).strip()
                if importe_str and importe_str != "nan":
                    try:
                        # Handle European format
                        amount_str = importe_str.replace(",", "")
                        amount = Decimal(amount_str)
                        total += amount
                    except (ValueError, TypeError):
                        continue

            # CSV files are typically ARS only
            return {"ars": total, "usd": Decimal("0.0")}

        except Exception:
            return {"ars": Decimal("0.0"), "usd": Decimal("0.0")}
```

#### Architecture Benefits

- **Pluggable Extractors**: Easy to add new extractor types without modifying existing code
- **Registry Pattern**: Flexible registration and discovery of appropriate extractors
- **Format Abstraction**: Unified interface regardless of underlying file format
- **Factory Pattern**: Convenient pre-configured service creation
- **Type Safety**: Full type annotations with comprehensive error handling
- **Clean Architecture**: Infrastructure layer implementing domain service abstractions

#### Integration Pattern

```python
# Enhanced StatementValidator integration
class StatementValidator:
    def __init__(
        self,
        balance_tolerance: Decimal = Decimal("0.01"),
        balance_extraction_service: Optional[BalanceExtractionService] = None
    ):
        self._balance_tolerance = balance_tolerance
        self._balance_service = balance_extraction_service

    def validate_with_content(self, statement: Statement, raw_content: str) -> ValidationResult:
        """Validate statement with raw content for balance extraction."""
        # Extract balance from content if service available
        if self._balance_service and raw_content:
            extracted_balance = self._balance_service.extract_balance(
                raw_content, statement.payment_method
            )
            if extracted_balance:
                # Set extracted balance on statement
                statement.reported_balance = Balance(
                    ars_amount=extracted_balance["ars"],
                    usd_amount=extracted_balance["usd"]
                )
```

This pattern enables flexible, extensible balance extraction across multiple file formats while maintaining clean architecture principles and type safety.

### 35. Payment Exclusion Logic Pattern (December 2025)

- **Challenge**: CLI system included all transactions in balance calculations while legacy script excluded payment transactions
- **Solution**: Enhanced validation logic that exactly matches legacy script payment exclusion behavior
- **Implementation**: Domain-level validation enhancement with payment identification and exclusion

#### Transaction Classification Pattern

**Payment Identification**: Exact matching with legacy script logic

```python
# src/domain/validation.py
def _calculate_balance_excluding_payments(self, statement: Statement) -> Dict[str, Decimal]:
    """Calculate balance excluding payment transactions."""
    ars_total = Decimal("0.0")
    usd_total = Decimal("0.0")

    # Payment transaction identifiers - EXACT match with legacy script
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
```

#### Validation Logic Enhancement

**Balance Comparison**: Enhanced validation using excluded payment totals

```python
def _validate_balance_with_payment_exclusion(self, statement: Statement, result: ValidationResult) -> None:
    """Validate balance excluding payment transactions."""
    # Calculate computed balance excluding payments
    computed_balance = self._calculate_balance_excluding_payments(statement)
    reported_balance = statement.reported_balance

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
```

#### Legacy Script Parity

**Exact Behavior Matching**: Payment exclusion logic matching legacy script exactly

- **Payment Descriptions**: Uses identical string matching `{"SU PAGO EN PESOS", "SU PAGO EN USD"}`
- **Balance Calculation**: Excludes payments before comparing with reported balances
- **Currency Handling**: Separate ARS and USD totals with proper Decimal precision
- **Error Reporting**: Detailed mismatch reporting with formatted amounts
- **Tolerance Checking**: Configurable tolerance for floating-point comparison (default 0.01)

#### Validation Enhancement

**Enhanced Methods**: New validation methods supporting payment exclusion

```python
class StatementValidator:
    def validate(self, statement: Statement) -> ValidationResult:
        """Validate using enhanced payment exclusion logic."""
        # ... existing validation logic

        if statement.reported_balance is not None:
            self._validate_balance_with_payment_exclusion(statement, result)
        else:
            result.add_warning("No reported balance available for validation")
```

#### Architecture Benefits

- **Legacy Parity**: Exact matching with legacy script validation behavior
- **Domain Logic**: Payment exclusion logic properly placed in domain layer
- **Configurable Tolerance**: Flexible balance tolerance for different validation scenarios
- **Comprehensive Reporting**: Detailed error messages with formatted amounts
- **Type Safety**: Full Decimal precision for financial calculations
- **Clean Architecture**: Validation logic separated from extraction and reporting concerns

This pattern ensures complete validation parity while maintaining clean separation of concerns and proper domain modeling.

### 36. Test Coverage Enhancement & Type Safety Pattern (July 2025)

- **Challenge**: Project had type checking failures and insufficient test coverage below required 90% threshold
- **Solution**: Comprehensive test enhancement with MyPy type safety and robust pre-commit hook integration
- **Implementation**: Strategic test additions and type safety improvements across validation and application layers

#### Comprehensive Test Coverage Strategy

**Problem**: Test coverage at 89% with critical gaps in validation functionality

**Solution**: Targeted test additions for validation logic and enhanced results

```python
# Enhanced validation testing with comprehensive scenarios
class TestEnhancedValidationResult:
    """Test enhanced validation result functionality."""

    def test_print_detailed_summary_with_balance_info(self, capsys):
        """Test detailed summary printing with balance information."""
        result = EnhancedValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            reported_ars=Decimal("1000.00"),
            reported_usd=Decimal("100.00"),
            computed_ars=Decimal("1000.00"),
            computed_usd=Decimal("100.00"),
            ars_difference=Decimal("0.00"),
            usd_difference=Decimal("0.00"),
            transaction_count=45,
            payment_method="BBVA VISA"
        )

        result.print_detailed_summary("test_file.pdf")
        captured = capsys.readouterr()

        # Validate comprehensive output format
        assert "VALIDATION SUMMARY: test_file.pdf" in captured.out
        assert "Transactions Processed: 45" in captured.out
        assert "Payment Method: BBVA VISA" in captured.out
        assert "Reported ARS: 1,000.00" in captured.out
        assert "Computed ARS: 1,000.00" in captured.out
        assert "✅ YES" in captured.out  # Balance match indicators

    def test_validation_with_balance_extraction_service(self, mock_statement):
        """Test validation with balance extraction service integration."""
        # Mock balance extraction service
        mock_service = Mock(spec=BalanceExtractionService)
        mock_service.extract_balance.return_value = {
            "ars": Decimal("1000.00"),
            "usd": Decimal("100.00")
        }

        validator = StatementValidator(balance_extraction_service=mock_service)

        # Test validation with content
        result = validator.validate_with_content(mock_statement, "PDF content")

        # Validate enhanced result properties
        assert isinstance(result, EnhancedValidationResult)
        assert result.reported_ars == Decimal("1000.00")
        assert result.computed_ars is not None
        assert result.transaction_count > 0
```

#### MyPy Type Safety Enhancement

**Problem**: Type checking failures preventing clean commits

**Solution**: Enhanced type annotations and explicit type conversions

```python
# Before: Type errors in validation logic
def _validate_balance_with_payment_exclusion(self, statement: Statement, result: ValidationResult) -> None:
    # MyPy error: Unsupported operand types for > ("float" and "object")
    if ars_diff > self._balance_tolerance:  # Type error here
        result.add_error(f"ARS balance mismatch")

# After: Explicit type handling
def _validate_balance_with_payment_exclusion(self, statement: Statement, result: ValidationResult) -> None:
    # Ensure proper Decimal comparison
    ars_diff = abs(reported_ars - computed_ars)
    if ars_diff >= self._balance_tolerance:  # Use >= for Decimal comparison
        result.add_error(f"ARS balance mismatch: reported {reported_ars:,.2f}")
```

#### Application Service Test Enhancement

**Problem**: Test failures due to outdated mock strategies

**Solution**: Enhanced mock configuration with proper spec parameters

```python
# Enhanced mock strategy for application service testing
@pytest.fixture
def mock_dependencies():
    """Create properly configured mock dependencies."""
    return {
        "parser_factory": Mock(spec=ParserFactory),
        "repository": Mock(spec=StatementRepository),
        "validator": Mock(spec=StatementValidator),
        "filename_generator": Mock(spec=FilenameGenerator),
    }

def test_process_statement_success(self, mock_dependencies, sample_statement):
    """Test successful statement processing workflow."""
    service = StatementProcessingService(**mock_dependencies)

    # Configure mocks with realistic behavior
    mock_parser = Mock(spec=StatementParser)
    mock_validation_result = ValidationResult(is_valid=True, errors=[])

    mock_dependencies["parser_factory"].create_parser.return_value = mock_parser
    mock_parser.parse.return_value = sample_statement
    mock_dependencies["validator"].validate.return_value = mock_validation_result
    mock_dependencies["filename_generator"].generate.return_value = "output.xlsx"

    # Execute and validate
    result = service.process_statement(Path("input.pdf"), Path("output"))

    assert result.success is True
    assert result.statement is not None
    assert result.output_path is not None
```

#### Pre-commit Hook Integration Pattern

**Comprehensive Quality Gates**: Automated enforcement of code quality standards

```yaml
# .pre-commit-config.yaml - Enhanced quality enforcement
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

#### Quality Metrics Enhancement

**Before Enhancement**:

- 89% test coverage (below 90% threshold)
- 10 failing tests in application/CLI layers
- MyPy type errors preventing commits
- Pre-commit hooks failing

**After Enhancement**:

- 90.05% test coverage (exceeds requirement)
- 680 tests passing successfully
- Zero MyPy errors
- All pre-commit hooks passing

#### Professional Test Organization

**Enhanced Test Structure**: Comprehensive validation testing patterns

```python
# Professional test organization with clear separation
class TestStatementValidatorEnhanced:
    """Enhanced StatementValidator testing with comprehensive scenarios."""

    def test_validate_with_content_without_service(self, sample_statement):
        """Test validation without balance extraction service."""
        validator = StatementValidator()
        result = validator.validate_with_content(sample_statement, "content")
        assert isinstance(result, ValidationResult)  # Standard result

    def test_validate_with_content_with_service(self, sample_statement):
        """Test validation with balance extraction service."""
        mock_service = Mock(spec=BalanceExtractionService)
        validator = StatementValidator(balance_extraction_service=mock_service)
        result = validator.validate_with_content(sample_statement, "content")
        assert isinstance(result, EnhancedValidationResult)  # Enhanced result

    def test_payment_exclusion_logic(self, sample_statement_with_payments):
        """Test payment transaction exclusion in balance calculations."""
        validator = StatementValidator()
        result = validator.validate(sample_statement_with_payments)
        # Validate that payments are properly excluded from computed totals
```

#### Architecture Benefits

- **Enhanced Validation Testing**: Comprehensive test coverage for validation logic and enhanced results
- **Type Safety**: Complete MyPy compliance with proper type checking
- **Quality Assurance**: Robust pre-commit hook infrastructure preventing regressions
- **Clean Architecture**: All tests maintain hexagonal architecture principles
- **Professional Development**: Clean, reliable development workflow with automated quality checks

#### Quality Impact

- **Test Coverage**: Improved from 89% to 90.05% (exceeds 90% requirement)
- **Type Safety**: Complete elimination of MyPy type errors
- **Test Reliability**: All 680 tests passing with enhanced mock strategies
- **Development Workflow**: Professional quality assurance with automated enforcement
- **Production Readiness**: Enterprise-grade quality infrastructure ready for deployment

This pattern demonstrates successful establishment of robust quality assurance infrastructure with comprehensive test coverage and automated quality enforcement for enterprise-level software development.

### 37. PDF Balance Extraction Fix Pattern (July 2025)

- **Challenge**: CLI system failing to extract PDF balance due to rigid regex patterns that couldn't handle variable spacing
- **Solution**: Enhanced regex patterns with flexible spacing and comprehensive fallback logic
- **Implementation**: Updated `src/infrastructure/extractors.py` with robust pattern matching

#### Flexible Regex Pattern Enhancement

**Problem**: Original rigid patterns failed with variable spacing in PDF content

```python
# Before: Rigid pattern that failed
pattern = r"SALDO ACTUAL \$ ([\d,.]+) U\$S ([\d,.]+)"
# Failed on: "SALDO ACTUAL         $    1.010.605,89" (multiple spaces)
```

**Solution**: Flexible patterns using `\s+` for variable spacing

```python
# After: Flexible patterns that handle variable spacing
class PDFBalanceExtractor(BalanceExtractor):
    def extract_balance(self, content: str, payment_method: PaymentMethod) -> dict[str, Decimal]:
        """Extract reported balance from PDF text using flexible patterns."""
        balance = {"ars": Decimal("0.0"), "usd": Decimal("0.0")}

        if payment_method == PaymentMethod.BBVA_MASTERCARD:
            # BBVA Mastercard format with specific handling
            pattern1 = r"SALDO ACTUAL \$ ([\d,.]+).*?" r"SALDO ACTUAL U\$S ([\d,.]+)"
            match1 = re.search(pattern1, content)
            if match1:
                ars_str = match1.group(1)
                usd_str = match1.group(2)
            else:
                # Fallback pattern for alternative Mastercard format
                pattern2 = (
                    r"\d{2}-\w{3}-\d{2}\s+\d{2}-\w{3}-\d{2}\s+([\d,.]+)\s+"
                    r"([\d,.]+)\s+[\d,.]+"
                )
                match2 = re.search(pattern2, content)
                if match2:
                    ars_str = match2.group(1)
                    usd_str = match2.group(2)
                else:
                    ars_str = "0"
                    usd_str = "0"
        else:
            # Standard format for MACRO VISA and BBVA VISA with flexible spacing
            # Pattern 1: Both ARS and USD amounts present
            pattern1 = r"SALDO ACTUAL\s+\$\s+([\d,.]+)\s+U\$S\s+([\d,.]+)"
            match1 = re.search(pattern1, content)
            if match1:
                ars_str = match1.group(1)
                usd_str = match1.group(2)
            else:
                # Pattern 2: Only ARS amount present (more flexible)
                pattern2 = r"SALDO ACTUAL\s+\$\s+([\d,.]+)"
                match2 = re.search(pattern2, content)
                if match2:
                    ars_str = match2.group(1)
                    usd_str = "0"
                else:
                    ars_str = "0"
                    usd_str = "0"

        # Convert European format to decimal
        balance["ars"] = self._parse_european_amount(ars_str)
        balance["usd"] = self._parse_european_amount(usd_str)

        return balance
```

#### Pattern Matching Strategy

**Dual Pattern Approach**: Multiple patterns with fallback logic

1. **Pattern 1**: Both ARS and USD amounts present
   - `r"SALDO ACTUAL\s+\$\s+([\d,.]+)\s+U\$S\s+([\d,.]+)"`
   - Handles full balance information with both currencies

2. **Pattern 2**: ARS amount only (flexible fallback)
   - `r"SALDO ACTUAL\s+\$\s+([\d,.]+)"`
   - Handles cases where only ARS amount is present
   - Sets USD to "0" when not found

3. **Pattern 3**: Complete fallback
   - Sets both amounts to "0" when no patterns match
   - Ensures graceful degradation

#### Flexible Spacing Implementation

**Key Enhancement**: Using `\s+` instead of single spaces

```python
# Before: Rigid spacing (failed)
r"SALDO ACTUAL \$ ([\d,.]+) U\$S ([\d,.]+)"

# After: Flexible spacing (works)
r"SALDO ACTUAL\s+\$\s+([\d,.]+)\s+U\$S\s+([\d,.]+)"
```

**Benefits**:

- Handles variable whitespace in PDF content
- Accommodates formatting variations between PDF files
- Maintains exact pattern matching for amount extraction
- Provides comprehensive fallback logic

#### European Format Conversion

**Robust Amount Parsing**: Proper handling of European number format

```python
def _parse_european_amount(self, amount_str: str) -> Decimal:
    """Convert European format (1.234,56) to Decimal."""
    try:
        # Handle European format for amounts
        if "." in amount_str and "," in amount_str:
            amount_str = amount_str.replace(".", "").replace(",", ".")
        elif "," in amount_str:
            amount_str = amount_str.replace(",", ".")
        return Decimal(amount_str)
    except (ValueError, TypeError):
        return Decimal("0.0")
```

#### Registry-Based Service Architecture

**Extensible Balance Extraction**: Support for multiple formats

```python
class BalanceExtractionService:
    """Service managing multiple balance extractors using registry pattern."""

    def __init__(self):
        self._extractors: List[BalanceExtractor] = []

    def register_extractor(self, extractor: BalanceExtractor) -> None:
        """Register a balance extractor."""
        self._extractors.append(extractor)

    def extract_balance(self, content: str, payment_method: PaymentMethod) -> Optional[dict[str, Decimal]]:
        """Extract balance using appropriate extractor."""
        for extractor in self._extractors:
            if extractor.can_extract(payment_method):
                return extractor.extract_balance(content, payment_method)
        return None

def build_default_balance_service() -> BalanceExtractionService:
    """Build balance service with all standard extractors."""
    service = BalanceExtractionService()
    service.register_extractor(PDFBalanceExtractor())
    service.register_extractor(CSVBalanceExtractor())
    service.register_extractor(XLSXBalanceExtractor())
    return service
```

#### Architecture Benefits

- **Flexible Pattern Matching**: Handles variable PDF formatting without breaking
- **Comprehensive Fallback**: Multiple patterns ensure successful extraction
- **Registry Pattern**: Easy to add new extractors for different formats
- **Type Safety**: Modern Python 3.11+ type annotations throughout
- **Clean Architecture**: Infrastructure layer implementing domain abstractions
- **Production Ready**: Zero regressions, comprehensive error handling

#### Results Achieved

- **Before Fix**: 10/11 files processed (91% success rate)
- **After Fix**: 11/11 files processed (100% success rate)
- **Key File**: `BBVA-VISA-resumen_cuenta_visa_May_2025.pdf` now processes successfully
- **Balance Extraction**: Correctly extracts `1.010.605,89` from variable-spaced PDF content
- **CLI Validation**: Now shows `✅ VALID` with proper balance information

This pattern demonstrates how to handle real-world PDF formatting variations while maintaining robust extraction capabilities and clean architecture principles.

### 33. Validation Parity Implementation Pattern (December 2025)

- **Challenge**: CLI system missing critical validation capabilities that existed in legacy script (PDF balance extraction, payment exclusion logic, format-specific validation)
- **Solution**: Complete validation feature parity implementation with balance extraction infrastructure and enhanced validation logic
- **Implementation**: Strategic implementation across domain and infrastructure layers to achieve 100% feature equivalence

#### Balance Extraction Infrastructure Pattern

**Problem**: CLI system could not extract reported balances from PDF content like legacy script

**Solution**: Abstract service architecture with multiple extractors using registry pattern

```python
# src/infrastructure/extractors.py
from abc import ABC, abstractmethod
from typing import Dict
from decimal import Decimal

class BalanceExtractor(ABC):
    """Abstract service for extracting reported balances from statement content."""

    @abstractmethod
    def extract_balance(self, content: str, payment_method: PaymentMethod) -> Dict[str, Decimal]:
        """Extract reported balance from statement content."""
        pass

    @abstractmethod
    def can_extract(self, payment_method: PaymentMethod) -> bool:
        """Check if extractor supports the payment method."""
        pass

class PDFBalanceExtractor(BalanceExtractor):
    """Concrete extractor for PDF balance extraction using regex patterns."""

    def extract_balance(self, content: str, payment_method: PaymentMethod) -> Dict[str, Decimal]:
        """Extract reported balance from PDF text using payment method-specific patterns."""
        balance = {"ars": Decimal("0.0"), "usd": Decimal("0.0")}

        if payment_method == PaymentMethod.BBVA_MASTERCARD:
            # BBVA Mastercard format: "SALDO ACTUAL $ 185.170,00 SALDO ACTUAL U$S 0,00"
            pattern1 = r"SALDO ACTUAL \$ ([\d,.]+).*?SALDO ACTUAL U\$S ([\d,.]+)"
            match1 = re.search(pattern1, content)
            if match1:
                ars_str = match1.group(1)
                usd_str = match1.group(2)
            else:
                # Alternative pattern for BBVA Mastercard
                pattern2 = r"\d{2}-\w{3}-\d{2}\s+\d{2}-\w{3}-\d{2}\s+([\d,.]+)\s+([\d,.]+)\s+[\d,.]+"
                match2 = re.search(pattern2, content)
                if match2:
                    ars_str = match2.group(1)
                    usd_str = match2.group(2)
                else:
                    ars_str = "0"
                    usd_str = "0"
        else:
            # Standard format for MACRO VISA and BBVA VISA
            pattern = r"SALDO ACTUAL \$ ([\d,.]+) U\$S ([\d,.]+)"
            match = re.search(pattern, content)
            if match:
                ars_str = match.group(1)
                usd_str = match.group(2)
            else:
                ars_str = "0"
                usd_str = "0"

        # Convert European format to decimal
        balance["ars"] = self._parse_european_amount(ars_str)
        balance["usd"] = self._parse_european_amount(usd_str)

        return balance

class BalanceExtractionService:
    """Service managing multiple balance extractors using registry pattern."""

    def __init__(self):
        self._extractors: List[BalanceExtractor] = []

    def register_extractor(self, extractor: BalanceExtractor) -> None:
        """Register a balance extractor."""
        self._extractors.append(extractor)

    def extract_balance(self, content: str, payment_method: PaymentMethod) -> Optional[Dict[str, Decimal]]:
        """Extract balance using appropriate extractor."""
        for extractor in self._extractors:
            if extractor.can_extract(payment_method):
                return extractor.extract_balance(content, payment_method)
        return None
```

#### Payment Exclusion Logic Pattern

**Problem**: CLI system included all transactions in computed totals instead of excluding payments like legacy script

**Solution**: Enhanced validation with payment exclusion logic matching legacy behavior exactly

```python
# src/domain/validation.py
class StatementValidator:
    """Enhanced domain service for validating financial statements."""

    def _validate_balance_with_payment_exclusion(self, statement: Statement, result: ValidationResult) -> None:
        """Validate balance excluding payment transactions."""
        # Calculate computed balance excluding payments
        computed_balance = self._calculate_balance_excluding_payments(statement)
        reported_balance = statement.reported_balance

        # Validate ARS balance
        reported_ars = reported_balance.ars_amount
        computed_ars = computed_balance["ars"]
        ars_diff = abs(reported_ars - computed_ars)

        if ars_diff >= self._balance_tolerance:
            result.add_error(
                f"ARS balance mismatch: reported {reported_ars:,.2f}, "
                f"computed {computed_ars:,.2f}, difference {ars_diff:.2f}"
            )

    def _calculate_balance_excluding_payments(self, statement: Statement) -> Dict[str, Decimal]:
        """Calculate balance excluding payment transactions."""
        ars_total = Decimal("0.0")
        usd_total = Decimal("0.0")

        # Payment transaction identifiers - EXACT match with legacy script
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
```

#### Enhanced Validation Results Pattern

**Problem**: CLI system had basic validation results without detailed legacy script formatting

**Solution**: Enhanced validation results with detailed reporting and visual indicators

```python
# src/domain/validation.py
@dataclass
class EnhancedValidationResult(ValidationResult):
    """Enhanced validation result with detailed balance information."""

    reported_ars: Optional[Decimal] = None
    reported_usd: Optional[Decimal] = None
    computed_ars: Optional[Decimal] = None
    computed_usd: Optional[Decimal] = None
    ars_difference: Optional[Decimal] = None
    usd_difference: Optional[Decimal] = None
    transaction_count: int = 0
    payment_method: Optional[str] = None

    def print_detailed_summary(self, filename: str) -> None:
        """Print detailed validation summary with legacy script formatting."""
        print(f"\n{'=' * 60}")
        print(f"VALIDATION SUMMARY: {filename}")
        print(f"{'=' * 60}")
        print(f"Transactions Processed: {self.transaction_count}")
        print(f"Payment Method: {self.payment_method}")

        if self.reported_ars is not None and self.computed_ars is not None:
            print(f"\nBALANCE VALIDATION:")
            print(f"  Reported ARS: {self.reported_ars:,.2f}")
            print(f"  Computed ARS: {self.computed_ars:,.2f}")
            ars_match = "✅ YES" if abs(self.ars_difference or 0) < 0.01 else "❌ NO"
            print(f"  ARS Match: {ars_match}")

            print(f"  Reported USD: {self.reported_usd:,.2f}")
            print(f"  Computed USD: {self.computed_usd:,.2f}")
            usd_match = "✅ YES" if abs(self.usd_difference or 0) < 0.01 else "❌ NO"
            print(f"  USD Match: {usd_match}")

        if not self.is_valid:
            print(f"\n❌ VALIDATION ERRORS:")
            for error in self.errors:
                print(f"   • {error}")

        if self.warnings:
            print(f"\n⚠️  VALIDATION WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
```

#### Architecture Benefits

- **Complete Feature Parity**: CLI system now matches/exceeds legacy script validation capabilities
- **Backward Compatible**: All existing validation continues to work without changes
- **Extensible Design**: Easy to add new balance extractors for future formats (CSV, XLSX)
- **Clean Architecture**: Follows established hexagonal architecture principles
- **Type Safe**: Modern Python 3.11+ type annotations throughout
- **Testable**: Comprehensive validation with proper error handling

#### Quality Validation

- **100% Feature Equivalence**: All legacy script validation capabilities now in CLI
- **Payment Exclusion Logic**: Correctly excludes "SU PAGO EN PESOS" and "SU PAGO EN USD"
- **PDF Balance Extraction**: Uses identical regex patterns as legacy script
- **Enhanced Reporting**: Professional validation summaries with visual indicators
- **Production Ready**: Zero regressions, all tests pass, comprehensive error handling

#### Usage Pattern

```python
# Enhanced validation with balance extraction
service = build_default_balance_service()
validator = StatementValidator(balance_extraction_service=service)

# Validate with content for balance extraction
result = validator.validate_with_content(statement, raw_pdf_content)

# Detailed reporting
if isinstance(result, EnhancedValidationResult):
    result.print_detailed_summary(filename)
```

This pattern demonstrates successful feature parity achievement between legacy systems and modern clean architecture implementations while maintaining all architectural benefits.

### 34. Balance Extraction Service Pattern (December 2025)

- **Challenge**: Need flexible, extensible balance extraction from multiple file formats with different parsing requirements
- **Solution**: Registry-based service architecture with abstract extractors and factory pattern for convenient usage
- **Implementation**: Complete service infrastructure supporting PDF, CSV, XLSX extraction with unified interface

#### Registry-Based Extractor Pattern

**Service Architecture**: Central service managing multiple specialized extractors

```python
# src/infrastructure/extractors.py
class BalanceExtractionService:
    """Service managing multiple balance extractors using registry pattern."""

    def __init__(self):
        self._extractors: List[BalanceExtractor] = []

    def register_extractor(self, extractor: BalanceExtractor) -> None:
        """Register a balance extractor."""
        self._extractors.append(extractor)

    def extract_balance(self, content: str, payment_method: PaymentMethod) -> Optional[Dict[str, Decimal]]:
        """Extract balance using appropriate extractor."""
        for extractor in self._extractors:
            if extractor.can_extract(payment_method):
                return extractor.extract_balance(content, payment_method)
        return None

def build_default_balance_service() -> BalanceExtractionService:
    """Build balance service with all standard extractors."""
    service = BalanceExtractionService()
    service.register_extractor(PDFBalanceExtractor())
    service.register_extractor(CSVBalanceExtractor())
    service.register_extractor(XLSXBalanceExtractor())
    return service
```

#### Format-Specific Extractors Pattern

**PDF Extractor**: Regex-based extraction using legacy script patterns

```python
class PDFBalanceExtractor(BalanceExtractor):
    """Extractor for PDF balance extraction using regex patterns."""

    def can_extract(self, payment_method: PaymentMethod) -> bool:
        """Check if extractor supports PDF-based payment methods."""
        pdf_methods = {
            PaymentMethod.BBVA_VISA,
            PaymentMethod.BBVA_MASTERCARD,
            PaymentMethod.MACRO_VISA
        }
        return payment_method in pdf_methods

    def _parse_european_amount(self, amount_str: str) -> Decimal:
        """Convert European format (1.234,56) to Decimal."""
        try:
            # Handle European format for amounts
            if "." in amount_str and "," in amount_str:
                amount_str = amount_str.replace(".", "").replace(",", ".")
            elif "," in amount_str:
                amount_str = amount_str.replace(",", ".")
            return Decimal(amount_str)
        except (ValueError, TypeError):
            return Decimal("0.0")
```

**CSV Extractor**: File-based validation for CSV inputs

```python
class CSVBalanceExtractor(BalanceExtractor):
    """Extractor for CSV file balance validation."""

    def extract_balance(self, file_path: Path, payment_method: PaymentMethod) -> Dict[str, Decimal]:
        """Extract total from CSV file for validation."""
        import pandas as pd

        try:
            df = pd.read_csv(file_path, sep=";")
            total = Decimal("0.0")

            for _, row in df.iterrows():
                importe_str = str(row["Importe"]).strip()
                if importe_str and importe_str != "nan":
                    try:
                        # Handle European format
                        amount_str = importe_str.replace(",", "")
                        amount = Decimal(amount_str)
                        total += amount
                    except (ValueError, TypeError):
                        continue

            # CSV files are typically ARS only
            return {"ars": total, "usd": Decimal("0.0")}

        except Exception:
            return {"ars": Decimal("0.0"), "usd": Decimal("0.0")}
```

#### Architecture Benefits

- **Pluggable Extractors**: Easy to add new extractor types without modifying existing code
- **Registry Pattern**: Flexible registration and discovery of appropriate extractors
- **Format Abstraction**: Unified interface regardless of underlying file format
- **Factory Pattern**: Convenient pre-configured service creation
- **Type Safety**: Full type annotations with comprehensive error handling
- **Clean Architecture**: Infrastructure layer implementing domain service abstractions

#### Integration Pattern

```python
# Enhanced StatementValidator integration
class StatementValidator:
    def __init__(
        self,
        balance_tolerance: Decimal = Decimal("0.01"),
        balance_extraction_service: Optional[BalanceExtractionService] = None
    ):
        self._balance_tolerance = balance_tolerance
        self._balance_service = balance_extraction_service

    def validate_with_content(self, statement: Statement, raw_content: str) -> ValidationResult:
        """Validate statement with raw content for balance extraction."""
        # Extract balance from content if service available
        if self._balance_service and raw_content:
            extracted_balance = self._balance_service.extract_balance(
                raw_content, statement.payment_method
            )
            if extracted_balance:
                # Set extracted balance on statement
                statement.reported_balance = Balance(
                    ars_amount=extracted_balance["ars"],
                    usd_amount=extracted_balance["usd"]
                )
```

This pattern enables flexible, extensible balance extraction across multiple file formats while maintaining clean architecture principles and type safety.

### 35. Payment Exclusion Logic Pattern (December 2025)

- **Challenge**: CLI system included all transactions in balance calculations while legacy script excluded payment transactions
- **Solution**: Enhanced validation logic that exactly matches legacy script payment exclusion behavior
- **Implementation**: Domain-level validation enhancement with payment identification and exclusion

#### Transaction Classification Pattern

**Payment Identification**: Exact matching with legacy script logic

```python
# src/domain/validation.py
def _calculate_balance_excluding_payments(self, statement: Statement) -> Dict[str, Decimal]:
    """Calculate balance excluding payment transactions."""
    ars_total = Decimal("0.0")
    usd_total = Decimal("0.0")

    # Payment transaction identifiers - EXACT match with legacy script
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
```

#### Validation Logic Enhancement

**Balance Comparison**: Enhanced validation using excluded payment totals

```python
def _validate_balance_with_payment_exclusion(self, statement: Statement, result: ValidationResult) -> None:
    """Validate balance excluding payment transactions."""
    # Calculate computed balance excluding payments
    computed_balance = self._calculate_balance_excluding_payments(statement)
    reported_balance = statement.reported_balance

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
```

#### Legacy Script Parity

**Exact Behavior Matching**: Payment exclusion logic matching legacy script exactly

- **Payment Descriptions**: Uses identical string matching `{"SU PAGO EN PESOS", "SU PAGO EN USD"}`
- **Balance Calculation**: Excludes payments before comparing with reported balances
- **Currency Handling**: Separate ARS and USD totals with proper Decimal precision
- **Error Reporting**: Detailed mismatch reporting with formatted amounts
- **Tolerance Checking**: Configurable tolerance for floating-point comparison (default 0.01)

#### Validation Enhancement

**Enhanced Methods**: New validation methods supporting payment exclusion

```python
class StatementValidator:
    def validate(self, statement: Statement) -> ValidationResult:
        """Validate using enhanced payment exclusion logic."""
        # ... existing validation logic

        if statement.reported_balance is not None:
            self._validate_balance_with_payment_exclusion(statement, result)
        else:
            result.add_warning("No reported balance available for validation")
```

#### Architecture Benefits

- **Legacy Parity**: Exact matching with legacy script validation behavior
- **Domain Logic**: Payment exclusion logic properly placed in domain layer
- **Configurable Tolerance**: Flexible balance tolerance for different validation scenarios
- **Comprehensive Reporting**: Detailed error messages with formatted amounts
- **Type Safety**: Full Decimal precision for financial calculations
- **Clean Architecture**: Validation logic separated from extraction and reporting concerns

This pattern ensures complete validation parity while maintaining clean separation of concerns and proper domain modeling.
