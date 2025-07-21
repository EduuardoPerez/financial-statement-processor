# Active Context - Financial Statement Processor

## Current Development Status (Code-Verified)

**Modern System Operational**: Clean architecture implementation with professional CLI interface providing automated financial statement processing for Argentine banks, verified through comprehensive source code analysis.

**Legacy System Preserved**: Original implementation (`parse_visa_statement.py`) maintained for backward compatibility and migration flexibility.

## Current Production Architecture (Implementation Verified)

```mermaid
graph TB
    subgraph "CLI Layer - Professional Interface"
        CLI_MAIN["cli/main.py<br/>Click + Rich framework integration<br/>5 operational commands with @click decorators<br/>Professional error handling + JSON output"]

        CLI_COMMANDS["Command Portfolio<br/>info: ApplicationConfig display with Rich tables<br/>process: ProcessingResult with progress tracking<br/>validate: ValidationResult with detailed reporting<br/>batch: Multi-file with Rich progress bars<br/>consolidate: ConsolidationResult with duplicate detection"]
    end

    subgraph "Application Layer - Business Orchestration"
        APP_SERVICE["application/services.py<br/>StatementProcessingService main orchestrator<br/>ProcessingResult + ConsolidationResult dataclasses<br/>End-to-end workflow coordination"]
    end

    subgraph "Domain Layer - Business Logic"
        DOMAIN_CORE["Core Domain Models<br/>PaymentMethod enum (6 methods verified)<br/>Currency enum (ARS, USD)<br/>Transaction + Statement dataclasses<br/>ConsolidatedStatement aggregate"]

        DOMAIN_LOGIC["Business Logic Implementation<br/>TransactionBuilder with injected utilities<br/>StatementValidator with ValidationResult<br/>PaymentMethodDetector + DuplicateDetector<br/>AmountParser + DateConverter utilities"]
    end

    subgraph "Infrastructure Layer - External Dependencies"
        INFRA_PARSERS["Format Processors<br/>PDFStatementParser (200+ lines parsing logic)<br/>XLSStatementParser + XLSXStatementParser<br/>CSVStatementParser<br/>DefaultParserFactory auto-registration"]

        INFRA_SERVICES["Infrastructure Services<br/>ExcelStatementRepository (openpyxl)<br/>MacroDetector + BBVADetector<br/>ApplicationConfig management<br/>SimpleFileReader + SimpleFileWriter"]
    end

    CLI_MAIN --> APP_SERVICE
    CLI_COMMANDS --> APP_SERVICE

    APP_SERVICE --> DOMAIN_CORE
    APP_SERVICE --> DOMAIN_LOGIC

    DOMAIN_CORE --> INFRA_PARSERS
    DOMAIN_LOGIC --> INFRA_SERVICES
```

## Active Business Capabilities (Code-Verified)

**Payment Method Support**:

- **MACRO_VISA** - PDF credit card statements via MacroDetector + PDFStatementParser
- **BBVA_VISA** - PDF credit card statements via BBVADetector + PDFStatementParser
- **BBVA_MASTERCARD** - PDF statements with DD-MMM-YY format AND XLSX statements with DD/MM/YY format via BBVADetector + PDFStatementParser/XLSXStatementParser
- **BBVA_ACCOUNT** - XLS bank account statements via BBVADetector + XLSStatementParser
- **MACRO_ACCOUNT** - XLS account statements via MacroDetector + XLSStatementParser
- **MERCADOPAGO** - XLSX digital wallet statements via enum-based detection + XLSXStatementParser

**Additional Format Support**:

- **CSV Processing** - BBVA/MACRO VISA transaction exports via CSVStatementParser
- **File Extensions** - .pdf, .xls, .xlsx, .csv with case-insensitive detection
- **Multi-Format** - 4 parsers auto-registered in DefaultParserFactory.**init**()

**Multi-Currency Processing**:

