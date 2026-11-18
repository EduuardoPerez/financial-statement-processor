---
name: add-statement-format
description: "Inspect statement samples and the existing parser pipeline, then add and validate support for a new bank or statement format in this repository."
---

# Add Statement Format

Use this skill when adding support for a bank, account or card product, or a new file layout. The task may cover PDF, CSV, XLS, or XLSX input; first establish which variations are actually present.

## Inspect and map the format

- Start with the sample paths supplied for the task. If local samples are mentioned but not located, inspect likely user-provided sample directories such as `input/` or `Downloads/` by filename and extension, then ask for the path if needed. Do not sweep unrelated folders.
- Treat statements as private financial data. Read only what is needed to identify headers, layout, date and amount conventions, transaction boundaries, and bank/product indicators. Never copy personal statements into the repository, paste account or transaction details into documentation, logs, or chat, or include them in a commit.
- Inspect the existing pipeline before designing a parser: `src/infrastructure/parsers/`, `src/infrastructure/detectors.py`, `src/infrastructure/factories.py`, `src/domain/models.py`, builders and utilities in `src/domain/`, plus the relevant parser and detector tests and fixtures.
- Compare the sample against existing parsers and detectors. Reuse a parser when its actual structure and conversion rules fit; otherwise add a focused parser. Confirm whether detection should use content, filename, or both, and whether a new payment method is needed.
- Check whether the format has balance data that affects `src/infrastructure/extractors.py` or statement validation. Trace the complete processing and output path so parsed transactions preserve the domain model's date, description, amount, currency, and payment method semantics.

## Implement and validate

- Keep format-specific file reading and row/text interpretation in infrastructure. Put reusable business rules in the domain layer and wire any new parser into `DefaultParserFactory`.
- Add narrow tests for file recognition, payment-method detection, representative transaction parsing, malformed or empty input where relevant, and balance validation when supported by the format. Use synthetic or anonymized fixtures; do not add the supplied personal statement.
- Run the focused tests first, then the repository checks appropriate to the change: Ruff lint and format checks, mypy, and the full pytest suite for a parser or detector change. Review the diff for private sample data and generated files.
- For local YAML behavior, use `config/local-statements.example.yaml` as the generic starting point and keep machine-specific paths in the ignored `config/local-statements.yaml`. Load the template with the existing `ApplicationConfig.from_yaml` path or CLI `--config` flow when validating configuration.

## Repository entry points

- Parsers: `src/infrastructure/parsers/`
- Parser registration: `src/infrastructure/factories.py`
- Bank and product detection: `src/infrastructure/detectors.py` and `src/domain/detectors.py`
- CLI configuration: `src/cli/main.py` (`--config`) and `src/infrastructure/config.py`
- Tests and safe fixtures: `tests/unit/`, `tests/integration/`, `tests/test_data/`
