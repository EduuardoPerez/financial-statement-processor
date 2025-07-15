# System Patterns - Financial Statement Processor

## Clean Architecture Implementation (Code-Verified)

```mermaid
graph TB
    subgraph "CLI Layer - User Interface"
        CLI_INTERFACE["cli/main.py<br/>Click framework with Rich UI<br/>5 commands with @click decorators<br/>Professional error handling + JSON output"]

        CLI_OPERATIONS["CLI Operations<br/>info: ApplicationConfig display<br/>process: Single file ProcessingResult<br/>validate: ValidationResult reporting<br/>batch: Multi-file with progress<br/>consolidate: ConsolidationResult"]
    end

    subgraph "Application Layer - Business Orchestration"
        APP_SERVICES["application/services.py<br/>StatementProcessingService<br/>ProcessingResult + ConsolidationResult dataclasses<br/>End-to-end workflow coordination"]

        SERVICE_COMPOSITION["Service Composition<br/>ParserFactory + Repository + Validator<br/>FilenameGenerator + BalanceExtractionService<br/>Dependency injection via constructor"]
    end

    subgraph "Domain Layer - Core Business Logic"
        DOMAIN_MODELS["domain/models.py<br/>PaymentMethod enum (6 values)<br/>Currency enum (ARS, USD)<br/>Transaction + Statement dataclasses<br/>ConsolidatedStatement aggregate"]

        DOMAIN_SERVICES["domain/builders.py + detectors.py + validation.py<br/>TransactionBuilder with injected utilities<br/>PaymentMethodDetector interface<br/>StatementValidator + DuplicateDetector"]

        PATTERNS["Domain Patterns<br/>Builder: TransactionBuilder + StatementBuilder<br/>Factory: ParserFactory interface<br/>Strategy: StatementParser interface"]
    end

    subgraph "Infrastructure Layer - External Dependencies"
        FORMAT_PROCESSORS["infrastructure/parsers/<br/>PDFStatementParser (pdfplumber)<br/>XLS/XLSX StatementParser (pandas)<br/>CSVStatementParser (pandas)<br/>Strategy implementations"]

        DATA_ACCESS["infrastructure/<br/>ExcelStatementRepository<br/>MacroDetector + BBVADetector<br/>DefaultParserFactory<br/>Configuration management"]
    end

    CLI_INTERFACE --> APP_SERVICES
    CLI_OPERATIONS --> SERVICE_COMPOSITION

    APP_SERVICES --> DOMAIN_MODELS
    SERVICE_COMPOSITION --> DOMAIN_SERVICES

    DOMAIN_MODELS --> FORMAT_PROCESSORS
    DOMAIN_SERVICES --> DATA_ACCESS
    PATTERNS --> FORMAT_PROCESSORS
```

## Enterprise Design Patterns Implementation (Code-Verified)

### Strategy Pattern - Format Processing

**Implementation**: Four concrete parsers in infrastructure/parsers/ with StatementParser interface

```mermaid
graph TB
    PARSER_INTERFACE["StatementParser Interface<br/>domain/services.py<br/>parse(), can_parse(), get_supported_extensions()"]

    PDF_STRATEGY["PDFStatementParser<br/>infrastructure/parsers/pdf_parser.py<br/>pdfplumber integration<br/>200+ lines of transaction parsing"]

    XLS_STRATEGY["XLSStatementParser<br/>infrastructure/parsers/xls_parser.py<br/>pandas + xlrd integration<br/>TransactionBuilder.build_from_xls_data()"]

    CSV_STRATEGY["CSVStatementParser<br/>infrastructure/parsers/csv_parser.py<br/>pandas delimiter detection<br/>TransactionBuilder.build_from_csv_data()"]

    XLSX_STRATEGY["XLSXStatementParser<br/>infrastructure/parsers/xlsx_parser.py<br/>pandas + openpyxl integration<br/>TransactionBuilder.build_from_xls_data()"]

    PARSER_INTERFACE --> PDF_STRATEGY
    PARSER_INTERFACE --> XLS_STRATEGY
    PARSER_INTERFACE --> CSV_STRATEGY
    PARSER_INTERFACE --> XLSX_STRATEGY
```

**Code Verification**:

- **Interface**: `StatementParser` abstract base class in domain/services.py
- **Concrete Implementations**: 4 parsers auto-registered in DefaultParserFactory.**init**()
- **Extension Detection**: `.pdf`, `.xls`, `.xlsx`, `.csv` via get_supported_extensions()
- **Strategy Selection**: `ParserFactory.create_parser()` based on file extension analysis