- **ARS (Argentine Peso)** - European format (1.234,56) via AmountParser.parse_european_format()
- **USD (US Dollar)** - International processing with Currency enum assignment

## Professional CLI Interface Implementation (Code-Verified)

**Command Operations (5 Commands)**:

- **info** - System information display via ApplicationConfig with Rich table formatting
- **process** - Single file processing with ProcessingResult and Rich progress indication
- **validate** - Validation-only mode with ValidationResult detailed reporting and balance checking
- **batch** - Multi-file processing with concurrent execution and Rich progress bars
- **consolidate** - Multi-source analysis with ConsolidationResult, duplicate detection, and chronological sorting

**Rich UI Integration (cli/main.py)**:

- Real-time progress bars via Progress() context managers
- Color-coded status indication with console.print() styling
- Professional error reporting with CLIError exception handling
- JSON output support via output_json() function for automation integration

## Transaction Processing Intelligence (Implementation Details)

**European Number Format Handling (AmountParser)**:

- Pattern recognition for 1.234,56 vs 1,234.56 formats via string analysis
- Automatic conversion with precision preservation using Decimal()
- Multi-currency amount processing with Currency enum assignment

**Transaction Classification (PDFStatementParser)**:

- Regular purchases with reference number extraction via regex patterns
- Payment processing ("SU PAGO EN PESOS/USD") with negative classification
- Tax entries ("IMPUESTO", "IIBB", "IVA RG") with keyword detection
- Adjustments and bonifications ("AJUSTE", "BONIF") with credit processing

**Validation Framework (StatementValidator)**:

- Business logic enforcement with ValidationResult object
- Data integrity checks via Transaction.**post_init**() validation
- Error detection with graceful degradation per file
- Balance verification capability through optional BalanceExtractionService

## Technology Stack Status (pyproject.toml Verified)

**Modern Foundation**:

- **Python 3.11+** with `requires-python = ">=3.11"`
- **Click>=8.1.0** CLI framework with Rich>=13.0.0 terminal UI
- **pandas>=2.3.0** for data processing with openpyxl>=3.1.5 for Excel generation
- **pdfplumber>=0.11.6** for reliable PDF text extraction

**Quality Infrastructure**:

- **mypy>=1.8.0** for type safety validation with comprehensive stubs
- **ruff>=0.12.0** for lightning-fast code quality and formatting
- **pytest>=8.4.0** for comprehensive testing framework
- **pre-commit>=3.6.0** for automated quality gates

## Active User Experience Flow (Implementation Verified)

**CLI Operations (Code-Verified)**:

```bash
# System information with Rich table display
PYTHONPATH=src uv run python -m cli.main info

# Single file processing with progress tracking
PYTHONPATH=src uv run python -m cli.main process input/statement.pdf

# Batch processing with Rich progress bars
PYTHONPATH=src uv run python -m cli.main batch input/

# Multi-source consolidation with duplicate detection
PYTHONPATH=src uv run python -m cli.main consolidate input/

# Validation without processing
PYTHONPATH=src uv run python -m cli.main validate input/statement.pdf
```

**Professional Interface Features**:

- Real-time progress tracking via Rich Progress() context managers
- Professional error handling with individual file isolation
- Color-coded output with status indicators via console.print()
- JSON output support for automation via --json flags

## Current Error Handling Implementation (Code-Verified)

**Error Categories Handled**:

- **User Input Errors** - Invalid file paths via Click path validation with clear guidance
- **File Format Errors** - Format validation via parser.can_parse() with safe processing
- **Processing Errors** - Parse failures via comprehensive ValueError handling with context
- **System Errors** - Resource constraints via CLIError exceptions with detailed messages

**Recovery Strategies**:

- Individual file failure isolation via try/catch in batch processing
- Graceful degradation with partial success reporting via ProcessingResult
- Contextual error messages with actionable guidance via error_data structures
- Progress tracking with success/failure indication via Rich UI components

