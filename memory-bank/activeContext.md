# Active Context - Financial Statement Processor

## Current Work Focus

### Memory Bank Initialization (Current Task)

- **Status**: In Progress - Creating foundational memory bank files
- **Completed**: projectbrief.md, productContext.md, systemPatterns.md, techContext.md
- **Remaining**: activeContext.md (this file), progress.md
- **Purpose**: Establishing comprehensive project documentation for future development sessions

### Project State Discovery

- **Codebase Analysis**: Comprehensive review of existing implementation
- **Architecture Understanding**: Single-module design with clear separation of concerns
- **Test Coverage**: Well-tested system with integration and unit tests
- **Current Capabilities**: Fully functional Macro VISA statement processing

## Recent Patterns Discovered

### European Number Format Handling

- **Critical Pattern**: Progressive format detection for 1.234,56 notation
- **Implementation**: Multi-stage conversion logic handles various edge cases
- **Reliability**: Robust handling of mixed separators and trailing dashes

### Transaction Type Classification

- **Payment Detection**: "SU PAGO EN PESOS" with negative amount logic
- **Tax Identification**: Multiple tax keywords with positive amount logic
- **Adjustment Handling**: "AJUSTE" patterns with negative amount logic
- **Regular Purchases**: Reference number + description + amount parsing

### Bank Detection Strategy

- **Content-Based**: Analyzes PDF text for bank-specific indicators
- **Extensible Design**: Easy to add new bank patterns
- **Current Implementation**: Macro bank detection with VISA card identification

## Key Decisions & Preferences

### Code Architecture Choices

- **Single Module**: Keep all logic in one file for simplicity during early development
- **Line-by-Line Processing**: Robust approach for variable PDF formatting
- **Graceful Degradation**: Continue processing even if individual transactions fail
- **Test-Driven Development**: Comprehensive test suite with expected output validation

### Data Handling Standards

- **Date Format**: Always output YYYY-MM-DD for consistency
- **Negative Amounts**: Payments and adjustments always negative
- **Currency Consistency**: Detect and preserve ARS/USD accurately
- **Description Cleaning**: Remove amounts, preserve reference numbers

### Quality Assurance Approach

- **Integration Testing**: Use real PDF files with expected output comparison
- **Data Integrity**: Validate transaction counts, amounts, currency distribution
- **Regression Protection**: Comprehensive test coverage prevents breaking changes

## Next Development Priorities

### Phase 1: BBVA Bank Support

- **Analysis Needed**: Study BBVA statement format and patterns
- **Implementation**: Extend detection logic and add BBVA-specific parsing
- **Testing**: Create BBVA test files and expected output
- **Validation**: Ensure no regression in existing Macro functionality

### Phase 2: System Improvements

- **CLI Interface**: Add command-line argument parsing for file paths
- **Batch Processing**: Handle multiple PDF files in one execution
- **Configuration System**: External config for bank patterns and settings
- **Error Reporting**: Enhanced error messages and logging

### Phase 3: Output Enhancements

- **Multiple Formats**: Add CSV and JSON output options
- **Template Support**: Customizable Excel templates
- **Data Validation**: Enhanced validation rules and error detection

## Active Technical Considerations

### Modularity Planning

- **When to Refactor**: Consider splitting into modules when adding 2nd bank
- **Architecture Evolution**: Move from single file to package structure
- **Backward Compatibility**: Maintain existing API during refactoring

### Testing Strategy

- **Test Data Management**: Organize test PDFs and expected outputs by bank
- **Test Automation**: Ensure all tests run automatically
- **Performance Testing**: Validate processing speed with larger statements

### Documentation Standards

- **Memory Bank Updates**: Update after significant changes or discoveries
- **Code Comments**: Minimal comments, self-explaining code preferred
- **README Maintenance**: Keep installation and usage instructions current

## Project Insights & Learnings

### Argentine Banking Complexity

- **Number Formats**: European notation is non-negotiable, must handle perfectly
- **Multi-Currency**: ARS/USD mixing requires careful currency detection
- **Transaction Variety**: Each bank has unique transaction type patterns
- **Language Specifics**: Spanish terminology and abbreviations are critical

### PDF Processing Realities

- **Text-Based Requirement**: Cannot process scanned images
- **Layout Sensitivity**: Small formatting changes can break parsing
- **Robust Patterns**: Need flexible regex patterns for reliable extraction
- **Quality Validation**: Real-world testing essential for reliability

### Development Workflow Effectiveness

- **uv Package Manager**: Fast, reliable dependency management
- **pytest Framework**: Comprehensive testing with clear output
- **Reference Files**: Expected output validation catches regressions
- **Incremental Development**: Small, validated changes work best

## Current Implementation Strengths

### Robustness

- **Error Handling**: Graceful degradation prevents total failures
- **Edge Case Coverage**: Handles various number formats and transaction types
- **Data Integrity**: Comprehensive validation ensures accurate output

### Maintainability

- **Clear Structure**: Easy to understand and modify
- **Test Coverage**: Changes are validated against expected behavior
- **Documentation**: Well-documented codebase with examples

### Extensibility

- **Bank Detection**: Easy to add new bank identification patterns
- **Transaction Types**: Straightforward to add new transaction categories
- **Output Formats**: Ready for additional output format support

## Immediate Next Steps

1. **Complete Memory Bank**: Finish progress.md documentation
2. **Validate Current System**: Run tests to ensure everything works
3. **Plan BBVA Support**: Analyze BBVA statement format requirements
4. **Architecture Review**: Assess if current structure supports expansion
5. **Priority Setting**: Determine which enhancements to tackle first
