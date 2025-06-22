# Active Context - Financial Statement Processor

## Current Work Focus

### Phase 1 → 1.1: Core Domain Models Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Core domain models successfully implemented with comprehensive unit tests
- **Achievement**: Foundation of clean architecture transformation with comprehensive domain layer and complete test coverage
- **Implementation**: Complete `src/domain/models.py` with all required classes and business logic
- **Key Features**:
  - **Currency enum**: ARS and USD support with proper string representation
  - **PaymentMethod enum**: All 6 supported payment methods (Macro VISA, BBVA VISA, BBVA Mastercard, BBVA Account, Macro Account, Mercadopago)
  - **Transaction value object**: Immutable with comprehensive validation and utility methods
  - **Balance value object**: Immutable with currency-specific calculations and comparisons
  - **Statement aggregate root**: Mutable container with business logic and transaction management
  - **Modern Python 3.11+ generics**: Uses `list[Transaction]` instead of `List[Transaction]`
  - **Standard library only**: dataclasses, enum, datetime, decimal, typing
  - **Comprehensive validation**: Business rule enforcement with descriptive error messages
  - **Public API**: Clean exports via `__all__` for controlled interface
- **Unit Tests**: Complete `tests/unit/domain/test_models.py` with 41 comprehensive tests covering:
  - **Valid Construction**: All domain objects with required and optional fields
  - **Validation Rules**: Empty descriptions, zero amounts, payment method mismatches
  - **Immutability**: Transaction and Balance objects are properly frozen
  - **Business Logic**: Statement transaction management, balance calculations, filtering
  - **Error Handling**: Descriptive error messages for all validation failures
  - **Utility Methods**: Credit/debit detection, currency filtering, date ranges
- **Validation**: All tests pass with `uv run --module pytest -q tests/unit/domain/test_models.py`
- **Quality**: Comprehensive testing with immutability, validation, and business logic verification
- **Architecture Alignment**: Perfect foundation for hexagonal architecture and SOLID principles

### Phase 1 → 1.2: Repository Abstractions Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Repository pattern abstractions successfully implemented for hexagonal architecture
- **Achievement**: Core ports (interfaces) established for data access operations, enabling dependency inversion and clean architecture
- **Implementation**: Complete `src/domain/repositories.py` with all required abstract interfaces
- **Key Features**:
  - **FileReader Protocol**: Structural typing interface for file reading operations with `read(path: Path) -> bytes` and `exists(path: Path) -> bool` methods
  - **FileWriter Protocol**: Structural typing interface for file writing operations with `write(path: Path, content: bytes) -> None` and `ensure_directory(path: Path) -> None` methods
  - **StatementRepository ABC**: Abstract base class for statement persistence with `save_statement(statement: Statement, output_path: Path) -> None` and `load_raw_data(input_path: Path) -> bytes` methods
  - **Hexagonal Architecture Compliance**: These abstractions serve as ports that infrastructure adapters will implement
  - **Dependency Inversion**: Core domain depends on abstractions, not concrete implementations
  - **Type Safety**: Full type annotations with pathlib.Path and proper return types
  - **Comprehensive Documentation**: Detailed docstrings with Args, Returns, and Raises sections
  - **Clean Exports**: Proper `__all__` definition for controlled public API
- **Validation**: Successfully validated with `uv run python -c "from domain.repositories import StatementRepository"`
- **Quality**: Clean import validation, proper Protocol vs ABC usage, comprehensive error documentation
- **Architecture Impact**: Enables next phase implementation of concrete adapters in infrastructure layer
- **SOLID Compliance**: Perfect implementation of Dependency Inversion Principle with abstract interfaces

### Phase 1 → 1.3: ExcelStatementRepository Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Concrete Excel repository implementation successfully created in infrastructure layer
- **Achievement**: First concrete adapter implementing the repository abstractions, demonstrating hexagonal architecture in action
- **Implementation**: Complete `src/infrastructure/repositories.py` with `ExcelStatementRepository` class
- **Key Features**:
  - **Dependency Injection**: Uses injected `FileReader` and `FileWriter` for clean architecture compliance
  - **Excel I/O Integration**: Leverages pandas with openpyxl engine for robust Excel file operations
  - **Statement to DataFrame Conversion**: Helper method `_statement_to_dataframe()` transforms domain objects to pandas format
  - **Standardized Output Format**: Creates Excel files with columns: Date, Description, Currency, Amount, Payment Method
  - **Comprehensive Error Handling**: Proper exception handling with FileNotFoundError, ValueError, OSError, and PermissionError
  - **Type Safety**: Full type annotations with modern Python 3.11+ syntax and explicit type declarations
  - **Clean Architecture**: Infrastructure layer implementing domain abstractions without circular dependencies
- **Technical Implementation**:
  - **save_statement()**: Converts Statement to DataFrame and saves as Excel with proper directory creation
  - **load_raw_data()**: Loads raw file data using injected FileReader with comprehensive error handling
  - **_statement_to_dataframe()**: Transforms Transaction objects to standardized DataFrame format
  - **Date Format**: YYYY-MM-DD string format for consistent Excel output
  - **Amount Format**: Float conversion from Decimal for pandas compatibility
- **Validation**:
  - ✅ Dummy snippet from PLAN.md executes without raising exceptions
  - ✅ All 242 existing tests continue to pass (zero regression)
  - ✅ Comprehensive integration testing with domain models
  - ✅ Type checking compliance with mypy
  - ✅ Code quality validation with ruff
- **Architecture Impact**: Demonstrates successful hexagonal architecture implementation with clean separation between domain and infrastructure
- **Quality Standards**: Maintains project's high standards of type safety, error handling, and comprehensive documentation

### Complete Multi-Format Financial Statement Processing System (PRODUCTION READY - June 2025)