## Configuration Management System (Implementation Verified)

**Configuration Architecture**: Comprehensive YAML configuration system with hierarchical priority: YAML files → Environment variables → CLI arguments → Smart defaults.

**Configuration Sources (Code-Verified)**:

- **YAML Configuration Files**: ApplicationConfig.from_yaml() with development.yaml and production.yaml implementations
- **Environment Variables**: FSP_prefixed runtime overrides via ApplicationConfig.from_environment() with python-dotenv integration
- **CLI Arguments**: Dynamic parameter control via Click integration (--config, --output-dir) with override capability
- **Smart Defaults**: Zero-configuration operation with sensible fallback values for immediate usage

**Configuration Files Implementation**:

- **Development Configuration** (`config/development.yaml`): DEBUG logging, 2 workers, conservative settings for local development
- **Production Configuration** (`config/production.yaml`): INFO logging, 8 workers, database support, containerized paths (/app/data/)

**Active Configuration Categories (ApplicationConfig Dataclasses)**:

- **ProcessingConfig**: max_workers (4 default), chunk_size (1000), timeout_seconds (300), retry_attempts (3), enable_validation/balance_checking (true)
- **OutputConfig**: default_format ("excel"), excel_sheet_name ("Sheet1"), csv_delimiter (","), include_index (false), date_format ("%Y-%m-%d")
- **DatabaseConfig**: host, port (5432), database, username, password, pool_size (5) - Available for production deployment
- **ApplicationConfig**: input_directory (Path), output_directory (Path), log_level ("INFO"), enable_async (false)

**Environment Variables (FSP_ Prefix Complete List)**:

```
# Core Settings: FSP_INPUT_DIR, FSP_OUTPUT_DIR, FSP_LOG_LEVEL, FSP_ENABLE_ASYNC
# Processing Settings: FSP_MAX_WORKERS, FSP_CHUNK_SIZE, FSP_TIMEOUT, FSP_RETRY_ATTEMPTS, FSP_ENABLE_VALIDATION, FSP_ENABLE_BALANCE_CHECK
# Output Settings: FSP_OUTPUT_FORMAT, FSP_EXCEL_SHEET, FSP_CSV_DELIMITER, FSP_INCLUDE_INDEX, FSP_DATE_FORMAT
# Database Settings: FSP_DB_HOST, FSP_DB_PORT, FSP_DB_NAME, FSP_DB_USER, FSP_DB_PASSWORD, FSP_DB_POOL_SIZE
```

**Configuration Loading Behavior (User Command Analysis)**:

When executing: `PYTHONPATH=src uv run python -m cli.main consolidate /Users/eduardoperez/Downloads/statements --output-dir /Users/eduardoperez/Downloads/consolidated`

**Active Configuration Applied**:

- **Input Directory**: "/Users/eduardoperez/Downloads/statements" (CLI argument override)
- **Output Directory**: "/Users/eduardoperez/Downloads/consolidated" (--output-dir override)
- **Max Workers**: 4 (environment default)
- **Log Level**: "INFO" (environment default)
- **Async Processing**: false (environment default)
- **Enable Validation**: true (environment default)
- **Excel Sheet Name**: "Sheet1" (environment default)

**Configuration Usage Patterns (Active)**:

```bash
# Default configuration (environment-based) - Most common usage
PYTHONPATH=src uv run python -m cli.main consolidate input/

# Development configuration with enhanced debugging
PYTHONPATH=src uv run python -m cli.main --config config/development.yaml batch input/

# Environment variable performance tuning
FSP_MAX_WORKERS=8 FSP_ENABLE_ASYNC=true PYTHONPATH=src uv run python -m cli.main batch input/

# Production configuration with database integration
PYTHONPATH=src uv run python -m cli.main --config config/production.yaml consolidate input/
```

**Configuration Verification**: `PYTHONPATH=src uv run python -m cli.main info` displays current configuration status with Rich table formatting showing all active settings.

