# CLI Layer Guidelines

## Responsibility

- Define command-line commands, options, help text, and user-facing output.
- Parse user input, invoke application workflows, and translate their results
  into appropriate output and exit statuses.
- Keep financial business rules and statement-format parsing out of CLI code.

## Dependency Boundaries

- CLI code may call application use cases and use infrastructure to assemble
  concrete implementations at startup.
- Do not put workflow logic in command callbacks when it belongs in application,
  or adapter behavior that belongs in infrastructure.
- Keep command interfaces independent of third-party parser and storage types.

## Testing Focus

- Test command behavior, option validation, output, and exit statuses through
  the CLI entry points.
- Stub or inject workflow and adapter dependencies where practical so tests
  remain fast and deterministic.
- Use end-to-end tests for representative user-visible workflows rather than
  duplicating domain and adapter unit coverage.