- **Status**: ✅ PRODUCTION READY - Comprehensive 10-statement-type processing system fully operational
- **Achievement**: Complete financial statement processor supporting all major Argentine banks and file formats
- **System Capabilities**:
  - **10 Statement Types**: Macro VISA (PDF), BBVA VISA (PDF), BBVA Mastercard (PDF), BBVA Account (XLS), Macro Account (XLS), BBVA VISA Autorizaciones (CSV), BBVA VISA Movimientos (CSV), Macro VISA Autorizaciones (CSV), Macro VISA Movimientos (CSV), Mercadopago (XLSX)
  - **4 File Formats**: PDF text extraction, XLS structured data, CSV parsing, XLSX processing
  - **Multi-Currency**: ARS and USD transaction support across all formats
  - **Intelligent Detection**: Automatic payment method identification from content and filenames
  - **European Number Format**: Perfect 1.234,56 handling across all formats
  - **Multiple Date Formats**: DD.MM.YY, DD-MMM-YY, DD/MM/YYYY, ISO 8601 timestamps
  - **Standardized Output**: Consistent filename normalization across all statement types
- **Quality Metrics**: 251 tests with 91% coverage, zero warnings, professional development workflow
- **Development Infrastructure**: Pre-commit hooks (ruff, mypy, pytest), type safety, automated quality enforcement

### File Naming Normalization Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Comprehensive file naming standardization implemented
- **Achievement**: Professional, consistent output filename generation across all 10 statement types
- **Key Features**:
  - Centralized `generate_output_filename()` function for all naming logic
  - Standardized naming convention: `{BANK}-{PRODUCT}-{TYPE}-transactions.xlsx`
  - Consistent formatting: BANK and PRODUCT always uppercase, TYPE lowercase
  - Support for file type variations (main, auth, movs) and optional date inclusion
  - Mapping for all supported payment methods with fallback for unknown methods
- **Quality**: 23 comprehensive unit tests covering all functionality and edge cases
- **Coverage Maintenance**: Maintained 90% coverage despite adding new functionality (178→201 tests)
- **Professional Output**: Clean, standardized filenames like `BBVA-VISA-transactions.xlsx`, `MACRO-ACCOUNT-transactions.xlsx`

### MyPy Static Type Checking Integration (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Successfully integrated mypy static type checking with modern Python 3.11+ type annotations
- **Achievement**: Enhanced code quality with static type checking, bringing project to modern Python development standards
- **Key Improvements**:
  - Added mypy>=1.8.0 with comprehensive configuration in pyproject.toml
  - Implemented modern Python 3.11+ type syntax (`str | None`, `dict[str, float]`)
  - Added type stubs: pandas-stubs>=2.1.0 and types-openpyxl>=3.1.0
  - Created type aliases for better code readability (Transaction, BalanceDict, ValidationResult)
  - Added type annotations to all major functions in parse_visa_statement.py
  - Gradual adoption approach with permissive settings for future enhancement
  - Seamless integration with existing Ruff and pytest workflow
- **Quality**: All 178 tests still pass, zero breaking changes to functionality
- **Type Safety**: Early error detection and enhanced IDE support for development
- **Documentation**: Type hints serve as inline documentation for function contracts

### flake8 → Ruff Migration (COMPLETED - December 2025)

- **Status**: ✅ COMPLETED - Successfully migrated from flake8 to Ruff for modern code quality tooling
- **Achievement**: Modernized development environment with 10-100x faster linting and enhanced capabilities
- **Key Improvements**:
  - Migrated from flake8 7.2.0 to Ruff 0.12.0
  - Maintained all existing code quality standards (88-character line length, test exceptions)
  - Added modern capabilities: import sorting (isort), code modernization (pyupgrade), auto-fixing
  - All-in-one solution replacing multiple tools (flake8 + isort + pyupgrade)
  - Enhanced rule sets: pycodestyle (E/W), Pyflakes (F), pep8-naming (N), import sorting (I), code modernization (UP)
  - Black-compatible formatting with double quotes and space indentation
- **Quality**: All 178 tests still pass, coverage maintained at 89.78%
- **Auto-fixes**: 20 issues automatically resolved (import sorting, unused imports)
- **Performance**: Dramatically faster linting for improved development experience

### Mercadopago XLSX Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Full Mercadopago XLSX statement support implemented
- **Achievement**: Extended system to support 10th statement type with native XLSX processing
- **Key Features**:
  - Mercadopago XLSX account summary processing (394 transactions)
  - ISO 8601 timestamp conversion ("2025-02-01T17:45:36Z" → "2025-02-01")
  - Filename-based detection for .xlsx files using "MERCADOPAGO" keyword
  - Transaction variety: payments, income, withdrawals, investment returns, money transfers
  - Balance validation: -64,841.11 ARS total matching expected output exactly
- **Quality**: 18 new tests (14 integration + 4 unit) for comprehensive XLSX workflow validation
- **Coverage Maintenance**: Maintained 90% meaningful coverage with all new functionality fully tested

### Code Quality & Warning Resolution (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - All warnings eliminated, professional code quality achieved
- **Achievement**: Zero-warning development environment with enhanced code quality standards
- **Key Improvements**:
  - Eliminated all 14 openpyxl warnings for clean test output
  - Added `.flake8` configuration file with proper linting standards
  - Updated `pyproject.toml` with warning filters and flake8 configuration
  - Fixed bare except clauses with specific exception handling
  - Resolved f-string issues and line length violations
  - Professional development experience with clean, warning-free output
- **Quality**: All 178 tests passing with zero warnings or noise
- **Standards**: Maintained high code quality while expanding functionality

### CSV Processing Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Full CSV statement support for BBVA and Macro VISA files
- **Achievement**: Extended system to support 4 additional CSV file types, bringing total to 9 statement types
- **Key Features**:
  - BBVA VISA Autorizaciones and Movimientos CSV processing
  - Macro VISA Autorizaciones and Movimientos CSV processing
  - CSV-specific validation logic
  - European number format handling in CSV data
  - Date conversion from DD/MM/YYYY to YYYY-MM-DD
  - Currency mapping (Pesos→ARS, Dolares→USD)
