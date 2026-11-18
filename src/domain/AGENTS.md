# Domain Layer Guidelines

## Responsibility

- Define the financial statement models, business rules, validations, and domain
  contracts used throughout the application.
- Keep behavior independent of file formats, databases, command-line interfaces,
  and third-party libraries.
- Prefer deterministic functions and explicit domain types for calculations and
  decisions.

## Dependency Boundaries

- Domain code may depend on other domain modules and the Python standard library.
- Do not import application, infrastructure, or CLI modules into the domain.
- Express external capabilities as domain contracts where appropriate; implement
  file and service integrations in infrastructure and connect them at the outer
  application boundary.

## Testing Focus

- Add fast unit tests for business rules, parsing-independent calculations,
  validation outcomes, and edge cases.
- Keep tests independent of the filesystem and third-party services unless a
  behavior specifically requires an adapter.
- Use representative domain values and assert both successful and invalid cases.
