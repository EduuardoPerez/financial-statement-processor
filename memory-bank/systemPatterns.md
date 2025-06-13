# System Patterns - Financial Statement Processor

## Architecture Overview

### Single-Module Design Pattern

- **Current Approach**: All logic in `parse_visa_statement.py` for simplicity
- **Benefits**: Easy to understand, minimal complexity, fast execution
- **Future Evolution**: Will modularize as we add more banks

### Processing Pipeline Architecture

```
PDF Input → Text Extraction → Pattern Matching → Data Transformation → Excel Output
```

## Core Design Patterns

### 1. Strategy Pattern for Bank Detection

- **Pattern**: `detect_payment_method()` function analyzes PDF content
- **Implementation**: String matching against known bank and card type indicators
- **Extensibility**: New banks add their indicator patterns
- **Card Type Priority**: Mastercard detection takes precedence over VISA when both present

```python
def detect_payment_method(full_text):
    # Bank indicators
    macro_indicators = ["MACRO PREMIA", "BANCO MACRO", "WWW.MACRO.COM.AR"]
    bbva_indicators = ["BBVA", "WWW.BBVA.COM.AR"]

    # Card type indicators
    visa_found = "VISA" in text_upper
    mastercard_found = "MASTERCARD" in text_upper

    # Detection logic with card type precedence
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
- **Output**: YYYY-MM-DD format
- **Logic**: Years < 50 = 20XX, years >= 50 = 19XX
- **Spanish Support**: "Abr" = April for Spanish month abbreviations

```python
# VISA format: 15.03.25 -> 2025-03-15
# Mastercard format: 15-Mar-25 -> 2025-03-15
# Spanish: 04-Abr-25 -> 2025-04-04
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

## Quality Assurance Patterns

### 1. Test Architecture Pattern

- **Structure**: Separated unit tests (fast) from integration tests (thorough)
- **Unit Tests**: `tests/unit/` - Individual function validation
- **Integration Tests**: `tests/integration/` - End-to-end PDF processing
- **Benefits**: Fast feedback loop for development, comprehensive validation for releases

### 2. Bank-Specific Testing Pattern

- **Organization**: Dedicated test files for each bank
- **MACRO Tests**: `test_macro_visa_processing.py` - Complete MACRO validation
- **BBVA Tests**: `test_bbva_visa_processing.py` - Complete BBVA validation
- **Benefits**: Isolated testing, easy debugging, parallel development

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

### 7. Test Suite Organization Pattern

- **Directory Structure**: Clear separation by test type and purpose
- **Documentation**: Comprehensive README with usage examples
- **Command Examples**: Bank-specific, type-specific, and full test runs
- **Scalability**: Easy to add new banks with consistent patterns

```
tests/
├── __init__.py
├── README.md
├── test_data/                          # Isolated test data
├── unit/                               # Fast, isolated tests
│   ├── test_convert_date.py           # Date function tests
│   ├── test_detect_payment_method.py  # Bank detection tests
│   ├── test_extract_balance_from_pdf.py  # Balance extraction tests
│   ├── test_validate_balance.py       # Balance validation tests
│   ├── test_print_processing_summary.py  # Summary output tests
│   ├── test_error_handling_paths.py   # Error handling tests
│   └── test_complete_coverage.py      # Specialized coverage tests
└── integration/                        # End-to-end tests
    ├── test_macro_visa_processing.py  # MACRO workflow tests
    └── test_bbva_visa_processing.py   # BBVA workflow tests
```

## Test Coverage Implementation Patterns

### 1. pytest-cov Integration Pattern

- **Tool**: pytest-cov plugin for comprehensive coverage measurement
- **Configuration**: `.coveragerc` file with proper exclusions and settings
- **Benefits**: Industry-standard coverage measurement with detailed reporting

### 2. Coverage Enforcement Pattern

- **Thresholds**: Configurable coverage requirements (80%, 90%, 100%)
- **Automated Failure**: Tests fail if coverage drops below threshold
- **Commands**:
  - `uv run pytest --cov=. --cov-report=term-missing --cov-fail-under=90 --cov-config=.coveragerc`
- **CI Integration**: Ready for automated testing pipelines

### 3. Coverage Exclusion Strategy

- **Test Files**: Exclude all `tests/*` from coverage calculation
- **Documentation**: Exclude `memory-bank/*`, README files
- **Data Directories**: Exclude `input/*`, `output/*`, `expected_output/*`
- **Configuration**: Exclude `pyproject.toml`, `.gitignore`, etc.
- **Main Blocks**: Exclude `if __name__ == "__main__":` sections

### 4. Specialized Coverage Tests Pattern

- **Error Handling**: Targeted tests for ValueError exceptions and continue statements
- **Edge Cases**: Tests for zero amounts, negative amounts, invalid formats
- **Fallback Logic**: Tests for European number format fallbacks
- **Line Coverage**: Strategic tests to hit specific uncovered code paths

### 5. Coverage Quality Assessment

- **Current Achievement**: 90.11% coverage (263 statements, 26 missing)
- **Quality Focus**: Meaningful coverage of business logic, not artificial inflation
- **Uncovered Code**: Complex error handling, edge cases, defensive programming
- **Industry Standard**: Exceeds typical 70-80% industry benchmarks

### 6. Coverage Documentation Pattern

- **COVERAGE.md**: Comprehensive documentation with usage examples
- **Current Metrics**: Real-time coverage statistics and achievement tracking
- **Command Reference**: All coverage commands with explanations
- **Best Practices**: Guidelines for maintaining and improving coverage
