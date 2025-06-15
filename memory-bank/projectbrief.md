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

- **Supported**: Macro VISA (PDF), BBVA VISA (PDF), BBVA Mastercard (PDF), BBVA Account (XLS), and Macro Account (XLS)
- **Formats**: PDF input → Excel output, XLS input → Excel output
- **Currencies**: ARS (Argentine Peso) and USD
- **Transaction Types**: Purchases, payments, taxes, adjustments, transfers, interest, compensations, commissions
- **Date Formats**: DD.MM.YY (VISA), DD-MMM-YY (Mastercard), DD/MM/YYYY (XLS Account), YYYY-MM-DD (datetime objects in Macro Account)

### Expansion Roadmap

- **Phase 3**: Santander bank support
- **Phase 4**: Additional financial institutions
- **Future**: CLI interface, batch processing, transaction categorization

## Recent Completions

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

### Quality Assurance (Current)

- **Test Coverage**: 130 comprehensive tests with 91% meaningful code coverage
- **Integration Tests**: 5 end-to-end test suites covering all statement types
- **Professional Test Organization**: Behavior-focused test architecture with logical grouping
- **Test Quality**: Descriptive names, clear validation, excellent maintainability
- **Coverage Improvement**: Added 21 new tests for Macro Account functionality (+6% coverage increase)

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
