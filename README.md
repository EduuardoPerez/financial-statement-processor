# Financial Statement Processor

A comprehensive Python tool for processing financial statements from various Argentine banks into structured Excel format. Supports 10 different statement types across 4 file formats with intelligent parsing and automatic bank detection.

## Features

### Multi-Format Processing

- **PDF Statements**: Text extraction and parsing for credit card statements
- **XLS Files**: Native Excel processing for account statements
- **CSV Files**: Pandas-based processing for transaction and authorization data
- **XLSX Files**: Modern Excel format support for digital account summaries

### Supported Banks & Statement Types (10 Total)

#### PDF Statements (3 types)

- **Macro VISA**: Credit card statements with DD.MM.YY date format
- **BBVA VISA**: Credit card statements with DD.MM.YY date format
- **BBVA Mastercard**: Credit card statements with DD-MMM-YY date format

#### XLS Statements (2 types)

- **BBVA Account**: Bank account statements with structured data
- **Macro Account**: Bank account statements with datetime objects

#### CSV Statements (4 types)

- **BBVA VISA Autorizaciones**: Authorization transaction data
- **BBVA VISA Movimientos**: Movement transaction data
- **Macro VISA Autorizaciones**: Authorization transaction data
- **Macro VISA Movimientos**: Movement transaction data

#### XLSX Statements (1 type)

- **Mercadopago**: Digital wallet account summaries with ISO 8601 timestamps

### Smart Processing Features

- **Automatic Detection**: Intelligently identifies bank and statement type from content/filename
- **Multi-Currency Support**: Handles both ARS (Argentine Peso) and USD transactions
- **European Number Format**: Properly processes 1.234,56 notation across all formats
- **Multiple Date Formats**: DD.MM.YY, DD-MMM-YY, DD/MM/YYYY, ISO 8601 timestamps
- **Transaction Classification**: Recognizes purchases, payments, taxes, adjustments, bonifications, promotions
- **Balance Validation**: Validates processed totals against source data for accuracy

### Transaction Types Supported

- Regular purchases with reference numbers
- Tax entries (IMPUESTO, IIBB, IVA, DB.RG, DB.IMPUESTO)
- Payments (SU PAGO EN PESOS, SU PAGO EN USD)
- Adjustments and discounts (AJUSTE)
- Bonifications (BONIF.)
- Promotions (OFF Promo)
- Investment returns and money transfers
- Compensations and commissions

## Requirements

- **Python**: 3.11 or higher
- **Dependencies**: Managed via `uv` (recommended) or `pip`
- **File Types**: Text-based PDFs, XLS, CSV, XLSX files
- **Platform**: Cross-platform (Windows, macOS, Linux)

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/EduuardoPerez/financial-statement-processor.git
cd financial-statement-processor

# Install dependencies
uv sync
```

### Using pip (Alternative)

```bash
# Clone the repository
git clone https://github.com/EduuardoPerez/financial-statement-processor.git
cd financial-statement-processor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Usage

### Quick Start

#### Using uv (Recommended)

```bash
# Run the processor (processes all files in input/ directory)
uv run python parse_visa_statement.py
```

#### Using pip (Alternative)

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the processor
python parse_visa_statement.py
```

### File Organization

Place your financial statement files in the `input/` directory:

```
input/
├── MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf
├── BBVA-Visa-resumen_cuenta_visa_Apr_2025.pdf
├── BBVA-Mastercard-2025-04.pdf
├── BBVA-Account-Detalle_mov_cuenta_07_06_2025.xls
├── MACRO-movimientos-de-cuenta.xls
├── BBVA-Visa-Autorizaciones.csv
├── BBVA-Visa-Movimientos.csv
├── MACRO-Visa-Autorizaciones.csv
├── MACRO-VISA-ult-Movimientos.csv
└── mercadopago.xlsx
```

Processed Excel files will be generated in the `output/` directory.

### Custom Processing

```python
from parse_visa_statement import (
    parse_visa_pdf,
    parse_account_xls,
    parse_macro_account_xls,
    parse_bbva_visa_csv,
    parse_macro_visa_csv,
    parse_mercadopago_xlsx
)