- **Quality**: 30 new tests (24 integration + 6 unit) for comprehensive CSV workflow validation
- **Coverage Recovery**: Improved coverage from 75% (post-CSV addition) back to 90% with comprehensive testing

### Test Suite Expansion Achievement (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Comprehensive test coverage for all 9 supported statement types
- **Achievement**: 160 well-organized, meaningful tests with 90% code coverage
- **Delivered**: Professional test architecture covering 9 statement types with end-to-end validation
- **Key Improvements**:
  - Added 24 new integration tests for CSV functionality
  - Added 6 new unit tests for CSV detection and validation
  - Enhanced detection tests for CSV filename patterns
- **Quality**: Maintains high standards with descriptive names and logical organization

### Previous Completion: Macro Account XLS Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Full Macro Account XLS statement support implemented
- **Achievement**: Extended system to support 5th statement type with comprehensive functionality
- **Key Features**: Case-insensitive filename detection, native XLS parsing, source balance validation
- **Quality**: 13 new integration tests + 8 unit tests for complete workflow validation
- **Coverage Impact**: Improved overall coverage from 85% to 91% (+6 percentage points)

### Recent Completion: Macro Account Integration

- **Coverage Achievement**: 91% meaningful code coverage (improved from 85%)
- **Test Suite**: 130 comprehensive tests (added 21 new tests for Macro Account)
- **New Functionality**: Native XLS processing with datetime object handling
- **Test Quality**: Professional integration tests following established patterns
- **Validation Excellence**: Source balance validation against XLS Saldo column

### BBVA Account XLS Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Full BBVA Account XLS statement support implemented
- **Achievement**: Extended system to support structured Excel data processing alongside existing PDF processing
- **Key Features**: Filename-based detection, European number format conversion, DD/MM/YYYY date parsing
- **Quality**: Comprehensive integration tests with 12 new test cases for complete workflow validation
- **Validation**: XLS-specific validation against input file totals, exact output matching expected results

### Phase 1 → 1.4: StatementParser Interface Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - StatementParser ABC successfully implemented with Strategy Pattern foundation
- **Achievement**: Core service abstraction established for pluggable parsing strategies, enabling clean architecture transformation
- **Implementation**: Complete `src/domain/services.py` with `StatementParser` abstract base class
- **Key Features**:
  - **StatementParser ABC**: Abstract strategy interface for different statement formats with three required methods
  - **can_parse(file_path: Path) -> bool**: Determine if parser can handle the given file format
  - **parse(file_path: Path) -> Statement**: Parse file and return properly constructed Statement object
  - **get_supported_extensions() -> set[str]**: Return supported file extensions for parser selection
  - **Strategy Pattern Foundation**: Enables pluggable parsing strategies for PDF, XLS, CSV, XLSX formats
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Domain Integration**: Seamlessly integrates with existing Statement domain model
  - **Validation Ready**: Supports `issubclass(ConcreteParser, StatementParser)` as required
  - **Clean Exports**: Proper `__all__` definition for controlled public API
- **Unit Tests**: Complete `tests/unit/domain/test_services.py` with 9 comprehensive tests covering:
  - **ABC Validation**: Confirms proper abstract base class configuration
  - **Interface Compliance**: Tests all required abstract methods are defined
  - **issubclass Validation**: Key requirement validation for future concrete parsers
  - **Strategy Pattern Support**: Demonstrates interface supports intended design patterns
  - **Domain Model Integration**: Validates seamless integration with existing models
  - **Error Handling**: Tests incomplete implementations and validation scenarios
  - **Multiple Implementations**: Confirms multiple concrete parsers can coexist
  - **Instantiation Control**: Validates abstract class cannot be instantiated directly
  - **Concrete Implementation**: Tests that proper implementations work correctly
- **Validation**: All tests pass with `uv run pytest tests/unit/domain/test_services.py -v`
- **Quality**: 100% interface coverage with comprehensive behavioral validation
- **Architecture Impact**: Provides foundation for Factory Pattern implementation (Phase 1 → 1.5)
- **SOLID Compliance**: Perfect implementation of Strategy Pattern with clean abstractions

### Phase 1 → 1.5: PDFStatementParser Skeleton Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - First concrete StatementParser implementation successfully created
- **Achievement**: Skeleton PDF parser demonstrating Strategy Pattern in action with pdfplumber integration
- **Implementation**: Complete `src/infrastructure/parsers/pdf_parser.py` with `PDFStatementParser` class
- **Key Features**:
  - **Strategy Pattern Implementation**: First concrete implementation of `StatementParser` ABC
  - **Case-Insensitive PDF Detection**: `can_parse()` returns `True` for `.pdf` files (case-insensitive)
  - **pdfplumber Integration**: `_extract_text()` helper method for robust PDF text extraction
  - **Skeleton Parse Method**: Returns `Statement` with zero transactions (foundation for full implementation)
  - **Comprehensive Error Handling**: FileNotFoundError, ValueError, PermissionError, OSError with proper chaining
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Dependency Injection**: Constructor accepts detector parameter for clean architecture compliance
  - **Clean Architecture**: Infrastructure layer implementing domain abstractions
- **Directory Structure**: Created `src/infrastructure/parsers/` with proper module organization
- **Validation Requirements**: ✅ `PDFStatementParser(detector).can_parse(Path("foo.PDF"))` returns `True`
- **pdfplumber Documentation**: Updated techContext.md with usage patterns and integration details
- **Testing**: Successfully tested with real PDF files, extracts 11,421 characters from BBVA VISA statement
- **Quality**: All 251 existing tests continue to pass, zero regression
- **Architecture Impact**: Demonstrates successful Strategy Pattern implementation ready for full parsing logic
- **Next Phase**: Ready for XLSStatementParser implementation (Phase 1 → 1.3 from task)

