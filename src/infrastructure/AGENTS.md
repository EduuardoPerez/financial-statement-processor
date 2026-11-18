# Infrastructure Layer Guidelines

## Responsibility

- Implement integrations for configuration, file access, statement extraction,
  parsing, and other external systems.
- Translate external representations into domain models and implement the
  contracts consumed by application workflows.
- Keep library-specific behavior and error handling at the adapter boundary.

## Dependency Boundaries

- Infrastructure may depend on domain contracts and models, plus the external
  libraries needed by its adapters.
- Avoid importing CLI code. Keep workflow coordination in application and
  business rules in domain.
- Do not make domain or application behavior depend directly on a parser or
  storage library's concrete types.

## Testing Focus

- Test format and adapter behavior with focused unit or integration tests,
  including malformed input, missing data, and conversion edge cases.
- Use small temporary files or fixtures for filesystem behavior; do not use
  personal statement data.
- Verify adapters produce the expected domain values and report failures in a
  form their callers can handle.
