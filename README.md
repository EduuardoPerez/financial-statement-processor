# Financial Statement Processor

A Python tool for processing financial statements from various banks into structured Excel format. Currently supports Macro VISA credit card statements with plans to expand to other financial institutions.

## Features

- **PDF to Excel Conversion**: Extracts transaction data from PDF statements and converts to structured Excel format
- **Multi-Currency Support**: Handles both ARS (Argentine Peso) and USD transactions
- **Smart Parsing**: Recognizes various transaction types including:
  - Regular purchases
  - Tax entries (IMPUESTO, IIBB, IVA, etc.)
  - Payments (SU PAGO EN PESOS)
  - Adjustments and discounts
- **European Number Format**: Properly handles European-style number formatting (1.234,56)
- **Date Conversion**: Converts DD.MM.YY format to standard YYYY-MM-DD

## Currently Supported

- **Macro VISA**: Credit card statements in PDF format

## Requirements

- Python >= 3.11
- Dependencies managed via `uv` (recommended) or `pip`

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/EduuardoPerez/financial-statement-processor.git
cd financial-statement-processor

# Install dependencies
uv sync
```

### Using pip

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

### Basic Usage

#### Using uv (Recommended)

```bash
# Run the processor with uv
uv run python parse_visa_statement.py
```

#### Using pip (Alternative)

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the processor
python parse_visa_statement.py
```

### Custom Input/Output Paths

```python
from parse_visa_statement import parse_visa_pdf

# Process a specific PDF file
df = parse_visa_pdf(
    pdf_path="path/to/your/statement.pdf",
    output_path="path/to/output.xlsx"
)
```

## Project Structure

```
financial-statement-processor/
├── parse_visa_statement.py    # Main processing script
├── hello.py                   # Simple test script
├── input/                     # Place PDF statements here
│   └── MACRO-VISA-resumen_cuenta_visa_Dec_2022.pdf
├── output/                    # Generated Excel files
│   └── MACRO-VISA-transactions.xlsx
├── expected_output/           # Reference output for testing
│   ├── MACRO-VISA-transactions.csv
│   └── MACRO-VISA-transactions.xlsx
├── pyproject.toml            # Project configuration
├── uv.lock                   # Dependency lock file
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Output Format

The processed data is saved as an Excel file with the following columns:

- **Date**: Transaction date in YYYY-MM-DD format
- **Description**: Transaction description including reference numbers
- **Currency**: ARS or USD
- **Amount**: Transaction amount (positive for charges, negative for payments)
- **Payment Method**: Always "Macro VISA" for current implementation

## Example Output

```
Date        Description                           Currency  Amount    Payment Method
2022-12-01  ABC123 COMPRA EN SUPERMERCADO        ARS       1250.00   Macro VISA
2022-12-02  DEF456 RESTAURANT XYZ                USD       45.00     Macro VISA
2022-12-05  SU PAGO EN PESOS                     ARS       -2000.00  Macro VISA
```

## Development

### Running Tests

#### Using uv (Recommended)

```bash
# Run the main processor to generate output
uv run python parse_visa_statement.py

# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest test_parse_visa_statement.py

# Run specific test with detailed output
uv run pytest test_parse_visa_statement.py::TestParseVisaStatement::test_parse_visa_pdf_integration -v
```

#### Using pip (Alternative)

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the main processor
python parse_visa_statement.py

# Run tests
pytest -v
```

**Note**: Check that `output/MACRO-VISA-transactions.xlsx` matches the expected format in `expected_output/`

### Adding Support for New Banks

To add support for additional financial institutions:

1. Create a new parser module following the pattern of `parse_visa_statement.py`
2. Implement the specific parsing logic for the new format
3. Update the main script to handle multiple input types
4. Add tests and expected output examples

## Future Roadmap

- [ ] Support for additional banks (Santander, BBVA, etc.)
- [ ] Command-line interface with argument parsing
- [ ] Batch processing for multiple files
- [ ] Configuration file support
- [ ] Additional output formats (CSV, JSON)
- [ ] Transaction categorization
- [ ] Duplicate detection and handling

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-bank-support`)
3. Commit your changes (`git commit -am 'Add support for Bank XYZ'`)
4. Push to the branch (`git push origin feature/new-bank-support`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

1. **PDF parsing errors**: Ensure the PDF is text-based, not scanned images
2. **Missing dependencies**: Run `uv sync` or `pip install -e .` to install required packages
3. **Date format issues**: Check that your PDF uses DD.MM.YY format

### Support

For questions or issues, please open an issue on GitHub.
