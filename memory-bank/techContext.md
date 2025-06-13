# Tech Context - Financial Statement Processor

## Technology Stack

### Core Technologies

- **Python 3.11+**: Modern Python with latest features and performance improvements
- **pdfplumber**: PDF text extraction library, chosen for robust text extraction capabilities
- **pandas**: Data manipulation and analysis, essential for transaction data processing
- **openpyxl**: Excel file generation, provides compatibility with Microsoft Excel

### Dependency Management

- **uv**: Primary package manager (recommended for speed and reliability)
- **pip**: Fallback option for traditional Python environments
- **pyproject.toml**: Modern Python project configuration

## Key Library Choices

### PDF Processing: pdfplumber

- **Why Chosen**: Superior text extraction compared to PyPDF2/PyMuPDF
- **Benefits**: Handles complex PDF layouts, maintains text positioning
- **Limitations**: Requires text-based PDFs (not scanned images)
- **Alternative Considered**: PyPDF2 (less reliable for complex layouts)

### Data Processing: pandas

- **Why Chosen**: Industry standard for data manipulation
- **Benefits**: DataFrame structure perfect for transaction data
- **Features Used**: Date parsing, data sorting, Excel export
- **Performance**: Efficient for typical statement sizes (hundreds of transactions)

### Excel Output: openpyxl

- **Why Chosen**: Native Excel format support (.xlsx)
- **Benefits**: Maintains formatting, compatible with Excel/LibreOffice
- **Alternative**: xlsxwriter (write-only, but faster for large datasets)

## Development Environment

### Project Structure

```
financial-statement-processor/
├── parse_visa_statement.py    # Main processor
├── test_parse_visa_statement.py  # Comprehensive test suite
├── pyproject.toml             # Dependencies and metadata
├── uv.lock                    # Dependency lock file
├── input/                     # PDF files to process
├── output/                    # Generated Excel files
├── expected_output/           # Reference files for testing
└── memory-bank/               # Project documentation
```

### Setup Requirements

- **Python Version**: 3.11+ (uses modern syntax and performance improvements)
- **Memory**: Minimal requirements, suitable for typical desktop environments
- **Storage**: PDF and Excel files, no significant storage needs
- **Platform**: Cross-platform (Windows, macOS, Linux)

## Technical Constraints

### PDF Processing Limitations

- **Text-Based Only**: Cannot process scanned/image-based PDFs
- **Layout Dependency**: Relies on consistent bank statement formatting
- **Language Specific**: Designed for Spanish/Argentine banking terminology

### Number Format Complexity

- **European Format**: Must handle 1.234,56 notation correctly
- **Multiple Separators**: Distinguish between thousands and decimal separators
- **Currency Mixing**: ARS and USD on same statement with different formats

### Date Format Challenges

- **Two-Digit Years**: DD.MM.YY format requires century inference
- **Cutoff Logic**: Years < 50 = 20XX, years >= 50 = 19XX
- **Future Proofing**: Will need adjustment in 2050

## Performance Characteristics

### Processing Speed

- **Small Statements**: < 1 second for typical monthly statements
- **Large Statements**: Scales linearly with transaction count
- **Memory Usage**: Low memory footprint, streams data processing

### Scalability Considerations

- **Single File**: Current design optimized for individual statement processing
- **Batch Processing**: Ready for extension to multiple file processing
- **Large Files**: Pandas handles thousands of transactions efficiently

## Quality Assurance Tools

### Testing Framework

- **pytest**: Industry standard testing framework
- **pytest-cov**: Test coverage measurement and enforcement using coverage.py
- **Integration Tests**: Process real PDF files, compare with expected output
- **Unit Tests**: Validate individual functions (date conversion, payment detection)
- **Coverage Enforcement**: 87% coverage with 83 tests, configurable thresholds (80%, 90%, 100%)
- **Specialized Coverage Tests**: Targeted tests for error handling and edge cases
- **Bank-Specific Tests**: Dedicated test files for MACRO VISA, BBVA VISA, and BBVA Mastercard

### Validation Approach

- **Reference Files**: `expected_output/` contains known-good results
- **Data Integrity**: Validates transaction counts, amounts, currency distribution
- **Regression Testing**: Ensures changes don't break existing functionality

## Development Workflow

### Package Management with uv

```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Development dependencies
uv add --dev pytest
```

### Traditional pip Workflow

```bash
# Virtual environment
python -m venv .venv
source .venv/bin/activate

# Install project
pip install -e .
```

### Testing Workflow

#### Using uv (Recommended)

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest test_parse_visa_statement.py

# Verbose output
uv run pytest -v

# Run main processor
uv run python parse_visa_statement.py
```

#### Using pip (Alternative)

```bash
# Run all tests
pytest

# Run specific test file
pytest test_parse_visa_statement.py

# Verbose output
pytest -v
```

## Configuration Management

### Project Configuration (pyproject.toml)

- **Metadata**: Project name, version, description
- **Dependencies**: Core and development dependencies
- **Python Version**: Minimum Python version requirement
- **Entry Points**: Future CLI command configuration

### File Paths

- **Hardcoded Paths**: Currently uses relative paths for input/output
- **Future Enhancement**: Configuration file for custom paths
- **Cross-Platform**: Uses os.path for platform compatibility

## Future Technical Considerations

### Modularity Improvements

- **Bank-Specific Modules**: Separate parsing logic for each bank
- **Plugin Architecture**: Dynamic loading of bank-specific processors
- **Configuration System**: YAML/JSON configuration for bank patterns

### Performance Optimizations

- **Compiled Regex**: Pre-compile frequently used patterns
- **Streaming Processing**: For very large statements
- **Caching**: Cache PDF parsing results for repeated processing

### Output Format Extensions

- **Multiple Formats**: CSV, JSON, XML output options
- **Template System**: Customizable Excel templates
- **Database Integration**: Direct database output for enterprise use

### Error Handling Enhancements

- **Logging System**: Structured logging for debugging
- **Error Recovery**: Partial processing with detailed error reports
- **Validation Rules**: Configurable validation and error detection

## Security Considerations

### File Handling

- **Input Validation**: Ensure input files are valid PDFs
- **Path Traversal**: Prevent directory traversal attacks
- **Temporary Files**: Secure handling of temporary data

### Data Privacy

- **Local Processing**: All processing happens locally, no data transmission
- **No Network Access**: No external API calls or data sharing
- **Secure Deletion**: Clean up temporary files after processing