# Process specific file types
df_pdf = parse_visa_pdf("path/to/statement.pdf", "output/result.xlsx")
df_xls = parse_account_xls("path/to/account.xls", "output/result.xlsx")
df_csv = parse_bbva_visa_csv("path/to/data.csv", "output/result.xlsx", "auth")
df_xlsx = parse_mercadopago_xlsx("path/to/summary.xlsx", "output/result.xlsx")
```

## Project Structure

```
financial-statement-processor/
├── parse_visa_statement.py    # Main processing engine
├── input/                     # Place statement files here
│   ├── *.pdf                 # PDF statements (Macro/BBVA VISA/Mastercard)
│   ├── *.xls                 # XLS account statements (BBVA/Macro)
│   ├── *.csv                 # CSV transaction data (BBVA/Macro VISA)
│   └── *.xlsx                # XLSX summaries (Mercadopago)
├── output/                    # Generated Excel files
│   ├── MACRO-VISA-transactions.xlsx
│   ├── BBVA-VISA-transactions.xlsx
│   ├── BBVA-Mastercard-transactions.xlsx
│   ├── BBVA-Account-transactions.xlsx
│   ├── Macro-Account-transactions.xlsx
│   ├── BBVA-Visa-auth-transactions.xlsx
│   ├── BBVA-Visa-movs-transactions.xlsx
│   ├── MACRO-Visa-auth-transactions.xlsx
│   ├── MACRO-Visa-movs-transactions.xlsx
│   └── mercadopago-transactions.xlsx
├── expected_output/           # Reference files for testing
├── tests/                     # Comprehensive test suite
│   ├── integration/          # End-to-end tests (8 files)
│   ├── unit/                 # Unit tests (8 files)
│   └── test_data/           # Isolated test data
├── memory-bank/              # Project documentation
├── pyproject.toml            # Project configuration
├── uv.lock                   # Dependency lock file
├── .pre-commit-config.yaml   # Code quality automation
└── README.md                 # This file
```

## Output Format

All processed data is saved as Excel files with standardized columns:

| Column | Description |
|--------|-------------|
| **Date** | Transaction date in YYYY-MM-DD format |
| **Description** | Transaction description with reference numbers |
| **Currency** | ARS or USD |
| **Amount** | Transaction amount (positive for charges, negative for payments) |
| **Payment Method** | Automatically detected bank/statement type |

## Example Outputs

### Macro VISA (PDF)

```
Date        Description                           Currency  Amount     Payment Method
2022-12-01  ABC123 COMPRA EN SUPERMERCADO        ARS       1,250.00   Macro VISA
2022-12-02  DEF456 RESTAURANT XYZ USD 45.00      USD       45.00      Macro VISA
2022-12-05  SU PAGO EN PESOS                     ARS       -2,000.00  Macro VISA
2022-12-10  IMPUESTO DE SELLOS                   ARS       15.75      Macro VISA
```

### BBVA Account (XLS)

```
Date        Description                           Currency  Amount     Payment Method
2025-06-09  TRANSFERENCIA RECIBIDA               ARS       50,000.00  BBVA Account
2025-06-08  DEBITO AUTOMATICO SERVICIOS          ARS       -8,500.00  BBVA Account
2025-06-07  ACREDITACION SUELDO                  ARS       120,000.00 BBVA Account
```

### Mercadopago (XLSX)

```
Date        Description                           Currency  Amount     Payment Method
2025-02-01  Pago recibido                        ARS       15,000.00  Mercadopago
2025-02-01  Retiro de dinero                     ARS       -5,000.00  Mercadopago
2025-02-02  Rendimiento de inversión             ARS       125.50     Mercadopago
```

## Development

### Quality Assurance

- **178 Tests**: Comprehensive test suite with 90% coverage
- **Pre-commit Hooks**: Automated quality checks (ruff, mypy, pytest)
- **Type Safety**: Modern Python 3.11+ type annotations
- **Code Quality**: Ruff linting and formatting (10-100x faster than flake8)
- **Warning-Free**: Clean development environment

### Running Tests

#### Using uv (Recommended)

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=term-missing --cov-config=.coveragerc

# Run specific test categories
uv run pytest tests/unit/ -v          # Unit tests only
uv run pytest tests/integration/ -v   # Integration tests only

# Run specific bank tests
uv run pytest tests/integration/test_macro_visa_processing.py -v
uv run pytest tests/integration/test_bbva_account_processing.py -v
uv run pytest tests/integration/test_mercadopago_processing.py -v
```