### Factory Pattern - Dynamic Parser Creation

**Implementation**: DefaultParserFactory with auto-registration in infrastructure/factories.py

```mermaid
graph TB
    FACTORY_INTERFACE["ParserFactory Interface<br/>domain/factories.py<br/>create_parser(), get_supported_extensions()"]

    DEFAULT_FACTORY["DefaultParserFactory<br/>infrastructure/factories.py<br/>Auto-registers 4 parsers in __init__<br/>Extension-based routing"]

    DETECTION_ENGINE["Detection Logic<br/>File extension analysis<br/>can_parse() validation<br/>ValueError on no match"]

    STRATEGY_CREATION["Strategy Creation<br/>Parser instantiation with<br/>detector + TransactionBuilder injection<br/>DateConverter + AmountParser dependencies"]

    FACTORY_INTERFACE --> DEFAULT_FACTORY
    DEFAULT_FACTORY --> DETECTION_ENGINE
    DETECTION_ENGINE --> STRATEGY_CREATION
    STRATEGY_CREATION --> PARSER_INTERFACE
```

**Code Verification**:

- **Auto-Registration**: DefaultParserFactory.**init**() registers PDFStatementParser, XLSStatementParser, XLSXStatementParser, CSVStatementParser
- **Dependency Injection**: Each parser receives detector + TransactionBuilder(DateConverter, AmountParser)
- **Factory Method**: `create_parser(file_path)` iterates registered parsers with can_parse() validation

### Builder Pattern - Transaction Construction

**Implementation**: TransactionBuilder in domain/builders.py with injected utilities

```mermaid
graph TB
    BUILDER_INTERFACE["TransactionBuilder<br/>domain/builders.py<br/>build_from_pdf_line()<br/>build_from_xls_data()<br/>build_from_csv_data()"]

    TRANSACTION_BUILDER["TransactionBuilder Implementation<br/>Injected DateConverter + AmountParser<br/>Immutable Transaction creation<br/>Multi-format support methods"]

    AMOUNT_PARSER["AmountParser<br/>domain/utils.py<br/>parse_european_format()<br/>1.234,56 → Decimal conversion"]

    DATE_CONVERTER["DateConverter<br/>domain/utils.py<br/>convert_dd_mm_yy()<br/>convert_dd_mmm_yy()"]

    VALIDATION_INTEGRATION["Validation Integration<br/>Transaction.__post_init__()<br/>Empty description checks<br/>Zero amount validation"]

    BUILDER_INTERFACE --> TRANSACTION_BUILDER
    TRANSACTION_BUILDER --> AMOUNT_PARSER
    TRANSACTION_BUILDER --> DATE_CONVERTER
    TRANSACTION_BUILDER --> VALIDATION_INTEGRATION
```

**Code Verification**:

- **Constructor Injection**: `TransactionBuilder(date_converter: DateConverter, amount_parser: AmountParser)`
- **Format-Specific Methods**: `build_from_pdf_line()`, `build_from_xls_data()`, `build_from_csv_data()`
- **Immutable Output**: Returns frozen Transaction dataclass instances
- **Error Handling**: Comprehensive ValueError with context information

### Command Pattern - CLI Operations

**Implementation**: Click decorators with command encapsulation in cli/main.py

```mermaid
graph TB
    CLI_GROUP["@click.group()<br/>cli/main.py main entry<br/>Context management<br/>Global options (config, verbose)"]

    COMMANDS["CLI Commands<br/>@cli.command() decorators<br/>info, process, validate, batch, consolidate<br/>Parameter validation via Click"]

    COMMAND_EXECUTION["Command Execution<br/>create_components() dependency setup<br/>Service integration<br/>ProcessingResult/ConsolidationResult"]

    RICH_INTEGRATION["Rich Integration<br/>Progress() context managers<br/>console.print() with styling<br/>JSON output support"]

    CLI_GROUP --> COMMANDS
    COMMANDS --> COMMAND_EXECUTION
    COMMAND_EXECUTION --> RICH_INTEGRATION
```

**Code Verification**:

- **Command Registration**: 5 commands with `@cli.command()` decorators
- **Dependency Setup**: `create_components()` function wires PaymentMethodDetector, DefaultParserFactory, StatementProcessingService
- **Error Isolation**: Individual command error handling with CLIError exceptions
- **Professional Output**: Rich UI with progress bars, tables, panels

### Repository Pattern - Data Abstraction

