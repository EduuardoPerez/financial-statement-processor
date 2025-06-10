# Integration Tests for MACRO VISA Statement Parser

This document describes the comprehensive integration tests created for the `parse_visa_statement.py` module.

## Test Overview

The test suite validates the MACRO VISA PDF parser using real data from `input/MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf` and compares results against the expected output in `expected_output/MACRO-VISA-transactions.csv`.

## Test Coverage

### Integration Test (`test_parse_visa_pdf_integration`)

- **Purpose**: End-to-end validation of the PDF parsing functionality
- **Validates**: Overall data integrity including transaction count, currency distribution, amount totals, date ranges, and special transaction types
- **Uses Real Data**: Processes the actual PDF file and validates against expected CSV output

### Individual Component Tests

#### 1. Transaction Count (`test_transaction_count`)

- Ensures exactly 91 transactions are parsed from the PDF
- Validates parser completeness

#### 2. Currency Handling (`test_currency_handling`)

- Verifies correct parsing of ARS (90 transactions) and USD (1 transaction)
- Validates multi-currency support
- Ensures no invalid currencies are present

#### 3. Amount Totals (`test_amount_totals`)

- Validates arithmetic accuracy of parsed amounts
- Checks ARS total: -122,087.04
- Checks USD total: 11.30
- Uses floating-point tolerance for comparison

#### 4. Date Range and Format (`test_date_range_and_format`)

- Validates date parsing from DD.MM.YY to YYYY-MM-DD format
- Ensures date range: 2022-05-25 to 2022-12-22
- Verifies consistent ISO date formatting

#### 5. Payment Method Consistency (`test_payment_method_consistency`)

- Ensures all transactions are correctly labeled as "Macro VISA"
- Validates metadata consistency

#### 6. Transaction Type Parsing (`test_specific_transaction_types`)

- **Payment transactions**: "SU PAGO EN PESOS" (1 transaction)
- **Adjustment transactions**: "AJUSTE P/DESCNTO. EN COMERCIO" (1 transaction)
- **Tax transactions**: Various tax types (IMPUESTO, IIBB, IVA, DB.RG, DB.IMPUESTO)
- Validates parser's ability to handle different transaction categories

#### 7. Negative Amount Validation (`test_negative_amounts`)

- Ensures payments and adjustments have negative amounts
- Validates proper sign handling for different transaction types

### Unit Tests for Helper Functions

#### Date Conversion Tests (`TestConvertDate`)

- **2000s years**: Validates 22 → 2022, 00 → 2000
- **1900s years**: Validates 99 → 1999, 50 → 1950
- **Padding**: Validates 1.1.22 → 2022-01-01

## Key Features Tested

### European Number Format Handling

- Validates parsing of amounts like "1.234,56" → 1234.56
- Ensures proper decimal conversion

### Complex Transaction Types

- Regular purchases with reference numbers
- Multi-currency transactions (ARS/USD)
- Tax entries with various formats
- Payment and adjustment entries
- European-style amount formatting

### Data Integrity Validation

- End-to-end accuracy verification
- Cross-validation with known good output
- Comprehensive error detection

## Running the Tests

```bash
# Install development dependencies
uv add --dev pytest

# Run all tests with verbose output
uv run pytest test_parse_visa_statement.py -v

# Run specific test categories
uv run pytest test_parse_visa_statement.py::TestParseVisaStatement::test_parse_visa_pdf_integration -v
uv run pytest test_parse_visa_statement.py::TestConvertDate -v
```

## Test Data

- **Input**: `input/MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf` (Real bank statement)
- **Expected Output**: `expected_output/MACRO-VISA-transactions.csv` (Validated results)
- **Transactions**: 91 total (90 ARS, 1 USD)
- **Date Range**: May 2022 - December 2022
- **Transaction Types**: Purchases, payments, adjustments, taxes

## Benefits

1. **Regression Testing**: Prevents bugs when modifying the parser
2. **Real Data Validation**: Uses actual bank statements for testing
3. **Comprehensive Coverage**: Tests all major parsing features
4. **Data Integrity**: Ensures accuracy of financial data processing
5. **Documentation**: Serves as specification for expected behavior

## Future Enhancements

- Add tests for edge cases and error conditions
- Include performance benchmarks
- Add tests for other bank statement formats
- Implement property-based testing for date conversion
