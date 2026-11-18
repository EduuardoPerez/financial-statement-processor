# Application Layer Guidelines

## Responsibility

- Coordinate use cases, including statement processing, batch workflows, and
  consolidation.
- Orchestrate domain services and repository or parser contracts without owning
  business rules or file-format details.
- Keep workflow decisions explicit so callers can handle results and failures.

## Dependency Boundaries

- Application code may depend on domain models, services, and contracts.
- Depend on abstractions for storage, parsing, and other external capabilities;
  concrete adapters belong in infrastructure and should be supplied at the
  composition boundary.
- Do not depend on CLI modules or expose infrastructure-specific library types
  through use-case interfaces.

## Testing Focus

- Test use-case orchestration with small fakes for repositories, parsers, and
  other external capabilities.
- Cover success, validation failure, duplicate handling, and adapter error
  propagation where those paths are part of a workflow.
- Keep file-format-specific behavior in infrastructure tests.
