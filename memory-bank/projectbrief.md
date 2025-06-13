# Financial Statement Processor - Project Brief

## Project Overview

A Python-based tool that automates the conversion of financial PDF statements from various Argentine banks into standardized Excel format, eliminating manual data entry and ensuring consistent transaction categorization.

## Core Requirements

### Primary Goals

- **PDF Processing**: Extract transaction data from bank statement PDFs
- **Multi-Bank Support**: Handle different bank formats and layouts
- **Data Standardization**: Convert to consistent Excel format with standardized columns
- **Currency Handling**: Support both ARS and USD transactions with proper decimal formatting
- **Transaction Categorization**: Automatically identify payment types, taxes, adjustments

### Success Criteria

- Process Macro VISA statements with 100% accuracy
- Handle European number format (1.234,56) correctly
- Maintain data integrity across all transaction types
- Generate Excel output compatible with financial analysis tools
- Provide clear error handling and validation

### Current Scope

- **Supported**: Macro VISA, BBVA VISA, and BBVA Mastercard credit card statements
- **Format**: PDF input → Excel output
- **Currencies**: ARS (Argentine Peso) and USD
- **Transaction Types**: Purchases, payments, taxes, adjustments
- **Date Formats**: DD.MM.YY (VISA) and DD-MMM-YY (Mastercard) with Spanish month support

### Expansion Roadmap

- **Phase 3**: Santander bank support
- **Phase 4**: Additional financial institutions
- **Future**: CLI interface, batch processing, transaction categorization

## Recent Completion: BBVA Mastercard Support

### Delivered Capabilities (December 2025)

- **BBVA Mastercard Processing**: Complete support for BBVA Mastercard PDF statements
- **Date Format Handling**: DD-MMM-YY format with Spanish abbreviations ("Abr" = April)
- **Single-Line Transaction Format**: Adapted parsing for Mastercard's consolidated transaction format
- **Balance Validation**: Custom balance extraction for Mastercard statement format
- **Test Coverage**: 83 comprehensive tests with 87% code coverage

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
