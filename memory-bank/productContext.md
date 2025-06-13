# Product Context - Financial Statement Processor

## Problem Statement

### Current Pain Points

- **Manual Data Entry**: Processing bank statements requires tedious manual transcription of transaction data
- **Format Inconsistency**: Different banks use varying PDF layouts and number formats
- **Error-Prone Process**: Manual entry leads to mistakes in amounts, dates, and descriptions
- **Time Consumption**: Hours spent on what should be automated tasks
- **Limited Analysis**: Raw PDFs don't integrate well with financial analysis tools

### Argentine Banking Specifics

- **European Number Format**: Banks use 1.234,56 format (periods for thousands, commas for decimals)
- **Multi-Currency Statements**: ARS and USD transactions on same statement
- **Complex Transaction Types**: Various tax entries, adjustments, and payment types
- **Date Format Variations**: DD.MM.YY and DD-MMM-YY formats require careful parsing
- **Card Type Differences**: VISA vs Mastercard statements have different layouts and date formats

## Solution Overview

### What We're Building

An intelligent PDF processor that transforms messy bank statements into clean, structured Excel data ready for financial analysis. Currently supports Macro VISA, BBVA VISA, and BBVA Mastercard statements with automatic payment method detection.

### Core Value Propositions

1. **Time Savings**: 5-minute automated process vs. hours of manual work
2. **Accuracy**: Eliminates human transcription errors
3. **Standardization**: Consistent output format regardless of bank or card type
4. **Integration Ready**: Excel output works with existing financial tools
5. **Multi-Format Support**: Handles both VISA and Mastercard statement formats seamlessly

## User Experience Goals

### Primary User Journey

1. **Input**: User places PDF file in input directory
2. **Processing**: Run simple Python script (automatic payment method detection)
3. **Output**: Clean Excel file with standardized transaction data
4. **Analysis**: Use Excel file in existing financial workflows

### Expected Outcomes

- **Complete Transaction Data**: All transactions captured with proper categorization
- **Proper Formatting**: Amounts, dates, and currencies correctly formatted
- **Readable Descriptions**: Clear transaction descriptions with reference numbers
- **Ready for Analysis**: Data structure supports immediate financial analysis
- **Payment Method Transparency**: Clear identification of payment method in output

## Product Characteristics

### Reliability

- Handles edge cases in transaction formatting across all supported payment methods
- Robust error detection and reporting
- Consistent results across different statement periods and formats
- Comprehensive balance validation for all statement types

### Usability

- Simple command-line execution
- Clear error messages when issues occur
- Minimal setup requirements
- Automatic payment method detection - no user configuration needed

### Extensibility

- Designed to easily add support for new banks and card types
- Modular architecture allows customization
- Test framework ensures quality across expansions
- Pattern-based approach makes adding new formats straightforward

## Success Metrics

### Functional Success

- 100% transaction capture rate from all supported statements (Macro VISA, BBVA VISA, BBVA Mastercard)
- Zero data corruption or formatting errors
- Complete currency and amount accuracy across all payment methods
- Perfect balance validation for all statement types

### User Success

- Reduces processing time from hours to minutes
- Eliminates manual transcription errors
- Enables immediate use in financial analysis tools
- Seamless handling of different payment methods without user intervention

### Technical Success

- Handles all known transaction types correctly across all supported payment methods
- Processes complex European number formats accurately
- Maintains data integrity throughout transformation
- Supports multiple date formats (DD.MM.YY for VISA, DD-MMM-YY for Mastercard)
- Comprehensive test coverage ensures reliability

## Recent Enhancements (December 2025)

### BBVA Mastercard Support

- **New Format Support**: DD-MMM-YY date format with Spanish month abbreviations
- **Single-Line Transactions**: Adapted parsing for Mastercard's consolidated transaction format
- **Custom Balance Extraction**: Specialized balance validation for Mastercard statements
- **Enhanced Detection**: Card type precedence (Mastercard over VISA when both present)
- **Comprehensive Testing**: 22 new tests specifically for BBVA Mastercard functionality

### Quality Improvements

- **Expanded Test Suite**: Now 83 tests (up from 63) with 87% code coverage
- **Real PDF Validation**: All tests use actual bank PDF files with expected output comparison
- **Regression Protection**: Ensures all existing functionality continues to work perfectly
- **Edge Case Coverage**: Comprehensive testing of date formats, amount parsing, and error handling

## Future Vision

### Next Phase Capabilities

- **CLI Interface**: Command-line arguments for custom file paths and batch processing
- **Additional Banks**: Santander and other Argentine financial institutions
- **Enhanced Output**: Multiple format support (CSV, JSON) and customizable templates
- **Configuration System**: External configuration for bank patterns and user preferences

### Long-term Goals

- **Universal Argentine Bank Support**: Handle all major banks and card types
- **Advanced Analytics**: Built-in financial analysis and reporting features
- **Enterprise Integration**: Database connectivity and API interfaces
- **Web Interface**: Browser-based interface for non-technical users
