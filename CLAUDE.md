# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool for processing financial statements from Argentine banks into standardized Excel format. Uses clean hexagonal architecture with 4 layers: domain, application, infrastructure, and CLI.

**Supported Banks/Formats:**
- PDF: Macro VISA, BBVA VISA, BBVA Mastercard
- XLS: BBVA Account, Macro Account
- XLSX: Mercadopago, BBVA Mastercard
- CSV: BBVA/Macro VISA (Autorizaciones, Movimientos)

## Common Commands

```bash
# Install dependencies
uv sync

# Run CLI commands (PYTHONPATH required)
PYTHONPATH=src uv run python -m cli.main info
PYTHONPATH=src uv run python -m cli.main process input/statement.pdf
PYTHONPATH=src uv run python -m cli.main batch input/
PYTHONPATH=src uv run python -m cli.main consolidate input/
PYTHONPATH=src uv run python -m cli.main validate input/statement.pdf

# Run tests
uv run pytest                                    # All tests
uv run pytest tests/unit/ -v                     # Unit tests only
uv run pytest tests/integration/ -v              # Integration tests
uv run pytest --cov=. --cov-report=term-missing  # With coverage
uv run pytest tests/unit/domain/test_models.py -v  # Single file

# Code quality
uv run ruff check .              # Lint
uv run ruff check . --fix        # Auto-fix
uv run ruff format .             # Format
uv run mypy .                    # Type check
pre-commit run --all-files       # All hooks
```

## Architecture

```
src/
├── domain/           # Core business logic (no external dependencies)
│   ├── models.py     # Transaction, Statement, PaymentMethod enum, Currency enum
│   ├── services.py   # DuplicateDetector, abstract parser/validator interfaces
│   ├── builders.py   # TransactionBuilder, StatementBuilder
│   ├── detectors.py  # BankDetector interface, PaymentMethodDetector
│   └── validation.py # StatementValidator, ValidationResult
├── application/      # Use case orchestration
│   └── services.py   # StatementProcessingService (main orchestrator)
├── infrastructure/   # External adapters
│   ├── parsers/      # PDFStatementParser, XLS/XLSX/CSVStatementParser
│   ├── detectors.py  # MacroDetector, BBVADetector implementations
│   ├── factories.py  # DefaultParserFactory
│   ├── repositories.py # ExcelStatementRepository
│   └── config.py     # ApplicationConfig, ProcessingConfig, OutputConfig
└── cli/
    └── main.py       # Click + Rich UI (5 commands: info, process, validate, batch, consolidate)
```

**Key Patterns:**
- Strategy: 4 file format parsers selected by extension
- Factory: DefaultParserFactory auto-registers parsers in `__init__`
- Builder: TransactionBuilder/StatementBuilder with injected DateConverter, AmountParser
- Repository: ExcelStatementRepository abstracts Excel output

## Key Implementation Details

**Payment Method Detection Flow:**
1. `PaymentMethodDetector` aggregates multiple `BankDetector` implementations
2. Detectors check filename keywords and file content
3. File extension routes to appropriate parser via `DefaultParserFactory`

**Transaction Processing:**
- European number format (1.234,56) via `AmountParser.parse_european_format()`
- Multiple date formats: DD.MM.YY, DD-MMM-YY, DD/MM/YYYY, ISO 8601
- Duplicate detection uses absolute amounts: `(date, abs(amount))` key

**Configuration Priority:**
1. CLI arguments (highest)
2. Environment variables (FSP_* prefix)
3. YAML config files
4. Built-in defaults

## Testing

Tests organized by layer in `tests/`:
- `unit/` - Component tests (~15 files)
- `integration/` - End-to-end workflows (~9 files)
- `e2e/` - CLI smoke tests

pytest config in `pyproject.toml` sets `pythonpath = ["src"]` so tests can import directly.

## Important Files

- `src/cli/main.py` - CLI entry point and command definitions
- `src/application/services.py` - Main processing orchestrator
- `src/domain/models.py` - Core data models
- `src/infrastructure/parsers/pdf_parser.py` - Complex PDF parsing logic (~200 lines)
- `config/development.yaml` - Development configuration example
