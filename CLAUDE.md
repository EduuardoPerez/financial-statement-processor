# Claude Code Notes

## Project layout

- `src/domain/`: business rules and models
- `src/application/`: processing and consolidation use cases
- `src/infrastructure/`: parsers, configuration, and Excel repository
- `src/cli/`: Click commands
- `tests/unit/`, `tests/integration/`, `tests/e2e/`: automated tests
- `tests/test_data/`: statement fixtures and expected results used by tests

Use the CLI and parser implementations under `src/`. The former root-level
`parse_visa_statement.py` entry point has been removed.

## Common commands

```bash
uv sync
PYTHONPATH=src uv run python -m cli.main info
PYTHONPATH=src uv run python -m cli.main process /path/to/statement.pdf
uv run pytest
uv run ruff check src tests --ignore=E501
uv run ruff format src tests
uv run mypy src/
pre-commit run --all-files
```

The pre-commit hooks run Ruff and mypy. GitHub Actions runs the complete test
suite on pushes and pull requests.

## Working with statements

Keep personal input files and generated reports in local `input/` and `output/`
directories; Git ignores these paths. Use only the curated fixtures in
`tests/test_data/` for automated tests, and avoid adding real account data to
those fixtures without anonymizing it.

Put business rules in `src/domain/`, orchestration in `src/application/`, and
file-format or library details in `src/infrastructure/`. Add or update tests in
the matching test layer when changing behavior.
