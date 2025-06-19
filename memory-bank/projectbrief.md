# Financial Statement Processor - Project Brief

## Project Overview

A Python-based tool that automates the conversion of financial PDF statements from various Argentine banks into standardized Excel format, eliminating manual data entry and ensuring consistent transaction categorization.

## Core Requirements

### Primary Goals

- **Multi-Format Processing**: Extract transaction data from both PDF statements and XLS account files
- **Multi-Bank Support**: Handle different bank formats and layouts across multiple file types
- **Data Standardization**: Convert to consistent Excel format with standardized columns
- **Currency Handling**: Support both ARS and USD transactions with proper decimal formatting
- **Transaction Categorization**: Automatically identify payment types, taxes, adjustments

### Success Criteria

- Process all supported statement types with 100% accuracy
- Handle European number format (1.234,56) correctly across all formats
- Maintain data integrity across all transaction types and file formats
- Generate Excel output compatible with financial analysis tools
- Provide clear error handling and validation

### Current Scope

- **Supported**: 10 statement types across 4 file formats
  - **PDF Statements**: Macro VISA, BBVA VISA, BBVA Mastercard
  - **XLS Statements**: BBVA Account, Macro Account
  - **CSV Statements**: BBVA VISA Autorizaciones, BBVA VISA Movimientos, Macro VISA Autorizaciones, Macro VISA Movimientos
  - **XLSX Statements**: Mercadopago
- **Processing Pipeline**: Multi-format input → Standardized Excel output
- **Currencies**: ARS (Argentine Peso) and USD with automatic detection
- **Transaction Types**: Purchases, payments, taxes, adjustments, transfers, interest, compensations, commissions, investment returns, money transfers, bonifications, promotions
- **Date Formats**: DD.MM.YY (PDF VISA), DD-MMM-YY (PDF Mastercard), DD/MM/YYYY (XLS/CSV), ISO 8601 timestamps (XLSX)
- **Quality Assurance**: 201 tests with 90% coverage, pre-commit hooks, type safety

### Expansion Roadmap

- **Phase 3**: Santander bank support
- **Phase 4**: Additional financial institutions
- **Future**: CLI interface, batch processing, transaction categorization

## Recent Completions

### File Naming Normalization (June 2025)

- **Centralized Filename Generation**: Implemented `generate_output_filename()` function for consistent output naming
- **Standardized Naming Convention**: `{BANK}-{PRODUCT}-{TYPE}-transactions.xlsx` format across all statement types
- **Professional Consistency**: BANK and PRODUCT always uppercase, TYPE lowercase for clean, professional output
- **Mapping Strategy**: Payment method mapping with fallback for unknown methods, extensible for new banks
- **File Type Support**: Support for main, auth, and movs file types with optional date inclusion
- **Comprehensive Testing**: 23 unit tests covering all functionality, edge cases, and error conditions
- **Coverage Maintenance**: Maintained 90% coverage despite adding new functionality (178→201 tests)
- **Zero Regressions**: All existing tests continue to pass with new standardized naming

### CSV Processing Support (June 2025)

- **CSV Statement Processing**: Complete support for 4 CSV statement types (BBVA VISA Auth/Movs, Macro VISA Auth/Movs)
- **Multi-Format Architecture**: Extended system to support 9 total statement types (3 PDF + 2 XLS + 4 CSV)
- **CSV-Specific Parsing**: Native pandas-based CSV processing with column mapping and European number format handling
- **Date Conversion**: DD/MM/YYYY to YYYY-MM-DD conversion for CSV date columns
- **Currency Mapping**: Automatic Pesos→ARS, Dolares→USD conversion from CSV data
- **CSV Validation**: Input CSV total validation against output Excel totals for data integrity
- **Detection Enhancement**: Extended filename-based detection for CSV files using case-insensitive keyword matching
- **Comprehensive Testing**: 30 new tests (24 integration + 6 unit) bringing total to 160 tests with 90% coverage
- **Test Architecture**: Professional CSV test organization following established patterns

### Macro Account XLS Support (June 2025)