#### Using pip (Alternative)

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run tests
pytest -v
pytest --cov=. --cov-report=term-missing
```

### Code Quality Tools

```bash
# Linting and formatting
uv run ruff check .                    # Check code quality
uv run ruff check . --fix              # Auto-fix issues
uv run ruff format .                   # Format code

# Type checking
uv run mypy .                          # Static type checking

# Pre-commit hooks (runs automatically on commit)
pre-commit run --all-files             # Manual run
```

### Test Organization

#### Unit Tests (8 files)

- `test_convert_date.py` - Date conversion functionality
- `test_detect_payment_method.py` - Bank/statement type detection
- `test_error_handling.py` - Error handling and edge cases
- `test_european_number_format.py` - Number format parsing
- `test_extract_balance_from_pdf.py` - PDF balance extraction
- `test_print_processing_summary.py` - Output formatting
- `test_transaction_types.py` - Transaction type classification
- `test_validate_balance.py` - Balance validation logic

#### Integration Tests (8 files)

- `test_bbva_account_processing.py` - BBVA Account XLS workflow
- `test_bbva_mastercard_processing.py` - BBVA Mastercard PDF workflow
- `test_bbva_visa_processing.py` - BBVA VISA PDF workflow
- `test_bbva_visa_csv_processing.py` - BBVA VISA CSV workflow
- `test_macro_account_processing.py` - Macro Account XLS workflow
- `test_macro_visa_processing.py` - Macro VISA PDF workflow
- `test_macro_visa_csv_processing.py` - Macro VISA CSV workflow
- `test_mercadopago_processing.py` - Mercadopago XLSX workflow

## Roadmap

### Phase 1: System Enhancements (Next Priority)

- [ ] CLI interface with argument parsing
- [ ] Batch processing for multiple files
- [ ] Configuration system for bank patterns
- [ ] Enhanced error reporting and logging

### Phase 2: Additional Banks (Medium Priority)

- [ ] Santander bank support
- [ ] Additional Argentine financial institutions
- [ ] Generic framework for easier bank addition

### Phase 3: Output Enhancements (Lower Priority)

- [ ] Multiple output formats (CSV, JSON)
- [ ] Customizable Excel templates
- [ ] Enhanced data validation
- [ ] Database integration

### Phase 4: Advanced Features (Future)

- [ ] Transaction categorization
- [ ] Duplicate detection
- [ ] Built-in financial analysis
- [ ] Web interface

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-bank-support`)
3. Make your changes with tests
4. Ensure all quality checks pass (`pre-commit run --all-files`)
5. Commit your changes (`git commit -am 'Add support for Bank XYZ'`)
6. Push to the branch (`git push origin feature/new-bank-support`)
7. Create a Pull Request

### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install

# Run quality checks
uv run pytest --cov=. --cov-report=term-missing
uv run ruff check . --fix
uv run mypy .
```

## Troubleshooting

### Common Issues

1. **PDF parsing errors**: Ensure PDFs are text-based, not scanned images
2. **Missing dependencies**: Run `uv sync` or `pip install -e .`
3. **Date format issues**: Check that your files use supported date formats
4. **File detection issues**: Ensure filenames contain bank-specific keywords
5. **Number format errors**: Verify European format (1.234,56) in source files

### File Naming Requirements

For automatic detection, files should contain these keywords:

- **BBVA Account**: "BBVA" + "DETALLE" or "ACCOUNT"
- **Macro Account**: "MACRO" + "MOVIMIENTOS"
- **BBVA VISA CSV**: "BBVA" + "VISA"
- **Macro VISA CSV**: "MACRO" + "VISA"
- **Mercadopago**: "MERCADOPAGO"

### Support

For questions or issues:

1. Check the troubleshooting section above
2. Review the test files for examples
3. Open an issue on GitHub with:
   - File type and bank
   - Error message
   - Sample data (anonymized)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for the Argentine banking system
- Supports European number formatting standards
- Designed for personal finance management and accounting workflows