### Phase 1 → 1.3: XLSStatementParser Skeleton Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Second concrete StatementParser implementation successfully created
- **Achievement**: Skeleton XLS/XLSX parser demonstrating Strategy Pattern expansion with pandas integration
- **Implementation**: Complete `src/infrastructure/parsers/xls_parser.py` with `XLSStatementParser` class
- **Key Features**:
  - **Strategy Pattern Expansion**: Second concrete implementation of `StatementParser` ABC
  - **Dual Extension Support**: `can_parse()` returns `True` for both `.xls` and `.xlsx` files (case-insensitive)
  - **Pandas Integration**: `_load_excel_data()` helper method for robust Excel data loading
  - **Skeleton Parse Method**: Returns `Statement` with zero transactions (foundation for full implementation)
  - **Comprehensive Error Handling**: FileNotFoundError, ValueError, PermissionError, OSError with proper chaining
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Dependency Injection**: Constructor accepts detector parameter for clean architecture compliance
  - **Clean Architecture**: Infrastructure layer implementing domain abstractions
- **Validation Requirements**:
  - ✅ `XLSStatementParser(detector).can_parse(Path("file.xlsx"))` returns `True`
  - ✅ `XLSStatementParser(detector).can_parse(Path("file.xls"))` returns `True`
  - ✅ `XLSStatementParser(detector).can_parse(Path("file.pdf"))` returns `False`
  - ✅ `parser.get_supported_extensions()` returns `{'.xls', '.xlsx'}`
- **Testing**: Successfully tested with mock files, creates proper Statement objects with zero transactions
- **Quality**: All 50 domain tests continue to pass, zero regression
- **Architecture Impact**: Demonstrates successful Strategy Pattern expansion with multiple concrete parsers
- **Next Phase**: Ready for Factory Pattern implementation (Phase 1 → 1.6) for parser creation and management

### Phase 1 → 1.4: DefaultParserFactory Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Concrete factory implementation successfully created with auto-registration
- **Achievement**: Complete infrastructure factory that auto-registers PDF and XLS parsers for convenient usage
- **Implementation**: Complete `src/infrastructure/factories.py` with `DefaultParserFactory` class
- **Key Features**:
  - **Auto-Registration**: Automatically registers `PDFStatementParser` and `XLSStatementParser` in constructor
  - **Dependency Injection**: Takes detector parameter and injects it into both parsers
  - **Factory Pattern Implementation**: Concrete implementation of abstract `ParserFactory` base class
  - **Convenience Interface**: Pre-configured factory ready for immediate use
  - **Extension Support**: Still allows additional parsers to be registered if needed
  - **Clean Architecture**: Infrastructure layer providing concrete implementation of domain abstraction
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
- **Validation Requirements**: ✅ All requirements met
  - ✅ `DefaultParserFactory(detector).get_supported_extensions()` returns `{'.pdf', '.xls', '.xlsx'}`
  - ✅ Factory auto-registers exactly 2 parsers (PDF and XLS)
  - ✅ Both parser types are correctly instantiated and registered
  - ✅ Inherits all base factory functionality (create_parser, register_parser, etc.)
- **Testing**: Successfully validated with comprehensive test scenarios
  - ✅ Extension aggregation works correctly
  - ✅ Parser registration and type validation
  - ✅ Integration with existing Strategy Pattern implementations
- **Quality**: All 267 tests continue to pass, zero regression maintained
- **Architecture Impact**: Completes Phase 1 → 1.4 factory implementation, ready for next phase
- **Usage Pattern**:

  ```python
  detector = PaymentMethodDetector()
  factory = DefaultParserFactory(detector)
  parser = factory.create_parser(Path("statement.pdf"))
  statement = parser.parse(Path("statement.pdf"))
  ```

### Phase 1 → 1.4: ParserFactory Base Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Factory Pattern implementation successfully created for parser creation and management
- **Achievement**: Complete `ParserFactory` base class implementing Factory Pattern with Strategy Pattern integration
- **Implementation**: Complete `src/domain/factories.py` with `ParserFactory` class
- **Key Features**:
  - **Factory Pattern Implementation**: Dynamic parser creation based on file characteristics
  - **Strategy Pattern Integration**: Works seamlessly with existing `StatementParser` ABC implementations
  - **Registration-Based Design**: Parsers are registered dynamically, following Open/Closed Principle
  - **Path-Based Selection**: Uses `parser.can_parse(file_path)` to find appropriate parser
  - **Comprehensive Error Handling**: Raises `ValueError` when no suitable parser is found (key validation requirement)
  - **Extension Discovery**: Aggregates supported extensions from all registered parsers
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Clean Architecture**: Domain layer factory abstraction enabling dependency inversion
- **Core Methods**:
  - **register_parser()**: Register StatementParser implementations with type validation
  - **create_parser()**: Create appropriate parser for given file path with descriptive error messages
  - **get_supported_extensions()**: Aggregate extensions from all registered parsers
  - **get_registered_parsers()**: Return copy of registered parsers for inspection
  - **clear_parsers()**: Remove all registered parsers for testing/reconfiguration
- **Validation Requirements**: ✅ All requirements met
  - ✅ `register_parser()` accepts StatementParser instances and rejects invalid types
  - ✅ `create_parser()` returns first matching parser for supported files
  - ✅ `create_parser()` raises `ValueError` with descriptive message when no parser matches
  - ✅ `get_supported_extensions()` aggregates extensions from all registered parsers
- **Comprehensive Testing**: 16 comprehensive unit tests covering all functionality
  - **Unit Tests**: Factory initialization, parser registration, creation, error handling
  - **Integration Tests**: Concrete parser implementations, registration order effects
  - **Error Scenarios**: Invalid types, unsupported files, no registered parsers
  - **Edge Cases**: First match wins, copy protection, parser clearing
