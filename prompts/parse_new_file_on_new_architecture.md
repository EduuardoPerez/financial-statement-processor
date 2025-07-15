# Reusable Prompt Template for Adding New File Format Support

Based on the successful BBVA Mastercard XLSX implementation, here's a comprehensive prompt template you can use to add support for new file formats:

---

## 🛠️ Task: Extend CLI Script to Support New File Format

### 🎯 Objective

Update the existing CLI script following the current clean architecture to support **[NEW_FILE_FORMAT]** files and generate valid `.xlsx` output files integrated into the consolidated report.

### 📋 File Information

**Input File**: `input/[SPECIFIC_FILENAME]`
**File Format**: [FORMAT_TYPE] (e.g., .xlsx, .csv, .xls, .pdf)
**Bank/Institution**: [BANK_NAME]
**Payment Method**: [PAYMENT_METHOD] (e.g., "Bank Credit Card", "Account", etc.)

### 📊 File Structure

The input file contains the following structure:

```plain
[DESCRIBE_FILE_STRUCTURE]
Example:
- Headers: "Date", "Description", "Amount", "Currency"
- Row 1: 2025-01-15, Purchase at Store, 100.00, USD
- Row 2: 2025-01-16, Online Payment, 50.00, EUR
```

### 🎯 Expected Output Structure

The generated output must match this structure:

| Date       | Description  | Currency | Amount    | Payment Method     |
|------------|--------------|----------|-----------|--------------------|
| 2025-01-15 | Purchase at Store | USD | 100.00 | [PAYMENT_METHOD] |
| 2025-01-16 | Online Payment    | EUR | 50.00  | [PAYMENT_METHOD] |

### 🔧 Technical Requirements

**Date Format Conversion**:

- Input format: [INPUT_DATE_FORMAT] (e.g., DD/MM/YY, YYYY-MM-DD, etc.)
- Output format: YYYY-MM-DD

**Currency Handling**:

- Expected currencies: [LIST_CURRENCIES] (e.g., USD, EUR, ARS)
- Currency detection method: [DETECTION_METHOD] (e.g., prefix in amount, separate column, etc.)

**Amount Format**:

- Input format: [INPUT_AMOUNT_FORMAT] (e.g., European "1.234,56", US "1,234.56")
- Special handling required: [YES/NO]

**Special Parsing Requirements**:

- [LIST_ANY_SPECIAL_REQUIREMENTS]
- Examples: Header row handling, empty row skipping, multi-line descriptions, etc.

### ✅ Current System Behavior

The script currently processes multiple file formats. This functionality **must remain working as it is**.

### ➕ Implementation Requirements

1. **Update PaymentMethodDetector** (`src/domain/detectors.py`):
   - Add filename detection for [BANK_NAME] [PAYMENT_METHOD] files
   - Pattern matching for: [FILENAME_PATTERNS]

2. **Extend/Create Parser** (`src/infrastructure/parsers/[parser_file].py`):
   - Add support for [FILE_FORMAT] processing
   - Handle [SPECIFIC_PARSING_REQUIREMENTS]
   - Implement date conversion: [DATE_CONVERSION_DETAILS]
   - Implement currency detection: [CURRENCY_DETECTION_DETAILS]
   - Handle amount parsing: [AMOUNT_PARSING_DETAILS]

3. **Architecture Compliance**:
   - Follow clean architecture patterns
   - Use Strategy Pattern for parser implementation
   - Integrate with existing Factory Pattern
   - Maintain Builder Pattern for transaction creation

### 🧪 Testing Requirements

Create comprehensive tests covering:

1. **Unit Tests** (`tests/unit/parsers/test_[format]_parser.py`):
   - File detection (`can_parse()` method)
   - Date conversion accuracy
   - Currency detection accuracy
   - Amount parsing accuracy
   - Error handling (invalid files, missing columns, etc.)

2. **Integration Tests** (`tests/integration/test_[bank]_[method]_[format]_processing.py`):
   - End-to-end processing with real file
   - Data integrity validation
   - Consolidation integration
   - Performance testing

3. **Test Data Setup**:
   - Copy test file to `tests/test_data/input/`
   - Generate expected output in `tests/test_data/expected_output/`

### 🔍 Validation Criteria

- ✅ Individual file processing works correctly
- ✅ Consolidation integration maintains compatibility
- ✅ Output format matches expected structure
- ✅ All transactions processed accurately
- ✅ Payment method detection works for filename variations
- ✅ Date format conversion is accurate
- ✅ Currency detection handles all expected currencies
- ✅ Amount parsing handles format correctly
- ✅ Clean architecture patterns maintained
- ✅ Comprehensive test coverage (unit + integration)
- ✅ All existing functionality remains intact

### 📝 Success Metrics

- Processing completes without errors
- Output file contains correct number of transactions
- All amounts, dates, and currencies are accurately parsed
- File integrates into consolidated report
- All tests pass (unit + integration)

---

## 🔧 Usage Instructions

1. Replace all `[PLACEHOLDER]` values with your specific file details
2. Provide the actual input file in the `input/` directory
3. Include sample data showing the file structure
4. Specify any special parsing requirements
5. Test with the actual file to ensure requirements are accurate

This template ensures you get consistent, high-quality implementation following the established clean architecture patterns while maintaining full test coverage.
