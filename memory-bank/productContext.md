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
- **Date Format Variations**: DD.MM.YY, DD-MMM-YY, and DD/MM/YYYY formats require careful parsing
- **Multiple File Formats**: PDF statements (text extraction) and XLS files (structured data)
- **Card Type Differences**: VISA vs Mastercard statements have different layouts and date formats

## Solution Overview

### What We're Building

An intelligent multi-format processor that transforms both messy PDF bank statements and structured XLS account files into clean, standardized Excel data ready for financial analysis. Currently supports Macro VISA, BBVA VISA, BBVA Mastercard (PDF), and BBVA Account (XLS) with automatic payment method detection.

### Core Value Propositions

1. **Time Savings**: 5-minute automated process vs. hours of manual work
2. **Accuracy**: Eliminates human transcription errors
3. **Standardization**: Consistent output format regardless of bank or card type
4. **Integration Ready**: Excel output works with existing financial tools
5. **Multi-Format Support**: Handles both VISA and Mastercard statement formats seamlessly

## User Experience Goals

### Primary User Journey

1. **Input**: User places PDF or XLS file in input directory
2. **Processing**: Run simple Python script (automatic payment method and format detection)
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

- 100% transaction capture rate from all four supported statement types (Macro VISA, BBVA VISA, BBVA Mastercard, BBVA Account)
- Zero data corruption or formatting errors across PDF and XLS formats
- Complete currency and amount accuracy across all payment methods and file types
- Perfect balance validation for all statement types including XLS-specific validation

### User Success

- Reduces processing time from hours to minutes
- Eliminates manual transcription errors across multiple file formats
- Enables immediate use in financial analysis tools
- Seamless handling of different payment methods and file formats without user intervention

### Technical Success

- Handles all known transaction types correctly across all supported payment methods and formats
- Processes complex European number formats accurately in both PDF and XLS sources
- Maintains data integrity throughout transformation regardless of input format
- Supports multiple date formats (DD.MM.YY for VISA, DD-MMM-YY for Mastercard, DD/MM/YYYY for XLS)
- Comprehensive test coverage ensures reliability across all formats

## Recent Enhancements

### BBVA Account XLS Support (June 2025)

- **Multi-Format Processing**: Extended system to handle structured XLS data alongside PDF text extraction
- **Filename-Based Detection**: Intelligent identification of BBVA Account statements from file patterns
- **XLS-Specific Validation**: Input file total validation against generated output for data integrity
- **Date Format Support**: DD/MM/YYYY format conversion with proper standardization
- **European Number Handling**: Seamless 1.234,56 format processing in structured Excel data
- **Comprehensive Testing**: 12 new integration tests for complete XLS workflow validation

### BBVA Mastercard Support (December 2025)

- **New Format Support**: DD-MMM-YY date format with Spanish month abbreviations
- **Single-Line Transactions**: Adapted parsing for Mastercard's consolidated transaction format
- **Custom Balance Extraction**: Specialized balance validation for Mastercard statements
- **Enhanced Detection**: Card type precedence (Mastercard over VISA when both present)

### Quality Improvements (Current)

- **Expanded Test Suite**: Now 109 tests with 90% meaningful code coverage
- **Real Data Validation**: All tests use actual bank statement files with expected output comparison
- **Professional Test Organization**: Behavior-focused test architecture with logical grouping
- **Regression Protection**: Ensures all existing functionality continues to work perfectly
- **Multi-Format Coverage**: Comprehensive testing of PDF text extraction and XLS structured data processing

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