- **Quality Metrics**: All 267 tests pass (251 existing + 16 new), zero regression
- **Architecture Impact**: Completes Factory Pattern foundation for Phase 1 → 1.6 infrastructure implementation
- **SOLID Compliance**: Perfect implementation of Factory Pattern with Strategy Pattern integration

### Clean Import Configuration Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Permanent solution for MyPy import path conflicts implemented
- **Achievement**: Configured project for clean import style eliminating "Source file found twice under different module names" errors
- **Implementation**: Updated `pyproject.toml` MyPy configuration and package discovery settings
- **Key Features**:
  - **Clean Import Style**: Use `from domain.models` instead of `from src.domain.models`
  - **MyPy Configuration**: `mypy_path = "src"`, `namespace_packages = true`, `explicit_package_bases = true`
  - **Package Discovery**: Proper setuptools configuration with `package-dir = {"" = "src"}`
  - **VS Code Integration**: `.vscode/settings.json` with `python.analysis.extraPaths = ["./src"]`
  - **Import Standardization**: Reverted all imports to clean style across infrastructure layer
- **Benefits**: Better IDE support, standard Python conventions, easier refactoring, cleaner code
- **Validation**: All 251 tests pass, MyPy type checking successful, pre-commit hooks working
- **Result**: Permanent solution preventing future MyPy import conflicts while enabling preferred clean import syntax

### Phase 2 → 2.2: Payment-Method Detection Core Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - Abstract PaymentMethodDetector successfully implemented with Strategy Pattern
- **Achievement**: Core payment method detection abstraction established for extensible bank identification, enabling Open/Closed Principle
- **Implementation**: Complete `src/domain/detectors.py` with abstract `BankDetector` and concrete `PaymentMethodDetector` classes
- **Key Features**:
  - **BankDetector ABC**: Abstract strategy interface for bank identification with `can_detect()` and `get_payment_method()` methods
  - **PaymentMethodDetector**: Registry-based detector with registration and detection methods following Strategy Pattern
  - **Registration System**: `register_detector()` method for adding new bank detection strategies dynamically
  - **Content Detection**: `detect_from_content()` method using registered detectors with validation requirement
  - **Filename Detection**: `detect_from_filename()` method for structured file naming patterns (CSV, XLS, XLSX)
  - **Validation Requirement**: ✅ Raises `ValueError` when `detect_from_content` is called before any detectors are registered
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Clean Architecture**: Domain layer abstraction enabling dependency inversion and extensibility
- **Core Methods**:
  - **register_detector()**: Register BankDetector implementations with type validation
  - **detect_from_content()**: Detect payment method from content using registered detectors (key validation requirement)
  - **detect_from_filename()**: Detect payment method from filename patterns for CSV/XLS/XLSX files
  - **get_registered_detectors()**: Return copy of registered detectors for inspection
  - **clear_detectors()**: Remove all registered detectors for testing/reconfiguration
- **Validation Requirements**: ✅ All requirements met
  - ✅ Calling `detect_from_content` before any detectors are registered raises `ValueError`
  - ✅ Registration and detection methods work correctly with proper error handling
  - ✅ Integration with existing `PaymentMethod` enum from domain models
  - ✅ Follows established clean architecture patterns in the codebase
- **Comprehensive Testing**: Complete `tests/unit/domain/test_detectors.py` with 23 comprehensive tests covering:
  - **Abstract Base Class**: BankDetector cannot be instantiated, proper subclass validation
  - **Registration System**: Valid detector registration, invalid type rejection, multiple detector support
  - **Content Detection**: Successful detection, first match wins, no match handling, empty content validation
  - **Filename Detection**: CSV (BBVA/Macro VISA), XLS (BBVA/Macro Account), XLSX (Mercadopago) pattern recognition
  - **Error Handling**: TypeError for invalid types, ValueError for no detectors/unknown patterns
  - **Registry Management**: Copy protection, detector clearing, registration order precedence
  - **Integration Tests**: Concrete detector implementations, precedence order validation
- **Quality Metrics**: All 290 tests pass (267 existing + 23 new), coverage at 91.86% (exceeds 90% requirement)
- **Architecture Impact**: Enables Open/Closed Principle for adding new banks without modifying existing code
- **SOLID Compliance**: Perfect implementation of Strategy Pattern with registry-based extensibility

### Phase 2 → 2.2: Concrete Bank Detectors Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - MacroDetector and BBVADetector successfully implemented with build_default_payment_detector function
- **Achievement**: Complete concrete bank detector implementations enabling extensible payment method detection from content
- **Implementation**: Complete `src/infrastructure/detectors.py` with `MacroDetector`, `BBVADetector`, and `build_default_payment_detector()` function
- **Key Features**:
  - **MacroDetector**: Concrete implementation for Macro bank statement identification
    - **Detection Indicators**: "MACRO PREMIA", "BANCO MACRO", "WWW.MACRO.COM.AR", "MACRO" (flexible matching)
    - **Payment Method Logic**: Returns `MACRO_VISA` for VISA content, `MACRO_ACCOUNT` for other Macro statements
    - **Case-Insensitive**: Handles variations like "Banco Macro" vs "BANCO MACRO"
  - **BBVADetector**: Concrete implementation for BBVA bank statement identification
    - **Detection Indicators**: "BBVA", "WWW.BBVA.COM.AR"
    - **Payment Method Logic**: Returns `BBVA_MASTERCARD` (priority), `BBVA_VISA`, or `BBVA_ACCOUNT`
    - **Precedence Handling**: Mastercard detection takes precedence over VISA when both present
  - **build_default_payment_detector()**: Factory function creating pre-configured detector
    - **Auto-Registration**: Automatically registers MacroDetector and BBVADetector
    - **Ready-to-Use**: Returns fully configured PaymentMethodDetector instance
    - **Extensible**: Additional detectors can still be registered if needed
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
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Error Handling**: Proper ValueError for empty content and unknown methods
  - **Clean Architecture**: Infrastructure layer implementing domain abstractions
  - **Code Quality**: Flake8 compliant with proper line length management