**Implementation**: ExcelStatementRepository in infrastructure/repositories.py

```mermaid
graph TB
    REPOSITORY_INTERFACE["StatementRepository Interface<br/>domain/repositories.py<br/>save_statement() abstract method"]

    EXCEL_REPOSITORY["ExcelStatementRepository<br/>infrastructure/repositories.py<br/>openpyxl integration<br/>Professional Excel formatting"]

    FILE_OPERATIONS["File Operations<br/>SimpleFileReader + SimpleFileWriter<br/>Path management<br/>Directory creation"]

    FORMAT_ENGINE["Format Engine<br/>openpyxl Workbook creation<br/>Column headers + data rows<br/>Professional styling"]

    REPOSITORY_INTERFACE --> EXCEL_REPOSITORY
    EXCEL_REPOSITORY --> FILE_OPERATIONS
    EXCEL_REPOSITORY --> FORMAT_ENGINE
```

**Code Verification**:

- **Interface**: `StatementRepository` abstract base class in domain/repositories.py
- **Implementation**: `ExcelStatementRepository` with `save_statement(statement, output_path)`
- **File Handling**: Injected SimpleFileReader/SimpleFileWriter for dependency inversion
- **Excel Generation**: openpyxl integration with professional formatting

## Bank Detection Pattern Implementation

**Implementation**: BankDetector interface with concrete implementations and enhanced detection flexibility

```mermaid
graph TB
    DETECTOR_INTERFACE["BankDetector Interface<br/>domain/detectors.py<br/>can_detect(), get_payment_method()"]

    MACRO_DETECTOR["MacroDetector<br/>infrastructure/detectors.py<br/>Macro bank content detection<br/>MACRO_VISA + MACRO_ACCOUNT"]

    BBVA_DETECTOR["BBVADetector<br/>infrastructure/detectors.py<br/>BBVA bank content detection<br/>BBVA_VISA + BBVA_MASTERCARD + BBVA_ACCOUNT"]

    PAYMENT_DETECTOR["PaymentMethodDetector<br/>domain/detectors.py<br/>Composite pattern + Enhanced filename detection<br/>detect_from_content() + detect_from_filename()"]

    ENHANCED_DETECTION["Enhanced Detection (July 2025)<br/>Flexible keyword matching<br/>MOVIMIENTOS + ACCOUNT support<br/>Variable file naming conventions"]

    DETECTOR_INTERFACE --> MACRO_DETECTOR
    DETECTOR_INTERFACE --> BBVA_DETECTOR
    PAYMENT_DETECTOR --> DETECTOR_INTERFACE
    PAYMENT_DETECTOR --> ENHANCED_DETECTION
```

**Code Verification**:

- **Abstract Interface**: `BankDetector` in domain/detectors.py with `can_detect()` and `get_payment_method()`
- **Concrete Implementations**: MacroDetector, BBVADetector with enhanced content analysis
- **Registration**: `PaymentMethodDetector.register_detector()` method for composite pattern
- **Enhanced Detection Logic**: Content analysis with bank-specific indicators and flexible keyword matching
- **Filename Detection**: Improved patterns supporting both "MOVIMIENTOS" and "ACCOUNT" keywords for Macro detection
- **Resilient Matching**: Variable file naming convention support with backward compatibility

## European Number Format Processing Pattern

**Implementation**: AmountParser with pattern recognition in domain/utils.py

```mermaid
flowchart TD
    RAW_INPUT["Raw Number Strings<br/>1.234,56 | 1,234.56 | 123.45"] --> PATTERN_ANALYZER["AmountParser<br/>domain/utils.py<br/>parse_european_format()"]

    subgraph "Detection Engine"
        REGEX_PATTERNS["Pattern Detection<br/>European format recognition<br/>Comma as decimal separator<br/>Dot as thousands separator"]

        FORMAT_CLASSIFIER["Format Classification<br/>String manipulation<br/>Decimal creation<br/>Error handling"]

        NEGATIVE_HANDLER["Negative Handling<br/>Prefix detection (-)<br/>Suffix detection<br/>Sign normalization"]
    end

    subgraph "Conversion Engine"
        EUROPEAN_CONVERTER["European Converter<br/>1.234,56 → 1234.56<br/>String replacement logic<br/>Validation checks"]

        DECIMAL_HANDLER["Decimal Creation<br/>Python decimal.Decimal<br/>Financial precision<br/>Exact arithmetic"]

        CURRENCY_ASSIGNMENT["Currency Assignment<br/>Transaction-level Currency enum<br/>ARS/USD detection<br/>Separate tracking via TransactionBuilder"]
    end

    PATTERN_ANALYZER --> REGEX_PATTERNS
    REGEX_PATTERNS --> FORMAT_CLASSIFIER
    FORMAT_CLASSIFIER --> NEGATIVE_HANDLER

    NEGATIVE_HANDLER --> EUROPEAN_CONVERTER
    EUROPEAN_CONVERTER --> DECIMAL_HANDLER
    DECIMAL_HANDLER --> CURRENCY_ASSIGNMENT
```

