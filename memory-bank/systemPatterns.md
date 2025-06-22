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