- **Macro Account Processing**: Complete support for Macro Account XLS statements
- **Enhanced Detection Logic**: Case-insensitive filename-based detection using "MACRO" and "MOVIMIENTOS" keywords
- **Native XLS Processing**: Direct parsing of datetime objects and numeric data from XLS structure
- **Source Balance Validation**: Validation against first row Saldo column value (34,122.00)
- **Transaction Variety**: Support for compensations, transfers, credit card payments, commissions, capitalizations
- **Comprehensive Testing**: 13 new integration tests covering complete end-to-end workflow
- **Unit Test Expansion**: 8 additional detection tests for XLS filename patterns

### BBVA Account XLS Support (June 2025)

- **BBVA Account Processing**: Complete support for BBVA Account XLS statements
- **XLS Data Processing**: Native Excel file processing for structured account data
- **Filename-Based Detection**: Intelligent payment method detection using file patterns
- **European Number Format**: Seamless handling of 1.234,56 notation in XLS format
- **Date Format Handling**: DD/MM/YYYY format conversion to standardized output
- **XLS-Specific Validation**: Input total validation against generated output totals
- **Comprehensive Testing**: 12 new integration tests for complete XLS workflow validation

### BBVA Mastercard Support (December 2025)

- **BBVA Mastercard Processing**: Complete support for BBVA Mastercard PDF statements
- **Date Format Handling**: DD-MMM-YY format with Spanish abbreviations ("Abr" = April)
- **Single-Line Transaction Format**: Adapted parsing for Mastercard's consolidated transaction format
- **Balance Validation**: Custom balance extraction for Mastercard statement format

### Mercadopago XLSX Support (June 2025)

- **Mercadopago Processing**: Complete support for Mercadopago XLSX account summaries
- **XLSX Format Support**: Native Excel file processing for Mercadopago transaction data
- **ISO 8601 Date Handling**: Conversion from "2025-02-01T17:45:36Z" to "2025-02-01" format
- **Filename-Based Detection**: Case-insensitive detection using "MERCADOPAGO" keyword in XLSX files
- **Transaction Variety**: Support for payments, income, withdrawals, investment returns, money transfers
- **Balance Validation**: Input XLSX total validation against output Excel totals (-64,841.11 ARS)
- **Comprehensive Testing**: 18 new tests (14 integration + 4 unit) for complete XLSX workflow validation

### Pre-commit Hook Integration & Type Safety (June 2025)

- **Pre-commit Hook Integration**: Complete automated quality checks with ruff, mypy, and pytest
- **MyPy Type Safety**: Modern Python 3.11+ type annotations with comprehensive static type checking
- **Type Error Resolution**: Fixed 4 mypy type errors preventing commits (float vs int assignments, pandas type conversions)
- **Development Workflow**: Clean, professional development experience with automated quality enforcement
- **Hook Configuration**: Comprehensive pre-commit setup ensuring code quality before every commit
- **Type Annotations**: Enhanced code reliability with proper type hints and conversions
- **Zero Breaking Changes**: All 178 tests pass with 89.74% coverage, maintained full functionality

### Code Quality & Warning Resolution (June 2025)

- **Warning-Free Environment**: Eliminated all 14 openpyxl warnings for clean test output
- **Ruff Integration**: Modern Python linter and formatter (10-100x faster than flake8)
- **Code Quality Standards**: Fixed bare except clauses, f-string issues, and line length violations
- **Professional Configuration**: Updated `pyproject.toml` with warning filters and development tools
- **Clean Development**: Zero warnings in test output, professional development experience

### Quality Assurance (Current)

- **Test Coverage**: 178 comprehensive tests with 90% meaningful code coverage
- **Integration Tests**: 8 end-to-end test suites covering all 10 statement types
- **Professional Test Organization**: Behavior-focused test architecture with logical grouping
- **Test Quality**: Descriptive names, clear validation, excellent maintainability
- **Coverage Maintenance**: Added 48 new tests for Mercadopago and CSV functionality maintaining high-quality coverage standards
- **Warning-Free Testing**: Clean test execution with zero warnings or noise

## Target Users

- Personal finance managers
- Accounting professionals
- Financial analysts
- Anyone processing Argentine bank statements regularly

## Key Constraints

- PDF must be text-based (not scanned images)
- Argentine banking formats and conventions
- European decimal notation (comma as decimal separator)
- Date format variations (DD.MM.YY)

## Technical Requirements

- Python 3.11+
- Cross-platform compatibility
- Minimal external dependencies
- Comprehensive test coverage
- Clear documentation and examples