- **Architecture Impact**: Completes Phase 2 → 2.2 concrete detector implementation, enabling Open/Closed Principle for new banks
- **Usage Pattern**:

  ```python
  detector = build_default_payment_detector()
  method = detector.detect_from_content("Banco Macro - Visa")
  # Returns PaymentMethod.MACRO_VISA
  ```

### Phase 2 → 2.3: Utility Parsers Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - DateConverter and AmountParser utility classes successfully implemented
- **Achievement**: Single Responsibility Principle utilities extracting date conversion and European number format parsing logic from monolithic code
- **Implementation**: Complete `src/domain/utils.py` with `DateConverter` and `AmountParser` classes
- **Key Features**:
  - **DateConverter Class**: Utility for converting various date formats to standardized date objects
    - **convert_dd_mm_yy()**: Converts DD.MM.YY format (VISA statements) with year logic <50 = 2000s, >=50 = 1900s
    - **convert_dd_mmm_yy()**: Converts DD-MMM-YY format (Mastercard statements) with Spanish month support
    - **Spanish Month Support**: Handles "Abr" for April and other Spanish abbreviations
    - **Comprehensive Error Handling**: Descriptive ValueError messages for invalid formats
  - **AmountParser Class**: Utility for parsing European number format amounts to Decimal objects
    - **parse_european_format()**: Handles 1.234,56 notation with financial precision using Decimal
    - **Multiple Format Support**: 1.234.567,89 (dots + comma), 1234,56 (comma only), 1500,75- (trailing dash)
    - **Negative Amount Handling**: Supports both leading and trailing dash notation
    - **Financial Precision**: Uses Decimal for accurate financial calculations
- **Validation Requirements**: ✅ All requirements met
  - ✅ `DateConverter().convert_dd_mm_yy("05.06.25").year == 2025` (key validation requirement)
  - ✅ Proper year logic implementation with 2000s/1900s cutoff at 50
  - ✅ Spanish month abbreviation support for Mastercard statements
  - ✅ European number format parsing with Decimal precision
- **Code Quality Standards**:
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Clean Architecture**: Domain layer utilities following Single Responsibility Principle
  - **Error Handling**: Comprehensive ValueError handling with descriptive messages
  - **Code Quality**: Flake8 compliant with proper line length management (79 characters)
  - **Documentation**: Comprehensive docstrings with Args, Returns, Raises, and Examples
- **Testing Validation**: ✅ Comprehensive functionality testing passed
  - ✅ Date conversion: "05.06.25" → 2025-06-05 (year 2025 confirmed)
  - ✅ Spanish months: "04-Abr-25" → 2025-04-04 (April in Spanish)
  - ✅ European amounts: "1.234,56" → Decimal('1234.56') (financial precision)
  - ✅ All utility methods working correctly with proper error handling
- **Architecture Impact**: Enables clean extraction of utility logic from monolithic parsers, supporting clean architecture transformation
- **Integration Ready**: Utilities ready for integration with infrastructure parsers (PDFStatementParser, XLSStatementParser)

### Phase 2 → 2.4: TransactionBuilder Implementation (COMPLETED - June 2025)

- **Status**: ✅ COMPLETED - TransactionBuilder class successfully implemented with dependency injection
- **Achievement**: Single Responsibility Principle builder for constructing Transaction objects from PDF line components
- **Implementation**: Complete `src/domain/builders.py` with `TransactionBuilder` class
- **Key Features**:
  - **Dependency Injection**: Constructor accepts `DateConverter` and `AmountParser` instances for clean architecture compliance
  - **build_from_pdf_line()**: Core method for building Transaction objects from parsed PDF line components
  - **Component Validation**: Validates all input components (date_str, description, amount_str) before processing
  - **Error Handling**: Comprehensive ValueError handling with descriptive error messages and proper exception chaining
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Clean Architecture**: Domain layer builder following Single Responsibility Principle
- **Method Signature**:

  ```python
  def build_from_pdf_line(
      self,
      date_str: str,           # DD.MM.YY format (e.g., "05.06.25")
      description: str,        # Transaction description text
      amount_str: str,         # European format (e.g., "1.234,56")
      currency: Currency,      # Currency enum value (ARS or USD)
      payment_method: PaymentMethod,  # PaymentMethod enum value
  ) -> Transaction:
  ```

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
- **Code Quality Standards**:
  - **Type Safety**: Modern Python 3.11+ type annotations with comprehensive documentation
  - **Clean Architecture**: Domain layer builder using injected domain utilities
  - **Error Handling**: Comprehensive ValueError handling with descriptive messages
  - **Code Quality**: Flake8 compliant with proper line length management
  - **Documentation**: Comprehensive docstrings with Args, Returns, Raises, and Examples
- **Architecture Impact**: Completes Phase 2 → 2.4 builder implementation, enabling clean Transaction object construction from PDF parsing workflows
- **Integration Ready**: Builder ready for integration with PDF parsing infrastructure components

### Memory Bank Status