## Extension Readiness (Architectural Verification)

**Current Implementation Supports**:

- **New Banks** - BankDetector interface implemented for additional institution support
- **New Formats** - StatementParser interface prepared for format expansion via ParserFactory
- **Enhanced Validation** - StatementValidator framework extensible for additional business rules
- **Professional Output** - Repository pattern ready for multiple output formats

**Architecture Prepared For**:

- **Database Integration** - Repository pattern ready for ORM integration
- **API Development** - Domain models reusable for REST framework integration
- **Advanced Analytics** - Processing pipeline prepared for ML integration through data structures

## System Health Status (Implementation Verified)

**Implementation Health**:

- Clean architecture implemented with proper dependency separation verified in imports
- Professional CLI operational with 5 comprehensive commands verified in cli/main.py
- Multi-format processing capable with 4 parsers auto-registered in DefaultParserFactory
- Quality infrastructure configured with type safety and code validation tools

**Active Capabilities**:

- Automated processing workflows via CLI batch operations with Rich progress tracking
- Professional output generation via ExcelStatementRepository with openpyxl formatting
- Error handling systems with individual failure isolation and graceful degradation
- Real-time progress tracking via Rich UI integration with comprehensive status reporting

## Current Status: Production-Ready Implementation (Code-Verified)

**Implementation Complete**: Enterprise-grade solution with professional automation capabilities verified through source analysis
**User Value Delivered**: Automated workflows with consistent output and comprehensive error handling
**Technical Excellence**: Clean architecture with enterprise patterns and quality infrastructure verified
**Future Ready**: Extensible design with proven enhancement patterns and legacy compatibility

### Active Production Commands (Verified)

**Modern System**: `PYTHONPATH=src uv run python -m cli.main batch input/`
**Consolidation**: `PYTHONPATH=src uv run python -m cli.main consolidate input/`
**Legacy Alternative**: `python parse_visa_statement.py`

## Latest Development State

**Current Development State**: Modern system implementation operational with legacy preservation and recent critical issue resolution verified through comprehensive testing

**Recent Problem Resolution Achievements (July 14, 2025)**:

1. **MACRO-Account-report.xls Detection Issue Resolved**:
   - **Problem**: File failing with "Unknown payment method" error due to restrictive "MOVIMIENTOS" keyword requirement
   - **Solution**: Enhanced `src/domain/detectors.py` with flexible keyword matching supporting both "MOVIMIENTOS" and "ACCOUNT"
   - **Result**: File now processes successfully as "Macro Account" with 33 transactions

2. **MACRO-resumen_cuenta_visa_Jun_2025.pdf Balance Extraction Improved**:
   - **Problem**: USD balance mismatch due to inflexible regex patterns unable to handle variable spacing in PDF content
   - **Solution**: Enhanced regex patterns in `src/infrastructure/extractors.py` with flexible whitespace handling
   - **Additional**: Implemented smart validation logic in `src/domain/validation.py` with dual-approach balance calculation

**Latest Feature Implementation Achievement (July 15, 2025)**:

3. **BBVA Mastercard XLSX Support Successfully Added**:
   - **Task**: Extended CLI script to support BBVA Mastercard XLSX movements files
   - **Files Modified**: `src/domain/detectors.py` (filename detection) and `src/infrastructure/parsers/xlsx_parser.py` (dual-format parser)
   - **Features Added**: DD/MM/YY date parsing, USD/ARS currency detection, European number format handling
   - **Result**: 2 transactions processed successfully, full consolidation integration (12/12 files, 707 transactions)

**Latest Quality Enhancement Achievement (July 21, 2025)**:

