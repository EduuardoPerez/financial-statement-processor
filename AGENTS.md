# Repository Guidelines

## Language

English is the default language for all project-authored content committed to
this repository. Write documentation, instructions, comments, identifiers,
tests, commit messages, pull request descriptions, and user-facing messages in
English. Preserve non-English source data and exact external-format labels when
they are required to parse, recognize, or test supported statement formats.

## Project Structure & Module Organization

The maintained application uses a `src/` layout with four layers: `src/domain/` holds business rules and models, `src/application/` coordinates use cases, `src/infrastructure/` contains parsers and external adapters, and `src/cli/` exposes commands. Tests live under `tests/unit/`, `tests/integration/`, and `tests/e2e/`; shared fixtures and expected results are in `tests/test_data/`. Bank configuration is in `config/`. Local `input/`, `output/`, and `expected_output/` directories are ignored by Git; do not commit personal statements or generated reports.

## Build, Test, and Development Commands

- `uv sync` installs locked project and development dependencies.
- `PYTHONPATH=src uv run python -m cli.main info` checks the CLI and lists supported formats/banks.
- `PYTHONPATH=src uv run python -m cli.main process input/statement.pdf` processes one statement; `batch` and `consolidate` accept directories.
- `PYTHONPATH=src uv run pytest` runs the test suite; target a file or directory to narrow it, such as `uv run pytest tests/unit/`.
- `uv run ruff check src tests --ignore=E501` lints and `uv run ruff format src tests` formats Python code.
- `uv run mypy src/` runs configured type checks. Pre-commit runs Ruff and mypy hooks.
- GitHub Actions runs the test suite on pushes and pull requests.

## Coding Style & Naming Conventions

Use Python 3.11+, four spaces, and an 88-character line target. Ruff is configured for linting, import sorting, and Black-compatible formatting with double quotes. Follow standard Python naming: `snake_case` for modules, functions, and variables; `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants. Keep business rules in the domain layer and isolate file-format or library details in infrastructure.

## Testing Guidelines

Use pytest. Name test files `test_*.py` and test functions `test_*`; place fast rule-level tests in `tests/unit/`, parser and workflow checks in `tests/integration/`, and end-to-end CLI checks in `tests/e2e/`. Add representative fixtures under `tests/test_data/` when a case depends on statement input. Run the narrow relevant tests, then the full `uv run pytest` suite for broad changes. No enforced coverage threshold is currently active.

## Commit & Pull Request Guidelines

Recent history follows Conventional Commit-style subjects such as `fix: ...` and `test: ...`; use a concise imperative summary with a scope prefix (`feat:`, `fix:`, `test:`, `docs:`) where appropriate. Pull requests should explain the behavior change, list validation commands and results, link related issues when available, and include sample output or screenshots for user-visible CLI/report changes. Avoid committing `.env` secrets or generated statement data unless needed for a test fixture.
