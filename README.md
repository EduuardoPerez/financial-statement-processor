# Financial Statement Processor

A command-line tool for converting bank statements into structured transactions
and Excel files. The application code is organized into four layers:
`src/domain`, `src/application`, `src/infrastructure`, and `src/cli`.

## Requirements

- Python 3.15 or later
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
uv sync
```

## Usage

```bash
# List recognized formats and payment methods
PYTHONPATH=src uv run python -m cli.main info

# Process a statement file
PYTHONPATH=src uv run python -m cli.main process /path/to/statement.pdf

# Validate a file without generating output
PYTHONPATH=src uv run python -m cli.main validate /path/to/statement.pdf

# Process supported files in a directory
PYTHONPATH=src uv run python -m cli.main batch /path/to/statements/

# Consolidate transactions from a directory
PYTHONPATH=src uv run python -m cli.main consolidate /path/to/statements/
```

Pass a YAML configuration with `--config` before the command. Without that
option, the CLI reads environment variables prefixed with `FSP_`. Available
settings and their defaults are defined in `src/infrastructure/config.py`; the
files `config/development.yaml` and `config/production.yaml` are examples. To
customize payment method names, see
[`docs/PAYMENT_METHOD_MAPPING.md`](docs/PAYMENT_METHOD_MAPPING.md).

Processed files are saved to `output/` by default. The `input/`, `output/`, and
`expected_output/` directories are local working directories excluded from Git.
Do not store personal statements in the repository. Test samples are kept in
`tests/test_data/`.

The planned structured reconciliation output is specified in
[`docs/RECONCILIATION_DATA_CONTRACT_V1.md`](docs/RECONCILIATION_DATA_CONTRACT_V1.md).
The current CLI does not emit that format yet.

Processing results now retain per-transaction source evidence and report rows
read, retained, and discarded. The CLI displays each discarded row's locator and
reason; `--json` includes the same internal extraction summary. CSV locators
use logical record numbers after blank lines are skipped, with the header as
record 1. Workbook locators use one-based physical row numbers. Headers and
completely blank rows are excluded from counts. XLS account
exports also exclude their known title/header rows. PDF locators use extracted
text line numbers; blank lines, lines without a leading transaction date, and
known balance/header lines are excluded. Any other candidate line that cannot
be parsed counts as discarded. These diagnostics do not yet form the versioned
manifest specified by the reconciliation contract.

## Development

```bash
uv sync
uv run pytest
uv run ruff check src tests --ignore=E501
uv run ruff format --check src tests
uv run mypy src/
```

Ruff and mypy run in the pre-commit hooks. The pytest suite runs in GitHub
Actions to keep local commits fast.