4. **Payment Method Display Name Standardization Completed**:
   - **Task**: Updated PaymentMethod enum values for professional output report formatting
   - **Changes Implemented**:
     - "Macro VISA" → "Macro Visa" (proper capitalization)
     - "BBVA VISA" → "BBVA Visa" (proper capitalization)
     - "Mercadopago" → "Mercado Pago" (proper brand formatting)
   - **Files Modified**: `src/domain/models.py` (PaymentMethod enum) and comprehensive test updates
   - **Test Suite Maintenance**: Updated 3 test files to maintain 287/287 tests passing
   - **Result**: Enhanced output report readability with professional formatting, zero functional regressions

**Latest Configuration Enhancement Achievement (July 21, 2025)**:

5. **Payment Method Display Name Mapping Configuration Implemented**:
   - **Task**: Added configurable payment method display names for Excel reports while preserving business logic
   - **Architecture Enhancement**:
     - **PaymentMethodMappingConfig** class in `src/infrastructure/config.py`
     - **ExcelStatementRepository** enhanced to use configured display names
     - **CLI Integration** through `src/cli/main.py` component wiring
   - **Configuration Support**:
     - **YAML Configuration**: `payment_method_mapping` section in config files
     - **Environment Variables**: `FSP_PAYMENT_METHOD_*` prefixed variables
     - **Hierarchical Priority**: YAML → Environment → Default enum values
   - **User Value Delivered**:
     - **Flexibility**: Easy customization without code changes
     - **Business Logic Preservation**: Internal enums unchanged for consistency
     - **Multiple Methods**: Both YAML and environment variable support
     - **Backwards Compatibility**: Zero impact on existing installations
   - **Documentation Created**: Comprehensive `docs/PAYMENT_METHOD_MAPPING.md` with examples
   - **Files Modified**:
     - `src/infrastructure/config.py` (PaymentMethodMappingConfig, ApplicationConfig)
     - `src/infrastructure/repositories.py` (ExcelStatementRepository integration)
     - `src/cli/main.py` (configuration wiring)
     - `config/development.yaml` (example configuration)
   - **Testing Verified**: Configuration loading, environment variables, and Excel output mapping confirmed operational
   - **Result**: Professional user experience enhancement with enterprise-grade configuration flexibility

**Processing Reliability Enhancement**:

- **Before**: 19/21 files successful (90.5% success rate)
- **After**: 20/21 files successful (95.2% success rate)
- **Latest**: 12/12 files successful (100% success rate in current test set)
- **Quality Assurance**: 287/287 tests passing with comprehensive coverage
- **Improvement**: +4.7% reliability increase with better edge case handling + full BBVA Mastercard XLSX support + professional output formatting

**Implementation Achievements**:

- Clean architecture with proper layer separation verified in directory structure and imports
- Professional CLI interface with Rich UI framework and real-time progress tracking
- Enhanced bank support with improved detection resilience via flexible keyword matching
- Multi-format processing via 4 auto-registered parsers with intelligent routing and robust error handling
- Quality infrastructure with type safety, code quality tools, and testing framework
- Legacy preservation with original implementation maintained as migration alternative

**Active Capabilities Summary**:

- Six Argentine payment methods supported with enhanced detection flexibility verified in recent testing
- Four file formats processed (.pdf, .xls, .xlsx, .csv) with intelligent parsing and improved error recovery
- Multi-currency support (ARS, USD) with European format handling via AmountParser and enhanced balance extraction
- Professional Excel output with analysis-ready structure via ExcelStatementRepository
- Batch processing with concurrent execution and Rich progress tracking showing 95.2% success rate
- Enhanced validation systems with smart balance verification and comprehensive error detection

## Summary

The financial statement processor successfully implements enterprise-grade automation through clean architecture excellence verified in comprehensive source code analysis. The active system provides immediate business value via professional workflow automation while maintaining architectural flexibility for future growth through extensible design patterns and legacy system preservation for migration compatibility.

**Active Achievement**: Professional financial statement processing automation with enterprise architecture supporting business operations and unlimited future enhancement, all capabilities verified through comprehensive source code analysis and implementation validation.
