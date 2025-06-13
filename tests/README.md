# Test Suite Structure

This directory contains the comprehensive test suite for the Financial Statement Processor, organized into clear categories for maintainability and efficient execution.

## Directory Structure

```
tests/
├── __init__.py
├── README.md
├── test_data/
│   ├── input/                          # Test PDF files (copied from ../input/)
│   │   ├── MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf
│   │   ├── BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf
│   │   └── BBVA-VISA-resumen_cuenta_visa_May_2025.pdf
│   └── expected_output/                # Expected test results (copied from ../expected_output/)
│       ├── MACRO-VISA-transactions.csv
│       ├── MACRO-VISA-transactions.xlsx
│       ├── BBVA-VISA-transactions.csv
│       └── BBVA-VISA-transactions.xlsx
├── unit/
│   ├── __init__.py
│   ├── test_convert_date.py           # Date conversion function tests
│   └── test_detect_payment_method.py  # Bank detection logic tests
└── integration/
    ├── __init__.py
    ├── test_macro_visa_processing.py  # End-to-end MACRO PDF processing
    └── test_bbva_visa_processing.py   # End-to-end BBVA PDF processing
```

## Test Categories

### Unit Tests (`tests/unit/`)

Fast, isolated tests for individual functions:

- **Date Conversion**: Tests the `convert_date()` function with various date formats
- **Payment Method Detection**: Tests bank detection logic for both MACRO and BBVA

### Integration Tests (`tests/integration/`)

End-to-end tests using real PDF files:

- **MACRO VISA Processing**: Complete workflow tests using MACRO PDF files
- **BBVA VISA Processing**: Complete workflow tests using BBVA PDF files

## Running Tests

### All Tests

```bash
uv run pytest tests/ -v
```

### Unit Tests Only (fast)

```bash
uv run pytest tests/unit/ -v
```

### Integration Tests Only

```bash
uv run pytest tests/integration/ -v
```

### Bank-Specific Tests

```bash
# MACRO tests only
uv run pytest tests/integration/test_macro_visa_processing.py -v

# BBVA tests only
uv run pytest tests/integration/test_bbva_visa_processing.py -v
```

## Test Data

Test data is copied from the main project directories to ensure test isolation:

- Input PDFs are copied from `../input/` to `tests/test_data/input/`
- Expected outputs are copied from `../expected_output/` to `tests/test_data/expected_output/`

This structure allows tests to run independently without affecting the main project files.

## Test Coverage

Current test suite includes:

- **34 total tests** across 5 test files - **ALL PASSING** ✅
- **Unit tests**: 16 tests covering core functions
- **Integration tests**: 18 tests covering end-to-end workflows
- **Bank coverage**: Both MACRO and BBVA banks with comprehensive test patterns

Each integration test validates:

- Transaction count accuracy
- Currency handling (ARS/USD)
- Amount totals and calculations
- Date range and format consistency
- Payment method detection
- Transaction type parsing
- Negative amount validation for payments/adjustments
