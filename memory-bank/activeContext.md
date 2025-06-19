# Active Context - Financial Statement Processor

## Current Work Focus

### Complete Multi-Format Financial Statement Processing System (CURRENT STATUS - June 2025)

- **Status**: ✅ PRODUCTION READY - Comprehensive 10-statement-type processing system fully operational
- **Achievement**: Complete financial statement processor supporting all major Argentine banks and file formats
- **System Capabilities**:
  - **10 Statement Types**: Macro VISA (PDF), BBVA VISA (PDF), BBVA Mastercard (PDF), BBVA Account (XLS), Macro Account (XLS), BBVA VISA Autorizaciones (CSV), BBVA VISA Movimientos (CSV), Macro VISA Autorizaciones (CSV), Macro VISA Movimientos (CSV), Mercadopago (XLSX)
  - **4 File Formats**: PDF text extraction, XLS structured data, CSV parsing, XLSX processing
  - **Multi-Currency**: ARS and USD transaction support across all formats
  - **Intelligent Detection**: Automatic payment method identification from content and filenames
  - **European Number Format**: Perfect 1.234,56 handling across all formats
  - **Multiple Date Formats**: DD.MM.YY, DD-MMM-YY, DD/MM/YYYY, ISO 8601 timestamps
- **Quality Metrics**: 178 tests with 90% coverage, zero warnings, professional development workflow
- **Development Infrastructure**: Pre-commit hooks (ruff, mypy, pytest), type safety, automated quality enforcement

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

### Memory Bank Status

- **Status**: ✅ UPDATED - June 2025 - Post-MyPy type error resolution
- **Last Update**: After completing pre-commit hook mypy type error fixes
- **Coverage**: Complete documentation of all 10 supported statement types, modern development infrastructure with clean pre-commit workflow, and comprehensive type safety
- **Next Phase**: Ready for CLI interface, batch processing, and additional bank implementations

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

- **Total Tests**: 178 (all passing)
- **Coverage**: 89.74% meaningful coverage
- **Organization**: Professional, logical grouping
- **Maintainability**: Excellent - descriptive names, clear structure
- **Functionality**: All application features verified working correctly
- **Recent Addition**: 48 new tests for Mercadopago and CSV functionality
- **Quality Assurance**: Pre-commit hooks ensure all tests pass before commits