- **Status**: ✅ UPDATED - June 2025 - Post-Utility Parsers Implementation (Phase 2 → 2.3 Complete)
- **Last Update**: After completing Phase 2 → 2.3 utility parsers implementation with DateConverter and AmountParser classes
- **Coverage**: Complete documentation of all 10 supported statement types, modern development infrastructure with clean pre-commit workflow, comprehensive type safety, Phase 1 → 1.2 repository abstractions, Phase 1 → 1.3 ExcelStatementRepository implementation, Phase 1 → 1.4 StatementParser interface, Phase 1 → 1.5 PDFStatementParser skeleton, Phase 1 → 1.3 XLSStatementParser skeleton, Phase 1 → 1.4 ParserFactory base implementation, Phase 1 → 1.4 DefaultParserFactory implementation, Phase 2 → 2.2 PaymentMethodDetector implementation, Phase 2 → 2.2 concrete bank detectors implementation, Phase 2 → 2.3 utility parsers implementation (COMPLETE), and clean import configuration
- **Architecture Progress**: Clean architecture transformation progressing successfully with domain utilities now extracted from monolithic code
- **Next Phase**: Ready for next phase of clean architecture transformation (Phase 3 implementation) or CLI interface implementation

## Recent Patterns Discovered

### Pre-commit Hook Integration Best Practices

- **Type Safety**: Explicit type annotations and conversions prevent mypy errors
- **Variable Initialization**: Use appropriate types from initialization (0.0 vs 0 for float variables)
- **Pandas Type Handling**: Convert pandas types to Python native types with explicit str() conversions
- **Hook Configuration**: Comprehensive pre-commit setup with ruff, mypy, and pytest ensures code quality
- **Clean Commits**: All hooks must pass before commits are allowed, maintaining high standards

### Test Organization Best Practices

- **Behavior-Focused Testing**: Tests organized by what they validate, not coverage metrics
- **Descriptive Naming**: Test function names clearly explain the behavior being tested
- **Logical Grouping**: Related tests grouped in coherent test classes and files
- **Error Handling Separation**: Dedicated test suite for error handling and edge cases
- **Format-Specific Testing**: European number format tests separated for clarity

### Test Suite Architecture

- **Error Handling**: `test_error_handling.py` - Invalid formats, exceptions, edge cases
- **Number Formats**: `test_european_number_format.py` - 1.234,56 format parsing
- **Transaction Types**: `test_transaction_types.py` - Tax, payment, adjustment parsing
- **Core Functions**: Individual test files for date conversion, payment detection, etc.
- **Integration Tests**: End-to-end PDF processing with real bank statements

### European Number Format Handling

- **Critical Pattern**: Progressive format detection for 1.234,56 notation
- **Implementation**: Multi-stage conversion logic handles various edge cases
- **Reliability**: Robust handling of mixed separators and trailing dashes

### Transaction Type Classification

- **Payment Detection**: "SU PAGO EN PESOS" with negative amount logic
- **Tax Identification**: Multiple tax keywords with positive amount logic
- **Adjustment Handling**: "AJUSTE" patterns with negative amount logic
- **Regular Purchases**: Reference number + description + amount parsing

### Bank Detection Strategy

- **Content-Based**: Analyzes PDF text for bank-specific indicators
- **Extensible Design**: Easy to add new bank patterns
- **Current Implementation**: Macro bank detection with VISA card identification

## Key Decisions & Preferences

### Development Workflow Standards

- **Pre-commit Hooks**: Mandatory ruff, mypy, and pytest checks before commits
- **Type Safety**: Modern Python 3.11+ type annotations with mypy validation
- **Code Quality**: Ruff for fast, comprehensive linting and formatting
- **Test Coverage**: Maintain 90% meaningful coverage with comprehensive test suite
- **Clean Commits**: Zero warnings, all hooks passing, professional development experience

### Test Quality Standards

- **Meaningful Coverage**: Focus on behavior validation over line coverage metrics
- **Professional Organization**: Tests grouped logically by functionality
- **Descriptive Names**: Every test clearly explains what behavior it validates
- **Maintainability**: Easy to understand, modify, and extend test suite

### Code Architecture Choices

- **Single Module**: Keep all logic in one file for simplicity during early development
- **Line-by-Line Processing**: Robust approach for variable PDF formatting
- **Graceful Degradation**: Continue processing even if individual transactions fail
- **Test-Driven Development**: Comprehensive test suite with expected output validation

### Data Handling Standards

- **Date Format**: Always output YYYY-MM-DD for consistency
- **Negative Amounts**: Payments and adjustments always negative
- **Currency Consistency**: Detect and preserve ARS/USD accurately
- **Description Cleaning**: Remove amounts, preserve reference numbers

### Quality Assurance Approach

- **Integration Testing**: Use real PDF files with expected output comparison
- **Data Integrity**: Validate transaction counts, amounts, currency distribution
- **Regression Protection**: Comprehensive test coverage prevents breaking changes
- **Test Organization**: Clear separation of unit tests vs integration tests

## Next Development Priorities

### Phase 1: System Improvements (Next Priority)

- **CLI Interface**: Add command-line argument parsing for custom file paths
- **Batch Processing**: Handle multiple PDF files in one execution
- **Configuration System**: External config for bank patterns and settings
- **Error Reporting**: Enhanced error messages and logging system

### Phase 2: Additional Banks (Medium Priority)

- **Santander Support**: Third bank implementation following BBVA success pattern
- **Additional Banks**: Expand to other Argentine financial institutions
- **Generic Framework**: Abstract common patterns for easier bank addition

### Phase 3: Output Enhancements (Lower Priority)

- **Multiple Formats**: Add CSV and JSON output options
- **Template Support**: Customizable Excel templates
- **Data Validation**: Enhanced validation rules and error detection

## Active Technical Considerations

### Development Environment Excellence

- **Pre-commit Integration**: Seamless workflow with automatic quality checks
- **Type Safety**: Modern Python development with comprehensive type checking
- **Code Quality**: Fast, reliable linting and formatting with Ruff
- **Test Automation**: Comprehensive test suite with coverage validation
- **Professional Standards**: Clean, warning-free development experience

### Test Suite Maintenance

- **Quality Over Quantity**: Focus on meaningful tests rather than coverage metrics
- **Logical Organization**: Keep tests grouped by functionality
- **Professional Standards**: Maintain descriptive names and clear test structure
- **Regression Prevention**: Ensure all changes are properly tested