**Code Verification**:

- **Implementation**: `AmountParser.parse_european_format()` method in domain/utils.py
- **Pattern Recognition**: String analysis for European format (1.234,56)
- **Conversion Logic**: Replace dots with empty string, comma with dot, then Decimal()
- **Integration**: Used by TransactionBuilder for all format-specific methods

## Validation Pattern Implementation

**Implementation**: StatementValidator with ValidationResult in domain/validation.py

```mermaid
graph TB
    VALIDATOR_INTERFACE["StatementValidator<br/>domain/validation.py<br/>validate() method<br/>ValidationResult return"]

    VALIDATION_RULES["Validation Rules<br/>Transaction count validation<br/>Balance verification capability<br/>Business rule enforcement"]

    BALANCE_SERVICE["BalanceExtractionService<br/>infrastructure/extractors.py<br/>PDF balance extraction<br/>Statement comparison"]

    VALIDATION_RESULT["ValidationResult<br/>domain/validation.py<br/>is_valid boolean<br/>errors list"]

    VALIDATOR_INTERFACE --> VALIDATION_RULES
    VALIDATION_RULES --> BALANCE_SERVICE
    VALIDATION_RULES --> VALIDATION_RESULT
```

**Code Verification**:

- **Interface**: `StatementValidator` class with `validate(statement)` method
- **Result Object**: `ValidationResult` dataclass with `is_valid` and `errors` fields
- **Integration**: Used by StatementProcessingService for validation workflow
- **Balance Checking**: Optional balance extraction service integration

## Pattern Integration Benefits (Implementation Verified)

**Extensibility Benefits**:

- **New Bank Addition**: Implement BankDetector interface, register with PaymentMethodDetector
- **New Format Support**: Implement StatementParser interface, register with ParserFactory
- **Enhanced Validation**: Extend StatementValidator with additional business rules

**Maintainability Benefits**:

- **Clear Separation**: Each pattern handles specific domain concerns
- **Isolated Testing**: Components tested independently via dependency injection
- **Code Reusability**: Shared utilities (AmountParser, DateConverter) across implementations

**Performance Benefits**:

- **Strategy Selection**: O(n) parser detection with early exit on match
- **Memory Efficiency**: Repository abstraction enables streaming for large files
- **Optimization Paths**: Clear bottleneck identification through pattern boundaries

## Architecture Quality Achievements (Code-Verified)

**SOLID Principles**:

- **Single Responsibility**: TransactionBuilder focuses solely on Transaction creation
- **Open/Closed**: ParserFactory extensible via registration without modification
- **Dependency Inversion**: StatementProcessingService depends on abstractions (interfaces)

**Clean Architecture**:

- **Layer Independence**: Domain models have no infrastructure dependencies
- **Dependency Flow**: CLI → Application → Domain → Infrastructure (verified in imports)
- **Framework Independence**: Domain logic isolated from pdfplumber, pandas specifics

**Pattern Consistency**:

- **Uniform Implementation**: Constructor injection pattern across all services
- **Error Handling**: Consistent ValueError usage with descriptive messages
- **Interface Contracts**: Abstract base classes define clear behavioral contracts

## Current Status: Pattern Implementation Complete (Code-Verified)

All enterprise patterns successfully implemented and verified in source:

- **Strategy Pattern**: StatementParser with 4 concrete implementations auto-registered
- **Factory Pattern**: DefaultParserFactory with extension-based routing
- **Builder Pattern**: TransactionBuilder with format-specific methods and utility injection
- **Command Pattern**: CLI operations with Click decorators and Rich UI integration
- **Repository Pattern**: ExcelStatementRepository with professional output formatting
- **Detection Pattern**: BankDetector interface with MacroDetector + BBVADetector implementations

**Architecture Achievement**: Robust enterprise foundation supporting professional financial statement processing with comprehensive extensibility verified through source code analysis, maintaining clean boundaries, testability, and performance optimization through established patterns.