### Modularity Planning

- **When to Refactor**: Consider splitting into modules when adding 3rd bank
- **Architecture Evolution**: Move from single file to package structure
- **Backward Compatibility**: Maintain existing API during refactoring

### Testing Strategy

- **Test Data Management**: Organize test PDFs and expected outputs by bank
- **Test Automation**: Ensure all tests run automatically
- **Performance Testing**: Validate processing speed with larger statements

### Documentation Standards

- **Memory Bank Updates**: Update after significant changes or discoveries
- **Code Comments**: Minimal comments, self-explaining code preferred
- **README Maintenance**: Keep installation and usage instructions current

## Project Insights & Learnings

### Modern Python Development Excellence

- **Type Safety**: MyPy integration provides early error detection and better IDE support
- **Code Quality**: Ruff provides fast, comprehensive linting with auto-fixing capabilities
- **Pre-commit Hooks**: Automated quality checks ensure consistent, professional code
- **Development Workflow**: Clean, efficient development process with immediate feedback
- **Professional Standards**: Zero-warning, type-safe code with comprehensive testing

### Test Quality Transformation

- **Before**: 160 tests with many cryptic, coverage-focused duplicates
- **After**: 97 well-organized, meaningful tests with clear purpose
- **Improvement**: Dramatically better maintainability and readability
- **Coverage**: 90% meaningful coverage vs 93% artificial coverage

### Argentine Banking Complexity

- **Number Formats**: European notation is non-negotiable, must handle perfectly
- **Multi-Currency**: ARS/USD mixing requires careful currency detection
- **Transaction Variety**: Each bank has unique transaction type patterns
- **Language Specifics**: Spanish terminology and abbreviations are critical

### PDF Processing Realities

- **Text-Based Requirement**: Cannot process scanned images
- **Layout Sensitivity**: Small formatting changes can break parsing
- **Robust Patterns**: Need flexible regex patterns for reliable extraction
- **Quality Validation**: Real-world testing essential for reliability

### Development Workflow Effectiveness

- **uv Package Manager**: Fast, reliable dependency management
- **pytest Framework**: Comprehensive testing with clear output
- **Reference Files**: Expected output validation catches regressions
- **Incremental Development**: Small, validated changes work best

## Current Implementation Strengths

### Development Infrastructure Excellence

- **Pre-commit Integration**: Automated quality checks with ruff, mypy, and pytest
- **Type Safety**: Modern Python 3.11+ type annotations with comprehensive checking
- **Code Quality**: Fast, reliable linting and formatting with auto-fixing
- **Test Automation**: Comprehensive test suite with coverage validation
- **Professional Workflow**: Clean, efficient development with immediate feedback

### Test Suite Excellence

- **Professional Organization**: Clear, logical test structure
- **Meaningful Coverage**: Tests validate actual behavior, not arbitrary metrics
- **Maintainability**: Easy to understand, modify, and extend
- **Quality Standards**: Descriptive names, proper grouping, clear purpose

### Robustness

- **Error Handling**: Graceful degradation prevents total failures
- **Edge Case Coverage**: Handles various number formats and transaction types
- **Data Integrity**: Comprehensive validation ensures accurate output

### Maintainability

- **Clear Structure**: Easy to understand and modify
- **Test Coverage**: Changes are validated against expected behavior
- **Documentation**: Well-documented codebase with examples

### Extensibility

- **Bank Detection**: Easy to add new bank identification patterns
- **Transaction Types**: Straightforward to add new transaction categories
- **Output Formats**: Ready for additional output format support

## Immediate Next Steps

1. **CLI Interface Implementation**: Add command-line argument parsing for custom file paths
2. **Batch Processing Design**: Handle multiple PDF files in single execution
3. **Configuration System**: External config file for bank patterns and settings
4. **Enhanced Error Reporting**: Detailed error messages and logging system
5. **Third Bank Planning**: Assess modularization needs for Santander support

## Test Suite Organization (Current State)

### Unit Tests (8 files, focused testing)

- `test_convert_date.py` - Date conversion functionality
- `test_detect_payment_method.py` - Bank and card type detection (includes XLS filename detection)
- `test_error_handling.py` - Error handling and edge cases
- `test_european_number_format.py` - European number format parsing
- `test_extract_balance_from_pdf.py` - Balance extraction from PDFs
- `test_print_processing_summary.py` - Output formatting
- `test_transaction_types.py` - Transaction type parsing
- `test_validate_balance.py` - Balance validation logic

### Integration Tests (8 files, end-to-end testing)

- `test_bbva_account_processing.py` - BBVA Account XLS complete workflow
- `test_bbva_mastercard_processing.py` - BBVA Mastercard PDF complete workflow
- `test_bbva_visa_processing.py` - BBVA VISA PDF complete workflow
- `test_bbva_visa_csv_processing.py` - BBVA VISA CSV complete workflow
- `test_macro_account_processing.py` - Macro Account XLS complete workflow
- `test_macro_visa_processing.py` - Macro VISA PDF complete workflow
- `test_macro_visa_csv_processing.py` - Macro VISA CSV complete workflow
- `test_mercadopago_processing.py` - Mercadopago XLSX complete workflow

### Test Quality Metrics

- **Total Tests**: 267 (all passing) - Added 16 new tests for Factory Pattern implementation
- **Coverage**: 91.08% meaningful coverage (exceeds 90% requirement)
- **Organization**: Professional, logical grouping with domain services and factory test modules
- **Maintainability**: Excellent - descriptive names, clear structure, comprehensive interface and factory testing
- **Functionality**: All application features verified working correctly including Strategy Pattern and Factory Pattern implementations
- **Recent Addition**: 16 comprehensive Factory Pattern tests covering parser registration, creation, error handling, and integration scenarios
- **Quality Assurance**: Pre-commit hooks ensure all tests pass before commits, zero regression maintained
